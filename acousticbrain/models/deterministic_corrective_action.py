from dataclasses import dataclass
from enum import Enum
from math import isfinite


class CorrectiveActionCategory(Enum):
    MEASUREMENT = "MEASUREMENT"
    LISTENING_POSITION = "LISTENING_POSITION"
    SPEAKER_POSITION = "SPEAKER_POSITION"
    CHANNEL_ORIENTATION = "CHANNEL_ORIENTATION"
    SIGNAL_CHAIN_VERIFICATION = "SIGNAL_CHAIN_VERIFICATION"
    ROOM_INTERACTION_TEST = "ROOM_INTERACTION_TEST"
    DOCUMENTATION = "DOCUMENTATION"
    NO_ACTION = "NO_ACTION"


class CorrectiveActionType(Enum):
    RUN_CONTROLLED_MEASUREMENT = "RUN_CONTROLLED_MEASUREMENT"
    VERIFY_CHANNEL_ASYMMETRY = "VERIFY_CHANNEL_ASYMMETRY"
    PRESERVE_CURRENT_CONFIGURATION = "PRESERVE_CURRENT_CONFIGURATION"
    DEFER_ACTION_PENDING_EVIDENCE = "DEFER_ACTION_PENDING_EVIDENCE"


class CorrectiveActionApplicability(Enum):
    APPLICABLE = "APPLICABLE"
    CONDITIONALLY_APPLICABLE = "CONDITIONALLY_APPLICABLE"
    BLOCKED_BY_CONTRADICTION = "BLOCKED_BY_CONTRADICTION"
    BLOCKED_BY_MISSING_PARAMETERS = "BLOCKED_BY_MISSING_PARAMETERS"
    BLOCKED_BY_HISTORY = "BLOCKED_BY_HISTORY"
    ALREADY_TESTED = "ALREADY_TESTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NO_ACTION_REQUIRED = "NO_ACTION_REQUIRED"


class CorrectiveActionPriority(Enum):
    REQUIRED_FOR_DISCRIMINATION = "REQUIRED_FOR_DISCRIMINATION"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    DEFERRED = "DEFERRED"
    BLOCKED = "BLOCKED"


class CorrectiveActionTraceabilityStatus(Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class CorrectiveActionJustification:
    justification_id: str
    rule_id: str
    reasoning_id: str
    conclusion_code: str
    statement: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (
                self.justification_id,
                self.rule_id,
                self.reasoning_id,
                self.conclusion_code,
                self.statement,
            )
        ):
            raise ValueError("Action justification requires stable structured values.")


