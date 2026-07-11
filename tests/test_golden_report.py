from pathlib import Path

from acousticbrain.brain import AcousticBrain
from acousticbrain.importers import ImportEngine
from acousticbrain.models import Speaker
from acousticbrain.report import ConsoleReporter


ROOT = Path(__file__).resolve().parents[1]


def reference_project():
    project = ImportEngine().load_directory(str(ROOT / "measurements"))
    project.add_speaker(
        Speaker(
            name="Left",
            distance_front_wall=0.82,
            distance_side_wall=0.55,
            height=1.05,
        )
    )
    project.add_speaker(
        Speaker(
            name="Right",
            distance_front_wall=0.82,
            distance_side_wall=0.55,
            height=1.05,
        )
    )
    return project


def test_reference_measurements_match_the_golden_report(capsys):
    report = AcousticBrain().analyze(reference_project())

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/reference_report.txt").read_text()
    assert capsys.readouterr().out == expected

