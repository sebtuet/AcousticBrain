from dataclasses import dataclass

from acousticbrain.application import evidence_acquisition_plan_fingerprint
from acousticbrain.models import EvidencePlanPreparationRegistry

from .evidence_plan_user_view_presenter import EvidencePlanUserViewPresenter


@dataclass(frozen=True)
class PresentedEvidencePlanPreparationUserView:
    confirmation_id: str
    plan_id: str
    plan_label: str
    declaration_lines: tuple[str, ...]
    prerequisite_lines: tuple[str, ...]
    decision_lines: tuple[str, ...]
    user_action_state: str
    user_action: str
    scientific_boundary_lines: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"


class EvidencePlanPreparationUserViewPresenter:
    """Read-only projection of one exact persisted preparation declaration."""

    def present(self, registry, plans, confirmation_id):
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("EvidencePlanPreparationRegistry is required.")
        matches = tuple(
            value for value in registry.records
            if value.confirmation_input.confirmation_id == confirmation_id
        )
        if not matches:
            raise ValueError(
                f"Unknown evidence-plan preparation confirmation_id: {confirmation_id}"
            )
        if len(matches) != 1:
            raise ValueError(
                f"Ambiguous evidence-plan preparation confirmation_id: {confirmation_id}"
            )
        record = matches[0]
        plan_matches = tuple(
            value for value in plans
            if value.plan_id == record.confirmation_input.plan_id
        )
        if not plan_matches:
            raise ValueError(
                "Preparation view plan unavailable: "
                + record.confirmation_input.plan_id
            )
        if len(plan_matches) != 1:
            raise ValueError(
                "Preparation view plan ambiguous: "
                + record.confirmation_input.plan_id
            )
        plan = plan_matches[0]
        if evidence_acquisition_plan_fingerprint(plan) != (
            record.confirmation_input.plan_contract_fingerprint
        ):
            raise ValueError(
                "PREPARATION_VIEW_PLAN_CONTRACT_FINGERPRINT_MISMATCH: "
                + plan.plan_id
            )
        value = record.confirmation_input
        action_state, action = self._action(value.prerequisites)
        return PresentedEvidencePlanPreparationUserView(
            confirmation_id=value.confirmation_id,
            plan_id=value.plan_id,
            plan_label=EvidencePlanUserViewPresenter._user_label(plan),
            declaration_lines=(
                "Source de déclaration : " + value.declaration_source,
                "Empreinte du plan : " + value.plan_contract_fingerprint,
                "Note utilisateur : " + (
                    value.user_note if value.user_note is not None else "absente"
                ),
            ),
            prerequisite_lines=tuple(
                f"{item.code} : {item.status.value}"
                for item in sorted(value.prerequisites, key=lambda item: item.code)
            ) or ("Aucun prérequis déclaré.",),
            decision_lines=(
                record.resolution_status.value,
                record.declaration_status.value,
                (
                    record.all_prerequisites_status.value
                    if record.all_prerequisites_status is not None
                    else "ALL_PREREQUISITES_USER_CONFIRMED : indisponible"
                ),
            ),
            user_action_state=action_state,
            user_action=action,
            scientific_boundary_lines=(
                "Les statuts sont des déclarations utilisateur ; aucun "
                "prérequis n’a été vérifié indépendamment.",
                "Aucune expérience n’a été déclarée ou exécutée par cette vue.",
                "Le plan, le registre, les mesures et les manifests restent "
                "inchangés.",
            ),
        )

    @staticmethod
    def _action(prerequisites):
        unknown = tuple(sorted(
            value.code for value in prerequisites if value.status.value == "UNKNOWN"
        ))
        if unknown:
            return (
                "REVIEW_UNKNOWN_PREREQUISITES",
                "Déterminer ces prérequis ou les laisser explicitement UNKNOWN : "
                + ", ".join(unknown) + ".",
            )
        unavailable = tuple(sorted(
            value.code
            for value in prerequisites
            if value.status.value == "NOT_CONFIRMED"
        ))
        if unavailable:
            return (
                "REVIEW_NOT_CONFIRMED_PREREQUISITES",
                "Satisfaire opérationnellement ces prérequis ou conserver la "
                "déclaration inchangée : " + ", ".join(unavailable) + ".",
            )
        return (
            "NO_PREPARATION_STATUS_ACTION",
            "Aucune action sur les statuts de préparation n’est requise.",
        )


class EvidencePlanPreparationUserViewConsoleReporter:
    def print(self, view):
        print(f"EVIDENCE PLAN PREPARATION VIEW — {view.confirmation_id}")
        print()
        print(view.plan_label)
        print(f"Plan : {view.plan_id}")
        print()
        print("Préparation déclarée")
        print("\n".join(view.declaration_lines))
        print()
        print("Statuts des prérequis")
        print("\n".join(view.prerequisite_lines))
        print()
        print("Décisions enregistrées")
        print("\n".join(view.decision_lines))
        print()
        print("Action utilisateur")
        print(view.user_action)
        print()
        print("Frontière scientifique")
        print("\n".join(view.scientific_boundary_lines))
        print(f"Causality status: {view.causality_status}")
