from pathlib import Path

import pytest

from acousticbrain.importers import ImportEngine, REWImpulseImporter
from acousticbrain.models import ImpulseChannel, ImpulseResponse


FIXTURE = Path(__file__).parent / "fixtures" / "impulse_minimal.txt"


def test_imports_rew_metadata_and_exact_raw_samples():
    impulse = REWImpulseImporter().load(
        FIXTURE,
        channel=ImpulseChannel.LEFT,
    )

    assert isinstance(impulse, ImpulseResponse)
    assert impulse.channel is ImpulseChannel.LEFT
    assert impulse.source_id == "Minimal impulse"
    assert impulse.peak_value == 0.75
    assert impulse.peak_index == 2
    assert impulse.response_length == 5
    assert impulse.sample_interval_s == 2.0833333333333333e-5
    assert impulse.sample_rate_hz == 48_000.0
    assert impulse.start_time_s == -0.00004166666666666667
    assert impulse.time_offset_seconds == impulse.start_time_s
    assert impulse.samples == [0.0, -0.25, 1.0, 0.5, -0.125]


def test_requires_the_channel_explicitly():
    with pytest.raises(TypeError):
        REWImpulseImporter().load(FIXTURE)


def test_rejects_an_incomplete_sample_sequence(tmp_path):
    incomplete = tmp_path / "incomplete.txt"
    incomplete.write_text(FIXTURE.read_text().replace("5 // Response", "6 // Response"))

    with pytest.raises(ValueError, match="sample count"):
        REWImpulseImporter().load(incomplete, channel=ImpulseChannel.STEREO)


def test_rejects_an_out_of_range_peak_index(tmp_path):
    inconsistent = tmp_path / "inconsistent.txt"
    inconsistent.write_text(FIXTURE.read_text().replace("2 // Peak index", "5 // Peak index"))

    with pytest.raises(ValueError, match="peak index"):
        REWImpulseImporter().load(inconsistent, channel=ImpulseChannel.RIGHT)


def test_rejects_missing_required_metadata(tmp_path):
    incomplete = tmp_path / "missing-metadata.txt"
    incomplete.write_text(
        FIXTURE.read_text().replace(
            "0.75 // Peak value before normalisation\n",
            "",
        )
    )

    with pytest.raises(ValueError, match="peak_value"):
        REWImpulseImporter().load(incomplete, channel=ImpulseChannel.SUB)


def test_rejects_non_numeric_samples(tmp_path):
    inconsistent = tmp_path / "invalid-sample.txt"
    inconsistent.write_text(FIXTURE.read_text().replace("-0.125\n", "invalid\n"))

    with pytest.raises(ValueError, match="Invalid REW impulse sample"):
        REWImpulseImporter().load(inconsistent, channel=ImpulseChannel.LEFT)


def test_rejects_duplicate_metadata(tmp_path):
    inconsistent = tmp_path / "duplicate-metadata.txt"
    inconsistent.write_text(
        FIXTURE.read_text().replace(
            "2 // Peak index\n",
            "2 // Peak index\n2 // Peak index\n",
        )
    )

    with pytest.raises(ValueError, match="Duplicate.*peak_index"):
        REWImpulseImporter().load(inconsistent, channel=ImpulseChannel.LEFT)


def test_directory_import_loads_reference_impulse_channels():
    project = ImportEngine().load_directory(
        Path(__file__).resolve().parents[1] / "measurements"
    )

    assert set(project.impulse_responses) == {
        ImpulseChannel.LEFT,
        ImpulseChannel.RIGHT,
        ImpulseChannel.STEREO,
    }
