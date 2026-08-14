import hashlib
import json
from pathlib import Path

from acousticbrain.models import ExperimentKind
from acousticbrain.persistence.measurement_repository import MeasurementRepository

from .experiment_declaration import ExperimentDeclarationService

from acousticbrain.models.exploratory import (
    ExploratoryAnalysis,
    ExploratoryFeasibilityDecision,
    ExploratoryFeasibilityRegistry,
    ExploratoryProposal,
    ExploratoryProposalInput,
    ExploratoryStatus,
    FeasibilityAnswer,
    ExploratoryResult,
    ReferenceStabilityStatus,
)


class DeterministicExploratoryService:
    RULE_VERSION = 1
    SUPPORTED_HYPOTHESIS = "DOMINANT_EARLY_REFLECTION_INTERACTION"
    SUPPORTED_EXPERIMENT = "LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION"

    def analyze(
        self, generated, proposal_inputs=(), decisions=None,
        executed_proposal_ids=(), reference_content_hashes=None,
    ):
        registry = decisions or ExploratoryFeasibilityRegistry()
        inputs = {item.candidate_id: item for item in proposal_inputs}
        proposals = tuple(
            proposal
            for experiment in sorted(
                generated.ordered_experiments,
                key=lambda item: (item.experiment_type.value, item.candidate_id),
            )
            if (proposal := self._admit(
                experiment,
                inputs.get(experiment.candidate_id),
                reference_content_hashes,
            ))
            is not None
            and proposal.proposal_id not in set(executed_proposal_ids)
        )
        for proposal in proposals:
            decision = registry.get(proposal)
            if decision is None:
                return ExploratoryAnalysis(ExploratoryStatus.FEASIBILITY_REQUIRED, proposal)
            if decision.answer is FeasibilityAnswer.FEASIBLE:
                return ExploratoryAnalysis(ExploratoryStatus.EXPLORATORY_READY, proposal)
        if proposals:
            return ExploratoryAnalysis(ExploratoryStatus.USER_INFEASIBLE, proposals[-1])
        return ExploratoryAnalysis(ExploratoryStatus.NO_ACTION_AVAILABLE, None)

    def decide(self, proposal, answer, registry=None, user_note=None):
        if not isinstance(answer, FeasibilityAnswer):
            raise ValueError("An explicit FEASIBLE or INFEASIBLE answer is required.")
        decision = ExploratoryFeasibilityDecision(
            proposal_id=proposal.proposal_id,
            reference_scope_id=proposal.reference_scope_id,
            rule_version=proposal.rule_version,
            answer=answer,
            user_note=user_note,
        )
        return (registry or ExploratoryFeasibilityRegistry()).record(decision)

    def _admit(self, experiment, proposal_input, reference_content_hashes):
        if (
            not experiment.eligible
            or experiment.hypothesis_code != self.SUPPORTED_HYPOTHESIS
            or experiment.experiment_type.value != self.SUPPORTED_EXPERIMENT
            or proposal_input is None
            or dict(proposal_input.action_parameters).get("target") != experiment.target
            or (
                reference_content_hashes is not None
                and reference_content_hashes.get(
                    proposal_input.reference_experiment_id
                ) != proposal_input.reference_content_fingerprint
            )
            or len(experiment.modified_variables) != 1
            or not experiment.controlled_variables
            or not experiment.expected_observations
            or experiment.required_measurements != ("LEFT", "RIGHT", "STEREO")
        ):
            return None
        observable = tuple(sorted({
            fact
            for observation in experiment.expected_observations
            for fact in observation.measured_fact_codes
        }))
        if not observable:
            return None
        scope_id = self.reference_scope_id(proposal_input)
        proposal_id = "exploratory.v1." + self._digest({
            "candidate_id": experiment.candidate_id,
            "reference_scope_id": scope_id,
            "rule_version": self.RULE_VERSION,
            "action_parameters": proposal_input.action_parameters,
            "return_action": proposal_input.return_action,
        })
        return ExploratoryProposal(
            proposal_id=proposal_id,
            rule_version=self.RULE_VERSION,
            reference_scope_id=scope_id,
            experiment=experiment,
            proposal_input=proposal_input,
            observable_fact_codes=observable,
        )

    @classmethod
    def reference_scope_id(cls, proposal_input):
        return "reference.v1." + cls._digest({
            "experiment_id": proposal_input.reference_experiment_id,
            "content_fingerprint": proposal_input.reference_content_fingerprint,
            "configuration": proposal_input.reference_configuration,
        })

    @staticmethod
    def _digest(value):
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


