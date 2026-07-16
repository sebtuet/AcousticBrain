from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedListeningPositionCampaignStep:
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
    execution_status: str


@dataclass(frozen=True)
class PresentedListeningPositionCampaignPlan:
    campaign_plan_id: str
    protocol_id: str | None
    protocol_version: int | None
    source_candidate_id: str
    source_hypothesis_code: str
    reference_experiment_id: str | None
    steps: tuple[PresentedListeningPositionCampaignStep, ...]
    status: str
    blocking_reasons: tuple[str, ...]
    causality_status: str
    comparability_rule: str | None
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    reference_selection_rule_codes: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class ListeningPositionCampaignPlanPresenter:
    def present(self, context):
        plan = getattr(context, "listening_position_campaign_plan", None)
        if plan is None:
            return None
        return PresentedListeningPositionCampaignPlan(
            campaign_plan_id=plan.campaign_plan_id,
            protocol_id=plan.protocol_id,
            protocol_version=plan.protocol_version,
            source_candidate_id=plan.source_candidate_id,
            source_hypothesis_code=plan.source_hypothesis_code,
            reference_experiment_id=plan.reference_experiment_id,
            steps=tuple(
                PresentedListeningPositionCampaignStep(
                    step_id=item.step_id,
                    order_index=item.order_index,
                    position_code=item.position_code,
                    position_role=item.position_role,
                    longitudinal_offset_m=item.longitudinal_offset_m,
                    lateral_offset_m=item.lateral_offset_m,
                    vertical_offset_m=item.vertical_offset_m,
                    parent_step_id=item.parent_step_id,
                    reference_step_id=item.reference_step_id,
                    reference_experiment_id=item.reference_experiment_id,
                    modified_variables=item.modified_variables,
                    controlled_variables=item.controlled_variables,
                    required_measurements=item.required_measurements,
                    comparability_requirements=item.comparability_requirements,
                    execution_status=item.execution_status.value,
                )
                for item in plan.steps
            ),
            status=plan.status.value,
            blocking_reasons=plan.blocking_reasons,
            causality_status=plan.causality_status,
            comparability_rule=plan.comparability_rule,
            controlled_variables=plan.controlled_variables,
            required_measurements=plan.required_measurements,
            reference_selection_rule_codes=plan.reference_selection_rule_codes,
        )
