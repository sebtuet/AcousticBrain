from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from acousticbrain.application import AcousticSession, OptimizationSessionService
from acousticbrain.analysis import (
    AnalysisContext,
    AcousticReasoningEngine,
    ExperimentPlanner,
    GeometryEarlyReflectionEngine,
    GeometrySBIRPredictionEngine,
    LoudspeakerPositioningExperimentEngine,
    RoomGeometryBuilder,
    SBIRGeometryCorrelationEngine,
)
from acousticbrain.importers import ImportEngine
from acousticbrain.models import (
    AcousticObservationSynthesis,
    ExperimentProtocol,
    GeometryDatumQualityDescription,
    ListeningPosition,
    LoudspeakerMovementDirection,
    LoudspeakerMovementDirectionDeclaration,
    LoudspeakerPositioningProposalStatus,
    Measurement,
    MovementDirectionDeclarationResolutionError,
    Peak,
    RoomDescription,
    RoomDimensions,
    Speaker,
    SpeakerOrientation,
    SpeakerPosition,
    SurfaceMaterialAssignment,
    SurfaceMaterialCoefficient,
    SurfaceMaterialDescription,
    SurfaceMaterialPrecision,
    SurfaceMaterialQuality,
    SurfaceMaterialSource,
)
from acousticbrain.report import (
    LoudspeakerPositioningExperimentPresenter,
    Report,
)
from acousticbrain.brain import AcousticBrain


ROOT = Path(__file__).resolve().parents[1]


def declaration(
    direction=LoudspeakerMovementDirection.BACKWARD,
    *,
    target="geometry_sbir.geometry_reflection.LEFT.MIC.front_wall",
    declaration_id="direction.user.front-wall",
):
    return LoudspeakerMovementDirectionDeclaration(
        declaration_id=declaration_id,
        target_geometry_candidate_id=target,
        direction=direction,
        provenance_code="USER_DECLARATION",
        source_id="operator.seb",
    )


def naturally_planned(*declarations, defer_asymmetry=True):
    quality_ids = (
        "LEFT",
        "MIC",
        "front_wall",
        "rear_wall",
        "left_wall",
        "right_wall",
        "floor",
        "ceiling",
    )
    geometry = RoomGeometryBuilder().from_description(RoomDescription(
        "Movement direction seam",
        RoomDimensions(5.0, 4.0, 3.0),
        speakers=(
            SpeakerPosition(
                "LEFT",
                1.0,
                1.0,
                1.0,
                SpeakerOrientation(0.0),
            ),
        ),
        listening_positions=(
            ListeningPosition("MIC", 3.0, 1.0, 1.0),
        ),
        geometry_data_quality=tuple(
            GeometryDatumQualityDescription(
                item,
                0.01,
                88.0,
                ("LASER_MEASURED",),
            )
            for item in quality_ids
        ),
    ))
    predictions = GeometrySBIRPredictionEngine().analyze(
        GeometryEarlyReflectionEngine().analyze(geometry),
        geometry,
    )
    correlations = SBIRGeometryCorrelationEngine().analyze(
        predictions,
        (Peak(86.0, 50.0, 1, 12.0),),
    )
    reasoning = AcousticReasoningEngine().analyze(
        sbir_geometry_correlations=correlations,
        room_geometry=geometry,
    )
    planning = ExperimentPlanner().plan(
        reasoning,
        deferred_action_codes=(
            ("VERIFY_SPEAKER_ROOM_ASYMMETRY",)
            if defer_asymmetry else ()
        ),
        movement_direction_declarations=tuple(declarations),
    )
    return geometry, planning


