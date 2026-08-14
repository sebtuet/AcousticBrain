from pathlib import Path
from types import SimpleNamespace

from acousticbrain.models import (
    ExperimentDeclaration,
    ExperimentDescriptor,
    ExperimentFileDescriptor,
    ExperimentFileType,
    ExperimentState,
    ExperimentType,
    ImpulseChannel,
)
from acousticbrain.report import ConsoleReporter, ExperimentDiscoveryPresenter, Report


ROOT = Path(__file__).resolve().parents[1]


def descriptor(
    experiment_id,
    experiment_type,
    state,
    timestamp,
    *,
    source_plan_id=None,
    source_protocol_id=None,
    available_channels=(ImpulseChannel.STEREO,),
    experiment_declaration=None,
    channel_isolation_declaration=None,
    channel_isolation_result_declaration=None,
):
    return ExperimentDescriptor(
        experiment_id=experiment_id,
        directory=f"/measurements/{experiment_id}",
        experiment_type=experiment_type,
        available_files=(
            ExperimentFileDescriptor(
                relative_path="measurements/arbitrary.txt",
                file_type=ExperimentFileType.TXT_MEASUREMENT,
                sha256="a" * 64,
                channel=ImpulseChannel.STEREO,
            ),
        ),
        available_channels=available_channels,
        wav_files=(),
        txt_files=("measurements/arbitrary.txt",),
        mdat_file=None,
        manifest_present=True,
        content_hash="b" * 64,
        timestamp=timestamp,
        imported_at="2026-07-13T12:00:00+00:00",
        state=state,
        source_evidence_acquisition_plan_id=source_plan_id,
        source_protocol_id=source_protocol_id,
        experiment_declaration=(
            experiment_declaration or ExperimentDeclaration.unknown()
        ),
        channel_isolation_declaration=channel_isolation_declaration,
        channel_isolation_result_declaration=(
            channel_isolation_result_declaration
        ),
    )


def test_discovery_presenter_and_console_match_golden(capsys):
    context = SimpleNamespace(
        experiment_descriptors=(
            descriptor(
                "baseline",
                ExperimentType.BASELINE,
                ExperimentState.READY,
                "2026-07-07T15:57:39",
            ),
            descriptor(
                "exp-001",
                ExperimentType.EXPERIMENT,
                ExperimentState.INCOMPLETE,
                "2026-07-13T10:53:20",
            ),
        )
    )
    report = Report(project_name="measurements")
    report.experiments_discovered = ExperimentDiscoveryPresenter().present(context)

    ConsoleReporter().print(report)

    expected = (
        ROOT / "tests/golden/experiment_discovery_report.txt"
    ).read_text() + "\n\n"
    assert capsys.readouterr().out == expected


def test_presenter_is_absent_without_discovery():
    context = SimpleNamespace(experiment_descriptors=())

    assert ExperimentDiscoveryPresenter().present(context) is None


def test_presenter_distinguishes_absent_resolved_and_unknown_plan_references():
    resolved_id = "EVIDENCE_ACQUISITION_PLAN_RESOLVED"
    context = SimpleNamespace(
        experiment_descriptors=(
            descriptor(
                "exp-001",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-13T10:53:20",
            ),
            descriptor(
                "exp-002",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-14T10:53:20",
                source_plan_id=resolved_id,
            ),
            descriptor(
                "exp-003",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-15T10:53:20",
                source_plan_id="EVIDENCE_ACQUISITION_PLAN_UNKNOWN",
            ),
        ),
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(SimpleNamespace(plan_id=resolved_id),)
        ),
    )

    presented = ExperimentDiscoveryPresenter().present(context)

    assert tuple(item.experiment_id for item in presented.experiments) == (
        "exp-001",
        "exp-002",
        "exp-003",
    )
    assert tuple(
        item.evidence_acquisition_plan_reference_status
        for item in presented.experiments
    ) == (
        "PLAN_NOT_REFERENCED",
        "PLAN_REFERENCE_RESOLVED",
        "PLAN_REFERENCE_UNKNOWN",
    )
    assert presented.experiments[1].source_evidence_acquisition_plan_id == (
        resolved_id
    )
    assert presented.experiments[2].source_evidence_acquisition_plan_id == (
        "EVIDENCE_ACQUISITION_PLAN_UNKNOWN"
    )


