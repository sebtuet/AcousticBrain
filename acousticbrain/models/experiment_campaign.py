from dataclasses import dataclass
from enum import Enum
from math import isfinite


class ExperimentCampaignStatus(Enum):
    INCOMPLETE = "INCOMPLETE"
    INCONCLUSIVE = "INCONCLUSIVE"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class ExperimentCampaignMeasurement:
    experiment_id: str
    role: str
    offset_m: float
    state: str

    def __post_init__(self):
        if any(not isinstance(value, str) or not value for value in (
            self.experiment_id, self.role, self.state
        )):
            raise ValueError("Campaign measurement identifiers are required.")
        if not isfinite(self.offset_m):
            raise ValueError("Campaign measurement offset must be finite.")


@dataclass(frozen=True)
class ExperimentCampaignMetric:
    code: str
    reference_value: float
    best_value: float
    improvement: float
    improvement_percent: float
    unit: str
    best_experiment_id: str

    def __post_init__(self):
        if any(not isinstance(value, str) or not value for value in (
            self.code, self.unit, self.best_experiment_id
        )):
            raise ValueError("Campaign metric identifiers are required.")
        if any(not isfinite(value) for value in (
            self.reference_value,
            self.best_value,
            self.improvement,
            self.improvement_percent,
        )):
            raise ValueError("Campaign metric values must be finite.")


@dataclass(frozen=True)
class ExperimentCampaignBranchResult:
    experiment_id: str
    role: str
    offset_m: float
    acoustic_outcome: str
    result_codes: tuple[str, ...]
    reference_value: float | None = None
    observed_value: float | None = None

    def __post_init__(self):
        if any(not isinstance(value, str) or not value for value in (
            self.experiment_id, self.role, self.acoustic_outcome
        )):
            raise ValueError("Campaign branch-result identifiers are required.")
        if not isinstance(self.result_codes, tuple):
            raise ValueError("Campaign branch result codes must be a tuple.")
        if not isfinite(self.offset_m):
            raise ValueError("Campaign branch offset must be finite.")
        if any(
            value is not None and not isfinite(value)
            for value in (self.reference_value, self.observed_value)
        ):
            raise ValueError("Campaign branch metric values must be finite.")


@dataclass(frozen=True)
class ExperimentCampaignTrace:
    trace_id: str
    experiment_ids: tuple[str, ...]
    comparison_result_ids: tuple[str, ...]
    observation_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]


@dataclass(frozen=True)
class ExperimentCampaignAnalysis:
    campaign_code: str
    protocol_id: str
    hypothesis_code: str
    objective_code: str
    status: ExperimentCampaignStatus
    reference_experiment_id: str | None
    measurements: tuple[ExperimentCampaignMeasurement, ...]
    branch_results: tuple[ExperimentCampaignBranchResult, ...]
    result_codes: tuple[str, ...]
    unresolved_discrimination_codes: tuple[str, ...]
    metrics: tuple[ExperimentCampaignMetric, ...]
    next_discrimination_code: str | None
    trace: ExperimentCampaignTrace
    detailed_traceability: bool = False

    def __post_init__(self):
        if any(not value for value in (
            self.campaign_code,
            self.protocol_id,
            self.hypothesis_code,
            self.objective_code,
        )):
            raise ValueError("Campaign identifiers are required.")
        for values in (
            self.measurements,
            self.branch_results,
            self.result_codes,
            self.unresolved_discrimination_codes,
            self.metrics,
        ):
            if not isinstance(values, tuple):
                raise ValueError("Campaign collections must be tuples.")
