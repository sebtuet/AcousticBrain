from dataclasses import FrozenInstanceError

import pytest

from acousticbrain.catalogs import (
    BuiltInSurfaceMaterialCatalog,
    SurfaceMaterialCatalog,
)
from acousticbrain.models import (
    GuidedAllowedValue,
    GuidedAnswerInterpretation,
    GuidedCompletenessProjection,
    GuidedInterpretationStatus,
    RoomDescriptionChangeProposalStatus,
    SurfaceMaterialAssignment,
    SurfaceMaterialDescriptionSource,
    SurfaceMaterialSource,
)


def test_profile_and_description_provenance_are_distinct():
    catalog = BuiltInSurfaceMaterialCatalog()
    profile = catalog.get("material.gypsum_board_painted.v1").material
    assignment = SurfaceMaterialAssignment(
        "a", profile.material_id, surface_id="left_wall",
        description_source=(
            SurfaceMaterialDescriptionSource.USER_DESCRIPTION_INTERPRETED
        ),
        description_confidence=60.0,
        provenance_codes=("USER_DESCRIPTION_INTERPRETED",),
    )

    assert profile.source is SurfaceMaterialSource.CATALOG_ESTIMATE
    assert profile.confidence == 65.0
    assert assignment.description_confidence == 60.0


@pytest.mark.parametrize("confidence", [-1, 101, float("inf"), True])
def test_assignment_rejects_invalid_description_confidence(confidence):
    with pytest.raises(ValueError):
        SurfaceMaterialAssignment(
            "a", "m", surface_id="left_wall",
            description_confidence=confidence,
        )


def test_catalog_identifiers_are_explicitly_versioned_and_immutable():
    catalog = BuiltInSurfaceMaterialCatalog()
    entry = catalog.get("material.gypsum_board_painted.v1")

    assert entry.catalog_entry_id.endswith(".v1")
    assert catalog.get("material.gypsum_board_painted") is None
    with pytest.raises(FrozenInstanceError):
        entry.display_name = "changed"


def test_catalog_rejects_duplicate_identifiers():
    entry = BuiltInSurfaceMaterialCatalog().entries[0]
    with pytest.raises(ValueError):
        SurfaceMaterialCatalog((entry, entry))


def test_catalog_contains_simple_user_facing_material_types():
    catalog = BuiltInSurfaceMaterialCatalog()
    assert {item.material_type for item in catalog.entries} == {
        "CONCRETE", "BRICK", "GYPSUM_BOARD_PAINTED", "WOOD", "GLAZING", "UNKNOWN"
    }


@pytest.mark.parametrize(
    "source",
    [
        SurfaceMaterialSource.MEASURED,
        SurfaceMaterialSource.MANUFACTURER_DATA,
        SurfaceMaterialSource.CATALOG_ESTIMATE,
        SurfaceMaterialSource.USER_PROVIDED,
    ],
)
def test_supported_profile_origins_are_explicit(source):
    assert source.value


def test_allowed_value_validates_catalog_identifier():
    with pytest.raises(ValueError):
        GuidedAllowedValue("WOOD", "Wood", catalog_entry_id="")


def test_interpretation_is_candidate_data_only():
    interpretation = GuidedAnswerInterpretation(
        GuidedInterpretationStatus.CANDIDATE,
        candidate_value_ids=("WOOD",),
        confidence=60,
    )
    assert interpretation.candidate_value_ids == ("WOOD",)
    assert not hasattr(interpretation, "room_description")


@pytest.mark.parametrize("before,after", [(-1, 0), (0, 101), (float("nan"), 0)])
def test_completeness_projection_is_bounded(before, after):
    with pytest.raises(ValueError):
        GuidedCompletenessProjection(before, after)


def test_confirmed_and_applied_states_remain_distinct():
    assert (
        RoomDescriptionChangeProposalStatus.CONFIRMED
        is not RoomDescriptionChangeProposalStatus.APPLIED
    )
