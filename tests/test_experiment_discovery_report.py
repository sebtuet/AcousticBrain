from pathlib import Path
from types import SimpleNamespace

from acousticbrain.models import (
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
        available_channels=(ImpulseChannel.STEREO,),
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

    expected = (ROOT / "tests/golden/experiment_discovery_report.txt").read_text()
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
