import json
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import ChannelIsolationOperationalWorksheetService
from acousticbrain.persistence import EvidencePlanPreparationConfirmationJsonLoader
from test_channel_isolation_documentation_review import complete_records
from test_evidence_plan_preparation_resolution import confirmation, ready_plan


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(plans=(ready_plan(),))
        )


def test_cli_reviews_documentation_without_prefilling_or_writing_statuses(tmp_path, capsys):
    plan = ready_plan()
    microphone_value, settings_value = complete_records(plan)
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    source = tmp_path / "source.json"
    microphone.write_text(json.dumps(microphone_value), encoding="utf-8")
    settings.write_text(json.dumps(settings_value), encoding="utf-8")
    EvidencePlanPreparationConfirmationJsonLoader().save_new(source, confirmation(plan))
    before = tuple(path.read_bytes() for path in (microphone, settings, source))

    result = acousticbrain_main.review_channel_isolation_documentation(
        tmp_path, plan.plan_id, microphone, settings, source, brain=Brain()
    )

    output = capsys.readouterr().out
    assert result.user_action_state == "EXPLICIT_PREPARATION_REVISION_REQUIRED"
    assert output.count("USER_PREPARATION_DECISION_REQUIRED") == 2
    assert "documented_microphone_position=<STATUS>" in output
    assert "existing_acquisition_settings=<STATUS>" in output
    assert "Aucun statut choisi" in output
    assert tuple(path.read_bytes() for path in (microphone, settings, source)) == before


def test_main_requires_source_preparation_for_documentation_review(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--review-channel-isolation-documentation", "READY_PLAN",
            "--microphone-position-record", str(microphone),
            "--acquisition-settings-record", str(settings),
        ))
    assert "requires --channel-isolation-source-preparation" in capsys.readouterr().err


def test_main_rejects_documentation_review_combined_with_preview(tmp_path, capsys):
    root = tmp_path / "measurements"
    root.mkdir()
    microphone = tmp_path / "microphone.json"
    settings = tmp_path / "settings.json"
    source = tmp_path / "source.json"
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--review-channel-isolation-documentation", "READY_PLAN",
            "--preview-channel-isolation-records", "READY_PLAN",
            "--microphone-position-record", str(microphone),
            "--acquisition-settings-record", str(settings),
            "--channel-isolation-source-preparation", str(source),
        ))
    assert "cannot be combined with --preview-channel-isolation-records" in capsys.readouterr().err
