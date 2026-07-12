from dataclasses import dataclass
from math import isfinite

from .reasoning_codes import EvidenceRole


ReasoningValue = str | int | float | bool


@dataclass(frozen=True)
class ReasoningEvidence:
    code: str
    role: EvidenceRole
    fact_code: str
    source_analysis: str
    value: ReasoningValue
    strength: float
    confidence: float
    threshold_codes: tuple[str, ...] = ()
    correlation_codes: tuple[str, ...] = ()

    def __post_init__(self):
        for value, label in (
            (self.code, "Evidence code"),
            (self.fact_code, "Evidence fact code"),
            (self.source_analysis, "Evidence source analysis"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} is required.")
        if not isinstance(self.role, EvidenceRole):
            raise ValueError("Reasoning evidence role is invalid.")
        if not isinstance(self.value, (str, int, float, bool)):
            raise ValueError("Reasoning evidence value must be scalar.")
        if isinstance(self.value, float) and not isfinite(self.value):
            raise ValueError("Reasoning evidence value must be finite.")
        if not isfinite(self.strength) or not isfinite(self.confidence):
            raise ValueError("Reasoning evidence scores must be finite.")
        if not 0.0 <= self.strength <= 100.0:
            raise ValueError("Evidence strength must be between 0 and 100.")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Evidence confidence must be between 0 and 100.")
        for collection in (self.threshold_codes, self.correlation_codes):
            if not isinstance(collection, tuple):
                raise ValueError("Reasoning evidence collections must be tuples.")


@dataclass(frozen=True)
class MissingReasoningFact:
    fact_code: str
    source_analysis: str
    rule_code: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.fact_code, self.source_analysis, self.rule_code)
        ):
            raise ValueError("Missing reasoning facts require stable provenance.")
