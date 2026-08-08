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


def sources(tmp_path):
    generated = ChannelIsolationOperationalWorksheetService().generate(
        "READY_PLAN", plans=(ready_plan(),)
    )
    microphone = tmp_path / "microphone-source.json"
    settings = tmp_path / "settings-source.json"
    microphone.write_text(
        json.dumps(generated.microphone_position), encoding="utf-8"
    )
    settings.write_text(
        json.dumps(generated.acquisition_settings), encoding="utf-8"
    )
    return microphone, settings


def test_cli_writes_only_two_new_partial_worksheets_with_guidance(tmp_path, capsys):
    microphone, settings = sources(tmp_path)
    microphone_output = tmp_path / "microphone-revised.json"
    settings_output = tmp_path / "settings-revised.json"
    before = (microphone.read_bytes(), settings.read_bytes())
    result = acousticbrain_main.revise_channel_isolation_records(
        tmp_path,
        "READY_PLAN",
        microphone,
        settings,
        {"microphone_position.reference_geometry": "Front wall centerline reference."},
        microphone_output,
        settings_output,
        brain=Brain(),
    )
    output = capsys.readouterr().out
    assert result.documentation_status == "DOCUMENTATION_INCOMPLETE"
    assert "Question : Quelle trace écrite identifie le gain" in output
    assert "Valeurs autorisées : INTENDED_UNCHANGED, NOT_INTENDED_UNCHANGED" in output
    assert "Aucun prérequis confirmé" in output
    assert (microphone.read_bytes(), settings.read_bytes()) == before
    assert tuple(sorted(path.name for path in tmp_path.iterdir())) == (
        "microphone-revised.json",
        "microphone-source.json",
        "settings-revised.json",
        "settings-source.json",
    )


def test_output_prevalidation_prevents_partial_write(tmp_path):
    microphone, settings = sources(tmp_path)
    microphone_output = tmp_path / "microphone-revised.json"
    settings_output = tmp_path / "settings-revised.json"
    settings_output.write_text("preserve\n", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        acousticbrain_main.revise_channel_isolation_records(
            tmp_path,
            "READY_PLAN",
            microphone,
            settings,
            {"microphone_position.reference_geometry": "Documented reference."},
            microphone_output,
            settings_output,
            brain=Brain(),
        )
    assert not microphone_output.exists()
    assert settings_output.read_text(encoding="utf-8") == "preserve\n"


def test_operational_field_parser_rejects_duplicates_and_preserves_equals():
    assert acousticbrain_main.parse_operational_fields((
        "acquisition_settings.gain=gain=recorded",
    )) == {"acquisition_settings.gain": "gain=recorded"}
    with pytest.raises(ValueError, match="Duplicate"):
        acousticbrain_main.parse_operational_fields((
            "acquisition_settings.gain=first",
            "acquisition_settings.gain=second",
        ))


def test_main_requires_outputs_and_explicit_field(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    microphone, settings = sources(tmp_path)
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--revise-channel-isolation-records", "READY_PLAN",
            "--microphone-position-record", str(microphone),
            "--acquisition-settings-record", str(settings),
        ))
    error = capsys.readouterr().err
    assert "--microphone-position-output" in error
    assert "--acquisition-settings-output" in error
