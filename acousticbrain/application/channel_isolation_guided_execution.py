from dataclasses import dataclass

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    EvidencePlanPreparationRecord,
    EvidencePlanPreparationRegistry,
)

from .evidence_plan_preparation import evidence_acquisition_plan_fingerprint


@dataclass(frozen=True)
class ChannelIsolationExecutionChecklist:
    required_inputs: tuple[str, ...]
    independent_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    measurements: tuple[str, ...]
    expected_observations: tuple[str, ...]
    instructions: tuple[str, ...]
    success_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    limitations: tuple[str, ...]
    required_acquired_channels: tuple[str, ...] = ("LEFT", "RIGHT")
    required_repeated_channels: tuple[str, ...] = ("LEFT", "RIGHT")


@dataclass(frozen=True)
class ChannelIsolationGuidedExecutionJourney:
    plan: EvidenceAcquisitionPlan
    preparation_record: EvidencePlanPreparationRecord
    preparation_status: str
    checklist: ChannelIsolationExecutionChecklist
    user_action_state: str


class ChannelIsolationGuidedExecutionService:
    """Builds operational guidance without declaring or executing an experiment."""

    def build(self, plan_id, confirmation_id, *, plans, registry):
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("EvidencePlanPreparationRegistry is required.")
        plan = self._one(plans, "plan_id", plan_id, "CHANNEL_ISOLATION_PLAN")
        if plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError(
                f"CHANNEL_ISOLATION_PLAN_NOT_READY: {plan.plan_id} is "
                f"{plan.status.value}."
            )
        if plan.test_type is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION:
            raise ValueError(
                f"CHANNEL_ISOLATION_PLAN_TYPE_INVALID: {plan.plan_id}."
            )
        record = self._one(
            registry.records,
            "confirmation_input.confirmation_id",
            confirmation_id,
            "CHANNEL_ISOLATION_PREPARATION",
        )
        value = record.confirmation_input
        if value.plan_id != plan.plan_id:
            raise ValueError("CHANNEL_ISOLATION_PREPARATION_PLAN_MISMATCH.")
        if value.plan_contract_fingerprint != evidence_acquisition_plan_fingerprint(plan):
            raise ValueError("CHANNEL_ISOLATION_PLAN_FINGERPRINT_MISMATCH.")
        confirmed = record.all_prerequisites_status is not None
        return ChannelIsolationGuidedExecutionJourney(
            plan=plan,
            preparation_record=record,
            preparation_status=(
                "PREPARATION_USER_CONFIRMED"
                if confirmed else "PREPARATION_INCOMPLETE"
            ),
            checklist=ChannelIsolationExecutionChecklist(
                required_inputs=plan.required_inputs,
                independent_variables=plan.independent_variables,
                controlled_variables=plan.controlled_variables,
                measurements=plan.measurements_to_capture,
                expected_observations=plan.expected_observations,
                instructions=plan.instructions,
                success_criteria=plan.success_criteria,
                failure_criteria=plan.failure_criteria,
                limitations=plan.limitations,
            ),
            user_action_state=(
                "DECLARE_EXPERIMENT_SEPARATELY"
                if confirmed else "REVIEW_PREPARATION_DECLARATION"
            ),
        )

    @staticmethod
    def _one(values, path, expected, prefix):
        def identity(value):
            current = value
            for part in path.split("."):
                current = getattr(current, part)
            return current
        matches = tuple(value for value in values if identity(value) == expected)
        if not matches:
            raise ValueError(f"{prefix}_UNKNOWN: {expected}.")
        if len(matches) != 1:
            raise ValueError(f"{prefix}_AMBIGUOUS: {expected}.")
        return matches[0]
