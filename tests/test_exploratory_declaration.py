import json

import pytest

from acousticbrain.application import (
    ExperimentDiscoveryService,
    ExploratoryExperimentDeclarationService,
)
from acousticbrain.report import PresentedExploratoryAnalysis


def ready_analysis(status="EXPLORATORY_READY"):
    return PresentedExploratoryAnalysis(
        status=status,
        proposal_id="exploratory.v1.proposal",
        reference_scope_id="reference.v1.scope",
        rule_version=1,
        candidate_id="generated.left.reflection",
        target="LEFT_FIRST_REFLECTION_AREA",
        reference_experiment_id="baseline",
        action_parameters=(("target", "LEFT_FIRST_REFLECTION_AREA"),
                           ("treatment", "operator-declared-mattress")),
        modified_variables=("TEMPORARY_ABSORPTION_AT_ONE_CANDIDATE_SURFACE",),
        controlled_variables=("LISTENING_POSITION", "LOUDSPEAKER_POSITION"),
        required_measurements=("LEFT", "RIGHT", "STEREO"),
        return_action="REMOVE_TREATMENT_AND_RESTORE_REFERENCE",
        feasibility_question="Can you perform this exact action?",
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
        observable_fact_codes=("etc.channel_specific_event_count",),
        mode="EXPLORATORY",
        causality_status="NOT_ESTABLISHED",
        universal_optimum="NOT_CLAIMED",
    )


def campaign(tmp_path):
    for name in ("baseline", "exp-007"):
        directory = tmp_path / name
        (directory / "measurements").mkdir(parents=True)
        (directory / "measurements" / "LEFT.txt").write_text(
            "Frequency SPL\n20 70\n", encoding="utf-8"
        )
    return tmp_path


def test_ready_proposal_is_preserved_in_generic_experiment_declaration(tmp_path):
    root = campaign(tmp_path)
    measurement = root / "exp-007/measurements/LEFT.txt"
    before = measurement.read_bytes()

    ExploratoryExperimentDeclarationService().declare(
        root, experiment_code="exp-007", analysis=ready_analysis(),
        user_note="Historical operator declaration.",
    )

    assert measurement.read_bytes() == before
    manifest = json.loads((root / "exp-007/manifest.json").read_text())
    assert manifest["exploratory_declaration"]["causality_status"] == "NOT_ESTABLISHED"
    assert manifest["exploratory_declaration"]["return_action"] == (
        "REMOVE_TREATMENT_AND_RESTORE_REFERENCE"
    )
    assert manifest["comparison"]["source_protocol_id"] == "exploratory.v1.proposal"
    assert manifest["comparison"]["required_fact_codes"] == [
        "etc.channel_specific_event_count"
    ]
    descriptor = ExperimentDiscoveryService().discover(root)[1]
    assert descriptor.source_protocol_id == "exploratory.v1.proposal"
    assert descriptor.required_comparison_fact_codes == (
        "etc.channel_specific_event_count",
    )
    assert descriptor.experiment_declaration.modified_variables == (
        "TEMPORARY_ABSORPTION_AT_ONE_CANDIDATE_SURFACE",
    )


def test_non_ready_proposal_cannot_be_declared(tmp_path):
    root = campaign(tmp_path)
    with pytest.raises(ValueError, match="EXPLORATORY_READY"):
        ExploratoryExperimentDeclarationService().declare(
            root, experiment_code="exp-007",
            analysis=ready_analysis("FEASIBILITY_REQUIRED"),
        )
    assert not (root / "exp-007/manifest.json").exists()
