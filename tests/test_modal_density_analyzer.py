from acousticbrain.analysis import ModalDensityAnalyzer
from acousticbrain.models import RoomMode


def test_modal_density_analyzer_reports_axial_mode_distribution():
    modes = [
        RoomMode(axis="Longueur", order=1, frequency=32),
        RoomMode(axis="Largeur", order=1, frequency=42),
        RoomMode(axis="Hauteur", order=1, frequency=70),
        RoomMode(axis="Longueur", order=2, frequency=95),
    ]

    analysis = ModalDensityAnalyzer().analyze(modes, schroeder_frequency=120)

    assert analysis.total_mode_count == 4
    assert len(analysis.bands) == 3
    assert analysis.average_spacing_hz == 21
    assert analysis.confidence == 70
    assert 0 <= analysis.score <= 100
