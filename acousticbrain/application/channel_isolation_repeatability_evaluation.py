"""Versioned numerical repeatability projection for CHANNEL_ISOLATION captures."""

from dataclasses import dataclass
from enum import Enum

from .channel_isolation_repeatability import ChannelIsolationRepeatabilityService


class RepeatabilityEvaluationStatus(str, Enum):
    REPEATABILITY_ACCEPTABLE_IN_BAND = "REPEATABILITY_ACCEPTABLE_IN_BAND"
    REPEATABILITY_UNCERTAIN = "REPEATABILITY_UNCERTAIN"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class RepeatabilityEvaluationContract:
    """A declared numerical convention, not a physical-stability conclusion."""

    contract_id: str = "repeatability_contract.v1"
    lower_hz: float = 40.0
    upper_hz: float = 200.0
    threshold_db: float = 3.0

    def __post_init__(self):
        if not self.contract_id:
            raise ValueError("Repeatability contract identifier is required.")
        if self.lower_hz <= 0 or self.upper_hz <= self.lower_hz:
            raise ValueError("Repeatability evaluation band must be increasing and positive.")
        if self.threshold_db < 0:
            raise ValueError("Repeatability threshold must be non-negative.")


@dataclass(frozen=True)
class ChannelIsolationRepeatabilityEvaluation:
    experiment_id: str
    contract_id: str
    lower_hz: float
    upper_hz: float
    threshold_db: float
    left_maximum_difference_db: float | None
    left_maximum_difference_frequency_hz: float | None
    right_maximum_difference_db: float | None
    right_maximum_difference_frequency_hz: float | None
    status: RepeatabilityEvaluationStatus
    causality_status: str = "NOT_ESTABLISHED"
    physical_stability_limit: str = (
        "This numerical result does not prove that the microphone or loudspeakers "
        "remained physically unchanged."
    )
    user_declaration_limit: str = (
        "An unchanged-position statement remains a user declaration and is not "
        "independently verified."
    )


class ChannelIsolationRepeatabilityEvaluationService:
    """Applies one declared band/threshold contract without changing reasoning."""

    def __init__(self, repeatability_service=None):
        self.repeatability_service = (
            repeatability_service or ChannelIsolationRepeatabilityService()
        )

    def evaluate(self, descriptors, *, contract=None):
        contract = contract or RepeatabilityEvaluationContract()
        results = []
        for facts in self.repeatability_service.band_facts(
            descriptors,
            lower_hz=contract.lower_hz,
            upper_hz=contract.upper_hz,
        ):
            values = (
                facts.left_maximum_difference_db,
                facts.right_maximum_difference_db,
            )
            if any(value is None for value in values):
                status = RepeatabilityEvaluationStatus.NOT_EVALUABLE
            elif all(value <= contract.threshold_db for value in values):
                status = RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
            else:
                status = RepeatabilityEvaluationStatus.REPEATABILITY_UNCERTAIN
            results.append(ChannelIsolationRepeatabilityEvaluation(
                experiment_id=facts.experiment_id,
                contract_id=contract.contract_id,
                lower_hz=contract.lower_hz,
                upper_hz=contract.upper_hz,
                threshold_db=contract.threshold_db,
                left_maximum_difference_db=facts.left_maximum_difference_db,
                left_maximum_difference_frequency_hz=(
                    facts.left_maximum_difference_frequency_hz
                ),
                right_maximum_difference_db=facts.right_maximum_difference_db,
                right_maximum_difference_frequency_hz=(
                    facts.right_maximum_difference_frequency_hz
                ),
                status=status,
            ))
        return tuple(results)
