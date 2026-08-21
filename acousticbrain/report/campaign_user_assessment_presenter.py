from dataclasses import dataclass

from .analysis_readiness_presenter import PresentedAnalysisReadiness


@dataclass(frozen=True)
class CampaignAssessmentSource:
    source_type: str
    source_id: str


@dataclass(frozen=True)
class CampaignAssessmentMeasurementStatus:
    experiment_states: tuple[tuple[str, str], ...]
    analysis_readiness: tuple[PresentedAnalysisReadiness, ...]


@dataclass(frozen=True)
class CampaignAssessmentFinding:
    reasoning_id: str
    title: str
    conclusion: str
    confidence: float | None
    observation_ids: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    excluded_conclusions: tuple[str, ...]
    provenance: tuple[CampaignAssessmentSource, ...]


@dataclass(frozen=True)
class CampaignAssessmentAction:
    action_id: str
    title: str
    objective: str
    description: str
    applicability: str
    preconditions: tuple[str, ...]
    required_missing_parameters: tuple[str, ...]
    risks: tuple[str, ...]
    constraints: tuple[str, ...]
    limitations: tuple[str, ...]
    provenance: tuple[CampaignAssessmentSource, ...]


@dataclass(frozen=True)
class CampaignAssessmentNextStep:
    plan_id: str
    objective: str
    test_type: str
    planning_status: str
    selection_rationale: str
    required_inputs: tuple[str, ...]
    procedure: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    variables_under_test: tuple[str, ...]
    measurements: tuple[str, ...]
    prerequisite_status: str
    limitations: tuple[str, ...]
    priority: str
    estimated_effort: str
    provenance: tuple[CampaignAssessmentSource, ...]


@dataclass(frozen=True)
class CampaignUserAssessment:
    measurement_status: CampaignAssessmentMeasurementStatus
    key_findings: tuple[CampaignAssessmentFinding, ...]
    uncertainties_and_contradictions: tuple[CampaignAssessmentFinding, ...]
    currently_applicable_controlled_actions: tuple[CampaignAssessmentAction, ...]
    actions_not_yet_justified: tuple[CampaignAssessmentAction, ...]
    recommended_next_step: CampaignAssessmentNextStep | None
    prerequisites: tuple[str, ...]
    scientific_boundaries: tuple[str, ...]
    provenance: tuple[CampaignAssessmentSource, ...]


