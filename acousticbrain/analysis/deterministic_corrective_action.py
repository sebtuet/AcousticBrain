from dataclasses import replace

from acousticbrain.models import (
    CorrectiveActionApplicability,
    CorrectiveActionCategory,
    CorrectiveActionJustification,
    CorrectiveActionPriority,
    CorrectiveActionTraceabilityStatus,
    CorrectiveActionType,
    DeterministicCorrectiveAction,
    DeterministicCorrectiveActionSynthesis,
    DeterministicReasoningConclusion,
)


class DeterministicCorrectiveActionEngine:
    """Maps bounded PR-055 conclusions to declarative, non-executing actions."""

    RULE_ID = "MAP_BOUNDED_REASONING_TO_DECLARATIVE_ACTION_V1"

    def synthesize(
        self,
        reasoning_synthesis,
        *,
        protocols_by_target=None,
        plans_by_target=None,
        tested_action_ids=(),
        invalidated_action_ids=(),
    ):
        protocols_by_target = protocols_by_target or {}
        plans_by_target = plans_by_target or {}
        generated = []
        for reasoning in reasoning_synthesis.reasonings:
            action = self._build(
                reasoning,
                protocols=tuple(protocols_by_target.get(self._target(reasoning), ())),
                plans=tuple(plans_by_target.get(self._target(reasoning), ())),
            )
            if action is not None:
                generated.append(action)
        deduplicated = self._deduplicate(generated)
        return DeterministicCorrectiveActionSynthesis(
            tuple(
                self._apply_history(
                    action,
                    tested_action_ids=set(tested_action_ids),
                    invalidated_action_ids=set(invalidated_action_ids),
                )
                for action in deduplicated
            )
        )

    @staticmethod
    def _target(reasoning):
        return reasoning.compatible_hypothesis_ids[0]

    def _build(self, reasoning, *, protocols, plans):
        target = self._target(reasoning)
        conclusion = reasoning.conclusion
        if conclusion is DeterministicReasoningConclusion.SUPPORTED:
            action_type = CorrectiveActionType.RUN_CONTROLLED_MEASUREMENT
            category = CorrectiveActionCategory.ROOM_INTERACTION_TEST
            applicability = (
                CorrectiveActionApplicability.APPLICABLE
                if protocols or plans
                else CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
            )
            priority = (
                CorrectiveActionPriority.HIGH
                if applicability is CorrectiveActionApplicability.APPLICABLE
                else CorrectiveActionPriority.BLOCKED
            )
            missing = () if protocols or plans else ("compatible_protocol_or_plan_id",)
            objective = "Evaluate the supported conclusion with an existing controlled contract."
        elif conclusion is DeterministicReasoningConclusion.PARTIALLY_SUPPORTED:
            action_type = CorrectiveActionType.RUN_CONTROLLED_MEASUREMENT
            category = CorrectiveActionCategory.MEASUREMENT
            applicability = (
                CorrectiveActionApplicability.CONDITIONALLY_APPLICABLE
                if protocols or plans
                else CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
            )
            priority = CorrectiveActionPriority.MEDIUM if protocols or plans else CorrectiveActionPriority.BLOCKED
            missing = () if protocols or plans else ("compatible_protocol_or_plan_id",)
            objective = "Collect controlled evidence without treating partial support as a correction."
        elif conclusion is DeterministicReasoningConclusion.NON_DISCRIMINATED:
            action_type = CorrectiveActionType.RUN_CONTROLLED_MEASUREMENT
            category = CorrectiveActionCategory.MEASUREMENT
            applicability = (
                CorrectiveActionApplicability.CONDITIONALLY_APPLICABLE
                if protocols or plans
                else CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
            )
            priority = (
                CorrectiveActionPriority.REQUIRED_FOR_DISCRIMINATION
                if protocols or plans
                else CorrectiveActionPriority.BLOCKED
            )
            missing = () if protocols or plans else ("compatible_protocol_or_plan_id",)
            objective = "Collect evidence required to discriminate the existing conclusion."
        elif conclusion is DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE:
            action_type = CorrectiveActionType.DEFER_ACTION_PENDING_EVIDENCE
            category = CorrectiveActionCategory.NO_ACTION
            applicability = CorrectiveActionApplicability.BLOCKED_BY_CONTRADICTION
            priority = CorrectiveActionPriority.BLOCKED
            missing = ()
            objective = "Keep corrective intervention blocked while contradictions remain unresolved."
        elif conclusion is DeterministicReasoningConclusion.INSUFFICIENT_EVIDENCE:
            action_type = CorrectiveActionType.DEFER_ACTION_PENDING_EVIDENCE
            category = CorrectiveActionCategory.DOCUMENTATION
            applicability = CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS
            priority = CorrectiveActionPriority.DEFERRED
            missing = ("additional_supporting_observation",)
            objective = "Defer corrective intervention pending additional structured evidence."
        elif conclusion is DeterministicReasoningConclusion.CONTRADICTED:
            action_type = CorrectiveActionType.PRESERVE_CURRENT_CONFIGURATION
            category = CorrectiveActionCategory.NO_ACTION
            applicability = CorrectiveActionApplicability.NO_ACTION_REQUIRED
            priority = CorrectiveActionPriority.LOW
            missing = ()
            objective = "Do not apply a correction based on the contradicted conclusion."
        else:
            return None

        action_id = f"ACTION_{action_type.value}_{target}"
        known_parameters = tuple(
            (f"compatible_protocol_id.{index}", value)
            for index, value in enumerate(protocols, start=1)
        ) + tuple(
            (f"compatible_plan_id.{index}", value)
            for index, value in enumerate(plans, start=1)
        )
        contradictions = (
            reasoning.contradicting_evidence
            if applicability
            is CorrectiveActionApplicability.BLOCKED_BY_CONTRADICTION
            else ()
        )
        if applicability is CorrectiveActionApplicability.BLOCKED_BY_CONTRADICTION and not contradictions:
            contradictions = ("reasoning.conclusion.CONTRADICTORY_EVIDENCE",)
        confidence = reasoning.confidence
        return DeterministicCorrectiveAction(
            action_id=action_id,
            category=category,
            action_type=action_type,
            target_id=target,
            title=f"Declarative action for {target}",
            objective=objective,
            description=(
                f"Action derived from {reasoning.reasoning_id}; it does not execute "
                "or create an experiment."
            ),
            applicability=applicability,
            priority=priority,
            confidence=confidence,
            source_confidence_ceiling=confidence,
            source_reasoning_ids=(reasoning.reasoning_id,),
            source_observation_ids=reasoning.observation_ids,
            upstream_source_ids=reasoning.upstream_source_ids,
            justifications=(
                CorrectiveActionJustification(
                    justification_id=f"justification.{action_id.lower()}",
                    rule_id=self.RULE_ID,
                    reasoning_id=reasoning.reasoning_id,
                    conclusion_code=conclusion.value,
                    statement=(
                        f"Rule {self.RULE_ID} maps {conclusion.value} to "
                        f"{action_type.value}."
                    ),
                ),
            ),
            preconditions=("Use only referenced existing protocols or plans.",),
            known_parameters=known_parameters,
            derivable_parameters=(),
            required_missing_parameters=missing,
            forbidden_to_invent_parameters=(
                "listening_position_distance",
                "speaker_position_distance",
                "channel_orientation_angle",
                "eq_frequency",
                "eq_gain",
                "eq_q",
                "treatment_dimensions",
            ),
            known_risks=("Uncontrolled variables can invalidate comparison.",),
            constraints=(
                "Do not invent geometry, distance, angle, frequency, gain or Q.",
                "Do not execute or create an experiment from this declaration.",
            ),
            success_criteria=("Referenced evidence becomes discriminating and traceable.",),
            stop_criteria=("Stop if the referenced contract is absent or incompatible.",),
            contradictions=tuple(dict.fromkeys(contradictions)),
            limitations=reasoning.limitations,
            traceability_status=CorrectiveActionTraceabilityStatus.COMPLETE,
            compatible_protocol_ids=protocols,
            compatible_plan_ids=plans,
        )

    @staticmethod
    def _deduplicate(actions):
        merged = {}
        order = []
        for action in actions:
            key = (
                action.action_type,
                action.target_id,
                action.compatible_protocol_ids,
                action.compatible_plan_ids,
            )
            if key not in merged:
                merged[key] = action
                order.append(key)
                continue
            previous = merged[key]
            confidences = tuple(
                value
                for value in (previous.confidence, action.confidence)
                if value is not None
            )
            confidence = min(confidences) if confidences else None
            merged[key] = replace(
                previous,
                confidence=confidence,
                source_confidence_ceiling=confidence,
                source_reasoning_ids=tuple(
                    dict.fromkeys((*previous.source_reasoning_ids, *action.source_reasoning_ids))
                ),
                source_observation_ids=tuple(
                    dict.fromkeys((*previous.source_observation_ids, *action.source_observation_ids))
                ),
                upstream_source_ids=tuple(
                    dict.fromkeys((*previous.upstream_source_ids, *action.upstream_source_ids))
                ),
                justifications=tuple(
                    dict.fromkeys((*previous.justifications, *action.justifications))
                ),
                contradictions=tuple(
                    dict.fromkeys((*previous.contradictions, *action.contradictions))
                ),
                limitations=tuple(
                    dict.fromkeys((*previous.limitations, *action.limitations))
                ),
            )
        return tuple(merged[key] for key in order)

    @staticmethod
    def _apply_history(action, *, tested_action_ids, invalidated_action_ids):
        if action.action_id in invalidated_action_ids:
            return replace(
                action,
                applicability=CorrectiveActionApplicability.BLOCKED_BY_HISTORY,
                priority=CorrectiveActionPriority.BLOCKED,
                contradictions=tuple(
                    dict.fromkeys((*action.contradictions, "history.invalidated_action"))
                ),
                required_missing_parameters=(),
            )
        if action.action_id in tested_action_ids:
            return replace(
                action,
                applicability=CorrectiveActionApplicability.ALREADY_TESTED,
                priority=CorrectiveActionPriority.LOW,
                required_missing_parameters=(),
                contradictions=(),
            )
        return action
