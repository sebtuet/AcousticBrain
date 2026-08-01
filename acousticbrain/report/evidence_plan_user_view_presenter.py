from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedEvidencePlanUserView:
    plan_id: str
    user_label: str
    plan_status: str
    intention_lines: tuple[str, ...]
    blocker_lines: tuple[str, ...]
    preparation_lines: tuple[str, ...]
    user_action_state: str
    user_action: str
    scientific_boundary_lines: tuple[str, ...]
    causality_status: str


@dataclass(frozen=True)
class PresentedEvidencePlanOverview:
    plans: tuple[PresentedEvidencePlanUserView, ...]
    causality_status: str = "NOT_ESTABLISHED"


class EvidencePlanUserViewPresenter:
    """Read-only explanation of one exact existing evidence plan."""

    MISSING_REFERENCE = "compatible_protocol_or_plan_id"
    SUBJECT_LABELS = {
        "ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING": (
            "Asymétrie entre les enceintes et la pièce"
        ),
        "MODAL_BASS_PERSISTENCE_REASONING": "Persistance modale dans le grave",
        "DOMINANT_EARLY_REFLECTION_INTERACTION_REASONING": (
            "Interaction avec une réflexion précoce dominante"
        ),
        "SBIR_PLACEMENT_INTERACTION_REASONING": "Interaction SBIR et placement",
    }
    TEST_TYPE_LABELS = {
        "CHANNEL_ISOLATION": "vérifier séparément les canaux",
        "COMPARATIVE_MEASUREMENT": "comparer des mesures contrôlées",
        "PARAMETER_COMPLETION": "compléter un prérequis documentaire",
        "ADDITIONAL_OBSERVATION": "acquérir une observation supplémentaire",
        "REPEAT_MEASUREMENT": "vérifier la répétabilité d’une mesure",
        "CONTROLLED_SPEAKER_DISPLACEMENT": (
            "tester un déplacement temporaire d’enceinte"
        ),
        "CONTROLLED_MICROPHONE_DISPLACEMENT": (
            "tester un déplacement temporaire du microphone"
        ),
        "GEOMETRY_ACQUISITION": "documenter la géométrie",
        "PROTOCOL_EXECUTION": "exécuter un protocole déclaré",
    }

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
            user_label=self._user_label(plan),
            plan_status=plan.status,
            intention_lines=(
                plan.objective,
                "Type d’essai : " + plan.test_type,
                "Mesures prévues : "
                + (", ".join(plan.measurements_to_capture) or "indisponibles"),
            ),
            blocker_lines=self._blocker_lines(plan, factors),
            preparation_lines=self._preparation_lines(plan),
            user_action_state=action_state,
            user_action=user_action,
            scientific_boundary_lines=self._scientific_boundary_lines(plan),
            causality_status="NOT_ESTABLISHED",
        )

    @classmethod
    def _user_label(cls, plan):
        subject = cls.SUBJECT_LABELS.get(
            plan.reasoning_id,
            "Plan d’acquisition de preuves",
        )
        operation = cls.TEST_TYPE_LABELS.get(
            plan.test_type,
            "objectif expérimental déclaré",
        )
        return f"{subject} — {operation}"

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

    @staticmethod
    def _preparation_lines(plan):
        if plan.status != "READY":
            return (
                "Préparation indisponible : le plan doit rester BLOCKED tant "
                "que son contrat n’est pas complet.",
            )

        def values(label, items, *, empty="aucun déclaré"):
            return f"{label} : " + (", ".join(items) if items else empty)

        return (
            values("Prérequis à confirmer", plan.required_inputs),
            values("Variables modifiées", plan.independent_variables),
            values("Variables contrôlées", plan.controlled_variables),
            values("Mesures à réaliser", plan.measurements_to_capture),
            values("Observations attendues", plan.expected_observations),
            *tuple(
                f"Procédure {index} : {instruction}"
                for index, instruction in enumerate(plan.instructions, start=1)
            ),
            values("Critères de réussite", plan.success_criteria),
            values("Critères d’échec", plan.failure_criteria),
            values("Limites scientifiques", plan.limitations),
        )

    @staticmethod
    def _scientific_boundary_lines(plan):
        common = (
            "Le plan source reste immuable.",
            "Aucune compatibilité, causalité, correction permanente ou "
            "configuration optimale n’est déduite.",
        )
        if plan.status == "READY":
            return (*common,
                "READY signifie seulement que le contrat de préparation est "
                "complet ; les prérequis ne sont pas vérifiés et l’expérience "
                "n’est ni déclarée ni exécutée.",
            )
        return (*common,
            "Une référence absente doit être établie par une source "
            "scientifique structurée ou une expertise acoustique.",
        )

    @classmethod
    def _user_action(cls, plan, factors, action):
        if plan.status == "READY":
            prerequisites = ", ".join(plan.required_inputs)
            return (
                "VERIFY_DECLARED_PREREQUISITES",
                (
                    "Vérifier explicitement les prérequis déclarés avant toute "
                    "déclaration : " + prerequisites + "."
                    if prerequisites
                    else "Relire et confirmer la procédure déclarée avant toute "
                    "déclaration."
                ),
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
        print(view.user_label)
        print()
        print("Intention")
        print("\n".join(view.intention_lines))
        print()
        print("État du plan")
        print(view.plan_status)
        print("\n".join(view.blocker_lines))
        print()
        print("Préparation déclarée")
        print("\n".join(view.preparation_lines))
        print()
        print("Action utilisateur")
        print(view.user_action)
        print()
        print("Frontière scientifique")
        print("\n".join(view.scientific_boundary_lines))
        print(f"Causality status: {view.causality_status}")


class EvidencePlanOverviewPresenter:
    """Projects every plan without ranking or selecting a candidate."""

    def present(self, report):
        plans = tuple(getattr(
            getattr(report, "evidence_acquisition_plans", None), "plans", ()
        ))
        identities = tuple(value.plan_id for value in plans)
        if len(identities) != len(set(identities)):
            duplicates = ", ".join(sorted(
                value for value in set(identities) if identities.count(value) > 1
            ))
            raise ValueError(f"Ambiguous evidence plan_id: {duplicates}")
        presenter = EvidencePlanUserViewPresenter()
        return PresentedEvidencePlanOverview(plans=tuple(
            presenter.present(report, plan_id)
            for plan_id in sorted(identities)
        ))


class EvidencePlanOverviewConsoleReporter:
    def print(self, report):
        overview = report.evidence_plan_overview
        print("EVIDENCE PLAN OVERVIEW")
        print()
        if not overview.plans:
            print("Aucun plan disponible.")
        for index, view in enumerate(overview.plans):
            if index:
                print()
                print("------------------------------------------------------------")
                print()
            print(view.plan_id)
            print(f"Lecture utilisateur : {view.user_label}")
            print(f"Statut : {view.plan_status}")
            print(f"Objectif contractuel : {view.intention_lines[0]}")
            print(f"Action utilisateur : {view.user_action}")
        print()
        print("Aucun plan n’est sélectionné ou recommandé par cette vue.")
        print(f"Causality status: {overview.causality_status}")
