from dataclasses import dataclass
from enum import Enum


class AdvisorAudience(Enum):
    GENERAL = "general"
    ENTHUSIAST = "enthusiast"
    ACOUSTICIAN = "acoustician"
    DEVELOPER = "developer"


class AdvisorDetailLevel(Enum):
    CONCISE = "concise"
    STANDARD = "standard"
    TECHNICAL = "technical"


class AdvisorValidationStatus(Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"


@dataclass(frozen=True)
class AdvisorContextObject:
    object_id: str
    object_type: str
    canonical_json: str
    referenced_object_ids: tuple[str, ...]

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (self.object_id, self.object_type, self.canonical_json)
        ):
            raise ValueError("Advisor context objects require stable values.")
        if (
            not isinstance(self.referenced_object_ids, tuple)
            or len(self.referenced_object_ids) != len(set(self.referenced_object_ids))
            or any(not isinstance(value, str) or not value for value in self.referenced_object_ids)
        ):
            raise ValueError("Advisor object references must be unique tuples.")


@dataclass(frozen=True)
class AdvisorDeterministicContext:
    schema_version: str
    project_id: str
    objects: tuple[AdvisorContextObject, ...]
    blocking_factors: tuple[str, ...]
    contradictions: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (self.schema_version, self.project_id)
        ):
            raise ValueError("Advisor context identity is required.")
        if not isinstance(self.objects, tuple) or any(
            not isinstance(value, AdvisorContextObject) for value in self.objects
        ):
            raise ValueError("Advisor context objects must be immutable.")
        object_ids = tuple(value.object_id for value in self.objects)
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("Advisor context object ids must be unique.")
        for values in (self.blocking_factors, self.contradictions, self.limitations):
            if (
                not isinstance(values, tuple)
                or len(values) != len(set(values))
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ValueError("Advisor context facts must be unique tuples.")


@dataclass(frozen=True)
class AdvisorRequest:
    schema_version: str
    request_id: str
    question: str
    requested_audience: AdvisorAudience
    requested_detail_level: AdvisorDetailLevel
    selected_project_id: str
    selected_object_ids: tuple[str, ...]
    deterministic_context: AdvisorDeterministicContext
    provider_configuration_reference: str

    def __post_init__(self):
        strings = (
            self.schema_version,
            self.request_id,
            self.question,
            self.selected_project_id,
            self.provider_configuration_reference,
        )
        if any(not isinstance(value, str) or not value.strip() for value in strings):
            raise ValueError("Advisor requests require stable non-empty values.")
        if not isinstance(self.requested_audience, AdvisorAudience) or not isinstance(
            self.requested_detail_level, AdvisorDetailLevel
        ):
            raise ValueError("Advisor request audience or detail is invalid.")
        if (
            not isinstance(self.selected_object_ids, tuple)
            or len(self.selected_object_ids) != len(set(self.selected_object_ids))
            or any(not isinstance(value, str) or not value for value in self.selected_object_ids)
        ):
            raise ValueError("Selected advisor ids must be a unique tuple.")
        if not isinstance(self.deterministic_context, AdvisorDeterministicContext):
            raise ValueError("Advisor request requires deterministic context.")


@dataclass(frozen=True)
class AdvisorClaim:
    text: str
    supporting_object_ids: tuple[str, ...]
    asserted_action_applicability: tuple[tuple[str, str], ...] = ()
    asserted_weight_dimensions: tuple[tuple[str, str, str], ...] = ()
    asserted_evidence: tuple[str, ...] = ()
    asserted_blocking_factors: tuple[str, ...] = ()
    asserted_contradictions: tuple[str, ...] = ()
    asserted_limitations: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Advisor claims require text.")
        if (
            not isinstance(self.supporting_object_ids, tuple)
            or not self.supporting_object_ids
            or len(self.supporting_object_ids) != len(set(self.supporting_object_ids))
        ):
            raise ValueError("Every advisor claim requires unique provenance.")
        for collection, size in (
            (self.asserted_action_applicability, 2),
            (self.asserted_weight_dimensions, 3),
        ):
            if not isinstance(collection, tuple) or any(
                not isinstance(value, tuple)
                or len(value) != size
                or any(not isinstance(item, str) or not item for item in value)
                for value in collection
            ):
                raise ValueError("Advisor structured assertions are invalid.")
        assertions = (
            self.asserted_evidence,
            self.asserted_blocking_factors,
            self.asserted_contradictions,
            self.asserted_limitations,
        )
        if any(
            not isinstance(values, tuple)
            or len(values) != len(set(values))
            or any(not isinstance(value, str) or not value for value in values)
            for values in assertions
        ):
            raise ValueError("Advisor fact assertions must be unique tuples.")
        if not any(
            (
                self.asserted_action_applicability,
                self.asserted_weight_dimensions,
                *assertions,
            )
        ):
            raise ValueError("Every advisor claim requires a structured fact assertion.")


@dataclass(frozen=True)
class AdvisorProviderOutput:
    answer: str
    referenced_object_ids: tuple[str, ...]
    claims: tuple[AdvisorClaim, ...]
    blocking_factors: tuple[str, ...]
    contradictions: tuple[str, ...]
    limitations: tuple[str, ...]
    proposed_action_ids: tuple[str, ...] = ()
    introduced_scores: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.answer, str) or not self.answer.strip():
            raise ValueError("Advisor provider output requires an answer.")
        collections = (
            self.referenced_object_ids,
            self.claims,
            self.blocking_factors,
            self.contradictions,
            self.limitations,
            self.proposed_action_ids,
            self.introduced_scores,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Advisor provider collections must be immutable tuples.")
        for values in (
            self.referenced_object_ids,
            self.blocking_factors,
            self.contradictions,
            self.limitations,
            self.proposed_action_ids,
            self.introduced_scores,
        ):
            if len(values) != len(set(values)) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise ValueError("Advisor provider values must be unique strings.")
        if any(not isinstance(value, AdvisorClaim) for value in self.claims):
            raise ValueError("Advisor claims must use the structured model.")


@dataclass(frozen=True)
class AdvisorResponse:
    schema_version: str
    advisor_request_id: str
    provider_id: str
    model_id: str | None
    original_question: str
    answer_text: str
    referenced_object_ids: tuple[str, ...]
    referenced_observation_ids: tuple[str, ...]
    referenced_reasoning_ids: tuple[str, ...]
    referenced_action_ids: tuple[str, ...]
    referenced_evidence_weight_ids: tuple[str, ...]
    preserved_blocking_factors: tuple[str, ...]
    preserved_contradictions: tuple[str, ...]
    preserved_limitations: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    validation_status: AdvisorValidationStatus
    warnings: tuple[str, ...]

    def __post_init__(self):
        required = (
            self.schema_version,
            self.advisor_request_id,
            self.provider_id,
            self.original_question,
            self.answer_text,
        )
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("Advisor response identity and text are required.")
        if self.model_id is not None and (
            not isinstance(self.model_id, str) or not self.model_id
        ):
            raise ValueError("Advisor model id cannot be empty.")
        if not isinstance(self.validation_status, AdvisorValidationStatus):
            raise ValueError("Advisor validation status is invalid.")
        collections = (
            self.referenced_object_ids,
            self.referenced_observation_ids,
            self.referenced_reasoning_ids,
            self.referenced_action_ids,
            self.referenced_evidence_weight_ids,
            self.preserved_blocking_factors,
            self.preserved_contradictions,
            self.preserved_limitations,
            self.unsupported_claims,
            self.warnings,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Advisor response collections must be immutable tuples.")
        if any(
            len(values) != len(set(values))
            or any(not isinstance(value, str) or not value for value in values)
            for values in collections
        ):
            raise ValueError("Advisor response values must be unique strings.")
