from dataclasses import replace

import pytest

from acousticbrain.application import SBIRProtocolInstanceCompatibilityValidator
from acousticbrain.models import (
    LoudspeakerMovementAxis,
    LoudspeakerMovementDirection,
    LoudspeakerPositioningExperimentProposal,
    LoudspeakerPositioningProposalStatus,
    LoudspeakerPositioningTarget,
    SBIRProtocolInstanceCompatibility,
    SBIRProtocolInstanceCompatibilityDecision,
)
from test_sbir_protocol_instance_resolution import resolve


def proposal(**overrides):
    values = {
        "proposal_id": "proposal-sbir-001",
        "source_recommendation_ids": ("VERIFY_SBIR_PLACEMENT",),
        "source_hypothesis_codes": ("SBIR_PLACEMENT_INTERACTION",),
        "target": LoudspeakerPositioningTarget.LEFT_SPEAKER,
        "movement_axis": LoudspeakerMovementAxis.LONGITUDINAL,
        "movement_direction": LoudspeakerMovementDirection.FORWARD,
        "step_distance_m": 0.12,
        "tested_variable": "LOUDSPEAKER_POSITION",
        "controlled_variables": ("MICROPHONE_POSITION",),
        "required_measurements": ("L", "R", "L+R"),
        "expected_observables": ("SBIR_MOVES_WITH_SPEAKER",),
        "rationale": ("Existing structured displacement proposal.",),
        "confidence": 90.0,
        "causality_status": "NOT_ESTABLISHED",
        "proposal_status": LoudspeakerPositioningProposalStatus.ELIGIBLE,
        "provenance": (("step_distance_m", "SOURCE_PARAMETER"),),
        "source_surface_id": "front_wall",
        "source_geometry_candidate_id": "geometry-candidate-001",
    }
    values.update(overrides)
    return LoudspeakerPositioningExperimentProposal(**values)


DEFAULT_PROPOSALS = object()


def validate(resolution=None, proposals=DEFAULT_PROPOSALS):
    return SBIRProtocolInstanceCompatibilityValidator().validate(
        resolution or resolve(),
        displacement_proposals=(
            (proposal(),) if proposals is DEFAULT_PROPOSALS else proposals
        ),
    )


def test_exact_existing_source_continuity_establishes_compatibility_only():
    result = validate()

    assert isinstance(result, SBIRProtocolInstanceCompatibility)
    assert result.decisions == tuple(SBIRProtocolInstanceCompatibilityDecision)
    assert result.displacement_proposal.proposal_id == "proposal-sbir-001"
    assert not hasattr(result, "experiment_declaration")
    assert not hasattr(result, "causality_status")


@pytest.mark.parametrize(
    ("field", "declared", "expected_fields"),
    (
        ("speaker_id", "RIGHT", "speaker_id"),
        ("surface_id", "rear_wall", "surface_id"),
    ),
)
def test_speaker_and_surface_must_match_candidate_exactly(
    field,
    declared,
    expected_fields,
):
    resolution = resolve()
    changed_input = replace(
        resolution.protocol_instance_input,
        **{field: declared},
    )
    changed_resolution = replace(
        resolution,
        protocol_instance_input=changed_input,
    )
    with pytest.raises(ValueError, match=(
        "SPEAKER_SURFACE_MISMATCH: incompatible fields: "
        f"{expected_fields}"
    )):
        validate(changed_resolution)


def test_all_speaker_surface_divergences_are_reported_in_fixed_order():
    resolution = resolve()
    changed_input = replace(
        resolution.protocol_instance_input,
        speaker_id="RIGHT",
        surface_id="rear_wall",
    )
    changed_resolution = replace(
        resolution,
        protocol_instance_input=changed_input,
    )
    with pytest.raises(ValueError) as error:
        validate(changed_resolution)
    assert str(error.value).endswith(
        "incompatible fields: speaker_id, surface_id."
    )


@pytest.mark.parametrize(
    ("proposals", "code"),
    (
        ((), "DISPLACEMENT_PROPOSAL_UNKNOWN"),
        ((proposal(), proposal(proposal_id="proposal-sbir-002")),
         "DISPLACEMENT_PROPOSAL_AMBIGUOUS"),
    ),
)
def test_displacement_proposal_association_is_exact(proposals, code):
    with pytest.raises(ValueError, match=code):
        validate(proposals=proposals)


def test_unrelated_proposals_are_not_selected_by_distance_or_surface():
    unrelated = proposal(
        proposal_id="unrelated",
        source_geometry_candidate_id="geometry-unrelated",
    )
    with pytest.raises(ValueError, match="DISPLACEMENT_PROPOSAL_UNKNOWN"):
        validate(proposals=(unrelated,))


@pytest.mark.parametrize(
    ("overrides", "field"),
    (
        ({"source_surface_id": "rear_wall"}, "source_surface_id"),
        ({"step_distance_m": 0.10}, "speaker_displacement_m"),
    ),
)
def test_proposal_surface_and_displacement_must_match_exactly(overrides, field):
    with pytest.raises(ValueError, match=(
        "DISPLACEMENT_SOURCE_MISMATCH: incompatible fields: " + field
    )):
        validate(proposals=(proposal(**overrides),))


def test_all_proposal_divergences_are_reported_in_fixed_order():
    with pytest.raises(ValueError) as error:
        validate(proposals=(proposal(
            source_surface_id="rear_wall",
            step_distance_m=0.10,
        ),))
    assert str(error.value).endswith(
        "incompatible fields: source_surface_id, speaker_displacement_m."
    )


def test_validation_is_independent_of_unrelated_proposal_order():
    expected = proposal()
    unrelated = proposal(
        proposal_id="unrelated",
        source_geometry_candidate_id="geometry-unrelated",
    )
    first = validate(proposals=(unrelated, expected))
    second = validate(proposals=(expected, unrelated))
    assert first == second


@pytest.mark.parametrize("values", ([], None, (object(),)))
def test_proposal_collection_is_explicitly_typed(values):
    with pytest.raises(TypeError, match="proposals"):
        validate(proposals=values)


def test_compatibility_model_rejects_missing_or_reordered_decisions():
    result = validate()
    with pytest.raises(ValueError, match="incomplete or out of order"):
        replace(result, decisions=tuple(reversed(result.decisions)))


def test_validation_does_not_mutate_resolution_or_proposals():
    resolution = resolve()
    proposals = (proposal(),)
    snapshot = (resolution, proposals)
    validate(resolution, proposals)
    assert snapshot == (resolution, proposals)
