from dataclasses import replace

import pytest

from acousticbrain.application import (
    RoomDescriptionProposalService,
    RoomDescriptionQuestionPlanner,
    StructuredRoomDescriptionInterpreter,
)
from acousticbrain.catalogs import BuiltInSurfaceMaterialCatalog
from acousticbrain.models import (
    GuidedAnswerInterpretation,
    GuidedInterpretationStatus,
    PlanarSurfaceDescription,
    PlanarSurfaceRole,
    PlanarVertexDescription,
    RoomDescription,
    RoomDescriptionChangeProposalStatus,
    RoomDimensions,
    SurfaceMaterialAssignment,
    SurfaceMaterialDescriptionSource,
)


def room(**overrides):
    values = {"name": "room", "dimensions": RoomDimensions(5, 4, 3)}
    values.update(overrides)
    return RoomDescription(**values)


def surface(surface_id, role, x):
    return PlanarSurfaceDescription(
        surface_id, role,
        (
            PlanarVertexDescription(x, 0, 0),
            PlanarVertexDescription(x, 1, 0),
            PlanarVertexDescription(x, 1, 1),
        ),
    )


def ready_proposal(description=None, value="GYPSUM_BOARD_PAINTED", target_id=None):
    description = description or room()
    question = RoomDescriptionQuestionPlanner().plan(description)
    interpretation = StructuredRoomDescriptionInterpreter().interpret(
        question, value, target_id=target_id, confidence=60.0
    )
    proposal = RoomDescriptionProposalService().propose(
        description, question, interpretation
    )
    return description, question, proposal


def test_planner_chooses_first_missing_material_fact_deterministically():
    question = RoomDescriptionQuestionPlanner().plan(room())
    assert question.question_id == "material.surface.left_wall"
    assert question.target_id == "left_wall"
    assert question.priority.value == 75


def test_question_exposes_values_constraints_and_unknown_consequences():
    question = RoomDescriptionQuestionPlanner().plan(room())
    assert "GYPSUM_BOARD_PAINTED" in {
        item.value_id for item in question.allowed_values
    }
    assert "VALUE_MUST_BE_ALLOWED" in question.validation_constraints
    assert "NO_PROTOCOL_ELIGIBILITY_IS_PROMISED" in question.unknown_consequences


def test_planner_returns_none_when_all_targets_are_assigned():
    material = BuiltInSurfaceMaterialCatalog().entries[0].material
    assignments = tuple(
        SurfaceMaterialAssignment(f"a:{target}", material.material_id, surface_id=target)
        for target in (
            "left_wall", "right_wall", "front_wall", "rear_wall", "floor", "ceiling"
        )
    )
    assert RoomDescriptionQuestionPlanner().plan(
        room(materials=(material,), material_assignments=assignments)
    ) is None


def test_multiple_surfaces_with_same_role_require_explicit_target():
    description = room(planar_surfaces=(
        surface("LEFT_WALL_PANEL_01", PlanarSurfaceRole.LEFT_WALL, 0),
        surface("LEFT_WALL_PANEL_02", PlanarSurfaceRole.LEFT_WALL, 1),
    ))
    question = RoomDescriptionQuestionPlanner().plan(description)
    assert question.target_id is None
    assert question.requires_target_confirmation
    assert question.target_candidates == ("LEFT_WALL_PANEL_01", "LEFT_WALL_PANEL_02")


def test_ambiguous_target_is_never_selected_silently():
    description = room(planar_surfaces=(
        surface("LEFT_WALL_PANEL_01", PlanarSurfaceRole.LEFT_WALL, 0),
        surface("LEFT_WALL_PANEL_02", PlanarSurfaceRole.LEFT_WALL, 1),
    ))
    question = RoomDescriptionQuestionPlanner().plan(description)
    interpretation = StructuredRoomDescriptionInterpreter().interpret(
        question, "WOOD", confidence=70
    )
    proposal = RoomDescriptionProposalService().propose(
        description, question, interpretation
    )
    assert proposal.status is RoomDescriptionChangeProposalStatus.NEEDS_CLARIFICATION
    assert "TARGET_REQUIRES_CLARIFICATION" in proposal.unresolved_ambiguities


def test_explicit_candidate_target_can_be_proposed():
    description = room(planar_surfaces=(
        surface("LEFT_WALL_PANEL_01", PlanarSurfaceRole.LEFT_WALL, 0),
        surface("LEFT_WALL_PANEL_02", PlanarSurfaceRole.LEFT_WALL, 1),
    ))
    _, _, proposal = ready_proposal(
        description, "WOOD", target_id="LEFT_WALL_PANEL_02"
    )
    assert proposal.target_id == "LEFT_WALL_PANEL_02"
    assert proposal.status is RoomDescriptionChangeProposalStatus.READY_FOR_CONFIRMATION


