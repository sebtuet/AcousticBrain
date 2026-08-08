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

    assert "SBIR PROTOCOL INSTANCE PREVIEW" in capsys.readouterr().out
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
