from acousticbrain.brain import AcousticBrain

from test_experiment_discovery import rew_measurement


def test_analyze_accepts_measurement_root_without_explicit_session(tmp_path):
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "free-name.txt").write_text(
        rew_measurement("LEFT"),
        encoding="utf-8",
    )

    report = AcousticBrain().analyze(measurement_root=tmp_path)

    assert report.experiments_discovered is not None
    assert report.experiments_discovered.experiments[0].state == "INCOMPLETE"
    assert report.optimization_session is None
    assert report.experiment_planning is None
