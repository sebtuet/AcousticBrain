from dataclasses import replace

import pytest

from acousticbrain.application import (
    SBIRProtocolInstanceResolver,
    evidence_acquisition_plan_fingerprint,
)
from acousticbrain.models import (
    ExperimentDeclaration,
    ExperimentDescriptor,
    ExperimentState,
    ExperimentType,
    GeometryCoordinate,
    GeometrySBIRCandidate,
    ReflectionSurface,
    SBIRProtocolInstanceInput,
    SBIRProtocolInstanceResolution,
    SBIRProtocolInstanceResolutionDecision,
)
from test_channel_isolation_plan_coverage import plan


PLAN_ID = SBIRProtocolInstanceInput.SOURCE_PLAN_ID
PROTOCOL_ID = SBIRProtocolInstanceInput.PROTOCOL_ID


def source_plan(**overrides):
    values = {"plan_id": PLAN_ID}
    values.update(overrides)
    return replace(plan(), **values)


def protocol_input(plan_value=None, **overrides):
    plan_value = plan_value or source_plan()
    values = {
        "schema_version": 1,
        "protocol_instance_id": "sbir-protocol-instance-001",
        "protocol_id": PROTOCOL_ID,
        "source_plan_id": PLAN_ID,
        "source_plan_contract_fingerprint": (
            evidence_acquisition_plan_fingerprint(plan_value)
        ),
        "reference_experiment_id": "baseline",
        "moved_experiment_id": "exp-sbir-001",
        "speaker_id": "left",
        "surface_id": "front_wall",
        "geometry_candidate_id": "geometry-candidate-001",
        "speaker_displacement_m": 0.12,
        "declaration_source": "STRUCTURED_SCIENTIFIC_SOURCE",
        "user_note": None,
    }
    values.update(overrides)
    return SBIRProtocolInstanceInput(**values)


def experiment(experiment_id):
    return ExperimentDescriptor(
        experiment_id=experiment_id,
        directory=f"/measurements/{experiment_id}",
        experiment_type=(
            ExperimentType.BASELINE
            if experiment_id == "baseline"
            else ExperimentType.EXPERIMENT
        ),
        available_files=(),
        available_channels=(),
        wav_files=(),
        txt_files=(),
        mdat_file=None,
        manifest_present=True,
        content_hash="a" * 64,
        timestamp="2026-08-08T00:00:00+00:00",
        imported_at="2026-08-08T00:00:00+00:00",
        state=ExperimentState.INCOMPLETE,
        experiment_declaration=ExperimentDeclaration.unknown(),
    )


def geometry_candidate(candidate_id="geometry-candidate-001"):
    return GeometrySBIRCandidate(
        candidate_id=candidate_id,
        geometry_path_id="path-001",
        speaker_id="left",
        listening_position_id="mic",
        surface_id="front_wall",
        base_surface_id="front_wall",
        surface=ReflectionSurface.FRONT_WALL,
        relationship_code="SPEAKER_BOUNDARY",
        impact_point=GeometryCoordinate(0.0, 1.0, 1.0),
        direct_path_m=2.0,
        reflected_path_m=3.0,
        extra_distance_m=1.0,
        speaker_boundary_distance_m=0.5,
        expected_cancellation_frequency_hz=171.5,
        distance_uncertainty_m=0.01,
        frequency_uncertainty_hz=3.0,
        confidence=90.0,
        provenance_codes=("ROOM_GEOMETRY",),
    )


def resolve(input_value=None, **overrides):
    plan_value = source_plan()
    arguments = {
        "plans": (plan_value,),
        "protocol_ids": (PROTOCOL_ID,),
        "experiments": (experiment("baseline"), experiment("exp-sbir-001")),
        "geometry_candidates": (geometry_candidate(),),
    }
    arguments.update(overrides)
    return SBIRProtocolInstanceResolver().resolve(
        input_value or protocol_input(plan_value),
        **arguments,
    )


def test_resolves_all_existing_identities_without_deciding_compatibility():
    result = resolve()

    assert isinstance(result, SBIRProtocolInstanceResolution)
    assert result.source_plan.plan_id == PLAN_ID
    assert result.protocol_id == PROTOCOL_ID
    assert result.reference_experiment.experiment_id == "baseline"
    assert result.moved_experiment.experiment_id == "exp-sbir-001"
    assert result.geometry_candidate.candidate_id == "geometry-candidate-001"
    assert result.decisions == tuple(SBIRProtocolInstanceResolutionDecision)
    assert not hasattr(result, "compatibility_status")


