from math import isclose

import pytest

from acousticbrain.analysis import RoomGeometryBuilder, RoomModesAnalyzer
from acousticbrain.models import Room, RoomModeType
from acousticbrain.physics import ModesCalculator


def room():
    return Room(name="Reference", length=5.4, width=4.1, height=2.45)


def geometry():
    return RoomGeometryBuilder().from_legacy_room(room())


def analyze(maximum_order=2, minimum_frequency_hz=0.0, maximum_frequency_hz=300.0):
    return RoomModesAnalyzer().analyze(
        geometry(),
        minimum_frequency_hz=minimum_frequency_hz,
        maximum_frequency_hz=maximum_frequency_hz,
        maximum_order=maximum_order,
    )


def test_calculates_and_classifies_all_modal_triplets():
    analysis = analyze(maximum_order=1)

    assert analysis.axial_count == 3
    assert analysis.tangential_count == 3
    assert analysis.oblique_count == 1
    assert analysis.total_count == 7
    assert len({
        (mode.order_x, mode.order_y, mode.order_z)
        for mode in analysis.modes
    }) == 7

    assert analysis.modes[-1].mode_type is RoomModeType.OBLIQUE
    assert analysis.modes[-1].axes == ("Longueur", "Largeur", "Hauteur")


def test_uses_the_complete_room_mode_frequency_formula():
    analysis = analyze(maximum_order=1)
    mode = next(
        mode
        for mode in analysis.modes
        if (mode.order_x, mode.order_y, mode.order_z) == (1, 1, 1)
    )
    expected = 343.0 / 2.0 * (
        (1 / 5.4) ** 2 + (1 / 4.1) ** 2 + (1 / 2.45) ** 2
    ) ** 0.5

    assert isclose(mode.frequency, expected)


def test_filters_by_frequency_and_sorts_the_result():
    analysis = analyze(
        maximum_order=4,
        minimum_frequency_hz=60.0,
        maximum_frequency_hz=100.0,
    )
    frequencies = [mode.frequency for mode in analysis.modes]

    assert frequencies == sorted(frequencies)
    assert all(60.0 <= frequency <= 100.0 for frequency in frequencies)
    assert analysis.minimum_frequency_hz == 60.0
    assert analysis.maximum_frequency_hz == 100.0


def test_preserves_existing_axial_calculation_as_reference():
    complete = analyze(maximum_order=4)
    legacy = ModesCalculator().axial_modes(geometry(), order=4)
    complete_by_axis_order = {
        (mode.axis, mode.order): mode.frequency
        for mode in complete.axial_modes
    }

    assert len(complete.axial_modes) == len(legacy)
    for mode in legacy:
        assert complete_by_axis_order[(mode.axis, mode.order)] == mode.frequency


def test_rejects_invalid_calculation_bounds():
    analyzer = RoomModesAnalyzer()

    with pytest.raises(ValueError):
        analyzer.analyze(
            geometry(),
            minimum_frequency_hz=100.0,
            maximum_frequency_hz=50.0,
            maximum_order=4,
        )

    with pytest.raises(ValueError):
        analyzer.analyze(
            geometry(),
            minimum_frequency_hz=0.0,
            maximum_frequency_hz=100.0,
            maximum_order=0,
        )