def public_pipeline_project():
    project = ImportEngine().load_directory(str(ROOT / "measurements"))
    project.add_speaker(
        Speaker(
            name="Left",
            distance_front_wall=0.82,
            distance_side_wall=0.55,
            height=1.05,
        )
    )
    project.add_speaker(
        Speaker(
            name="Right",
            distance_front_wall=0.82,
            distance_side_wall=0.55,
            height=1.05,
        )
    )
    material = SurfaceMaterialDescription(
        "measured-material",
        "Measured material",
        absorption_coefficients=(SurfaceMaterialCoefficient(125, 0.8),),
        diffusion_coefficients=(),
        source=SurfaceMaterialSource.MEASURED,
        confidence=88,
        quality=SurfaceMaterialQuality.VERIFIED,
        precision=SurfaceMaterialPrecision.OCTAVE,
        provenance_codes=("MEASURED_MATERIAL",),
    )
    surface_ids = (
        "front_wall",
        "rear_wall",
        "left_wall",
        "right_wall",
        "floor",
        "ceiling",
    )
    quality_ids = ("LEFT", "MIC", *surface_ids)
    project.room_description = RoomDescription(
        "Movement direction public pipeline",
        RoomDimensions(5.0, 4.0, 3.0),
        speakers=(
            SpeakerPosition(
                "LEFT",
                1.136,
                1.0,
                1.0,
                SpeakerOrientation(0.0),
            ),
        ),
        listening_positions=(ListeningPosition("MIC", 3.0, 1.0, 1.0),),
        geometry_data_quality=tuple(
            GeometryDatumQualityDescription(
                item,
                0.01,
                88.0,
                ("LASER_MEASURED",),
            )
            for item in quality_ids
        ),
        materials=(material,),
        material_assignments=tuple(
            SurfaceMaterialAssignment(
                f"assignment.{surface_id}",
                material.material_id,
                surface_id=surface_id,
                description_confidence=88,
                provenance_codes=("MEASURED_ASSIGNMENT",),
            )
            for surface_id in surface_ids
        ),
    )
    return project


def complete_asymmetry_experiment(brain, project):
    service = OptimizationSessionService()
    session_context = service.create("movement-direction-seam")
    brain.analyze(project, session_context=session_context)
    service.start_iteration(
        session_context,
        ExperimentProtocol(
            experiment_id="completed-asymmetry-experiment",
            hypothesis_code="ASYMMETRIC_SPEAKER_ROOM_INTERACTION",
            action_code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            label="Completed controlled asymmetry experiment",
            fact_codes=(),
        ),
    )
    brain.analyze(project, session_context=session_context)
    service.start_iteration(
        session_context,
        ExperimentProtocol(
            experiment_id="capture-positioning-proposal",
            hypothesis_code="SBIR_PLACEMENT_INTERACTION",
            action_code="CAPTURE_POSITIONING_PROPOSAL",
            label="Capture the planned positioning proposal",
            fact_codes=(),
        ),
    )
    return session_context


def planned_direction_result(parameters, *declarations):
    geometry, planning = naturally_planned(*declarations)
    candidate = replace(
        planning.plan.recommended_candidate,
        parameters={
            **planning.plan.recommended_candidate.parameters,
            **parameters,
        },
    )
    planning = replace(
        planning,
        plan=replace(
            planning.plan,
            ordered_candidates=(candidate,),
            recommended_candidate=candidate,
        ),
    )
    return LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=planning,
        room_geometry=geometry,
        measurements_available=True,
    )


@pytest.mark.parametrize(
    "direction",
    (
        LoudspeakerMovementDirection.FORWARD,
        LoudspeakerMovementDirection.BACKWARD,
    ),
)
def test_declaration_accepts_longitudinal_direction(direction):
    value = declaration(direction)
    assert value.direction is direction
    with pytest.raises(FrozenInstanceError):
        value.direction = LoudspeakerMovementDirection.OUTWARD


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("declaration_id", ""),
        ("target_geometry_candidate_id", " "),
        ("source_id", ""),
        ("provenance_code", "PROTOCOL_DECLARATION"),
        ("direction", "BACKWARD"),
    ),
)
def test_declaration_rejects_invalid_contract_fields(field, value):
    values = declaration().__dict__.copy()
    values[field] = value
    with pytest.raises(ValueError):
        LoudspeakerMovementDirectionDeclaration(**values)


def test_planner_attaches_declaration_by_exact_geometry_candidate_identity():
    expected = declaration()
    _, baseline = naturally_planned()
    _, planning = naturally_planned(expected)
    candidate = planning.plan.recommended_candidate
    assert candidate is not None
    assert candidate.movement_direction_declaration is expected
    assert candidate.parameters["geometry_candidate_id"] == (
        expected.target_geometry_candidate_id
    )
    assert "movement_direction" not in candidate.parameters
    assert replace(candidate, movement_direction_declaration=None) == (
        baseline.plan.recommended_candidate
    )
    assert tuple(
        replace(item, movement_direction_declaration=None)
        for item in planning.plan.ordered_candidates
    ) == baseline.plan.ordered_candidates


