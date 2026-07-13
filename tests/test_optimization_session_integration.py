from acousticbrain.application import OptimizationSessionService
from acousticbrain.brain import AcousticBrain
from acousticbrain.models import ExperimentProtocol

from test_golden_report import reference_project


def test_pipeline_records_states_only_with_an_explicit_session_context():
    brain = AcousticBrain()
    project = reference_project()

    historical_report = brain.analyze(project)

    service = OptimizationSessionService()
    session_context = service.create("pipeline-session")
    session_report = brain.analyze(project, session_context=session_context)

    assert historical_report.optimization_session is None
    assert session_report.optimization_session.session_id == "pipeline-session"
    assert len(session_context.session.states) == 1
    assert session_context.session.iterations == []
    assert session_report.optimization_session.completed_experiments == 0

    hypothesis_code = session_context.session.current_state.hypotheses[0].code
    service.start_iteration(
        session_context,
        ExperimentProtocol(
            experiment_id="integration-experiment",
            hypothesis_code=hypothesis_code,
            action_code="EXPLICIT_TEST_ACTION",
            label="Expérience d’intégration explicitement choisie",
            fact_codes=(),
        ),
    )
    completed_report = brain.analyze(project, session_context=session_context)

    assert len(session_context.session.states) == 2
    assert session_context.session.iterations[0].comparison is not None
    assert completed_report.optimization_session.completed_experiments == 1
