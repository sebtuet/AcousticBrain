from acousticbrain.importers import REWTxtImporter
from acousticbrain.analyzers import SPLAnalyzer
from test_golden_report import reference_stereo_measurement_path


def test_spl_analyzer():

    importer = REWTxtImporter()

    measurement = importer.load(reference_stereo_measurement_path())

    analyzer = SPLAnalyzer()

    result = analyzer.analyze(measurement)

    assert result["points"] > 0

    assert result["max_frequency"] > result["min_frequency"]

    assert result["max_spl"] > result["min_spl"]
