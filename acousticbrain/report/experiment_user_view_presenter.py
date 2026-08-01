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
        plan = plans[0] if plans else None

        intent = self._intent(experiment, plan, comparison)
        lifecycle = self._lifecycle(experiment, plan, comparison)
        action_state, action = self._action(lifecycle, experiment, comparison)
        observed, observed_lines = self._observed(comparison)
        boundary = self._boundary(experiment, plan, comparison)
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
    def _intent(experiment, plan, comparison):
        lines = []
        preserved_objective = getattr(experiment, "preserved_plan_objective", None)
        if preserved_objective is None:
            lines.append("Original plan intent unavailable.")
        else:
            lines.append(preserved_objective)
        modified = comparison.modified_variables if comparison else ()
        controlled = getattr(experiment, "preserved_plan_controlled_variables", ())
        if not controlled and comparison:
            controlled = comparison.controlled_variables
        lines.append(
            "Modified variables: " + (", ".join(modified) if modified else "unavailable")
        )
        lines.append(
            "Controlled variables: "
            + (", ".join(controlled) if controlled else "unavailable")
        )
        lines.append(
            "Expected observations: "
            + (", ".join(getattr(experiment, "preserved_plan_expected_observations", ())) or "unavailable")
        )
        lines.append(
            "Plan limitations: "
            + (", ".join(getattr(experiment, "preserved_plan_limitations", ())) or "none declared")
        )
        return tuple(lines)

    @staticmethod
    def _lifecycle(experiment, plan, comparison):
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
                "Restore the already-referenced plan contract without reconstructing it.",
            )
        if lifecycle == "CONTRACT_INCONSISTENT":
            return "RESOLVE_PLAN_CONTRACT_MISMATCH", "Resolve the declared plan contract mismatch."
        if lifecycle in ("ACQUISITION_PENDING", "ACQUISITION_INCOMPLETE"):
            return "COMPLETE_REQUIRED_ACQUISITION", "Complete the already-declared required acquisition."
        if lifecycle == "COMPARISON_UNAVAILABLE":
            return "RESTORE_COMPARABILITY", "Restore comparability using the existing declaration."
        if comparison is not None:
            return "REVIEW_OBSERVED_RESULT", "Review the observed result."
        return "NO_USER_ACTION", "No action."

    @staticmethod
    def _observed(comparison):
        if comparison is None:
            return "NOT_AVAILABLE", ("No unique local comparison is available.",)
        if comparison.eligibility != "COMPARABLE":
            reasons = comparison.ineligibility_reasons or ("reason unavailable",)
            return "NOT_COMPARABLE", ("Ineligibility: " + ", ".join(reasons),)
        return comparison.acoustic_outcome, (
            "Improved facts: " + (", ".join(comparison.improved_fact_codes) or "none"),
            "Degraded facts: " + (", ".join(comparison.degraded_fact_codes) or "none"),
            "Changed facts: " + (", ".join(comparison.changed_fact_codes) or "none"),
            "Unchanged facts: " + (", ".join(comparison.unchanged_fact_codes) or "none"),
            "Unavailable facts: " + (", ".join(comparison.unavailable_fact_codes) or "none"),
        )

    @staticmethod
    def _boundary(experiment, plan, comparison):
        lines = ["No cause, permanent correction, optimum, or general recommendation is established."]
        if comparison is None:
            lines.append("Local comparison unavailable.")
        else:
            lines.append(f"Measured scope: {comparison.comparison_type}.")
        if plan is None:
            lines.append("Historical limit: preserved original plan contract unavailable.")
        lines.extend(experiment.plan_contract_limitations)
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
