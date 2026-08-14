import json
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.commands import accept_positioning_proposal as command
from test_loudspeaker_positioning_experiment import analyze, recommendation


def campaign(root):
    reference = root / "exp-006"
    measurements = reference / "measurements"
    measurements.mkdir(parents=True)
    measurement = measurements / "LEFT.txt"
    measurement.write_text("existing measurement", encoding="utf-8")
    return root, measurement


def acceptance_arguments(root, proposal_id, experiment_id="exp-007"):
    return (
        "--measurements-root", str(root),
        "--accept-positioning-proposal", proposal_id,
        "--positioning-experiment-id", experiment_id,
        "--positioning-reference", "exp-006",
        "--positioning-declaration-note", "Accepted reversible test.",
    )


def current_proposal_brain(proposal):
    return lambda: SimpleNamespace(
        analyze=lambda **arguments: SimpleNamespace(
            loudspeaker_positioning_experiment=SimpleNamespace(proposal=proposal)
        )
    )


def test_parser_accepts_public_positioning_acceptance_options():
    arguments = acousticbrain_main.create_parser().parse_args((
        "--accept-positioning-proposal", "proposal-001",
        "--positioning-experiment-id", "exp-007",
        "--positioning-reference", "exp-006",
        "--positioning-declaration-note", "Explicit note",
    ))

    assert arguments.accept_positioning_proposal == "proposal-001"
    assert arguments.positioning_experiment_id == "exp-007"
    assert arguments.positioning_reference == "exp-006"
    assert arguments.positioning_declaration_note == "Explicit note"


def test_main_requires_positioning_identifiers_and_rejects_specific_options_alone(
    tmp_path, capsys,
):
    root, _ = campaign(tmp_path / "campaign")

    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--accept-positioning-proposal", "proposal-001",
        ))
    assert "--positioning-experiment-id, --positioning-reference" in (
        capsys.readouterr().err
    )

    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(root),
            "--positioning-experiment-id", "exp-007",
        ))
    assert "require --accept-positioning-proposal" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("conflict", "option"),
    (
        (("--full-assessment",), "--full-assessment"),
        (
            ("--declare-evidence-plan-experiment", "exp-other"),
            "--declare-evidence-plan-experiment",
        ),
        (
            ("--record-sbir-protocol-instance", "protocol.json"),
            "--record-sbir-protocol-instance",
        ),
        (("--exploratory",), "--exploratory"),
    ),
)
def test_main_rejects_incompatible_mode_before_calling_internal_command(
    tmp_path, monkeypatch, capsys, conflict, option,
):
    root, _ = campaign(tmp_path / "campaign")
    calls = []
    monkeypatch.setattr(command, "main", lambda argv: calls.append(argv))

    with pytest.raises(SystemExit):
        acousticbrain_main.main(acceptance_arguments(root, "proposal-001") + conflict)

    assert f"cannot be combined with {option}" in capsys.readouterr().err
    assert calls == []
    assert not (root / "exp-007").exists()


def test_main_delegates_exact_public_arguments_and_returns_immediately(
    tmp_path, monkeypatch,
):
    root, _ = campaign(tmp_path / "campaign")
    calls = []
    monkeypatch.setattr(command, "main", lambda argv: calls.append(argv))

    assert acousticbrain_main.main(
        acceptance_arguments(root, "proposal-001")
    ) == 0

    assert calls == [(
        str(root),
        "--proposal-id", "proposal-001",
        "--experiment", "exp-007",
        "--reference", "exp-006",
        "--note", "Accepted reversible test.",
    )]


def test_main_and_internal_command_create_identical_declarations_without_execution(
    tmp_path, monkeypatch,
):
    proposal = analyze(recommendation()).proposal
    monkeypatch.setattr(command, "AcousticBrain", current_proposal_brain(proposal))
    main_root, main_measurement = campaign(tmp_path / "main")
    internal_root, internal_measurement = campaign(tmp_path / "internal")
    main_before = main_measurement.read_bytes()
    internal_before = internal_measurement.read_bytes()

    assert acousticbrain_main.main(
        acceptance_arguments(main_root, proposal.proposal_id)
    ) == 0
    command.main((
        str(internal_root),
        "--proposal-id", proposal.proposal_id,
        "--experiment", "exp-007",
        "--reference", "exp-006",
        "--note", "Accepted reversible test.",
    ))

    main_manifest = (main_root / "exp-007" / "manifest.json").read_bytes()
    internal_manifest = (internal_root / "exp-007" / "manifest.json").read_bytes()
    assert main_manifest == internal_manifest
    payload = json.loads(main_manifest)
    declaration = payload["experiment_declaration"]
    assert proposal.proposal_id in declaration["field_provenance"]["experiment_kind"]
    assert declaration["modified_variables"] == [
        "LOUDSPEAKER_POSITION"
    ]
    assert "causal_protocol_step" not in payload
    assert "result" not in payload
    assert main_measurement.read_bytes() == main_before
    assert internal_measurement.read_bytes() == internal_before

    assert acousticbrain_main.main(
        acceptance_arguments(main_root, proposal.proposal_id)
    ) == 0
    assert (main_root / "exp-007" / "manifest.json").read_bytes() == main_manifest


def test_main_preserves_internal_stale_proposal_error(tmp_path, monkeypatch, capsys):
    proposal = analyze(recommendation()).proposal
    monkeypatch.setattr(command, "AcousticBrain", current_proposal_brain(proposal))
    root, _ = campaign(tmp_path / "campaign")

    with pytest.raises(ValueError) as internal_error:
        command.main((
            str(root),
            "--proposal-id", "stale-proposal",
            "--experiment", "internal-target",
            "--reference", "exp-006",
        ))
    with pytest.raises(SystemExit):
        acousticbrain_main.main(
            acceptance_arguments(root, "stale-proposal", "main-target")
        )

    assert str(internal_error.value) in capsys.readouterr().err
    assert not (root / "internal-target").exists()
    assert not (root / "main-target").exists()


def test_main_preserves_internal_ineligible_proposal_error(
    tmp_path, monkeypatch, capsys,
):
    monkeypatch.setattr(
        command,
        "AcousticBrain",
        lambda: SimpleNamespace(
            analyze=lambda **arguments: SimpleNamespace(
                loudspeaker_positioning_experiment=None
            )
        ),
    )
    root, _ = campaign(tmp_path / "campaign")

    with pytest.raises(ValueError) as internal_error:
        command.main((
            str(root),
            "--proposal-id", "unknown-proposal",
            "--experiment", "internal-target",
            "--reference", "exp-006",
        ))
    with pytest.raises(SystemExit):
        acousticbrain_main.main(
            acceptance_arguments(root, "unknown-proposal", "main-target")
        )

    assert str(internal_error.value) in capsys.readouterr().err
    assert not (root / "internal-target").exists()
    assert not (root / "main-target").exists()
