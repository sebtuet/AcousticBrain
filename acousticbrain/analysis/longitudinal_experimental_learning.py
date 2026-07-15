from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentEvolutionOutcome,
    ExperimentFactChange,
    ExperimentInformationAssessment,
    ExperimentInformationStatus,
    ExperimentKind,
    LongitudinalExperimentalLearningAnalysis,
    LongitudinalExperimentalLearningState,
    LongitudinalLearningStatus,
)


class LongitudinalExperimentalLearningEngine:
    """Construit une mémoire expérimentale sans recalcul acoustique."""

    CAUSAL_HYPOTHESIS_BY_PROTOCOL = {
        "VERIFY_SPEAKER_ROOM_ASYMMETRY": "ASYMMETRIC_SPEAKER_ROOM_INTERACTION",
    }
    RULE_CODES = (
        "LONGITUDINAL_GROUP_BY_EXPLICIT_HYPOTHESIS",
        "LONGITUDINAL_USE_LOCAL_COMPARISONS_ONCE",
        "LONGITUDINAL_REQUIRE_EXPLICIT_COMPARABILITY",
        "LONGITUDINAL_REQUIRE_DECLARED_INTERVENTION_FOR_HYPOTHESIS_EVIDENCE",
        "LONGITUDINAL_REPEAT_INFORMS_REPEATABILITY_ONLY",
        "LONGITUDINAL_NEVER_SUM_SUPPORT_SCORES",
        "LONGITUDINAL_NEVER_ESTABLISH_CAUSALITY",
    )

    def analyze(
        self,
        *,
        descriptors=(),
        comparison_analysis=None,
        campaign_analyses=(),
        causal_discrimination=None,
        acoustic_reasoning=None,
    ):
        local = (
            comparison_analysis.sequence.local_comparisons
            if comparison_analysis is not None else ()
        )
        hypotheses = {
            item.source_hypothesis_code
            for item in local
            if item.source_hypothesis_code
        }
        hypotheses.update(item.hypothesis_code for item in campaign_analyses)
        if acoustic_reasoning is not None:
            hypotheses.update(item.code.value for item in acoustic_reasoning.hypotheses)
        if causal_discrimination is not None:
            code = self.CAUSAL_HYPOTHESIS_BY_PROTOCOL.get(
                causal_discrimination.protocol_code
            )
            if code:
                hypotheses.add(code)
        descriptor_by_code = {item.experiment_id: item for item in descriptors}
        states = tuple(
            self._state(
                hypothesis,
                local=local,
                descriptor_by_code=descriptor_by_code,
                campaigns=campaign_analyses,
                causal=causal_discrimination,
            )
            for hypothesis in sorted(hypotheses)
        )
        return LongitudinalExperimentalLearningAnalysis(
            states=states,
            applied_rule_codes=self.RULE_CODES,
            source_analysis_codes=(
                "ExperimentComparisonAnalysis",
                "ExperimentCampaignAnalysis",
                "CausalDiscriminationAnalysis",
                "ExperimentDeclaration",
                "AcousticReasoningAnalysis",
            ),
        )

    def _state(self, hypothesis, *, local, descriptor_by_code, campaigns, causal):
        comparisons = tuple(
            item for item in local if item.source_hypothesis_code == hypothesis
        )
        campaigns = tuple(item for item in campaigns if item.hypothesis_code == hypothesis)
        relevant_causal = (
            causal
            if causal is not None
            and self.CAUSAL_HYPOTHESIS_BY_PROTOCOL.get(causal.protocol_code) == hypothesis
            else None
        )
        experiment_codes = set()
        protocols = set()
        for item in comparisons:
            experiment_codes.add(item.after_experiment_id)
            if item.source_protocol_id:
                protocols.add(item.source_protocol_id)
        for campaign in campaigns:
            experiment_codes.update(item.experiment_id for item in campaign.measurements)
            protocols.add(campaign.protocol_id)
        if relevant_causal is not None:
            experiment_codes.update(item.experiment_id for item in relevant_causal.completed_steps)
            protocols.add(relevant_causal.protocol_code)

        comparable, non_comparable = set(), set()
        controlled, repeats, unknown = set(), set(), set()
        supporting, contradicting, unchanged, inconclusive = set(), set(), set(), set()
        supporting_experiments, contradicting_experiments = set(), set()
        comparison_ids = []
        for item in comparisons:
            code = item.after_experiment_id
            comparison_ids.append(item.result_id)
            if item.eligibility is ComparisonEligibilityStatus.COMPARABLE:
                comparable.add(code)
            else:
                non_comparable.add(code)
            kind = item.experiment_kind
            if kind is ExperimentKind.CONTROLLED_INTERVENTION:
                controlled.add(code)
            elif kind is ExperimentKind.MEASUREMENT_REPEAT:
                repeats.add(code)
            else:
                unknown.add(code)
            if item.eligibility is not ComparisonEligibilityStatus.COMPARABLE:
                continue
            prefix = f"{item.result_id}:"
            if kind is ExperimentKind.CONTROLLED_INTERVENTION:
                if item.outcome is ExperimentEvolutionOutcome.STRONGER:
                    supporting.update(prefix + fact.code for fact in item.observed_facts)
                    if item.observed_facts:
                        supporting_experiments.add(code)
                contradicting.update(prefix + fact.code for fact in item.counter_facts)
                if item.counter_facts:
                    contradicting_experiments.add(code)
                if item.outcome in {
                    ExperimentEvolutionOutcome.WEAKER,
                    ExperimentEvolutionOutcome.CONTRADICTED,
                } and not item.counter_facts:
                    inconclusive.add(prefix + "NON_SUPPORT_WITHOUT_COUNTER_FACT")
                if item.outcome is ExperimentEvolutionOutcome.INCONCLUSIVE:
                    inconclusive.add(prefix + "INCONCLUSIVE")
                if item.outcome is ExperimentEvolutionOutcome.UNCHANGED:
                    unchanged.update(
                        prefix + delta.fact_code
                        for delta in item.fact_deltas
                        if delta.change is ExperimentFactChange.UNCHANGED
                    )
            elif kind is ExperimentKind.MEASUREMENT_REPEAT:
                if item.outcome is ExperimentEvolutionOutcome.UNCHANGED:
                    unchanged.update(
                        prefix + delta.fact_code
                        for delta in item.fact_deltas
                        if delta.change is ExperimentFactChange.UNCHANGED
                    )
                else:
                    inconclusive.add(prefix + "REPEATABILITY_NOT_ESTABLISHED")

        resolved, remaining, deferred, completed, exhausted = set(), set(), set(), set(), set()
        campaign_ids = []
        next_needs = []
        for campaign in campaigns:
            campaign_ids.append(campaign.campaign_code)
            remaining.update(campaign.unresolved_discrimination_codes)
            if campaign.next_discrimination_code:
                next_needs.append(campaign.next_discrimination_code)
            elif not campaign.unresolved_discrimination_codes:
                exhausted.add(campaign.campaign_code)
        causal_id = None
        if relevant_causal is not None:
            causal_id = relevant_causal.trace.trace_id
            resolved.update(relevant_causal.resolved_discrimination_codes)
            completed.update(relevant_causal.resolved_discrimination_codes)
            remaining.update(relevant_causal.remaining_discrimination_codes)
            deferred.update(
                item.discrimination_code
                for item in relevant_causal.discrimination_decisions
                if item.status.value == "DEFERRED"
            )
            if (
                not relevant_causal.remaining_discrimination_codes
                and relevant_causal.recommended_next_protocol is None
            ):
                exhausted.add(relevant_causal.protocol_code)

        status = self._status(
            experiment_codes=experiment_codes,
            controlled=controlled,
            unknown=unknown,
            non_comparable=non_comparable,
            supporting=supporting,
            contradicting=contradicting,
            supporting_experiments=supporting_experiments,
            contradicting_experiments=contradicting_experiments,
            remaining=remaining,
            deferred=deferred,
            exhausted=exhausted,
        )
        next_need = self._next_need(
            status=status,
            unknown=unknown,
            non_comparable=non_comparable,
            repeats=repeats,
            remaining=remaining,
            deferred=deferred,
            explicit=next_needs,
        )
        provenance = (
            ("campaigns", tuple(sorted(campaign_ids))),
            ("causal_discrimination", ((causal_id,) if causal_id else ())),
            ("comparisons", tuple(sorted(comparison_ids))),
            ("declarations", tuple(sorted(
                code for code in experiment_codes if code in descriptor_by_code
            ))),
        )
        return LongitudinalExperimentalLearningState(
            state_id=f"longitudinal-learning:{hypothesis.lower()}",
            hypothesis_code=hypothesis,
            protocol_codes=tuple(sorted(protocols)),
            experiment_codes=tuple(sorted(experiment_codes)),
            comparable_experiment_codes=tuple(sorted(comparable)),
            non_comparable_experiment_codes=tuple(sorted(non_comparable)),
            controlled_intervention_codes=tuple(sorted(controlled)),
            measurement_repeat_codes=tuple(sorted(repeats)),
            unknown_declaration_codes=tuple(sorted(unknown)),
            supporting_observation_ids=tuple(sorted(supporting)),
            contradicting_observation_ids=tuple(sorted(contradicting)),
            unchanged_observation_ids=tuple(sorted(unchanged)),
            inconclusive_observation_ids=tuple(sorted(inconclusive)),
            resolved_ambiguities=tuple(sorted(resolved)),
            remaining_ambiguities=tuple(sorted(remaining)),
            deferred_discriminations=tuple(sorted(deferred)),
            completed_discriminations=tuple(sorted(completed)),
            exhausted_discriminations=tuple(sorted(exhausted)),
            evidence_summary=(
                ("SUPPORTING", len(supporting)),
                ("CONTRADICTING", len(contradicting)),
                ("UNCHANGED", len(unchanged)),
                ("INCONCLUSIVE", len(inconclusive)),
            ),
            learning_status=status,
            next_information_need=next_need,
            causality_status="NOT_ESTABLISHED",
            provenance=provenance,
        )

    @staticmethod
    def _status(*, experiment_codes, controlled, unknown, non_comparable,
                supporting, contradicting, supporting_experiments,
                contradicting_experiments, remaining, deferred, exhausted):
        if not experiment_codes:
            return LongitudinalLearningStatus.NOT_TESTED
        if deferred:
            return LongitudinalLearningStatus.DEFERRED_BY_USER
        if supporting and contradicting:
            return LongitudinalLearningStatus.CONFLICTING_EVIDENCE
        if len(supporting_experiments) >= 2:
            return LongitudinalLearningStatus.STABLE_SUPPORT
        if len(contradicting_experiments) >= 2:
            return LongitudinalLearningStatus.STABLE_NON_SUPPORT
        if supporting or contradicting:
            return LongitudinalLearningStatus.EVIDENCE_ACCUMULATING
        if unknown:
            return LongitudinalLearningStatus.INSUFFICIENT_DECLARATION
        if non_comparable:
            return LongitudinalLearningStatus.INSUFFICIENT_COMPARABILITY
        if remaining:
            return LongitudinalLearningStatus.DISCRIMINATION_REQUIRED
        if exhausted:
            return LongitudinalLearningStatus.EXPERIMENTAL_PATH_EXHAUSTED
        return LongitudinalLearningStatus.EVIDENCE_ACCUMULATING

    @staticmethod
    def _next_need(*, status, unknown, non_comparable, repeats, remaining,
                   deferred, explicit):
        if deferred:
            return f"EXECUTE_DEFERRED_DISCRIMINATION:{sorted(deferred)[0]}"
        if unknown:
            return "DECLARE_TESTED_VARIABLE_OR_UNCHANGED_CONFIGURATION"
        if non_comparable:
            return "RESTORE_EXPLICIT_EXPERIMENT_COMPARABILITY"
        if len(repeats) == 1:
            return "ADDITIONAL_REPEAT_FOR_STABILITY"
        if explicit:
            return sorted(explicit)[0]
        if remaining:
            return f"RESOLVE_DISCRIMINATION:{sorted(remaining)[0]}"
        if status is LongitudinalLearningStatus.EXPERIMENTAL_PATH_EXHAUSTED:
            return "NO_ADDITIONAL_DISCRIMINATION_AVAILABLE"
        if status is LongitudinalLearningStatus.NOT_TESTED:
            return "CONTROLLED_SINGLE_VARIABLE_INTERVENTION"
        return "REVIEW_EXISTING_EXPERIMENTAL_EVIDENCE"

    @staticmethod
    def assess_proposal(
        descriptors,
        *,
        hypothesis_code,
        protocol_code,
        experiment_kind,
        reference_experiment_code,
        modified_variables,
        controlled_variables,
        comparable=True,
        deferred=False,
        already_completed=False,
    ):
        if experiment_kind is ExperimentKind.UNKNOWN:
            return ExperimentInformationAssessment(
                ExperimentInformationStatus.BLOCKED_BY_MISSING_DECLARATION,
                (), ("EXPERIMENT_DECLARATION_UNKNOWN",), ("ExperimentDeclaration",),
            )
        if not comparable:
            return ExperimentInformationAssessment(
                ExperimentInformationStatus.BLOCKED_BY_NON_COMPARABILITY,
                (), ("COMPARISON_NOT_COMPARABLE",), ("ExperimentComparison",),
            )
        if deferred:
            return ExperimentInformationAssessment(
                ExperimentInformationStatus.DEFERRED_BY_USER,
                (), ("DISCRIMINATION_DEFERRED",), ("CausalDiscriminationDecision",),
            )
        if already_completed:
            return ExperimentInformationAssessment(
                ExperimentInformationStatus.ALREADY_COMPLETED,
                (), ("PROTOCOL_ALREADY_COMPLETED",), ("ExperimentCampaign",),
            )
        exact, partial, same_hypothesis = [], [], []
        signature = (
            hypothesis_code, protocol_code, experiment_kind,
            reference_experiment_code, tuple(modified_variables),
            tuple(controlled_variables),
        )
        for item in descriptors:
            declaration = item.experiment_declaration
            item_signature = (
                item.source_hypothesis_code, item.source_protocol_id,
                declaration.experiment_kind, declaration.reference_experiment_code,
                declaration.modified_variables, declaration.controlled_variables,
            )
            if item.source_hypothesis_code == hypothesis_code:
                same_hypothesis.append(item.experiment_id)
            if item_signature == signature:
                exact.append(item.experiment_id)
            elif (
                item.source_hypothesis_code == hypothesis_code
                and item.source_protocol_id == protocol_code
                and set(declaration.modified_variables) & set(modified_variables)
            ):
                partial.append(item.experiment_id)
        if exact:
            status, matches, reason = (
                ExperimentInformationStatus.EXACT_REPEAT,
                exact,
                "DECLARED_EXPERIMENT_SIGNATURE_IDENTICAL",
            )
        elif partial:
            status, matches, reason = (
                ExperimentInformationStatus.PARTIAL_REPEAT,
                partial,
                "DECLARED_EXPERIMENT_SIGNATURE_OVERLAPS",
            )
        elif same_hypothesis:
            status, matches, reason = (
                ExperimentInformationStatus.STILL_INFORMATIVE,
                same_hypothesis,
                "HYPOTHESIS_TESTED_WITH_DIFFERENT_DECLARED_SCOPE",
            )
        else:
            status, matches, reason = (
                ExperimentInformationStatus.NEW_INFORMATION,
                (),
                "HYPOTHESIS_NOT_PREVIOUSLY_TESTED",
            )
        return ExperimentInformationAssessment(
            status,
            tuple(sorted(matches)),
            (reason,),
            ("ExperimentDescriptor", "ExperimentDeclaration"),
        )