def test_public_analyze_transports_declarations_to_pipeline():
    expected = declaration()

    class RecordingPipeline:
        def __init__(self):
            self.arguments = None

        def run(self, project, **arguments):
            self.arguments = project, arguments
            return "report"

    brain = AcousticBrain()
    brain.pipeline = RecordingPipeline()
    project = object()
    assert brain.analyze(
        project,
        movement_direction_declarations=(expected,),
    ) == "report"
    assert brain.pipeline.arguments[0] is project
    assert brain.pipeline.arguments[1]["movement_direction_declarations"] == (
        expected,
    )


def test_unknown_target_and_duplicate_target_are_structured_errors():
    with pytest.raises(MovementDirectionDeclarationResolutionError) as unknown:
        naturally_planned(declaration(target="geometry.unknown"))
    assert unknown.value.code == "MOVEMENT_DIRECTION_TARGET_NOT_FOUND"

    with pytest.raises(MovementDirectionDeclarationResolutionError) as conflict:
        naturally_planned(
            declaration(),
            declaration(
                LoudspeakerMovementDirection.FORWARD,
                declaration_id="direction.user.conflict",
            ),
        )
    assert conflict.value.code == "CONFLICTING_MOVEMENT_DIRECTION_DECLARATIONS"


def test_typed_direction_reaches_engine_and_true_report_without_transformation():
    expected = declaration()
    geometry, planning = naturally_planned(expected)
    result = LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=planning,
        room_geometry=geometry,
        measurements_available=True,
    )
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.ALREADY_PLANNED
    assert result.proposal.movement_direction is expected.direction
    assert result.proposal.step_distance_m == 0.10
    assert result.proposal.movement_direction_declaration_id == expected.declaration_id
    assert result.proposal.movement_direction_source_id == expected.source_id
    assert (
        result.proposal.movement_direction_provenance_code
        == expected.provenance_code
    )
    assert result.proposal.source_geometry_candidate_id == (
        expected.target_geometry_candidate_id
    )

    context = type(
        "Context",
        (),
        {"loudspeaker_positioning_experiment_analysis": result},
    )()
    report = Report(project_name="Movement direction seam")
    report.loudspeaker_positioning_experiment = (
        LoudspeakerPositioningExperimentPresenter().present(context)
    )
    assert report.loudspeaker_positioning_experiment.proposal.movement_direction == (
        expected.direction.value
    )


def test_public_mono_analysis_exposes_typed_direction_in_true_report():
    expected = declaration()
    project = public_pipeline_project()
    brain = AcousticBrain()
    session_context = complete_asymmetry_experiment(brain, project)

    report = brain.analyze(
        project,
        session_context=session_context,
        plan_experiments=True,
        movement_direction_declarations=(expected,),
    )

    assert report.experiment_planning.status == "READY"
    assert report.experiment_planning.recommended_candidate.candidate_id == (
        "experiment_candidate.sbir_placement_interaction"
    )
    proposal = report.loudspeaker_positioning_experiment.proposal
    assert proposal.movement_direction == expected.direction.value
    assert proposal.movement_direction_declaration_id == expected.declaration_id
    assert proposal.movement_direction_source_id == expected.source_id
    assert proposal.movement_direction_provenance_code == expected.provenance_code
    assert proposal.source_geometry_candidate_id == (
        expected.target_geometry_candidate_id
    )
    assert proposal.source_surface_id == "front_wall"
    assert proposal.step_distance_m == 0.10


