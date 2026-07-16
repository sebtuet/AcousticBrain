from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .listening_position_sampling_protocol import REQUIRED_POSITION_MEASUREMENTS


class ListeningPositionCampaignPlanStatus(Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ListeningPositionCampaignStepExecutionStatus(Enum):
    PLANNED = "PLANNED"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True)
class ListeningPositionCampaignStep:
    step_id: str
    order_index: int
    position_code: str
    position_role: str
    longitudinal_offset_m: float | None
    lateral_offset_m: float | None
    vertical_offset_m: float | None
    parent_step_id: str | None
    reference_step_id: str | None
    reference_experiment_id: str | None
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    comparability_requirements: tuple[str, ...]
    execution_status: ListeningPositionCampaignStepExecutionStatus

    def __post_init__(self):
        if (
            not isinstance(self.step_id, str)
            or not self.step_id.startswith("campaign-step.")
            or not isinstance(self.position_code, str)
            or not self.position_code
            or self.position_role not in {"REFERENCE", "FORWARD", "BACKWARD"}
        ):
            raise ValueError("Campaign-step identity and role are invalid.")
        if (
            not isinstance(self.order_index, int)
            or isinstance(self.order_index, bool)
            or self.order_index < 1
        ):
            raise ValueError("Campaign-step order must be positive.")
        for value in (
            self.longitudinal_offset_m,
            self.lateral_offset_m,
            self.vertical_offset_m,
        ):
            if value is not None and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(value)
            ):
                raise ValueError("Campaign-step offsets must be finite when present.")
        collections = (
            self.modified_variables,
            self.controlled_variables,
            self.required_measurements,
            self.comparability_requirements,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Campaign-step collections must be tuples.")
        if self.modified_variables != ("LISTENING_POSITION",):
            raise ValueError("Campaign steps modify LISTENING_POSITION only.")
        if (
            not self.controlled_variables
            or set(self.modified_variables) & set(self.controlled_variables)
            or self.required_measurements != REQUIRED_POSITION_MEASUREMENTS
            or not self.comparability_requirements
        ):
            raise ValueError("Campaign-step controls and measurements are incomplete.")
        for relation in (
            self.parent_step_id,
            self.reference_step_id,
            self.reference_experiment_id,
        ):
            if relation is not None and (
                not isinstance(relation, str) or not relation
            ):
                raise ValueError("Campaign-step relations are invalid.")


@dataclass(frozen=True)
class ListeningPositionCampaignPlan:
    campaign_plan_id: str
    protocol_id: str | None
    protocol_version: int | None
    source_candidate_id: str
    source_hypothesis_code: str
    reference_experiment_id: str | None
    steps: tuple[ListeningPositionCampaignStep, ...]
    status: ListeningPositionCampaignPlanStatus
    blocking_reasons: tuple[str, ...]
    causality_status: str
    comparability_rule: str | None
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    reference_selection_rule_codes: tuple[str, ...]

    def __post_init__(self):
        collections = (
            self.steps,
            self.blocking_reasons,
            self.controlled_variables,
            self.required_measurements,
            self.reference_selection_rule_codes,
        )
        if (
            not self.campaign_plan_id
            or not self.source_candidate_id
            or not self.source_hypothesis_code
            or any(not isinstance(value, tuple) for value in collections)
        ):
            raise ValueError("Listening-position campaign plan is invalid.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("A campaign plan cannot establish causality.")
        if self.protocol_version is not None and (
            not isinstance(self.protocol_version, int)
            or isinstance(self.protocol_version, bool)
            or self.protocol_version < 1
        ):
            raise ValueError("Campaign protocol version must be positive.")
        if self.status is ListeningPositionCampaignPlanStatus.READY:
            if (
                self.blocking_reasons
                or not self.protocol_id
                or self.protocol_version is None
                or not self.reference_experiment_id
                or not self.steps
                or not self.comparability_rule
                or self.required_measurements != REQUIRED_POSITION_MEASUREMENTS
                or not self.controlled_variables
            ):
                raise ValueError("A READY campaign plan must be directly executable.")
            if any(
                item.execution_status
                is not ListeningPositionCampaignStepExecutionStatus.PLANNED
                for item in self.steps
            ):
                raise ValueError("READY campaign steps must be PLANNED.")
        elif self.status is ListeningPositionCampaignPlanStatus.BLOCKED:
            if not self.blocking_reasons:
                raise ValueError("A BLOCKED campaign plan requires structured reasons.")
            if any(
                item.execution_status
                is not ListeningPositionCampaignStepExecutionStatus.BLOCKED
                for item in self.steps
            ):
                raise ValueError("BLOCKED campaign steps must remain blocked.")
        self._validate_steps()

    def _validate_steps(self):
        if any(
            not isinstance(item, ListeningPositionCampaignStep)
            for item in self.steps
        ):
            raise ValueError("Campaign plan steps must use the structured model.")
        step_ids = tuple(item.step_id for item in self.steps)
        position_codes = tuple(item.position_code for item in self.steps)
        orders = tuple(item.order_index for item in self.steps)
        if (
            len(step_ids) != len(set(step_ids))
            or len(position_codes) != len(set(position_codes))
            or orders != tuple(range(1, len(orders) + 1))
        ):
            raise ValueError("Campaign steps must be unique and totally ordered.")
        known = set(step_ids)
        order_by_id = {item.step_id: item.order_index for item in self.steps}
        references = tuple(item for item in self.steps if item.position_role == "REFERENCE")
        for step in self.steps:
            if step.parent_step_id is not None and (
                step.parent_step_id not in known
                or order_by_id[step.parent_step_id] >= step.order_index
            ):
                raise ValueError("Campaign parent relations are invalid or cyclic.")
            if step.reference_step_id is not None and step.reference_step_id not in known:
                raise ValueError("Campaign reference relations target an unknown step.")
            if (
                step.controlled_variables != self.controlled_variables
                or step.required_measurements != self.required_measurements
                or step.reference_experiment_id != self.reference_experiment_id
                or (
                    self.comparability_rule is not None
                    and step.comparability_requirements
                    != (self.comparability_rule,)
                )
            ):
                raise ValueError("Campaign step requirements must match the plan.")
        if self.steps and len(references) != 1:
            raise ValueError("A campaign plan requires exactly one reference step.")
        if references:
            reference = references[0]
            if (
                reference.longitudinal_offset_m != 0.0
                or reference.lateral_offset_m not in (None, 0.0)
                or reference.vertical_offset_m not in (None, 0.0)
                or reference.parent_step_id is not None
                or reference.reference_step_id != reference.step_id
            ):
                raise ValueError("The campaign reference step is inconsistent.")
            for step in self.steps:
                if step.position_role == "FORWARD" and not (
                    step.longitudinal_offset_m is not None
                    and step.longitudinal_offset_m > 0.0
                ):
                    raise ValueError("FORWARD campaign steps require a positive offset.")
                if step.position_role == "BACKWARD" and not (
                    step.longitudinal_offset_m is not None
                    and step.longitudinal_offset_m < 0.0
                ):
                    raise ValueError("BACKWARD campaign steps require a negative offset.")
                if step.position_role != "REFERENCE" and (
                    step.reference_step_id != reference.step_id
                ):
                    raise ValueError("Campaign steps must share the declared reference.")
