from pathlib import Path

from acousticbrain.importers import REWTxtImporter


MEASUREMENT_FILE = (
    Path(__file__).resolve().parents[1]
    / "measurements"
    / "LR.txt"
)


def test_import():

    measurement = REWTxtImporter().load(
        MEASUREMENT_FILE
    )

    assert measurement.name == "L+R retour sans eq Jul 7"

    assert len(measurement.frequency) > 0

    assert len(measurement.frequency) == len(
        measurement.spl
    )

    assert len(measurement.spl) == len(
        measurement.phase
    )

    assert measurement.frequency[0] > 20

    assert measurement.frequency[-1] > 20000