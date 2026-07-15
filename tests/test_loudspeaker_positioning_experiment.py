import copy
import json
from types import SimpleNamespace

import pytest

from acousticbrain.analysis import LoudspeakerPositioningExperimentEngine
from acousticbrain.application import PositioningProposalDeclarationService
from acousticbrain.models import (
    ExperimentKind,
    LoudspeakerMovementAxis,
    LoudspeakerMovementDirection,
    LoudspeakerPositioningExperimentProposal,
    LoudspeakerPositioningProposalStatus,
    LoudspeakerPositioningTarget,
    Recommendation,
    RecommendationAnalysis,
    RecommendationPriority,
    RecommendationStatus,
)
from acousticbrain.report import (
    ActionOrientedPositioningPresenter,
    DecisionFirstReportPresenter,
    LoudspeakerPositioningExperimentPresenter,
    OneMinuteExecutiveSummaryPresenter,
    Report,
)


def recommendation(
    *,
    code="CHECK_STEREO_PLACEMENT",
    target="stereo_speakers",
    speaker_id="STEREO",
    direction="FORWARD",
    distance=None,
    priority=RecommendationPriority.HIGH,
    status=RecommendationStatus.ACTIVE,
):
    parameters = {}
    if speaker_id is not None:
        parameters["speaker_id"] = speaker_id
    if direction is not None:
        parameters["movement_direction"] = direction
    if distance is not None:
        parameters["proposed_displacement_m"] = distance
    return Recommendation(
        code=code,
        action="test",
        target=target,
        priority=priority,
        confidence=73.0,
        source_analyses=("SyntheticStructuredSource",),
        parameters=parameters,
        hypothesis_codes=("SYNTHETIC_POSITIONING_HYPOTHESIS",),
        status=status,
    )


def analyze(*items, measurements_available=True, planning=None, room_geometry=None):
    return LoudspeakerPositioningExperimentEngine().analyze(
        experiment_planning=planning,
        recommendation_analysis=RecommendationAnalysis(list(items)),
        room_geometry=room_geometry,
        measurements_available=measurements_available,
    )


@pytest.mark.parametrize(
    ("speaker_id", "target"),
    (
        ("LEFT", LoudspeakerPositioningTarget.LEFT_SPEAKER),
        ("RIGHT", LoudspeakerPositioningTarget.RIGHT_SPEAKER),
        ("STEREO", LoudspeakerPositioningTarget.BOTH_SPEAKERS),
    ),
)
def test_supported_targets_are_preserved(speaker_id, target):
    result = analyze(recommendation(speaker_id=speaker_id))
    assert result.proposal.target is target


@pytest.mark.parametrize(
    ("direction", "axis"),
    (
        ("FORWARD", LoudspeakerMovementAxis.LONGITUDINAL),
        ("BACKWARD", LoudspeakerMovementAxis.LONGITUDINAL),
        ("INWARD", LoudspeakerMovementAxis.LATERAL),
        ("OUTWARD", LoudspeakerMovementAxis.LATERAL),
    ),
)
def test_supported_directions_determine_only_their_axis(direction, axis):
    result = analyze(recommendation(direction=direction))
    assert result.proposal.movement_direction.value == direction
    assert result.proposal.movement_axis is axis


@pytest.mark.parametrize("distance", (None, 0, -0.1, float("nan")))
def test_missing_or_invalid_amplitude_uses_five_cm_protocol_step(distance):
    result = analyze(recommendation(distance=distance))
    assert result.proposal.step_distance_m == 0.05
    assert dict(result.proposal.provenance)["step_distance_m"] == (
        "OPERATIONAL_FIVE_CM_POLICY"
    )


@pytest.mark.parametrize(
    ("direction", "status"),
    (
        (None, LoudspeakerPositioningProposalStatus.MISSING_DIRECTION),
        ("LEFT", LoudspeakerPositioningProposalStatus.MISSING_DIRECTION),
        ("TOWARD_BETTER_SCORE", LoudspeakerPositioningProposalStatus.MISSING_DIRECTION),
    ),
)
def test_direction_is_never_derived_from_a_score_or_unknown_label(direction, status):
    result = analyze(recommendation(direction=direction))
    assert result.proposal is None
    assert result.proposal_status is status


@pytest.mark.parametrize("speaker_id", (None, "CENTER", "LISTENING_POSITION"))
def test_unknown_or_forbidden_target_never_creates_a_proposal(speaker_id):
    result = analyze(recommendation(target="speaker", speaker_id=speaker_id))
    assert result.proposal is None
    assert "LOUDSPEAKER_TARGET_AMBIGUOUS" in result.blocking_reason_codes


