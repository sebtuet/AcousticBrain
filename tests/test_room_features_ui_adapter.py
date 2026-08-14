from dataclasses import fields

from acousticbrain.ui import (
    AcousticTreatmentFormRow,
    FurnitureFormRow,
    RoomDescriptionEditorAdapter,
    RoomDescriptionEditorLevel,
    RoomDescriptionFormState,
    SpeakerPositionFormRow,
    SurfaceCoveringZoneFormRow,
    SurfaceMaterialFormRow,
    section_visibility,
)


def enriched_state():
    return RoomDescriptionFormState(
        name="Room",
        length_m="5.84",
        width_m="5.51",
        height_m="2.6",
        speakers=(
            SpeakerPositionFormRow("LEFT", "0.54", "0.77", "0.88", "15.0"),
            SpeakerPositionFormRow("RIGHT", "0.51", "3.25", "0.88", "-15.0"),
        ),
        surface_materials=(
            SurfaceMaterialFormRow("FLOOR", "TILE", "carrelage"),
            SurfaceMaterialFormRow("FRONT_WALL", "WOOD", ""),
        ),
        covering_zones=(
            SurfaceCoveringZoneFormRow("RUG", "FLOOR", "CARPET"),
        ),
        furniture=(FurnitureFormRow("SOFA", "SOFA"),),
        acoustic_treatments=(
            AcousticTreatmentFormRow(
                "PANEL",
                "ABSORBER",
                "broadband",
                "FRONT_WALL",
                "1.0",
                "1.0",
                "1.0",
                "1.0",
            ),
        ),
    )


def test_three_editor_levels_only_control_section_visibility():
    minimal = section_visibility(RoomDescriptionEditorLevel.MINIMAL)
    guided = section_visibility(RoomDescriptionEditorLevel.GUIDED)
    expert = section_visibility(RoomDescriptionEditorLevel.EXPERT)

    assert not any(minimal.__dict__.values())
    assert guided.speakers
    assert guided.listening_positions
    assert guided.surface_materials
    assert not guided.openings
    assert not guided.covering_zones
    assert all(expert.__dict__.values())
    assert "editor_level" not in {field.name for field in fields(RoomDescriptionFormState)}


def test_visibility_level_never_changes_form_semantics():
    adapter = RoomDescriptionEditorAdapter()
    state = enriched_state()
    expected = adapter.validate(state).description

    for level in RoomDescriptionEditorLevel:
        section_visibility(level)
        assert adapter.validate(state).description == expected


def test_enriched_form_round_trip_preserves_orientation_features_and_blanks():
    adapter = RoomDescriptionEditorAdapter()
    state = enriched_state()

    serialized = adapter.serialize(state)
    loaded = adapter.load(serialized.payload)

    assert serialized.is_success
    assert loaded.is_success
    assert loaded.state == state
    description = adapter.validate(state).description
    assert description.speakers[0].orientation.yaw_degrees == 15.0
    assert description.speakers[1].orientation.yaw_degrees == -15.0
    assert description.covering_zones[0].width_m is None
    assert description.furniture[0].x_m is None


def test_optional_form_values_are_not_replaced_when_blank():
    description = RoomDescriptionEditorAdapter().validate(enriched_state()).description

    assert description.surface_materials[1].detail is None
    assert description.covering_zones[0].detail is None
    assert description.acoustic_treatments[0].surface.value == "FRONT_WALL"
