from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedActionOrientedPositioning:
    status: str
    situation: str
    certainty: str
    measured_facts: tuple[str, ...]
    possible_explanations: tuple[str, ...]
    action: str
    target: str | None
    direction: str | None
    amplitude: str | None
    unchanged_items: tuple[str, ...]
    required_measurements: tuple[str, ...]
    comparison_criteria: tuple[str, ...]
    previous_result: str | None
    missing_information: tuple[str, ...]
    limitations: tuple[str, ...]
    causality_status: str
    source_codes: tuple[str, ...]


@dataclass(frozen=True)
class _Action:
    action: str
    target: str
    direction: str | None
    amplitude: str | None
    controlled_variable_codes: tuple[str, ...]
    observable_fact_codes: tuple[str, ...]
    source_codes: tuple[str, ...]
    causality_status: str = "NOT_ESTABLISHED"


class ActionOrientedPositioningPresenter:
    """Traduit les décisions existantes sans ajouter de raisonnement acoustique."""

    REQUIRED_MEASUREMENTS = ("L", "R", "L+R")
    DEFAULT_LIMITATIONS = (
        "La causalité n’est pas établie.",
        "Une seule variable doit être modifiée.",
        "Une nouvelle mesure est nécessaire.",
        "Le résultat peut être favorable, défavorable ou inconclusif.",
    )

    def present(self, report):
        priority = self._priority(report)
        situation = self._situation(priority)
        certainty = self._certainty(priority)
        facts = self._facts(priority)
        previous_result = self._previous_result(report)

        positioning = getattr(report, "loudspeaker_positioning_experiment", None)
        if positioning is not None:
            proposal = getattr(positioning, "proposal", None)
            if proposal is None:
                return self._unavailable_positioning(
                    positioning,
                    situation,
                    certainty,
                    facts,
                    previous_result,
                    priority,
                )
            action = self._positioning_action(proposal)
            return PresentedActionOrientedPositioning(
                status="ACTION_AVAILABLE",
                situation=situation,
                certainty=certainty,
                measured_facts=facts,
                possible_explanations=proposal.rationale,
                action=action.action,
                target=action.target,
                direction=action.direction,
                amplitude=action.amplitude,
                unchanged_items=self._unchanged_items(
                    action.controlled_variable_codes,
                    action.target,
                ),
                required_measurements=self.REQUIRED_MEASUREMENTS,
                comparison_criteria=self._comparison_criteria(
                    action.observable_fact_codes
                ),
                previous_result=previous_result,
                missing_information=(),
                limitations=(
                    "Il s’agit d’un pas expérimental réversible, pas d’une position optimale prédite.",
                    *self.DEFAULT_LIMITATIONS,
                ),
                causality_status=action.causality_status,
                source_codes=action.source_codes,
            )

        action = self._planned_action(report)
        if action is None:
            action = self._declared_reflection_action(report)

        top_tie = self._top_tie(report)
        proposals = self._reflection_proposals(report)
        if action is None and (top_tie or len(proposals) > 1):
            return PresentedActionOrientedPositioning(
                status="MULTIPLE_PLAUSIBLE_PATHS",
                situation=situation,
                certainty=certainty,
                measured_facts=facts,
                possible_explanations=self._possible_explanations(priority),
                action=(
                    "Plusieurs explications restent également plausibles. "
                    "Une mesure supplémentaire est nécessaire avant de proposer "
                    "un déplacement."
                ),
                target=None,
                direction=None,
                amplitude=None,
                unchanged_items=(),
                required_measurements=(),
                comparison_criteria=(),
                previous_result=previous_result,
                missing_information=(
                    "Une piste unique déjà départagée par les analyses existantes.",
                ),
                limitations=self.DEFAULT_LIMITATIONS,
                causality_status="NOT_ESTABLISHED",
                source_codes=self._priority_source_codes(priority),
            )

        if action is None:
            missing_information = (
                ("Une déclaration d’expérience planifiée pour la proposition existante.",)
                if len(proposals) == 1
                else ("Une cible et une variable à modifier déjà déterminées.",)
            )
            return PresentedActionOrientedPositioning(
                status="INSUFFICIENT_DATA",
                situation=situation,
                certainty=certainty,
                measured_facts=facts,
                possible_explanations=self._possible_explanations(priority),
                action=(
                    "Aucune expérience de positionnement fiable ne peut être "
                    "proposée avec les données actuelles."
                ),
                target=None,
                direction=None,
                amplitude=None,
                unchanged_items=(),
                required_measurements=(),
                comparison_criteria=(),
                previous_result=previous_result,
                missing_information=missing_information,
                limitations=self.DEFAULT_LIMITATIONS,
                causality_status="NOT_ESTABLISHED",
                source_codes=self._priority_source_codes(priority),
            )

        return PresentedActionOrientedPositioning(
            status="ACTION_AVAILABLE",
            situation=situation,
            certainty=certainty,
            measured_facts=facts,
            possible_explanations=self._possible_explanations(priority),
            action=action.action,
            target=action.target,
            direction=action.direction,
            amplitude=action.amplitude,
            unchanged_items=self._unchanged_items(
                action.controlled_variable_codes,
                action.target,
            ),
            required_measurements=self.REQUIRED_MEASUREMENTS,
            comparison_criteria=self._comparison_criteria(
                action.observable_fact_codes
            ),
            previous_result=previous_result,
            missing_information=(),
            limitations=self.DEFAULT_LIMITATIONS,
            causality_status=action.causality_status,
            source_codes=tuple(dict.fromkeys(
                (*action.source_codes, *self._priority_source_codes(priority))
            )),
        )

    def _unavailable_positioning(
        self, analysis, situation, certainty, facts, previous_result, priority
    ):
        status = getattr(analysis.proposal_status, "value", analysis.proposal_status)
        messages = {
            "MISSING_DIRECTION": (
                "Une expérience de positionnement semble pertinente. Cependant, "
                "les observations disponibles ne permettent pas de choisir entre "
                "un déplacement vers l’avant, l’arrière, l’intérieur ou l’extérieur "
                "sans formuler une hypothèse non démontrée. Aucune direction n’est "
                "donc proposée."
            ),
            "MISSING_GEOMETRY": (
                "La géométrie disponible ne permet pas de définir honnêtement "
                "un déplacement d’enceinte."
            ),
            "AMBIGUOUS": (
                "Plusieurs expériences de positionnement restent également "
                "plausibles. AcousticBrain ne peut pas en sélectionner une seule."
            ),
            "BLOCKED_BY_USER_DECISION": (
                "L’expérience de positionnement correspondante est différée par "
                "une décision utilisateur."
            ),
        }
        limitations = self.DEFAULT_LIMITATIONS
        if status == "MISSING_DIRECTION":
            limitations = tuple(
                item
                for item in self.DEFAULT_LIMITATIONS
                if item != "Une nouvelle mesure est nécessaire."
            ) + (
                "Les mesures REW disponibles ne sont pas la cause de ce blocage.",
            )
        return PresentedActionOrientedPositioning(
            status=status,
            situation=situation,
            certainty=certainty,
            measured_facts=facts,
            possible_explanations=self._possible_explanations(priority),
            action=messages.get(
                status,
                "Aucune expérience de positionnement déterministe n’est éligible avec les données actuelles.",
            ),
            target=None,
            direction=None,
            amplitude=None,
            unchanged_items=(),
            required_measurements=(),
            comparison_criteria=(),
            previous_result=previous_result,
            missing_information=self._user_missing_information(
                analysis.blocking_reason_codes
            ),
            limitations=limitations,
            causality_status="NOT_ESTABLISHED",
            source_codes=tuple(analysis.considered_source_ids),
        )

    @staticmethod
    def _user_missing_information(reason_codes):
        labels = {
            "EXPLICIT_MOVEMENT_DIRECTION_MISSING": (
                "Des critères scientifiques permettant de choisir une direction "
                "de test sans supposer une cause non démontrée."
            ),
            "SOURCE_GEOMETRY_MISSING": (
                "Une description géométrique suffisamment précise pour relier "
                "le test à la configuration de la pièce."
            ),
            "LOUDSPEAKER_TARGET_AMBIGUOUS": (
                "Une enceinte cible définie sans ambiguïté."
            ),
            "SOURCE_NOT_REVERSIBLE": (
                "Un protocole de déplacement court et réversible."
            ),
            "L_R_STEREO_MEASUREMENTS_UNAVAILABLE": (
                "Les mesures L, R et L+R nécessaires à la comparaison."
            ),
            "OBSERVABLE_FACTS_MISSING": (
                "Des indicateurs existants permettant de comparer le test."
            ),
            "EQUAL_PRIORITY_POSITIONING_SOURCES": (
                "Un critère permettant de départager les expériences possibles."
            ),
            "SOURCE_DEFERRED_BY_USER": (
                "La reprise de l’investigation précédemment différée."
            ),
            "NO_ACTIVE_LOUDSPEAKER_POSITIONING_SOURCE": (
                "Une piste active concernant explicitement le placement des enceintes."
            ),
        }
        return tuple(dict.fromkeys(
            labels.get(
                code,
                "Les critères scientifiques nécessaires pour définir un test précis.",
            )
            for code in reason_codes
        ))

    @classmethod
    def _positioning_action(cls, proposal):
        target_code = getattr(proposal.target, "value", proposal.target)
        direction_code = getattr(
            proposal.movement_direction, "value", proposal.movement_direction
        )
        target = {
            "LEFT_SPEAKER": "l’enceinte gauche",
            "RIGHT_SPEAKER": "l’enceinte droite",
            "BOTH_SPEAKERS": "les deux enceintes",
        }[target_code]
        movement_target = (
            "des deux enceintes"
            if target_code == "BOTH_SPEAKERS"
            else f"de {target}"
        )
        direction = {
            "FORWARD": "vers l’avant",
            "BACKWARD": "vers l’arrière",
            "INWARD": "vers l’intérieur",
            "OUTWARD": "vers l’extérieur",
        }[direction_code]
        amplitude = f"{proposal.step_distance_m * 100:g} cm"
        return _Action(
            action=(
                f"Testez un déplacement réversible {movement_target} de {amplitude} "
                f"{direction}."
            ),
            target=target,
            direction=direction,
            amplitude=amplitude,
            controlled_variable_codes=proposal.controlled_variables,
            observable_fact_codes=proposal.expected_observables,
            source_codes=(proposal.proposal_id, *proposal.source_recommendation_ids),
            causality_status=proposal.causality_status,
        )

    @staticmethod
    def _priority(report):
        analysis = report.diagnostic_priority
        if analysis is None or not analysis.prioritized_diagnostics:
            return None
        return analysis.prioritized_diagnostics[0]

    @staticmethod
    def _top_tie(report):
        analysis = report.diagnostic_priority
        if analysis is None:
            return False
        return any(
            len(group) > 1 and group[0].rank == 1
            for group in analysis.tie_groups
        )

    @staticmethod
    def _situation(priority):
        if priority is None:
            return "Aucun problème prioritaire n’est évaluable avec les données disponibles."
        diagnostic = priority.diagnostic
        labels = {
            "Symétrie stéréo": (
                "Un déséquilibre entre les enceintes gauche et droite mérite "
                "d’être vérifié."
            ),
            "Réponse dans le grave": (
                "Une anomalie du grave mérite d’être vérifiée."
            ),
            "Creux importants": (
                "Un creux de la réponse fréquentielle mérite d’être vérifié."
            ),
            "Décroissance dans le grave": (
                "La stabilité du grave mérite d’être vérifiée."
            ),
            "Réflexions temporelles précoces": (
                "Une réflexion précoce constitue une piste à vérifier."
            ),
        }
        return labels.get(
            diagnostic.title,
            diagnostic.conclusion or diagnostic.message,
        )

    @staticmethod
    def _certainty(priority):
        if priority is None:
            return "Non évaluable avec les mesures disponibles"
        level = priority.diagnostic.evidence_level.value
        return {
            "OBSERVED": "Observation mesurée",
            "CONFIRMED": "Observation mesurée",
            "CALCULATED": "Observation calculée à interpréter",
            "HYPOTHESIS": "Explication possible — à vérifier",
        }.get(level, "Résultat inconclusif")

    @staticmethod
    def _facts(priority):
        if priority is None:
            return ()
        diagnostic = priority.diagnostic
        if diagnostic.observations:
            return tuple(diagnostic.observations[:3])
        return tuple(
            item for item in (diagnostic.conclusion or diagnostic.message,) if item
        )

    @staticmethod
    def _possible_explanations(priority):
        if priority is None:
            return ()
        return tuple(priority.diagnostic.causes)

    @staticmethod
    def _priority_source_codes(priority):
        if priority is None:
            return ()
        return (f"diagnostic.{priority.diagnostic.title}",)

    def _planned_action(self, report):
        planning = report.experiment_planning
        candidate = planning.recommended_candidate if planning is not None else None
        if candidate is None:
            return None
        changed = set(candidate.changed_variable_codes)
        parameters = candidate.parameters
        source_codes = tuple(dict.fromkeys((
            candidate.candidate_id,
            candidate.source_protocol_id,
            *(candidate.observable_fact_codes),
        )))

        if "LOUDSPEAKER_POSITION" in changed:
            speaker_id = parameters.get("speaker_id")
            if not isinstance(speaker_id, str) or not speaker_id.strip():
                return None
            target = self._speaker_label(speaker_id)
            return _Action(
                action=f"Effectuez un déplacement contrôlé de {target}.",
                target=target,
                direction=self._direction(parameters),
                amplitude=self._amplitude(parameters),
                controlled_variable_codes=candidate.controlled_variable_codes,
                observable_fact_codes=candidate.observable_fact_codes,
                source_codes=source_codes,
            )

        if changed.intersection({"SURFACE_MASKING_STATE", "TEMPORARY_MASK_STATE"}):
            surface = parameters.get("surface")
            if not isinstance(surface, str) or not surface.strip():
                return None
            target = f"la surface {surface}"
            return _Action(
                action=f"Modifiez uniquement l’état de masquage temporaire de {target}.",
                target=target,
                direction=None,
                amplitude=None,
                controlled_variable_codes=candidate.controlled_variable_codes,
                observable_fact_codes=candidate.observable_fact_codes,
                source_codes=source_codes,
            )

        return None

    def _declared_reflection_action(self, report):
        declarations = tuple(
            item
            for item in report.controlled_reflection_experiment_declarations
            if item.status == "PLANNED"
        )
        if len(declarations) != 1:
            return None
        proposal = next(
            (
                item
                for item in self._reflection_proposals(report)
                if item.proposal_id == declarations[0].proposal_id
            ),
            None,
        )
        return self._reflection_action(proposal) if proposal is not None else None

    @staticmethod
    def _reflection_proposals(report):
        planning = report.controlled_reflection_verification_planning
        return planning.proposals if planning is not None else ()

    @staticmethod
    def _reflection_action(proposal):
        target = (
            f"la région {proposal.target_id}"
            if proposal.target_kind == "REGION"
            else f"la surface {proposal.target_id}"
        )
        return _Action(
            action=f"Testez uniquement le masquage temporaire de {target}.",
            target=target,
            direction=None,
            amplitude=None,
            controlled_variable_codes=proposal.controlled_variable_codes,
            observable_fact_codes=proposal.observable_fact_codes,
            source_codes=(
                proposal.proposal_id,
                proposal.source_candidate_id,
                proposal.observed_event_id,
            ),
            causality_status=proposal.causality_status,
        )

    @staticmethod
    def _speaker_label(value):
        labels = {
            "LEFT": "l’enceinte gauche",
            "RIGHT": "l’enceinte droite",
            "STEREO": "les deux enceintes",
        }
        return labels.get(value.upper(), f"l’enceinte {value}")

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
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            return None
        centimeters = value * 100.0
        return f"{centimeters:g} cm"

    @classmethod
    def _unchanged_items(cls, codes, target):
        labels = {
            "MICROPHONE_POSITION": "la position du microphone",
            "MEASUREMENT_LEVEL": "le volume de mesure",
            "LOUDSPEAKER_ORIENTATION": "l’orientation des enceintes",
            "SIGNAL_CHAIN_ASSIGNMENT": "les branchements et canaux",
            "ROOM_CONFIGURATION": "les traitements et la configuration de la pièce",
            "LOUDSPEAKER_POSITION": "la position des enceintes",
            "OTHER_LOUDSPEAKER_POSITIONS": "la position de l’autre enceinte",
            "LISTENING_POSITION": "la position d’écoute",
            "REW_MEASUREMENT_PARAMETERS": "les paramètres de mesure REW",
            "LOUDSPEAKER_SEPARATION": "l’écartement entre les enceintes",
            "LOUDSPEAKER_PAIR_SYMMETRY": (
                "un déplacement identique et symétrique des deux enceintes"
            ),
        }
        values = [
            "la position du microphone",
            "le volume de mesure",
        ]
        values.extend(labels[code] for code in codes if code in labels)
        return tuple(
            item for item in dict.fromkeys(values)
            if item != target
        )

    @staticmethod
    def _comparison_criteria(codes):
        criteria = []
        for code in codes:
            lowered = code.lower()
            if "stereo" in lowered or "spatial" in lowered or "asymmetry" in lowered:
                label = "l’équilibre mesuré entre les enceintes gauche et droite"
            elif "reflection" in lowered or lowered.startswith("etc"):
                label = "le niveau et le délai de la réflexion ciblée"
            elif "bass" in lowered or "decay" in lowered or "sbir" in lowered:
                label = "l’évolution mesurable du grave"
            else:
                continue
            if label not in criteria:
                criteria.append(label)
        return tuple(criteria)

    @staticmethod
    def _previous_result(report):
        comparison = (
            report.controlled_reflection_experiment_comparisons[-1]
            if report.controlled_reflection_experiment_comparisons
            else None
        )
        update = (
            report.controlled_reflection_hypothesis_status_updates[-1]
            if report.controlled_reflection_hypothesis_status_updates
            else None
        )
        if comparison is None and update is None:
            return None

        labels = {
            "NOT_COMPARABLE": (
                "Les mesures disponibles ne permettent pas de comparer ce test."
            ),
            "INCONCLUSIVE": (
                "Le déplacement testé n’a pas produit un résultat suffisamment "
                "clair. Ne concluez pas que la position est meilleure ou moins bonne."
            ),
            "NO_OBSERVABLE_CHANGE": (
                "Aucun changement mesurable n’a été observé dans le périmètre du test."
            ),
            "CHANGE_OBSERVED": (
                "Un changement mesurable a été observé après le test. Cela soutient "
                "l’intérêt de poursuivre ce test, sans établir encore une causalité."
            ),
        }
        result = labels.get(comparison.status) if comparison is not None else None
        if update is not None:
            if update.status == "SUPPORTED_BY_OBSERVATION":
                result = (
                    "L’observation soutient la piste testée, sans établir de causalité."
                )
            elif update.status == "NOT_SUPPORTED_BY_OBSERVATION":
                result = (
                    "L’observation ne soutient pas la piste testée; aucune causalité "
                    "ne peut être conclue."
                )
        return result
