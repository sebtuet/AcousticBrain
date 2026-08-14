from acousticbrain.importers import REWTxtImporter
from acousticbrain.analyzers.peak_detector import PeakDetector
from test_golden_report import reference_stereo_measurement_path


def test_peak_detector():

    measurement = REWTxtImporter().load(reference_stereo_measurement_path())

    detector = PeakDetector()

    peaks = detector.detect(measurement)

    assert len(peaks) > 0

    assert peaks[0].frequency > 20
