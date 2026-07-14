from acousticbrain.models import (
    ControlledReflectionExperimentComparison,
    ControlledReflectionExperimentDeclaration,
    ControlledReflectionHypothesisStatusUpdate,
    ReflectionCandidateVerificationProposal,
    ReflectionExperimentComparisonStatus,
    ReflectionHypothesisCausalityStatus,
    ReflectionHypothesisImpact,
    ReflectionHypothesisObservationStatus,
)


class ControlledReflectionHypothesisStatusUpdateEngine:
    """Updates observation support without attributing a causal mechanism."""

    LEVEL_OBSERVABLE = "etc.observed_event_relative_level_db"
    SOURCE_ANALYSES = (
        "ControlledReflectionVerificationPlanningAnalysis",
        "ControlledReflectionExperimentDeclaration",
        "ControlledReflectionExperimentComparison",
    )
    COMMON_RULES = (
        "SINGLE_COMPARISON_ONLY",
        "OBSERVATION_SUPPORT_ONLY",
        "CAUSALITY_NOT_ESTABLISHED",
        "DECISIONS_UNCHANGED",
    )

    def analyze(self, proposal, declaration, comparison):
        if not isinstance(proposal, ReflectionCandidateVerificationProposal):
            raise ValueError("PR-039 requires one PR-036 proposal.")
        if not isinstance(declaration, ControlledReflectionExperimentDeclaration):
            raise ValueError("PR-039 requires one PR-037 declaration.")
        if declaration.proposal_id != proposal.proposal_id:
            return self._missing_or_incoherent(
                proposal, declaration, "PROPOSAL_DECLARATION_LINK_INCOHERENT"
            )
        if comparison is None:
            return self._missing_or_incoherent(
                proposal, declaration, "COMPARISON_ABSENT"
            )
        if not isinstance(comparison, ControlledReflectionExperimentComparison):
            return self._missing_or_incoherent(
                proposal, declaration, "COMPARISON_TYPE_INVALID"
            )
        if (
            comparison.proposal_id != proposal.proposal_id
            or comparison.experiment_declaration_id != declaration.declaration_id
        ):
            return self._missing_or_incoherent(
                proposal, declaration, "COMPARISON_LINK_INCOHERENT"
            )

        status = comparison.status
        if status is ReflectionExperimentComparisonStatus.NOT_COMPARABLE:
            return self._result(
                proposal, declaration, comparison,
                ReflectionHypothesisObservationStatus.NOT_ASSESSABLE,
                "NOT_COMPARABLE_TO_NOT_ASSESSABLE",
                "COMPARISON_NOT_COMPARABLE",
            )
        if status is ReflectionExperimentComparisonStatus.INCONCLUSIVE:
            return self._result(
                proposal, declaration, comparison,
                ReflectionHypothesisObservationStatus.INCONCLUSIVE,
                "INCONCLUSIVE_REMAINS_INCONCLUSIVE",
                "COMPARISON_INCONCLUSIVE",
            )
        if status is ReflectionExperimentComparisonStatus.NO_OBSERVABLE_CHANGE:
            return self._result(
                proposal, declaration, comparison,
                ReflectionHypothesisObservationStatus.NOT_SUPPORTED_BY_OBSERVATION,
                "NO_CHANGE_TO_NOT_SUPPORTED_BY_OBSERVATION",
                "NO_CHANGE_WITHIN_OBSERVED_PROTOCOL_SCOPE",
            )

        level = next(
            (
                item for item in comparison.observed_differences
                if item.observable_code == self.LEVEL_OBSERVABLE
            ),
            None,
        )
        if level is None or level.signed_difference == 0.0:
            return self._result(
                proposal, declaration, comparison,
                ReflectionHypothesisObservationStatus.INCONCLUSIVE,
                "CHANGE_WITHOUT_LEVEL_DECREASE_IS_INCONCLUSIVE",
                "TARGET_LEVEL_DECREASE_NOT_OBSERVED",
            )
        if level.signed_difference < 0.0:
            return self._result(
                proposal, declaration, comparison,
                ReflectionHypothesisObservationStatus.SUPPORTED_BY_OBSERVATION,
                "TARGET_LEVEL_DECREASE_TO_OBSERVATION_SUPPORT",
                "TARGET_EVENT_LEVEL_DECREASED_AFTER_INTERVENTION",
            )
        return self._result(
            proposal, declaration, comparison,
            ReflectionHypothesisObservationStatus.NOT_SUPPORTED_BY_OBSERVATION,
            "TARGET_LEVEL_INCREASE_TO_NOT_SUPPORTED",
            "TARGET_EVENT_LEVEL_DID_NOT_DECREASE_AFTER_INTERVENTION",
        )

    @classmethod
    def _missing_or_incoherent(cls, proposal, declaration, justification):
        return cls._build(
            proposal=proposal,
            declaration=declaration,
            comparison=None,
            status=ReflectionHypothesisObservationStatus.NOT_ASSESSABLE,
            measured_fact_codes=(),
            comparison_result_codes=(),
            rule="ABSENT_OR_INCOHERENT_INPUT_TO_NOT_ASSESSABLE",
            justification=justification,
        )

    @classmethod
    def _result(cls, proposal, declaration, comparison, status, rule, justification):
        measured = tuple(
            f"{comparison.comparison_id}.{item.observable_code}.difference"
            for item in comparison.observed_differences
        )
        return cls._build(
            proposal=proposal,
            declaration=declaration,
            comparison=comparison,
            status=status,
            measured_fact_codes=measured,
            comparison_result_codes=(
                comparison.comparison_id,
                f"comparison_status.{comparison.status.value}",
            ),
            rule=rule,
            justification=justification,
        )

    @classmethod
    def _build(
        cls, *, proposal, declaration, comparison, status,
        measured_fact_codes, comparison_result_codes, rule, justification,
    ):
        source_id = (
            comparison.comparison_id
            if comparison is not None
            else declaration.declaration_id
        )
        return ControlledReflectionHypothesisStatusUpdate(
            update_id=f"reflection_hypothesis_status_update.{source_id}",
            target_kind="CANDIDATE",
            target_id=proposal.source_candidate_id,
            proposal_id=proposal.proposal_id,
            experiment_declaration_id=declaration.declaration_id,
            comparison_id=(
                comparison.comparison_id if comparison is not None else None
            ),
            status=status,
            measured_fact_codes=measured_fact_codes,
            comparison_result_codes=comparison_result_codes,
            transition_rule_codes=(*cls.COMMON_RULES, rule),
            status_provenance_codes=(
                "STATUS_DERIVED_FROM_EXPLICIT_TRANSITION_RULE",
            ),
            justification_codes=(justification,),
            causality_status=ReflectionHypothesisCausalityStatus.NOT_ESTABLISHED,
            recommendation_impact=ReflectionHypothesisImpact.NONE,
            ranking_impact=ReflectionHypothesisImpact.NONE,
            eligibility_impact=ReflectionHypothesisImpact.NONE,
            source_analysis_codes=cls.SOURCE_ANALYSES,
        )
