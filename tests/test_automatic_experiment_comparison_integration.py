import json
import shutil
from dataclasses import replace

from acousticbrain.application import AcousticSession
from acousticbrain.brain import AcousticBrain
from acousticbrain.application import ExperimentDiscoveryService
from acousticbrain.application.channel_isolation_repeatability_evaluation import (
    ChannelIsolationRepeatabilityEvaluationService,
)
from acousticbrain.application.channel_isolation_repeatability_qualification import (
    ChannelIsolationRepeatabilityQualificationService,
    ChannelIsolationRepeatabilityQualificationStatus,
)
from acousticbrain.report import AssessmentSummaryPresenter
import pytest

from historical_campaign import HISTORICAL_CAMPAIGN_ROOT


@pytest.fixture
def versioned_measurement_root(tmp_path):
    measurement_root = tmp_path / "measurements"
    for experiment_id in ("baseline", "exp-001", "exp-002"):
        shutil.copytree(
            HISTORICAL_CAMPAIGN_ROOT / experiment_id,
            measurement_root / experiment_id,
        )
    return measurement_root


def test_explicit_mode_analyzes_versioned_experiments_without_local_data(
    versioned_measurement_root,
):
    report = AcousticBrain().analyze(
        measurement_root=versioned_measurement_root,
        compare_experiments=True,
        detailed_comparison_traceability=True,
    )

    assert report.experiment_comparison.chronology == (
        "baseline", "exp-001", "exp-002"
    )
    assert len(report.experiment_comparison.local_comparisons) == 2
    assert len(report.experiment_comparison.cumulative_comparisons) == 2
    assert report.experiment_campaigns == ()
    assert report.experiment_comparison.local_comparisons[0].trace_id
    assert report.optimization_session is None


@pytest.fixture
def native_measurement_root(tmp_path):
    source = HISTORICAL_CAMPAIGN_ROOT.parents[3] / "measurements"
    root = tmp_path / "measurements"
    for experiment_id in (
        "exp-native-reference-20260902-173717",
        "exp-native-candidate-20260902-173717",
    ):
        shutil.copytree(source / experiment_id, root / experiment_id)
    return root


def test_qualified_native_repetitions_produce_canonical_imports(
    native_measurement_root,
):
    descriptors = ExperimentDiscoveryService().discover(native_measurement_root)
    qualifications = ChannelIsolationRepeatabilityQualificationService().qualify(
        ChannelIsolationRepeatabilityEvaluationService().evaluate(descriptors)
    )

    with pytest.raises(ValueError, match="measured L\\+R"):
        AcousticSession.auto_open(
            native_measurement_root,
            channel_isolation_repeatability_qualifications=qualifications,
        )


def _add_measured_stereo(experiment_directory, experiment_id, spl):
    relative = f"measurements/L+R {experiment_id}.txt"
    path = experiment_directory / relative
    path.write_text(
        "\n".join((
            f"* Measurement: L+R {experiment_id}",
            "* Freq(Hz) SPL(dB) Phase(degrees)",
            f"40 {spl} 12",
            f"100 {spl} 13",
            f"200 {spl} 14",
            "",
        )),
        encoding="utf-8",
    )
    manifest_path = experiment_directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["channel_assignments"][relative] = "STEREO"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


@pytest.fixture
def complete_native_measurement_root(native_measurement_root):
    for experiment_id, spl in (
        ("exp-native-reference-20260902-173717", 72.0),
        ("exp-native-candidate-20260902-173717", 69.0),
    ):
        _add_measured_stereo(native_measurement_root / experiment_id, experiment_id, spl)
    return native_measurement_root


def test_qualified_native_repetitions_with_measured_stereo_produce_canonical_imports(
    complete_native_measurement_root,
):
    descriptors = ExperimentDiscoveryService().discover(complete_native_measurement_root)
    qualifications = ChannelIsolationRepeatabilityQualificationService().qualify(
        ChannelIsolationRepeatabilityEvaluationService().evaluate(descriptors)
    )

    session = AcousticSession.auto_open(
        complete_native_measurement_root,
        channel_isolation_repeatability_qualifications=qualifications,
    )

    assert all(item.project is not None for item in session.experiments)
    for item in session.experiments:
        representation = item.canonical_representation
        assert representation is not None
        assert representation.method == "SELECT_REPRESENTATIVE_REPEAT_A"
        assert representation.representative_selection_derived is True
        assert representation.stereo_derived is False
        assert len(representation.selected_files) == 2
        assert len(representation.source_files) == 4
        assert representation.measured_stereo_file.startswith("measurements/L+R ")
        assert item.project.has_measurement("L+R")


