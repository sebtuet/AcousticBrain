from pathlib import Path
import json
import shutil

from acousticbrain.brain import AcousticBrain
import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_explicit_mode_analyzes_discovered_experiments_without_business_history():
    report = AcousticBrain().analyze(
        measurement_root=ROOT / "measurements",
        compare_experiments=True,
        detailed_comparison_traceability=True,
    )

    assert report.experiment_comparison.chronology == (
        "baseline", "exp-001", "exp-002", "exp-003", "exp-004", "exp-005"
    )
    assert len(report.experiment_comparison.local_comparisons) == 5
    assert len(report.experiment_comparison.cumulative_comparisons) == 5
    assert len(report.experiment_campaigns) == 1
    campaign = report.experiment_campaigns[0]
    assert campaign.campaign_code == "VERIFY_MODAL_BASS_PERSISTENCE"
    assert campaign.status == "PARTIALLY_RESOLVED"
    assert campaign.objective_label == (
        "déterminer si la persistance du grave dépend du point d’écoute"
    )
    assert campaign.reference_experiment_id == "exp-003"
    assert tuple(item.experiment_id for item in campaign.measurements) == (
        "exp-003", "exp-004", "exp-005"
    )
    assert "un effet local de position est soutenu" in campaign.result_labels
    assert "la composante modale globale reste non discriminée" in (
        campaign.result_labels
    )
    metric = campaign.metrics[0]
    assert metric.reference_value == pytest.approx(0.790, abs=0.001)
    assert metric.best_value == pytest.approx(0.636, abs=0.001)
    assert metric.best_experiment_id == "exp-005"
    assert campaign.next_discrimination_label == (
        "variation contrôlée de la position de la source, microphone fixe"
    )
    assert report.experiment_comparison.local_comparisons[0].trace_id
    exp004 = next(
        item for item in report.experiment_comparison.local_comparisons
        if item.after_experiment_id == "exp-004"
    )
    exp005 = next(
        item for item in report.experiment_comparison.local_comparisons
        if item.after_experiment_id == "exp-005"
    )
    assert exp004.before_experiment_id == "exp-003"
    assert exp005.before_experiment_id == "exp-003"
    assert exp005.source_protocol_id == (
        "protocol.verify_modal_bass_persistence.v1"
    )
    assert exp005.experiment_parameters == (
        ("listening_position_offset_m", 0.3),
        ("position_role", "FORWARD"),
    )
    assert exp004.acoustic_outcome == "UNCHANGED"
    assert exp005.acoustic_outcome == "IMPROVED"
    assert exp005.outcome == "UNCHANGED"
    assert exp005.experimental_result_labels == (
        "un effet local de position est soutenu",
    )
    assert "la décroissance grave varie selon la position d’écoute" in (
        exp005.observation_labels
    )
    assert report.optimization_session is None


def test_comparison_is_absent_when_explicit_mode_is_disabled():
    report = AcousticBrain().analyze(measurement_root=ROOT / "measurements")

    assert report.experiment_comparison is None
    assert report.optimization_session is None


