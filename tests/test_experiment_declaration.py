import json
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO

import pytest

from acousticbrain.application import (
    ExperimentDeclarationService,
    ExperimentDiscoveryService,
)
from acousticbrain.commands.declare_experiment import main as declare_main
from acousticbrain.models import ExperimentDeclaration, ExperimentKind
from acousticbrain.persistence import MeasurementRepository
from acousticbrain.report import (
    ConsoleReporter,
    DecisionFirstReportPresenter,
    OneMinuteExecutiveSummaryPresenter,
    ExperimentComparisonPresenter,
)
from manifest_test_data import future_manifest_extension
from test_automatic_experiment_comparison import comparison, descriptor
from test_decision_first_report import (
    evolution,
    recommendation,
    report,
    with_comparison,
)
from test_experiment_discovery import complete_experiment
from test_one_minute_executive_summary import add_quality


REPEAT_CONTROLS = ExperimentDeclarationService.REPEAT_CONTROLLED_VARIABLES


def experiment_root(tmp_path):
    complete_experiment(tmp_path / "exp-005")
    complete_experiment(tmp_path / "exp-006")
    return tmp_path


def repeat_evolution(status="MIXED"):
    return replace(
        evolution(status, protocol=None, hypothesis=None),
        experiment_kind="MEASUREMENT_REPEAT",
        reference_experiment_code="exp-005",
        modified_variables=("MEASUREMENT_ACQUISITION",),
        controlled_variables=REPEAT_CONTROLS,
        declaration_user_note="Répétition sans modification volontaire.",
        declaration_field_provenance=tuple(
            (field, "USER_CLI") for field in (
                "experiment_kind",
                "reference_experiment_code",
                "modified_variables",
                "controlled_variables",
                "user_note",
            )
        ),
    )


def repeat_report(status="MIXED"):
    value = with_comparison(add_quality(report()), repeat_evolution(status))
    value.recommendations = [
        recommendation("CHECK_STEREO_PLACEMENT"),
        recommendation("INVESTIGATE_DOMINANT_EARLY_REFLECTIONS"),
    ]
    return value


def render_decision(value):
    decision = DecisionFirstReportPresenter().present(value)
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter._print_decision_first(decision)
    return decision, stream.getvalue()


def render_summary(value):
    decision = DecisionFirstReportPresenter().present(value)
    summary = OneMinuteExecutiveSummaryPresenter().present(decision)
    stream = StringIO()
    with redirect_stdout(stream):
        ConsoleReporter._print_one_minute(summary)
    return summary, stream.getvalue()


def test_historical_experiment_without_declaration_is_unknown(tmp_path):
    complete_experiment(tmp_path / "exp-001")

    descriptor = ExperimentDiscoveryService().discover(tmp_path)[0]

    assert descriptor.experiment_declaration.experiment_kind is ExperimentKind.UNKNOWN
    persisted = json.loads((tmp_path / "exp-001/manifest.json").read_text())
    assert "experiment_declaration" not in persisted


def test_controlled_intervention_is_persisted_with_field_provenance(tmp_path):
    root = experiment_root(tmp_path)

    declaration = ExperimentDeclarationService().declare(
        root,
        experiment_code="exp-006",
        experiment_kind="CONTROLLED_INTERVENTION",
        reference_experiment_code="exp-005",
        modified_variables=("LOUDSPEAKER_POSITION",),
        controlled_variables=("MICROPHONE_POSITION", "MEASUREMENT_LEVEL"),
        user_note="Déplacement temporaire documenté.",
    )

    assert declaration.experiment_kind is ExperimentKind.CONTROLLED_INTERVENTION
    assert declaration.modified_variables == ("LOUDSPEAKER_POSITION",)
    assert set(dict(declaration.field_provenance)) == {
        "experiment_kind",
        "reference_experiment_code",
        "modified_variables",
        "controlled_variables",
        "user_note",
    }


def test_measurement_repeat_defaults_only_acquisition_and_explicit_controls(tmp_path):
    root = experiment_root(tmp_path)

    declaration = ExperimentDeclarationService().declare(
        root,
        experiment_code="exp-006",
        experiment_kind="MEASUREMENT_REPEAT",
        reference_experiment_code="exp-005",
        user_note="Même configuration, nouvelle acquisition.",
    )

    assert declaration.modified_variables == ("MEASUREMENT_ACQUISITION",)
    assert declaration.controlled_variables == REPEAT_CONTROLS
    assert "LOUDSPEAKER_POSITION" in declaration.controlled_variables
    assert "LISTENING_POSITION" in declaration.controlled_variables


def test_repeat_with_missing_reference_is_rejected(tmp_path):
    complete_experiment(tmp_path / "exp-006")

    with pytest.raises(ValueError, match="Unknown reference experiment"):
        ExperimentDeclarationService().declare(
            tmp_path,
            experiment_code="exp-006",
            experiment_kind="MEASUREMENT_REPEAT",
            reference_experiment_code="exp-005",
        )


def test_persistence_is_atomic_idempotent_and_read_back_deterministically(tmp_path):
    root = experiment_root(tmp_path)
    ExperimentDiscoveryService().discover(root)
    extension = future_manifest_extension()
    existing = MeasurementRepository.load_manifest(root / "exp-006")
    existing["future_extension"] = extension
    MeasurementRepository.save_manifest(root / "exp-006", existing)
    service = ExperimentDeclarationService()
    arguments = dict(
        experiment_code="exp-006",
        experiment_kind="MEASUREMENT_REPEAT",
        reference_experiment_code="exp-005",
        controlled_variables=tuple(reversed(REPEAT_CONTROLS)),
        user_note="Contrôle de répétition.",
    )
    service.declare(root, **arguments)
    manifest = root / "exp-006/manifest.json"
    first_content = manifest.read_text()
    first_timestamp = manifest.stat().st_mtime_ns

    service.declare(root, **arguments)
    descriptor = ExperimentDiscoveryService().discover(root)[1]

    assert manifest.stat().st_mtime_ns == first_timestamp
    assert manifest.read_text() == first_content
    assert descriptor.parent_experiment_ids == ("exp-005",)
    assert descriptor.experiment_declaration.controlled_variables == REPEAT_CONTROLS
    persisted = MeasurementRepository.load_manifest(root / "exp-006")
    assert persisted["future_extension"] == extension
    assert not (root / "exp-006/manifest.json.tmp").exists()


