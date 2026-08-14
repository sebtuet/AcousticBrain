from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedReasoningPremise:
    premise_id: str
    source_type: str
    source_id: str
    statement: str
    role: str


@dataclass(frozen=True)
class PresentedInferenceStep:
    step_id: str
    rule_id: str
    input_premise_ids: tuple[str, ...]
    output_code: str
    statement: str


@dataclass(frozen=True)
class PresentedDeterministicAcousticReasoning:
    reasoning_id: str
    category: str
    title: str
    conclusion: str
    confidence: float | None
    observation_ids: tuple[str, ...]
    premises: tuple[PresentedReasoningPremise, ...]
    inference_steps: tuple[PresentedInferenceStep, ...]
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    compatible_hypothesis_ids: tuple[str, ...]
    excluded_conclusions: tuple[str, ...]
    upstream_source_ids: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class PresentedDeterministicAcousticReasoningReport:
    reasonings: tuple[PresentedDeterministicAcousticReasoning, ...]

    def to_dict(self):
        return {"reasonings": tuple(item.to_dict() for item in self.reasonings)}


class DeterministicAcousticReasoningPresenter:
    def present(self, context):
        synthesis = getattr(
            context, "deterministic_acoustic_reasoning_synthesis", None
        )
        if synthesis is None:
            return None
        return PresentedDeterministicAcousticReasoningReport(
            reasonings=tuple(
                PresentedDeterministicAcousticReasoning(
                    reasoning_id=item.reasoning_id,
                    category=item.category.value,
                    title=item.title,
                    conclusion=item.conclusion.value,
                    confidence=item.confidence,
                    observation_ids=item.observation_ids,
                    premises=tuple(
                        PresentedReasoningPremise(
                            premise_id=premise.premise_id,
                            source_type=premise.source_type.value,
                            source_id=premise.source_id,
                            statement=premise.statement,
                            role=premise.role.value,
                        )
                        for premise in item.premises
                    ),
                    inference_steps=tuple(
                        PresentedInferenceStep(
                            step_id=step.step_id,
                            rule_id=step.rule_id,
                            input_premise_ids=step.input_premise_ids,
                            output_code=step.output_code,
                            statement=step.statement,
                        )
                        for step in item.inference_steps
                    ),
                    supporting_evidence=item.supporting_evidence,
                    contradicting_evidence=item.contradicting_evidence,
                    limitations=item.limitations,
                    compatible_hypothesis_ids=item.compatible_hypothesis_ids,
                    excluded_conclusions=item.excluded_conclusions,
                    upstream_source_ids=item.upstream_source_ids,
                )
                for item in synthesis.reasonings
            )
        )
