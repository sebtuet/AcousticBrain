from pathlib import Path

from acousticbrain.brain import AcousticBrain


ROOT = Path(__file__).resolve().parents[1]


def test_explicit_mode_analyzes_discovered_experiments_without_business_history():
    report = AcousticBrain().analyze(
        measurement_root=ROOT / "measurements",
        compare_experiments=True,
        detailed_comparison_traceability=True,
    )

    assert report.experiment_comparison.chronology == ("baseline", "exp-001")
    assert len(report.experiment_comparison.local_comparisons) == 1
    assert len(report.experiment_comparison.cumulative_comparisons) == 1
    assert report.experiment_comparison.local_comparisons[0].trace_id
    assert report.optimization_session is None


def test_comparison_is_absent_when_explicit_mode_is_disabled():
    report = AcousticBrain().analyze(measurement_root=ROOT / "measurements")

    assert report.experiment_comparison is None
    assert report.optimization_session is None
