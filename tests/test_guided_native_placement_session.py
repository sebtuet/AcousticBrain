import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import (
    AcousticSession,
    AutomaticExperimentComparisonService,
    ExperimentDiscoveryService,
    GuidedNativePlacementSessionConfig,
    GuidedNativePlacementSessionService,
    GuidedNativePlacementSessionStatus,
    GuidedNativePlacementVerdict,
    GuidedNativePlacementVerdictProjector,
    OptimizationSessionService,
    PlacementComparisonSelectionQualificationService,
)
from acousticbrain.application.channel_isolation_repeatability_evaluation import (
    RepeatabilityEvaluationStatus,
)
from acousticbrain.application.channel_isolation_repeatability_qualification import (
    ChannelIsolationRepeatabilityMetric,
    ChannelIsolationRepeatabilityQualification,
    ChannelIsolationRepeatabilityQualificationProvenance,
    ChannelIsolationRepeatabilityQualificationStatus,
)
from acousticbrain.application.placement_comparison_qualification import (
    PlacementComparisonStatus,
)
from acousticbrain.models import (
    ComparableExperimentFact,
    ComparisonEligibilityStatus,
    ComparisonIneligibilityReason,
    ExperimentAcousticOutcome,
    ExperimentFactChange,
    ExperimentFactDelta,
)
from acousticbrain.report import GuidedNativePlacementSessionConsoleReporter


class _Summary:
    def __init__(self, root, experiment_id):
        self.experiment_id = experiment_id
        self.experiment_directory = Path(root) / experiment_id


class _CaptureService:
    def __init__(self, root):
        self.root = Path(root)
        self.configs = []

    def capture(self, config):
        self.configs.append(config)
        return _Summary(self.root, config.experiment_id)


class _Discovery:
    def discover(self, root):
        return ()


class _Evaluation:
    def __init__(self, experiment_ids):
        self.experiment_ids = tuple(experiment_ids)

    def evaluate(self, descriptors):
        return tuple(SimpleNamespace(experiment_id=value) for value in self.experiment_ids)


class _Qualification:
    def __init__(self, statuses):
        self.statuses = statuses

    def qualify(self, evaluations):
        return tuple(
            _qualification(item.experiment_id, self.statuses[item.experiment_id])
            for item in evaluations
        )


class _Declaration:
    def __init__(self):
        self.calls = []

    def declare(self, measurement_root, **kwargs):
        self.calls.append((measurement_root, kwargs))
        return SimpleNamespace()


class _Brain:
    def __init__(self, comparison):
        self.comparison = comparison
        self.calls = []

    def analyze(self, **kwargs):
        self.calls.append(kwargs)
        return (
            SimpleNamespace(),
            SimpleNamespace(
                experiment_comparison_analysis=SimpleNamespace(
                    sequence=SimpleNamespace(
                        local_comparisons=(self.comparison,),
                        cumulative_comparisons=(),
                    )
                )
            ),
        )


class _FailingBrain:
    def __init__(self):
        self.calls = []

    def analyze(self, **kwargs):
        self.calls.append(kwargs)
        raise ValueError("Aucune mesure stéréo n'a été trouvée.")


def _qualification(experiment_id, status):
    verdict = {
        ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED: (
            RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
        ),
        ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED: (
            RepeatabilityEvaluationStatus.REPEATABILITY_UNCERTAIN
        ),
        ChannelIsolationRepeatabilityQualificationStatus.INDETERMINATE: (
            RepeatabilityEvaluationStatus.NOT_EVALUABLE
        ),
    }[status]
    return ChannelIsolationRepeatabilityQualification(
        repeatability_contract_id="repeatability_contract.v1",
        repeatability_contract_version="v1",
        left_channel_metric=ChannelIsolationRepeatabilityMetric(0.2, 80.0),
        right_channel_metric=ChannelIsolationRepeatabilityMetric(0.3, 90.0),
        source_numeric_verdict=verdict,
        qualification_status=status,
        reason_codes=(verdict.value,),
        provenance=ChannelIsolationRepeatabilityQualificationProvenance(
            experiment_id=experiment_id,
            capture_labels=("A", "B"),
            repeatability_contract_id="repeatability_contract.v1",
            repeatability_contract_version="v1",
            lower_hz=40.0,
            upper_hz=200.0,
            threshold_db=3.0,
        ),
    )


