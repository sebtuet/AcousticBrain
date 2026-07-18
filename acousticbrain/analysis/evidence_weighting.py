from acousticbrain.models import (
    CorrectiveActionApplicability,
    DeterministicEvidenceWeight,
    DeterministicEvidenceWeightingSynthesis,
    DeterministicReasoningConclusion,
    EvidenceBlockingFactor,
    EvidenceDimension,
    EvidenceDimensionCeiling,
    EvidenceWeightLevel,
    EvidenceWeightRuleApplication,
    WeightedActionApplicability,
    WeightedObjectReference,
    WeightedObjectType,
)


class DeterministicEvidenceWeightingEngine:
    """Qualifies existing evidence without creating or changing scientific objects."""

    BASE_RULE = "QUALIFY_EXISTING_EVIDENCE_VECTOR_V1"
    CONTRADICTION_RULE = "CAP_CONSISTENCY_ON_CONTRADICTION_V1"
    DISCRIMINATION_RULE = "CAP_POWER_WHEN_NOT_DISCRIMINATED_V1"
    PARAMETERS_RULE = "CAP_COMPLETENESS_ON_MISSING_PARAMETERS_V1"
    APPLICABILITY_RULE = "PROJECT_EXISTING_ACTION_APPLICABILITY_V1"

    _APPLICABILITY = {
        CorrectiveActionApplicability.APPLICABLE: WeightedActionApplicability.APPLICABLE,
        CorrectiveActionApplicability.CONDITIONALLY_APPLICABLE: (
            WeightedActionApplicability.CONDITIONALLY_APPLICABLE
        ),
        CorrectiveActionApplicability.BLOCKED_BY_CONTRADICTION: (
            WeightedActionApplicability.BLOCKED
        ),
        CorrectiveActionApplicability.BLOCKED_BY_MISSING_PARAMETERS: (
            WeightedActionApplicability.BLOCKED
        ),
        CorrectiveActionApplicability.BLOCKED_BY_HISTORY: (
            WeightedActionApplicability.BLOCKED
        ),
        CorrectiveActionApplicability.ALREADY_TESTED: (
            WeightedActionApplicability.ALREADY_TESTED
        ),
        CorrectiveActionApplicability.NOT_SUPPORTED: (
            WeightedActionApplicability.NOT_SUPPORTED
        ),
        CorrectiveActionApplicability.NO_ACTION_REQUIRED: (
            WeightedActionApplicability.NO_ACTION_REQUIRED
        ),
    }

    def weigh(self, observation_synthesis, reasoning_synthesis, action_synthesis):
        observations = {
            value.observation_id: value for value in observation_synthesis.observations
        }
        reasonings = {
            value.reasoning_id: value for value in reasoning_synthesis.reasonings
        }
        weights = tuple(
            self._weigh_action(action, observations, reasonings)
            for action in action_synthesis.actions
        )
        return DeterministicEvidenceWeightingSynthesis(weights)

    def _weigh_action(self, action, observations, reasonings):
        try:
            source_reasonings = tuple(reasonings[value] for value in action.source_reasoning_ids)
            source_observations = tuple(
                observations[value] for value in action.source_observation_ids
            )
        except KeyError as error:
            raise ValueError(
                f"Evidence weighting references an unknown upstream object: {error.args[0]}"
            ) from error
        reasoning_observations = {
            value for reasoning in source_reasonings for value in reasoning.observation_ids
        }
        if not set(action.source_observation_ids).issubset(reasoning_observations):
            raise ValueError("Action observations must be referenced by source reasonings.")

        supporting = self._unique(
            value
            for source in (*source_observations, *source_reasonings)
            for value in source.supporting_evidence
        )
        contradicting = self._unique(
            value
            for source in (*source_observations, *source_reasonings)
            for value in source.contradicting_evidence
        )
        contradicting = self._unique((*contradicting, *action.contradictions))
        limitations = self._unique(
            value
            for source in (*source_observations, *source_reasonings, action)
            for value in source.limitations
        )

        evidence_strength = self._strength(source_observations, supporting)
        source_consistency = (
            EvidenceWeightLevel.LOW if contradicting else EvidenceWeightLevel.HIGH
        )
        discriminative_power = self._discrimination(source_reasonings)
        parameter_completeness = self._parameters(action)
        applicability = self._APPLICABILITY[action.applicability]
        blocking_factors = self._blocking_factors(action, source_reasonings, contradicting)
        ceilings = self._ceilings(
            action,
            source_reasonings,
            contradicting,
            source_consistency,
            discriminative_power,
            parameter_completeness,
        )
        source_ids = (
            *action.source_reasoning_ids,
            *action.source_observation_ids,
            action.action_id,
        )
        applications = (
            EvidenceWeightRuleApplication(
                application_id=f"application.{action.action_id.lower()}.base",
                rule_id=self.BASE_RULE,
                condition_codes=("EXISTING_TRACE_COMPLETE",),
                affected_dimensions=(
                    EvidenceDimension.EVIDENCE_STRENGTH,
                    EvidenceDimension.SOURCE_CONSISTENCY,
                    EvidenceDimension.DISCRIMINATIVE_POWER,
                    EvidenceDimension.PARAMETER_COMPLETENESS,
                ),
                source_object_ids=source_ids,
                justification="Qualify only evidence and state already referenced upstream.",
                limitations=("No global score or probabilistic inference is produced.",),
            ),
            EvidenceWeightRuleApplication(
                application_id=f"application.{action.action_id.lower()}.applicability",
                rule_id=self.APPLICABILITY_RULE,
                condition_codes=("PR056_ACTION_STATUS_PRESENT",),
                affected_dimensions=(EvidenceDimension.PARAMETER_COMPLETENESS,),
                source_object_ids=(action.action_id,),
                justification="Project the existing action status without authorizing or blocking it.",
                limitations=("Applicability remains authoritative in PR-056.",),
            ),
            *(
                EvidenceWeightRuleApplication(
                    application_id=f"application.{value.ceiling_id}",
                    rule_id=value.rule_id,
                    condition_codes=(self._ceiling_condition(value.dimension),),
                    affected_dimensions=(value.dimension,),
                    source_object_ids=source_ids,
                    justification=value.justification,
                    limitations=("The ceiling affects only its named dimension.",),
                )
                for value in ceilings
            ),
        )
        references = (
            WeightedObjectReference(WeightedObjectType.ACTION, action.action_id),
            *(WeightedObjectReference(WeightedObjectType.REASONING, value) for value in action.source_reasoning_ids),
            *(WeightedObjectReference(WeightedObjectType.OBSERVATION, value) for value in action.source_observation_ids),
        )
        return DeterministicEvidenceWeight(
            weight_id=f"EVIDENCE_WEIGHT_{action.action_id}",
            evidence_strength=evidence_strength,
            source_consistency=source_consistency,
            discriminative_power=discriminative_power,
            parameter_completeness=parameter_completeness,
            action_applicability=applicability,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            limitations=limitations,
            blocking_factors=blocking_factors,
            weighted_object_references=references,
            reasoning_references=action.source_reasoning_ids,
            observation_references=action.source_observation_ids,
            action_references=(action.action_id,),
            ceilings=ceilings,
            rule_applications=applications,
        )

    @staticmethod
    def _strength(observations, supporting):
        if not supporting:
            return EvidenceWeightLevel.UNAVAILABLE
        if len(observations) < 2:
            return EvidenceWeightLevel.LOW
        if any(value.confidence is None for value in observations):
            return EvidenceWeightLevel.MEDIUM
        return EvidenceWeightLevel.HIGH

    @staticmethod
    def _discrimination(reasonings):
        conclusions = {value.conclusion for value in reasonings}
        if conclusions & {
            DeterministicReasoningConclusion.NON_DISCRIMINATED,
            DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE,
            DeterministicReasoningConclusion.INSUFFICIENT_EVIDENCE,
        }:
            return EvidenceWeightLevel.LOW
        if DeterministicReasoningConclusion.PARTIALLY_SUPPORTED in conclusions:
            return EvidenceWeightLevel.MEDIUM
        return EvidenceWeightLevel.HIGH

    @staticmethod
    def _parameters(action):
        if action.required_missing_parameters:
            return EvidenceWeightLevel.LOW
        if action.derivable_parameters:
            return EvidenceWeightLevel.MEDIUM
        return EvidenceWeightLevel.HIGH

    def _blocking_factors(self, action, reasonings, contradicting):
        values = []
        if contradicting:
            values.append(
                self._factor(action, "CONTRADICTORY_EVIDENCE", contradicting)
            )
        if action.required_missing_parameters:
            values.append(
                self._factor(action, "MISSING_PARAMETERS", action.required_missing_parameters)
            )
        if any(
            value.conclusion is DeterministicReasoningConclusion.NON_DISCRIMINATED
            for value in reasonings
        ):
            values.append(
                self._factor(action, "INSUFFICIENT_DISCRIMINATION", action.source_reasoning_ids)
            )
        status_codes = {
            CorrectiveActionApplicability.BLOCKED_BY_HISTORY: "BLOCKED_BY_HISTORY",
            CorrectiveActionApplicability.ALREADY_TESTED: "ALREADY_TESTED",
            CorrectiveActionApplicability.NOT_SUPPORTED: "NOT_SUPPORTED",
        }
        if action.applicability in status_codes:
            values.append(self._factor(action, status_codes[action.applicability], (action.action_id,)))
        if self._APPLICABILITY[action.applicability] is WeightedActionApplicability.BLOCKED and not values:
            values.append(self._factor(action, action.applicability.value, (action.action_id,)))
        return tuple(values)

    @staticmethod
    def _factor(action, code, sources):
        return EvidenceBlockingFactor(
            factor_id=f"blocking.{action.action_id.lower()}.{code.lower()}",
            code=code,
            source_object_ids=tuple(sources),
            justification=f"Existing upstream state exposes {code}.",
        )

    def _ceilings(
        self,
        action,
        reasonings,
        contradicting,
        consistency,
        discrimination,
        parameters,
    ):
        values = []
        if contradicting:
            values.append(
                self._ceiling(
                    action,
                    self.CONTRADICTION_RULE,
                    EvidenceDimension.SOURCE_CONSISTENCY,
                    consistency,
                    "Contradictory evidence caps source consistency at LOW.",
                )
            )
        if discrimination is EvidenceWeightLevel.LOW:
            values.append(
                self._ceiling(
                    action,
                    self.DISCRIMINATION_RULE,
                    EvidenceDimension.DISCRIMINATIVE_POWER,
                    discrimination,
                    "Unresolved discrimination caps discriminative power at LOW.",
                )
            )
        if action.required_missing_parameters:
            values.append(
                self._ceiling(
                    action,
                    self.PARAMETERS_RULE,
                    EvidenceDimension.PARAMETER_COMPLETENESS,
                    parameters,
                    "Missing required parameters cap completeness at LOW.",
                )
            )
        return tuple(values)

    @staticmethod
    def _ceiling(action, rule, dimension, maximum, justification):
        return EvidenceDimensionCeiling(
            ceiling_id=f"ceiling.{action.action_id.lower()}.{dimension.value.lower()}",
            rule_id=rule,
            dimension=dimension,
            maximum=maximum,
            justification=justification,
        )

    @staticmethod
    def _ceiling_condition(dimension):
        return {
            EvidenceDimension.SOURCE_CONSISTENCY: "CONTRADICTING_EVIDENCE_PRESENT",
            EvidenceDimension.DISCRIMINATIVE_POWER: "DISCRIMINATION_UNRESOLVED",
            EvidenceDimension.PARAMETER_COMPLETENESS: "REQUIRED_PARAMETER_MISSING",
        }[dimension]

    @staticmethod
    def _unique(values):
        return tuple(dict.fromkeys(values))
