from pathlib import Path
from types import SimpleNamespace

from acousticbrain.report import (
    CausalDiscriminationPresenter,
    ConsoleReporter,
    Report,
)

from test_causal_discrimination import (
    analyze,
    baseline,
    remeasurement,
    speaker_swap,
)


ROOT = Path(__file__).resolve().parents[1]


def presented_analysis():
    analysis = analyze(
        baseline(),
        remeasurement(),
        speaker_swap("ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"),
    )
    context = SimpleNamespace(causal_discrimination_analysis=analysis)
    return analysis, CausalDiscriminationPresenter().present(context)


def test_presenter_is_a_pure_projection():
    analysis, first = presented_analysis()
    snapshot = repr(analysis)

    second = CausalDiscriminationPresenter().present(
        SimpleNamespace(causal_discrimination_analysis=analysis)
    )

    assert first == second
    assert repr(analysis) == snapshot
    assert first.recommended_next_protocol == "STEP_3_SIGNAL_CHAIN_SWAP"
    assert {item.trajectory_code for item in first.contradicted_trajectories} == {
        "ANOMALY_REMAINS_WITH_ROOM_SIDE"
    }


def test_causal_discrimination_report_matches_golden(capsys):
    _, presented = presented_analysis()
    report = Report(project_name="causal-fixture")
    report.causal_discrimination = presented

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/causal_discrimination_report.txt").read_text()
    assert capsys.readouterr().out == expected
