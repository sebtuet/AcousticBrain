"""Read-only selection of one exact presented experiment comparison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedPlacementComparisonSelection:
    comparison_id: str
    reference_experiment_id: str
    target_experiment_id: str
    comparison_type: str
    eligibility: str
    causality_status: str = "NOT_ESTABLISHED"


class PlacementComparisonSelectionPresenter:
    """Resolves a trace identifier without preferring local or cumulative data."""

    def present(self, report, comparison_id):
        comparisons = (
            *getattr(
                getattr(report, "experiment_comparison", None),
                "local_comparisons",
                (),
            ),
            *getattr(
                getattr(report, "experiment_comparison", None),
                "cumulative_comparisons",
                (),
            ),
        )
        matches = tuple(
            item for item in comparisons if item.trace_id == comparison_id
        )
        if not matches:
            raise ValueError(f"COMPARISON_UNKNOWN: {comparison_id}.")
        if len(matches) != 1:
            raise ValueError(f"COMPARISON_AMBIGUOUS: {comparison_id}.")
        comparison = matches[0]
        return PresentedPlacementComparisonSelection(
            comparison_id=comparison_id,
            reference_experiment_id=comparison.before_experiment_id,
            target_experiment_id=comparison.after_experiment_id,
            comparison_type=comparison.comparison_type,
            eligibility=comparison.eligibility,
        )


class PlacementComparisonSelectionConsoleReporter:
    """Keeps the public selection view concise and non-causal."""

    def print(self, report):
        selection = report.placement_comparison_selection
        print("COMPARAISON SÉLECTIONNÉE")
        print()
        print(f"Référence : {selection.reference_experiment_id}")
        print(f"Cible : {selection.target_experiment_id}")
        if selection.eligibility == "COMPARABLE":
            print("État : comparaison disponible.")
        else:
            print("Résultat : COMPARAISON IMPOSSIBLE")
            print(
                "Les mesures actuellement disponibles ne permettent pas de "
                "comparer ces deux placements."
            )
        print()
        print("Frontière scientifique")
        print(
            "Cette vue sélectionne une comparaison existante ; elle ne calcule "
            "ni verdict de placement ni causalité."
        )
        print(f"Causality status: {selection.causality_status}")
