from pathlib import Path
from types import SimpleNamespace

from acousticbrain.analysis import AcousticReasoningEngine, ExperimentPlanner
from acousticbrain.report import (
    ConsoleReporter,
    ExperimentPlanningPresenter,
    Report,
)


ROOT = Path(__file__).resolve().parents[1]


def test_presenter_is_a_pure_bounded_projection():
    analysis = ExperimentPlanner().plan(AcousticReasoningEngine().analyze())
    context = SimpleNamespace(experiment_planning_analysis=analysis)

    presented = ExperimentPlanningPresenter().present(context)

    assert presented.recommended_candidate.candidate_id == (
        analysis.plan.recommended_candidate.candidate_id
    )
    assert len(presented.alternatives) <= 3
    assert len(presented.all_candidates) == 4
    assert analysis.plan.recommended_candidate.informative_value == 26.33


def test_planning_console_projection_matches_its_golden(capsys):
    analysis = ExperimentPlanner().plan(AcousticReasoningEngine().analyze())
    context = SimpleNamespace(experiment_planning_analysis=analysis)
    report = Report(project_name="Studio")
    report.experiment_planning = ExperimentPlanningPresenter().present(context)

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/experiment_planning_report.txt").read_text()
    assert capsys.readouterr().out == expected + "\n"
