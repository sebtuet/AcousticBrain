from dataclasses import replace

import pytest

from acousticbrain.application import (
    DeterministicExploratoryService,
    ExploratoryFeasibilityRegistry,
)
from acousticbrain.models import (
    AcousticHypothesisExperimentGenerationAnalysis,
    ExpectedExperimentalObservation,
    ExpectedObservationOutcome,
    ExploratoryProposalInput,
    ExploratoryStatus,
    FeasibilityAnswer,
    GeneratedAcousticExperiment,
    GeneratedExperimentDifficulty,
    GeneratedExperimentReversibility,
    GeneratedExperimentType,
)


def experiment(candidate_id="generated.left.reflection"):
    return GeneratedAcousticExperiment(
        candidate_id=candidate_id,
        hypothesis_code="DOMINANT_EARLY_REFLECTION_INTERACTION",
        experiment_type=GeneratedExperimentType.LEFT_FIRST_REFLECTION_TEMPORARY_ABSORPTION,
        target="LEFT_FIRST_REFLECTION_AREA",
        movement_axis=None,
        movement_direction=None,
        step_distance_m=None,
        modified_variables=("TEMPORARY_ABSORPTION_AT_ONE_CANDIDATE_SURFACE",),
        controlled_variables=("LISTENING_POSITION", "LOUDSPEAKER_POSITION"),
        required_measurements=("LEFT", "RIGHT", "STEREO"),
        expected_observations=(ExpectedExperimentalObservation(
            observation_code="EARLY_REFLECTION_CHANGE",
            outcome=ExpectedObservationOutcome.NEUTRAL,
            measured_fact_codes=("ETC_LEFT_EARLY_REFLECTION", "STEREO_SYMMETRY"),
        ),),
        expected_frequency_regions=(),
        expected_time_regions=((3.0, 5.0),),
        information_value=80.0,
        reversibility=GeneratedExperimentReversibility.HIGH,
        difficulty=GeneratedExperimentDifficulty.EASY,
        blocking_reasons=(),
        rationale_codes=("REVERSIBLE_LOCALIZED_TEMPORARY_TREATMENT",),
    )


def generated(*items):
    return AcousticHypothesisExperimentGenerationAnalysis(
        hypotheses=(), ordered_experiments=tuple(items),
        recommended_candidate_id=items[0].candidate_id if items else None,
        applied_rule_codes=(), source_analysis_codes=(),
    )


def proposal_input(candidate_id="generated.left.reflection", fingerprint="sha256:one"):
    return ExploratoryProposalInput(
        candidate_id=candidate_id,
        reference_experiment_id="baseline",
        reference_content_fingerprint=fingerprint,
        reference_configuration=(("room", "reference"), ("speaker", "left")),
        action_parameters=(("target", "LEFT_FIRST_REFLECTION_AREA"),
                           ("treatment", "operator-declared-mattress")),
        return_action="REMOVE_TREATMENT_AND_RESTORE_REFERENCE",
        feasibility_question="Can you perform and reverse this exact intervention?",
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
        field_provenance=(("target", "GENERATED_EXPERIMENT"),
                          ("treatment", "USER_DECLARATION")),
    )


def test_complete_candidate_requires_explicit_feasibility_before_ready():
    service = DeterministicExploratoryService()
    first = service.analyze(generated(experiment()), (proposal_input(),))
    assert first.status is ExploratoryStatus.FEASIBILITY_REQUIRED
    assert first.proposal.mode == "EXPLORATORY"
    assert first.proposal.causality_status == "NOT_ESTABLISHED"
    assert first.proposal.universal_optimum == "NOT_CLAIMED"

    decisions = service.decide(first.proposal, FeasibilityAnswer.FEASIBLE)
    second = service.analyze(generated(experiment()), (proposal_input(),), decisions)
    assert second.status is ExploratoryStatus.EXPLORATORY_READY
    assert second.proposal == first.proposal