def _comparison(
    outcome,
    *,
    before="ref",
    after="cand",
    eligibility=ComparisonEligibilityStatus.COMPARABLE,
    reasons=(),
):
    return SimpleNamespace(
        trace=SimpleNamespace(trace_id=f"trace:comparison:local:{before}:{after}"),
        before_experiment_id=before,
        after_experiment_id=after,
        result_id=f"comparison:local:{before}:{after}",
        eligibility=eligibility,
        ineligibility_reasons=reasons,
        acoustic_outcome=ExperimentAcousticOutcome(outcome),
        fact_deltas=(ExperimentFactDelta(
            fact_code="metric",
            before=2.0,
            after=1.0,
            delta=-1.0,
            unit="DB",
            change=ExperimentFactChange.IMPROVED,
            threshold=1.0,
            source_analysis_codes=("fixture",),
        ),),
        provenance_codes=("ref", "cand"),
    )


def _config(root):
    calibration = Path(root) / "cal.txt"
    calibration.write_text("20 0\n20000 0\n", encoding="utf-8")
    return GuidedNativePlacementSessionConfig(
        measurements_root=Path(root),
        input_device="UMIK-1",
        output_device="AirPlay",
        calibration_file=calibration,
        sample_rate_hz=8000,
        sweep_level_dbfs=-18.0,
        reference_experiment_id="ref",
        candidate_experiment_id="cand",
    )


def _answers(*values):
    iterator = iter(values)
    return lambda prompt="": next(iterator)


@pytest.mark.parametrize(
    ("placement_status", "expected"),
    (
        (PlacementComparisonStatus.BETTER, GuidedNativePlacementVerdict.KEEP),
        (PlacementComparisonStatus.WORSE, GuidedNativePlacementVerdict.REVERT),
        (PlacementComparisonStatus.EQUIVALENT, GuidedNativePlacementVerdict.INDETERMINATE),
        (PlacementComparisonStatus.INDETERMINATE, GuidedNativePlacementVerdict.INDETERMINATE),
        (None, GuidedNativePlacementVerdict.INDETERMINATE),
    ),
)
def test_guided_native_verdict_projection_has_no_numeric_rule(
    placement_status, expected,
):
    assert GuidedNativePlacementVerdictProjector().project(placement_status) is expected


