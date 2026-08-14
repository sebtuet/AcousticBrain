from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

import pytest

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import EvidenceLevel, RecommendationStatus
from acousticbrain.report import (
    ConsoleReporter,
    DecisionFirstReportPresenter,
    OneMinuteExecutiveSummaryPresenter,
)
from test_decision_first_report import (
    candidate,
    evolution,
    planning,
    proposal,
    recommendation,
    report,
    with_comparison,
)


HEADINGS = (
    "Situation",
    "Verdict",
    "Puis-je conclure ?",
    "Ce que je fais maintenant",
    "Pourquoi",
    "Confiance",
)


def add_quality(value, severity="LOW"):
    value.diagnostics.append(Diagnostic(
        title="Qualité des mesures",
        severity=severity,
        confidence=90,
        evidence_level=EvidenceLevel.CALCULATED,
        message="Statut technique synthétique.",
    ))
    return value


def summary(value):
    decision = DecisionFirstReportPresenter().present(value)
    return OneMinuteExecutiveSummaryPresenter().present(decision)


def rendered(value):
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter().print(value)
    return stream.getvalue()


def rendered_summary(value):
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter._print_one_minute(summary(value))
    return stream.getvalue()


def section(output):
    return output.split("EN UNE MINUTE\n", 1)[1].split(
        "\nDÉCISION ACOUSTIQUE", 1
    )[0]


def useful_lines(output):
    return [line for line in output.splitlines() if line.strip()]


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        ("IMPROVED", "amélioration mesurable"),
        ("DEGRADED", "dégradation mesurable"),
        ("MIXED", "Certains indicateurs s’améliorent"),
        ("UNCHANGED", "Aucun changement acoustique significatif"),
        ("INCONCLUSIVE", "ne permettent pas de conclure"),
    ),
)
def test_translates_every_comparable_verdict(status, expected):
    value = with_comparison(add_quality(report()), evolution(status))

    assert expected in " ".join(summary(value).verdict)
    assert len(useful_lines(rendered_summary(value))) <= 24


def test_not_comparable_and_absent_comparisons_are_distinct():
    unavailable = with_comparison(
        add_quality(report()),
        evolution("IMPROVED", eligibility="NOT_COMPARABLE"),
    )

    assert summary(unavailable).situation == (
        "Comparaison indisponible : les expériences ne sont pas comparables.",
    )
    assert "ne peut pas être comparée" in " ".join(summary(unavailable).verdict)
    assert summary(add_quality(report())).verdict == (
        "Aucune comparaison avec une expérience précédente n’est disponible.",
    )
    assert len(useful_lines(rendered_summary(unavailable))) <= 24
    assert len(useful_lines(rendered_summary(add_quality(report())))) <= 24


def test_section_precedes_pr041_and_has_exactly_the_six_required_blocks():
    output = rendered(with_comparison(add_quality(report()), evolution("MIXED")))
    page = section(output)

    assert output.index("EN UNE MINUTE") < output.index("DÉCISION ACOUSTIQUE")
    positions = [page.index(item) for item in HEADINGS]
    assert positions == sorted(positions)
    assert [line for line in page.splitlines() if line in HEADINGS] == list(HEADINGS)


def test_precise_eligible_action_reuses_target_direction_distance_and_measurements():
    value = with_comparison(add_quality(report()), evolution("IMPROVED"))
    value.experiment_planning = planning(candidate({
        "speaker_id": "LEFT",
        "movement_direction": "vers l’avant",
        "proposed_displacement_m": 0.10,
    }))

    actions = summary(value).actions

    assert actions == (
        "Modifiez uniquement l’enceinte gauche — 10 cm vers l’avant.",
        "Conservez la position du microphone et le volume de mesure inchangés.",
        "Reprenez L, R, L+R.",
    )


def test_unique_planned_action_remains_preferred():
    value = add_quality(report())
    item = proposal()
    value.controlled_reflection_verification_planning = SimpleNamespace(
        proposals=(item,),
    )
    value.controlled_reflection_experiment_declarations = (
        SimpleNamespace(status="PLANNED", proposal_id=item.proposal_id),
    )
    value.experiment_planning = planning(candidate({"speaker_id": "LEFT"}))

    assert "masquage temporaire" in summary(value).actions[0]


def test_missing_direction_or_distance_is_never_invented():
    value = add_quality(report())
    value.experiment_planning = planning(candidate({"speaker_id": "RIGHT"}))
    text = " ".join(summary(value).actions)

    assert "enceinte droite" in text
    assert "Direction" not in text
    assert "cm" not in text
    assert "vers l’avant" not in text


