from dataclasses import dataclass
from pathlib import Path
import shlex

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
        unresolved = tuple(
            value for value in confirmation.prerequisites
            if value.status is not EvidencePlanPrerequisiteStatus.CONFIRMED
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
                "Aucune préparation n’est vérifiée indépendamment et aucune expérience n’est déclarée ou exécutée.",
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
