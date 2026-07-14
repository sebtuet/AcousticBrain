from acousticbrain.models import (
    ControlledReflectionVerificationPlanningAnalysis,
    ReflectionCandidateGeometricStatus,
    ReflectionCandidateVerificationExclusion,
    ReflectionCandidateVerificationProposal,
    ReflectionVerificationCausalityStatus,
    ReflectionVerificationExclusionReason,
    ReflectionVerificationExecutionStatus,
    ReflectionVerificationImpact,
    ReflectionVerificationMethod,
)


class ControlledReflectionVerificationPlanningEngine:
    """Builds descriptive verification proposals from existing PR-035 candidates."""

    SOURCE_ANALYSES = ("MaterialAwareReflectionCandidateAnalysis",)
    RULES = (
        "REFLECTION_VERIFICATION_EXISTING_CANDIDATES_ONLY",
        "REFLECTION_VERIFICATION_INHERITS_INFORMATIVE_ORDER",
        "REFLECTION_VERIFICATION_CONTROL_PROVENANCE_SEPARATED",
        "REFLECTION_VERIFICATION_NOT_EXECUTED",
        "REFLECTION_VERIFICATION_NO_CAUSALITY",
        "REFLECTION_VERIFICATION_NO_ELIGIBILITY_IMPACT",
        "REFLECTION_VERIFICATION_NO_RECOMMENDATION_IMPACT",
    )
    CONTROLLED_VARIABLES = (
        "MICROPHONE_POSITION",
        "LOUDSPEAKER_POSITION",
        "LOUDSPEAKER_ORIENTATION",
        "SIGNAL_CHAIN_ASSIGNMENT",
        "MEASUREMENT_LEVEL",
    )
    CHANGED_VARIABLES = ("TEMPORARY_MASK_STATE",)
    OBSERVABLE_FACTS = (
        "etc.observed_event_delay_ms",
        "etc.observed_event_relative_level_db",
        "etc_reflection.geometry_timing_error_ms",
    )
    SUPPORTING_OUTCOMES = ("REFLECTION_DECREASES_AFTER_MASKING",)
    COUNTER_OUTCOMES = ("REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING",)
    LIMITATIONS = (
        "PROPOSAL_NOT_EXECUTED",
        "CAUSALITY_NOT_ESTABLISHED",
        "ELIGIBILITY_UNCHANGED",
        "RECOMMENDATIONS_UNCHANGED",
        "MASK_PROPERTIES_AND_PLACEMENT_NOT_PRESCRIBED",
        "OBSERVED_CHANGE_REQUIRES_FUTURE_COMPARISON",
    )

    def analyze(self, candidate_analysis):
        """Pure function of MaterialAwareReflectionCandidateAnalysis."""
        proposals = []
        exclusions = []
        for candidate in sorted(
            candidate_analysis.candidates,
            key=lambda item: (
                item.informative_rank is None,
                item.informative_rank or 0,
                item.candidate_id,
            ),
        ):
            if candidate.geometric_status is ReflectionCandidateGeometricStatus.REJECTED:
                exclusions.append(self._exclusion(candidate))
            else:
                proposals.append(self._proposal(candidate))
        return ControlledReflectionVerificationPlanningAnalysis(
            proposals=tuple(proposals),
            exclusions=tuple(sorted(
                exclusions, key=lambda item: item.source_candidate_id
            )),
            source_analysis_codes=self.SOURCE_ANALYSES,
            applied_rule_codes=self.RULES,
        )

    @classmethod
    def _proposal(cls, candidate):
        if (
            candidate.informative_rank is None
            or candidate.correlation_id is None
            or candidate.observed_event_id is None
        ):
            raise ValueError("Accepted reflection candidates require existing references.")
        target_kind = "REGION" if candidate.region_id is not None else "SURFACE"
        target_id = candidate.region_id or candidate.surface_id
        return ReflectionCandidateVerificationProposal(
            proposal_id=f"reflection_verification_proposal.{candidate.candidate_id}",
            source_candidate_id=candidate.candidate_id,
            proposal_order=candidate.informative_rank,
            correlation_id=candidate.correlation_id,
            path_id=candidate.path_id,
            surface_id=candidate.surface_id,
            region_id=candidate.region_id,
            observed_event_id=candidate.observed_event_id,
            target_kind=target_kind,
            target_id=target_id,
            method=ReflectionVerificationMethod.TEMPORARY_MASK,
            reference_condition_code="UNMASKED_REFERENCE",
            intervention_condition_code="TEMPORARY_MASK_APPLIED",
            controlled_variable_codes=cls.CONTROLLED_VARIABLES,
            changed_variable_codes=cls.CHANGED_VARIABLES,
            observable_fact_codes=cls.OBSERVABLE_FACTS,
            supporting_outcome_codes=cls.SUPPORTING_OUTCOMES,
            counter_outcome_codes=cls.COUNTER_OUTCOMES,
            source_evidence_codes=cls._evidence_codes(candidate),
            source_provenance_codes=candidate.provenance_codes,
            planning_rule_codes=cls.RULES,
            execution_status=ReflectionVerificationExecutionStatus.NOT_EXECUTED,
            causality_status=ReflectionVerificationCausalityStatus.NOT_ESTABLISHED,
            eligibility_impact=ReflectionVerificationImpact.NONE,
            recommendation_impact=ReflectionVerificationImpact.NONE,
            limitations=cls.LIMITATIONS,
        )

    @classmethod
    def _exclusion(cls, candidate):
        return ReflectionCandidateVerificationExclusion(
            source_candidate_id=candidate.candidate_id,
            reason=ReflectionVerificationExclusionReason.GEOMETRICALLY_REJECTED,
            source_evidence_codes=cls._evidence_codes(candidate),
            source_provenance_codes=candidate.provenance_codes,
            planning_rule_codes=cls.RULES,
        )

    @staticmethod
    def _evidence_codes(candidate):
        return (
            f"evidence.{candidate.candidate_id}.overall_compatibility",
            *(item.code for item in candidate.evidence_links),
        )
