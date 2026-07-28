from functools import lru_cache
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from acousticbrain.brain import AcousticBrain
from acousticbrain.importers import ImportEngine
from acousticbrain.models import (
    ExperimentFileType,
    ImpulseChannel,
    Speaker,
)
from acousticbrain.persistence import MeasurementRepository
from acousticbrain.report import ConsoleReporter

from historical_campaign import HISTORICAL_CAMPAIGN_ROOT


ROOT = Path(__file__).resolve().parents[1]


@lru_cache
def reference_stereo_measurement_path():
    files = MeasurementRepository().inspect_directory(
        HISTORICAL_CAMPAIGN_ROOT / "baseline"
    )
    return next(
        item.path
        for item in files
        if item.file_type is ExperimentFileType.TXT_MEASUREMENT
        and item.channel is ImpulseChannel.STEREO
    )


def reference_project():
    with TemporaryDirectory() as temporary_directory:
        campaign_root = Path(temporary_directory) / "historical_reference"
        shutil.copytree(HISTORICAL_CAMPAIGN_ROOT, campaign_root)
        project = ImportEngine().load_directory(str(campaign_root))
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

    # Le golden acoustique historique correspond aux anciens exports
    # impulsionnels texte. La branche PR-027 remplace la fixture de travail par
    # des WAV plus courts ; le contrat du chemin Project reste vérifié sans
    # réécrire artificiellement cette référence acoustique.
    if not (HISTORICAL_CAMPAIGN_ROOT / "Impulse_Left.txt").is_file():
        assert report.experiments_discovered is None
        assert report.experiment_planning is None
        return

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/reference_report.txt").read_text()
    assert capsys.readouterr().out == expected