@pytest.mark.parametrize(
    ("outcome", "expected_status", "expected_verdict"),
    (
        ("IMPROVED", GuidedNativePlacementSessionStatus.KEEP, "KEEP"),
        ("DEGRADED", GuidedNativePlacementSessionStatus.REVERT, "REVERT"),
        ("UNCHANGED", GuidedNativePlacementSessionStatus.INDETERMINATE, "INDETERMINATE"),
        ("MIXED", GuidedNativePlacementSessionStatus.INDETERMINATE, "INDETERMINATE"),
        ("INCONCLUSIVE", GuidedNativePlacementSessionStatus.INDETERMINATE, "INDETERMINATE"),
    ),
)
def test_guided_native_session_projects_existing_placement_outcomes(
    tmp_path, outcome, expected_status, expected_verdict,
):
    root = tmp_path / "measurements"
    root.mkdir()
    declaration = _Declaration()
    brain = _Brain(_comparison(outcome))
    service = GuidedNativePlacementSessionService(
        capture_service=_CaptureService(root),
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(("ref", "cand")),
        repeatability_qualification_service=_Qualification({
            "ref": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
            "cand": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
        }),
        experiment_declaration_service=declaration,
        brain=brain,
        input_func=_answers("left speaker +10 cm forward", ""),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is expected_status
    assert result.verdict.value == expected_verdict
    assert result.comparison_id == "trace:comparison:local:ref:cand"
    assert brain.calls[0]["channel_isolation_repeatability_qualifications"] == (
        result.reference_repeatability_qualification,
        result.candidate_repeatability_qualification,
    )
    assert declaration.calls[0][1]["reference_experiment_code"] == "ref"
    assert declaration.calls[0][1]["modified_variables"] == ("LOUDSPEAKER_POSITION",)
    assert declaration.calls[0][1]["user_note"] == "left speaker +10 cm forward"


def _presented_result(*, status, verdict, placement_status=None, comparison_id="trace"):
    return SimpleNamespace(
        status=status,
        verdict=verdict,
        reference_experiment_id="ref",
        candidate_experiment_id="cand",
        comparison_id=comparison_id,
        placement_status=placement_status,
        displacement_description="left speaker +10 cm forward",
        causality_status="NOT_ESTABLISHED",
    )


@pytest.mark.parametrize(
    ("status", "verdict", "placement_status", "expected"),
    (
        (
            GuidedNativePlacementSessionStatus.KEEP,
            GuidedNativePlacementVerdict.KEEP,
            PlacementComparisonStatus.BETTER,
            "Verdict : KEEP",
        ),
        (
            GuidedNativePlacementSessionStatus.REVERT,
            GuidedNativePlacementVerdict.REVERT,
            PlacementComparisonStatus.WORSE,
            "Verdict : REVERT",
        ),
    ),
)
def test_guided_native_presenter_preserves_keep_revert_verdicts(
    capsys, status, verdict, placement_status, expected
):
    GuidedNativePlacementSessionConsoleReporter().print(
        _presented_result(
            status=status,
            verdict=verdict,
            placement_status=placement_status,
        )
    )

    output = capsys.readouterr().out
    assert expected in output
    assert f"Qualification placement : {placement_status.value}" in output


def test_guided_native_presenter_reports_equivalent_without_uncertainty_wording(
    capsys,
):
    GuidedNativePlacementSessionConsoleReporter().print(
        _presented_result(
            status=GuidedNativePlacementSessionStatus.INDETERMINATE,
            verdict=GuidedNativePlacementVerdict.INDETERMINATE,
            placement_status=PlacementComparisonStatus.EQUIVALENT,
        )
    )

    output = capsys.readouterr().out
    assert "Verdict : EQUIVALENT" in output
    assert "Qualification placement : EQUIVALENT" not in output
    assert "Les mesures disponibles ne permettent pas de conclure" not in output
    assert "aucun KEEP/REVERT" not in output
    assert "pour recommander KEEP ou REVERT" in output
    assert "État : comparaison qualifiée EQUIVALENT" in output


def test_guided_native_presenter_keeps_indeterminate_uncertainty_wording(
    capsys,
):
    GuidedNativePlacementSessionConsoleReporter().print(
        _presented_result(
            status=GuidedNativePlacementSessionStatus.INDETERMINATE,
            verdict=GuidedNativePlacementVerdict.INDETERMINATE,
            placement_status=PlacementComparisonStatus.INDETERMINATE,
        )
    )

    output = capsys.readouterr().out
    assert "Verdict : INDETERMINATE" in output
    assert "Les mesures disponibles ne permettent pas de conclure" in output
    assert "État : verdict métier INDETERMINATE" in output


def test_guided_native_presenter_keeps_blocked_comparison_wording(capsys):
    GuidedNativePlacementSessionConsoleReporter().print(
        _presented_result(
            status=GuidedNativePlacementSessionStatus.COMPARISON_NOT_COMPARABLE,
            verdict=GuidedNativePlacementVerdict.INDETERMINATE,
            placement_status=None,
            comparison_id=None,
        )
    )

    output = capsys.readouterr().out
    assert "Verdict : INDETERMINATE" in output
    assert "La comparaison existante n'est pas comparable" in output
    assert "État : comparaison non exécutée" in output


def test_reference_capture_invalid_stops_before_candidate(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    capture = _CaptureService(root)
    service = GuidedNativePlacementSessionService(
        capture_service=capture,
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(()),
        repeatability_qualification_service=_Qualification({}),
        brain=_Brain(_comparison("IMPROVED")),
        input_func=_answers(),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is GuidedNativePlacementSessionStatus.REFERENCE_CAPTURE_INVALID
    assert result.verdict is GuidedNativePlacementVerdict.INDETERMINATE
    assert [item.experiment_id for item in capture.configs] == ["ref"]
    assert result.comparison_id is None


def test_reference_not_qualified_stops_before_candidate_and_comparison(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    capture = _CaptureService(root)
    brain = _Brain(_comparison("IMPROVED"))
    service = GuidedNativePlacementSessionService(
        capture_service=capture,
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(("ref",)),
        repeatability_qualification_service=_Qualification({
            "ref": ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED,
        }),
        brain=brain,
        input_func=_answers(),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is GuidedNativePlacementSessionStatus.REFERENCE_NOT_QUALIFIED
    assert [item.experiment_id for item in capture.configs] == ["ref"]
    assert brain.calls == []


def test_candidate_capture_invalid_keeps_diagnostics_without_comparison(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    capture = _CaptureService(root)
    brain = _Brain(_comparison("IMPROVED"))
    service = GuidedNativePlacementSessionService(
        capture_service=capture,
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(("ref",)),
        repeatability_qualification_service=_Qualification({
            "ref": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
        }),
        brain=brain,
        input_func=_answers("left speaker +10 cm forward", ""),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is GuidedNativePlacementSessionStatus.CANDIDATE_CAPTURE_INVALID
    assert [item.experiment_id for item in capture.configs] == ["ref", "cand"]
    assert brain.calls == []


def test_candidate_not_qualified_does_not_emit_directional_decision(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = _Brain(_comparison("IMPROVED"))
    service = GuidedNativePlacementSessionService(
        capture_service=_CaptureService(root),
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(("ref", "cand")),
        repeatability_qualification_service=_Qualification({
            "ref": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
            "cand": ChannelIsolationRepeatabilityQualificationStatus.NOT_QUALIFIED,
        }),
        experiment_declaration_service=_Declaration(),
        brain=brain,
        input_func=_answers("left speaker +10 cm forward", ""),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is GuidedNativePlacementSessionStatus.CANDIDATE_NOT_QUALIFIED
    assert result.verdict is GuidedNativePlacementVerdict.INDETERMINATE
    assert brain.calls == []


def test_non_comparable_comparison_does_not_emit_keep_or_revert(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    service = GuidedNativePlacementSessionService(
        capture_service=_CaptureService(root),
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(("ref", "cand")),
        repeatability_qualification_service=_Qualification({
            "ref": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
            "cand": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
        }),
        experiment_declaration_service=_Declaration(),
        brain=_Brain(_comparison(
            "INCONCLUSIVE",
            eligibility=ComparisonEligibilityStatus.NOT_COMPARABLE,
            reasons=(ComparisonIneligibilityReason.NO_USABLE_MEASUREMENT,),
        )),
        input_func=_answers("left speaker +10 cm forward", ""),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is GuidedNativePlacementSessionStatus.COMPARISON_NOT_COMPARABLE
    assert result.verdict is GuidedNativePlacementVerdict.INDETERMINATE
    assert result.blocking_reason_codes == ("NO_USABLE_MEASUREMENT",)


def test_missing_measured_stereo_stops_without_directional_decision(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()
    brain = _FailingBrain()
    service = GuidedNativePlacementSessionService(
        capture_service=_CaptureService(root),
        discovery_service=_Discovery(),
        repeatability_evaluation_service=_Evaluation(("ref", "cand")),
        repeatability_qualification_service=_Qualification({
            "ref": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
            "cand": ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED,
        }),
        experiment_declaration_service=_Declaration(),
        brain=brain,
        input_func=_answers("left speaker +10 cm forward", ""),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.status is GuidedNativePlacementSessionStatus.COMPARISON_NOT_COMPARABLE
    assert result.verdict is GuidedNativePlacementVerdict.INDETERMINATE
    assert result.blocking_reason_codes == ("MEASURED_STEREO_UNAVAILABLE",)
    assert len(brain.calls) == 1


def _write_native_experiment(root, experiment_id, values):
    experiment = Path(root) / experiment_id
    measurements = experiment / "measurements"
    measurements.mkdir(parents=True)
    assignments = {}
    for channel, repeat, spl in (
        ("LEFT", "A", values["left"]),
        ("LEFT", "B", values["left"]),
        ("RIGHT", "A", values["right"]),
        ("RIGHT", "B", values["right"]),
    ):
        relative = f"measurements/{channel} {experiment_id} {repeat}.txt"
        assignments[relative] = channel
        (experiment / relative).write_text(
            "\n".join((
                f"* Measurement: {channel} {experiment_id} {repeat}",
                "* Freq(Hz) SPL(dB) Phase(degrees)",
                f"40 {spl} 0",
                f"100 {spl} 0",
                f"200 {spl} 0",
                "",
            )),
            encoding="utf-8",
        )
    stereo_relative = f"measurements/L+R {experiment_id}.txt"
    assignments[stereo_relative] = "STEREO"
    (experiment / stereo_relative).write_text(
        "\n".join((
            f"* Measurement: L+R {experiment_id}",
            "* Freq(Hz) SPL(dB) Phase(degrees)",
            f"40 {values['stereo']} 12",
            f"100 {values['stereo']} 13",
            f"200 {values['stereo']} 14",
            "",
        )),
        encoding="utf-8",
    )
    manifest = {
        "source_evidence_acquisition_plan_id": (
            "native-placement-capture.channel-isolation.v1"
        ),
        "channel_assignments": assignments,
        "native_acquisition": {
            "schema_version": 1,
            "identity": "acousticbrain.native_placement_capture.v1",
            "experimental": True,
        },
        "evidence_acquisition_plan_contract": {
            "schema_version": 1,
            "mode": "EXPLORATORY",
            "declaration_source": "native-placement-capture",
            "reference_experiment_code": "baseline",
            "plan": {
                "plan_id": "native-placement-capture.channel-isolation.v1",
                "reasoning_id": "native-placement-capture",
                "corrective_action_id": "native-placement-capture",
                "evidence_weight_id": "native-placement-capture",
                "blocking_factor_ids": ["NATIVE_CAPTURE_EXPERIMENTAL"],
                "objective": "Capture LEFT/RIGHT A/B repeatability and measured L+R natively.",
                "test_type": "CHANNEL_ISOLATION",
                "instructions": ["Capture LEFT A, LEFT B, RIGHT A, RIGHT B, L+R."],
                "required_inputs": ["UMIK_CALIBRATION", "STEREO_OUTPUT"],
                "controlled_variables": ["MICROPHONE_POSITION", "LOUDSPEAKER_POSITION"],
                "independent_variables": ["REPEAT_LABEL"],
                "measurements_to_capture": [
                    "LEFT_A",
                    "LEFT_B",
                    "RIGHT_A",
                    "RIGHT_B",
                    "L+R",
                ],
                "expected_observations": ["A_B_REPEATABILITY"],
                "success_criteria": ["TXT_MEASUREMENTS_DISCOVERABLE"],
                "failure_criteria": ["CAPTURE_NOT_COMPLETED"],
                "resulting_evidence_targets": ["CHANNEL_ISOLATION_REPEATABILITY"],
                "priority": "MEDIUM",
                "estimated_effort": "LOW",
                "status": "READY",
                "limitations": ["Experimental native acquisition."],
                "channel_isolation_evaluation_criteria": [],
            },
        },
        "channel_isolation_declaration": {
            "repeated_channels": ["LEFT", "RIGHT"],
            "available_inputs": ["UMIK_CALIBRATION", "STEREO_OUTPUT"],
            "controlled_variables": ["MICROPHONE_POSITION", "LOUDSPEAKER_POSITION"],
            "independent_variables": ["REPEAT_LABEL"],
            "measurements": ["LEFT_A", "LEFT_B", "RIGHT_A", "RIGHT_B"],
        },
    }
    (experiment / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


class _FileCaptureService:
    def __init__(self, root):
        self.root = Path(root)
        self.configs = []

    def capture(self, config):
        self.configs.append(config)
        values = (
            {"left": 70.0, "right": 70.0, "stereo": 72.0}
            if config.experiment_id == "ref"
            else {"left": 68.0, "right": 68.0, "stereo": 69.0}
        )
        _write_native_experiment(self.root, config.experiment_id, values)
        return _Summary(self.root, config.experiment_id)


class _FactProjector:
    def project(self, context):
        return context.facts


class _RealComparisonBrain:
    def analyze(self, **kwargs):
        session = AcousticSession.auto_open(kwargs["measurement_root"])
        facts = {
            "ref": 10.0,
            "cand": 8.0,
        }
        contexts = {
            experiment.descriptor.experiment_id: SimpleNamespace(
                state=None,
                facts=(ComparableExperimentFact(
                    code="placement.metric",
                    value=facts[experiment.descriptor.experiment_id],
                    unit="DB",
                    family="PLACEMENT",
                    semantic="placement.metric",
                    source_analysis="fixture",
                    threshold=1.0,
                    higher_is_better=False,
                ),),
                confidence_analysis=SimpleNamespace(score=90.0),
            )
            for experiment in session.experiments
        }
        analysis = AutomaticExperimentComparisonService(_FactProjector()).analyze(
            session,
            contexts,
            channel_isolation_repeatability_qualifications=(
                kwargs["channel_isolation_repeatability_qualifications"]
            ),
        )
        return SimpleNamespace(), SimpleNamespace(
            experiment_comparison_analysis=analysis
        )


def test_session_uses_real_discovery_repeatability_and_explicit_parent_relation(
    tmp_path, monkeypatch,
):
    root = tmp_path / "measurements"
    root.mkdir()
    monkeypatch.setattr(
        OptimizationSessionService,
        "snapshot_analysis",
        staticmethod(lambda context, *, state_id: context.state),
    )
    service = GuidedNativePlacementSessionService(
        capture_service=_FileCaptureService(root),
        discovery_service=ExperimentDiscoveryService(),
        brain=_RealComparisonBrain(),
        selection_qualification_service=PlacementComparisonSelectionQualificationService(),
        clock=lambda: datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
        input_func=_answers("left speaker +10 cm forward", ""),
        output_func=lambda value: None,
    )

    result = service.run(_config(root))

    assert result.verdict is GuidedNativePlacementVerdict.KEEP
    assert result.placement_status is PlacementComparisonStatus.BETTER
    assert result.comparison_id == "trace:comparison:local:ref:cand"
    manifest = json.loads((root / "cand/manifest.json").read_text(encoding="utf-8"))
    assert manifest["comparison"]["parent_experiment_ids"] == ["ref"]
    assert manifest["experiment_declaration"]["modified_variables"] == [
        "LOUDSPEAKER_POSITION"
    ]
    assert manifest["experiment_declaration"]["user_note"] == (
        "left speaker +10 cm forward"
    )


class _SessionService:
    def __init__(self):
        self.configs = []

    def run(self, config):
        self.configs.append(config)
        return SimpleNamespace(
            status=GuidedNativePlacementSessionStatus.KEEP,
            verdict=GuidedNativePlacementVerdict.KEEP,
            reference_experiment_id="ref",
            candidate_experiment_id="cand",
            comparison_id="trace:comparison:local:ref:cand",
            placement_status=PlacementComparisonStatus.BETTER,
            displacement_description="left speaker +10 cm forward",
            causality_status="NOT_ESTABLISHED",
        )


def test_main_cli_runs_guided_native_session_with_existing_native_options(
    tmp_path, capsys,
):
    root = tmp_path / "measurements"
    root.mkdir()
    calibration = tmp_path / "7171499_90deg.txt"
    calibration.write_text("20 0\n20000 0\n", encoding="utf-8")
    service = _SessionService()

    result = acousticbrain_main.main(
        [
            "--measurements-root", str(root),
            "--native-placement-session",
            "--input-device", "UMIK-1",
            "--output-device", "AirPlay",
            "--calibration-file", str(calibration),
            "--native-sweep-level-dbfs", "-18",
        ],
        guided_native_placement_session_service=service,
        placement_input=_answers("left speaker +10 cm forward", ""),
    )

    assert result == 0
    assert service.configs[0].measurements_root == root
    assert service.configs[0].input_device == "UMIK-1"
    assert service.configs[0].output_device == "AirPlay"
    assert service.configs[0].calibration_file == calibration
    assert service.configs[0].sweep_level_dbfs == -18.0
    output = capsys.readouterr().out
    assert "Verdict : KEEP" in output
    assert "Référence : ref" in output
    assert "Candidate : cand" in output


def test_main_cli_rejects_guided_native_session_without_hardware_inputs(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            ["--measurements-root", str(root), "--native-placement-session"]
        )

    assert error.value.code == 2


def test_main_cli_rejects_guided_session_and_single_capture_together(tmp_path):
    root = tmp_path / "measurements"
    root.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root", str(root),
                "--native-placement-session",
                "--native-placement-capture",
            ]
        )

    assert error.value.code == 2