def test_causal_mode_projects_only_explicit_repository_steps():
    report = AcousticBrain().analyze(
        measurement_root=ROOT / "measurements",
        compare_experiments=True,
        analyze_causal_discrimination=True,
        plan_experiments=True,
    )

    assert report.experiment_comparison is not None
    assert report.causal_discrimination is not None
    assert tuple(
        item.step_code for item in report.causal_discrimination.completed_steps
    ) == (
        "STEP_0_BASELINE",
        "STEP_1_LEFT_RIGHT_REMEASUREMENT",
        "STEP_3_SIGNAL_CHAIN_SWAP",
    )
    assert report.causal_discrimination.remaining_discrimination_codes == (
        "LOUDSPEAKER_VS_ROOM_SIDE",
    )
    assert report.causal_discrimination.remaining_step_codes == ()
    assert report.causal_discrimination.deferred_step_codes == (
        "STEP_2_SPEAKER_SWAP",
    )
    assert report.causal_discrimination.recommended_next_protocol is None
    assert report.causal_discrimination.status == "DEFERRED"
    decision = report.causal_discrimination.discrimination_decisions[0]
    assert (decision.discrimination_code, decision.status, decision.reason) == (
        "LOUDSPEAKER_VS_ROOM_SIDE", "DEFERRED", "USER_DECISION"
    )
    assert report.causal_discrimination.outcome == "INCONCLUSIVE"
    exp002 = next(
        item for item in report.experiment_comparison.local_comparisons
        if item.after_experiment_id == "exp-002"
    )
    assert exp002.outcome == "WEAKER"
    deferred_recommendation = next(
        item for item in report.recommendations
        if item.code == "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    )
    assert deferred_recommendation.status.name == "DEFERRED"
    assert deferred_recommendation.status_reason == "USER_DECISION"
    planned_asymmetry = next(
        item for item in report.experiment_planning.all_candidates
        if item.hypothesis_code == "ASYMMETRIC_SPEAKER_ROOM_INTERACTION"
    )
    assert planned_asymmetry.eligible is False
    assert "USER_DEFERRED" in planned_asymmetry.ineligibility_reasons
    planned_modal = next(
        item for item in report.experiment_planning.all_candidates
        if item.hypothesis_code == "MODAL_BASS_PERSISTENCE"
    )
    assert planned_modal.eligible is False
    assert "ALREADY_COMPLETED" in planned_modal.ineligibility_reasons
    multi_position = next(
        item for item in report.recommendations
        if item.code == "MEASURE_MULTIPLE_POSITIONS"
    )
    assert multi_position.status.name == "COMPLETED"
    modal_domain = next(
        item for item in report.global_analysis.domains
        if item.code == "MODAL_DENSITY"
    )
    assert modal_domain.recommendation_statuses == (
        ("MEASURE_MULTIPLE_POSITIONS", "COMPLETED"),
    )
    reasoning_diagnostic = next(
        item for item in report.diagnostics
        if item.title == "Raisonnement acoustique déterministe"
    )
    assert any(
        "VERIFY_SPEAKER_ROOM_ASYMMETRY" in item
        and "DEFERRED (USER_DECISION)" in item
        for item in reasoning_diagnostic.recommendations
    )
    assert report.experiment_planning.recommended_candidate is None
    assert "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS" in (
        report.experiment_planning.uncovered_active_action_codes
    )
    assert report.optimization_session is None


def test_causal_mode_requires_explicit_experiment_comparison():
    with pytest.raises(ValueError, match="compare_experiments=True"):
        AcousticBrain().analyze(
            measurement_root=ROOT / "measurements",
            analyze_causal_discrimination=True,
        )


def test_explicit_manifest_steps_are_projected_in_final_report(tmp_path):
    measurement_root = tmp_path / "measurements"
    for experiment_id in ("baseline", "exp-001"):
        shutil.copytree(
            ROOT / "measurements" / experiment_id,
            measurement_root / experiment_id,
        )
    causal_steps = {
        "baseline": {
            "protocol_code": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
            "step_code": "STEP_0_BASELINE",
            "step_index": 0,
            "controlled_variable_codes": [
                "ROOM_CONFIGURATION", "MEASUREMENT_LEVEL"
            ],
            "changed_variable_codes": [],
            "unknown_variable_codes": [],
            "observation_codes": [],
        },
        "exp-001": {
            "protocol_code": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
            "step_code": "STEP_1_LEFT_RIGHT_REMEASUREMENT",
            "step_index": 1,
            "controlled_variable_codes": [
                "LOUDSPEAKER_ASSIGNMENT",
                "SIGNAL_CHAIN_ASSIGNMENT",
                "ROOM_SIDE",
                "MICROPHONE_POSITION",
            ],
            "changed_variable_codes": ["MEASUREMENT_ACQUISITION"],
            "unknown_variable_codes": [],
            "observation_codes": ["CHANNEL_SPECIFIC_PATTERN_CHANGED"],
        },
    }
    for experiment_id, causal_step in causal_steps.items():
        manifest_path = measurement_root / experiment_id / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["causal_protocol_step"] = causal_step
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = AcousticBrain().analyze(
        measurement_root=measurement_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )

    assert report.causal_discrimination.protocol_code == (
        "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    )
    assert tuple(
        item.step_code for item in report.causal_discrimination.completed_steps
    ) == ("STEP_0_BASELINE", "STEP_1_LEFT_RIGHT_REMEASUREMENT")
    assert report.causal_discrimination.recommended_next_protocol == (
        "STEP_2_SPEAKER_SWAP"
    )
    assert report.optimization_session is None
