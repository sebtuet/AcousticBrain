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


def descriptor(experiment_id, experiment_type, state, timestamp):
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
