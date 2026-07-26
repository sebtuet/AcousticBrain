from pathlib import Path
import subprocess
import sys

import pytest

import main as acousticbrain_main


class RecordingBrain:
    def __init__(self, report=None):
        self.report = report or object()
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return self.report


class RecordingReporter:
    def __init__(self):
        self.reports = []

    def print(self, report):
        self.reports.append(report)


def test_parser_uses_historical_measurements_default():
    arguments = acousticbrain_main.create_parser().parse_args([])

    assert arguments.measurements_root == Path("measurements")


def test_parser_accepts_full_assessment():
    arguments = acousticbrain_main.create_parser().parse_args(["--full-assessment"])

    assert arguments.full_assessment is True


@pytest.mark.parametrize(
    "value",
    (
        "relative/campaign",
        "/tmp/absolute-campaign",
        "campaign with spaces",
    ),
)
def test_parser_preserves_explicit_path(value):
    arguments = acousticbrain_main.create_parser().parse_args(
        ["--measurements-root", value]
    )

    assert arguments.measurements_root == Path(value)


def test_validation_rejects_missing_path(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="Measurements root does not exist"):
        acousticbrain_main.validate_measurements_root(missing)


def test_validation_rejects_file(tmp_path):
    file_path = tmp_path / "campaign.txt"
    file_path.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValueError, match="Measurements root is not a directory"):
        acousticbrain_main.validate_measurements_root(file_path)


@pytest.mark.parametrize(
    ("path_kind", "message"),
    (
        ("missing", "Measurements root does not exist"),
        ("file", "Measurements root is not a directory"),
    ),
)
def test_main_returns_nonzero_for_invalid_root(
    tmp_path, capsys, path_kind, message
):
    path = tmp_path / "invalid campaign"
    if path_kind == "file":
        path.write_text("not a directory", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(["--measurements-root", str(path)])

    assert error.value.code == 2
    assert message in capsys.readouterr().err


def test_main_passes_exact_relative_path_without_changing_cwd(tmp_path, monkeypatch):
    campaign = tmp_path / "campaign with spaces"
    campaign.mkdir()
    relative = Path("campaign with spaces")
    monkeypatch.chdir(tmp_path)
    original_cwd = Path.cwd()
    brain = RecordingBrain()
    reporter = RecordingReporter()

    result = acousticbrain_main.main(
        ["--measurements-root", str(relative)],
        brain=brain,
        reporter=reporter,
    )

    assert result == 0
    assert Path.cwd() == original_cwd
    assert brain.calls == [
        {
            "measurement_root": relative,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
        }
    ]
    assert reporter.reports == [brain.report]


def test_main_passes_exact_absolute_path(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert brain.calls[0]["measurement_root"] == campaign


def test_full_assessment_activates_only_evidence_acquisition_synthesis(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--full-assessment"],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_evidence_acquisition": True,
        }
    ]


@pytest.mark.parametrize(
    "option",
    (
        "--observations",
        "--reasoning",
        "--actions",
        "--weighting",
        "--evidence-acquisition",
        "--advisor",
    ),
)
def test_full_assessment_rejects_each_incompatible_option(
    tmp_path, capsys, option
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            ["--measurements-root", str(campaign), "--full-assessment", option],
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert f"--full-assessment cannot be combined with {option}." in (
        capsys.readouterr().err
    )


def test_default_and_explicit_historical_path_are_invariant(tmp_path, monkeypatch):
    (tmp_path / "measurements").mkdir()
    monkeypatch.chdir(tmp_path)
    default_brain = RecordingBrain(report="same-report")
    explicit_brain = RecordingBrain(report="same-report")

    acousticbrain_main.main(
        [], brain=default_brain, reporter=RecordingReporter()
    )
    acousticbrain_main.main(
        ["--measurements-root", "measurements"],
        brain=explicit_brain,
        reporter=RecordingReporter(),
    )

    assert default_brain.calls == explicit_brain.calls


def test_cli_reports_invalid_path_without_traceback(tmp_path):
    missing = tmp_path / "missing campaign"

    result = subprocess.run(
        [
            sys.executable,
            str(Path(acousticbrain_main.__file__).resolve()),
            "--measurements-root",
            str(missing),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert f"Measurements root does not exist: {missing}" in result.stderr
    assert "Traceback" not in result.stderr
