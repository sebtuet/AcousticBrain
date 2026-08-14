import json
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import ChannelIsolationOperationalWorksheetService
from test_evidence_plan_preparation_resolution import ready_plan


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(ready_plan(),))
        )


def test_cli_previews_incomplete_worksheets_without_writing(tmp_path, capsys):
    generated = ChannelIsolationOperationalWorksheetService().generate(
        "READY_PLAN", plans=(ready_plan(),)
    )
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    microphone.write_text(json.dumps(generated.microphone_position), encoding="utf-8")
    settings.write_text(json.dumps(generated.acquisition_settings), encoding="utf-8")
    before = (microphone.read_bytes(), settings.read_bytes())
    result = acousticbrain_main.preview_channel_isolation_records(
        tmp_path, "READY_PLAN", microphone, settings, brain=Brain()
    )
    output = capsys.readouterr().out
    assert result.status == "DOCUMENTATION_INCOMPLETE"
    assert "microphone_position.reference_geometry" in output
    assert "Aucun prérequis confirmé" in output
    assert (microphone.read_bytes(), settings.read_bytes()) == before


def test_main_requires_both_operational_record_paths(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--preview-channel-isolation-records", "READY_PLAN",
            "--microphone-position-record", str(tmp_path / "microphone.json"),
        ))
    assert "requires both operational record paths" in capsys.readouterr().err


def test_main_rejects_preview_combined_with_full_assessment(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    microphone.write_text("{}", encoding="utf-8")
    settings.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--preview-channel-isolation-records", "READY_PLAN",
            "--microphone-position-record", str(microphone),
            "--acquisition-settings-record", str(settings),
            "--full-assessment",
        ))
    assert "cannot be combined with --full-assessment" in capsys.readouterr().err
