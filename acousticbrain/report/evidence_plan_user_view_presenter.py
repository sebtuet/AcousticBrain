from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedEvidencePlanUserView:
    plan_id: str
    plan_status: str
    intention_lines: tuple[str, ...]
    blocker_lines: tuple[str, ...]
    user_action_state: str
    user_action: str
    scientific_boundary_lines: tuple[str, ...]
    causality_status: str


class EvidencePlanUserViewPresenter:
    """Read-only explanation of one exact existing evidence plan."""

    MISSING_REFERENCE = "compatible_protocol_or_plan_id"

    def present(self, report, plan_id):
        plans = tuple(
            value for value in getattr(
                getattr(report, "evidence_acquisition_plans", None),
                "plans",
                (),
            )
            if value.plan_id == plan_id
        )
        if not plans:
            raise ValueError(f"Unknown evidence plan_id: {plan_id}")
        if len(plans) != 1:
            raise ValueError(f"Ambiguous evidence plan_id: {plan_id}")
        plan = plans[0]
        factors = self._factors(report, plan.blocking_factor_ids)
        action = self._action(report, plan.corrective_action_id)
        action_state, user_action = self._user_action(plan, factors, action)
        return PresentedEvidencePlanUserView(
            plan_id=plan.plan_id,
            plan_status=plan.status,
            intention_lines=(
                plan.objective,
                "Type d’essai : " + plan.test_type,
                "Mesures prévues : "
                + (", ".join(plan.measurements_to_capture) or "indisponibles"),
            ),
            blocker_lines=self._blocker_lines(plan, factors),
            user_action_state=action_state,
            user_action=user_action,
            scientific_boundary_lines=(
                "Le plan source reste immuable et son statut n’est jamais promu.",
                "Aucune compatibilité, causalité, correction permanente ou "
                "configuration optimale n’est déduite.",
                "Une référence absente doit être établie par une source "
                "scientifique structurée ou une expertise acoustique.",
            ),
            causality_status="NOT_ESTABLISHED",
        )

    @staticmethod
    def _factors(report, expected_ids):
        all_factors = tuple(
            factor
            for weight in getattr(
                getattr(report, "deterministic_evidence_weighting", None),
                "weights",
                (),
            )
            for factor in weight.blocking_factors
            if factor.factor_id in expected_ids
        )
        identities = tuple(value.factor_id for value in all_factors)
        if len(identities) != len(set(identities)):
            duplicates = ", ".join(sorted(
                value for value in set(identities) if identities.count(value) > 1
            ))
            raise ValueError(f"Ambiguous evidence blocking_factor_id: {duplicates}")
        return tuple(sorted(all_factors, key=lambda value: value.factor_id))

    @staticmethod
    def _action(report, action_id):
        actions = tuple(
            value for value in getattr(
                getattr(report, "deterministic_corrective_actions", None),
                "actions",
                (),
            )
            if value.action_id == action_id
        )
        if len(actions) > 1:
            raise ValueError(f"Ambiguous corrective action_id: {action_id}")
        return actions[0] if actions else None

    @classmethod
    def _blocker_lines(cls, plan, factors):
        if plan.status == "READY":
            return ("Aucun blocage de complétion : le plan est déjà READY.",)
        if not plan.blocking_factor_ids:
            return ("Facteurs bloquants indisponibles.",)
        resolved = {value.factor_id: value for value in factors}
        lines = []
        for identifier in plan.blocking_factor_ids:
            factor = resolved.get(identifier)
            if factor is None:
                lines.append(f"{identifier} : détail indisponible.")
            else:
                missing = ", ".join(factor.source_object_ids) or "non précisé"
                lines.append(
                    f"{factor.code} — élément requis : {missing}. "
                    f"{factor.justification}"
                )
        return tuple(lines)

    @classmethod
    def _user_action(cls, plan, factors, action):
        if plan.status == "READY":
            return (
                "NO_COMPLETION_ACTION",
                "Aucune action de complétion : ce plan est déjà READY.",
            )
        missing_reference = (
            cls.MISSING_REFERENCE in plan.required_inputs
            or any(
                cls.MISSING_REFERENCE in factor.source_object_ids
                for factor in factors
            )
        )
        compatible = () if action is None else tuple(sorted((
            *action.compatible_protocol_ids,
            *action.compatible_plan_ids,
        )))
        if missing_reference and compatible:
            return (
                "SUBMIT_STRUCTURED_COMPLETION_INPUT",
                "Soumettre une entrée structurée désignant exactement une "
                "référence déjà déclarée compatible : " + ", ".join(compatible),
            )
        if missing_reference:
            return (
                "EXPERT_VALIDATION_REQUIRED",
                "Aucune action sûre pour vous : faire établir une référence "
                "compatible par une source scientifique ou un acousticien.",
            )
        return (
            "NO_SAFE_USER_ACTION",
            "Aucune action sûre actuellement : conserver le plan bloqué.",
        )


class EvidencePlanUserViewConsoleReporter:
    def print(self, report):
        view = report.evidence_plan_user_view
        print(f"EVIDENCE PLAN VIEW — {view.plan_id}")
        print()
        print("Intention")
        print("\n".join(view.intention_lines))
        print()
        print("Pourquoi le plan est bloqué")
        print(view.plan_status)
        print("\n".join(view.blocker_lines))
        print()
        print("Action utilisateur")
        print(view.user_action)
        print()
        print("Frontière scientifique")
        print("\n".join(view.scientific_boundary_lines))
        print(f"Causality status: {view.causality_status}")
