"""Read-only selection of one exact presented experiment comparison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedPlacementComparisonSelection:
    comparison_id: str
    reference_experiment_id: str
    target_experiment_id: str
    comparison_type: str
    eligibility: str
    placement_result: str | None = None
    comparison_blocked: bool = False
    repeatability_blocked: bool = False
    causality_status: str = "NOT_ESTABLISHED"


class PlacementComparisonSelectionPresenter:
    """Resolves a trace identifier without preferring local or cumulative data."""

    def present(self, report, comparison_id, *, qualification=None):
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
            placement_result=(
                qualification.placement_qualification.comparison_status.value
                if qualification is not None
                and qualification.placement_qualification is not None
                else None
            ),
            comparison_blocked=(
                qualification is not None
                and qualification.placement_qualification is None
            ),
            repeatability_blocked=(
                qualification is not None
                and any(
                    code.startswith("REPEATABILITY_QUALIFICATION_")
                    for code in qualification.blocking_reason_codes
                )
            ),
        )


class PlacementComparisonSelectionConsoleReporter:
    """Keeps the public selection view concise and non-causal."""

    def print(self, report):
        selection = report.placement_comparison_selection
        print("COMPARAISON SÉLECTIONNÉE")
        print()
        print(f"Référence : {selection.reference_experiment_id}")
        print(f"Cible : {selection.target_experiment_id}")
        labels = {
            "BETTER": "MEILLEUR",
            "WORSE": "PIRE",
            "EQUIVALENT": "ÉQUIVALENT",
            "INDETERMINATE": "INDÉTERMINÉ",
        }
        if selection.placement_result is not None:
            print(f"Résultat : {labels[selection.placement_result]}")
        elif selection.eligibility == "COMPARABLE" and not selection.comparison_blocked:
            print("État : comparaison disponible.")
        else:
            print("Résultat : COMPARAISON IMPOSSIBLE")
            if selection.repeatability_blocked:
                print(
                    "Les mesures de la référence ou du nouveau placement ne "
                    "sont pas suffisamment fiables pour être comparées."
                )
            else:
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