def test_unqualified_native_repetitions_are_not_imported(
    native_measurement_root,
):
    descriptors = ExperimentDiscoveryService().discover(native_measurement_root)
    qualifications = tuple(
        replace(
            item,
            qualification_status=(
                ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED
            ),
        )
        for item in ChannelIsolationRepeatabilityQualificationService().qualify(
            ChannelIsolationRepeatabilityEvaluationService().evaluate(descriptors)
        )
        if item.provenance.experiment_id.endswith("candidate-20260902-173717")
    )

    session = AcousticSession.auto_open(
        native_measurement_root,
        channel_isolation_repeatability_qualifications=qualifications,
    )

    reference = next(
        item for item in session.experiments
        if "reference" in item.descriptor.experiment_id
    )
    candidate = next(
        item for item in session.experiments
        if "candidate" in item.descriptor.experiment_id
    )
    assert reference.project is None
    assert candidate.project is None


def test_qualified_native_repetitions_without_measured_stereo_do_not_reach_context(
    native_measurement_root,
):
    descriptors = ExperimentDiscoveryService().discover(native_measurement_root)
    qualifications = ChannelIsolationRepeatabilityQualificationService().qualify(
        ChannelIsolationRepeatabilityEvaluationService().evaluate(descriptors)
    )

    with pytest.raises(ValueError, match="measured L\\+R"):
        AcousticBrain().analyze(
            measurement_root=native_measurement_root,
            compare_experiments=True,
            channel_isolation_repeatability_qualifications=qualifications,
            return_context=True,
        )


def test_qualified_native_repetitions_with_measured_stereo_reach_comparable_comparison(
    complete_native_measurement_root,
):
    descriptors = ExperimentDiscoveryService().discover(complete_native_measurement_root)
    qualifications = ChannelIsolationRepeatabilityQualificationService().qualify(
        ChannelIsolationRepeatabilityEvaluationService().evaluate(descriptors)
    )

    _, context = AcousticBrain().analyze(
        measurement_root=complete_native_measurement_root,
        compare_experiments=True,
        channel_isolation_repeatability_qualifications=qualifications,
        return_context=True,
    )

    comparison = next(
        item
        for item in context.experiment_comparison_analysis.sequence.local_comparisons
        if item.after_experiment_id.endswith("candidate-20260902-173717")
    )
    assert comparison.eligibility.value == "COMPARABLE"
    assert comparison.ineligibility_reasons == ()
    assert comparison.fact_deltas


def test_comparison_is_absent_when_explicit_mode_is_disabled(
    versioned_measurement_root,
):
    report = AcousticBrain().analyze(
        measurement_root=versioned_measurement_root
    )

    assert report.experiment_comparison is None
    assert report.optimization_session is None


def test_multi_experiment_assessment_summary_matches_final_report(
    historical_campaign_root,
):
    report = AcousticBrain().analyze(
        measurement_root=historical_campaign_root,
        compare_experiments=True,
        synthesize_evidence_acquisition=True,
    )

    assert report.assessment_summary == AssessmentSummaryPresenter().present(report)
    assert tuple(
        item.plan_id for item in report.assessment_summary.recommended_experiments
    ) == tuple(
        item.plan_id for item in report.evidence_acquisition_plans.plans
    )
    assert report.assessment_summary.recommended_experiments


def test_single_experiment_assessment_summary_remains_synchronized(
    historical_campaign_root,
):
    project = AcousticSession.auto_open(
        historical_campaign_root
    ).current_project

    report = AcousticBrain().analyze(
        project,
        synthesize_evidence_acquisition=True,
    )

    assert report.assessment_summary == AssessmentSummaryPresenter().present(report)


def test_causal_mode_projects_only_explicit_repository_steps(
    versioned_measurement_root,
):
    report = AcousticBrain().analyze(
        measurement_root=versioned_measurement_root,
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
    multi_position = next(
        item for item in report.recommendations
        if item.code == "MEASURE_MULTIPLE_POSITIONS"
    )
    assert multi_position.status.name == "ACTIVE"
    modal_domain = next(
        item for item in report.global_analysis.domains
        if item.code == "MODAL_DENSITY"
    )
    assert modal_domain.recommendation_statuses == (
        ("MEASURE_MULTIPLE_POSITIONS", "ACTIVE"),
    )
    planned_modal = next(
        item
        for item in report.experiment_planning.all_candidates
        if item.hypothesis_code == "MODAL_BASS_PERSISTENCE"
    )
    assert planned_modal.eligible is False
    assert "ACQUISITION_PROTOCOL_INCOMPLETE" in (
        planned_modal.ineligibility_reasons
    )
    assert report.experiment_planning.recommended_candidate is None
    assert "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS" in (
        report.experiment_planning.uncovered_active_action_codes
    )
    assert report.optimization_session is None


def test_causal_mode_requires_explicit_experiment_comparison(
    historical_campaign_root,
):
    with pytest.raises(ValueError, match="compare_experiments=True"):
        AcousticBrain().analyze(
            measurement_root=historical_campaign_root,
            analyze_causal_discrimination=True,
        )


def test_explicit_manifest_steps_are_projected_in_final_report(tmp_path):
    measurement_root = tmp_path / "measurements"
    for experiment_id in ("baseline", "exp-001"):
        shutil.copytree(
            HISTORICAL_CAMPAIGN_ROOT / experiment_id,
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
