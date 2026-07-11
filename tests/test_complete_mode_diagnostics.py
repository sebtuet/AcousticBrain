from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import RoomModeDiagnostic
from acousticbrain.models import (
    Measurement,
    ModeMatch,
    Peak,
    RoomMode,
    RoomModeType,
)


def test_room_mode_diagnostic_uses_the_complete_mode_family_and_indices():
    peak = Peak(frequency=109.11, spl=80.0, index=0, prominence=5.0)
    mode = RoomMode(
        mode_type=RoomModeType.TANGENTIAL,
        order_x=0,
        order_y=1,
        order_z=2,
        frequency=109.0,
        axes=("Largeur", "Hauteur"),
    )
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.mode_matches = [
        ModeMatch(
            peak=peak,
            mode=mode,
            error_hz=0.11,
            confidence=94.5,
        )
    ]

    diagnostic = RoomModeDiagnostic().analyze(context)

    assert diagnostic.message == (
        "Mode tangentiel Largeur / Hauteur "
        "(indices (0, 1, 2)) à 109.11 Hz"
    )