class CampaignUserAssessmentPresenter:
    """Projects already-presented V1 results without adding scientific authority."""

    _UNRESOLVED_CONCLUSIONS = frozenset(
        (
            "PARTIALLY_SUPPORTED",
            "CONTRADICTED",
            "INSUFFICIENT_EVIDENCE",
            "CONTRADICTORY_EVIDENCE",
            "NON_DISCRIMINATED",
            "NO_APPLICABLE_RULE",
        )
    )
    _SCIENTIFIC_BOUNDARIES = (
        "Observation does not establish cause.",
        "SUPPORTED does not establish causality.",
        "READY does not establish execution readiness.",
        "APPLICABLE does not establish benefit or physical safety.",
        "No physical change is authorized by this assessment.",
        "No improvement is predicted by this assessment.",
        "Causality status: NOT_ESTABLISHED.",
    )

    def present(self, report):
        findings = self._findings(report)
        actions = self._actions(report)
        next_step = self._next_step(report)
        return CampaignUserAssessment(
            measurement_status=self._measurement_status(report),
            key_findings=findings,
            uncertainties_and_contradictions=tuple(
                finding
                for finding in findings
                if finding.conclusion in self._UNRESOLVED_CONCLUSIONS
            ),
            currently_applicable_controlled_actions=tuple(
                action for action in actions if action.applicability == "APPLICABLE"
            ),
            actions_not_yet_justified=tuple(
                action for action in actions if action.applicability != "APPLICABLE"
            ),
            recommended_next_step=next_step,
            prerequisites=next_step.required_inputs if next_step is not None else (),
            scientific_boundaries=self._scientific_boundaries(next_step),
            provenance=self._report_provenance(report),
        )

    @staticmethod
    def _measurement_status(report):
        discovered = getattr(report, "experiments_discovered", None)
        readiness = getattr(report, "analysis_readiness", None)
        return CampaignAssessmentMeasurementStatus(
            experiment_states=tuple(
                (item.experiment_id, item.state)
                for item in discovered.experiments
            ) if discovered is not None else (),
            analysis_readiness=(
                readiness.analyses if readiness is not None else ()
            ),
        )

    @classmethod
    def _findings(cls, report):
        presented = getattr(report, "deterministic_acoustic_reasoning", None)
        if presented is None:
            return ()
        return tuple(
            CampaignAssessmentFinding(
                reasoning_id=item.reasoning_id,
                title=item.title,
                conclusion=item.conclusion,
                confidence=item.confidence,
                observation_ids=item.observation_ids,
                supporting_evidence=item.supporting_evidence,
                contradicting_evidence=item.contradicting_evidence,
                limitations=item.limitations,
                excluded_conclusions=item.excluded_conclusions,
                provenance=cls._sources(
                    (("REASONING", item.reasoning_id),)
                    + tuple(("OBSERVATION", value) for value in item.observation_ids)
                    + tuple(("UPSTREAM", value) for value in item.upstream_source_ids)
                ),
            )
            for item in presented.reasonings
        )

    @classmethod
    def _actions(cls, report):
        presented = getattr(report, "deterministic_corrective_actions", None)
        if presented is None:
            return ()
        return tuple(
            CampaignAssessmentAction(
                action_id=item.action_id,
                title=item.title,
                objective=item.objective,
                description=item.description,
                applicability=item.applicability,
                preconditions=item.preconditions,
                required_missing_parameters=item.required_missing_parameters,
                risks=item.known_risks,
                constraints=item.constraints,
                limitations=item.limitations,
                provenance=cls._sources(
                    (("ACTION", item.action_id),)
                    + tuple(("REASONING", value) for value in item.source_reasoning_ids)
                    + tuple(("OBSERVATION", value) for value in item.source_observation_ids)
                    + tuple(("UPSTREAM", value) for value in item.upstream_source_ids)
                ),
            )
            for item in presented.actions
        )

    @classmethod
    def _next_step(cls, report):
        presented = getattr(report, "evidence_acquisition_plans", None)
        if presented is None or presented.recommended_plan is None:
            return None
        plan = presented.recommended_plan
        return CampaignAssessmentNextStep(
            plan_id=plan.plan_id,
            objective=plan.display_objective or plan.objective,
            test_type=plan.test_type,
            planning_status=plan.status,
            selection_rationale=presented.selection_justification or "",
            required_inputs=plan.required_inputs,
            procedure=plan.instructions,
            controlled_variables=plan.controlled_variables,
            variables_under_test=plan.independent_variables,
            measurements=plan.measurements_to_capture,
            prerequisite_status=plan.prerequisite_status,
            limitations=plan.limitations,
            priority=plan.priority,
            estimated_effort=plan.estimated_effort,
            provenance=cls._sources(
                (
                    ("EVIDENCE_PLAN", plan.plan_id),
                    ("EVIDENCE_WEIGHT", plan.evidence_weight_id),
                    ("ACTION", plan.corrective_action_id),
                    ("REASONING", plan.reasoning_id),
                )
            ),
        )

    @classmethod
    def _report_provenance(cls, report):
        values = []
        for finding in cls._findings(report):
            values.extend(finding.provenance)
        for action in cls._actions(report):
            values.extend(action.provenance)
        next_step = cls._next_step(report)
        if next_step is not None:
            values.extend(next_step.provenance)
        return cls._sources(
            tuple((value.source_type, value.source_id) for value in values)
        )

    @classmethod
    def _scientific_boundaries(cls, next_step):
        values = list(cls._SCIENTIFIC_BOUNDARIES)
        if next_step is not None:
            values.insert(4, "The recommended plan has not been executed.")
            if next_step.required_inputs:
                values.insert(
                    5,
                    "Prerequisite availability has not been independently verified.",
                )
        return tuple(values)

    @staticmethod
    def _sources(values):
        return tuple(
            CampaignAssessmentSource(source_type=source_type, source_id=source_id)
            for source_type, source_id in dict.fromkeys(values)
        )
