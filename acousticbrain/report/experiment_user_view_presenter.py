from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedExperimentUserView:
    experiment_id: str
    lifecycle_state: str
    intent_lines: tuple[str, ...]
    user_action_state: str
    user_action: str
    observed_result: str
    observed_result_lines: tuple[str, ...]
    scientific_boundary_lines: tuple[str, ...]
    causality_status: str
    reference_experiment_id: str | None = None
    source_plan_id: str | None = None
    source_protocol_id: str | None = None
    source_hypothesis_code: str | None = None
    comparison_id: str | None = None


class ExperimentUserViewPresenter:
    """Read-only projection of one experiment's established report objects."""

    def present(self, report, experiment_id):
        experiments = tuple(
            value for value in getattr(
                getattr(report, "experiments_discovered", None),
                "experiments",
                (),
            )
            if value.experiment_id == experiment_id
        )
        if not experiments:
            raise ValueError(f"Unknown experiment_id: {experiment_id}")
        if len(experiments) != 1:
            raise ValueError(f"Ambiguous experiment_id: {experiment_id}")
        experiment = experiments[0]

        comparisons = tuple(
            value for value in getattr(
                getattr(report, "experiment_comparison", None),
                "local_comparisons",
                (),
            )
            if value.after_experiment_id == experiment_id
        )
        if len(comparisons) > 1:
            references = ", ".join(sorted(
                value.before_experiment_id for value in comparisons
            ))
            raise ValueError(
                f"Ambiguous local comparison for experiment_id {experiment_id}: "
                f"references {references}"
            )
        comparison = comparisons[0] if comparisons else None

        plan_id = experiment.source_evidence_acquisition_plan_id
        plans = tuple(
            value for value in getattr(
                getattr(report, "evidence_acquisition_plans", None), "plans", ()
            )
            if value.plan_id == plan_id
        ) if plan_id is not None else ()
        if len(plans) > 1:
            raise ValueError(f"Ambiguous source plan_id: {plan_id}")

        intent = self._intent(experiment, comparison)
        lifecycle = self._lifecycle(experiment, comparison)
        action_state, action = self._action(lifecycle, experiment, comparison)
        observed, observed_lines = self._observed(comparison)
        boundary = self._boundary(experiment, comparison)
        return PresentedExperimentUserView(
            experiment_id=experiment_id,
            lifecycle_state=lifecycle,
            intent_lines=intent,
            user_action_state=action_state,
            user_action=action,
            observed_result=observed,
            observed_result_lines=observed_lines,
            scientific_boundary_lines=boundary,
            causality_status="NOT_ESTABLISHED",
            reference_experiment_id=(
                comparison.before_experiment_id if comparison else None
            ),
            source_plan_id=plan_id,
            source_protocol_id=(comparison.source_protocol_id if comparison else None),
            source_hypothesis_code=(
                comparison.source_hypothesis_code if comparison else None
            ),
            comparison_id=(comparison.trace_id if comparison else None),
        )

    @staticmethod
    def _intent(experiment, comparison):
        lines = []
        preserved_objective = getattr(experiment, "preserved_plan_objective", None)
        if preserved_objective is None:
            lines.append("Intention originale du plan indisponible.")
        else:
            lines.append(preserved_objective)
        modified = comparison.modified_variables if comparison else ()
        controlled = getattr(experiment, "preserved_plan_controlled_variables", ())
        if not controlled and comparison:
            controlled = comparison.controlled_variables
        lines.append(
            "Variables modifiées : "
            + (", ".join(modified) if modified else "indisponibles")
        )
        lines.append(
            "Variables contrôlées : "
            + (", ".join(controlled) if controlled else "indisponibles")
        )
        lines.append(
            "Observations attendues : "
            + (
                ", ".join(getattr(
                    experiment,
                    "preserved_plan_expected_observations",
                    (),
                ))
                or "indisponibles"
            )
        )
        lines.append(
            "Limites du plan : "
            + (", ".join(getattr(experiment, "preserved_plan_limitations", ())) or "aucune déclarée")
        )
        return tuple(lines)

    @staticmethod
    def _lifecycle(experiment, comparison):
        if (
            experiment.source_evidence_acquisition_plan_id is None
            or getattr(experiment, "preserved_plan_objective", None) is None
        ):
            return "CONTRACT_MISSING"
        if experiment.plan_contract_preservation_status in (
            "PLAN_COVERAGE_PARTIAL",
            "PLAN_COVERAGE_INSUFFICIENT_DECLARATION",
        ):
            return "CONTRACT_INCONSISTENT"
        if experiment.file_count == 0:
            return "ACQUISITION_PENDING"
        if (
            experiment.state != "READY"
            or experiment.evidence_acquisition_plan_coverage_status
            not in ("PLAN_COVERAGE_COMPLETE", "PLAN_COVERAGE_NOT_APPLICABLE")
        ):
            return "ACQUISITION_INCOMPLETE"
        if comparison is None or comparison.eligibility != "COMPARABLE":
            return "COMPARISON_UNAVAILABLE"
        if comparison.acoustic_outcome in ("INCONCLUSIVE", "MIXED"):
            return "RESULT_INCONCLUSIVE"
        return "RESULT_AVAILABLE"

    @staticmethod
    def _action(lifecycle, experiment, comparison):
        if lifecycle == "CONTRACT_MISSING":
            if experiment.source_evidence_acquisition_plan_id is None:
                return (
                    "NO_USER_ACTION",
                    "Aucune action : ne pas reconstruire ni écraser le contrat historique.",
                )
            return (
                "RESOLVE_PLAN_CONTRACT_MISMATCH",
                "Restaurer le contrat du plan déjà référencé sans le reconstruire.",
            )
        if lifecycle == "CONTRACT_INCONSISTENT":
            return (
                "RESOLVE_PLAN_CONTRACT_MISMATCH",
                "Résoudre la divergence du contrat de plan déclaré.",
            )
        if lifecycle in ("ACQUISITION_PENDING", "ACQUISITION_INCOMPLETE"):
            return (
                "COMPLETE_REQUIRED_ACQUISITION",
                "Compléter l’acquisition requise déjà déclarée.",
            )
        if lifecycle == "COMPARISON_UNAVAILABLE":
            return (
                "RESTORE_COMPARABILITY",
                "Rétablir la comparabilité à partir de la déclaration existante.",
            )
        if comparison is not None:
            return "REVIEW_OBSERVED_RESULT", "Examiner le résultat observé."
        return "NO_USER_ACTION", "Aucune action."

    @staticmethod
    def _observed(comparison):
        if comparison is None:
            return "NOT_AVAILABLE", (
                "Aucune comparaison locale unique n’est disponible.",
            )
        if comparison.eligibility != "COMPARABLE":
            reasons = comparison.ineligibility_reasons or ("motif indisponible",)
            return "NOT_COMPARABLE", ("Inéligibilité : " + ", ".join(reasons),)
        return comparison.acoustic_outcome, (
            "Faits améliorés : "
            + (", ".join(comparison.improved_fact_codes) or "aucun"),
            "Faits dégradés : "
            + (", ".join(comparison.degraded_fact_codes) or "aucun"),
            "Faits modifiés : "
            + (", ".join(comparison.changed_fact_codes) or "aucun"),
            "Faits inchangés : "
            + (", ".join(comparison.unchanged_fact_codes) or "aucun"),
            "Faits indisponibles : "
            + (", ".join(comparison.unavailable_fact_codes) or "aucun"),
        )

    @staticmethod
    def _boundary(experiment, comparison):
        lines = [
            "Aucune cause, correction permanente, configuration optimale "
            "ou recommandation générale n’est établie."
        ]
        if comparison is None:
            lines.append("Comparaison locale indisponible.")
        else:
            lines.append(f"Périmètre mesuré : {comparison.comparison_type}.")
        if getattr(experiment, "preserved_plan_objective", None) is None:
            lines.append("Limite historique : contrat original préservé du plan indisponible.")
        lines.extend(
            f"Limite contractuelle : {value}"
            for value in experiment.plan_contract_limitations
        )
        return tuple(lines)


class ExperimentUserViewConsoleReporter:
    def print(self, report):
        view = report.experiment_user_view
        print(f"EXPERIMENT VIEW — {view.experiment_id}")
        print()
        print("Intention")
        print("\n".join(view.intent_lines))
        print()
        print("Action utilisateur")
        print(view.user_action)
        print()
        print("Résultat observé")
        print(view.observed_result)
        print("\n".join(view.observed_result_lines))
        print()
        print("Frontière scientifique")
        print("\n".join(view.scientific_boundary_lines))
        print(f"Causality status: {view.causality_status}")
