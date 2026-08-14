from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedEvidenceBlockingFactor:
    factor_id: str
    code: str
    source_object_ids: tuple[str, ...]
    justification: str


@dataclass(frozen=True)
class PresentedEvidenceCeiling:
    ceiling_id: str
    rule_id: str
    dimension: str
    maximum: str
    justification: str


@dataclass(frozen=True)
class PresentedDeterministicEvidenceWeight:
    weight_id: str
    evidence_strength: str
    source_consistency: str
    discriminative_power: str
    parameter_completeness: str
    action_applicability: str
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    blocking_factors: tuple[PresentedEvidenceBlockingFactor, ...]
    weighted_object_references: tuple[str, ...]
    reasoning_references: tuple[str, ...]
    observation_references: tuple[str, ...]
    action_references: tuple[str, ...]
    ceilings: tuple[PresentedEvidenceCeiling, ...]
    applied_rule_ids: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class PresentedDeterministicEvidenceWeightingReport:
    weights: tuple[PresentedDeterministicEvidenceWeight, ...]

    def to_dict(self):
        return {"weights": tuple(value.to_dict() for value in self.weights)}


class DeterministicEvidenceWeightingPresenter:
    def present(self, context):
        synthesis = getattr(context, "deterministic_evidence_weighting_synthesis", None)
        if synthesis is None:
            return None
        return PresentedDeterministicEvidenceWeightingReport(
            weights=tuple(
                PresentedDeterministicEvidenceWeight(
                    weight_id=value.weight_id,
                    evidence_strength=value.evidence_strength.value,
                    source_consistency=value.source_consistency.value,
                    discriminative_power=value.discriminative_power.value,
                    parameter_completeness=value.parameter_completeness.value,
                    action_applicability=value.action_applicability.value,
                    supporting_evidence=value.supporting_evidence,
                    contradicting_evidence=value.contradicting_evidence,
                    limitations=value.limitations,
                    blocking_factors=tuple(
                        PresentedEvidenceBlockingFactor(
                            factor_id=item.factor_id,
                            code=item.code,
                            source_object_ids=item.source_object_ids,
                            justification=item.justification,
                        )
                        for item in value.blocking_factors
                    ),
                    weighted_object_references=tuple(
                        f"{item.object_type.value}:{item.object_id}"
                        for item in value.weighted_object_references
                    ),
                    reasoning_references=value.reasoning_references,
                    observation_references=value.observation_references,
                    action_references=value.action_references,
                    ceilings=tuple(
                        PresentedEvidenceCeiling(
                            ceiling_id=item.ceiling_id,
                            rule_id=item.rule_id,
                            dimension=item.dimension.value,
                            maximum=item.maximum.value,
                            justification=item.justification,
                        )
                        for item in value.ceilings
                    ),
                    applied_rule_ids=tuple(
                        item.rule_id for item in value.rule_applications
                    ),
                )
                for value in synthesis.weights
            )
        )