def test_public_multi_analysis_uses_declaration_only_in_final_current_pipeline(
    monkeypatch,
):
    expected = declaration()
    session = AcousticSession.auto_open(ROOT / "measurements")
    for imported in session.experiments:
        if imported.project is not None:
            configured = public_pipeline_project()
            imported.project.speakers = configured.speakers
            imported.project.room_description = configured.room_description
    monkeypatch.setattr(
        AcousticSession,
        "auto_open",
        classmethod(lambda cls, path: session),
    )

    report = AcousticBrain().analyze(
        measurement_root=ROOT / "measurements",
        compare_experiments=True,
        movement_direction_declarations=(expected,),
    )

    assert report.experiment_planning.status == "READY"
    assert report.experiment_planning.recommended_candidate.candidate_id == (
        "experiment_candidate.sbir_placement_interaction"
    )
    proposal = report.loudspeaker_positioning_experiment.proposal
    assert proposal.movement_direction == expected.direction.value
    assert proposal.movement_direction_declaration_id == expected.declaration_id
    assert proposal.movement_direction_source_id == expected.source_id
    assert proposal.movement_direction_provenance_code == expected.provenance_code
    assert proposal.source_geometry_candidate_id == (
        expected.target_geometry_candidate_id
    )
    assert report.experiment_comparison is not None


@pytest.mark.parametrize(
    "direction",
    (
        LoudspeakerMovementDirection.INWARD,
        LoudspeakerMovementDirection.OUTWARD,
    ),
)
def test_lateral_direction_is_blocked_for_longitudinal_sbir(direction):
    geometry, planning = naturally_planned(declaration(direction))
    result = LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=planning,
        room_geometry=geometry,
        measurements_available=True,
    )
    assert result.proposal is None
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE
    assert result.blocking_reason_codes == (
        "MOVEMENT_DIRECTION_INCOMPATIBLE_WITH_LONGITUDINAL_SBIR",
    )


def test_typed_and_conflicting_historical_direction_are_blocked():
    expected = declaration(LoudspeakerMovementDirection.BACKWARD)
    geometry, planning = naturally_planned(expected)
    candidate = planning.plan.recommended_candidate
    conflicting_candidate = replace(
        candidate,
        parameters={
            **candidate.parameters,
            "movement_direction": "FORWARD",
        },
    )
    conflicting_plan = replace(
        planning,
        plan=replace(
            planning.plan,
            ordered_candidates=(conflicting_candidate,),
            recommended_candidate=conflicting_candidate,
        ),
    )
    result = LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=conflicting_plan,
        room_geometry=geometry,
        measurements_available=True,
    )
    assert result.proposal is None
    assert result.blocking_reason_codes == (
        "CONFLICTING_MOVEMENT_DIRECTION_DECLARATIONS",
    )


@pytest.mark.parametrize(
    "parameters",
    (
        {
            "movement_direction": "FORWARD",
            "proposed_direction": "BACKWARD",
        },
        {
            "movement_direction": "FORWARD",
            "direction": "BACKWARD",
        },
        {
            "proposed_direction": "BACKWARD",
            "direction": "FORWARD",
        },
        {
            "movement_direction": "SIDEWAYS",
            "proposed_direction": "BACKWARD",
            "direction": "FORWARD",
        },
    ),
)
def test_recognized_historical_direction_conflicts_are_blocked(parameters):
    result = planned_direction_result(parameters)

    assert result.proposal is None
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE
    assert result.blocking_reason_codes == (
        "CONFLICTING_MOVEMENT_DIRECTION_DECLARATIONS",
    )


def test_historical_conflict_does_not_depend_on_mapping_order():
    first = planned_direction_result({
        "movement_direction": "FORWARD",
        "proposed_direction": "BACKWARD",
    })
    second = planned_direction_result({
        "proposed_direction": "BACKWARD",
        "movement_direction": "FORWARD",
    })

    assert first == second
    assert first.blocking_reason_codes == (
        "CONFLICTING_MOVEMENT_DIRECTION_DECLARATIONS",
    )


@pytest.mark.parametrize(
    ("parameters", "expected"),
    (
        (
            {
                "movement_direction": "FORWARD",
                "proposed_direction": "FORWARD",
            },
            LoudspeakerMovementDirection.FORWARD,
        ),
        (
            {
                "movement_direction": "BACKWARD",
                "proposed_direction": "BACKWARD",
                "direction": "BACKWARD",
            },
            LoudspeakerMovementDirection.BACKWARD,
        ),
        (
            {"direction": "FORWARD"},
            LoudspeakerMovementDirection.FORWARD,
        ),
    ),
)
def test_concordant_historical_directions_resolve_once(parameters, expected):
    result = planned_direction_result(parameters)

    assert result.proposal_status is LoudspeakerPositioningProposalStatus.ALREADY_PLANNED
    assert result.proposal.movement_direction is expected


