"""Console projection for the guided native placement session."""

from acousticbrain.application.guided_native_placement_session import (
    GuidedNativePlacementSessionStatus,
    GuidedNativePlacementVerdict,
)
from acousticbrain.application.placement_comparison_qualification import (
    PlacementComparisonStatus,
)


class GuidedNativePlacementSessionConsoleReporter:
    """Presents the product verdict without adding an acoustic decision."""

    _STATUS_EXPLANATIONS = {
        GuidedNativePlacementSessionStatus.KEEP: (
            "La position candidate est qualifiée BETTER par le moteur de "
            "comparaison de placement."
        ),
        GuidedNativePlacementSessionStatus.REVERT: (
            "La position candidate est qualifiée WORSE par le moteur de "
            "comparaison de placement."
        ),
        GuidedNativePlacementSessionStatus.INDETERMINATE: (
            "Les mesures disponibles ne permettent pas de conclure de manière "
            "directionnelle."
        ),
        GuidedNativePlacementSessionStatus.REFERENCE_CAPTURE_INVALID: (
            "La référence n'a pas produit une capture exploitable."
        ),
        GuidedNativePlacementSessionStatus.REFERENCE_NOT_QUALIFIED: (
            "Référence non suffisamment répétable. La session est arrêtée "
            "avant comparaison."
        ),
        GuidedNativePlacementSessionStatus.CANDIDATE_CAPTURE_INVALID: (
            "La candidate n'a pas produit une capture exploitable."
        ),
        GuidedNativePlacementSessionStatus.CANDIDATE_NOT_QUALIFIED: (
            "Mesure candidate non suffisamment répétable. Impossible de "
            "conclure sur le placement."
        ),
        GuidedNativePlacementSessionStatus.COMPARISON_NOT_COMPARABLE: (
            "La comparaison existante n'est pas comparable ; aucun KEEP/REVERT "
            "n'est émis."
        ),
    }

    def print(self, result):
        print()
        print("Résultat placement guidé")
        print()
        print(f"Verdict : {self._display_verdict(result)}")
        print(self._explanation(result))
        print()
        if result.reference_experiment_id is not None:
            print(f"Référence : {result.reference_experiment_id}")
        if result.candidate_experiment_id is not None:
            print(f"Candidate : {result.candidate_experiment_id}")
        if result.comparison_id is not None:
            print(f"Comparaison : {result.comparison_id}")
        if (
            result.placement_status is not None
            and result.placement_status is not PlacementComparisonStatus.EQUIVALENT
        ):
            print(f"Qualification placement : {result.placement_status.value}")
        if result.displacement_description is not None:
            print(f"Déplacement déclaré : {result.displacement_description}")
        if result.verdict is GuidedNativePlacementVerdict.INDETERMINATE:
            label = self._indeterminate_detail(result)
            if label is not None:
                print(f"État : {label}")
        print(f"Causality status: {result.causality_status}")

    @staticmethod
    def _display_verdict(result):
        if result.placement_status is PlacementComparisonStatus.EQUIVALENT:
            return PlacementComparisonStatus.EQUIVALENT.value
        return result.verdict.value

    @classmethod
    def _explanation(cls, result):
        if result.placement_status is PlacementComparisonStatus.EQUIVALENT:
            return (
                "Le déplacement n'a pas produit de différence directionnelle "
                "suffisante pour recommander KEEP ou REVERT."
            )
        return cls._STATUS_EXPLANATIONS[result.status]

    @staticmethod
    def _indeterminate_detail(result):
        if result.placement_status is PlacementComparisonStatus.INDETERMINATE:
            return "verdict métier INDETERMINATE"
        if result.placement_status is PlacementComparisonStatus.EQUIVALENT:
            return "comparaison qualifiée EQUIVALENT"
        if result.comparison_id is None:
            return "comparaison non exécutée"
        return "comparaison non directionnelle"
