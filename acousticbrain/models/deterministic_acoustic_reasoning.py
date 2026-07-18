from dataclasses import dataclass
from enum import Enum
from math import isfinite


class DeterministicReasoningCategory(Enum):
    HYPOTHESIS_EXPLANATION = "HYPOTHESIS_EXPLANATION"


class DeterministicReasoningConclusion(Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    NON_DISCRIMINATED = "NON_DISCRIMINATED"
    NO_APPLICABLE_RULE = "NO_APPLICABLE_RULE"


class ReasoningPremiseSourceType(Enum):
    OBSERVATION = "OBSERVATION"
    EXISTING_HYPOTHESIS = "EXISTING_HYPOTHESIS"
    CAUSAL_RESULT = "CAUSAL_RESULT"
    LONGITUDINAL_STATE = "LONGITUDINAL_STATE"


class ReasoningPremiseRole(Enum):
    SUPPORTING = "SUPPORTING"
    CONTRADICTING = "CONTRADICTING"
    CONTEXT = "CONTEXT"
    LIMITING = "LIMITING"


@dataclass(frozen=True)
class DeterministicReasoningPremise:
    premise_id: str
    source_type: ReasoningPremiseSourceType
    source_id: str
    statement: str
    role: ReasoningPremiseRole

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (self.premise_id, self.source_id, self.statement)
        ):
            raise ValueError("Reasoning premises require stable structured values.")
        if not isinstance(self.source_type, ReasoningPremiseSourceType) or not isinstance(
            self.role, ReasoningPremiseRole
        ):
            raise ValueError("Reasoning premise types are invalid.")


@dataclass(frozen=True)
class DeterministicInferenceStep:
    step_id: str
    rule_id: str
    input_premise_ids: tuple[str, ...]
    output_code: str
    statement: str

    def __post_init__(self):
        if any(
            not isinstance(value, str) or not value
            for value in (self.step_id, self.rule_id, self.output_code, self.statement)
        ):
            raise ValueError("Inference steps require stable structured values.")
        if (
            not isinstance(self.input_premise_ids, tuple)
            or not self.input_premise_ids
            or len(self.input_premise_ids) != len(set(self.input_premise_ids))
        ):
            raise ValueError("Inference steps require unique premise ids.")


@dataclass(frozen=True)
class DeterministicAcousticReasoning:
    reasoning_id: str
    category: DeterministicReasoningCategory
    title: str
    conclusion: DeterministicReasoningConclusion
    confidence: float | None
    observation_ids: tuple[str, ...]
    premises: tuple[DeterministicReasoningPremise, ...]
    inference_steps: tuple[DeterministicInferenceStep, ...]
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    compatible_hypothesis_ids: tuple[str, ...]
    excluded_conclusions: tuple[str, ...]
    upstream_source_ids: tuple[str, ...]

    _FORBIDDEN_LANGUAGE = (
        "you should",
        "vous devriez",
        "try ",
        "essayez",
        "move ",
        "déplacez",
        "install ",
        "installez",
        "prioritize",
        "priorisez",
        "i recommend",
        "je recommande",
    )

    def __post_init__(self):
        if not isinstance(self.reasoning_id, str) or not self.reasoning_id:
            raise ValueError("A deterministic reasoning requires a stable id.")
        if not isinstance(self.category, DeterministicReasoningCategory):
            raise ValueError("A deterministic reasoning requires a category.")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("A deterministic reasoning requires a title.")
        if not isinstance(self.conclusion, DeterministicReasoningConclusion):
            raise ValueError("A deterministic reasoning conclusion is invalid.")
        if self.confidence is not None and (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 100.0
        ):
            raise ValueError("Reasoning confidence must be unavailable or bounded.")
        collections = (
            self.observation_ids,
            self.premises,
            self.inference_steps,
            self.supporting_evidence,
            self.contradicting_evidence,
            self.limitations,
            self.compatible_hypothesis_ids,
            self.excluded_conclusions,
            self.upstream_source_ids,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Deterministic-reasoning collections must be tuples.")
        if not self.premises or not self.inference_steps or not self.upstream_source_ids:
            raise ValueError("Reasoning requires premises, inference and provenance.")
        premise_ids = tuple(item.premise_id for item in self.premises)
        if len(premise_ids) != len(set(premise_ids)):
            raise ValueError("Reasoning premise ids must be unique.")
        if any(
            not set(step.input_premise_ids).issubset(premise_ids)
            for step in self.inference_steps
        ):
            raise ValueError("Every inference step must reference existing premises.")
        if not set(self.observation_ids).issubset(
            premise.source_id
            for premise in self.premises
            if premise.source_type is ReasoningPremiseSourceType.OBSERVATION
        ):
            raise ValueError("Every source observation must have a premise.")
        for values in (
            self.observation_ids,
            self.supporting_evidence,
            self.contradicting_evidence,
            self.limitations,
            self.compatible_hypothesis_ids,
            self.excluded_conclusions,
            self.upstream_source_ids,
        ):
            if len(values) != len(set(values)) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise ValueError("Reasoning codes must be unique non-empty strings.")
        language = " ".join(
            (
                self.title,
                *(premise.statement for premise in self.premises),
                *(step.statement for step in self.inference_steps),
                *self.limitations,
            )
        ).casefold()
        if any(value in language for value in self._FORBIDDEN_LANGUAGE):
            raise ValueError("Deterministic reasoning must not prescribe an action.")


@dataclass(frozen=True)
class DeterministicAcousticReasoningSynthesis:
    reasonings: tuple[DeterministicAcousticReasoning, ...] = ()

    def __post_init__(self):
        if not isinstance(self.reasonings, tuple) or any(
            not isinstance(item, DeterministicAcousticReasoning)
            for item in self.reasonings
        ):
            raise ValueError("Reasoning synthesis must contain immutable reasonings.")
        identifiers = tuple(item.reasoning_id for item in self.reasonings)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Reasoning ids must be unique.")
