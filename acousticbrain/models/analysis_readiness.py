from dataclasses import dataclass

from .impulse_channel import ImpulseChannel
from .measurement_quality_issue import MeasurementQualityIssue
from .measurement_readiness_status import (
    MeasurementAnalysisFamily,
    MeasurementReadinessStatus,
)


@dataclass(frozen=True)
class AnalysisReadiness:
    """Décision d'exploitabilité structurée pour une famille d'analyse."""

    family: MeasurementAnalysisFamily
    status: MeasurementReadinessStatus
    blocking_issues: tuple[MeasurementQualityIssue, ...] = ()
    non_blocking_issues: tuple[MeasurementQualityIssue, ...] = ()
    required_channels: tuple[ImpulseChannel, ...] = ()
    missing_facts: tuple[str, ...] = ()
    confidence: float = 0.0
    applied_rule_codes: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.family, MeasurementAnalysisFamily):
            raise ValueError("Readiness family must be a MeasurementAnalysisFamily.")
        if not isinstance(self.status, MeasurementReadinessStatus):
            raise ValueError("Readiness status must be a MeasurementReadinessStatus.")
        collections = (
            self.blocking_issues,
            self.non_blocking_issues,
            self.required_channels,
            self.missing_facts,
            self.applied_rule_codes,
        )
        if any(not isinstance(collection, tuple) for collection in collections):
            raise ValueError("Readiness collections must be tuples.")
        if any(
            not isinstance(channel, ImpulseChannel)
            for channel in self.required_channels
        ):
            raise ValueError("Required channels must be ImpulseChannel values.")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (*self.missing_facts, *self.applied_rule_codes)
        ):
            raise ValueError("Readiness fact and rule codes must be non-empty.")
        if any(
            issue in self.non_blocking_issues for issue in self.blocking_issues
        ):
            raise ValueError("A readiness issue cannot be blocking and non-blocking.")
        for collection, label in (
            (self.required_channels, "required channels"),
            (self.missing_facts, "missing facts"),
            (self.applied_rule_codes, "applied rules"),
        ):
            if len(collection) != len(set(collection)):
                raise ValueError(f"Readiness {label} must be unique.")
        if not isinstance(self.confidence, (int, float)) or not (
            0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Readiness confidence must be between 0 and 100.")
        expected = (
            MeasurementReadinessStatus.BLOCKED
            if self.blocking_issues or self.missing_facts
            else MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS
            if self.non_blocking_issues
            else MeasurementReadinessStatus.AVAILABLE
        )
        if self.status is not expected:
            raise ValueError("Readiness status must match its structured reasons.")
