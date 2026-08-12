from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from test_sbir_protocol_instance_compatibility import proposal
from test_sbir_protocol_instance_resolution import (
    experiment,
    geometry_candidate,
    source_plan,
)
from test_sbir_protocol_instance_sources import planning_candidate


class Brain:
    def analyze(self, **arguments):
        return object(), SimpleNamespace(
            evidence_acquisition_plan_synthesis=SimpleNamespace(
                plans=(source_plan(),)
            ),
            experiment_descriptors=(
                experiment("exp-sbir-001"),
                experiment("baseline"),
            ),
            geometry_sbir_analysis=SimpleNamespace(
                candidates=(geometry_candidate(),)
            ),
            loudspeaker_positioning_experiment_analysis=SimpleNamespace(
                proposal=proposal()
            ),
            experiment_planning_analysis=SimpleNamespace(
                plan=SimpleNamespace(
                    ordered_candidates=(),
                    ineligible_candidates=(planning_candidate(),),
                )
            ),
        )


def test_source_overview_prints_all_blocks_without_selection(tmp_path, capsys):
    result = acousticbrain_main.show_sbir_protocol_instance_sources(
        tmp_path,
        brain=Brain(),
    )
    output = capsys.readouterr().out
    assert "Plans sources" in output
    assert "Expériences disponibles" in output
    assert "Candidats géométriques" in output
    assert "Propositions de déplacement" in output
    assert "Planification du déplacement SBIR" in output
    assert "geometry-candidate-001" in output
    assert "proposal-sbir-001" in output
    assert "SBIR_PREDICTION_UNCERTAINTY_TOO_HIGH" in output
    assert "23.17 %" in output
    assert "Limite d'éligibilité : 10.00 %" in output
    assert "Dépassement de limite : 13.17 %" in output
    assert "NO_SELECTION_PERFORMED" in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert result.selection_status == "NO_SELECTION_PERFORMED"


def test_main_source_overview_is_standalone_and_creates_no_file(
    tmp_path,
    capsys,
):
    before = tuple(tmp_path.iterdir())
    assert acousticbrain_main.main((
        "--measurements-root", str(tmp_path),
        "--sbir-protocol-instance-sources",
    ), brain=Brain()) == 0
    assert "SBIR PROTOCOL INSTANCE SOURCES" in capsys.readouterr().out
    assert tuple(tmp_path.iterdir()) == before


def test_source_overview_rejects_existing_output_modes(tmp_path, capsys):
    with pytest.raises(SystemExit):
        acousticbrain_main.main((
            "--measurements-root", str(tmp_path),
            "--sbir-protocol-instance-sources",
            "--full-assessment",
        ), brain=Brain())
    assert "cannot be combined with --full-assessment" in (
        capsys.readouterr().err
    )
