from dataclasses import dataclass

from .decision_first_presenter import PresentedDecisionFirstReport


@dataclass(frozen=True)
class PresentedOneMinuteExecutiveSummary:
    situation: tuple[str, ...]
    verdict: tuple[str, ...]
    conclusion: tuple[str, str]
    actions: tuple[str, ...]
    reasons: tuple[str, ...]
    confidence: tuple[str, str, str]


class OneMinuteExecutiveSummaryPresenter:
    """Condense la décision PR-041 sans recalculer ni arbitrer son contenu."""

    MAXIMUM_ACTION_LINES = 3
    MAXIMUM_REASON_LINES = 2

    def present(
        self,
        decision: PresentedDecisionFirstReport,
    ) -> PresentedOneMinuteExecutiveSummary:
        return PresentedOneMinuteExecutiveSummary(
            situation=self._situation(decision),
            verdict=self._verdict(decision),
            conclusion=self._conclusion(decision),
            actions=self._actions(decision)[: self.MAXIMUM_ACTION_LINES],
            reasons=self._reasons(decision)[: self.MAXIMUM_REASON_LINES],
            confidence=self._confidence(decision),
        )

    @staticmethod
    def _situation(decision):
        if not decision.comparison_available:
            return (
                "Première mesure disponible : aucune expérience précédente comparable.",
            )
        if not decision.comparison_comparable:
            return (
                "Comparaison indisponible : les expériences ne sont pas comparables.",
            )
        values = [
            (
                f"Comparaison : {decision.comparison_before_experiment_id} → "
                f"{decision.comparison_after_experiment_id}."
            )
        ]
        if decision.configuration_declared_unchanged:
            values.append(
                "Selon la déclaration utilisateur, aucune modification volontaire "
                "de la configuration n’était prévue."
            )
            return tuple(values)
        if decision.experiment_kind == "MEASUREMENT_REPEAT":
            values.append(
                "L’expérience est déclarée par l’utilisateur comme une répétition "
                "de mesure."
            )
            return tuple(values)
        if not decision.tested_conditions_declared:
            values.append(
                "La variable testée, ou l’absence de changement volontaire, "
                "n’a pas été déclarée."
            )
        return tuple(values)

    @staticmethod
    def _verdict(decision):
        if not decision.comparison_available:
            return (
                "Aucune comparaison avec une expérience précédente n’est disponible.",
            )
        return decision.verdict_lines

    @staticmethod
    def _conclusion(decision):
        if not decision.comparison_available:
            return "Non.", "Aucune comparaison fiable n’est disponible."
        if not decision.comparison_comparable:
            return "Non.", "Les expériences ne sont pas comparables."
        if decision.experiment_kind == "MEASUREMENT_REPEAT":
            if decision.configuration_declared_unchanged:
                return (
                    "Partiellement.",
                    "Ces écarts renseignent sur la répétition déclarée du protocole ; "
                    "ils ne permettent pas d’établir l’effet d’un changement de "
                    "positionnement.",
                )
            return (
                "Partiellement.",
                "L’utilisateur déclare une répétition, mais ne déclare pas toutes "
                "les variables comme contrôlées.",
            )
        if not decision.tested_conditions_declared:
            return "Non.", "AcousticBrain ne sait pas formellement ce qui était testé."
        if decision.comparison_acoustic_outcome in {"MIXED", "INCONCLUSIVE"}:
            return "Non.", "Le verdict mesuré reste contradictoire ou inconclusif."
        if decision.comparison_acoustic_outcome in {
            "IMPROVED",
            "DEGRADED",
            "UNCHANGED",
        }:
            return (
                "Oui, mais uniquement dans le périmètre mesuré.",
                "Le protocole et la variable testée sont explicitement déclarés.",
            )
        return "Partiellement.", "L’origine du changement n’est pas établie."

    @classmethod
    def _actions(cls, decision):
        if decision.experiment_kind == "MEASUREMENT_REPEAT":
            labels = tuple(
                label for code, label in (
                    ("MICROPHONE_POSITION", "le microphone"),
                    ("MEASUREMENT_LEVEL", "le volume"),
                    ("REW_MEASUREMENT_PARAMETERS", "les paramètres REW"),
                )
                if code in decision.controlled_variables
            )
            control = (
                "Vérifiez concrètement la conformité à la déclaration pour "
                + cls._join_labels(labels) + "."
                if labels
                else "Complétez la déclaration des variables maintenues inchangées."
            )
            return (
                "Ne déplacez pas encore les enceintes.",
                control,
                "Réalisez éventuellement une nouvelle répétition de contrôle.",
            )
        if decision.action_status == "AVAILABLE":
            values = [cls._precise_action(decision)]
            if decision.unchanged_items:
                controls = tuple(
                    item
                    for item in (
                        "la position du microphone",
                        "le volume de mesure",
                    )
                    if item in decision.unchanged_items
                )
                if controls:
                    values.append(
                        "Conservez " + cls._join_labels(controls) + " inchangés."
                    )
            if decision.required_measurements:
                values.append(
                    "Reprenez " + ", ".join(decision.required_measurements) + "."
                )
            return tuple(values)

        values = ["Aucune action fiable ne peut être recommandée actuellement."]
        values.extend(decision.unblock_steps)
        return tuple(values)

    @staticmethod
    def _precise_action(decision):
        if decision.positioning_proposal_id is not None:
            return decision.action
        if decision.target is None or (
            decision.direction is None and decision.amplitude is None
        ):
            return decision.action
        details = " ".join(
            item for item in (decision.amplitude, decision.direction) if item
        )
        return decision.action.rstrip(".") + f" — {details}."

    @staticmethod
    def _join_labels(values):
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return " et ".join(values)
        return ", ".join(values[:-1]) + " et " + values[-1]

    @staticmethod
    def _reasons(decision):
        if decision.experiment_kind == "MEASUREMENT_REPEAT":
            return (
                "La déclaration utilisateur n’indique aucune modification volontaire "
                "de placement.",
                "AcousticBrain ne peut donc pas attribuer les différences observées "
                "à un déplacement.",
            )
        if not decision.tested_conditions_declared and decision.comparison_available:
            if decision.comparison_acoustic_outcome == "MIXED":
                return (
                    "Les effets observés sont contradictoires et la modification "
                    "testée n’est pas suffisamment documentée.",
                )
            return (
                "La modification testée n’est pas suffisamment documentée.",
            )
        if decision.action_status == "TIED":
            return (
                "Plusieurs actions restent également prioritaires.",
                "AcousticBrain ne peut pas choisir honnêtement entre elles.",
            )
        if decision.comparison_acoustic_outcome == "MIXED":
            return (
                "Les améliorations et dégradations observées se compensent.",
            )
        if decision.action_status == "AVAILABLE":
            if decision.positioning_proposal_id is not None:
                observables = ", ".join(
                    decision.positioning_expected_observables[:2]
                )
                detail = (
                    f" Les observables suivis seront : {observables}."
                    if observables
                    else ""
                )
                return (
                    "Une seule variable est modifiée dans un pas expérimental réversible.",
                    "Ce test n’est pas une position optimale prédite et ne promet "
                    "aucune amélioration." + detail,
                )
            return ("Une action structurée est déjà disponible.",)
        if decision.action_reasons:
            return (decision.action_reasons[0],)
        return ("Aucune action suffisamment établie n’est disponible.",)

    @staticmethod
    def _confidence(decision):
        measurement = {
            "EXPLOITABLE": "Mesures : exploitables.",
            "WITH_RESERVATIONS": "Mesures : exploitables avec réserves.",
            "INSUFFICIENT": "Mesures : insuffisantes.",
            "UNKNOWN": "Mesures : statut non établi.",
        }[decision.measurement_status]
        if (
            not decision.comparison_available
            or not decision.comparison_comparable
        ):
            verdict = "Verdict : non établi."
        elif (
            not decision.tested_conditions_declared
            or decision.comparison_acoustic_outcome in {"MIXED", "INCONCLUSIVE"}
        ):
            verdict = "Verdict : incertain."
        else:
            verdict = "Verdict : établi par les mesures."
        cause = "Cause : non établie (NOT_ESTABLISHED)."
        if decision.positioning_proposal_id is not None:
            cause = (
                "Action : expérience réversible proposée ; amélioration non garantie. "
                "Cause : non établie (NOT_ESTABLISHED)."
            )
        return measurement, verdict, cause
