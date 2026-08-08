from dataclasses import dataclass
from pathlib import Path
import shlex

from .experiment_user_view_presenter import PresentedExperimentUserView
from .experiment_discovery_presenter import PresentedDiscoveredExperiment

from acousticbrain.application import (
    ChannelIsolationDeclarationReadiness,
    ChannelIsolationOperationalRecordPreview,
    EvidencePlanPreparationResolver,
)
from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)


@dataclass(frozen=True)
class PresentedGuidedGlobalStatus:
    workflow_state: str
    current_state_lines: tuple[str, ...]
    validated_step_lines: tuple[str, ...]
    blocker_lines: tuple[str, ...]
    user_action_state: str
    user_action: str
    scientific_boundary_lines: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"


class GuidedGlobalStatusPresenter:
    """Projects existing workflow decisions without creating a new decision."""

    def __init__(self, preparation_resolver=None):
        self.preparation_resolver = (
            preparation_resolver or EvidencePlanPreparationResolver()
        )

    def present(
        self, report, *, plans, preparation_registry=None,
        preparation_id=None, operational_record_preview=None,
        declaration_readiness=None, measurement_root=None,
        preparation_registry_path=None,
        declared_experiment_view=None,
    ):
        if not isinstance(plans, tuple) or any(
            not isinstance(value, EvidenceAcquisitionPlan) for value in plans
        ):
            raise TypeError("Guided global status requires exact typed plans.")
        if preparation_registry is not None and not isinstance(
            preparation_registry, EvidencePlanPreparationRegistry
        ):
            raise TypeError("Guided global status preparation registry is invalid.")
        if preparation_id is not None and (
            not isinstance(preparation_id, str)
            or not preparation_id
            or preparation_id != preparation_id.strip()
        ):
            raise ValueError("Guided global status preparation id must be exact text.")
        if preparation_id is not None and preparation_registry is None:
            raise ValueError(
                "Guided global status preparation id requires a registry."
            )
        if operational_record_preview is not None:
            if not isinstance(
                operational_record_preview,
                ChannelIsolationOperationalRecordPreview,
            ):
                raise TypeError(
                    "Guided global status operational record preview is invalid."
                )
            if preparation_registry is None or preparation_id is None:
                raise ValueError(
                    "Guided global status operational records require one exact "
                    "preparation selection."
                )
        if declaration_readiness is not None:
            if not isinstance(
                declaration_readiness, ChannelIsolationDeclarationReadiness
            ):
                raise TypeError(
                    "Guided global status declaration readiness is invalid."
                )
            if preparation_registry is None or preparation_id is None:
                raise ValueError(
                    "Guided global status declaration readiness requires one "
                    "exact preparation selection."
                )
            if not isinstance(measurement_root, Path):
                raise TypeError(
                    "Guided global status declaration readiness requires an "
                    "exact measurement root."
                )
            if not isinstance(preparation_registry_path, Path):
                raise TypeError(
                    "Guided global status declaration readiness requires an "
                    "exact preparation registry path."
                )
        if declared_experiment_view is not None:
            if not isinstance(
                declared_experiment_view, PresentedExperimentUserView
            ):
                raise TypeError(
                    "Guided global status declared experiment view is invalid."
                )
            if preparation_registry is None or preparation_id is None:
                raise ValueError(
                    "Guided global status declared experiment requires one exact "
                    "preparation selection."
                )
        plan_report = getattr(report, "evidence_acquisition_plans", None)
        experiments = tuple(getattr(
            getattr(report, "experiments_discovered", None), "experiments", ()
        ))
        base_state = (
            f"Campagne analysée : {len(experiments)} expérience(s) découverte(s).",
        )
        if plan_report is None or not plan_report.plans:
            return self._result(
                "NO_EVIDENCE_PLAN",
                base_state,
                ("Analyse déterministe disponible ; aucun plan d’acquisition produit.",),
                ("Aucun plan d’acquisition de preuves n’est disponible.",),
                "REVIEW_FULL_ASSESSMENT",
                "Consulter l’évaluation complète avec --full-assessment.",
            )
        recommended = plan_report.recommended_plan
        if recommended is None:
            statuses = ", ".join(sorted({value.status for value in plan_report.plans}))
            return self._result(
                "NO_READY_EVIDENCE_PLAN",
                (*base_state, f"Plans disponibles : {len(plan_report.plans)}."),
                ("Les plans existants ont été conservés sans nouvelle sélection.",),
                (f"Aucun plan READY ; statuts présents : {statuses}.",),
                "REVIEW_EVIDENCE_PLAN_OVERVIEW",
                "Consulter la vue d’ensemble avec --evidence-plan-overview.",
            )
        matches = tuple(value for value in plans if value.plan_id == recommended.plan_id)
        if len(matches) != 1:
            raise ValueError(
                "Guided global status requires one exact recommended source plan: "
                f"{recommended.plan_id}."
            )
        plan = matches[0]
        current = (
            *base_state,
            f"Plan recommandé existant : {recommended.plan_id}.",
            f"Statut du plan : {recommended.status}.",
        )
        validated = (
            "Analyse déterministe disponible.",
            "Recommandation de plan réutilisée sans nouveau classement.",
        )
        if preparation_registry is None:
            return self._result(
                "READY_PLAN_PREPARATION_UNAVAILABLE",
                current,
                validated,
                ("État de préparation indisponible : aucun registre explicite fourni.",),
                "REVIEW_RECOMMENDED_PLAN",
                "Consulter le plan exact avec --evidence-plan-view "
                f"{recommended.plan_id}.",
            )
        records = tuple(
            value for value in preparation_registry.records
            if value.confirmation_input.plan_id == recommended.plan_id
        )
        if preparation_id is not None:
            exact = tuple(
                value for value in preparation_registry.records
                if value.confirmation_input.confirmation_id == preparation_id
            )
            if len(exact) != 1:
                raise ValueError(
                    "Guided global status requires one exact preparation: "
                    f"{preparation_id}."
                )
            if exact[0].confirmation_input.plan_id != recommended.plan_id:
                raise ValueError(
                    "Guided global status preparation targets another plan."
                )
            records = exact
        if not records:
            return self._result(
                "READY_PLAN_PREPARATION_NOT_DECLARED",
                current,
                validated,
                ("Aucune préparation déclarée pour le plan recommandé.",),
                "GENERATE_PREPARATION_DRAFT",
                "Générer un brouillon avec --generate-evidence-plan-preparation "
                f"{recommended.plan_id}.",
            )
        if len(records) > 1:
            identifiers = ", ".join(sorted(
                value.confirmation_input.confirmation_id for value in records
            ))
            return self._result(
                "READY_PLAN_PREPARATION_AMBIGUOUS",
                current,
                validated,
                ("Plusieurs préparations existent : " + identifiers + ".",),
                "SELECT_EXACT_PREPARATION",
                "Relancer cette vue avec --guided-preparation CONFIRMATION_ID parmi : "
                + identifiers
                + ".",
            )
        record = records[0]
        confirmation = record.confirmation_input
        try:
            self.preparation_resolver.resolve(confirmation, plans=(plan,))
        except (TypeError, ValueError) as error:
            return self._result(
                "READY_PLAN_PREPARATION_STALE",
                current,
                validated,
                (f"Préparation incompatible ou historique : {error}",),
                "GENERATE_CURRENT_PREPARATION_DRAFT",
                "Générer un nouveau brouillon depuis le plan actuel avec "
                f"--generate-evidence-plan-preparation {recommended.plan_id}.",
            )
        declared_candidates = tuple(
            value for value in experiments
            if declared_experiment_view is None
            and getattr(
                value,
                "channel_isolation_preparation_confirmation_id",
                None,
            ) == confirmation.confirmation_id
        )
        if any(
            not isinstance(value, PresentedDiscoveredExperiment)
            for value in declared_candidates
        ):
            raise TypeError(
                "Guided global status declared experiment candidates are invalid."
            )
        if any(
            not isinstance(value.experiment_id, str)
            or not value.experiment_id
            or value.experiment_id != value.experiment_id.strip()
            for value in declared_candidates
        ):
            raise ValueError(
                "Guided global status declared experiment candidate id must be "
                "exact text."
            )
        declared_candidates = tuple(sorted(
            declared_candidates,
            key=lambda value: value.experiment_id,
        ))
        candidate_ids = tuple(value.experiment_id for value in declared_candidates)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError(
                "Guided global status declared experiment candidate identity is "
                "ambiguous."
            )
        for candidate in declared_candidates:
            if candidate.source_evidence_acquisition_plan_id != recommended.plan_id:
                raise ValueError(
                    "Guided global status declared experiment candidate targets "
                    "another plan."
                )
            if (
                candidate.channel_isolation_preparation_plan_fingerprint
                != confirmation.plan_contract_fingerprint
                or candidate.channel_isolation_preparation_qualification_status
                != "ALL_PREREQUISITES_USER_CONFIRMED"
            ):
                raise ValueError(
                    "Guided global status declared experiment candidate preparation "
                    "provenance is inconsistent."
                )
            if candidate.evidence_acquisition_plan_coverage_status not in (
                "PLAN_COVERAGE_PARTIAL",
                "PLAN_COVERAGE_COMPLETE",
            ):
                raise ValueError(
                    "Guided global status declared experiment candidate specialized "
                    "declaration is insufficient."
                )
        unresolved = tuple(
            value for value in confirmation.prerequisites
            if value.status is not EvidencePlanPrerequisiteStatus.CONFIRMED
        )
        if declared_experiment_view is not None:
            if declared_experiment_view.source_plan_id != recommended.plan_id:
                raise ValueError(
                    "Guided global status declared experiment targets another plan."
                )
            if (
                declared_experiment_view.preparation_confirmation_id
                != confirmation.confirmation_id
                or declared_experiment_view.preparation_plan_fingerprint
                != confirmation.plan_contract_fingerprint
                or declared_experiment_view.preparation_qualification_status
                != "ALL_PREREQUISITES_USER_CONFIRMED"
            ):
                raise ValueError(
                    "Guided global status declared experiment preparation "
                    "provenance is inconsistent."
                )
            lifecycle = declared_experiment_view.lifecycle_state
            accepted_coverage = (
                ("PLAN_COVERAGE_COMPLETE",)
                if lifecycle in (
                    "COMPARISON_UNAVAILABLE",
                    "RESULT_INCONCLUSIVE",
                    "RESULT_AVAILABLE",
                )
                else ("PLAN_COVERAGE_PARTIAL", "PLAN_COVERAGE_COMPLETE")
            )
            if (
                declared_experiment_view.declared_plan_coverage_status
                not in accepted_coverage
            ):
                raise ValueError(
                    "Guided global status declared experiment specialized "
                    "declaration is insufficient."
                )
            if unresolved:
                raise ValueError(
                    "Guided global status declared experiment conflicts with an "
                    "incomplete preparation."
                )
            if lifecycle not in (
                "ACQUISITION_PENDING",
                "ACQUISITION_INCOMPLETE",
                "COMPARISON_UNAVAILABLE",
                "RESULT_INCONCLUSIVE",
                "RESULT_AVAILABLE",
            ):
                raise ValueError(
                    "Guided global status declared experiment is outside the "
                    "guided experiment lifecycle."
                )
            if declared_experiment_view.causality_status != "NOT_ESTABLISHED":
                raise ValueError(
                    "Guided global status cannot promote experiment causality."
                )
            result_outcomes = {
                "RESULT_INCONCLUSIVE": ("MIXED", "INCONCLUSIVE"),
                "RESULT_AVAILABLE": ("IMPROVED", "DEGRADED", "UNCHANGED"),
            }
            if lifecycle in result_outcomes:
                if (
                    any(
                        not isinstance(value, str)
                        or not value
                        or value != value.strip()
                        for value in (
                            declared_experiment_view.comparison_id,
                            declared_experiment_view.reference_experiment_id,
                        )
                    )
                ):
                    raise ValueError(
                        "Guided global status result requires one exact local "
                        "comparison."
                    )
                if (
                    declared_experiment_view.observed_result
                    not in result_outcomes[lifecycle]
                ):
                    raise ValueError(
                        "Guided global status result lifecycle and observed "
                        "outcome are inconsistent."
                    )
            expected_action_state, expected_action = {
                "ACQUISITION_PENDING": (
                    "COMPLETE_REQUIRED_ACQUISITION",
                    "Compléter l’acquisition requise déjà déclarée.",
                ),
                "ACQUISITION_INCOMPLETE": (
                    "COMPLETE_REQUIRED_ACQUISITION",
                    "Compléter l’acquisition requise déjà déclarée.",
                ),
                "COMPARISON_UNAVAILABLE": (
                    "RESTORE_COMPARABILITY",
                    "Rétablir la comparabilité à partir de la déclaration existante.",
                ),
                "RESULT_INCONCLUSIVE": (
                    "REVIEW_OBSERVED_RESULT",
                    "Examiner le résultat observé.",
                ),
                "RESULT_AVAILABLE": (
                    "REVIEW_OBSERVED_RESULT",
                    "Examiner le résultat observé.",
                ),
            }[lifecycle]
            if (
                declared_experiment_view.user_action_state != expected_action_state
                or declared_experiment_view.user_action != expected_action
            ):
                raise ValueError(
                    "Guided global status declared experiment lifecycle action "
                    "is inconsistent."
                )
            workflow = {
                "ACQUISITION_PENDING": (
                    "READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_PENDING"
                ),
                "ACQUISITION_INCOMPLETE": (
                    "READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_INCOMPLETE"
                ),
                "COMPARISON_UNAVAILABLE": (
                    "READY_PLAN_EXPERIMENT_ACQUISITION_COMPLETE_"
                    "COMPARISON_UNAVAILABLE"
                ),
                "RESULT_INCONCLUSIVE": (
                    "READY_PLAN_EXPERIMENT_RESULT_INCONCLUSIVE"
                ),
                "RESULT_AVAILABLE": "READY_PLAN_EXPERIMENT_RESULT_AVAILABLE",
            }[lifecycle]
            if lifecycle in ("RESULT_INCONCLUSIVE", "RESULT_AVAILABLE"):
                blocker_lines = (
                    "Résultat observé : "
                    + declared_experiment_view.observed_result
                    + ".",
                    "Aucune cause, correction permanente ou configuration "
                    "optimale n’est établie.",
                )
            else:
                blocker_lines = (
                    (
                        "Acquisition requise : LEFT, RIGHT et répétitions déclarées.",
                        "Mesures attendues : "
                        + ", ".join(plan.measurements_to_capture)
                        + ".",
                    )
                    if lifecycle in (
                        "ACQUISITION_PENDING",
                        "ACQUISITION_INCOMPLETE",
                    )
                    else (
                        "Acquisition complète selon la déclaration spécialisée ; "
                        "comparaison locale unique indisponible.",
                    )
                )
            return self._result(
                workflow,
                (
                    *current,
                    f"Préparation : {confirmation.confirmation_id}.",
                    f"Expérience déclarée : {declared_experiment_view.experiment_id}.",
                    f"Cycle de vie : {lifecycle}.",
                    *(
                        (
                            "Comparaison locale : "
                            + declared_experiment_view.comparison_id
                            + ".",
                        )
                        if lifecycle in result_outcomes
                        else ()
                    ),
                ),
                (
                    *validated,
                    "Contrat du plan, préparation et déclaration qualifiée "
                    "exactement reliés.",
                    *(
                        (
                            "Acquisition spécialisée complète.",
                            "Comparaison locale unique et comparable disponible.",
                        )
                        if lifecycle in result_outcomes
                        else ("Acquisition spécialisée complète.",)
                        if lifecycle == "COMPARISON_UNAVAILABLE"
                        else ()
                    ),
                ),
                blocker_lines,
                expected_action_state,
                expected_action,
            )
        if declared_candidates:
            if unresolved:
                raise ValueError(
                    "Guided global status declared experiment candidates conflict "
                    "with an incomplete preparation."
                )
            identifiers = ", ".join(candidate_ids)
            single = len(declared_candidates) == 1
            return self._result(
                (
                    "READY_PLAN_DECLARED_EXPERIMENT_SELECTION_REQUIRED"
                    if single
                    else "READY_PLAN_DECLARED_EXPERIMENT_SELECTION_AMBIGUOUS"
                ),
                (
                    *current,
                    f"Préparation : {confirmation.confirmation_id}.",
                    "Expériences qualifiées découvertes : "
                    + str(len(declared_candidates))
                    + ".",
                ),
                (
                    *validated,
                    "Préparation exactement résolue et entièrement confirmée.",
                    "Provenance des expériences qualifiées exactement reliée.",
                ),
                (
                    "Aucune expérience sélectionnée explicitement parmi : "
                    + identifiers
                    + ".",
                ),
                "SELECT_EXACT_DECLARED_EXPERIMENT",
                "Relancer cette vue avec --guided-declared-experiment "
                + (candidate_ids[0] if single else "EXPERIMENT_ID")
                + ".",
            )
        if unresolved:
            details = ", ".join(
                f"{value.code}={value.status.value}" for value in unresolved
            )
            if operational_record_preview is not None:
                if operational_record_preview.status == "DOCUMENTATION_INCOMPLETE":
                    missing = ", ".join(operational_record_preview.missing_fields)
                    return self._result(
                        "READY_PLAN_OPERATIONAL_DOCUMENTATION_INCOMPLETE",
                        (*current, f"Préparation : {confirmation.confirmation_id}."),
                        (*validated, "Préparation exactement résolue."),
                        (
                            "Documentation opérationnelle incomplète : " + missing + ".",
                            "Prérequis non confirmés : " + details + ".",
                        ),
                        "REVISE_OPERATIONAL_WORKSHEETS",
                        "Compléter uniquement les champs documentaires listés avec "
                        f"--revise-channel-isolation-records {recommended.plan_id}.",
                    )
                if operational_record_preview.status == "DOCUMENTATION_COMPLETE":
                    return self._result(
                        "READY_PLAN_OPERATIONAL_DOCUMENTATION_COMPLETE_PREPARATION_INCOMPLETE",
                        (*current, f"Préparation : {confirmation.confirmation_id}."),
                        (
                            *validated,
                            "Préparation exactement résolue.",
                            "Documentation opérationnelle complète et exactement reliée au plan.",
                        ),
                        ("Prérequis non confirmés : " + details + ".",),
                        "REVIEW_EXACT_PREPARATION",
                        "Consulter sans modification avec "
                        "--evidence-plan-preparation-view "
                        f"{confirmation.confirmation_id}.",
                    )
                raise ValueError(
                    "Guided global status operational documentation status is unknown: "
                    f"{operational_record_preview.status}."
                )
            return self._result(
                "READY_PLAN_PREPARATION_INCOMPLETE",
                (*current, f"Préparation : {confirmation.confirmation_id}."),
                (*validated, "Préparation exactement résolue."),
                ("Prérequis non confirmés : " + details + ".",),
                "REVIEW_EXACT_PREPARATION",
                "Consulter sans modification avec "
                "--evidence-plan-preparation-view "
                f"{confirmation.confirmation_id}.",
            )
        if declaration_readiness is not None:
            if declaration_readiness.plan_id != recommended.plan_id:
                raise ValueError(
                    "Guided global status declaration readiness targets another plan."
                )
            if declaration_readiness.confirmation_id != confirmation.confirmation_id:
                raise ValueError(
                    "Guided global status declaration readiness targets another "
                    "preparation."
                )
            statuses = ", ".join(declaration_readiness.statuses)
            command = shlex.join((
                "python",
                "-m",
                "acousticbrain.commands.declare_evidence_plan_experiment",
                str(measurement_root.resolve()),
                "--plan-id",
                recommended.plan_id,
                "--experiment",
                declaration_readiness.experiment_id,
                "--reference",
                declaration_readiness.reference_experiment_id,
                "--preparation-registry",
                str(preparation_registry_path.resolve()),
                "--preparation",
                confirmation.confirmation_id,
            ))
            return self._result(
                "READY_PLAN_DECLARATION_READY",
                (
                    *current,
                    f"Préparation : {confirmation.confirmation_id}.",
                    f"Référence : {declaration_readiness.reference_experiment_id}.",
                    f"Nouvelle expérience : {declaration_readiness.experiment_id}.",
                ),
                (
                    *validated,
                    "Tous les prérequis ont été déclarés CONFIRMED par l’utilisateur.",
                    "Préflight de déclaration : " + statuses + ".",
                ),
                (
                    "Aucun blocage contractuel de déclaration ; la création reste "
                    "une opération explicite séparée.",
                ),
                "DECLARE_EXPERIMENT_SEPARATELY",
                "Déclarer séparément le contrat expérimental avec : " + command,
            )
        return self._result(
            "READY_PLAN_PREPARATION_CONFIRMED",
            (*current, f"Préparation : {confirmation.confirmation_id}."),
            (*validated, "Tous les prérequis ont été déclarés CONFIRMED par l’utilisateur."),
            ("Aucun blocage contractuel de préparation ; la déclaration reste séparée.",),
            "RUN_DECLARATION_READINESS",
            "Exécuter --channel-isolation-declaration-readiness "
            f"{recommended.plan_id} avec une référence et un nouvel identifiant explicites.",
        )

    @staticmethod
    def _result(state, current, validated, blockers, action_state, action):
        return PresentedGuidedGlobalStatus(
            workflow_state=state,
            current_state_lines=current,
            validated_step_lines=validated,
            blocker_lines=blockers,
            user_action_state=action_state,
            user_action=action,
            scientific_boundary_lines=(
                "Cette vue réutilise des décisions existantes et ne produit aucune nouvelle analyse.",
                "Cette vue ne vérifie aucune préparation indépendamment, ne déclare "
                "et n’exécute aucune expérience.",
            ),
        )


class GuidedGlobalStatusConsoleReporter:
    def print(self, view):
        print("GUIDED STATUS")
        print()
        print("État actuel")
        print(view.workflow_state)
        print("\n".join(view.current_state_lines))
        print()
        print("Dernière étape validée")
        print("\n".join(view.validated_step_lines))
        print()
        print("Blocage actuel")
        print("\n".join(view.blocker_lines))
        print()
        print("Action utilisateur")
        print(view.user_action)
        print()
        print("Frontière scientifique")
        print("\n".join(view.scientific_boundary_lines))
        print(f"Causality status: {view.causality_status}")
