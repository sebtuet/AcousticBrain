from pathlib import Path

from acousticbrain.report import (
    ConsoleReporter,
    PresentedOptimizationSession,
    PresentedSessionIteration,
    Report,
)


ROOT = Path(__file__).resolve().parents[1]


def test_session_console_projection_matches_its_golden(capsys):
    report = Report(project_name="Studio")
    report.optimization_session = PresentedOptimizationSession(
        session_id="session-1",
        current_iteration=1,
        completed_experiments=1,
        open_hypotheses=("SBIR_PLACEMENT_INTERACTION",),
        reinforced_hypotheses=("SBIR_PLACEMENT_INTERACTION",),
        refuted_hypotheses=(),
        global_gain=10.0,
        main_improvements=("global.domain.sbir.score",),
        main_degradations=(),
        pending_experiment=None,
        iterations=(
            PresentedSessionIteration(
                number=1,
                hypothesis_code="SBIR_PLACEMENT_INTERACTION",
                experiment_label="Déplacement temporaire des enceintes",
                before_state_id="session-1:state:1",
                after_state_id="session-1:state:2",
                improved_fact_codes=("global.domain.sbir.score",),
                degraded_fact_codes=(),
                hypothesis_result="REINFORCED",
            ),
        ),
        trace_chains=(),
    )

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/session_report.txt").read_text()
    assert capsys.readouterr().out == expected