@pytest.mark.parametrize(
    ("plans", "code"),
    (
        ((), "PLAN_UNKNOWN"),
        ((source_plan(), source_plan()), "PLAN_AMBIGUOUS"),
    ),
)
def test_plan_resolution_is_exact(plans, code):
    with pytest.raises(ValueError, match=code):
        resolve(plans=plans)


def test_plan_fingerprint_must_match_before_protocol_resolution():
    value = protocol_input(
        source_plan(),
        source_plan_contract_fingerprint="0" * 64,
    )
    with pytest.raises(ValueError, match="PLAN_FINGERPRINT_MISMATCH"):
        resolve(value, protocol_ids=())


@pytest.mark.parametrize(
    ("protocol_ids", "code"),
    (
        ((), "PROTOCOL_UNKNOWN"),
        ((PROTOCOL_ID, PROTOCOL_ID), "PROTOCOL_AMBIGUOUS"),
    ),
)
def test_protocol_resolution_is_exact(protocol_ids, code):
    with pytest.raises(ValueError, match=code):
        resolve(protocol_ids=protocol_ids)


@pytest.mark.parametrize(
    ("experiments", "code"),
    (
        ((experiment("exp-sbir-001"),), "REFERENCE_EXPERIMENT_UNKNOWN"),
        (
            (
                experiment("baseline"),
                experiment("baseline"),
                experiment("exp-sbir-001"),
            ),
            "REFERENCE_EXPERIMENT_AMBIGUOUS",
        ),
        ((experiment("baseline"),), "MOVED_EXPERIMENT_UNKNOWN"),
        (
            (
                experiment("baseline"),
                experiment("exp-sbir-001"),
                experiment("exp-sbir-001"),
            ),
            "MOVED_EXPERIMENT_AMBIGUOUS",
        ),
    ),
)
def test_experiment_resolution_is_exact_and_ordered(experiments, code):
    with pytest.raises(ValueError, match=code):
        resolve(experiments=experiments)


@pytest.mark.parametrize(
    ("candidates", "code"),
    (
        ((), "GEOMETRY_CANDIDATE_UNKNOWN"),
        (
            (geometry_candidate(), geometry_candidate()),
            "GEOMETRY_CANDIDATE_AMBIGUOUS",
        ),
    ),
)
def test_geometry_candidate_resolution_is_exact(candidates, code):
    with pytest.raises(ValueError, match=code):
        resolve(geometry_candidates=candidates)


def test_resolution_is_independent_of_collection_order():
    unrelated_plan = replace(source_plan(), plan_id="UNRELATED")
    unrelated_experiment = experiment("exp-unrelated")
    unrelated_geometry = geometry_candidate("geometry-unrelated")
    arguments = {
        "plans": (unrelated_plan, source_plan()),
        "protocol_ids": ("protocol.unrelated.v1", PROTOCOL_ID),
        "experiments": (
            unrelated_experiment,
            experiment("exp-sbir-001"),
            experiment("baseline"),
        ),
        "geometry_candidates": (unrelated_geometry, geometry_candidate()),
    }

    first = resolve(**arguments)
    second = resolve(**{
        name: tuple(reversed(values)) for name, values in arguments.items()
    })

    assert first == second


@pytest.mark.parametrize(
    ("field", "invalid", "label"),
    (
        ("plans", [], "plans must be a typed tuple"),
        ("protocol_ids", [], "protocol ids must be a typed tuple"),
        ("experiments", [], "experiments must be a typed tuple"),
        ("geometry_candidates", [], "geometry candidates must be a typed tuple"),
    ),
)
def test_source_collections_are_explicitly_typed(field, invalid, label):
    with pytest.raises(TypeError, match=label):
        resolve(**{field: invalid})


def test_resolution_model_rejects_missing_or_reordered_decisions():
    result = resolve()
    with pytest.raises(ValueError, match="incomplete or out of order"):
        replace(result, decisions=tuple(reversed(result.decisions)))


def test_resolver_does_not_mutate_any_source_collection():
    plans = (source_plan(),)
    protocols = (PROTOCOL_ID,)
    experiments = (experiment("baseline"), experiment("exp-sbir-001"))
    candidates = (geometry_candidate(),)
    snapshots = (plans, protocols, experiments, candidates)

    resolve(
        plans=plans,
        protocol_ids=protocols,
        experiments=experiments,
        geometry_candidates=candidates,
    )

    assert snapshots == (plans, protocols, experiments, candidates)
