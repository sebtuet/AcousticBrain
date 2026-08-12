from dataclasses import replace

from acousticbrain.analysis import ExperimentPlanner
from acousticbrain.application import SBIRProtocolInstanceSourceOverviewService
from acousticbrain.models import HypothesisCode
from test_experiment_planner import ACTION_DATA, analysis, candidate, hypothesis
from test_sbir_protocol_instance_compatibility import proposal
from test_sbir_protocol_instance_resolution import (
    experiment,
    geometry_candidate,
    source_plan,
)


def planning_candidate(*, uncertainty_percent=23.1665):
    parameters = dict(
        ACTION_DATA[HypothesisCode.SBIR_PLACEMENT_INTERACTION][2]
    )
    parameters.update({
        "geometry_candidate_id": (
            "geometry_sbir.geometry_reflection.LEFT."
            "LISTENING_POSITION.floor"
        ),
        "surface": "floor",
        "frequency_uncertainty_percent": uncertainty_percent,
    })
    result = ExperimentPlanner().plan(analysis(hypothesis(
        HypothesisCode.SBIR_PLACEMENT_INTERACTION,
        parameters=parameters,
    )))
    return candidate(result, HypothesisCode.SBIR_PLACEMENT_INTERACTION)


def test_lists_exact_sources_without_selecting_or_recommending():
    result = SBIRProtocolInstanceSourceOverviewService().build(
        plans=(source_plan(),),
        experiments=(experiment("exp-sbir-001"), experiment("baseline")),
        geometry_candidates=(geometry_candidate(),),
        proposals=(proposal(),),
    )
    assert result.plans[0].plan_id.endswith("ACQUIRE_SUPPORTING_OBSERVATION_V2")
    assert len(result.plans[0].contract_fingerprint) == 64
    assert tuple(value.experiment_id for value in result.experiments) == (
        "baseline",
        "exp-sbir-001",
    )
    assert result.geometry_candidates[0].speaker_id == "left"
    assert result.geometry_candidates[0].surface_id == "front_wall"
    assert result.displacement_proposals[0].geometry_candidate_id == (
        "geometry-candidate-001"
    )
    assert result.displacement_proposals[0].displacement_m == 0.12
    assert result.selection_status == "NO_SELECTION_PERFORMED"
    assert result.causality_status == "NOT_ESTABLISHED"
    assert not hasattr(result, "selected_candidate")
    assert not hasattr(result, "recommended_candidate")


def test_empty_sources_remain_explicit_and_do_not_create_placeholders():
    result = SBIRProtocolInstanceSourceOverviewService().build(
        plans=(),
        experiments=(),
        geometry_candidates=(),
        proposals=(),
    )
    assert result.plans == ()
    assert result.experiments == ()
    assert result.geometry_candidates == ()
    assert result.displacement_proposals == ()
    assert result.displacement_planning_sources == ()


def test_preserves_existing_sbir_planning_blockage_without_new_verdict():
    source = planning_candidate()
    unrelated = replace(source, source_protocol_id="protocol.unrelated.v1")
    result = SBIRProtocolInstanceSourceOverviewService().build(
        plans=(),
        experiments=(),
        geometry_candidates=(),
        proposals=(),
        planning_candidates=(unrelated, source),
        prediction_uncertainty_limit_percent=10.0,
    )

    assert len(result.displacement_planning_sources) == 1
    value = result.displacement_planning_sources[0]
    assert value.candidate_id == (
        "experiment_candidate.sbir_placement_interaction"
    )
    assert value.eligibility_status == "INELIGIBLE"
    assert value.ineligibility_reason_codes == (
        "SBIR_PREDICTION_UNCERTAINTY_TOO_HIGH",
    )
    assert value.geometry_candidate_id == (
        "geometry_sbir.geometry_reflection.LEFT."
        "LISTENING_POSITION.floor"
    )
    assert value.surface_id == "floor"
    assert value.prediction_uncertainty_percent == 23.1665
    assert value.prediction_uncertainty_limit_percent == 10.0
    assert value.prediction_uncertainty_excess_percent == 13.1665


def test_unrelated_plans_are_not_presented_as_the_fixed_source_plan():
    unrelated = source_plan(plan_id="UNRELATED")
    result = SBIRProtocolInstanceSourceOverviewService().build(
        plans=(unrelated,),
        experiments=(),
        geometry_candidates=(),
        proposals=(),
    )
    assert result.plans == ()


def test_collection_order_does_not_change_the_overview():
    candidates = (
        geometry_candidate("geometry-z"),
        geometry_candidate("geometry-a"),
    )
    first = SBIRProtocolInstanceSourceOverviewService().build(
        plans=(source_plan(),),
        experiments=(experiment("exp-sbir-001"), experiment("baseline")),
        geometry_candidates=candidates,
        proposals=(),
    )
    second = SBIRProtocolInstanceSourceOverviewService().build(
        plans=(source_plan(),),
        experiments=(experiment("baseline"), experiment("exp-sbir-001")),
        geometry_candidates=tuple(reversed(candidates)),
        proposals=(),
    )
    assert first == second
