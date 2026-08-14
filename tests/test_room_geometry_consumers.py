import math

import pytest

from acousticbrain.analysis import RoomGeometryBuilder, RoomModesAnalyzer
from acousticbrain.models import (
    Room,
    RoomDescription,
    RoomDimensions,
)
from acousticbrain.physics import RoomAcoustics


def equivalent_geometries():
    builder = RoomGeometryBuilder()
    legacy = builder.from_legacy_room(Room("Legacy", 5.84, 5.51, 2.60))
    declared = builder.from_description(
        RoomDescription(
            name="Declared",
            dimensions=RoomDimensions(5.84, 5.51, 2.60),
        )
    )
    return legacy, declared


def analyze_modes(geometry):
    return RoomModesAnalyzer().analyze(
        geometry,
        minimum_frequency_hz=0.0,
        maximum_frequency_hz=300.0,
        maximum_order=4,
    )


def test_equivalent_sources_produce_bit_identical_room_properties():
    legacy, declared = equivalent_geometries()

    legacy_properties = RoomAcoustics().calculate(legacy)
    declared_properties = RoomAcoustics().calculate(declared)

    assert declared_properties == legacy_properties
    assert legacy_properties.volume == 5.84 * 5.51 * 2.60
    assert legacy_properties.floor_area == 5.84 * 5.51
    assert legacy_properties.total_area == (
        2 * 5.84 * 5.51 + 2 * 5.84 * 2.60 + 2 * 5.51 * 2.60
    )
    assert legacy_properties.schroeder_frequency == (
        2000 * math.sqrt(0.30 / legacy_properties.volume)
    )


def test_equivalent_sources_produce_identical_modes_in_identical_order():
    legacy, declared = equivalent_geometries()

    legacy_modes = analyze_modes(legacy)
    declared_modes = analyze_modes(declared)

    legacy_facts = [
        (
            mode.mode_type,
            mode.order_x,
            mode.order_y,
            mode.order_z,
            mode.frequency,
            mode.axes,
        )
        for mode in legacy_modes.modes
    ]
    declared_facts = [
        (
            mode.mode_type,
            mode.order_x,
            mode.order_y,
            mode.order_z,
            mode.frequency,
            mode.axes,
        )
        for mode in declared_modes.modes
    ]

    assert declared_facts == legacy_facts
    assert declared_modes.axial_count == legacy_modes.axial_count
    assert declared_modes.tangential_count == legacy_modes.tangential_count
    assert declared_modes.oblique_count == legacy_modes.oblique_count


@pytest.mark.parametrize(
    "consumer",
    [
        lambda room: RoomAcoustics().calculate(room),
        lambda room: RoomModesAnalyzer().analyze(
            room,
            minimum_frequency_hz=0.0,
            maximum_frequency_hz=300.0,
            maximum_order=4,
        ),
    ],
)
def test_migrated_consumers_reject_legacy_room_directly(consumer):
    with pytest.raises(TypeError, match="RoomGeometry"):
        consumer(Room("Legacy", 5.84, 5.51, 2.60))
