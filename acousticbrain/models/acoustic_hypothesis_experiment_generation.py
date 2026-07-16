from dataclasses import dataclass
from enum import Enum, IntEnum
from math import isfinite


class GeneratedHypothesisStatus(Enum):
    PLAUSIBLE = "PLAUSIBLE"
    WEAKLY_PLAUSIBLE = "WEAKLY_PLAUSIBLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONTRADICTED = "CONTRADICTED"


class GeneratedExperimentType(Enum):
    LEFT_SPEAKER_FORWARD = "LEFT_SPEAKER_FORWARD"
    LEFT_SPEAKER_BACKWARD = "LEFT_SPEAKER_BACKWARD"
    RIGHT_SPEAKER_FORWARD = "RIGHT_SPEAKER_FORWARD"
    RIGHT_SPEAKER_BACKWARD = "RIGHT_SPEAKER_BACKWARD"
    BOTH_SPEAKERS_FORWARD = "BOTH_SPEAKERS_FORWARD"
    BOTH_SPEAKERS_BACKWARD = "BOTH_SPEAKERS_BACKWARD"
    LEFT_TOE_IN_INCREASE = "LEFT_TOE_IN_INCREASE"
    LEFT_TOE_IN_DECREASE = "LEFT_TOE_IN_DECREASE"
    RIGHT_TOE_IN_INCREASE = "RIGHT_TOE_IN_INCREASE"
    RIGHT_TOE_IN_DECREASE = "RIGHT_TOE_IN_DECREASE"
    BOTH_TOE_IN_INCREASE = "BOTH_TOE_IN_INCREASE"
    BOTH_TOE_IN_DECREASE = "BOTH_TOE_IN_DECREASE"
    LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION = (
        "LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION"
    )
    RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION = (
        "RIGHT_FIRST_REFLECTION_TEMPORARY_ABSORPTION"
    )
    FRONT_WALL_TEMPORARY_ABSORPTION = "FRONT_WALL_TEMPORARY_ABSORPTION"
    REAR_LISTENING_AREA_TEMPORARY_ABSORPTION = (
        "REAR_LISTENING_AREA_TEMPORARY_ABSORPTION"
    )
    LISTENING_POSITION_FORWARD = "LISTENING_POSITION_FORWARD"
    LISTENING_POSITION_BACKWARD = "LISTENING_POSITION_BACKWARD"
    LISTENING_POSITION_MULTI_POINT = "LISTENING_POSITION_MULTI_POINT"


class ExpectedObservationOutcome(Enum):
    SUPPORTING = "SUPPORTING"
    CONTRADICTING = "CONTRADICTING"
    NEUTRAL = "NEUTRAL"
    INCONCLUSIVE = "INCONCLUSIVE"


class GeneratedExperimentReversibility(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class GeneratedExperimentDifficulty(IntEnum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


@dataclass(frozen=True)
class ExpectedExperimentalObservation:
    observation_code: str
    outcome: ExpectedObservationOutcome
    measured_fact_codes: tuple[str, ...]

    def __post_init__(self):
        if not self.observation_code:
            raise ValueError("Expected-observation code is required.")
        if not isinstance(self.measured_fact_codes, tuple):
            raise ValueError("Expected-observation facts must be a tuple.")


@dataclass(frozen=True)
class GeneratedAcousticExperiment:
    candidate_id: str
    hypothesis_code: str
    experiment_type: GeneratedExperimentType
    target: str
    movement_axis: str | None
    movement_direction: str | None
    step_distance_m: float | None
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    expected_observations: tuple[ExpectedExperimentalObservation, ...]
    expected_frequency_regions: tuple[tuple[float, float], ...]
    expected_time_regions: tuple[tuple[float, float], ...]
    information_value: float
    reversibility: GeneratedExperimentReversibility
    difficulty: GeneratedExperimentDifficulty
    blocking_reasons: tuple[str, ...]
    rationale_codes: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        if not self.candidate_id or not self.hypothesis_code or not self.target:
            raise ValueError("Generated-experiment identifiers are required.")
        collections = (
            self.modified_variables,
            self.controlled_variables,
            self.required_measurements,
            self.expected_observations,
            self.expected_frequency_regions,
            self.expected_time_regions,
            self.blocking_reasons,
            self.rationale_codes,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Generated-experiment collections must be tuples.")
        if len(self.modified_variables) != 1:
            raise ValueError("A generated experiment must modify exactly one variable.")
        if set(self.modified_variables) & set(self.controlled_variables):
            raise ValueError("Modified and controlled variables must be disjoint.")
        if self.required_measurements != ("LEFT", "RIGHT", "STEREO"):
            raise ValueError("Generated experiments require LEFT, RIGHT and STEREO.")
        if self.step_distance_m is not None and (
            not isfinite(self.step_distance_m) or self.step_distance_m <= 0.0
        ):
            raise ValueError("A structured movement distance must be positive.")
        if not isfinite(self.information_value) or not 0.0 <= self.information_value <= 100.0:
            raise ValueError("Information value must be bounded.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Exploratory generation cannot establish causality.")

    @property
    def expected_observation_codes(self) -> tuple[str, ...]:
        return tuple(item.observation_code for item in self.expected_observations)

    @property
    def eligible(self) -> bool:
        return not self.blocking_reasons


@dataclass(frozen=True)
class GeneratedAcousticHypothesis:
    hypothesis_code: str
    status: GeneratedHypothesisStatus
    supporting_fact_codes: tuple[str, ...]
    contradicting_fact_codes: tuple[str, ...]
    missing_fact_codes: tuple[str, ...]
    experiment_candidate_ids: tuple[str, ...]
    expected_observation_codes: tuple[str, ...]
    rationale_codes: tuple[str, ...]
    uncertainty_reasons: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        collections = (
            self.supporting_fact_codes,
            self.contradicting_fact_codes,
            self.missing_fact_codes,
            self.experiment_candidate_ids,
            self.expected_observation_codes,
            self.rationale_codes,
            self.uncertainty_reasons,
        )
        if not self.hypothesis_code or any(
            not isinstance(value, tuple) for value in collections
        ):
            raise ValueError("Generated-hypothesis structure is invalid.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Exploratory hypotheses cannot establish causality.")


@dataclass(frozen=True)
class AcousticHypothesisExperimentGenerationAnalysis:
    hypotheses: tuple[GeneratedAcousticHypothesis, ...]
    ordered_experiments: tuple[GeneratedAcousticExperiment, ...]
    recommended_candidate_id: str | None
    applied_rule_codes: tuple[str, ...]
    source_analysis_codes: tuple[str, ...]

    def __post_init__(self):
        collections = (
            self.hypotheses,
            self.ordered_experiments,
            self.applied_rule_codes,
            self.source_analysis_codes,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Generation-analysis collections must be tuples.")
        if len(self.hypotheses) > 5 or len(self.ordered_experiments) > 5:
            raise ValueError("Exploratory generation is limited to five results.")
        ids = tuple(item.candidate_id for item in self.ordered_experiments)
        if len(ids) != len(set(ids)):
            raise ValueError("Generated experiment candidates must be unique.")
        if self.recommended_candidate_id is not None:
            recommended = tuple(
                item for item in self.ordered_experiments
                if item.candidate_id == self.recommended_candidate_id
            )
            if len(recommended) != 1 or not recommended[0].eligible:
                raise ValueError("The recommended experiment must be eligible.")
