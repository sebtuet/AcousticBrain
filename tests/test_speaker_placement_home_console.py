from dataclasses import dataclass
from types import SimpleNamespace

import main as acousticbrain_main

from acousticbrain.report import (
    PresentedActionOrientedPositioning,
    Report,
    SpeakerPlacementHomeConsoleReporter,
)


@dataclass(frozen=True)
class _Plan:
    plan_id: str
    objective: str
    display_objective: str | None = None


class _PositioningPresenter:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def present(self, report):
        self.calls.append(report)
        return self.value


class _Brain:
    def __init__(self, report):
        self.report = report
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return self.report


def _positioning(*, status="MULTIPLE_PLAUSIBLE_PATHS"):
    available = status == "ACTION_AVAILABLE"
    return PresentedActionOrientedPositioning(
        status=status,
        situation="Les observations existantes ne départagent pas une cause.",
        certainty="Certitude limitée.",
        measured_facts=("Un écart gauche/droite est observé.",),
        possible_explanations=(),
        action=(
            "Tester un déplacement réversible déjà proposé."
            if available else
            "Plusieurs explications restent également plausibles."
        ),
        target="l’enceinte gauche" if available else None,
        direction="vers l’avant" if available else None,
        amplitude="10 cm" if available else None,
        unchanged_items=(),
        required_measurements=(),
        comparison_criteria=(),
        previous_result=None,
        missing_information=("Une piste unique déjà départagée.",) if not available else (),
        limitations=("La causalité n’est pas établie.",),
        causality_status="NOT_ESTABLISHED",
        source_codes=("existing.source",),
    )


def test_blocked_homepage_routes_to_existing_guided_status_without_a_move(capsys, tmp_path):
    report = SimpleNamespace(
        evidence_acquisition_plans=SimpleNamespace(
            recommended_plan=_Plan(
                plan_id="EVIDENCE_PLAN_EXISTING",
                objective="Acquire controlled evidence.",
                display_objective="Vérifier séparément les deux canaux.",
            )
        ),
        loudspeaker_positioning_experiment=None,
    )
    presenter = _PositioningPresenter(_positioning())

    SpeakerPlacementHomeConsoleReporter(
        measurements_root=tmp_path / "measurements",
        positioning_presenter=presenter,
    ).print(report)

    output = capsys.readouterr().out
    assert "PLACEMENT DES ENCEINTES" in output
    assert "Aucun déplacement unique" in output
    assert "Plan : EVIDENCE_PLAN_EXISTING" in output
    assert "python main.py" in output
    assert "--start-placement" in output
    assert "Direction :" not in output
    assert "Causality status: NOT_ESTABLISHED" in output
    assert presenter.calls == [report]


def test_available_homepage_exposes_only_existing_reversible_test_and_declaration(capsys, tmp_path):
    report = SimpleNamespace(
        evidence_acquisition_plans=None,
        loudspeaker_positioning_experiment=SimpleNamespace(
            proposal=SimpleNamespace(proposal_id="existing-proposal-001")
        ),
    )

    SpeakerPlacementHomeConsoleReporter(
        measurements_root=tmp_path / "measurements",
        positioning_presenter=_PositioningPresenter(
            _positioning(status="ACTION_AVAILABLE")
        ),
    ).print(report)

    output = capsys.readouterr().out
    assert "l’enceinte gauche" in output
    assert "Direction : vers l’avant" in output
    assert "Amplitude : 10 cm" in output
    assert "--accept-positioning-proposal existing-proposal-001" in output
    assert "--positioning-experiment-id <NOUVEL_EXPERIMENT_ID>" in output
    assert "ne l’exécute pas" in output
    assert "correction établie" in output
    assert "Causality status: NOT_ESTABLISHED" in output


def test_homepage_does_not_mutate_the_existing_report(capsys, tmp_path):
    plan = _Plan("EVIDENCE_PLAN_EXISTING", "Acquire controlled evidence.")
    report = SimpleNamespace(
        evidence_acquisition_plans=SimpleNamespace(recommended_plan=plan),
        loudspeaker_positioning_experiment=None,
    )
    before = repr(report)

    SpeakerPlacementHomeConsoleReporter(
        measurements_root=tmp_path,
        positioning_presenter=_PositioningPresenter(_positioning()),
    ).print(report)

    capsys.readouterr()
    assert repr(report) == before


def test_homepage_preserves_repeated_capture_without_requesting_a_new_test(
    capsys, tmp_path,
):
    repeated = SimpleNamespace(
        experiment_id="test-canaux-001",
        state="READY",
        available_channels=("LEFT", "RIGHT"),
        source_evidence_acquisition_plan_id="CHANNEL_PLAN",
        preserved_plan_objective="Acquire repeated evidence.",
    )
    report = SimpleNamespace(
        evidence_acquisition_plans=SimpleNamespace(
            recommended_plan=_Plan("EVIDENCE_PLAN_EXISTING", "Acquire evidence.")
        ),
        loudspeaker_positioning_experiment=None,
        experiments_discovered=SimpleNamespace(experiments=(repeated,)),
    )

    SpeakerPlacementHomeConsoleReporter(
        measurements_root=tmp_path,
        positioning_presenter=_PositioningPresenter(_positioning()),
    ).print(report)

    output = capsys.readouterr().out
    assert "test-canaux-001" in output
    assert "Aucune nouvelle mesure n’est demandée" in output
    assert "--start-placement" not in output
    assert "verdict de comparaison n’est encore produit" in output


def test_default_main_cli_uses_the_placement_homepage(capsys, tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    report = Report(project_name="fixture")
    report.evidence_acquisition_plans = SimpleNamespace(
        recommended_plan=_Plan("EVIDENCE_PLAN_EXISTING", "Acquire evidence.")
    )

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=_Brain(report),
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "ACOUSTICBRAIN — PLACEMENT DES ENCEINTES" in output
    assert "ACOUSTICBRAIN REPORT" not in output
    assert "--start-placement" in output
