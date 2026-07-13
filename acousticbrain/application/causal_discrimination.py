from dataclasses import dataclass

from acousticbrain.models import (
    CausalDiscriminationAnalysis,
    CausalDiscriminationTrace,
    CausalProtocolStatus,
    CausalTrajectoryAssessment,
    CausalTrajectoryCode,
    CausalTrajectoryStatus,
)


@dataclass(frozen=True)
class _ObservationRule:
    rule_code: str
    step_code: str
    observation_code: str
    supporting_trajectory: CausalTrajectoryCode
    contradicted_trajectories: tuple[CausalTrajectoryCode, ...]
    resolved_discrimination_codes: tuple[str, ...]


class CausalDiscriminationService:
    """Réduit des ambiguïtés à partir d'étapes et observations explicites."""

    PROTOCOL_CODE = "VERIFY_SPEAKER_ROOM_ASYMMETRY"
    STEP_CODES = (
        "STEP_0_BASELINE",
        "STEP_1_LEFT_RIGHT_REMEASUREMENT",
        "STEP_2_SPEAKER_SWAP",
        "STEP_3_SIGNAL_CHAIN_SWAP",
    )
    INITIAL_DISCRIMINATIONS = (
        "LOUDSPEAKER_VS_ROOM_SIDE",
        "LOUDSPEAKER_VS_SIGNAL_CHAIN",
        "SIGNAL_CHAIN_VS_ROOM_SIDE",
    )
    RULE_CODES = (
        "CAUSAL_REQUIRE_EXPLICIT_STEPS",
        "CAUSAL_REQUIRE_DECLARED_OBSERVATIONS",
        "CAUSAL_REQUIRE_CONTROLLED_SWAP_VARIABLES",
        "CAUSAL_REDUCE_ONLY_OBSERVED_DISCRIMINATIONS",
        "CAUSAL_NEVER_CONFIRM_TRAJECTORY",
        "CAUSAL_DETERMINISTIC_SUPPORT_COVERAGE_V1",
    )
    OBSERVATION_RULES = (
        _ObservationRule(
            "SPEAKER_SWAP_ANOMALY_FOLLOWS_LOUDSPEAKER",
            "STEP_2_SPEAKER_SWAP",
            "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",
            CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER,
            (CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE,),
            ("LOUDSPEAKER_VS_ROOM_SIDE",),
        ),
        _ObservationRule(
            "SPEAKER_SWAP_ANOMALY_REMAINS_WITH_ROOM_SIDE",
            "STEP_2_SPEAKER_SWAP",
            "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP",
            CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE,
            (CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER,),
            ("LOUDSPEAKER_VS_ROOM_SIDE",),
        ),
        _ObservationRule(
            "SIGNAL_SWAP_ANOMALY_FOLLOWS_SIGNAL_CHAIN",
            "STEP_3_SIGNAL_CHAIN_SWAP",
            "ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN",
            CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN,
            (
                CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER,
                CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE,
            ),
            (
                "LOUDSPEAKER_VS_SIGNAL_CHAIN",
                "SIGNAL_CHAIN_VS_ROOM_SIDE",
            ),
        ),
        _ObservationRule(
            "SIGNAL_SWAP_ANOMALY_REMAINS_WITH_LOUDSPEAKER",
            "STEP_3_SIGNAL_CHAIN_SWAP",
            "ANOMALY_REMAINED_WITH_LOUDSPEAKER_AFTER_SIGNAL_CHAIN_SWAP",
            CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER,
            (CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN,),
            ("LOUDSPEAKER_VS_SIGNAL_CHAIN",),
        ),
        _ObservationRule(
            "SIGNAL_SWAP_ANOMALY_REMAINS_WITH_ROOM_SIDE",
            "STEP_3_SIGNAL_CHAIN_SWAP",
            "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP",
            CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE,
            (CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN,),
            ("SIGNAL_CHAIN_VS_ROOM_SIDE",),
        ),
    )
    REQUIRED_VARIABLES = {
        "STEP_2_SPEAKER_SWAP": (
            "LOUDSPEAKER_ASSIGNMENT",
            ("ROOM_SIDE", "SIGNAL_CHAIN_ASSIGNMENT"),
        ),
        "STEP_3_SIGNAL_CHAIN_SWAP": (
            "SIGNAL_CHAIN_ASSIGNMENT",
            ("ROOM_SIDE", "LOUDSPEAKER_ASSIGNMENT"),
        ),
    }

    def analyze(
        self,
        descriptors,
        experiment_comparison_analysis,
        *,
        detailed_traceability=False,
    ):
        steps = tuple(sorted(
            (
                item.causal_protocol_step
                for item in descriptors
                if item.causal_protocol_step is not None
            ),
            key=lambda item: (item.step_index, item.experiment_id),
        ))
        if not steps:
            return None
        protocol_codes = tuple(dict.fromkeys(item.protocol_code for item in steps))
        if len(protocol_codes) != 1:
            raise ValueError("A causal analysis requires exactly one protocol code.")
        protocol_code = protocol_codes[0]
        if protocol_code != self.PROTOCOL_CODE:
            raise ValueError(f"Unsupported causal protocol: {protocol_code}")
        if len({item.step_index for item in steps}) != len(steps):
            raise ValueError("Causal protocol step indices must be unique.")

        initial = self._initial_discriminations(experiment_comparison_analysis)
        supporting = {item: [] for item in CausalTrajectoryCode}
        counters = {item: [] for item in CausalTrajectoryCode}
        trajectory_rules = {item: [] for item in CausalTrajectoryCode}
        resolved = []
        new_ambiguities = (
            [] if initial else ["SOURCE_COMPARISON_UNAVAILABLE"]
        )
        applied_rules = list(self.RULE_CODES)
        valid_discriminating_steps = set()

        for step in steps:
            if step.unknown_variable_codes:
                new_ambiguities.append("UNKNOWN_CONTROL_VARIABLES")
            if "ANOMALY_NOT_REPRODUCIBLE" in step.observation_codes:
                new_ambiguities.append("MEASUREMENT_VARIABILITY_VS_CAUSAL_PATTERN")
                supporting[CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE].append(
                    "ANOMALY_NOT_REPRODUCIBLE"
                )
            valid = self._variables_are_controlled(step)
            if step.step_code in self.REQUIRED_VARIABLES and not valid:
                new_ambiguities.append("CONTROLLED_VARIABLES_INCOMPLETE")
            if not valid:
                continue
            applicable = [
                rule for rule in self.OBSERVATION_RULES
                if rule.step_code == step.step_code
                and rule.observation_code in step.observation_codes
            ]
            if applicable:
                valid_discriminating_steps.add(step.step_code)
            for rule in applicable:
                supporting[rule.supporting_trajectory].append(rule.observation_code)
                trajectory_rules[rule.supporting_trajectory].append(rule.rule_code)
                for trajectory in rule.contradicted_trajectories:
                    counters[trajectory].append(rule.observation_code)
                    trajectory_rules[trajectory].append(rule.rule_code)
                resolved.extend(rule.resolved_discrimination_codes)
                applied_rules.append(rule.rule_code)

        declared_observations = {
            value for item in steps for value in item.observation_codes
        }
        contradictory_observation_groups = (
            (
                "LOUDSPEAKER_VS_ROOM_SIDE",
                {
                    "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",
                    "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP",
                },
            ),
            (
                "SIGNAL_CHAIN_VS_ROOM_SIDE",
                {
                    "ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN",
                    "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP",
                    "ANOMALY_REMAINED_WITH_LOUDSPEAKER_AFTER_SIGNAL_CHAIN_SWAP",
                },
            ),
        )
        for discrimination, observation_group in contradictory_observation_groups:
            if len(observation_group & declared_observations) > 1:
                resolved = [code for code in resolved if code != discrimination]
                new_ambiguities.append("CONTRADICTORY_OBSERVATIONS")
                applied_rules.append("KEEP_CONTRADICTORY_DISCRIMINATION_OPEN")

        pairwise = set(resolved)
        closure_rules = (
            (
                {"LOUDSPEAKER_VS_ROOM_SIDE", "SIGNAL_CHAIN_VS_ROOM_SIDE"},
                "LOUDSPEAKER_VS_SIGNAL_CHAIN",
            ),
            (
                {"LOUDSPEAKER_VS_ROOM_SIDE", "LOUDSPEAKER_VS_SIGNAL_CHAIN"},
                "SIGNAL_CHAIN_VS_ROOM_SIDE",
            ),
            (
                {"SIGNAL_CHAIN_VS_ROOM_SIDE", "LOUDSPEAKER_VS_SIGNAL_CHAIN"},
                "LOUDSPEAKER_VS_ROOM_SIDE",
            ),
        )
        for required, inferred in closure_rules:
            if required.issubset(pairwise) and inferred not in pairwise:
                resolved.append(inferred)
                pairwise.add(inferred)
                applied_rules.append("COMPLETE_PAIRWISE_CAUSAL_DISCRIMINATION")

        resolved = tuple(code for code in initial if code in set(resolved))
        remaining = tuple(code for code in initial if code not in resolved)
        new_ambiguities = tuple(dict.fromkeys(new_ambiguities))
        contradictory = any(
            supporting[item] and counters[item]
            for item in CausalTrajectoryCode
            if item is not CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE
        )
        if contradictory:
            new_ambiguities = tuple(dict.fromkeys((
                *new_ambiguities,
                "TRAJECTORY_EVIDENCE_CONFLICT",
            )))
        if remaining or new_ambiguities or contradictory:
            supporting[CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE].append(
                "CAUSAL_AMBIGUITY_REMAINS"
            )
        else:
            counters[CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE].append(
                "ALL_DECLARED_DISCRIMINATIONS_RESOLVED"
            )

        denominator = max(1, len(valid_discriminating_steps))
        assessments = tuple(
            CausalTrajectoryAssessment(
                trajectory_code=trajectory,
                status=(
                    CausalTrajectoryStatus.CONTRADICTED
                    if counters[trajectory]
                    else CausalTrajectoryStatus.COMPATIBLE
                ),
                support_score=(
                    100.0
                    if trajectory is CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE
                    and supporting[trajectory]
                    else min(100.0, 100.0 * len(set(supporting[trajectory])) / denominator)
                ),
                supporting_observation_codes=tuple(dict.fromkeys(supporting[trajectory])),
                counter_evidence_codes=tuple(dict.fromkeys(counters[trajectory])),
                remaining_ambiguity_codes=tuple((*remaining, *new_ambiguities)),
                applied_rule_codes=tuple(dict.fromkeys(trajectory_rules[trajectory])),
            )
            for trajectory in CausalTrajectoryCode
        )
        completed_codes = {item.step_code for item in steps}
        remaining_steps = tuple(
            code for code in self.STEP_CODES if code not in completed_codes
        )
        recommendation = self._next_step(remaining, completed_codes)
        status = (
            CausalProtocolStatus.CONTRADICTORY
            if contradictory
            else CausalProtocolStatus.ACTIVE
            if valid_discriminating_steps
            else CausalProtocolStatus.INCOMPLETE
        )
        applied_rules = tuple(dict.fromkeys(applied_rules))
        trace = CausalDiscriminationTrace(
            trace_id=f"causal-trace:{protocol_code.lower()}",
            protocol_code=protocol_code,
            experiment_ids=tuple(item.experiment_id for item in steps),
            step_codes=tuple(item.step_code for item in steps),
            changed_variable_codes=tuple(dict.fromkeys(
                value for item in steps for value in item.changed_variable_codes
            )),
            controlled_variable_codes=tuple(dict.fromkeys(
                value for item in steps for value in item.controlled_variable_codes
            )),
            observation_codes=tuple(dict.fromkeys(
                value for item in steps for value in item.observation_codes
            )),
            applied_rule_codes=applied_rules,
            trajectory_codes=tuple(item.trajectory_code.value for item in assessments),
            resolved_discrimination_codes=resolved,
            remaining_discrimination_codes=remaining,
        )
        return CausalDiscriminationAnalysis(
            protocol_code=protocol_code,
            status=status,
            completed_steps=steps,
            remaining_step_codes=remaining_steps,
            trajectory_assessments=assessments,
            resolved_discrimination_codes=resolved,
            remaining_discrimination_codes=remaining,
            new_ambiguity_codes=new_ambiguities,
            lost_ambiguity_codes=resolved,
            recommended_next_protocol=recommendation,
            applied_rule_codes=applied_rules,
            trace=trace,
            detailed_traceability=detailed_traceability,
        )

    @classmethod
    def _variables_are_controlled(cls, step):
        requirement = cls.REQUIRED_VARIABLES.get(step.step_code)
        if requirement is None:
            return True
        changed, controlled = requirement
        return (
            changed in step.changed_variable_codes
            and set(controlled).issubset(step.controlled_variable_codes)
            and changed not in step.unknown_variable_codes
        )

    @classmethod
    def _initial_discriminations(cls, comparison_analysis):
        if comparison_analysis is None:
            return ()
        comparisons = comparison_analysis.sequence.local_comparisons
        if not comparisons:
            return ()
        codes = tuple(
            item.code for item in comparisons[0].unresolved_discriminations
        )
        return tuple(code for code in cls.INITIAL_DISCRIMINATIONS if code in codes)

    @staticmethod
    def _next_step(remaining, completed_codes):
        if (
            "LOUDSPEAKER_VS_ROOM_SIDE" in remaining
            and "STEP_2_SPEAKER_SWAP" not in completed_codes
        ):
            return "STEP_2_SPEAKER_SWAP"
        if (
            set(remaining) & {
                "SIGNAL_CHAIN_VS_ROOM_SIDE",
                "LOUDSPEAKER_VS_SIGNAL_CHAIN",
            }
            and "STEP_3_SIGNAL_CHAIN_SWAP" not in completed_codes
        ):
            return "STEP_3_SIGNAL_CHAIN_SWAP"
        return None