@dataclass(frozen=True)
class DeterministicCorrectiveAction:
    action_id: str
    category: CorrectiveActionCategory
    action_type: CorrectiveActionType
    target_id: str
    title: str
    objective: str
    description: str
    applicability: CorrectiveActionApplicability
    priority: CorrectiveActionPriority
    confidence: float | None
    source_confidence_ceiling: float | None
    source_reasoning_ids: tuple[str, ...]
    source_observation_ids: tuple[str, ...]
    upstream_source_ids: tuple[str, ...]
    justifications: tuple[CorrectiveActionJustification, ...]
    preconditions: tuple[str, ...]
    known_parameters: tuple[tuple[str, str], ...]
    derivable_parameters: tuple[str, ...]
    required_missing_parameters: tuple[str, ...]
    forbidden_to_invent_parameters: tuple[str, ...]
    known_risks: tuple[str, ...]
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    stop_criteria: tuple[str, ...]
    contradictions: tuple[str, ...]
    limitations: tuple[str, ...]
    traceability_status: CorrectiveActionTraceabilityStatus
    compatible_protocol_ids: tuple[str, ...]
    compatible_plan_ids: tuple[str, ...]

    _FORBIDDEN_LANGUAGE = (
        "buy ",
        "achetez",
        "install ",
        "installez",
        "best choice",
        "meilleur choix",
        "you absolutely should",
        "vous devriez absolument",
        "will solve",
        "résoudra le problème",
    )

    def __post_init__(self):
        identifiers = (self.action_id, self.target_id, self.title, self.objective, self.description)
        if any(not isinstance(value, str) or not value for value in identifiers):
            raise ValueError("Corrective actions require stable descriptive values.")
        enums = (
            (self.category, CorrectiveActionCategory),
            (self.action_type, CorrectiveActionType),
            (self.applicability, CorrectiveActionApplicability),
            (self.priority, CorrectiveActionPriority),
            (self.traceability_status, CorrectiveActionTraceabilityStatus),
        )
        if any(not isinstance(value, kind) for value, kind in enums):
            raise ValueError("Corrective action enum value is invalid.")
        for value in (self.confidence, self.source_confidence_ceiling):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or not 0.0 <= value <= 100.0
            ):
                raise ValueError("Corrective action confidence must be bounded.")
        if (
            self.confidence is not None
            and self.source_confidence_ceiling is not None
            and self.confidence > self.source_confidence_ceiling
        ):
            raise ValueError("Action confidence cannot exceed source reasoning confidence.")
        collections = (
            self.source_reasoning_ids,
            self.source_observation_ids,
            self.upstream_source_ids,
            self.justifications,
            self.preconditions,
            self.known_parameters,
            self.derivable_parameters,
            self.required_missing_parameters,
            self.forbidden_to_invent_parameters,
            self.known_risks,
            self.constraints,
            self.success_criteria,
            self.stop_criteria,
            self.contradictions,
            self.limitations,
            self.compatible_protocol_ids,
            self.compatible_plan_ids,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Corrective-action collections must be tuples.")
        if not self.source_reasoning_ids or not self.source_observation_ids:
            raise ValueError("An action requires reasoning and observation provenance.")
        if not self.justifications or not self.upstream_source_ids:
            raise ValueError("An action requires justification and upstream provenance.")
        string_collections = (
            self.source_reasoning_ids,
            self.source_observation_ids,
            self.upstream_source_ids,
            self.preconditions,
            self.derivable_parameters,
            self.required_missing_parameters,
            self.forbidden_to_invent_parameters,
            self.known_risks,
            self.constraints,
            self.success_criteria,
            self.stop_criteria,
            self.contradictions,
            self.limitations,
            self.compatible_protocol_ids,
            self.compatible_plan_ids,
        )
        if any(
            len(values) != len(set(values))
            or any(not isinstance(value, str) or not value for value in values)
            for values in string_collections
        ):
            raise ValueError("Corrective-action codes must be unique non-empty strings.")
        if any(
            not isinstance(item, tuple)
            or len(item) != 2
            or any(not isinstance(value, str) or not value for value in item)
            for item in self.known_parameters
        ) or len(self.known_parameters) != len({item[0] for item in self.known_parameters}):
            raise ValueError("Known action parameters must be unique string pairs.")
        justification_reasonings = {item.reasoning_id for item in self.justifications}
        if not set(self.source_reasoning_ids).issubset(justification_reasonings):
            raise ValueError("Every source reasoning requires structured justification.")
        if self.applicability in (
            CorrectiveActionApplicability.APPLICABLE,
            CorrectiveActionApplicability.NO_ACTION_REQUIRED,
        ) and (self.required_missing_parameters or self.contradictions):
            raise ValueError("Applicable actions cannot hide missing parameters or contradictions.")
        if (
            self.applicability
            is CorrectiveActionApplicability.BLOCKED_BY_CONTRADICTION
            and not self.contradictions
        ):
            raise ValueError("Contradiction-blocked actions require contradictions.")
        if (
            self.applicability
            is CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
            and not self.required_missing_parameters
        ):
            raise ValueError("Missing-parameter actions must identify missing parameters.")
        if self.traceability_status is not CorrectiveActionTraceabilityStatus.COMPLETE:
            raise ValueError("Generated corrective actions require complete traceability.")
        language = " ".join(
            (
                self.title,
                self.objective,
                self.description,
                *(item.statement for item in self.justifications),
                *self.preconditions,
                *self.constraints,
                *self.success_criteria,
                *self.stop_criteria,
                *self.limitations,
            )
        ).casefold()
        if any(value in language for value in self._FORBIDDEN_LANGUAGE):
            raise ValueError("Corrective actions must not contain commercial prescriptions.")


@dataclass(frozen=True)
class DeterministicCorrectiveActionSynthesis:
    actions: tuple[DeterministicCorrectiveAction, ...] = ()

    def __post_init__(self):
        if not isinstance(self.actions, tuple) or any(
            not isinstance(item, DeterministicCorrectiveAction) for item in self.actions
        ):
            raise ValueError("Action synthesis must contain immutable actions.")
        identifiers = tuple(item.action_id for item in self.actions)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Corrective action ids must be unique.")
