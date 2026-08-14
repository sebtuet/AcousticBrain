from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO

from acousticbrain.report import (
    ConsoleReporter,
    DecisionFirstReportPresenter,
    OneMinuteExecutiveSummaryPresenter,
    PresentedExperimentComparison,
)
from test_decision_first_report import (
    candidate,
    evolution,
    planning,
    recommendation,
    report,
    with_comparison,
)
from test_experiment_declaration import repeat_evolution
from test_one_minute_executive_summary import add_quality


def declared_intervention(*, comparison_type="LOCAL", protocol=None, hypothesis=None):
    return replace(
        evolution("MIXED", protocol=protocol, hypothesis=hypothesis),
        before_experiment_id="exp-003",
        after_experiment_id="exp-004",
        comparison_type=comparison_type,
        experiment_kind="CONTROLLED_INTERVENTION",
        reference_experiment_code="exp-003",
        modified_variables=("RIGHT_SPEAKER_POSITION_FORWARD_50MM",),
        controlled_variables=(
            "LISTENING_POSITION",
            "MEASUREMENT_LEVEL",
            "MICROPHONE_POSITION",
            "ROOM_CONFIGURATION",
        ),
    )


def decision_for(item):
    return DecisionFirstReportPresenter().present(
        with_comparison(add_quality(report()), item)
    )


def render_summary(item):
    decision = decision_for(item)
    summary = OneMinuteExecutiveSummaryPresenter().present(decision)
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter._print_one_minute(summary)
    return decision, stream.getvalue()


def render_decision(item):
    decision = decision_for(item)
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter._print_decision_first(decision)
    return decision, stream.getvalue()


def test_controlled_intervention_without_protocol_or_hypothesis_keeps_dimensions_separate():
    decision = decision_for(declared_intervention())

    assert decision.tested_variable_declared is True
    assert decision.protocol_scope_declared is False
    assert decision.tested_conditions_declared is False


def test_declared_modified_variable_is_visible_in_one_minute_summary():
    _, output = render_summary(declared_intervention())

    assert "Intervention déclarée : enceinte droite avancée de 5 cm." in output
    assert "Référence déclarée : exp-003." in output


def test_declared_modified_variable_and_scope_are_visible_in_decision_report():
    _, output = render_decision(declared_intervention())

    assert "Déclaration expérimentale\nCONTROLLED_INTERVENTION" in output
    assert "Référence\nexp-003" in output
    assert " • RIGHT_SPEAKER_POSITION_FORWARD_50MM" in output
    assert "Protocole scientifique\nnon établi" in output
    assert "Hypothèse scientifique\nnon établie" in output


def test_declared_intervention_never_uses_undeclared_variable_wording():
    _, minute = render_summary(declared_intervention())
    _, decision = render_decision(declared_intervention())
    output = minute + decision

    assert "variable testée, ou l’absence de changement volontaire" not in output
    assert "AcousticBrain ne sait pas formellement ce qui était testé" not in output
    assert "Déclarez si la configuration devait rester inchangée" not in output


def test_declared_intervention_without_scope_is_only_partially_conclusive():
    decision, output = render_summary(declared_intervention())
    summary = OneMinuteExecutiveSummaryPresenter().present(decision)

    assert summary.conclusion[0] == "Partiellement."
    assert "La variable modifiée est connue" in summary.conclusion[1]
    assert "La comparaison mesure les effets de l’intervention déclarée." in output
    assert "Protocole scientifique : non établi." in output


def test_unknown_declaration_preserves_undeclared_variable_wording():
    _, output = render_summary(evolution("MIXED", protocol=None, hypothesis=None))

    assert "n’a pas été déclarée" in output
    assert "AcousticBrain ne sait pas formellement ce qui était testé" in output


def test_historical_manifest_without_declaration_uses_unknown_projection():
    item = evolution("MIXED", protocol=None, hypothesis=None)

    assert item.experiment_kind == "UNKNOWN"
    assert decision_for(item).tested_variable_declared is False


def test_valid_measurement_repeat_remains_a_declared_repeat():
    decision, output = render_summary(repeat_evolution())

    assert decision.tested_variable_declared is True
    assert decision.experiment_kind == "MEASUREMENT_REPEAT"
    assert "répétition" in output
    assert "variable testée" not in output


def test_declared_variable_with_protocol_and_hypothesis_declares_both_dimensions():
    item = declared_intervention(
        protocol="protocol.positioning.v1",
        hypothesis="SBIR_PLACEMENT_INTERACTION",
    )
    decision, output = render_decision(item)

    assert decision.tested_variable_declared is True
    assert decision.protocol_scope_declared is True
    assert decision.tested_conditions_declared is True
    assert "Protocole scientifique\nprotocol.positioning.v1" in output
    assert "Hypothèse scientifique\nSBIR_PLACEMENT_INTERACTION" in output


def test_local_and_cumulative_comparisons_render_the_same_declaration():
    local = declared_intervention(comparison_type="LOCAL")
    cumulative = declared_intervention(comparison_type="CUMULATIVE")
    value = report()
    value.experiment_comparison = PresentedExperimentComparison(
        chronology=("exp-003", "exp-004"),
        local_comparisons=(local,),
        cumulative_comparisons=(cumulative,),
        detailed_traceability=False,
    )
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter().print(value)
    output = stream.getvalue()

    assert output.count("Déclaration expérimentale : CONTROLLED_INTERVENTION") == 2
    assert output.count("RIGHT_SPEAKER_POSITION_FORWARD_50MM") >= 2


def test_exp004_analogue_preserves_not_established_causality():
    decision, output = render_decision(declared_intervention())

    assert decision.causality_status == "NOT_ESTABLISHED"
    assert "Causalité : Non établi (NOT_ESTABLISHED)." in output


def test_presentation_does_not_change_scores_recommendations_rankings_or_eligibility():
    item = declared_intervention()
    value = with_comparison(add_quality(report()), item)
    value.recommendations = [recommendation("CHECK_STEREO_PLACEMENT")]
    value.experiment_planning = planning(candidate({"speaker_id": "RIGHT"}))
    recommendations_before = tuple(value.recommendations)
    planning_before = value.experiment_planning
    eligibility_before = item.eligibility
    outcome_before = item.acoustic_outcome

    DecisionFirstReportPresenter().present(value)

    assert tuple(value.recommendations) == recommendations_before
    assert value.experiment_planning == planning_before
    assert item.eligibility == eligibility_before == "COMPARABLE"
    assert item.acoustic_outcome == outcome_before == "MIXED"
