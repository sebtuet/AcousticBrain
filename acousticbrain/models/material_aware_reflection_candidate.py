from dataclasses import dataclass
from enum import Enum
from math import isfinite


class ReflectionCandidateGeometricStatus(Enum):
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"


class MaterialAssessment(Enum):
    UNKNOWN = "UNKNOWN"
    COMPATIBLE = "COMPATIBLE"
    WEAKLY_INCOMPATIBLE = "WEAKLY_INCOMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"


class ReflectionCandidateStatus(Enum):
    REJECTED = "REJECTED"
    CANDIDATE = "CANDIDATE"
    STRONG_CANDIDATE = "STRONG_CANDIDATE"


class ReflectionCandidateCausalityStatus(Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class ReflectionCandidateEligibilityImpact(Enum):
    NONE = "NONE"


@dataclass(frozen=True)
class ReflectionCandidateEvidenceLink:
    code: str
    source_analysis: str
    source_id: str
    fact_code: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (
                self.code,
                self.source_analysis,
                self.source_id,
                self.fact_code,
            )
        ):
            raise ValueError("Reflection-candidate evidence links require identifiers.")


@dataclass(frozen=True)
class ReflectionCandidateAssessment:
    candidate_id: str
    correlation_id: str | None
    path_id: str
    surface_id: str
    region_id: str | None
    observed_event_id: str | None
    geometric_temporal_score: float
    geometric_confidence: float | None
    geometric_status: ReflectionCandidateGeometricStatus
    material_assessment: MaterialAssessment
    material_confidence: float | None
    material_id: str | None
    assignment_id: str | None
    catalog_entry_id: str | None
    overall_compatibility_score: float
    informative_rank: int | None
    status: ReflectionCandidateStatus
    causality_status: ReflectionCandidateCausalityStatus
    eligibility_impact: ReflectionCandidateEligibilityImpact
    evidence_links: tuple[ReflectionCandidateEvidenceLink, ...]
    limitations: tuple[str, ...]
    provenance_codes: tuple[str, ...]
    rules_applied: tuple[str, ...]

    def __post_init__(self):
        required_ids = (self.candidate_id, self.path_id, self.surface_id)
        if any(not isinstance(value, str) or not value.strip() for value in required_ids):
            raise ValueError("Reflection-candidate identifiers are required.")
        for value in (self.correlation_id, self.region_id, self.observed_event_id):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError("Optional reflection-candidate identifiers cannot be empty.")
        for value in (self.geometric_temporal_score, self.overall_compatibility_score):
            if not isfinite(value) or not 0.0 <= value <= 100.0:
                raise ValueError("Reflection-candidate scores must be bounded.")
        if self.overall_compatibility_score > self.geometric_temporal_score:
            raise ValueError("Material evidence cannot exceed geometric compatibility.")
        if (
            self.material_assessment is MaterialAssessment.UNKNOWN
            and self.overall_compatibility_score != self.geometric_temporal_score
        ):
            raise ValueError("Unknown material evidence must be score-neutral.")
        for confidence in (self.geometric_confidence, self.material_confidence):
            if confidence is not None and (
                not isfinite(confidence) or not 0.0 <= confidence <= 100.0
            ):
                raise ValueError("Reflection-candidate confidence must be bounded.")
        if self.geometric_status is ReflectionCandidateGeometricStatus.REJECTED:
            if self.status is not ReflectionCandidateStatus.REJECTED:
                raise ValueError("A geometrically rejected path must remain rejected.")
            if self.informative_rank is not None:
                raise ValueError("Rejected paths cannot receive an informative rank.")
        elif self.informative_rank is None or self.informative_rank < 1:
            raise ValueError("Accepted candidates require a positive informative rank.")
        if self.causality_status is not ReflectionCandidateCausalityStatus.NOT_ESTABLISHED:
            raise ValueError("Material ranking cannot establish causality.")
        if self.eligibility_impact is not ReflectionCandidateEligibilityImpact.NONE:
            raise ValueError("Material ranking cannot affect eligibility.")
        typed_collections = (
            (self.evidence_links, ReflectionCandidateEvidenceLink),
            (self.limitations, str),
            (self.provenance_codes, str),
            (self.rules_applied, str),
        )
        for collection, expected in typed_collections:
            if not isinstance(collection, tuple) or any(
                not isinstance(item, expected) or (expected is str and not item.strip())
                for item in collection
            ):
                raise ValueError("Reflection-candidate trace fields must be typed tuples.")


@dataclass(frozen=True)
class MaterialAwareReflectionCandidateAnalysis:
    candidates: tuple[ReflectionCandidateAssessment, ...]
    source_analysis_codes: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.candidates, tuple) or any(
            not isinstance(item, ReflectionCandidateAssessment)
            for item in self.candidates
        ):
            raise ValueError("Material-aware candidates must be a typed tuple.")
        if any(
            not isinstance(values, tuple)
            for values in (self.source_analysis_codes, self.applied_rule_codes)
        ):
            raise ValueError("Material-aware analysis trace fields must be tuples.")
