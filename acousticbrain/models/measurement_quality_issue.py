from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from .impulse_channel import ImpulseChannel
from .measurement_quality_issue_code import MeasurementQualityIssueCode


MeasurementQualityValue = str | int | float | bool


class MeasurementQualityScope(Enum):
    CHANNEL = "CHANNEL"
    MEASUREMENT_SET = "MEASUREMENT_SET"


class MeasurementQualityTechnicalSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class MeasurementQualityIssue:
    """Fait atomique de qualité technique, sans diagnostic utilisateur."""

    code: MeasurementQualityIssueCode
    scope: MeasurementQualityScope
    channel: ImpulseChannel | None = None
    observed_metrics: Mapping[str, MeasurementQualityValue] = field(
        default_factory=dict
    )
    applied_thresholds: Mapping[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    severity: MeasurementQualityTechnicalSeverity | None = None
    source_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.code, MeasurementQualityIssueCode):
            raise ValueError("Issue code must be a MeasurementQualityIssueCode.")
        if not isinstance(self.scope, MeasurementQualityScope):
            raise ValueError("Issue scope must be a MeasurementQualityScope.")
        if self.channel is not None and not isinstance(
            self.channel, ImpulseChannel
        ):
            raise ValueError("Issue channel must be an ImpulseChannel.")
        if self.severity is not None and not isinstance(
            self.severity, MeasurementQualityTechnicalSeverity
        ):
            raise ValueError(
                "Issue severity must be a technical severity enum."
            )
        if self.scope is MeasurementQualityScope.CHANNEL and self.channel is None:
            raise ValueError("A channel issue requires an ImpulseChannel.")
        if (
            self.scope is MeasurementQualityScope.MEASUREMENT_SET
            and self.channel is not None
        ):
            raise ValueError("A measurement-set issue cannot target one channel.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Issue confidence must be between 0 and 100.")
        if not isinstance(self.source_ids, tuple):
            raise ValueError("Issue source ids must be a tuple.")
        if not self.source_ids or any(
            not isinstance(source, str) or not source.strip()
            for source in self.source_ids
        ):
            raise ValueError("Issue provenance requires non-empty source ids.")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("Issue source ids must be unique.")
        self._validate_mapping(self.observed_metrics, thresholds=False)
        self._validate_mapping(self.applied_thresholds, thresholds=True)
        object.__setattr__(
            self,
            "observed_metrics",
            MappingProxyType(dict(self.observed_metrics)),
        )
        object.__setattr__(
            self,
            "applied_thresholds",
            MappingProxyType(dict(self.applied_thresholds)),
        )

    @staticmethod
    def _validate_mapping(values, *, thresholds):
        for name, value in values.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Quality metric names must be non-empty strings.")
            if thresholds:
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not isfinite(value)
                ):
                    raise ValueError("Applied thresholds must be finite numbers.")
            elif not isinstance(value, (str, int, float, bool)) or (
                isinstance(value, float) and not isfinite(value)
            ):
                raise ValueError("Observed metrics must be finite scalar values.")
