from unittest.mock import Mock

import pytest

from acousticbrain.application import ExperimentDiscoveryService
from acousticbrain.brain import AcousticBrain
from acousticbrain.importers import ExperimentImporter, REWTxtImporter


def rew_export(channel, rows):
    return (
        "* Measurement data measured by REW\n"
        f"* Measurement: {channel}\n"
        "* Freq(Hz) SPL(dB) Phase(degrees)\n"
        + "\n".join(rows)
        + "\n"
    )


@pytest.mark.parametrize(
    "content",
    (
        "* Measurement: LEFT\n* Freq(Hz) SPL(dB) Phase(degrees)\n",
        "* Measurement: LEFT\n* Freq(Hz) SPL(dB)\n20 70\n100 71\n",
        rew_export("LEFT", ("20 70 phase?", "100 71 phase?")),
        rew_export("LEFT", ("20 70 0", "100 71 phase?")),
    ),
    ids=("header-only", "frequency-spl-only", "empty-phase", "unequal-lengths"),
)
def test_rejects_incomplete_frequency_exports_with_actionable_file_error(
    tmp_path,
    content,
):
    path = tmp_path / "invalid-export.txt"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError) as raised:
        REWTxtImporter().load(path)

    message = str(raised.value)
    assert str(path) in message
    assert "does not contain the expected frequency" in message
    assert "phase inclusion" in message


def test_preserves_a_nominal_frequency_export(tmp_path):
    path = tmp_path / "nominal.txt"
    path.write_text(
        rew_export("LEFT", ("20 70 0", "100 71 1", "20000 69 -2")),
        encoding="utf-8",
    )

    measurement = REWTxtImporter().load(path)

    assert measurement.name == "LEFT"
    assert measurement.frequency == [20.0, 100.0, 20000.0]
    assert measurement.spl == [70.0, 71.0, 69.0]
    assert measurement.phase == [0.0, 1.0, -2.0]


def test_rejects_multiple_frequency_exports_for_the_same_channel(tmp_path):
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "left-first.txt").write_text(
        rew_export("LEFT", ("20 70 0",)), encoding="utf-8"
    )
    (baseline / "left-second.txt").write_text(
        rew_export("LEFT", ("20 72 0",)), encoding="utf-8"
    )
    (baseline / "right.txt").write_text(
        rew_export("RIGHT", ("20 70 0",)), encoding="utf-8"
    )
    (baseline / "stereo.txt").write_text(
        rew_export("L+R", ("20 70 0",)), encoding="utf-8"
    )
    descriptor = ExperimentDiscoveryService().discover(tmp_path)[0]

    with pytest.raises(ValueError) as raised:
        ExperimentImporter().load(descriptor)

    message = str(raised.value)
    assert "Ambiguous REW measurement channel assignment" in message
    assert "LEFT" in message
    assert "left-first.txt" in message
    assert "left-second.txt" in message


def test_invalid_frequency_export_stops_before_pipeline_report(tmp_path):
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "left.txt").write_text(
        rew_export("LEFT", ("20 70 0",)), encoding="utf-8"
    )
    (baseline / "right.txt").write_text(
        rew_export("RIGHT", ("20 70 0",)), encoding="utf-8"
    )
    invalid_stereo = baseline / "stereo.txt"
    invalid_stereo.write_text(
        "* Measurement: L+R\n* Freq(Hz) SPL(dB) Phase(degrees)\n",
        encoding="utf-8",
    )
    brain = AcousticBrain()
    brain.pipeline.run = Mock()

    with pytest.raises(ValueError) as raised:
        brain.analyze(measurement_root=tmp_path)

    assert str(invalid_stereo) in str(raised.value)
    assert "does not contain the expected frequency" in str(raised.value)
    brain.pipeline.run.assert_not_called()