def test_presented_json_preserves_exact_plan_reference():
    source_plan_id = " EVIDENCE_ACQUISITION_PLAN_EXACT "
    context = SimpleNamespace(
        experiment_descriptors=(
            descriptor(
                "exp-001",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-13T10:53:20",
                source_plan_id=source_plan_id,
            ),
        ),
        evidence_acquisition_plan_synthesis=SimpleNamespace(plans=()),
    )

    payload = ExperimentDiscoveryPresenter().present(context).to_dict()

    assert payload["experiments"][0][
        "source_evidence_acquisition_plan_id"
    ] == source_plan_id
    assert payload["experiments"][0][
        "evidence_acquisition_plan_reference_status"
    ] == "PLAN_REFERENCE_UNKNOWN"


def test_presenter_never_infers_plan_reference_from_similar_metadata():
    plan_id = "protocol.same-text"
    context = SimpleNamespace(
        experiment_descriptors=(
            descriptor(
                "exp-001",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-13T10:53:20",
                source_protocol_id=plan_id,
            ),
        ),
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(SimpleNamespace(plan_id=plan_id),)
        ),
    )

    presented = ExperimentDiscoveryPresenter().present(context).experiments[0]

    assert presented.source_evidence_acquisition_plan_id is None
    assert (
        presented.evidence_acquisition_plan_reference_status
        == "PLAN_NOT_REFERENCED"
    )


def test_presenter_exposes_channel_isolation_coverage_and_console_details(capsys):
    from test_channel_isolation_plan_coverage import (
        complete_channel_declaration,
        experimental_declaration,
        plan,
    )

    source_plan = plan()
    context = SimpleNamespace(
        experiment_descriptors=(
            descriptor(
                "exp-001",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-13T10:53:20",
                source_plan_id=source_plan.plan_id,
                available_channels=(
                    ImpulseChannel.LEFT,
                    ImpulseChannel.RIGHT,
                ),
                experiment_declaration=experimental_declaration(),
                channel_isolation_declaration=complete_channel_declaration(),
            ),
        ),
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(source_plan,)
        ),
    )
    report = Report(project_name="measurements")
    report.experiments_discovered = ExperimentDiscoveryPresenter().present(context)

    ConsoleReporter().print(report)

    presented = report.experiments_discovered.experiments[0]
    assert presented.evidence_acquisition_plan_reference_status == (
        "PLAN_REFERENCE_RESOLVED"
    )
    assert presented.evidence_acquisition_plan_coverage_status == (
        "PLAN_COVERAGE_COMPLETE"
    )
    assert presented.missing_plan_requirements == ()
    output = capsys.readouterr().out
    assert "Plan coverage status : PLAN_COVERAGE_COMPLETE" in output
    assert "Missing plan requirements :\n- none" in output
    assert "Unverifiable plan requirements :" in output


def test_presenter_keeps_partial_coverage_independent_from_compatible_result(
    capsys,
):
    from test_channel_isolation_plan_coverage import (
        complete_channel_declaration,
    )
    from test_channel_isolation_plan_result import (
        criterion,
        plan,
        result,
    )
    from acousticbrain.models import ChannelIsolationResultDeclaration

    source_plan = plan(criterion(
        "DECLARED_METRIC_EXPECTED",
        "declared_metric",
        expected_value="1.5",
    ))
    context = SimpleNamespace(
        experiment_descriptors=(
            descriptor(
                "exp-001",
                ExperimentType.EXPERIMENT,
                ExperimentState.READY,
                "2026-07-13T10:53:20",
                source_plan_id=source_plan.plan_id,
                available_channels=(ImpulseChannel.LEFT,),
                channel_isolation_declaration=complete_channel_declaration(
                    repeated_channels=(ImpulseChannel.LEFT,),
                    available_inputs=(),
                    controlled_variables=(),
                    measurements=(),
                ),
                channel_isolation_result_declaration=(
                    ChannelIsolationResultDeclaration((
                        result("declared_metric", "1.5"),
                    ))
                ),
            ),
        ),
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(source_plan,)
        ),
    )
    report = Report(project_name="measurements")
    report.experiments_discovered = ExperimentDiscoveryPresenter().present(context)

    ConsoleReporter().print(report)

    presented = report.experiments_discovered.experiments[0]
    assert presented.evidence_acquisition_plan_coverage_status == (
        "PLAN_COVERAGE_PARTIAL"
    )
    assert presented.plan_result_evaluation_status == "PLAN_RESULT_COMPATIBLE"
    assert presented.compatible_criteria == ("DECLARED_METRIC_EXPECTED",)
    output = capsys.readouterr().out
    assert "Plan coverage status : PLAN_COVERAGE_PARTIAL" in output
    assert "Plan result evaluation status : PLAN_RESULT_COMPATIBLE" in output
    assert (
        "Criterion evaluation : DECLARED_METRIC_EXPECTED | declared_metric | "
        "COMPATIBLE | VALUE_MATCHES_EXPECTATION"
    ) in output
