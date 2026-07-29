import json
from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedEvidenceAcquisitionPlan:
    plan_id: str
    reasoning_id: str
    corrective_action_id: str
    evidence_weight_id: str
    blocking_factor_ids: tuple[str, ...]
    objective: str
    test_type: str
    instructions: tuple[str, ...]
    required_inputs: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    independent_variables: tuple[str, ...]
    measurements_to_capture: tuple[str, ...]
    expected_observations: tuple[str, ...]
    success_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    resulting_evidence_targets: tuple[str, ...]
    priority: str
    estimated_effort: str
    status: str
    limitations: tuple[str, ...]

    def to_dict(self):
        return dict(self.__dict__)


@dataclass(frozen=True)
class PresentedEvidenceAcquisitionPlanReport:
    plans: tuple[PresentedEvidenceAcquisitionPlan, ...]

    _PRIORITY_ORDER = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }
    _EFFORT_ORDER = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
    }

    @property
    def recommended_plan(self):
        ready = tuple(value for value in self.plans if value.status == "READY")
        if not ready:
            return None
        return min(
            ready,
            key=lambda value: (
                self._PRIORITY_ORDER[value.priority],
                self._EFFORT_ORDER[value.estimated_effort],
                value.plan_id,
            ),
        )

    @property
    def recommendation_status(self):
        if not self.plans:
            return "NO_PLAN"
        if self.recommended_plan is None:
            return "ALL_PLANS_BLOCKED"
        return "EXPERIMENT_RECOMMENDED"

    @property
    def selection_justification(self):
        plan = self.recommended_plan
        if plan is None:
            return None
        return (
            f"Selected among READY plans by priority ({plan.priority}), "
            f"then estimated effort ({plan.estimated_effort}), "
            "then stable plan id."
        )

    def to_dict(self):
        return {
            "plans": tuple(value.to_dict() for value in self.plans),
            "recommendation_status": self.recommendation_status,
            "recommended_plan": (
                self.recommended_plan.to_dict()
                if self.recommended_plan is not None
                else None
            ),
            "selection_justification": self.selection_justification,
        }

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class EvidenceAcquisitionPlanPresenter:
    def present(self, context):
        synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
        if synthesis is None:
            return None
        return PresentedEvidenceAcquisitionPlanReport(
            plans=tuple(
                PresentedEvidenceAcquisitionPlan(
                    plan_id=value.plan_id,
                    reasoning_id=value.reasoning_id,
                    corrective_action_id=value.corrective_action_id,
                    evidence_weight_id=value.evidence_weight_id,
                    blocking_factor_ids=value.blocking_factor_ids,
                    objective=value.objective,
                    test_type=value.test_type.value,
                    instructions=value.instructions,
                    required_inputs=value.required_inputs,
                    controlled_variables=value.controlled_variables,
                    independent_variables=value.independent_variables,
                    measurements_to_capture=value.measurements_to_capture,
                    expected_observations=value.expected_observations,
                    success_criteria=value.success_criteria,
                    failure_criteria=value.failure_criteria,
                    resulting_evidence_targets=value.resulting_evidence_targets,
                    priority=value.priority.value,
                    estimated_effort=value.estimated_effort.value,
                    status=value.status.value,
                    limitations=value.limitations,
                )
                for value in synthesis.plans
            )
        )