def test_real_exp006_shape_without_direction_stays_honestly_blocked():
    result = analyze(
        recommendation(direction=None),
        recommendation(
            code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            target="left_right_measurements_and_placement",
            speaker_id=None,
            direction=None,
            status=RecommendationStatus.DEFERRED,
        ),
    )
    assert result.proposal is None
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.MISSING_DIRECTION


def test_user_deferred_only_source_is_blocked():
    result = analyze(recommendation(status=RecommendationStatus.DEFERRED))
    assert result.proposal_status is (
        LoudspeakerPositioningProposalStatus.BLOCKED_BY_USER_DECISION
    )


def test_equal_priority_sources_are_ambiguous_and_not_order_dependent():
    left = recommendation(speaker_id="LEFT")
    right = recommendation(
        code="VERIFY_SPEAKER_ROOM_ASYMMETRY", speaker_id="RIGHT"
    )
    first = analyze(left, right)
    second = analyze(right, left)
    assert first.proposal is second.proposal is None
    assert first.proposal_status is LoudspeakerPositioningProposalStatus.AMBIGUOUS
    assert first.considered_source_ids == second.considered_source_ids


def test_higher_priority_unique_source_is_selected():
    result = analyze(
        recommendation(speaker_id="LEFT", priority=RecommendationPriority.HIGH),
        recommendation(
            code="VERIFY_SPEAKER_ROOM_ASYMMETRY",
            speaker_id="RIGHT",
            priority=RecommendationPriority.MEDIUM,
        ),
    )
    assert result.proposal.target is LoudspeakerPositioningTarget.LEFT_SPEAKER


def test_missing_lr_stereo_measurements_blocks_the_proposal():
    result = analyze(recommendation(), measurements_available=False)
    assert result.proposal is None
    assert "L_R_STEREO_MEASUREMENTS_UNAVAILABLE" in result.blocking_reason_codes


@pytest.mark.parametrize("code", ("UNRELATED_ACTION", "MEASURE_MULTIPLE_POSITIONS"))
def test_unrelated_or_listening_position_recommendation_is_ignored(code):
    result = analyze(recommendation(code=code, target="listening_area"))
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE


def test_existing_structured_distance_is_reused():
    result = analyze(recommendation(distance=0.10))
    assert result.proposal.step_distance_m == 0.10
    assert dict(result.proposal.provenance)["step_distance_m"] == "SOURCE_PARAMETER"


def test_proposal_has_required_controls_measurements_observables_and_causal_limit():
    proposal = analyze(recommendation(speaker_id="LEFT")).proposal
    assert proposal.required_measurements == ("L", "R", "L+R")
    assert proposal.tested_variable == "LOUDSPEAKER_POSITION"
    assert proposal.causality_status == "NOT_ESTABLISHED"
    assert "LISTENING_POSITION" in proposal.controlled_variables
    assert "MICROPHONE_POSITION" in proposal.controlled_variables
    assert "OTHER_LOUDSPEAKER_POSITION" in proposal.controlled_variables
    assert proposal.expected_observables


def test_both_speakers_does_not_claim_an_other_speaker_control():
    proposal = analyze(recommendation()).proposal
    assert "OTHER_LOUDSPEAKER_POSITION" not in proposal.controlled_variables
    assert "LOUDSPEAKER_PAIR_SYMMETRY" in proposal.controlled_variables


def test_observables_cover_frequency_bass_temporal_and_spatial_comparison():
    observables = set(analyze(recommendation()).proposal.expected_observables)
    assert {
        "global.domain.stereo.score",
        "bass_decay.maximum_decay_time_s",
        "etc.channel_specific_event_count",
        "spatial.left_right.level_difference_abs_db",
    } <= observables


def test_forward_motion_controls_pair_separation():
    proposal = analyze(recommendation(direction="FORWARD")).proposal
    assert "LOUDSPEAKER_SEPARATION" in proposal.controlled_variables


def test_lateral_motion_does_not_invent_pair_separation_control():
    proposal = analyze(recommendation(direction="INWARD")).proposal
    assert "LOUDSPEAKER_SEPARATION" not in proposal.controlled_variables


