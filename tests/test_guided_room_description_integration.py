import json
from types import SimpleNamespace

from acousticbrain.adapters import OllamaGuidedRoomDescriptionAdapter
from acousticbrain.application import (
    GuidedRoomDescriptionWorkflow,
    RoomDescriptionProposalService,
    RoomDescriptionQuestionPlanner,
    StructuredRoomDescriptionInterpreter,
)
from acousticbrain.models import (
    GuidedInterpretationStatus,
    RoomDescription,
    RoomDescriptionChangeProposalStatus,
    RoomDimensions,
)
from acousticbrain.report import RoomDescriptionChangeProposalPresenter


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.prompts = []

    def ask(self, prompt):
        self.prompts.append(prompt)
        return self.response


def room():
    return RoomDescription("room", RoomDimensions(5, 4, 3))


def question():
    return RoomDescriptionQuestionPlanner().plan(room())


def test_ollama_formulates_question_without_changing_question_plan():
    source = question()
    client = FakeClient("Quel matériau compose le mur gauche ?")
    adapter = OllamaGuidedRoomDescriptionAdapter(client)
    result = adapter.formulate(source)
    assert result == "Quel matériau compose le mur gauche ?"
    assert source.target_id == "left_wall"


def test_ollama_maps_free_text_to_an_authorized_candidate_only():
    client = FakeClient(json.dumps({
        "status": "CANDIDATE",
        "candidate_value_ids": ["GYPSUM_BOARD_PAINTED"],
        "target_id": "left_wall",
        "confidence": 60,
        "ambiguity_codes": [],
    }))
    result = OllamaGuidedRoomDescriptionAdapter(client).interpret(
        question(), "Cela ressemble probablement à du placo peint."
    )
    assert result.status is GuidedInterpretationStatus.CANDIDATE
    assert result.candidate_value_ids == ("GYPSUM_BOARD_PAINTED",)
    assert result.provenance_codes == ("USER_DESCRIPTION_INTERPRETED",)


def test_ollama_cannot_invent_a_material_candidate():
    client = FakeClient(json.dumps({
        "status": "CANDIDATE",
        "candidate_value_ids": ["MAGIC_FOAM"],
        "confidence": 100,
    }))
    result = OllamaGuidedRoomDescriptionAdapter(client).interpret(
        question(), "mousse magique"
    )
    assert result.status is GuidedInterpretationStatus.INSUFFICIENT
    assert result.candidate_value_ids == ()


def test_ollama_cannot_select_a_target_outside_candidates():
    client = FakeClient(json.dumps({
        "status": "CANDIDATE",
        "candidate_value_ids": ["WOOD"],
        "target_id": "invented_surface",
        "confidence": 70,
    }))
    result = OllamaGuidedRoomDescriptionAdapter(client).interpret(
        question(), "bois"
    )
    assert result.status is GuidedInterpretationStatus.INSUFFICIENT
    assert "TARGET_OUTSIDE" in result.ambiguity_codes[0]


def test_invalid_ollama_json_becomes_insufficient_information():
    result = OllamaGuidedRoomDescriptionAdapter(FakeClient("not json")).interpret(
        question(), "placo"
    )
    assert result.status is GuidedInterpretationStatus.INSUFFICIENT


def test_empty_user_answer_does_not_call_ollama():
    client = FakeClient("unused")
    result = OllamaGuidedRoomDescriptionAdapter(client).interpret(question(), "  ")
    assert result.status is GuidedInterpretationStatus.INSUFFICIENT
    assert client.prompts == []


def test_ollama_prompt_forbids_acoustic_invention():
    client = FakeClient("{}")
    OllamaGuidedRoomDescriptionAdapter(client).interpret(question(), "placo")
    assert "N'invente aucune propriété acoustique" in client.prompts[0]


def confirmed_proposal():
    description = room()
    planned = RoomDescriptionQuestionPlanner().plan(description)
    interpretation = StructuredRoomDescriptionInterpreter().interpret(
        planned, "GYPSUM_BOARD_PAINTED", confidence=60
    )
    service = RoomDescriptionProposalService()
    return description, service.confirm(
        service.propose(description, planned, interpretation)
    )


def test_confirmation_presenter_contains_projection_disclaimer():
    _, proposal = confirmed_proposal()
    presented = RoomDescriptionChangeProposalPresenter().present(proposal)
    assert presented.status == "CONFIRMED"
    assert "eligibility requires a complete new analysis" in (
        presented.eligibility_disclaimer
    )
    assert not presented.requires_confirmation


def test_workflow_persists_v5_then_runs_one_complete_analysis():
    description, proposal = confirmed_proposal()
    project = SimpleNamespace(room_description=description)
    calls = []

    def analyze(candidate_project):
        calls.append(candidate_project.room_description)
        return "new-report"

    result = GuidedRoomDescriptionWorkflow().apply(project, proposal, analyze)

    assert json.loads(result.serialized_room_description)["schema_version"] == 5
    assert len(calls) == 1
    assert calls[0] is project.room_description
    assert result.analysis_result == "new-report"
    assert result.full_analysis_triggered
    assert result.proposal.status is RoomDescriptionChangeProposalStatus.APPLIED


def test_workflow_never_mutates_scientific_conclusions_directly():
    description, proposal = confirmed_proposal()
    project = SimpleNamespace(
        room_description=description,
        acoustic_reasoning_analysis="old-conclusions",
    )

    GuidedRoomDescriptionWorkflow().apply(project, proposal, lambda _: "report")

    assert project.acoustic_reasoning_analysis == "old-conclusions"


def test_deterministic_mode_has_no_ollama_dependency():
    planned = question()
    result = StructuredRoomDescriptionInterpreter().interpret(
        planned, "WOOD", confidence=100
    )
    assert result.status is GuidedInterpretationStatus.CANDIDATE
