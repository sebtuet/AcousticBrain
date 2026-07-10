from acousticbrain.importers import REWTxtImporter

from acousticbrain.analyzers.peak_detector import PeakDetector

from acousticbrain.classifiers import FrequencyBandClassifier


def test_band_classifier():

    measurement = REWTxtImporter().load("measurements/LR.txt")

    peaks = PeakDetector().detect(measurement)

    bands = FrequencyBandClassifier().classify(peaks)

    assert len(bands) == 4

    assert sum(len(b.peaks) for b in bands) == len(peaks)

    