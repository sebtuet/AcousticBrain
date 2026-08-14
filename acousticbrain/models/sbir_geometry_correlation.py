from dataclasses import dataclass
from math import isfinite

from .geometry_sbir_candidate import GeometrySBIRCandidate
from .peak import Peak


@dataclass(frozen=True)
class SBIRGeometryCorrelation:
    code: str
    candidate: GeometrySBIRCandidate
    observed_dip: Peak
    frequency_error_hz: float
    frequency_error_percent: float
    match_score: float
    confidence: float
    source_analysis_codes: tuple[str, ...]
    provenance_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("SBIR geometry correlation code is required.")
        if not isinstance(self.candidate, GeometrySBIRCandidate):
            raise ValueError("SBIR geometry correlation requires a prediction.")
        if not isinstance(self.observed_dip, Peak):
            raise ValueError("SBIR geometry correlation requires an observed dip.")
        for value in (self.frequency_error_hz, self.frequency_error_percent):
            if not isfinite(value) or value < 0.0:
                raise ValueError("SBIR frequency error must be non-negative.")
        for value in (self.match_score, self.confidence):
            if not isfinite(value) or not 0.0 <= value <= 100.0:
                raise ValueError("SBIR correlation scores must be bounded.")
        if not self.source_analysis_codes or not isinstance(
            self.source_analysis_codes, tuple
        ):
            raise ValueError("SBIR correlation sources are required.")
        if not isinstance(self.provenance_codes, tuple):
            raise ValueError("SBIR correlation provenance must be a tuple.")


@dataclass(frozen=True)
class SBIRGeometryCorrelationAnalysis:
    correlations: tuple[SBIRGeometryCorrelation, ...]
    best_match: SBIRGeometryCorrelation | None
    unmatched_candidate_ids: tuple[str, ...]
    evaluated_candidate_count: int
    observed_dip_count: int
    confidence: float
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.correlations, tuple) or any(
            not isinstance(item, SBIRGeometryCorrelation)
            for item in self.correlations
        ):
            raise ValueError("SBIR geometry correlations must be a typed tuple.")
        if self.best_match is not None and self.best_match not in self.correlations:
            raise ValueError("SBIR best match must belong to correlations.")
        collections = (
            self.unmatched_candidate_ids,
            self.source_analysis_codes,
            self.applied_rule_codes,
        )
        if any(not isinstance(values, tuple) for values in collections):
            raise ValueError("SBIR correlation collections must be tuples.")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in (self.evaluated_candidate_count, self.observed_dip_count)
        ):
            raise ValueError("SBIR correlation counts must be non-negative.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("SBIR correlation confidence must be bounded.")
