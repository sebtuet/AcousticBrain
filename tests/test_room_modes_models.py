from dataclasses import asdict, fields

from acousticbrain.models import RoomMode, RoomModesAnalysis, RoomModeType


def test_room_mode_keeps_complete_modal_indices():
    mode = RoomMode(
        mode_type=RoomModeType.TANGENTIAL,
        order_x=1,
        order_y=1,
        order_z=0,
        frequency=52.4,
        axes=("Longueur", "Largeur"),
    )

    assert asdict(mode) == {
        "mode_type": RoomModeType.TANGENTIAL,
        "order_x": 1,
        "order_y": 1,
        "order_z": 0,
        "frequency": 52.4,
        "axes": ("Longueur", "Largeur"),
    }


def test_room_mode_type_distinguishes_all_geometric_families():
    assert [mode_type.value for mode_type in RoomModeType] == [
        "AXIAL",
        "TANGENTIAL",
        "OBLIQUE",
    ]


def test_room_modes_analysis_contains_facts_without_an_acoustic_score():
    axial = RoomMode(
        mode_type=RoomModeType.AXIAL,
        order_x=2,
        order_y=0,
        order_z=0,
        frequency=63.5,
        axes=("Longueur",),
    )
    analysis = RoomModesAnalysis(
        modes=[axial],
        axial_modes=[axial],
        tangential_modes=[],
        oblique_modes=[],
        minimum_frequency_hz=63.5,
        maximum_frequency_hz=63.5,
        axial_count=1,
        tangential_count=0,
        oblique_count=0,
        total_count=1,
        confidence=100.0,
    )

    assert analysis.modes == [axial]
    assert analysis.total_count == 1
    assert "score" not in {field.name for field in fields(RoomModesAnalysis)}


def test_legacy_axial_constructor_and_accessors_remain_compatible():
    mode = RoomMode(axis="Largeur", order=2, frequency=83.7)

    assert mode.mode_type is RoomModeType.AXIAL
    assert (mode.order_x, mode.order_y, mode.order_z) == (0, 2, 0)
    assert mode.axes == ("Largeur",)
    assert mode.axis == "Largeur"
    assert mode.order == 2


def test_room_modes_contract_contains_no_user_or_action_text():
    field_names = set()
    for model in (RoomMode, RoomModesAnalysis):
        field_names.update(field.name for field in fields(model))

    assert field_names.isdisjoint(
        {
            "diagnostic",
            "message",
            "recommendation",
            "recommendations",
            "title",
        }
    )

