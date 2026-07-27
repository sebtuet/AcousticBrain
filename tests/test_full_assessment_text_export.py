from pathlib import Path
import subprocess
import sys

import pytest

import main as acousticbrain_main
from acousticbrain.report import (
    FullAssessmentConsoleReporter,
    FullAssessmentTextExportError,
    Report,
)


class RecordingBrain:
    def __init__(self, report):
        self.report = report
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return self.report


class RecordingReporter:
    def __init__(self, text="", error=None):
        self.text = text
        self.error = error
        self.reports = []

    def print(self, report):
        self.reports.append(report)
        if self.error is not None:
            raise self.error
        print(self.text)


class NamedRecordingReporter:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def print(self, report):
        self.calls.append((self.name, report))
        print(self.name)


def run_export(tmp_path, capsys, *, report=None, reporter=None, name="report.txt"):
    campaign = tmp_path / "campaign"
    campaign.mkdir(exist_ok=True)
    output = tmp_path / name
    report = report or object()
    brain = RecordingBrain(report)
    reporter = reporter or RecordingReporter("deterministic report")

    result = acousticbrain_main.main(
        [
            "--measurements-root",
            str(campaign),
            "--full-assessment",
            "--full-assessment-output",
            str(output),
        ],
        brain=brain,
        reporter=reporter,
    )

    return result, output, brain, reporter, capsys.readouterr().out


def test_export_runs_pipeline_and_reporter_once(tmp_path, capsys):
    result, output, brain, reporter, _ = run_export(tmp_path, capsys)

    assert result == 0
    assert output.exists()
    assert len(brain.calls) == 1
    assert len(reporter.reports) == 1


def test_real_cli_stdout_and_file_are_identical_utf8_bytes(tmp_path):
    campaign = tmp_path / "campagne-é"
    campaign.mkdir()
    output = tmp_path / "assessment.txt"

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(acousticbrain_main.__file__).resolve()),
            "--measurements-root",
            str(campaign),
            "--full-assessment",
            "--full-assessment-output",
            str(output),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    exported = output.read_bytes()
    assert completed.returncode == 0, completed.stderr.decode("utf-8")
    assert completed.stdout == exported
    assert "campagne-é".encode("utf-8") in completed.stdout
    assert completed.stdout.decode("utf-8").count("\n") > 5
    assert b"\r\n" not in completed.stdout


def test_export_uses_the_same_report_once(tmp_path, capsys):
    report = object()

    _, _, brain, reporter, _ = run_export(tmp_path, capsys, report=report)

    assert brain.calls == [
        {
            "measurement_root": tmp_path / "campaign",
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_evidence_acquisition": True,
        }
    ]
    assert reporter.reports == [report]


def test_export_runs_each_historical_reporter_once_in_order(tmp_path, capsys):
    report = Report(project_name="export")
    calls = []
    names = ("observations", "reasoning", "actions", "weighting", "plans")
    reporter = FullAssessmentConsoleReporter(
        reporters=tuple(NamedRecordingReporter(name, calls) for name in names)
    )

    _, output, _, _, stdout = run_export(
        tmp_path,
        capsys,
        report=report,
        reporter=reporter,
    )

    assert calls == [(name, report) for name in names]
    assert tuple(stdout.index(name) for name in names) == tuple(
        sorted(stdout.index(name) for name in names)
    )
    assert output.read_bytes() == stdout.encode("utf-8")


def test_two_exports_are_byte_for_byte_identical(tmp_path, capsys):
    _, first, _, _, first_stdout = run_export(
        tmp_path, capsys, name="first.txt"
    )
    _, second, _, _, second_stdout = run_export(
        tmp_path, capsys, name="second.txt"
    )

    assert first.read_bytes() == second.read_bytes()
    assert first_stdout.encode("utf-8") == second_stdout.encode("utf-8")


def test_analysis_error_leaves_no_final_file(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    output = tmp_path / "assessment.txt"

    class FailingBrain:
        def analyze(self, **arguments):
            raise RuntimeError("analysis failed")

    with pytest.raises(RuntimeError, match="analysis failed"):
        acousticbrain_main.main(
            [
                "--measurements-root",
                str(campaign),
                "--full-assessment",
                "--full-assessment-output",
                str(output),
            ],
            brain=FailingBrain(),
            reporter=RecordingReporter(),
        )

    assert not output.exists()


def test_render_error_leaves_no_final_file(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    output = tmp_path / "assessment.txt"

    with pytest.raises(RuntimeError, match="render failed"):
        acousticbrain_main.main(
            [
                "--measurements-root",
                str(campaign),
                "--full-assessment",
                "--full-assessment-output",
                str(output),
            ],
            brain=RecordingBrain(object()),
            reporter=RecordingReporter(error=RuntimeError("render failed")),
        )

    assert not output.exists()


def test_write_error_leaves_no_final_file(tmp_path, capsys, monkeypatch):
    output = tmp_path / "report.txt"

    def fail_link(source, destination):
        raise OSError("write failed")

    monkeypatch.setattr(
        "acousticbrain.report.full_assessment_text_export.os.link",
        fail_link,
    )

    with pytest.raises(SystemExit) as error:
        run_export(tmp_path, capsys)

    assert error.value.code == 2
    assert not output.exists()
    assert not tuple(tmp_path.glob(".report.txt.*.tmp"))


def test_full_assessment_without_export_keeps_historical_output(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    report = object()
    reporter = RecordingReporter("historical output")

    acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--full-assessment"],
        brain=RecordingBrain(report),
        reporter=reporter,
    )
    historical = capsys.readouterr().out

    _, output, _, _, exported = run_export(
        tmp_path,
        capsys,
        report=report,
        reporter=RecordingReporter("historical output"),
    )

    assert historical.encode("utf-8") == exported.encode("utf-8")
    assert output.read_bytes() == historical.encode("utf-8")


def test_export_does_not_create_advisor(monkeypatch, tmp_path, capsys):
    def fail_provider(provider_id):
        raise AssertionError("advisor provider must not be created")

    monkeypatch.setattr(acousticbrain_main, "create_advisor_provider", fail_provider)

    _, output, _, _, _ = run_export(tmp_path, capsys)

    assert output.exists()


def test_exporter_rejects_racing_existing_target(tmp_path, monkeypatch):
    output = tmp_path / "assessment.txt"

    def create_target_before_link(source, destination):
        Path(destination).write_text("preserve", encoding="utf-8")
        raise FileExistsError

    monkeypatch.setattr(
        "acousticbrain.report.full_assessment_text_export.os.link",
        create_target_before_link,
    )

    with pytest.raises(
        FullAssessmentTextExportError,
        match="Full assessment output already exists",
    ):
        acousticbrain_main.FullAssessmentTextExporter(output).write(b"new")

    assert output.read_text(encoding="utf-8") == "preserve"
    assert not tuple(tmp_path.glob(".assessment.txt.*.tmp"))
