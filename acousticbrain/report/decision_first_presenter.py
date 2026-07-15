from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedDecisionFirstReport:
    objective: str
    verdict: str
    comparison_context: tuple[str, ...]
    action_status: str
    action: str
    target: str | None
    direction: str | None
    amplitude: str | None
    tested_variable: str | None
    unchanged_items: tuple[str, ...]
    required_measurements: tuple[str, ...]
    action_reasons: tuple[str, ...]
    unblock_steps: tuple[str, ...]
    established_facts: tuple[str, ...]
    active_limits: tuple[str, ...]
    verdict_confidence: str
    action_confidence: str
    causality_status: str
    source_codes: tuple[str, ...]


@dataclass(frozen=True)
class _DecisionAction:
    objective: str
    action: str
    target: str | None
    direction: str | None
    amplitude: str | None
    tested_variable: str | None
    unchanged_items: tuple[str, ...]
    required_measurements: tuple[str, ...]
    source_codes: tuple[str, ...]


class DecisionFirstReportPresenter:
    """Projette la prochaine décision sans enrichir le raisonnement existant."""

    MAXIMUM_FACTS = 3
    MAXIMUM_LIMITS = 2
    REQUIRED_MEASUREMENTS = ("L", "R", "L+R")

    OBJECTIVE_LABELS = {
        "DISCRIMINATE_CHANNEL_AND_ROOM_ASYMMETRY": (
            "Comprendre l’origine de l’asymétrie entre les enceintes."
        ),
        "DISCRIMINATE_LOCAL_AND_GLOBAL_BASS_DECAY": (
            "Vérifier l’influence du placement sur la persistance du grave."
        ),
        "DISCRIMINATE_CANDIDATE_EARLY_REFLECTION_SURFACE": (
            "Comprendre l’origine d’une réflexion précoce dominante."
        ),
        "DISCRIMINATE_SBIR_PLACEMENT_INTERACTION": (
            "Vérifier l’influence du placement des enceintes sur le grave."
        ),
    }
    RECOMMENDATION_OBJECTIVES = {
        "CHECK_STEREO_PLACEMENT": "Améliorer la symétrie entre les enceintes.",
        "TEST_SPEAKER_DISTANCE": (
            "Vérifier l’influence de la distance enceinte-surface sur le grave."
        ),
        "MEASURE_MULTIPLE_POSITIONS": (
            "Vérifier l’influence du point d’écoute sur le grave."
        ),
        "CHECK_EARLY_REFLECTION_SYMMETRY": (
            "Comprendre l’asymétrie des réflexions précoces."
        ),
        "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS": (
            "Comprendre l’origine des réflexions précoces dominantes."
        ),
        "VERIFY_DOMINANT_EARLY_REFLECTION": (
            "Comprendre l’origine d’une réflexion précoce dominante."
        ),
    }
    RECOMMENDATION_ACTIONS = {
        "CHECK_STEREO_PLACEMENT": "Vérifiez le placement relatif des deux enceintes.",
        "TEST_SPEAKER_DISTANCE": (
            "Réalisez le test de distance enceinte-surface déjà recommandé."
        ),
        "MEASURE_MULTIPLE_POSITIONS": (
            "Réalisez les mesures aux positions d’écoute déjà définies."
        ),
        "CHECK_EARLY_REFLECTION_SYMMETRY": (
            "Comparez les conditions de réflexion des canaux gauche et droit."
        ),
        "INVESTIGATE_DOMINANT_EARLY_REFLECTIONS": (
            "Examinez les événements précoces dominants déjà identifiés."
        ),
    }
    VARIABLE_LABELS = {
        "LOUDSPEAKER_POSITION": "la position d’une enceinte",
        "LISTENING_POSITION": "la position d’écoute",
        "MICROPHONE_POSITION": "la position du microphone",
        "SURFACE_MASKING_STATE": "l’état de masquage de la surface ciblée",
        "TEMPORARY_MASK_STATE": "l’état de masquage de la surface ciblée",
        "MEASUREMENT_ACQUISITION": "l’acquisition de mesure",
        "SIGNAL_CHAIN_ASSIGNMENT": "l’affectation de la chaîne du signal",
    }
    CONTROL_LABELS = {
        "MICROPHONE_POSITION": "la position du microphone",
        "MEASUREMENT_LEVEL": "le volume de mesure",
        "LOUDSPEAKER_ORIENTATION": "l’orientation des enceintes",
        "LOUDSPEAKER_POSITION": "la position des enceintes",
        "OTHER_LOUDSPEAKER_POSITIONS": "la position de l’autre enceinte",
        "SIGNAL_CHAIN_ASSIGNMENT": "les branchements et canaux",
        "ROOM_CONFIGURATION": "la configuration de la pièce",
    }

    def present(self, report):
        comparison = self._latest_comparison(report)
        verdict, verdict_confidence = self._verdict(comparison)
        comparison_context = self._comparison_context(comparison)
        undeclared = self._undeclared_change(comparison)
        deferred = self._deferred_messages(report)

        action, action_status = self._select_action(report)
        action_reasons = self._action_reasons(
            report,
            action_status,
            undeclared,
            deferred,
        )
        unblock_steps = self._unblock_steps(
            report,
            action_status,
            undeclared,
            deferred,
        )
        facts = self._established_facts(report, comparison)
        limits = self._active_limits(comparison, undeclared, deferred)

        if action is None:
            objective = "Aucun objectif expérimental prioritaire n’est actuellement établi."
            action_text = self._unavailable_action_text(action_status)
            target = direction = amplitude = tested_variable = None
            unchanged_items = required_measurements = ()
            source_codes = self._comparison_sources(comparison)
        else:
            objective = action.objective
            action_text = action.action
            target = action.target
            direction = action.direction
            amplitude = action.amplitude
            tested_variable = action.tested_variable
            unchanged_items = action.unchanged_items
            required_measurements = action.required_measurements
            source_codes = tuple(dict.fromkeys(
                (*self._comparison_sources(comparison), *action.source_codes)
            ))

        return PresentedDecisionFirstReport(
            objective=objective,
            verdict=verdict,
            comparison_context=comparison_context,
            action_status=action_status,
            action=action_text,
            target=target,
            direction=direction,
            amplitude=amplitude,
            tested_variable=tested_variable,
            unchanged_items=unchanged_items,
            required_measurements=required_measurements,
            action_reasons=action_reasons,
            unblock_steps=unblock_steps,
            established_facts=facts,
            active_limits=limits,
            verdict_confidence=verdict_confidence,
            action_confidence=(
                "Explication possible" if action is not None else "Non établi"
            ),
            causality_status="NOT_ESTABLISHED",
            source_codes=source_codes,
        )

    @staticmethod
    def _latest_comparison(report):
        analysis = report.experiment_comparison
        if analysis is None or not analysis.local_comparisons:
            return None
        return analysis.local_comparisons[-1]

    @classmethod
    def _verdict(cls, comparison):
        if comparison is None or comparison.eligibility != "COMPARABLE":
            return (
                "La dernière expérience ne peut pas être comparée de manière fiable.",
                "Non établi",
            )
        labels = {
            "IMPROVED": (
                "La dernière expérience montre une amélioration mesurable dans "
                "le périmètre testé."
            ),
            "DEGRADED": (
                "La dernière expérience montre une dégradation mesurable dans "
                "le périmètre testé."
            ),
            "MIXED": (
                "La dernière expérience présente des améliorations et des "
                "dégradations. Aucun verdict global simple n’est possible."
            ),
            "UNCHANGED": "Aucun changement acoustique significatif n’a été observé.",
            "INCONCLUSIVE": (
                "Les mesures ne permettent pas de conclure sur la dernière expérience."
            ),
        }
        status = comparison.acoustic_outcome
        if status not in labels and comparison.outcome == "INCONCLUSIVE":
            status = "INCONCLUSIVE"
        return labels.get(
            status,
            "Les mesures ne permettent pas de conclure sur la dernière expérience.",
        ), "Établi par les mesures"

    @staticmethod
    def _comparison_context(comparison):
        if comparison is None:
            return ("Aucune comparaison d’expérience n’est disponible.",)
        protocol = comparison.source_protocol_id or "non déclaré"
        return (
            (
                f"Comparaison : {comparison.before_experiment_id} → "
                f"{comparison.after_experiment_id}."
            ),
            f"Protocole : {protocol}.",
            "Le verdict porte uniquement sur le périmètre mesuré.",
        )

    @staticmethod
    def _undeclared_change(comparison):
        if comparison is None:
            return False
        return (
            comparison.source_protocol_id is None
            or comparison.source_hypothesis_code is None
        )

    def _select_action(self, report):
        declared = self._declared_actions(report)
        if len(declared) > 1:
            return None, "TIED"
        if declared:
            return declared[0], "AVAILABLE"

        planning = report.experiment_planning
        candidate = planning.recommended_candidate if planning is not None else None
        if candidate is not None and candidate.eligible:
            return self._candidate_action(candidate), "AVAILABLE"

        recommendations = tuple(
            item
            for item in report.recommendations
            if self._enum_value(item.status) == "ACTIVE"
        )
        if recommendations:
            maximum = max(int(item.priority) for item in recommendations)
            top = tuple(
                item for item in recommendations if int(item.priority) == maximum
            )
            if len(top) > 1:
                return None, "TIED"
            return self._recommendation_action(top[0]), "AVAILABLE"

        return None, "UNAVAILABLE"

    def _declared_actions(self, report):
        declarations = tuple(
            item
            for item in report.controlled_reflection_experiment_declarations
            if item.status == "PLANNED"
        )
        planning = report.controlled_reflection_verification_planning
        proposals = planning.proposals if planning is not None else ()
        by_id = {item.proposal_id: item for item in proposals}
        return tuple(
            self._reflection_action(by_id[item.proposal_id])
            for item in declarations
            if item.proposal_id in by_id
        )

    def _candidate_action(self, candidate):
        objective = self.OBJECTIVE_LABELS.get(
            candidate.objective_code,
            "Réaliser l’expérience contrôlée déjà planifiée.",
        )
        parameters = candidate.parameters
        changed = candidate.changed_variable_codes
        target = None
        direction = self._direction(parameters)
        amplitude = self._amplitude(parameters)

        if "LOUDSPEAKER_POSITION" in changed:
            speaker_id = parameters.get("speaker_id")
            if isinstance(speaker_id, str) and speaker_id.strip():
                target = self._speaker_label(speaker_id)
        elif set(changed).intersection({"SURFACE_MASKING_STATE", "TEMPORARY_MASK_STATE"}):
            surface = parameters.get("surface")
            if isinstance(surface, str) and surface.strip():
                target = f"la surface {surface}"
        elif "LISTENING_POSITION" in changed:
            target = "la position d’écoute"

        action = (
            f"Modifiez uniquement {target}."
            if target is not None
            else (
                "Une piste a été identifiée, mais le déplacement exact "
                "n’est pas encore déterminé."
            )
        )
        return _DecisionAction(
            objective=objective,
            action=action,
            target=target,
            direction=direction,
            amplitude=amplitude,
            tested_variable=self._tested_variable(changed),
            unchanged_items=self._unchanged_items(candidate.controlled_variable_codes),
            required_measurements=self.REQUIRED_MEASUREMENTS,
            source_codes=(candidate.candidate_id, candidate.source_protocol_id),
        )

    def _reflection_action(self, proposal):
        target = (
            f"la région {proposal.target_id}"
            if proposal.target_kind == "REGION"
            else f"la surface {proposal.target_id}"
        )
        return _DecisionAction(
            objective="Comprendre l’origine d’une réflexion précoce dominante.",
            action=f"Testez uniquement le masquage temporaire de {target}.",
            target=target,
            direction=None,
            amplitude=None,
            tested_variable=self._tested_variable(proposal.changed_variable_codes),
            unchanged_items=self._unchanged_items(
                proposal.controlled_variable_codes
            ),
            required_measurements=self.REQUIRED_MEASUREMENTS,
            source_codes=(proposal.proposal_id, proposal.source_candidate_id),
        )

    def _recommendation_action(self, recommendation):
        objective = self.RECOMMENDATION_OBJECTIVES.get(
            recommendation.code,
            "Examiner la recommandation structurée actuellement prioritaire.",
        )
        action = self.RECOMMENDATION_ACTIONS.get(
            recommendation.code,
            (
                "Une piste a été identifiée, mais le déplacement exact "
                "n’est pas encore déterminé."
            ),
        )
        return _DecisionAction(
            objective=objective,
            action=action,
            target=None,
            direction=None,
            amplitude=None,
            tested_variable=None,
            unchanged_items=(),
            required_measurements=(),
            source_codes=(recommendation.code,),
        )

    def _action_reasons(self, report, status, undeclared, deferred):
        if status == "AVAILABLE":
            return ()
        reasons = []
        if undeclared:
            reasons.append(
                "La variable testée, ou l’absence de changement volontaire, "
                "n’a pas été déclarée."
            )
        planning = report.experiment_planning
        if planning is not None and planning.recommended_candidate is None:
            reasons.append("Aucune expérience contrôlée n’est actuellement éligible.")
        if status == "TIED":
            reasons.append(
                "Plusieurs actions restent également prioritaires et ne "
                "peuvent pas être départagées."
            )
        reasons.extend(deferred[:1])
        return tuple(dict.fromkeys(reasons))

    @staticmethod
    def _unavailable_action_text(status):
        if status == "TIED":
            return (
                "Plusieurs actions restent également prioritaires. AcousticBrain "
                "ne peut pas en sélectionner une seule sans information supplémentaire."
            )
        return "Aucun déplacement fiable ne peut être recommandé actuellement."

    def _unblock_steps(self, report, status, undeclared, deferred):
        if status == "AVAILABLE":
            return ()
        steps = []
        if undeclared:
            steps.append(
                "Déclarez si la configuration devait rester inchangée ou quelle "
                "variable était testée pendant la dernière expérience."
            )
        if deferred:
            steps.append(
                "Vous pouvez décider de reprendre l’investigation actuellement différée."
            )
        planning = report.experiment_planning
        if (
            not steps
            and planning is not None
            and planning.recommended_candidate is None
        ):
            steps.append(
                "Complétez les prérequis indiqués dans la planification technique."
            )
        if not steps and status == "TIED":
            steps.append(
                "Fournissez une information permettant de départager les actions existantes."
            )
        return tuple(steps)

    def _established_facts(self, report, comparison):
        values = []
        if comparison is not None:
            values.extend(comparison.observation_labels)
        quality = next(
            (item for item in report.diagnostics if item.title == "Qualité des mesures"),
            None,
        )
        if quality is not None:
            values.append(quality.conclusion or quality.message)
        priority = self._priority(report)
        if (
            priority is not None
            and priority.diagnostic.evidence_level.value != "HYPOTHESIS"
        ):
            diagnostic = priority.diagnostic
            values.extend(
                diagnostic.observations
                or [diagnostic.conclusion or diagnostic.message]
            )
        return tuple(dict.fromkeys(
            item for item in values if item
        ))[: self.MAXIMUM_FACTS]

    def _active_limits(self, comparison, undeclared, deferred):
        values = []
        if undeclared:
            values.append(
                "AcousticBrain ne sait pas formellement quelle variable était "
                "testée ni si la configuration devait rester inchangée."
            )
        if comparison is None or comparison.eligibility != "COMPARABLE":
            values.append("La dernière comparaison n’est pas établie.")
        elif comparison.acoustic_outcome == "MIXED":
            values.append("La dernière expérience présente des effets contradictoires.")
        elif comparison.outcome == "INCONCLUSIVE":
            values.append("Le résultat de la dernière expérience reste inconclusif.")
        values.extend(deferred[:1])
        return tuple(dict.fromkeys(values))[: self.MAXIMUM_LIMITS]

    @staticmethod
    def _deferred_messages(report):
        causal = report.causal_discrimination
        decisions = causal.discrimination_decisions if causal is not None else ()
        messages = []
        for item in decisions:
            if item.status == "DEFERRED":
                messages.append(
                    "Une investigation utile est actuellement différée par décision utilisateur."
                )
        if not messages:
            for item in report.recommendations:
                if DecisionFirstReportPresenter._enum_value(item.status) == "DEFERRED":
                    messages.append(
                        "Une investigation utile est actuellement différée "
                        "par décision utilisateur."
                    )
                    break
        return tuple(messages)

    @staticmethod
    def _priority(report):
        analysis = report.diagnostic_priority
        if analysis is None or not analysis.prioritized_diagnostics:
            return None
        return analysis.prioritized_diagnostics[0]

    @staticmethod
    def _comparison_sources(comparison):
        if comparison is None:
            return ()
        return tuple(
            item
            for item in (
                comparison.trace_id,
                comparison.source_protocol_id,
                comparison.source_hypothesis_code,
            )
            if item
        )

    @classmethod
    def _tested_variable(cls, codes):
        labels = tuple(cls.VARIABLE_LABELS[code] for code in codes if code in cls.VARIABLE_LABELS)
        return labels[0] if len(labels) == 1 else None

    @classmethod
    def _unchanged_items(cls, codes):
        defaults = ("la position du microphone", "le volume de mesure")
        values = (
            *defaults,
            *(cls.CONTROL_LABELS[code] for code in codes if code in cls.CONTROL_LABELS),
        )
        return tuple(dict.fromkeys(values))

    @staticmethod
    def _speaker_label(value):
        return {
            "LEFT": "l’enceinte gauche",
            "RIGHT": "l’enceinte droite",
            "STEREO": "les deux enceintes",
        }.get(value.upper(), f"l’enceinte {value}")

    @staticmethod
    def _direction(parameters):
        for key in ("movement_direction", "proposed_direction", "direction"):
            value = parameters.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _amplitude(parameters):
        value = parameters.get("proposed_displacement_m")
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value <= 0
        ):
            return None
        return f"{value * 100:g} cm"

    @staticmethod
    def _enum_value(value):
        return getattr(value, "value", value)