def test_declaration_does_not_modify_measurement_files(tmp_path):
    root = experiment_root(tmp_path)
    files = tuple(sorted((root / "exp-006/measurements").glob("*.txt")))
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in files}

    ExperimentDeclarationService().declare(
        root,
        experiment_code="exp-006",
        experiment_kind="MEASUREMENT_REPEAT",
        reference_experiment_code="exp-005",
    )

    assert {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in files} == before


def test_cli_declares_exp006_without_editing_measurements(tmp_path, capsys):
    root = experiment_root(tmp_path)

    declare_main([
        str(root),
        "exp-006",
        "--kind", "MEASUREMENT_REPEAT",
        "--reference", "exp-005",
        "--note", "Répétition à configuration inchangée.",
    ])

    assert "Declared exp-006: MEASUREMENT_REPEAT" in capsys.readouterr().out
    value = json.loads((root / "exp-006/manifest.json").read_text())
    assert value["experiment_declaration"]["reference_experiment_code"] == "exp-005"


def test_declaration_propagates_through_comparison_without_changing_outcome(monkeypatch):
    declaration = ExperimentDeclaration(
        schema_version=1,
        experiment_kind=ExperimentKind.MEASUREMENT_REPEAT,
        reference_experiment_code="exp-005",
        modified_variables=("MEASUREMENT_ACQUISITION",),
        controlled_variables=REPEAT_CONTROLS,
        user_note="Contrôle.",
        field_provenance=tuple(
            (field, "USER_CLI") for field in (
                "experiment_kind",
                "reference_experiment_code",
                "modified_variables",
                "controlled_variables",
                "user_note",
            )
        ),
    )
    descriptors = (
        descriptor("exp-005", baseline=True, hypothesis=None),
        replace(
            descriptor("exp-006", parents=("exp-005",), hypothesis=None),
            experiment_declaration=declaration,
        ),
    )

    analysis = comparison(
        monkeypatch,
        descriptors,
        {"exp-005": 70.0, "exp-006": 75.0},
    )
    control = comparison(
        monkeypatch,
        (
            descriptors[0],
            replace(descriptors[1], experiment_declaration=ExperimentDeclaration.unknown()),
        ),
        {"exp-005": 70.0, "exp-006": 75.0},
    ).sequence.local_comparisons[0]
    result = analysis.sequence.local_comparisons[0]
    presented = ExperimentComparisonPresenter().present(
        type("Context", (), {"experiment_comparison_analysis": analysis})()
    ).local_comparisons[0]

    assert result.acoustic_outcome == control.acoustic_outcome
    assert result.outcome == control.outcome
    assert result.experiment_kind is ExperimentKind.MEASUREMENT_REPEAT
    assert presented.experiment_kind == "MEASUREMENT_REPEAT"
    assert presented.controlled_variables == REPEAT_CONTROLS


def test_pr041_renders_repeat_without_claiming_a_position_change():
    decision, output = render_decision(repeat_report())

    assert "Selon la déclaration utilisateur" in output
    assert "aucune modification volontaire de la configuration n’était prévue" in output
    assert "Certaines mesures diffèrent" in output
    assert "Ne déplacez pas encore les enceintes" in output
    assert decision.causality_status == "NOT_ESTABLISHED"
    assert "nouvelle position" not in output.lower()
    assert "amélioration de placement" not in output.lower()


def test_pr042_mixed_repeat_is_partial_and_never_claims_good_repeatability():
    summary, output = render_summary(repeat_report())

    assert summary.conclusion[0] == "Partiellement."
    assert "répétition déclarée du protocole" in summary.conclusion[1]
    assert "la déclaration utilisateur indique" in output
    assert "AcousticBrain ne peut donc pas attribuer" in output
    forbidden = (
        "la nouvelle position est meilleure",
        "amélioration de placement",
        "bonne répétabilité",
        "répétabilité satisfaisante",
        "cause confirmée",
    )
    assert not any(value in output.lower() for value in forbidden)


def test_partial_repeat_declaration_does_not_invent_controlled_variables():
    item = replace(
        repeat_evolution(),
        controlled_variables=("MICROPHONE_POSITION",),
    )
    value = with_comparison(add_quality(report()), item)

    _, output = render_summary(value)

    assert "déclarée par l’utilisateur comme une répétition" in output
    assert "le microphone" in output
    assert "le volume" not in output
    assert "les paramètres REW" not in output
    assert "aucune modification volontaire de la configuration n’était prévue" not in output


def test_repeat_rendering_attributes_configuration_claims_to_the_user():
    _, output = render_summary(repeat_report())

    assert "Selon la déclaration utilisateur" in output
    assert "La déclaration utilisateur n’indique" in output
    assert "configuration déclarée inchangée" not in output.lower()
    assert "configuration inchangée" not in output.lower()


def test_repeat_rendering_is_deterministic():
    value = repeat_report()

    assert render_decision(value)[1] == render_decision(value)[1]
    assert render_summary(value)[1] == render_summary(value)[1]
