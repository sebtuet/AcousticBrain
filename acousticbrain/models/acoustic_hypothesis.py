from dataclasses import dataclass
from math import isfinite

from .reasoning_codes import HypothesisCode, HypothesisStatus
from .reasoning_evidence import MissingReasoningFact, ReasoningEvidence
from .verification_action import VerificationAction


@dataclass(frozen=True)
class AcousticHypothesis:
    code: HypothesisCode
    phenomenon: str
    domain_codes: tuple[str, ...]
    supporting_evidence: tuple[ReasoningEvidence, ...]
    counter_evidence: tuple[ReasoningEvidence, ...]
    context_evidence: tuple[ReasoningEvidence, ...]
    missing_facts: tuple[MissingReasoningFact, ...]
    applied_rule_codes: tuple[str, ...]
    support_score: float
    confidence: float
    status: HypothesisStatus
    verification_actions: tuple[VerificationAction, ...] = ()

    def __post_init__(self):
        if not isinstance(self.code, HypothesisCode):
            raise ValueError("Hypothesis code is invalid.")
        if not isinstance(self.status, HypothesisStatus):
            raise ValueError("Hypothesis status is invalid.")
        if not isinstance(self.phenomenon, str) or not self.phenomenon.strip():
            raise ValueError("Hypothesis phenomenon is required.")
        collections = (
            self.domain_codes,
            self.supporting_evidence,
            self.counter_evidence,
            self.context_evidence,
            self.missing_facts,
            self.applied_rule_codes,
            self.verification_actions,
        )
        if any(not isinstance(collection, tuple) for collection in collections):
            raise ValueError("Hypothesis collections must be tuples.")
        if not isfinite(self.support_score) or not 0.0 <= self.support_score <= 100.0:
            raise ValueError("Hypothesis support score must be bounded.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Hypothesis confidence must be bounded.")
        evidence_codes = [
            item.code
            for collection in (
                self.supporting_evidence,
                self.counter_evidence,
                self.context_evidence,
            )
            for item in collection
        ]
        if len(evidence_codes) != len(set(evidence_codes)):
            raise ValueError("Hypothesis evidence codes must be unique.")
        fact_codes = {
            item.fact_code
            for collection in (
                self.supporting_evidence,
                self.counter_evidence,
                self.context_evidence,
            )
            for item in collection
        }
        if any(
            not set(action.evidence_fact_codes).issubset(fact_codes)
            for action in self.verification_actions
        ):
            raise ValueError("Verification actions require hypothesis evidence.")
        if self.status is HypothesisStatus.INCONCLUSIVE and any(
            action.definitive for action in self.verification_actions
        ):
            raise ValueError("Inconclusive hypotheses cannot define corrections.")
