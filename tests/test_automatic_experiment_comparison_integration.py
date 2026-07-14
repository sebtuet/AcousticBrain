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
        "baseline", "exp-001", "exp-002"
    )
    assert len(report.experiment_comparison.local_comparisons) == 2
    assert len(report.experiment_comparison.cumulative_comparisons) == 2
    assert report.experiment_comparison.local_comparisons[0].trace_id
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
    assert report.experiment_comparison.local_comparisons[-1].outcome == "WEAKER"
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
