from acousticbrain.analysis import StereoAnalyzer
from acousticbrain.models import Measurement, Peak, RoomMode


def peak(frequency, prominence=5.0):
    return Peak(frequency=frequency, spl=80.0, index=0, prominence=prominence)


def test_matches_low_frequency_with_minimum_tolerance():
    analysis = StereoAnalyzer().analyze([peak(40)], [peak(42)])

    assert analysis.common_count == 1


def test_matches_high_frequency_with_relative_tolerance():
    analysis = StereoAnalyzer().analyze([peak(1000)], [peak(1019)])

    assert analysis.common_count == 1


def test_rejects_peaks_in_different_bands():
    analysis = StereoAnalyzer().analyze([peak(199)], [peak(201)])

    assert analysis.common_count == 0


def test_rejects_peaks_with_different_prominence():
    analysis = StereoAnalyzer().analyze([peak(1000, 4)], [peak(1001, 8)])

    assert analysis.common_count == 0


def test_classifies_room_modes_per_channel():
    modes = [RoomMode(axis="Longueur", order=1, frequency=63.0)]

    analysis = StereoAnalyzer().analyze(
        [peak(63)],
        [peak(64)],
        room_modes=modes,
    )

    assert analysis.common_modes == modes
    assert analysis.left_only_modes == []
    assert analysis.right_only_modes == []


def test_calculates_average_balance_by_frequency_range():
    left = Measurement(
        name="Left",
        frequency=[100, 1000, 5000],
        spl=[80, 81, 82],
    )
    right = Measurement(
        name="Right",
        frequency=[100, 1000, 5000],
        spl=[78, 80, 82],
    )

    analysis = StereoAnalyzer().analyze(
        [],
        [],
        left_measurement=left,
        right_measurement=right,
    )

    assert analysis.balance_low == 2
    assert analysis.balance_mid == 1
    assert analysis.balance_high == 0


def test_symmetry_score_weights_strong_peaks_more_heavily():
    analysis = StereoAnalyzer().analyze(
        [peak(63, 20), peak(100, 3)],
        [peak(63, 20)],
    )

    assert analysis.symmetry_score > 90
