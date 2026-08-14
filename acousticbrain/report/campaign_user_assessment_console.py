from .campaign_user_assessment_human_text import CampaignUserAssessmentHumanText
from .campaign_user_assessment_presenter import CampaignUserAssessmentPresenter


class HumanReadableAssessmentRenderer:
    """Render a deterministic human view while retaining V1 audit references."""

    TEXT = CampaignUserAssessmentHumanText

    def print(self, report):
        assessment = getattr(report, "campaign_user_assessment", None)
        if assessment is None:
            assessment = CampaignUserAssessmentPresenter().present(report)

        print()
        print("=" * 60)
        print("ACOUSTICBRAIN — USER ASSESSMENT")
        print("=" * 60)
        self._campaign(assessment)
        self._findings(assessment)
        self._uncertainties(assessment)
        self._actions(assessment)
        self._next_measurement(assessment)
        self._before_starting(assessment)
        self._boundaries(assessment)
        self._technical_references(assessment)
        print("=" * 60)

    @classmethod
    def _campaign(cls, assessment):
        print("\nCampaign")
        status = assessment.measurement_status
        experiments = status.experiment_states
        if not experiments:
            print("No experiment discovery status is available.")
        elif all(state == "READY" for _, state in experiments):
            count = len(experiments)
            noun = "experiment" if count == 1 else "experiments"
            print(
                f"{count} {noun} were discovered. The measurement files required "
                "for discovery are present."
            )
        else:
            print(f"{len(experiments)} experiments were discovered.")
            for experiment_id, state in experiments:
                if state != "READY":
                    print(
                        f"- {experiment_id}: measurement discovery state "
                        f"{state.replace('_', ' ').lower()}"
                    )

        available = tuple(
            value
            for value in status.analysis_readiness
            if value.status == "AVAILABLE"
        )
        limited = tuple(
            value
            for value in status.analysis_readiness
            if value.status != "AVAILABLE"
        )
        if available:
            print(
                "Available deterministic analyses: "
                + ", ".join(
                    cls.TEXT.analysis_family(value.family) for value in available
                )
                + "."
            )
        for value in limited:
            print(
                f"- {cls.TEXT.analysis_family(value.family).capitalize()}: "
                f"{cls.TEXT.analysis_status(value.status)}."
            )

    @classmethod
    def _findings(cls, assessment):
        print("\nWhat the measurements show")
        if not assessment.key_findings:
            print("No deterministic reasoning finding is available.")
            return
        for finding in assessment.key_findings:
            print(f"\n{cls.TEXT.finding_title(finding)}")
            print(cls.TEXT.conclusion(finding.conclusion))
            if finding.confidence is not None:
                print(f"Confidence: {finding.confidence:.1f} / 100")
            if finding.limitations and cls._is_human_text(finding.limitations[0]):
                print(
                    "Recorded limitation: "
                    + cls.TEXT.limitation(finding.limitations[0])
                )
            if finding.conclusion in {"SUPPORTED", "PARTIALLY_SUPPORTED"}:
                print("This is observational support, not proof of acoustic causality.")

    @classmethod
    def _uncertainties(cls, assessment):
        print("\nWhat remains uncertain")
        findings = assessment.uncertainties_and_contradictions
        if not findings:
            print("No unresolved deterministic reasoning is recorded.")
            return
        for finding in findings:
            print(
                f"- {cls.TEXT.finding_title(finding)}: "
                f"{cls.TEXT.conclusion(finding.conclusion)}"
            )

    @classmethod
    def _actions(cls, assessment):
        print("\nWhat you can do now")
        applicable = assessment.currently_applicable_controlled_actions
        if not applicable:
            print("No controlled action is currently applicable.")
        for action in applicable:
            print("\nControlled verification available")
            print(f"For: {cls._action_subject(action)}")
            print(cls.TEXT.action_applicability(action.applicability))
            print(f"Existing objective: {action.objective}")
            for precondition in action.preconditions:
                print(f"- Precondition: {precondition}")

        unavailable = assessment.actions_not_yet_justified
        if unavailable:
            print("\nOther existing actions are not currently available:")
        for action in unavailable:
            print(
                f"- {cls._action_subject(action)}: "
                f"{cls.TEXT.action_applicability(action.applicability)}"
            )

    @classmethod
    def _next_measurement(cls, assessment):
        print("\nRecommended next measurement")
        step = assessment.recommended_next_step
        if step is None:
            print("The V1 report has not selected a next measurement plan.")
            return
        print(step.objective)
        print(cls.TEXT.plan_status(step.planning_status))
        print(f"Measurement type: {cls.TEXT.test_type(step.test_type)}.")
        print(cls.TEXT.prerequisite_status(step.prerequisite_status))
        if step.procedure:
            print("\nExisting procedure:")
            for index, instruction in enumerate(step.procedure, 1):
                print(f"{index}. {instruction}")
        if step.limitations:
            print(f"Recorded limitation: {step.limitations[0]}")
        print(
            "Inspect and prepare this existing plan with --guided-status before "
            "declaration or acquisition."
        )

    @classmethod
    def _before_starting(cls, assessment):
        print("\nBefore you start")
        step = assessment.recommended_next_step
        if step is None:
            print("No selected plan prerequisites are available.")
            return
        print(cls.TEXT.prerequisite_status(step.prerequisite_status))
        if not assessment.prerequisites:
            print("The selected plan declares no required pre-acquisition inputs.")
            return
        print("Before starting this measurement, confirm:")
        for prerequisite in assessment.prerequisites:
            print(f"- {cls.TEXT.prerequisite(prerequisite)};")

    @staticmethod
    def _boundaries(assessment):
        print("\nWhat AcousticBrain cannot conclude yet")
        print("- This assessment has not established an acoustic cause.")
        if assessment.recommended_next_step is not None:
            print("- The proposed measurement has not been performed.")
        if assessment.prerequisites:
            print("- The required inputs have not been independently verified.")
        print(
            "- No speaker movement, treatment, or other physical correction is "
            "authorized by this assessment."
        )
        print("- This assessment does not predict an improvement.")

    @staticmethod
    def _technical_references(assessment):
        print("\nTechnical references")
        for readiness in assessment.measurement_status.analysis_readiness:
            if readiness.blocking_issue_codes:
                print(
                    f"- {readiness.family} blocking codes: "
                    + ", ".join(readiness.blocking_issue_codes)
                )
            if readiness.reservation_issue_codes:
                print(
                    f"- {readiness.family} reservation codes: "
                    + ", ".join(readiness.reservation_issue_codes)
                )
        for finding in assessment.key_findings:
            print(f"- Reasoning: {finding.reasoning_id} [{finding.conclusion}]")
        for action in (
            *assessment.currently_applicable_controlled_actions,
            *assessment.actions_not_yet_justified,
        ):
            print(f"- Action: {action.action_id} [{action.applicability}]")
        step = assessment.recommended_next_step
        if step is not None:
            print(f"- Plan: {step.plan_id} [{step.planning_status}]")
        print(
            "- Detailed views: --full-assessment, --reasoning, --actions, "
            "--evidence-plan-view PLAN_ID"
        )

    @staticmethod
    def _is_human_text(value):
        return " " in value and not value.isupper()

    @classmethod
    def _action_subject(cls, action):
        return next(
            (
                cls.TEXT.FINDING_TITLES[source.source_id]
                for source in action.provenance
                if source.source_type == "REASONING"
                and source.source_id in cls.TEXT.FINDING_TITLES
            ),
            action.title,
        )


class CampaignUserAssessmentConsoleReporter(HumanReadableAssessmentRenderer):
    """Compatibility name for the public console reporter."""