def test_unallowed_structured_value_requires_clarification():
    question = RoomDescriptionQuestionPlanner().plan(room())
    interpretation = StructuredRoomDescriptionInterpreter().interpret(
        question, "INVENTED_MATERIAL"
    )
    proposal = RoomDescriptionProposalService().propose(
        room(), question, interpretation
    )
    assert proposal.status is RoomDescriptionChangeProposalStatus.NEEDS_CLARIFICATION
    assert not proposal.requested_changes


def test_other_material_requires_further_description():
    _, _, proposal = ready_proposal(value="OTHER")
    assert proposal.status is RoomDescriptionChangeProposalStatus.NEEDS_CLARIFICATION
    assert "OTHER_MATERIAL_REQUIRES_DESCRIPTION" in proposal.unresolved_ambiguities


@pytest.mark.parametrize(
    "status",
    [
        GuidedInterpretationStatus.AMBIGUOUS,
        GuidedInterpretationStatus.CONTRADICTORY,
        GuidedInterpretationStatus.INSUFFICIENT,
    ],
)
def test_non_candidate_interpretations_do_not_bypass_clarification(status):
    description = room()
    question = RoomDescriptionQuestionPlanner().plan(description)
    interpretation = GuidedAnswerInterpretation(
        status, ambiguity_codes=(status.value,)
    )
    proposal = RoomDescriptionProposalService().propose(
        description, question, interpretation
    )
    assert proposal.status is RoomDescriptionChangeProposalStatus.NEEDS_CLARIFICATION


def test_ready_proposal_contains_before_after_confirmation_summary_data():
    _, _, proposal = ready_proposal()
    assert proposal.predicted_completeness_change.before == 0
    assert proposal.predicted_completeness_change.after == pytest.approx(100 / 6)
    assert proposal.requires_confirmation
    assert proposal.potentially_unblocked_capabilities == ()


def test_potential_capability_is_only_reported_as_projection():
    material = BuiltInSurfaceMaterialCatalog().entries[0].material
    targets = ("left_wall", "right_wall", "front_wall", "rear_wall", "floor")
    assignments = tuple(
        SurfaceMaterialAssignment(f"a:{target}", material.material_id, surface_id=target)
        for target in targets
    )
    description = room(materials=(material,), material_assignments=assignments)
    _, _, proposal = ready_proposal(description)
    assert proposal.potentially_unblocked_capabilities == (
        "POTENTIALLY_COMPLETE_SURFACE_MATERIAL_ASSIGNMENTS",
    )
    assert "ELIGIBLE" not in proposal.potentially_unblocked_capabilities[0]


def test_only_ready_proposal_can_be_confirmed():
    service = RoomDescriptionProposalService()
    _, _, proposal = ready_proposal(value="OTHER")
    with pytest.raises(ValueError):
        service.confirm(proposal)


def test_confirmation_does_not_apply_or_persist_the_change():
    service = RoomDescriptionProposalService()
    description, _, proposal = ready_proposal()
    confirmed = service.confirm(proposal)
    assert confirmed.status is RoomDescriptionChangeProposalStatus.CONFIRMED
    assert description.material_assignments == ()


def test_only_confirmed_proposal_can_be_applied():
    service = RoomDescriptionProposalService()
    description, _, proposal = ready_proposal()
    with pytest.raises(ValueError):
        service.apply(description, proposal)


def test_apply_adds_catalog_profile_and_separate_description_provenance():
    service = RoomDescriptionProposalService()
    description, _, proposal = ready_proposal()
    updated, applied = service.apply(description, service.confirm(proposal))
    material = updated.materials[0]
    assignment = updated.material_assignments[0]
    assert material.catalog_entry_id == "material.gypsum_board_painted.v1"
    assert assignment.description_source is (
        SurfaceMaterialDescriptionSource.USER_STRUCTURED_INPUT
    )
    assert assignment.description_confidence == 60.0
    assert applied.status is RoomDescriptionChangeProposalStatus.APPLIED


def test_unknown_is_persisted_as_unknown_without_invented_coefficients():
    service = RoomDescriptionProposalService()
    description, _, proposal = ready_proposal(value="UNKNOWN")
    updated, _ = service.apply(description, service.confirm(proposal))
    assert updated.materials[0].absorption_coefficients == ()
    assert updated.materials[0].confidence == 0.0


def test_applied_proposal_cannot_be_rejected():
    service = RoomDescriptionProposalService()
    description, _, proposal = ready_proposal()
    _, applied = service.apply(description, service.confirm(proposal))
    with pytest.raises(ValueError):
        service.reject(applied)


def test_proposal_identifier_is_deterministic():
    assert ready_proposal()[2].proposal_id == ready_proposal()[2].proposal_id
