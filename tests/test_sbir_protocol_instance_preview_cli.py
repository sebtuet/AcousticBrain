from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import SBIRProtocolInstanceRegistry
from acousticbrain.persistence import (
    SBIRProtocolInstanceInputJsonLoader,
    SBIRProtocolInstanceRegistryJsonRepository,
)
from test_sbir_protocol_instance_compatibility import proposal
from test_sbir_protocol_instance_resolution import (
    experiment,
    geometry_candidate,
    protocol_input,
    source_plan,
)


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(
                plans=(source_plan(),)
            ),
            experiment_descriptors=(
                experiment("baseline"),
                experiment("exp-sbir-001"),
            ),
            geometry_sbir_analysis=SimpleNamespace(
                candidates=(geometry_candidate(),)
            ),
            loudspeaker_positioning_experiment_analysis=SimpleNamespace(
                proposal=proposal()
            ),
        )


class BrainWithoutProposal(Brain):
    def analyze(self, **arguments):
        _, context = super().analyze(**arguments)
        context.loudspeaker_positioning_experiment_analysis = SimpleNamespace(
            proposal=None
        )
        return object(), context


def test_preview_cli_is_read_only_and_prints_all_decisions(tmp_path, capsys):
    registry_path = tmp_path / "registry.json"
    repository = SBIRProtocolInstanceRegistryJsonRepository()
    repository.save(registry_path, SBIRProtocolInstanceRegistry())
    before = registry_path.read_bytes()

    result = acousticbrain_main.preview_sbir_protocol_instance(
        tmp_path,
        protocol_input(source_plan()),
        registry_path,
        brain=Brain(),
    )

    output = capsys.readouterr().out
    assert result.registry_state == "NOT_RECORDED"
    assert "PLAN_EXACTLY_RESOLVED" in output
    assert "SPEAKER_SURFACE_MATCH" in output
    assert "PROTOCOL_INSTANCE_COMPATIBLE" in output
    assert "--record-sbir-protocol-instance" in output
    assert "elle ne déclare ni n’exécute une expérience" in output
    assert "Aucune instance enregistrée" in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert registry_path.read_bytes() == before


def test_main_preview_loads_exact_input_and_does_not_create_registry(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text(
        SBIRProtocolInstanceInputJsonLoader().dumps(
            protocol_input(source_plan())
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "missing-registry.json"

    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--preview-sbir-protocol-instance", str(input_path),
        "--sbir-protocol-instance-registry", str(registry_path),
    ), brain=Brain()) == 0

    output = capsys.readouterr().out
    assert "SBIR PROTOCOL INSTANCE PREVIEW" in output
    assert (
        "python main.py --measurements-root "
        f"{tmp_path} --record-sbir-protocol-instance {input_path} "
        f"--sbir-protocol-instance-registry {registry_path}"
    ) in output
    assert "validation scientifique" not in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert not registry_path.exists()


def test_main_preview_of_recorded_instance_requires_no_recording_action(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text(
        SBIRProtocolInstanceInputJsonLoader().dumps(
            protocol_input(source_plan())
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "sbir-registry.json"

    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--record-sbir-protocol-instance", str(input_path),
        "--sbir-protocol-instance-registry", str(registry_path),
    ), brain=Brain()) == 0
    capsys.readouterr()

    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--preview-sbir-protocol-instance", str(input_path),
        "--sbir-protocol-instance-registry", str(registry_path),
    ), brain=Brain()) == 0

    output = capsys.readouterr().out
    assert "État du registre : ALREADY_RECORDED" in output
    assert "Aucune action : cette instance identique est déjà enregistrée." in output
    assert "--record-sbir-protocol-instance" not in output
    assert "Causality status: NOT_ESTABLISHED" in output


def test_record_cli_writes_only_the_dedicated_registry(tmp_path, capsys):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text(
        SBIRProtocolInstanceInputJsonLoader().dumps(
            protocol_input(source_plan())
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "sbir-registry.json"

    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--record-sbir-protocol-instance", str(input_path),
        "--sbir-protocol-instance-registry", str(registry_path),
    ), brain=Brain()) == 0

    output = capsys.readouterr().out
    assert "SBIR PROTOCOL INSTANCE RECORDED" in output
    assert "PROTOCOL_INSTANCE_COMPATIBLE" in output
    assert "État du registre : RECORDED" in output
    assert "Aucune expérience n’a été déclarée ou exécutée." in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert tuple(sorted(item.name for item in tmp_path.iterdir())) == (
        "sbir-input.json",
        "sbir-registry.json",
    )
    registry = SBIRProtocolInstanceRegistryJsonRepository().load(registry_path)
    assert len(registry.records) == 1


def test_record_cli_is_idempotent_for_identical_input(tmp_path, capsys):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text(
        SBIRProtocolInstanceInputJsonLoader().dumps(
            protocol_input(source_plan())
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "sbir-registry.json"

    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--record-sbir-protocol-instance", str(input_path),
        "--sbir-protocol-instance-registry", str(registry_path),
    ), brain=Brain()) == 0
    first = registry_path.read_bytes()
    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--record-sbir-protocol-instance", str(input_path),
        "--sbir-protocol-instance-registry", str(registry_path),
    ), brain=Brain()) == 0

    output = capsys.readouterr().out
    assert "État du registre : ALREADY_RECORDED" in output
    assert registry_path.read_bytes() == first


def test_record_cli_requires_existing_displacement_proposal(tmp_path):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text(
        SBIRProtocolInstanceInputJsonLoader().dumps(
            protocol_input(source_plan())
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "sbir-registry.json"

    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(tmp_path),
            "--record-sbir-protocol-instance", str(input_path),
            "--sbir-protocol-instance-registry", str(registry_path),
        ), brain=BrainWithoutProposal())

    assert not registry_path.exists()


def test_preview_parser_requires_explicit_registry(tmp_path, capsys):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(tmp_path),
            "--preview-sbir-protocol-instance", str(input_path),
        ), brain=Brain())
    assert "requires --sbir-protocol-instance-registry" in (
        capsys.readouterr().err
    )


def test_record_parser_requires_explicit_registry(tmp_path, capsys):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(tmp_path),
            "--record-sbir-protocol-instance", str(input_path),
        ), brain=Brain())
    assert "requires --sbir-protocol-instance-registry" in (
        capsys.readouterr().err
    )


def test_preview_cannot_be_combined_with_an_existing_output_mode(
    tmp_path,
    capsys,
):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(tmp_path),
            "--preview-sbir-protocol-instance", str(input_path),
            "--sbir-protocol-instance-registry", str(tmp_path / "registry.json"),
            "--full-assessment",
        ), brain=Brain())
    assert "cannot be combined with --full-assessment" in (
        capsys.readouterr().err
    )


def test_record_cannot_be_combined_with_preview(tmp_path, capsys):
    input_path = tmp_path / "sbir-input.json"
    input_path.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(tmp_path),
            "--preview-sbir-protocol-instance", str(input_path),
            "--record-sbir-protocol-instance", str(input_path),
            "--sbir-protocol-instance-registry", str(tmp_path / "registry.json"),
        ), brain=Brain())
    assert "cannot be combined with --record-sbir-protocol-instance" in (
        capsys.readouterr().err
    )
