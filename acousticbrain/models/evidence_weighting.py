from dataclasses import dataclass
from enum import Enum


class EvidenceWeightLevel(Enum):
    UNAVAILABLE = "UNAVAILABLE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceDimension(Enum):
    EVIDENCE_STRENGTH = "EVIDENCE_STRENGTH"
    SOURCE_CONSISTENCY = "SOURCE_CONSISTENCY"
    DISCRIMINATIVE_POWER = "DISCRIMINATIVE_POWER"
    PARAMETER_COMPLETENESS = "PARAMETER_COMPLETENESS"


class WeightedActionApplicability(Enum):
    APPLICABLE = "APPLICABLE"
    CONDITIONALLY_APPLICABLE = "CONDITIONALLY_APPLICABLE"
    BLOCKED = "BLOCKED"
    ALREADY_TESTED = "ALREADY_TESTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NO_ACTION_REQUIRED = "NO_ACTION_REQUIRED"


class WeightedObjectType(Enum):
    ACTION = "ACTION"
    REASONING = "REASONING"
    OBSERVATION = "OBSERVATION"


@dataclass(frozen=True)
class WeightedObjectReference:
    object_type: WeightedObjectType
    object_id: str

    def __post_init__(self):
        if not isinstance(self.object_type, WeightedObjectType):
            raise ValueError("Weighted object type is invalid.")
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ValueError("Weighted object reference requires a stable id.")


@dataclass(frozen=True)
class EvidenceBlockingFactor:
    factor_id: str
    code: str
    source_object_ids: tuple[str, ...]
    justification: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (self.factor_id, self.code, self.justification)
        ):
            raise ValueError("Blocking factors require structured values.")
        if (
            not isinstance(self.source_object_ids, tuple)
            or not self.source_object_ids
            or len(self.source_object_ids) != len(set(self.source_object_ids))
            or any(not isinstance(value, str) or not value for value in self.source_object_ids)
        ):
            raise ValueError("Blocking factors require unique source references.")


@dataclass(frozen=True)
class EvidenceDimensionCeiling:
    ceiling_id: str
    rule_id: str
    dimension: EvidenceDimension
    maximum: EvidenceWeightLevel
    justification: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (self.ceiling_id, self.rule_id, self.justification)
        ):
            raise ValueError("Evidence ceilings require structured values.")
        if not isinstance(self.dimension, EvidenceDimension) or not isinstance(
            self.maximum, EvidenceWeightLevel
        ):
            raise ValueError("Evidence ceiling dimension is invalid.")


