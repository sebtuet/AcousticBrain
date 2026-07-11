from acousticbrain.analysis import ModalDensityAnalyzer
from acousticbrain.models import (
    RoomMode,
    RoomModesAnalysis,
    RoomModeType,
)


def mode(mode_type, indices, frequency):
    axes = tuple(
        axis
        for axis, order in zip(
            ("Longueur", "Largeur", "Hauteur"),
            indices,
        )
        if order
    )
    return RoomMode(
        mode_type=mode_type,
        order_x=indices[0],
        order_y=indices[1],
        order_z=indices[2],
        frequency=frequency,
        axes=axes,
    )


def room_modes_analysis(modes):
    axial = [item for item in modes if item.mode_type is RoomModeType.AXIAL]
    tangential = [
        item for item in modes if item.mode_type is RoomModeType.TANGENTIAL
    ]
    oblique = [item for item in modes if item.mode_type is RoomModeType.OBLIQUE]
    return RoomModesAnalysis(
        modes=modes,
        axial_modes=axial,
        tangential_modes=tangential,
        oblique_modes=oblique,
        minimum_frequency_hz=0.0,
        maximum_frequency_hz=300.0,
        axial_count=len(axial),
        tangential_count=len(tangential),
        oblique_count=len(oblique),
        total_count=len(modes),
        confidence=100.0,
    )


def test_modal_density_analyzer_reports_complete_mode_distribution():
    modes = [
        mode(RoomModeType.AXIAL, (1, 0, 0), 32),
        mode(RoomModeType.TANGENTIAL, (1, 1, 0), 42),
        mode(RoomModeType.OBLIQUE, (1, 1, 1), 70),
        mode(RoomModeType.AXIAL, (2, 0, 0), 95),
    ]

    analysis = ModalDensityAnalyzer().analyze(
        room_modes_analysis(modes),
        schroeder_frequency=120,
    )

    assert analysis.total_mode_count == 4
    assert analysis.axial_mode_count == 2
    assert analysis.tangential_mode_count == 1
    assert analysis.oblique_mode_count == 1
    assert len(analysis.bands) == 3
    assert analysis.average_spacing_hz == 21
    assert analysis.confidence == 70
    assert 0 <= analysis.score <= 100
