from types import SimpleNamespace

import pytest

from acousticbrain.report import (
    PlacementComparisonSelectionConsoleReporter,
    PlacementComparisonSelectionPresenter,
    PresentedPlacementComparisonSelection,
    Report,
)


def comparison(comparison_type, *, trace_id=None, eligibility="COMPARABLE"):
    return SimpleNamespace(
        trace_id=trace_id or f"trace:comparison:{comparison_type.lower()}:a:b",
        before_experiment_id="position-a",
        after_experiment_id="position-b",
        comparison_type=comparison_type,
        eligibility=eligibility,
    )


def report(*, local=(), cumulative=()):
    value = Report(project_name="selection-fixture")
    value.experiment_comparison = SimpleNamespace(
        local_comparisons=local,
        cumulative_comparisons=cumulative,
    )
    return value


def test_resolves_one_exact_trace_identifier_without_preferring_comparison_type():
    local = comparison("LOCAL")
    cumulative = comparison("CUMULATIVE")

    value = PlacementComparisonSelectionPresenter().present(
        report(local=(local,), cumulative=(cumulative,)), cumulative.trace_id
    )

    assert value.comparison_id == cumulative.trace_id
    assert value.reference_experiment_id == "position-a"
    assert value.target_experiment_id == "position-b"
    assert value.comparison_type == "CUMULATIVE"
    assert value.eligibility == "COMPARABLE"
    assert value.causality_status == "NOT_ESTABLISHED"


def test_unknown_trace_identifier_is_rejected_without_fallback():
    with pytest.raises(ValueError, match="COMPARISON_UNKNOWN: trace:missing"):
        PlacementComparisonSelectionPresenter().present(
            report(local=(comparison("LOCAL"),)), "trace:missing"
        )


def test_duplicate_trace_identifier_is_rejected_as_ambiguous():
    duplicate = "trace:comparison:duplicate"

    with pytest.raises(ValueError, match="COMPARISON_AMBIGUOUS"):
        PlacementComparisonSelectionPresenter().present(
            report(
                local=(comparison("LOCAL", trace_id=duplicate),),
                cumulative=(comparison("CUMULATIVE", trace_id=duplicate),),
            ),
            duplicate,
        )


def test_exact_resolution_is_independent_of_collection_order():
    first = comparison("LOCAL", trace_id="trace:comparison:local:a:b")
    second = comparison("CUMULATIVE", trace_id="trace:comparison:cumulative:a:b")
    presenter = PlacementComparisonSelectionPresenter()

    original = presenter.present(
        report(local=(first,), cumulative=(second,)), second.trace_id
    )
    reordered = presenter.present(
        report(local=(first,), cumulative=tuple(reversed((second,)))), second.trace_id
    )

    assert reordered == original


def test_console_renders_a_concise_non_causal_selection(capsys):
    value = PlacementComparisonSelectionPresenter().present(
        report(local=(comparison("LOCAL"),)), "trace:comparison:local:a:b"
    )
    rendered = report(local=(comparison("LOCAL"),))
    rendered.placement_comparison_selection = value

    PlacementComparisonSelectionConsoleReporter().print(rendered)

    output = capsys.readouterr().out
    assert "COMPARAISON SÉLECTIONNÉE" in output
    assert "Référence : position-a" in output
    assert "Cible : position-b" in output
    assert "BETTER" not in output
    assert "causé" not in output
    assert "Causality status: NOT_ESTABLISHED" in output


def test_console_explains_a_blocked_comparison_without_internal_reason_codes(capsys):
    item = comparison("LOCAL", eligibility="NOT_COMPARABLE")
    rendered = report(local=(item,))
    rendered.placement_comparison_selection = (
        PlacementComparisonSelectionPresenter().present(rendered, item.trace_id)
    )

    PlacementComparisonSelectionConsoleReporter().print(rendered)

    output = capsys.readouterr().out
    assert "COMPARAISON IMPOSSIBLE" in output
    assert "reason" not in output.lower()
    assert "Causality status: NOT_ESTABLISHED" in output


def test_console_explains_a_repeatability_block_without_reason_codes(capsys):
    rendered = Report(project_name="selection-fixture")
    rendered.placement_comparison_selection = PresentedPlacementComparisonSelection(
        comparison_id="trace:comparison:local:a:b",
        reference_experiment_id="position-a",
        target_experiment_id="position-b",
        comparison_type="LOCAL",
        eligibility="NOT_COMPARABLE",
        comparison_blocked=True,
        repeatability_blocked=True,
    )

    PlacementComparisonSelectionConsoleReporter().print(rendered)

    output = capsys.readouterr().out
    assert "COMPARAISON IMPOSSIBLE" in output
    assert "pas suffisamment fiables" in output
    assert "reason" not in output.lower()


@pytest.mark.parametrize(
    ("status", "label"),
    (
        ("BETTER", "MEILLEUR"),
        ("WORSE", "PIRE"),
        ("EQUIVALENT", "ÉQUIVALENT"),
        ("INDETERMINATE", "INDÉTERMINÉ"),
    ),
)
def test_console_translates_only_an_existing_placement_qualification(status, label, capsys):
    rendered = Report(project_name="selection-fixture")
    rendered.placement_comparison_selection = PresentedPlacementComparisonSelection(
        comparison_id="trace:comparison:local:a:b",
        reference_experiment_id="position-a",
        target_experiment_id="position-b",
        comparison_type="LOCAL",
        eligibility="COMPARABLE",
        placement_result=status,
    )

    PlacementComparisonSelectionConsoleReporter().print(rendered)

    output = capsys.readouterr().out
    assert f"Résultat : {label}" in output
    assert "Causality status: NOT_ESTABLISHED" in output
