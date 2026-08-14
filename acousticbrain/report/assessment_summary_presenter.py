from dataclasses import dataclass


@dataclass(frozen=True)
class PresentedAssessmentExperiment:
    experiment_id: str
    state: str


@dataclass(frozen=True)
class PresentedAssessmentFinding:
    finding_id: str
    title: str
    description: str


@dataclass(frozen=True)
class PresentedAssessmentAction:
    action_id: str
    title: str
    applicability: str
    justifications: tuple[str, ...]


@dataclass(frozen=True)
class PresentedRecommendedExperiment:
    plan_id: str
    objective: str
    status: str


@dataclass(frozen=True)
class PresentedAssessmentSummary:
    experiments: tuple[PresentedAssessmentExperiment, ...]
    readiness_statuses: tuple[tuple[str, str], ...]
    findings: tuple[PresentedAssessmentFinding, ...]
    applicable_actions: tuple[PresentedAssessmentAction, ...]
    blocked_actions: tuple[PresentedAssessmentAction, ...]
    recommended_experiments: tuple[PresentedRecommendedExperiment, ...]


class AssessmentSummaryPresenter:
    """Selects only explicitly structured user-facing content from Report."""

    APPLICABLE = frozenset(("APPLICABLE", "CONDITIONALLY_APPLICABLE"))
    BLOCKED = frozenset(
        (
            "BLOCKED_BY_CONTRADICTION",
            "BLOCKED_BY_MISSING_PARAMETERS",
            "BLOCKED_BY_HISTORY",
            "NOT_SUPPORTED",
        )
    )

    def present(self, report):
        actions = self._actions(report)
        return PresentedAssessmentSummary(
            experiments=self._experiments(report),
            readiness_statuses=self._readiness(report),
            findings=self._findings(report),
            applicable_actions=tuple(
                action for action in actions if action.applicability in self.APPLICABLE
            ),
            blocked_actions=tuple(
                action for action in actions if action.applicability in self.BLOCKED
            ),
            recommended_experiments=self._recommended_experiments(report),
        )

    @staticmethod
    def _experiments(report):
        presented = report.experiments_discovered
        if presented is None:
            return ()
        return tuple(
            PresentedAssessmentExperiment(
                experiment_id=item.experiment_id,
                state=item.state,
            )
            for item in presented.experiments
        )

    @staticmethod
    def _readiness(report):
        presented = report.analysis_readiness
        if presented is None:
            return ()
        return tuple(
            (item.family, item.status)
            for item in presented.analyses
        )

    @staticmethod
    def _findings(report):
        presented = report.acoustic_observations
        if presented is None:
            return ()
        return tuple(
            PresentedAssessmentFinding(
                finding_id=item.observation_id,
                title=item.title,
                description=item.description,
            )
            for item in presented.observations
        )

    @staticmethod
    def _actions(report):
        presented = report.deterministic_corrective_actions
        if presented is None:
            return ()
        return tuple(
            PresentedAssessmentAction(
                action_id=item.action_id,
                title=item.title,
                applicability=item.applicability,
                justifications=tuple(
                    f"{value.rule_id}:{value.reasoning_id}:{value.conclusion_code}"
                    for value in item.justifications
                ),
            )
            for item in presented.actions
        )

    @staticmethod
    def _recommended_experiments(report):
        presented = report.evidence_acquisition_plans
        if presented is None:
            return ()
        return tuple(
            PresentedRecommendedExperiment(
                plan_id=item.plan_id,
                objective=item.display_objective or item.objective,
                status=item.status,
            )
            for item in presented.plans
        )
