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

    def to_dict(self):
        return {"plans": tuple(value.to_dict() for value in self.plans)}

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
