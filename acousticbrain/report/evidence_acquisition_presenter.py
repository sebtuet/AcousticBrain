import json
from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedEvidenceAcquisitionPlan:
    plan_id: str
    reasoning_id: str
    corrective_action_id: str
    evidence_weight_id: str
    blocking_factor_ids: tuple[str, ...]
    objective: str
    test_type: str
    instructions: tuple[str, ...]
    required_inputs: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    independent_variables: tuple[str, ...]
    measurements_to_capture: tuple[str, ...]
    expected_observations: tuple[str, ...]
    success_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]
    resulting_evidence_targets: tuple[str, ...]
    priority: str
    estimated_effort: str
    status: str
    limitations: tuple[str, ...]
    compatible_protocol_ids: tuple[str, ...] = ()
    scientific_justification: str = ""
    display_objective: str | None = None

    def to_dict(self):
        return {
            **self.__dict__,
            "prerequisite_status": self.prerequisite_status,
        }

    @property
    def prerequisite_status(self):
        if not self.required_inputs:
            return "NO_REQUIRED_INPUTS"
        return "AVAILABILITY_NOT_VERIFIED"


@dataclass(frozen=True)
class PresentedEvidenceAcquisitionPlanReport:
    plans: tuple[PresentedEvidenceAcquisitionPlan, ...]

    _PRIORITY_ORDER = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }
    _EFFORT_ORDER = {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
    }

    @property
    def recommended_plan(self):
        ready = tuple(value for value in self.plans if value.status == "READY")
        if not ready:
            return None
        return min(
            ready,
            key=lambda value: (
                self._PRIORITY_ORDER[value.priority],
                self._EFFORT_ORDER[value.estimated_effort],
                value.plan_id,
            ),
        )

    @property
    def recommendation_status(self):
        if not self.plans:
            return "NO_PLANS"
        if self.recommended_plan is not None:
            return "RECOMMENDED_EXPERIMENT"
        if any(value.status == "PROPOSED" for value in self.plans):
            return "PLANS_PROPOSED_BUT_NOT_READY"
        return "ALL_PLANS_BLOCKED"

    @property
    def selection_justification(self):
        plan = self.recommended_plan
        if plan is None:
            return None
        return (
            f"Selected among READY plans by priority ({plan.priority}), "
            f"then estimated effort ({plan.estimated_effort}), "
            "with plan id used only as a stable final tie-breaker."
        )

    def to_dict(self):
        return {
            "plans": tuple(value.to_dict() for value in self.plans),
            "recommendation_status": self.recommendation_status,
            "recommended_plan": (
                self.recommended_plan.to_dict()
                if self.recommended_plan is not None
                else None
            ),
            "selection_justification": self.selection_justification,
        }

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class EvidenceAcquisitionPlanPresenter:
    def present(self, context):
        synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
        if synthesis is None:
            return None
        action_synthesis = getattr(
            context,
            "deterministic_corrective_action_synthesis",
            None,
        )
        actions = {
            value.action_id: value
            for value in action_synthesis.actions
        } if action_synthesis is not None else {}
        reasoning_synthesis = getattr(
            context,
            "deterministic_acoustic_reasoning_synthesis",
            None,
        )
        reasonings = {
            value.reasoning_id: value
            for value in reasoning_synthesis.reasonings
        } if reasoning_synthesis is not None else {}
        return PresentedEvidenceAcquisitionPlanReport(
            plans=tuple(
                PresentedEvidenceAcquisitionPlan(
                    plan_id=value.plan_id,
                    reasoning_id=value.reasoning_id,
                    corrective_action_id=value.corrective_action_id,
                    evidence_weight_id=value.evidence_weight_id,
                    blocking_factor_ids=value.blocking_factor_ids,
                    objective=value.objective,
                    test_type=value.test_type.value,
                    instructions=value.instructions,
                    required_inputs=value.required_inputs,
                    controlled_variables=value.controlled_variables,
                    independent_variables=value.independent_variables,
                    measurements_to_capture=value.measurements_to_capture,
                    expected_observations=value.expected_observations,
                    success_criteria=value.success_criteria,
                    failure_criteria=value.failure_criteria,
                    resulting_evidence_targets=value.resulting_evidence_targets,
                    priority=value.priority.value,
                    estimated_effort=value.estimated_effort.value,
                    status=value.status.value,
                    limitations=value.limitations,
                    compatible_protocol_ids=tuple(
                        sorted(
                            actions[value.corrective_action_id].compatible_protocol_ids
                        )
                    ) if value.corrective_action_id in actions else (),
                    scientific_justification=self._scientific_justification(
                        value,
                        reasonings.get(value.reasoning_id),
                    ),
                    display_objective=self._display_objective(value),
                )
                for value in synthesis.plans
            )
        )

    @staticmethod
    def _display_objective(plan):
        expected = set(plan.expected_observations)
        variables = set(plan.independent_variables)
        measurements = set(plan.measurements_to_capture)
        test_type = plan.test_type.value

        if (
            test_type == "CHANNEL_ISOLATION"
            and "active_channel" in variables
            and "repeatability_metric" in expected
        ):
            return (
                "Determine whether the observed left/right acoustic difference "
                "is stable and repeatable."
            )
        if (
            test_type == "REPEAT_MEASUREMENT"
            and "repeatability" in expected
        ):
            return (
                "Determine whether the observed acoustic result is stable "
                "and repeatable."
            )
        if (
            test_type == "COMPARATIVE_MEASUREMENT"
            and variables
            and expected
        ):
            return (
                "Compare the declared experimental variables to determine "
                "whether the expected acoustic patterns differ."
            )
        if (
            test_type == "PARAMETER_COMPLETION"
            and "validated_protocol_compatibility" in expected
        ):
            return (
                "Identify and validate the protocol or plan required before "
                "measurement execution."
            )
        if test_type == "ADDITIONAL_OBSERVATION" and expected:
            return (
                "Acquire an additional traceable observation for the associated "
                "acoustic reasoning."
            )
        if (
            test_type == "GEOMETRY_ACQUISITION"
            and "speaker_position_m" in measurements
            and "listening_position_m" in measurements
        ):
            return (
                "Document the speaker, listening and microphone geometry "
                "required for a future acoustic comparison."
            )
        return (
            "Acquire the evidence required by the associated acoustic "
            "reasoning without establishing causality."
        )

    @staticmethod
    def _scientific_justification(plan, reasoning):
        title = (
            EvidenceAcquisitionPlanPresenter._readable_title(reasoning.title)
            if reasoning is not None
            else "the associated acoustic reasoning"
        )
        conclusion = (
            reasoning.conclusion.value.replace("_", " ").lower()
            if reasoning is not None
            else "unresolved"
        )
        observation_count = (
            len(reasoning.observation_ids)
            if reasoning is not None
            else 0
        )
        supporting_observation_count = sum(
            1
            for premise in getattr(reasoning, "premises", ())
            if premise.source_type.value == "OBSERVATION"
            and premise.role.value == "SUPPORTING"
        )
        evidence_context = (
            f"{supporting_observation_count} structured observation"
            f"{'s' if supporting_observation_count != 1 else ''} support the reasoning about "
            f"{title}, which remains {conclusion}."
            if supporting_observation_count
            else (
                f"{observation_count} structured observation"
                f"{'s' if observation_count != 1 else ''} inform the reasoning about "
                f"{title}, which remains {conclusion}."
                if observation_count
                else f"The experiment addresses {title}, which remains {conclusion}."
            )
        )
        if reasoning is not None and getattr(
            reasoning,
            "contradicting_evidence",
            (),
        ):
            evidence_context += " The reasoning also retains contradictory evidence."
        if plan.test_type.value == "CHANNEL_ISOLATION":
            method = (
                "Acquiring LEFT and RIGHT separately while keeping the declared "
                "controlled variables constant tests whether the observed channel "
                "difference is stable and repeatable."
            )
        else:
            outcomes = ", ".join(
                value.replace("_", " ")
                for value in plan.expected_observations
            )
            method = (
                f"The declared procedure tests for {outcomes}."
                if outcomes
                else "The declared procedure acquires evidence for that reasoning."
            )
        return (
            f"{evidence_context} {method} "
            "The experiment acquires evidence and does not establish causality."
        )

    @staticmethod
    def _readable_title(value):
        title = value.rsplit(":", 1)[-1].strip()
        return title.replace("_", " ").lower()
