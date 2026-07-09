from acousticbrain.importers import REWTxtImporter
from acousticbrain.analyzers.peak_detector import PeakDetector


def test_peak_detector():

    measurement = REWTxtImporter().load("LR.txt")

    detector = PeakDetector()

    peaks = detector.detect(measurement)

    assert len(peaks) > 0

    assert peaks[0].frequency > 20
    