def test_typed_direction_does_not_mask_a_second_historical_conflict():
    expected = declaration(LoudspeakerMovementDirection.FORWARD)
    result = planned_direction_result(
        {
            "movement_direction": "FORWARD",
            "proposed_direction": "BACKWARD",
        },
        expected,
    )

    assert result.proposal is None
    assert result.blocking_reason_codes == (
        "CONFLICTING_MOVEMENT_DIRECTION_DECLARATIONS",
    )


def test_typed_and_concordant_historical_directions_preserve_provenance():
    expected = declaration(LoudspeakerMovementDirection.FORWARD)
    result = planned_direction_result(
        {
            "movement_direction": "FORWARD",
            "proposed_direction": "FORWARD",
        },
        expected,
    )

    assert result.proposal.movement_direction is expected.direction
    assert result.proposal.movement_direction_declaration_id == expected.declaration_id
    assert result.proposal.movement_direction_source_id == expected.source_id
    assert (
        result.proposal.movement_direction_provenance_code
        == expected.provenance_code
    )


@pytest.mark.parametrize(
    ("parameters", "typed", "status", "expected"),
    (
        (
            {"movement_direction": "SIDEWAYS"},
            None,
            LoudspeakerPositioningProposalStatus.MISSING_DIRECTION,
            None,
        ),
        (
            {
                "movement_direction": "SIDEWAYS",
                "proposed_direction": "FORWARD",
            },
            None,
            LoudspeakerPositioningProposalStatus.ALREADY_PLANNED,
            LoudspeakerMovementDirection.FORWARD,
        ),
        (
            {
                "movement_direction": "SIDEWAYS",
                "proposed_direction": "UNKNOWN",
            },
            None,
            LoudspeakerPositioningProposalStatus.MISSING_DIRECTION,
            None,
        ),
        (
            {"movement_direction": "SIDEWAYS"},
            declaration(LoudspeakerMovementDirection.BACKWARD),
            LoudspeakerPositioningProposalStatus.ALREADY_PLANNED,
            LoudspeakerMovementDirection.BACKWARD,
        ),
    ),
)
def test_unrecognized_historical_values_preserve_existing_policy(
    parameters,
    typed,
    status,
    expected,
):
    result = planned_direction_result(
        parameters,
        *((typed,) if typed is not None else ()),
    )

    assert result.proposal_status is status
    assert (
        result.proposal.movement_direction if result.proposal is not None else None
    ) is expected


def test_absence_preserves_historical_missing_direction():
    geometry, planning = naturally_planned()
    result = LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=planning,
        room_geometry=geometry,
        measurements_available=True,
    )
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.MISSING_DIRECTION
    assert result.blocking_reason_codes == (
        "EXPLICIT_MOVEMENT_DIRECTION_MISSING",
    )


def test_declaration_for_non_recommended_candidate_is_not_applied():
    expected = declaration()
    geometry, planning = naturally_planned(expected, defer_asymmetry=False)
    assert planning.plan.recommended_candidate is not None
    assert (
        planning.plan.recommended_candidate.movement_direction_declaration
        is None
    )
    sbir = next(
        item
        for item in planning.plan.ordered_candidates
        if item.movement_direction_declaration is expected
    )
    assert sbir is not planning.plan.recommended_candidate
    result = LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=planning,
        room_geometry=geometry,
        measurements_available=True,
    )
    assert result.proposal is None


def test_analysis_context_preserves_historical_positional_construction():
    measurement = Measurement("stereo")
    synthesis = AcousticObservationSynthesis()

    context = AnalysisContext(measurement, synthesis)

    assert context.measurement is measurement
    assert context.acoustic_observation_synthesis is synthesis
    assert context.movement_direction_declarations == ()


def test_analysis_context_accepts_named_movement_direction_declarations():
    measurement = Measurement("stereo")
    expected = declaration()

    context = AnalysisContext(
        measurement=measurement,
        movement_direction_declarations=(expected,),
    )

    assert context.measurement is measurement
    assert context.acoustic_observation_synthesis is None
    assert context.movement_direction_declarations == (expected,)