class ExploratoryExperimentDeclarationService:
    """Declares one explicitly authorized acquisition without executing it."""

    def __init__(self, declaration_service=None, repository=None):
        self.repository = repository or MeasurementRepository()
        self.declaration_service = declaration_service or ExperimentDeclarationService(
            self.repository
        )

    def declare(self, measurement_root, *, experiment_code, analysis, user_note=None):
        if analysis is None or analysis.status != "EXPLORATORY_READY":
            raise ValueError("An EXPLORATORY_READY analysis is required.")
        if not analysis.proposal_id or not analysis.reference_experiment_id:
            raise ValueError("The exploratory proposal identity is incomplete.")
        declaration = self.declaration_service.declare(
            measurement_root,
            experiment_code=experiment_code,
            experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
            reference_experiment_code=analysis.reference_experiment_id,
            modified_variables=analysis.modified_variables,
            controlled_variables=analysis.controlled_variables,
            user_note=user_note,
            provenance_source="EXPLORATORY_V1_EXPLICIT_DECLARATION",
        )
        directory = Path(measurement_root) / experiment_code
        manifest = self.repository.load_manifest(directory) or {}
        comparison = manifest.get("comparison", {})
        if not isinstance(comparison, dict):
            comparison = {}
        comparison.update({
            "parent_experiment_ids": [analysis.reference_experiment_id],
            "source_protocol_id": analysis.proposal_id,
            "source_hypothesis_code": (
                DeterministicExploratoryService.SUPPORTED_HYPOTHESIS
            ),
            "declared_change_codes": list(analysis.modified_variables),
            "required_fact_codes": list(analysis.observable_fact_codes),
            "parameters": dict(analysis.action_parameters),
        })
        manifest["comparison"] = comparison
        manifest["exploratory_declaration"] = {
            "contract_id": "acousticbrain.exploratory.v1",
            "proposal_id": analysis.proposal_id,
            "reference_scope_id": analysis.reference_scope_id,
            "rule_version": analysis.rule_version,
            "target": analysis.target,
            "return_action": analysis.return_action,
            "required_measurements": list(analysis.required_measurements),
            "observable_fact_codes": list(analysis.observable_fact_codes),
            "limitations": list(analysis.limitations),
            "mode": analysis.mode,
            "causality_status": analysis.causality_status,
            "universal_optimum": analysis.universal_optimum,
        }
        self.repository.save_manifest(directory, manifest)
        return declaration


class ExploratoryResultService:
    NEXT_STEPS = {
        "DEGRADED": "RETURN_TO_REFERENCE",
        "UNCHANGED": "RETURN_THEN_CONSIDER_NEXT_ADMISSIBLE_CANDIDATE",
        "MIXED": "NO_PREFERENCE_RETURN_THEN_CONSIDER_EXISTING_CANDIDATE",
        "INCONCLUSIVE": "NO_PREFERENCE_RETURN_THEN_CONSIDER_EXISTING_CANDIDATE",
        "IMPROVED": "REPORT_BETTER_OBSERVED_FOR_DECLARED_OBJECTIVE",
    }

    def project(self, proposal_id, comparison_analysis, return_comparison=None):
        comparisons = tuple(
            item for item in comparison_analysis.sequence.local_comparisons
            if item.source_protocol_id == proposal_id
        )
        if len(comparisons) != 1:
            raise ValueError("Exactly one exploratory intervention comparison is required.")
        comparison = comparisons[0]
        outcome = comparison.acoustic_outcome.value
        observed = tuple(sorted(
            item.fact_code for item in comparison.fact_deltas
            if item.fact_code in set(comparison.required_fact_codes)
        ))
        if set(observed) != set(comparison.required_fact_codes):
            outcome = "INCONCLUSIVE"
        stability = ReferenceStabilityStatus.NOT_EVALUATED
        if return_comparison is not None:
            stable = (
                return_comparison.eligibility.value == "COMPARABLE"
                and return_comparison.acoustic_outcome.value == "UNCHANGED"
            )
            stability = (
                ReferenceStabilityStatus.ESTABLISHED
                if stable else ReferenceStabilityStatus.NOT_ESTABLISHED
            )
        winner = outcome == "IMPROVED" and stability is ReferenceStabilityStatus.ESTABLISHED
        next_step = self.NEXT_STEPS[outcome]
        if outcome == "IMPROVED" and not winner:
            next_step = "REFERENCE_STABILITY_NOT_ESTABLISHED_NO_ROBUST_WINNER"
        return ExploratoryResult(
            proposal_id=proposal_id,
            acoustic_outcome=outcome,
            reference_stability=stability,
            robust_winner=winner,
            next_step=next_step,
            observed_fact_codes=observed,
        )

    def project_historical_first_slice(self, comparison_analysis):
        matches = tuple(
            item for item in comparison_analysis.sequence.local_comparisons
            if item.before_experiment_id == "baseline"
            and item.after_experiment_id == "exp-007"
            and item.modified_variables == (
                "TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION",
            )
        )
        if len(matches) != 1:
            return None
        comparison = matches[0]
        outcome = comparison.acoustic_outcome.value
        observed = tuple(sorted(
            item.fact_code for item in comparison.fact_deltas
            if not item.fact_code.startswith("hypothesis.")
        ))
        return ExploratoryResult(
            proposal_id="exploratory.v1.replay.baseline.exp-007",
            acoustic_outcome=outcome,
            reference_stability=ReferenceStabilityStatus.NOT_EVALUATED,
            robust_winner=False,
            next_step=(
                "HISTORICAL_MIXED_INTERVENTION_NOT_PROPOSED_AGAIN"
                if outcome == "MIXED"
                else self.NEXT_STEPS[outcome]
            ),
            observed_fact_codes=observed,
        )
