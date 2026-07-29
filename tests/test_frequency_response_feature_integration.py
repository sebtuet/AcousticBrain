import hashlib
import json
import shutil
from pathlib import Path

import main as acousticbrain_main
import pytest

from acousticbrain.application import AcousticSession
from acousticbrain.brain import AcousticBrain
from acousticbrain.models import (
    FrequencyFeatureChannelClassification,
    FrequencyResponseFeatureType,
    MeasurementAnalysisFamily,
    MeasurementReadinessStatus,
)


BASELINE = Path(__file__).resolve().parents[1] / "measurements" / "baseline"


def copy_campaign(tmp_path):
    root = tmp_path / "measurements"
    shutil.copytree(BASELINE, root / "baseline")
    return root


def hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_real_pipeline_analyzes_all_baseline_txt_without_mutating_campaign(tmp_path):
    root = copy_campaign(tmp_path)
    before = hashes(root)
    session = AcousticSession.auto_open(root)

    report, context = AcousticBrain().pipeline.run(
        session.current_project,
        experiment_descriptors=session.descriptors,
        synthesize_evidence_acquisition=True,
        return_context=True,
    )

    analysis = context.frequency_response_feature_analysis
    assert analysis is not None
    assert tuple(item.sample_count for item in analysis.channels) == (957, 957, 957)
    assert all(item.features for item in analysis.channels)
    assert any(
        feature.feature_type is FrequencyResponseFeatureType.PEAK
        for item in analysis.channels
        for feature in item.features
    )
    assert any(
        feature.feature_type is FrequencyResponseFeatureType.NOTCH
        for item in analysis.channels
        for feature in item.features
    )
    assert any(
        item.classification is FrequencyFeatureChannelClassification.COMMON
        for item in analysis.left_right_comparisons
    )
    observation_ids = tuple(
        item.observation_id for item in report.acoustic_observations.observations
    )
    assert "FREQUENCY_RESPONSE_FEATURE_FACTS" in observation_ids
    assert "LEFT_RIGHT_FREQUENCY_FEATURE_COMPARISON_FACTS" in observation_ids
    assert "STEREO_FREQUENCY_FEATURE_RELATION_FACTS" in observation_ids
    feature_observation = next(
        item
        for item in report.acoustic_observations.observations
        if item.observation_id == "FREQUENCY_RESPONSE_FEATURE_FACTS"
    )
    assert feature_observation.source_analysis_ids == (
        "FrequencyResponseFeatureAnalysis",
    )
    assert any(
        value.startswith("frequency_features.left.peak_count=")
        for value in feature_observation.supporting_evidence
    )
    assert any(
        value.startswith("frequency_features.deepest_notch.depth_db=")
        for value in feature_observation.supporting_evidence
    )
    assert "do not establish cause" in " ".join(feature_observation.limitations)
    frequency_readiness = next(
        item
        for item in context.measurement_readiness_analysis.analyses
        if item.family is MeasurementAnalysisFamily.FREQUENCY
    )
    assert frequency_readiness.status is MeasurementReadinessStatus.AVAILABLE
    assert frequency_readiness.missing_facts == ()
    assert before == hashes(root)


def test_new_observations_do_not_enter_existing_causal_reasoning(tmp_path):
    root = copy_campaign(tmp_path)

    report = AcousticBrain().analyze(
        measurement_root=root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
    )

    new_observations = {
        "FREQUENCY_RESPONSE_FEATURE_FACTS",
        "LEFT_RIGHT_FREQUENCY_FEATURE_COMPARISON_FACTS",
        "STEREO_FREQUENCY_FEATURE_RELATION_FACTS",
    }
    reasoning_observations = {
        observation_id
        for item in report.deterministic_acoustic_reasoning.reasonings
        for observation_id in item.observation_ids
    }
    assert new_observations.isdisjoint(reasoning_observations)
    assert all(
        "RECOMMEND_GEOMETRY_ADJUSTMENT" not in item.title
        for item in report.deterministic_corrective_actions.actions
    )


