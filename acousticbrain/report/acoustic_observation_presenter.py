from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedAcousticObservation:
    observation_id: str
    category: str
    title: str
    description: str
    confidence: float | None
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    source_analysis_ids: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class PresentedAcousticObservationReport:
    observations: tuple[PresentedAcousticObservation, ...]

    def to_dict(self):
        return {
            "observations": tuple(item.to_dict() for item in self.observations)
        }


class AcousticObservationPresenter:
    def present(self, context):
        synthesis = getattr(context, "acoustic_observation_synthesis", None)
        if synthesis is None:
            return None
        return PresentedAcousticObservationReport(
            observations=tuple(
                PresentedAcousticObservation(
                    observation_id=item.observation_id,
                    category=item.category.value,
                    title=item.title,
                    description=item.description,
                    confidence=item.confidence,
                    supporting_evidence=item.supporting_evidence,
                    contradicting_evidence=item.contradicting_evidence,
                    limitations=item.limitations,
                    source_analysis_ids=item.source_analysis_ids,
                )
                for item in synthesis.observations
            )
        )