def test_proposal_identifier_and_result_are_deterministic():
    first = analyze(recommendation(speaker_id="LEFT", direction="OUTWARD"))
    second = analyze(recommendation(speaker_id="LEFT", direction="OUTWARD"))
    assert first == second
    assert first.proposal.proposal_id.endswith("left_speaker.outward.50mm")


def test_engine_does_not_mutate_recommendations_scores_or_order():
    source = RecommendationAnalysis([
        recommendation(speaker_id="LEFT"),
        recommendation(code="UNRELATED_ACTION"),
    ])
    before = copy.deepcopy(source)
    LoudspeakerPositioningExperimentEngine().analyze(
        recommendation_analysis=source,
        measurements_available=True,
    )
    assert source == before


def planned_candidate(**parameters):
    values = {
        "speaker_id": "LEFT",
        "movement_direction": "BACKWARD",
        "proposed_displacement_m": 0.10,
        "surface": "front_wall",
        "geometry_candidate_id": "candidate.LEFT.front_wall",
        "geometry_path_id": "path.LEFT.front_wall",
    }
    values.update(parameters)
    candidate = SimpleNamespace(
        candidate_id="experiment_candidate.sbir_placement_interaction",
        source_action_code="VERIFY_SBIR_PLACEMENT",
        hypothesis_code="SBIR_PLACEMENT_INTERACTION",
        source_protocol_id="protocol.temporary_move_speaker.v1",
        changed_variable_codes=("LOUDSPEAKER_POSITION",),
        parameters=values,
        observable_fact_codes=("SBIR_MOVES_WITH_SPEAKER",),
        confidence=81.0,
        controlled_variable_codes=("MICROPHONE_POSITION",),
        reversibility=SimpleNamespace(name="HIGH"),
    )
    return SimpleNamespace(plan=SimpleNamespace(recommended_candidate=candidate))


def test_existing_plan_wins_and_preserves_ten_cm():
    result = analyze(
        recommendation(speaker_id="RIGHT", direction="FORWARD"),
        planning=planned_candidate(),
        room_geometry=SimpleNamespace(speakers=(object(),)),
    )
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.ALREADY_PLANNED
    assert result.proposal.target is LoudspeakerPositioningTarget.LEFT_SPEAKER
    assert result.proposal.step_distance_m == 0.10


def test_geometry_dependent_plan_without_geometry_is_blocked():
    result = analyze(planning=planned_candidate(), room_geometry=None)
    assert result.proposal is None
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.MISSING_GEOMETRY


def test_plan_without_explicit_direction_is_blocked():
    result = analyze(
        planning=planned_candidate(movement_direction=None),
        room_geometry=SimpleNamespace(speakers=(object(),)),
    )
    assert result.proposal_status is LoudspeakerPositioningProposalStatus.MISSING_DIRECTION


def test_model_rejects_a_causal_claim():
    with pytest.raises(ValueError, match="cannot establish causality"):
        LoudspeakerPositioningExperimentProposal(
            **{
                **analyze(recommendation()).proposal.__dict__,
                "causality_status": "ESTABLISHED",
            }
        )


def presented_analysis(result):
    return LoudspeakerPositioningExperimentPresenter().present(SimpleNamespace(
        loudspeaker_positioning_experiment_analysis=result
    ))


def test_all_three_report_levels_present_a_positive_proposal_as_experimental():
    report = Report(project_name="synthetic")
    report.loudspeaker_positioning_experiment = presented_analysis(
        analyze(recommendation(speaker_id="LEFT", direction="OUTWARD"))
    )
    action = ActionOrientedPositioningPresenter().present(report)
    decision = DecisionFirstReportPresenter().present(report)
    minute = OneMinuteExecutiveSummaryPresenter().present(decision)
    assert action.status == "ACTION_AVAILABLE"
    assert "réversible" in action.action
    assert decision.positioning_proposal_id is not None
    assert any("pas une position optimale" in item for item in minute.reasons)
    assert "amélioration non garantie" in minute.confidence[2]


def test_report_missing_direction_does_not_fall_back_to_generic_placement_advice():
    report = Report(project_name="real-exp006-shape")
    report.loudspeaker_positioning_experiment = presented_analysis(
        analyze(recommendation(direction=None))
    )
    action = ActionOrientedPositioningPresenter().present(report)
    decision = DecisionFirstReportPresenter().present(report)
    assert action.status == "MISSING_DIRECTION"
    assert action.target is action.direction is action.amplitude is None
    assert "Aucune direction" in decision.action