@dataclass(frozen=True)
class EvidenceWeightRuleApplication:
    application_id: str
    rule_id: str
    condition_codes: tuple[str, ...]
    affected_dimensions: tuple[EvidenceDimension, ...]
    source_object_ids: tuple[str, ...]
    justification: str
    limitations: tuple[str, ...]

    def __post_init__(self):
        strings = (self.application_id, self.rule_id, self.justification)
        if any(not isinstance(value, str) or not value for value in strings):
            raise ValueError("Rule applications require structured values.")
        if (
            not isinstance(self.affected_dimensions, tuple)
            or not self.affected_dimensions
            or any(not isinstance(value, EvidenceDimension) for value in self.affected_dimensions)
            or len(self.affected_dimensions) != len(set(self.affected_dimensions))
        ):
            raise ValueError("Rule applications require unique dimensions.")
        for values in (self.condition_codes, self.source_object_ids, self.limitations):
            if (
                not isinstance(values, tuple)
                or len(values) != len(set(values))
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ValueError("Rule application references must be unique tuples.")
        if not self.condition_codes or not self.source_object_ids:
            raise ValueError("Rule applications require conditions and source objects.")


@dataclass(frozen=True)
class DeterministicEvidenceWeight:
    weight_id: str
    evidence_strength: EvidenceWeightLevel
    source_consistency: EvidenceWeightLevel
    discriminative_power: EvidenceWeightLevel
    parameter_completeness: EvidenceWeightLevel
    action_applicability: WeightedActionApplicability
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    blocking_factors: tuple[EvidenceBlockingFactor, ...]
    weighted_object_references: tuple[WeightedObjectReference, ...]
    reasoning_references: tuple[str, ...]
    observation_references: tuple[str, ...]
    action_references: tuple[str, ...]
    ceilings: tuple[EvidenceDimensionCeiling, ...]
    rule_applications: tuple[EvidenceWeightRuleApplication, ...]

    _LEVEL_RANK = {
        EvidenceWeightLevel.UNAVAILABLE: 0,
        EvidenceWeightLevel.LOW: 1,
        EvidenceWeightLevel.MEDIUM: 2,
        EvidenceWeightLevel.HIGH: 3,
    }

    def __post_init__(self):
        if not isinstance(self.weight_id, str) or not self.weight_id:
            raise ValueError("Evidence weights require a stable id.")
        levels = (
            self.evidence_strength,
            self.source_consistency,
            self.discriminative_power,
            self.parameter_completeness,
        )
        if any(not isinstance(value, EvidenceWeightLevel) for value in levels):
            raise ValueError("Evidence dimensions require categorical levels.")
        if not isinstance(self.action_applicability, WeightedActionApplicability):
            raise ValueError("Weighted action applicability is invalid.")
        collections = (
            self.supporting_evidence,
            self.contradicting_evidence,
            self.limitations,
            self.blocking_factors,
            self.weighted_object_references,
            self.reasoning_references,
            self.observation_references,
            self.action_references,
            self.ceilings,
            self.rule_applications,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Evidence-weight collections must be immutable tuples.")
        for values in (
            self.supporting_evidence,
            self.contradicting_evidence,
            self.limitations,
            self.reasoning_references,
            self.observation_references,
            self.action_references,
        ):
            if len(values) != len(set(values)) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise ValueError("Evidence-weight references must be unique strings.")
        if not self.action_references or not self.reasoning_references or not self.observation_references:
            raise ValueError("Evidence weights require action, reasoning and observation references.")
        references = {(item.object_type, item.object_id) for item in self.weighted_object_references}
        expected = {
            *((WeightedObjectType.ACTION, value) for value in self.action_references),
            *((WeightedObjectType.REASONING, value) for value in self.reasoning_references),
            *((WeightedObjectType.OBSERVATION, value) for value in self.observation_references),
        }
        if references != expected or len(references) != len(self.weighted_object_references):
            raise ValueError("Weighted object references must exactly match typed references.")
        actual = {
            EvidenceDimension.EVIDENCE_STRENGTH: self.evidence_strength,
            EvidenceDimension.SOURCE_CONSISTENCY: self.source_consistency,
            EvidenceDimension.DISCRIMINATIVE_POWER: self.discriminative_power,
            EvidenceDimension.PARAMETER_COMPLETENESS: self.parameter_completeness,
        }
        ceiling_dimensions = tuple(value.dimension for value in self.ceilings)
        if len(ceiling_dimensions) != len(set(ceiling_dimensions)):
            raise ValueError("Only one effective ceiling is allowed per dimension.")
        if any(
            self._LEVEL_RANK[actual[value.dimension]] > self._LEVEL_RANK[value.maximum]
            for value in self.ceilings
        ):
            raise ValueError("An evidence dimension exceeds its explicit ceiling.")
        blocked = self.action_applicability is WeightedActionApplicability.BLOCKED
        if blocked and not self.blocking_factors:
            raise ValueError("Blocked applicability requires explicit blocking factors.")
        if self.contradicting_evidence and not any(
            value.code == "CONTRADICTORY_EVIDENCE" for value in self.blocking_factors
        ):
            raise ValueError("Contradictory evidence cannot be hidden.")


@dataclass(frozen=True)
class DeterministicEvidenceWeightingSynthesis:
    weights: tuple[DeterministicEvidenceWeight, ...] = ()

    def __post_init__(self):
        if not isinstance(self.weights, tuple) or any(
            not isinstance(value, DeterministicEvidenceWeight) for value in self.weights
        ):
            raise ValueError("Evidence weighting synthesis requires immutable weights.")
        identifiers = tuple(value.weight_id for value in self.weights)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Evidence weight ids must be unique.")