def test_selection_is_stable_and_returns_no_more_than_one_proposal():
    service = DeterministicExploratoryService()
    a, b = experiment("candidate.b"), experiment("candidate.a")
    inputs = (proposal_input("candidate.a"), proposal_input("candidate.b"))
    forward = service.analyze(generated(a, b), inputs)
    reverse = service.analyze(generated(b, a), tuple(reversed(inputs)))
    assert forward.proposal.proposal_id == reverse.proposal.proposal_id
    assert forward.proposal.experiment.candidate_id == "candidate.a"


@pytest.mark.parametrize("missing", ["action_parameters", "return_action"])
def test_incomplete_exact_action_or_return_produces_no_proposal(missing):
    values = {missing: () if missing == "action_parameters" else ""}
    with pytest.raises(ValueError):
        replace(proposal_input(), **values)


def test_refusal_is_idempotent_and_not_asked_again_in_same_scope():
    service = DeterministicExploratoryService()
    first = service.analyze(generated(experiment()), (proposal_input(),))
    registry = service.decide(first.proposal, FeasibilityAnswer.INFEASIBLE)
    assert service.decide(
        first.proposal, FeasibilityAnswer.INFEASIBLE, registry
    ).decisions == registry.decisions
    result = service.analyze(generated(experiment()), (proposal_input(),), registry)
    assert result.status is ExploratoryStatus.USER_INFEASIBLE


def test_decision_is_not_reused_when_reference_content_changes():
    service = DeterministicExploratoryService()
    first = service.analyze(generated(experiment()), (proposal_input(),))
    registry = service.decide(first.proposal, FeasibilityAnswer.FEASIBLE)
    changed = service.analyze(
        generated(experiment()), (proposal_input(fingerprint="sha256:two"),), registry
    )
    assert changed.status is ExploratoryStatus.FEASIBILITY_REQUIRED
    assert changed.proposal.reference_scope_id != first.proposal.reference_scope_id


def test_refusal_is_not_generalized_to_another_candidate():
    service = DeterministicExploratoryService()
    a, b = experiment("candidate.a"), experiment("candidate.b")
    inputs = (proposal_input("candidate.a"), proposal_input("candidate.b"))
    first = service.analyze(generated(a, b), inputs)
    registry = service.decide(first.proposal, FeasibilityAnswer.INFEASIBLE)
    second = service.analyze(generated(a, b), inputs, registry)
    assert second.status is ExploratoryStatus.FEASIBILITY_REQUIRED
    assert second.proposal.experiment.candidate_id == "candidate.b"


def test_executed_identical_proposal_is_not_offered_again():
    service = DeterministicExploratoryService()
    first = service.analyze(generated(experiment()), (proposal_input(),))
    result = service.analyze(
        generated(experiment()), (proposal_input(),),
        executed_proposal_ids=(first.proposal.proposal_id,),
    )
    assert result.status is ExploratoryStatus.NO_ACTION_AVAILABLE
    assert result.proposal is None


def test_missing_explicit_input_and_unsupported_family_are_not_admitted():
    service = DeterministicExploratoryService()
    unsupported = replace(experiment(), hypothesis_code="SBIR_PLACEMENT_INTERACTION")
    assert service.analyze(generated(experiment())).status is ExploratoryStatus.NO_ACTION_AVAILABLE
    assert service.analyze(
        generated(unsupported), (proposal_input(),)
    ).status is ExploratoryStatus.NO_ACTION_AVAILABLE


def test_conflicting_decision_in_same_scope_is_rejected():
    service = DeterministicExploratoryService()
    proposal = service.analyze(generated(experiment()), (proposal_input(),)).proposal
    registry = service.decide(proposal, FeasibilityAnswer.FEASIBLE)
    with pytest.raises(ValueError, match="different feasibility decision"):
        service.decide(proposal, FeasibilityAnswer.INFEASIBLE, registry)
