from dataclasses import dataclass
from enum import Enum
from math import isfinite


class AcousticObservationCategory(Enum):
    LOW_FREQUENCY = "LOW_FREQUENCY"
    EARLY_REFLECTIONS = "EARLY_REFLECTIONS"
    DECAY = "DECAY"
    STEREO = "STEREO"
    CLARITY = "CLARITY"
    MEASUREMENT_QUALITY = "MEASUREMENT_QUALITY"
    GENERAL = "GENERAL"


@dataclass(frozen=True)
class AcousticObservation:
    observation_id: str
    category: AcousticObservationCategory
    title: str
    description: str
    confidence: float | None
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    source_analysis_ids: tuple[str, ...]

    _FORBIDDEN_LANGUAGE = (
        "move the speaker",
        "move the speakers",
        "déplacer les enceintes",
        "use a panel",
        "utiliser un panneau",
        "try an eq",
        "essayer un eq",
        "run an experiment",
        "faire une expérience",
        "i recommend",
        "je recommande",
    )

    def __post_init__(self):
        if not isinstance(self.observation_id, str) or not self.observation_id:
            raise ValueError("An acoustic observation requires a stable id.")
        if not isinstance(self.category, AcousticObservationCategory):
            raise ValueError("An acoustic observation requires a category.")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("An acoustic observation requires a title.")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("An acoustic observation requires a description.")
        if self.confidence is not None and (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Observation confidence must be unavailable or bounded.")
        collections = (
            self.supporting_evidence,
            self.contradicting_evidence,
            self.limitations,
            self.source_analysis_ids,
        )
        if not all(isinstance(items, tuple) for items in collections):
            raise ValueError("Acoustic-observation collections must be tuples.")
        if not self.supporting_evidence or not self.source_analysis_ids:
            raise ValueError("An observation requires evidence and source analyses.")
        if any(
            not isinstance(item, str) or not item
            for items in collections
            for item in items
        ):
            raise ValueError("Observation evidence values must be non-empty strings.")
        if any(len(items) != len(set(items)) for items in collections):
            raise ValueError("Observation evidence values must be unique.")
        language = " ".join(
            (
                self.title,
                self.description,
                *self.supporting_evidence,
                *self.contradicting_evidence,
                *self.limitations,
            )
        ).casefold()
        if any(value in language for value in self._FORBIDDEN_LANGUAGE):
            raise ValueError("An observation must remain strictly descriptive.")


@dataclass(frozen=True)
class AcousticObservationSynthesis:
    observations: tuple[AcousticObservation, ...] = ()

    def __post_init__(self):
        if not isinstance(self.observations, tuple) or any(
            not isinstance(item, AcousticObservation) for item in self.observations
        ):
            raise ValueError("Observation synthesis must contain immutable observations.")
        identifiers = tuple(item.observation_id for item in self.observations)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Observation ids must be unique.")
