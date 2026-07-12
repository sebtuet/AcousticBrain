from acousticbrain.models import (
    Peak,
    Room,
    RoomModeType,
)
from acousticbrain.analysis import RoomGeometryBuilder, RoomModesAnalyzer
from acousticbrain.physics import ModeMatcher


def test_matches_peaks_against_all_mode_families():
    modes = RoomModesAnalyzer().analyze(
        RoomGeometryBuilder().from_legacy_room(
            Room(name="Room", length=5.4, width=4.1, height=2.45)
        ),
        minimum_frequency_hz=0.0,
        maximum_frequency_hz=150.0,
        maximum_order=2,
    )
    target = next(
        mode
        for mode in modes.oblique_modes
        if (mode.order_x, mode.order_y, mode.order_z) == (1, 1, 1)
    )
    peak = Peak(
        frequency=target.frequency + 0.5,
        spl=80.0,
        index=0,
        prominence=5.0,
    )

    match = ModeMatcher().match([peak], modes, tolerance=2.0)[0]

    assert match.mode is target
    assert match.mode.mode_type is RoomModeType.OBLIQUE
    assert match.mode.axes == ("Longueur", "Largeur", "Hauteur")
