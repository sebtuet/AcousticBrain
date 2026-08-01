from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidenceBlockingFactor,
    EvidencePlanCompletionInput,
    EvidencePlanCompletionReferenceKind,
    EvidencePlanCompletionResolution,
    EvidencePlanCompletionResolutionStatus,
    ListeningPositionSamplingProtocol,
)


class EvidencePlanCompletionReferenceResolver:
    """Resolves V1 identities without deciding compatibility or readiness."""

    MISSING_INPUT = "compatible_protocol_or_plan_id"

    def resolve(
        self,
        completion_input,
        *,
        source_plans,
        blocking_factors,
        protocol_references=(),
        plan_references=(),
    ):
        if not isinstance(completion_input, EvidencePlanCompletionInput):
            raise TypeError("EvidencePlanCompletionInput is required.")
        source_plans = self._typed(
            source_plans,
            EvidenceAcquisitionPlan,
            "source plans",
        )
        blocking_factors = self._typed(
            blocking_factors,
            EvidenceBlockingFactor,
            "blocking factors",
        )
        protocols = self._typed(
            protocol_references,
            ListeningPositionSamplingProtocol,
            "protocol references",
        )
        plans = self._typed(
            plan_references,
            EvidenceAcquisitionPlan,
            "plan references",
        )

        source = self._one(
            source_plans,
            key="plan_id",
            expected=completion_input.source_plan_id,
            unknown="SOURCE_PLAN_UNKNOWN",
            ambiguous="SOURCE_PLAN_AMBIGUOUS",
        )
        self._validate_source(source, blocking_factors)

        if (
            completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
        ):
            references = protocols
            key = "protocol_id"
        else:
            references = plans
            key = "plan_id"
        reference = self._one(
            references,
            key=key,
            expected=completion_input.reference_id,
            unknown="REFERENCE_UNKNOWN",
            ambiguous="REFERENCE_AMBIGUOUS",
        )
        if (
            completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PLAN
            and reference.plan_id == source.plan_id
        ):
            raise ValueError(
                f"REFERENCE_SELF_REFERENCE: {source.plan_id} cannot reference itself."
            )
        return EvidencePlanCompletionResolution(
            completion_input=completion_input,
            source_plan=source,
            reference=reference,
            status=(
                EvidencePlanCompletionResolutionStatus.REFERENCE_RESOLVED
            ),
        )

    def _validate_source(self, source, blocking_factors):
        if source.status is not EvidenceAcquisitionStatus.BLOCKED:
            raise ValueError(
                f"SOURCE_PLAN_NOT_BLOCKED: {source.plan_id} is {source.status.value}."
            )
        matching = tuple(
            factor
            for factor in blocking_factors
            if factor.factor_id in source.blocking_factor_ids
        )
        matched_ids = tuple(factor.factor_id for factor in matching)
        if (
            len(matched_ids) != len(set(matched_ids))
            or set(matched_ids) != set(source.blocking_factor_ids)
        ):
            raise ValueError(
                "SOURCE_PLAN_NOT_V1_COMPLETABLE: blocking-factor identity is "
                f"not exactly resolved for {source.plan_id}."
            )
        completable = tuple(
            factor
            for factor in matching
            if factor.code == "MISSING_PARAMETERS"
            and factor.source_object_ids == (self.MISSING_INPUT,)
        )
        if len(completable) != 1:
            raise ValueError(
                "SOURCE_PLAN_NOT_V1_COMPLETABLE: "
                f"{source.plan_id} is not blocked only by {self.MISSING_INPUT}."
            )
        if len(matching) != 1:
            raise ValueError(
                "SOURCE_PLAN_HAS_OTHER_BLOCKERS: "
                f"{source.plan_id} retains other blocking factors."
            )
        if self.MISSING_INPUT not in source.required_inputs:
            raise ValueError(
                "SOURCE_PLAN_NOT_V1_COMPLETABLE: "
                f"{source.plan_id} does not require {self.MISSING_INPUT}."
            )

    @staticmethod
    def _typed(values, expected_type, label):
        if not isinstance(values, tuple):
            raise TypeError(f"Evidence-plan completion {label} must be a tuple.")
        if any(not isinstance(value, expected_type) for value in values):
            raise TypeError(
                f"Evidence-plan completion {label} contain an invalid object."
            )
        return values

    @staticmethod
    def _one(values, *, key, expected, unknown, ambiguous):
        matches = tuple(
            value for value in values if getattr(value, key) == expected
        )
        if not matches:
            raise ValueError(f"{unknown}: {expected}.")
        if len(matches) != 1:
            raise ValueError(f"{ambiguous}: {expected}.")
        return matches[0]
