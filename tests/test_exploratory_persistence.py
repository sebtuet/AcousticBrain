import json

import pytest

from acousticbrain.application import ExploratoryFeasibilityRegistry
from acousticbrain.models import ExploratoryFeasibilityDecision, FeasibilityAnswer
from acousticbrain.persistence import (
    ExploratoryFeasibilityJsonRepository,
    ExploratoryProposalInputJsonLoader,
)


def test_proposal_input_loader_requires_explicit_structured_fields(tmp_path):
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "exploratory_proposal_input": {
            "candidate_id": "candidate.one",
            "reference_experiment_id": "baseline",
            "reference_content_fingerprint": "sha256:abc",
            "reference_configuration": {"room": "reference"},
            "action_parameters": {"target": "LEFT_FIRST_REFLECTION_AREA"},
            "return_action": "RESTORE_REFERENCE",
            "feasibility_question": "Can you perform and reverse this action?",
            "limitations": ["CAUSALITY_NOT_ESTABLISHED"],
            "field_provenance": {"target": "USER_DECLARATION"},
        },
    }), encoding="utf-8")
    result = ExploratoryProposalInputJsonLoader().load(path)
    assert result.reference_configuration == (("room", "reference"),)
    assert result.action_parameters == (("target", "LEFT_FIRST_REFLECTION_AREA"),)


def test_proposal_input_loader_never_parses_free_text_as_parameters(tmp_path):
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "exploratory_proposal_input": {
            "candidate_id": "candidate.one",
            "reference_experiment_id": "baseline",
            "reference_content_fingerprint": "sha256:abc",
            "reference_configuration": {"room": "reference"},
            "user_note": "put a mattress on the left wall",
            "return_action": "RESTORE_REFERENCE",
            "feasibility_question": "Can you do it?",
            "limitations": ["CAUSALITY_NOT_ESTABLISHED"],
            "field_provenance": {"target": "USER_DECLARATION"},
        },
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="action_parameters"):
        ExploratoryProposalInputJsonLoader().load(path)


def test_feasibility_repository_round_trip_and_missing_file(tmp_path):
    repository = ExploratoryFeasibilityJsonRepository()
    path = tmp_path / "decisions.json"
    assert repository.load(path).decisions == ()
    decision = ExploratoryFeasibilityDecision(
        proposal_id="proposal.one", reference_scope_id="reference.one",
        rule_version=1, answer=FeasibilityAnswer.INFEASIBLE,
        user_note="Not possible in this configuration.",
    )
    repository.save(ExploratoryFeasibilityRegistry((decision,)), path)
    assert repository.load(path).decisions == (decision,)
