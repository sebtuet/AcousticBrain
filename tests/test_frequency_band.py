from acousticbrain.importers import REWTxtImporter

from acousticbrain.analyzers.peak_detector import PeakDetector

from acousticbrain.classifiers import FrequencyBandClassifier
from test_golden_report import reference_stereo_measurement_path


def test_band_classifier():

    measurement = REWTxtImporter().load(reference_stereo_measurement_path())

    peaks = PeakDetector().detect(measurement)

    bands = FrequencyBandClassifier().classify(peaks)

    assert len(bands) == 4

    assert sum(len(b.peaks) for b in bands) == len(peaks)

