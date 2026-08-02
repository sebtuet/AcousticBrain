import json
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from test_evidence_plan_preparation_resolution import ready_plan


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(ready_plan(),))
        )


def test_cli_generates_both_explicit_worksheets_without_other_writes(tmp_path, capsys):
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    acousticbrain_main.generate_channel_isolation_records(
        tmp_path, "READY_PLAN", microphone, settings, brain=Brain()
    )
    assert json.loads(microphone.read_text())["reference_geometry"].startswith("REPLACE_")
    assert json.loads(settings.read_text())["reuse_declaration"].startswith("REPLACE_")
    assert tuple(sorted(path.name for path in tmp_path.iterdir())) == (
        "microphone.json", "settings.json"
    )
    assert "Aucun prérequis confirmé" in capsys.readouterr().out


def test_prevalidation_prevents_partial_output(tmp_path):
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    settings.write_text("existing\n")
    with pytest.raises(ValueError, match="already exists"):
        acousticbrain_main.generate_channel_isolation_records(
            tmp_path, "READY_PLAN", microphone, settings, brain=Brain()
        )
    assert not microphone.exists()
    assert settings.read_text() == "existing\n"


def test_main_requires_both_output_paths(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--generate-channel-isolation-records", "READY_PLAN",
            "--microphone-position-output", str(tmp_path / "microphone.json"),
        ))
    assert "requires both worksheet output paths" in capsys.readouterr().err
