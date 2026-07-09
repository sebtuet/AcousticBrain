from acousticbrain.importers import REWTxtImporter


def test_import():

    importer = REWTxtImporter()

    measurement = importer.load("LR.txt")

    assert len(measurement.frequency) > 1000

    assert len(measurement.frequency) == len(measurement.spl)

    assert len(measurement.spl) == len(measurement.phase)

    