from acousticbrain.application import SBIRProtocolInstanceSourceOverviewService
from test_sbir_protocol_instance_compatibility import proposal
from test_sbir_protocol_instance_resolution import (
    experiment,
    geometry_candidate,
    source_plan,
)


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
