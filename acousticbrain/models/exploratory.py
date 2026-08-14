from dataclasses import dataclass
from enum import Enum

from .acoustic_hypothesis_experiment_generation import GeneratedAcousticExperiment


class ExploratoryStatus(Enum):
    FEASIBILITY_REQUIRED = "FEASIBILITY_REQUIRED"
    EXPLORATORY_READY = "EXPLORATORY_READY"
    USER_INFEASIBLE = "USER_INFEASIBLE"
    NO_ACTION_AVAILABLE = "NO_ACTION_AVAILABLE"


class FeasibilityAnswer(Enum):
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"


class ReferenceStabilityStatus(Enum):
    ESTABLISHED = "ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True)
class ExploratoryProposalInput:
    candidate_id: str
    reference_experiment_id: str
    reference_content_fingerprint: str
    reference_configuration: tuple[tuple[str, str], ...]
    action_parameters: tuple[tuple[str, str], ...]
    return_action: str
    feasibility_question: str
    limitations: tuple[str, ...]
    field_provenance: tuple[tuple[str, str], ...]

    def __post_init__(self):
        collections = (
            self.reference_configuration,
            self.action_parameters,
            self.limitations,
            self.field_provenance,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise ValueError("Exploratory proposal collections must be tuples.")
        required = (
            self.candidate_id,
            self.reference_experiment_id,
            self.reference_content_fingerprint,
            self.return_action,
            self.feasibility_question,
        )
        if any(not value for value in required):
            raise ValueError("Exploratory proposal input must be explicit and complete.")
        if not self.reference_configuration or not self.action_parameters:
            raise ValueError("Reference configuration and action parameters are required.")
        if not self.limitations or not self.field_provenance:
            raise ValueError("Field-level provenance is required.")
        if not set(dict(self.action_parameters)) <= set(dict(self.field_provenance)):
            raise ValueError("Every action parameter requires field-level provenance.")


@dataclass(frozen=True)
class ExploratoryProposal:
    proposal_id: str
    rule_version: int
    reference_scope_id: str
    experiment: GeneratedAcousticExperiment
    proposal_input: ExploratoryProposalInput
    observable_fact_codes: tuple[str, ...]
    mode: str = "EXPLORATORY"
    causality_status: str = "NOT_ESTABLISHED"
    universal_optimum: str = "NOT_CLAIMED"

    def __post_init__(self):
        if not self.proposal_id or self.rule_version < 1 or not self.reference_scope_id:
            raise ValueError("Exploratory proposal identity is required.")
        if not isinstance(self.observable_fact_codes, tuple) or not self.observable_fact_codes:
            raise ValueError("Exploratory observable facts are required.")
        if self.experiment.candidate_id != self.proposal_input.candidate_id:
            raise ValueError("Proposal input must target the selected candidate.")
        if (self.mode, self.causality_status, self.universal_optimum) != (
            "EXPLORATORY", "NOT_ESTABLISHED", "NOT_CLAIMED"
        ):
            raise ValueError("Exploratory knowledge-boundary markers are immutable.")


@dataclass(frozen=True)
class ExploratoryFeasibilityDecision:
    proposal_id: str
    reference_scope_id: str
    rule_version: int
    answer: FeasibilityAnswer
    user_note: str | None = None


@dataclass(frozen=True)
class ExploratoryAnalysis:
    status: ExploratoryStatus
    proposal: ExploratoryProposal | None

    def __post_init__(self):
        needs_proposal = self.status is not ExploratoryStatus.NO_ACTION_AVAILABLE
        if needs_proposal != (self.proposal is not None):
            raise ValueError("Exploratory status and proposal are inconsistent.")


@dataclass(frozen=True)
class ExploratoryResult:
    proposal_id: str
    acoustic_outcome: str
    reference_stability: ReferenceStabilityStatus
    robust_winner: bool
    next_step: str
    observed_fact_codes: tuple[str, ...]
    mode: str = "EXPLORATORY"
    causality_status: str = "NOT_ESTABLISHED"
    universal_optimum: str = "NOT_CLAIMED"

    def __post_init__(self):
        allowed = {"IMPROVED", "DEGRADED", "UNCHANGED", "MIXED", "INCONCLUSIVE"}
        if self.acoustic_outcome not in allowed:
            raise ValueError("Unsupported exploratory acoustic outcome.")
        if self.robust_winner and not (
            self.acoustic_outcome == "IMPROVED"
            and self.reference_stability is ReferenceStabilityStatus.ESTABLISHED
        ):
            raise ValueError("A robust winner requires improvement and stable reference.")
        if not isinstance(self.observed_fact_codes, tuple):
            raise ValueError("Exploratory observed facts must be a tuple.")


class ExploratoryFeasibilityRegistry:
    def __init__(self, decisions=()):
        self._decisions = tuple(decisions)
        keys = tuple(self._key(item) for item in self._decisions)
        if len(keys) != len(set(keys)):
            raise ValueError("Feasibility decisions must have unique scopes.")

    @property
    def decisions(self):
        return self._decisions

    def get(self, proposal):
        key = (proposal.proposal_id, proposal.reference_scope_id, proposal.rule_version)
        return next((item for item in self._decisions if self._key(item) == key), None)

    def record(self, decision):
        key = self._key(decision)
        current = next((item for item in self._decisions if self._key(item) == key), None)
        if current is not None:
            if current == decision:
                return self
            raise ValueError("A different feasibility decision already exists in this scope.")
        return ExploratoryFeasibilityRegistry((*self._decisions, decision))

    @staticmethod
    def _key(decision):
        return (decision.proposal_id, decision.reference_scope_id, decision.rule_version)