def test_report_ambiguity_names_no_single_selection():
    report = Report(project_name="ambiguous")
    report.loudspeaker_positioning_experiment = presented_analysis(analyze(
        recommendation(speaker_id="LEFT"),
        recommendation(code="VERIFY_SPEAKER_ROOM_ASYMMETRY", speaker_id="RIGHT"),
    ))
    action = ActionOrientedPositioningPresenter().present(report)
    assert action.status == "AMBIGUOUS"
    assert "ne peut pas en sélectionner une seule" in action.action


def test_accepted_proposal_persists_a_pr043_controlled_intervention(tmp_path):
    root = tmp_path / "measurements"
    (root / "exp-005").mkdir(parents=True)
    (root / "exp-007").mkdir()
    measurement = root / "exp-007" / "left.txt"
    measurement.write_text("measurement", encoding="utf-8")
    proposal = analyze(recommendation(speaker_id="LEFT")).proposal
    service = PositioningProposalDeclarationService()
    declaration = service.declare(
        root,
        experiment_code="exp-007",
        reference_experiment_code="exp-005",
        proposal=proposal,
        user_note="Accepted reversible test.",
    )
    first = (root / "exp-007" / "manifest.json").read_bytes()
    service.declare(
        root,
        experiment_code="exp-007",
        reference_experiment_code="exp-005",
        proposal=proposal,
        user_note="Accepted reversible test.",
    )
    assert first == (root / "exp-007" / "manifest.json").read_bytes()
    payload = json.loads(first)
    value = payload["experiment_declaration"]
    assert declaration.experiment_kind is ExperimentKind.CONTROLLED_INTERVENTION
    assert value["modified_variables"] == ["LOUDSPEAKER_POSITION"]
    assert proposal.proposal_id in value["field_provenance"]["experiment_kind"]
    assert measurement.read_text(encoding="utf-8") == "measurement"


def test_declaration_conversion_rejects_non_positioning_proposal(tmp_path):
    root = tmp_path / "measurements"
    (root / "base").mkdir(parents=True)
    (root / "next").mkdir()
    proposal = analyze(recommendation()).proposal
    proposal = SimpleNamespace(
        **{**proposal.__dict__, "tested_variable": "LISTENING_POSITION"}
    )
    with pytest.raises(ValueError, match="loudspeaker-positioning"):
        PositioningProposalDeclarationService().declare(
            root,
            experiment_code="next",
            reference_experiment_code="base",
            proposal=proposal,
        )


def test_acceptance_cli_requires_explicit_matching_proposal_and_creates_draft(
    tmp_path, monkeypatch, capsys
):
    from acousticbrain.commands import accept_positioning_proposal as command

    root = tmp_path / "measurements"
    (root / "exp-006").mkdir(parents=True)
    proposal = analyze(recommendation()).proposal
    captured = {}

    class Brain:
        def analyze(self, **kwargs):
            captured["analysis_arguments"] = kwargs
            return SimpleNamespace(
                loudspeaker_positioning_experiment=SimpleNamespace(
                    proposal=proposal
                )
            )

    class Service:
        def declare(self, measurement_root, **kwargs):
            captured["declaration"] = (measurement_root, kwargs)
            return SimpleNamespace(
                experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION
            )

    monkeypatch.setattr(command, "AcousticBrain", Brain)
    monkeypatch.setattr(command, "PositioningProposalDeclarationService", Service)
    command.main([
        str(root),
        "--proposal-id", proposal.proposal_id,
        "--experiment", "exp-007",
        "--reference", "exp-006",
    ])
    assert (root / "exp-007").is_dir()
    assert captured["declaration"][1]["proposal"] is proposal
    assert "Accepted" in capsys.readouterr().out


def test_acceptance_cli_rejects_a_stale_or_different_proposal_id(
    tmp_path, monkeypatch
):
    from acousticbrain.commands import accept_positioning_proposal as command

    root = tmp_path / "measurements"
    (root / "exp-006").mkdir(parents=True)
    proposal = analyze(recommendation()).proposal
    monkeypatch.setattr(
        command,
        "AcousticBrain",
        lambda: SimpleNamespace(analyze=lambda **kwargs: SimpleNamespace(
            loudspeaker_positioning_experiment=SimpleNamespace(proposal=proposal)
        )),
    )
    with pytest.raises(ValueError, match="not currently eligible"):
        command.main([
            str(root),
            "--proposal-id", "stale-proposal",
            "--experiment", "exp-007",
            "--reference", "exp-006",
        ])
    assert not (root / "exp-007").exists()
