from acousticbrain.importers import REWTxtImporter
from acousticbrain.analyzers import SPLAnalyzer


def test_spl_analyzer():

    importer = REWTxtImporter()

    measurement = importer.load("LR.txt")

    analyzer = SPLAnalyzer()

    result = analyzer.analyze(measurement)

    assert result["points"] > 0

    assert result["max_frequency"] > result["min_frequency"]

    assert result["max_spl"] > result["min_spl"]