def test_tied_deferred_and_absent_actions_are_honest():
    tied = add_quality(report())
    tied.recommendations = [
        recommendation("CHECK_STEREO_PLACEMENT"),
        recommendation("INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"),
    ]
    deferred = add_quality(report())
    deferred.recommendations = [recommendation(
        "VERIFY_SPEAKER_ROOM_ASYMMETRY",
        status=RecommendationStatus.DEFERRED,
    )]
    deferred.causal_discrimination = SimpleNamespace(
        discrimination_decisions=(SimpleNamespace(status="DEFERRED"),)
    )
    absent = add_quality(report())

    assert "Aucune action fiable" in summary(tied).actions[0]
    assert "également prioritaires" in " ".join(summary(tied).reasons)
    assert any("reprendre l’investigation" in item for item in summary(deferred).actions)
    assert summary(absent).actions == (
        "Aucune action fiable ne peut être recommandée actuellement.",
    )


@pytest.mark.parametrize(
    ("protocol", "hypothesis"),
    ((None, "HYPOTHESIS"), ("protocol.test.v1", None), (None, None)),
)
def test_missing_test_declarations_prevent_a_conclusion_without_inventing_a_move(
    protocol,
    hypothesis,
):
    value = with_comparison(
        add_quality(report()),
        evolution("MIXED", protocol=protocol, hypothesis=hypothesis),
    )
    page = rendered_summary(value).lower()

    assert summary(value).conclusion[0] == "Non."
    assert "ne sait pas formellement" in summary(value).conclusion[1]
    assert "déplacement a eu lieu" not in page
    assert "nouvelle position" not in page


@pytest.mark.parametrize(
    ("severity", "expected"),
    (
        ("LOW", "Mesures : exploitables."),
        ("MEDIUM", "Mesures : exploitables avec réserves."),
        ("HIGH", "Mesures : insuffisantes."),
    ),
)
def test_translates_existing_measurement_availability(severity, expected):
    value = with_comparison(add_quality(report(), severity), evolution("IMPROVED"))

    assert summary(value).confidence[0] == expected


def test_mixed_never_becomes_a_global_improvement():
    value = with_comparison(add_quality(report()), evolution("MIXED"))
    page = rendered_summary(value).lower()

    for forbidden in (
        "la nouvelle position est meilleure",
        "amélioration globale",
        "position optimale",
        "amélioration garantie",
        "cause confirmée",
    ):
        assert forbidden not in page


def test_action_and_reason_limits_hold_in_complex_case():
    value = with_comparison(
        add_quality(report()),
        evolution("MIXED", protocol=None, hypothesis=None),
    )
    value.recommendations = [
        recommendation("CHECK_STEREO_PLACEMENT"),
        recommendation("INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"),
    ]
    value.causal_discrimination = SimpleNamespace(
        discrimination_decisions=(SimpleNamespace(status="DEFERRED"),)
    )

    result = summary(value)

    assert len(result.actions) <= 3
    assert len(result.reasons) <= 2
    assert len(useful_lines(rendered_summary(value))) <= 24


def test_nominal_summary_has_at_most_twenty_useful_lines():
    value = with_comparison(add_quality(report()), evolution("IMPROVED"))
    value.experiment_planning = planning(candidate({"speaker_id": "LEFT"}))

    assert len(useful_lines(rendered_summary(value))) <= 20


def test_rendering_is_deterministic_and_order_is_stable():
    value = with_comparison(add_quality(report()), evolution("UNCHANGED"))

    assert rendered(value) == rendered(value)
    lines = useful_lines(rendered(value))
    assert lines.index("EN UNE MINUTE") < lines.index("DÉCISION ACOUSTIQUE")
    assert lines.index("DÉCISION ACOUSTIQUE") < lines.index(
        "PROCHAINE ÉTAPE DE POSITIONNEMENT"
    )


def test_pr041_and_the_complete_technical_report_remain_after_the_summary():
    value = with_comparison(add_quality(report()), evolution("IMPROVED"))
    value.room_properties = SimpleNamespace(
        volume=80.0,
        floor_area=30.0,
        schroeder_frequency=120.0,
    )
    output = rendered(value)

    assert "DÉCISION ACOUSTIQUE" in output
    assert "PROCHAINE ÉTAPE DE POSITIONNEMENT" in output
    assert "Salle" in output
    assert "Volume : 80.00 m³" in output


def test_exp006_analogue_stays_honest_and_concise():
    value = with_comparison(
        add_quality(report()),
        evolution("MIXED", protocol=None, hypothesis=None),
    )
    value.experiment_planning = planning(None, status="NO_ELIGIBLE_CANDIDATE")
    value.recommendations = [
        recommendation("CHECK_STEREO_PLACEMENT"),
        recommendation("INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"),
    ]
    value.causal_discrimination = SimpleNamespace(
        discrimination_decisions=(SimpleNamespace(status="DEFERRED"),)
    )
    page = rendered_summary(value)

    assert "Comparaison : exp-005 → exp-006." in page
    assert "Aucun verdict global simple" in page
    assert "AcousticBrain ne sait pas formellement ce qui était testé" in page
    assert "Aucune action fiable" in page
    assert "Déclarez si la configuration devait rester inchangée" in page
    assert "Mesures : exploitables." in page
    assert "Verdict : incertain." in page
    assert len(useful_lines(page)) <= 24
