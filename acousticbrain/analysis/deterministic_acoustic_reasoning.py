from acousticbrain.models import (
    CausalDiscriminationOutcome,
    DeterministicAcousticReasoning,
    DeterministicAcousticReasoningSynthesis,
    DeterministicInferenceStep,
    DeterministicReasoningCategory,
    DeterministicReasoningConclusion,
    DeterministicReasoningPremise,
    HypothesisCode,
    HypothesisStatus,
    LongitudinalLearningStatus,
    ReasoningPremiseRole,
    ReasoningPremiseSourceType,
)


class DeterministicAcousticReasoningEngine:
    """Explains existing hypothesis statuses from PR-054 observations."""

    RULE_ID = "EXPLAIN_EXISTING_HYPOTHESIS_FROM_OBSERVATIONS_V1"
    OBSERVATIONS_BY_HYPOTHESIS = {
        HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION: (
            "STEREO_PEAK_DISTRIBUTION_FACTS",
            "EARLY_REFLECTION_EVENT_FACTS",
        ),
        HypothesisCode.MODAL_BASS_PERSISTENCE: (
            "LOW_FREQUENCY_DECAY_FACTS",
            "DECAY_RT60_FACTS",
        ),
        HypothesisCode.DOMINANT_EARLY_REFLECTION_INTERACTION: (
            "EARLY_REFLECTION_EVENT_FACTS",
            "CLARITY_C80_FACTS",
        ),
        HypothesisCode.SBIR_PLACEMENT_INTERACTION: (
            "LOW_FREQUENCY_DECAY_FACTS",
        ),
    }

    def synthesize(
        self,
        observations,
        *,
        acoustic_reasoning=None,
        causal_discrimination=None,
        longitudinal_learning=None,
    ):
        by_id = {item.observation_id: item for item in observations.observations}
        hypotheses = {
            item.code: item
            for item in getattr(acoustic_reasoning, "hypotheses", ())
        }
        states = {
            item.hypothesis_code: item
            for item in getattr(longitudinal_learning, "states", ())
        }
        reasonings = []
        for hypothesis_code, expected_ids in self.OBSERVATIONS_BY_HYPOTHESIS.items():
            hypothesis = hypotheses.get(hypothesis_code)
            if hypothesis is None:
                continue
            relevant = tuple(by_id[item] for item in expected_ids if item in by_id)
            if not relevant:
                continue
            reasonings.append(
                self._explain(
                    hypothesis,
                    relevant,
                    causal_discrimination=(
                        causal_discrimination
                        if hypothesis_code
                        is HypothesisCode.ASYMMETRIC_SPEAKER_ROOM_INTERACTION
                        else None
                    ),
                    longitudinal_state=states.get(hypothesis_code.value),
                )
            )
        return DeterministicAcousticReasoningSynthesis(tuple(reasonings))

    def _explain(
        self,
        hypothesis,
        observations,
        *,
        causal_discrimination,
        longitudinal_state,
    ):
        premises = [
            DeterministicReasoningPremise(
                premise_id=f"premise.observation.{item.observation_id.lower()}",
                source_type=ReasoningPremiseSourceType.OBSERVATION,
                source_id=item.observation_id,
                statement=item.description,
                role=(
                    ReasoningPremiseRole.CONTRADICTING
                    if item.contradicting_evidence
                    else ReasoningPremiseRole.SUPPORTING
                ),
            )
            for item in observations
        ]
        premises.append(
            DeterministicReasoningPremise(
                premise_id=f"premise.hypothesis.{hypothesis.code.value.lower()}",
                source_type=ReasoningPremiseSourceType.EXISTING_HYPOTHESIS,
                source_id=hypothesis.code.value,
                statement=f"Existing hypothesis status is {hypothesis.status.value}.",
                role=ReasoningPremiseRole.CONTEXT,
            )
        )
        if causal_discrimination is not None:
            premises.append(
                DeterministicReasoningPremise(
                    premise_id="premise.causal_discrimination.outcome",
                    source_type=ReasoningPremiseSourceType.CAUSAL_RESULT,
                    source_id=causal_discrimination.protocol_code,
                    statement=(
                        "Existing causal discrimination outcome is "
                        f"{causal_discrimination.outcome.value}."
                    ),
                    role=(
                        ReasoningPremiseRole.SUPPORTING
                        if causal_discrimination.outcome
                        is CausalDiscriminationOutcome.DISCRIMINATED
                        else ReasoningPremiseRole.LIMITING
                    ),
                )
            )
        if longitudinal_state is not None:
            premises.append(
                DeterministicReasoningPremise(
                    premise_id=(
                        "premise.longitudinal."
                        f"{longitudinal_state.state_id.lower()}"
                    ),
                    source_type=ReasoningPremiseSourceType.LONGITUDINAL_STATE,
                    source_id=longitudinal_state.state_id,
                    statement=(
                        "Existing longitudinal learning status is "
                        f"{longitudinal_state.learning_status.value}."
                    ),
                    role=(
                        ReasoningPremiseRole.CONTRADICTING
                        if longitudinal_state.learning_status
                        in (
                            LongitudinalLearningStatus.CONFLICTING_EVIDENCE,
                            LongitudinalLearningStatus.STABLE_NON_SUPPORT,
                        )
                        else ReasoningPremiseRole.SUPPORTING
                        if longitudinal_state.learning_status
                        is LongitudinalLearningStatus.STABLE_SUPPORT
                        else ReasoningPremiseRole.CONTEXT
                    ),
                )
            )

        contradiction = any(item.contradicting_evidence for item in observations)
        if longitudinal_state is not None and (
            longitudinal_state.learning_status
            in (
                LongitudinalLearningStatus.CONFLICTING_EVIDENCE,
                LongitudinalLearningStatus.STABLE_NON_SUPPORT,
            )
        ):
            contradiction = True
        insufficient = len(observations) < 2 or any(
            item.confidence is None for item in observations
        )
        causal_outcome = getattr(causal_discrimination, "outcome", None)
        if contradiction or causal_outcome is CausalDiscriminationOutcome.CONTRADICTORY:
            conclusion = DeterministicReasoningConclusion.CONTRADICTORY_EVIDENCE
        elif causal_outcome is CausalDiscriminationOutcome.INCONCLUSIVE:
            conclusion = DeterministicReasoningConclusion.NON_DISCRIMINATED
        elif insufficient:
            conclusion = DeterministicReasoningConclusion.INSUFFICIENT_EVIDENCE
        else:
            conclusion = {
                HypothesisStatus.SUPPORTED: DeterministicReasoningConclusion.SUPPORTED,
                HypothesisStatus.PLAUSIBLE: (
                    DeterministicReasoningConclusion.PARTIALLY_SUPPORTED
                ),
                HypothesisStatus.CONTRADICTED: (
                    DeterministicReasoningConclusion.CONTRADICTED
                ),
                HypothesisStatus.INCONCLUSIVE: (
                    DeterministicReasoningConclusion.NON_DISCRIMINATED
                ),
            }[hypothesis.status]

        confidence_values = [hypothesis.confidence]
        confidence_values.extend(
            item.confidence for item in observations if item.confidence is not None
        )
        confidence = min(confidence_values) if confidence_values else None
        supporting = tuple(
            dict.fromkeys(
                value
                for item in observations
                for value in item.supporting_evidence
            )
        ) + tuple(item.code for item in hypothesis.supporting_evidence)
        contradicting = tuple(
            dict.fromkeys(
                value
                for item in observations
                for value in item.contradicting_evidence
            )
        ) + tuple(item.code for item in hypothesis.counter_evidence)
        if causal_outcome is CausalDiscriminationOutcome.CONTRADICTORY:
            contradicting += ("causal_discrimination.outcome.CONTRADICTORY",)
        limitations = tuple(
            dict.fromkeys(
                value for item in observations for value in item.limitations
            )
        ) + tuple(item.fact_code for item in hypothesis.missing_facts)
        if insufficient:
            limitations += ("At least two confident source observations are required.",)
        if causal_outcome is CausalDiscriminationOutcome.INCONCLUSIVE:
            limitations += ("Causal discrimination remains inconclusive.",)
        upstream = tuple(
            dict.fromkeys(
                source for item in observations for source in item.source_analysis_ids
            )
        ) + ("AcousticReasoningAnalysis",)
        if causal_discrimination is not None:
            upstream += ("CausalDiscriminationAnalysis",)
        if longitudinal_state is not None:
            upstream += ("LongitudinalExperimentalLearningAnalysis",)
        premise_ids = tuple(item.premise_id for item in premises)
        step = DeterministicInferenceStep(
            step_id=f"inference.{hypothesis.code.value.lower()}.1",
            rule_id=self.RULE_ID,
            input_premise_ids=premise_ids,
            output_code=conclusion.value,
            statement=(
                f"Rule {self.RULE_ID} maps the structured premises to "
                f"{conclusion.value}."
            ),
        )
        return DeterministicAcousticReasoning(
            reasoning_id=f"{hypothesis.code.value}_REASONING",
            category=DeterministicReasoningCategory.HYPOTHESIS_EXPLANATION,
            title=f"Existing hypothesis explanation: {hypothesis.code.value}",
            conclusion=conclusion,
            confidence=confidence,
            observation_ids=tuple(item.observation_id for item in observations),
            premises=tuple(premises),
            inference_steps=(step,),
            supporting_evidence=tuple(dict.fromkeys(supporting)),
            contradicting_evidence=tuple(dict.fromkeys(contradicting)),
            limitations=tuple(dict.fromkeys(limitations)),
            compatible_hypothesis_ids=(hypothesis.code.value,),
            excluded_conclusions=tuple(
                item.value
                for item in DeterministicReasoningConclusion
                if item is not conclusion
            ),
            upstream_source_ids=tuple(dict.fromkeys(upstream)),
        )