@pytest.mark.parametrize(
    ("source_plan_id", "expected_source", "expected_status"),
    (
        (None, "none", "PLAN_NOT_REFERENCED"),
        (
            "EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_"
            "REASONING_RESOLVE_CONTRADICTION",
            "EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_"
            "REASONING_RESOLVE_CONTRADICTION",
            "PLAN_REFERENCE_RESOLVED",
        ),
        (
            "EVIDENCE_ACQUISITION_PLAN_UNKNOWN",
            "EVIDENCE_ACQUISITION_PLAN_UNKNOWN",
            "PLAN_REFERENCE_UNKNOWN",
        ),
    ),
)
def test_standard_cli_resolves_plan_reference_against_real_pipeline(
    tmp_path,
    capsys,
    source_plan_id,
    expected_source,
    expected_status,
):
    root = copy_campaign(tmp_path)
    manifest_path = root / "baseline" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if source_plan_id is not None:
        manifest["source_evidence_acquisition_plan_id"] = source_plan_id
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    acousticbrain_main.run(root)

    output = capsys.readouterr().out
    assert f"Source evidence acquisition plan : {expected_source}" in output
    assert f"Plan reference status : {expected_status}" in output
    assert "NEXT RECOMMENDED EXPERIMENT" not in output


def test_standard_cli_exposes_complete_channel_isolation_coverage(
    tmp_path,
    capsys,
):
    root = copy_campaign(tmp_path)
    manifest_path = root / "baseline" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "source_evidence_acquisition_plan_id": (
            "EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_"
            "REASONING_RESOLVE_CONTRADICTION"
        ),
        "experiment_declaration": {
            "schema_version": 1,
            "experiment_kind": "CONTROLLED_INTERVENTION",
            "reference_experiment_code": "pre-plan-baseline",
            "modified_variables": ["active_channel"],
            "controlled_variables": [
                "gain",
                "microphone_position",
                "signal_chain",
                "time_window",
            ],
            "user_note": None,
            "field_provenance": {
                "experiment_kind": "USER_MANIFEST",
                "reference_experiment_code": "USER_MANIFEST",
                "modified_variables": "USER_MANIFEST",
                "controlled_variables": "USER_MANIFEST",
                "user_note": "USER_MANIFEST",
            },
        },
        "channel_isolation_declaration": {
            "repeated_channels": ["LEFT", "RIGHT"],
            "available_inputs": [
                "documented_microphone_position",
                "existing_acquisition_settings",
            ],
            "controlled_variables": [
                "gain",
                "microphone_position",
                "signal_chain",
                "time_window",
            ],
            "independent_variables": ["active_channel"],
            "measurements": [
                "left_channel_response",
                "right_channel_response",
                "repeat_response",
            ],
        },
    })
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    acousticbrain_main.run(root)

    output = capsys.readouterr().out
    assert "Plan reference status : PLAN_REFERENCE_RESOLVED" in output
    assert "Plan coverage status : PLAN_COVERAGE_COMPLETE" in output
    assert "Missing plan requirements :\n- none" in output
    assert "NEXT RECOMMENDED EXPERIMENT" not in output


def test_cli_exposes_readiness_observations_and_full_assessment_deterministically(
    tmp_path,
    capsys,
):
    root = copy_campaign(tmp_path)
    original_manifest = json.loads(
        (root / "baseline" / "manifest.json").read_text(encoding="utf-8")
    )
    original_hashes = hashes(root)

    assert acousticbrain_main.main(
        ["--measurements-root", str(root), "--analysis-readiness"]
    ) == 0
    readiness_output = capsys.readouterr().out
    assert "\nFREQUENCY\n" in readiness_output
    assert "Status: AVAILABLE" in readiness_output

    assert acousticbrain_main.main(
        ["--measurements-root", str(root), "--observations"]
    ) == 0
    first_observations = capsys.readouterr().out
    assert "FREQUENCY_RESPONSE_FEATURE_FACTS" in first_observations
    assert "LEFT_RIGHT_FREQUENCY_FEATURE_COMPARISON_FACTS" in first_observations
    assert "STEREO_FREQUENCY_FEATURE_RELATION_FACTS" in first_observations

    assert acousticbrain_main.main(
        ["--measurements-root", str(root), "--observations"]
    ) == 0
    second_observations = capsys.readouterr().out
    assert second_observations == first_observations

    assert acousticbrain_main.main(
        ["--measurements-root", str(root), "--full-assessment"]
    ) == 0
    full_output = capsys.readouterr().out
    assert "FREQUENCY_RESPONSE_FEATURE_FACTS" in full_output
    assert full_output.index("DETERMINISTIC ACOUSTIC OBSERVATIONS") < (
        full_output.index("DETERMINISTIC ACOUSTIC REASONING")
    )

    assert original_manifest == json.loads(
        (root / "baseline" / "manifest.json").read_text(encoding="utf-8")
    )
    assert original_hashes == hashes(root)
