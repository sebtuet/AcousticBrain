from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedCorrectiveActionJustification:
    justification_id: str
    rule_id: str
    reasoning_id: str
    conclusion_code: str
    statement: str


@dataclass(frozen=True)
class PresentedDeterministicCorrectiveAction:
    action_id: str
    category: str
    action_type: str
    target_id: str
    title: str
    objective: str
    description: str
    applicability: str
    priority: str
    confidence: float | None
    source_reasoning_ids: tuple[str, ...]
    source_observation_ids: tuple[str, ...]
    upstream_source_ids: tuple[str, ...]
    justifications: tuple[PresentedCorrectiveActionJustification, ...]
    preconditions: tuple[str, ...]
    known_parameters: tuple[tuple[str, str], ...]
    derivable_parameters: tuple[str, ...]
    required_missing_parameters: tuple[str, ...]
    forbidden_to_invent_parameters: tuple[str, ...]
    known_risks: tuple[str, ...]
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    stop_criteria: tuple[str, ...]
    contradictions: tuple[str, ...]
    limitations: tuple[str, ...]
    traceability_status: str
    compatible_protocol_ids: tuple[str, ...]
    compatible_plan_ids: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class PresentedDeterministicCorrectiveActionReport:
    actions: tuple[PresentedDeterministicCorrectiveAction, ...]

    def to_dict(self):
        return {"actions": tuple(item.to_dict() for item in self.actions)}


class DeterministicCorrectiveActionPresenter:
    def present(self, context):
        synthesis = getattr(context, "deterministic_corrective_action_synthesis", None)
        if synthesis is None:
            return None
        return PresentedDeterministicCorrectiveActionReport(
            actions=tuple(
                PresentedDeterministicCorrectiveAction(
                    action_id=item.action_id,
                    category=item.category.value,
                    action_type=item.action_type.value,
                    target_id=item.target_id,
                    title=item.title,
                    objective=item.objective,
                    description=item.description,
                    applicability=item.applicability.value,
                    priority=item.priority.value,
                    confidence=item.confidence,
                    source_reasoning_ids=item.source_reasoning_ids,
                    source_observation_ids=item.source_observation_ids,
                    upstream_source_ids=item.upstream_source_ids,
                    justifications=tuple(
                        PresentedCorrectiveActionJustification(
                            justification_id=value.justification_id,
                            rule_id=value.rule_id,
                            reasoning_id=value.reasoning_id,
                            conclusion_code=value.conclusion_code,
                            statement=value.statement,
                        )
                        for value in item.justifications
                    ),
                    preconditions=item.preconditions,
                    known_parameters=item.known_parameters,
                    derivable_parameters=item.derivable_parameters,
                    required_missing_parameters=item.required_missing_parameters,
                    forbidden_to_invent_parameters=(
                        item.forbidden_to_invent_parameters
                    ),
                    known_risks=item.known_risks,
                    constraints=item.constraints,
                    success_criteria=item.success_criteria,
                    stop_criteria=item.stop_criteria,
                    contradictions=item.contradictions,
                    limitations=item.limitations,
                    traceability_status=item.traceability_status.value,
                    compatible_protocol_ids=item.compatible_protocol_ids,
                    compatible_plan_ids=item.compatible_plan_ids,
                )
                for item in synthesis.actions
            )
        )
