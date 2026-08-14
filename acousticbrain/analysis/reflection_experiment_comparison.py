from acousticbrain.models import (
    ControlledReflectionExperimentComparison,
    ControlledReflectionExperimentDeclaration,
    ObservedReflectionDifference,
    ReflectionCandidateVerificationProposal,
    ReflectionComparisonCausalityStatus,
    ReflectionComparisonImpact,
    ReflectionComparisonObservation,
    ReflectionExperimentComparisonStatus,
    ReflectionExperimentDeclarationStatus,
)


class DeterministicReflectionExperimentComparisonEngine:
    """Compares declared observations without interpreting their cause."""

    SOURCE_ANALYSES = (
        "ControlledReflectionVerificationPlanningAnalysis",
        "ControlledReflectionExperimentDeclaration",
        "DeclaredReflectionComparisonObservation",
    )
    RULES = (
        "PR036_TEMPORAL_TARGET_ONLY",
        "EXECUTED_DECLARATION_REQUIRED",
        "EXPLICIT_MEASUREMENT_REFERENCES_ONLY",
        "EXACT_NUMERICAL_DIFFERENCE_ONLY",
        "PARTIAL_COVERAGE_IS_INCONCLUSIVE",
        "CAUSALITY_NOT_ESTABLISHED",
        "DECISIONS_UNCHANGED",
    )

    def analyze(
        self,
        proposal,
        declaration,
        baseline_observations,
        intervention_observations,
    ):
        if not isinstance(proposal, ReflectionCandidateVerificationProposal):
            raise ValueError("PR-038 requires one PR-036 proposal.")
        if not isinstance(declaration, ControlledReflectionExperimentDeclaration):
            raise ValueError("PR-038 requires one PR-037 declaration.")
        if declaration.proposal_id != proposal.proposal_id:
            raise ValueError("Comparison proposal and declaration must match.")
        baseline = tuple(baseline_observations)
        intervention = tuple(intervention_observations)
        if any(not isinstance(item, ReflectionComparisonObservation) for item in (*baseline, *intervention)):
            raise ValueError("Comparison observations must be typed.")

        baseline_ids = tuple(
            item.reference_id
            for item in declaration.reference_condition.measurement_references
        )
        intervention_ids = tuple(
            item.reference_id
            for item in declaration.intervention_condition.measurement_references
        )
        reason_codes = []
        if declaration.status is not ReflectionExperimentDeclarationStatus.EXECUTED:
            reason_codes.append("DECLARATION_NOT_EXECUTED")
        if len(baseline_ids) != 1 or len(intervention_ids) != 1:
            reason_codes.append("SINGLE_MEASUREMENT_PER_CONDITION_REQUIRED")
        if not baseline or not intervention:
            reason_codes.append("OBSERVATIONS_MISSING")
        allowed = set(proposal.observable_fact_codes)
        expected_window = proposal.observed_event_id
        for observations, expected_ids, side in (
            (baseline, set(baseline_ids), "BASELINE"),
            (intervention, set(intervention_ids), "INTERVENTION"),
        ):
            if any(item.measurement_reference_id not in expected_ids for item in observations):
                reason_codes.append(f"{side}_MEASUREMENT_REFERENCE_MISMATCH")
            if any(item.temporal_window_code != expected_window for item in observations):
                reason_codes.append(f"{side}_TEMPORAL_WINDOW_MISMATCH")
            if any(item.observable_code not in allowed for item in observations):
                reason_codes.append(f"{side}_OBSERVABLE_NOT_PLANNED")
            codes = tuple(item.observable_code for item in observations)
            if len(codes) != len(set(codes)):
                reason_codes.append(f"{side}_OBSERVABLE_DUPLICATED")

        if reason_codes:
            return self._result(
                proposal, declaration, baseline_ids, intervention_ids, (),
                ReflectionExperimentComparisonStatus.NOT_COMPARABLE,
                tuple(dict.fromkeys(reason_codes)),
            )

        baseline_by_code = {item.observable_code: item for item in baseline}
        intervention_by_code = {item.observable_code: item for item in intervention}
        common_codes = sorted(set(baseline_by_code) & set(intervention_by_code))
        differences = []
        incompatible_units = False
        for code in common_codes:
            before = baseline_by_code[code]
            after = intervention_by_code[code]
            if before.unit != after.unit:
                incompatible_units = True
                continue
            signed = round(after.value - before.value, 10)
            differences.append(ObservedReflectionDifference(
                observable_code=code,
                unit=before.unit,
                baseline_value=before.value,
                intervention_value=after.value,
                signed_difference=signed,
                absolute_difference=abs(signed),
                baseline_provenance_codes=before.provenance_codes,
                intervention_provenance_codes=after.provenance_codes,
            ))
        complete = set(baseline_by_code) == allowed == set(intervention_by_code)
        if incompatible_units or not complete:
            status = ReflectionExperimentComparisonStatus.INCONCLUSIVE
            reasons = tuple(
                code for code, active in (
                    ("OBSERVABLE_UNITS_DIFFER", incompatible_units),
                    ("OBSERVABLE_COVERAGE_INCOMPLETE", not complete),
                ) if active
            )
        elif any(item.absolute_difference > 0.0 for item in differences):
            status = ReflectionExperimentComparisonStatus.CHANGE_OBSERVED
            reasons = ()
        else:
            status = ReflectionExperimentComparisonStatus.NO_OBSERVABLE_CHANGE
            reasons = ()
        return self._result(
            proposal, declaration, baseline_ids, intervention_ids,
            tuple(differences), status, reasons,
        )

    @classmethod
    def _result(
        cls, proposal, declaration, baseline_ids, intervention_ids,
        differences, status, reasons,
    ):
        return ControlledReflectionExperimentComparison(
            comparison_id=(
                "reflection_experiment_comparison."
                f"{declaration.declaration_id}"
            ),
            experiment_declaration_id=declaration.declaration_id,
            proposal_id=proposal.proposal_id,
            status=status,
            temporal_window_code=proposal.observed_event_id,
            baseline_measurement_reference_ids=tuple(sorted(baseline_ids)),
            intervention_measurement_reference_ids=tuple(sorted(intervention_ids)),
            observed_differences=tuple(sorted(
                differences, key=lambda item: item.observable_code
            )),
            reason_codes=reasons,
            causality_status=ReflectionComparisonCausalityStatus.NOT_ESTABLISHED,
            ranking_impact=ReflectionComparisonImpact.NONE,
            recommendation_impact=ReflectionComparisonImpact.NONE,
            eligibility_impact=ReflectionComparisonImpact.NONE,
            source_analysis_codes=cls.SOURCE_ANALYSES,
            applied_rule_codes=cls.RULES,
        )
