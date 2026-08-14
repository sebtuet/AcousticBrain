from .campaign_user_assessment_presenter import CampaignUserAssessmentPresenter


class CampaignUserAssessmentConsoleReporter:
    """Renders the concise read-only projection while retaining audit detail."""

    def print(self, report):
        assessment = getattr(report, "campaign_user_assessment", None)
        if assessment is None:
            assessment = CampaignUserAssessmentPresenter().present(report)

        print()
        print("=" * 60)
        print("USER ASSESSMENT")
        print("=" * 60)
        self._measurement_status(assessment)
        self._findings("Key findings", assessment.key_findings)
        self._uncertainties(assessment.uncertainties_and_contradictions)
        self._actions(
            "Currently applicable controlled actions",
            assessment.currently_applicable_controlled_actions,
        )
        self._actions(
            "Actions not yet justified",
            assessment.actions_not_yet_justified,
        )
        self._next_step(assessment)
        self._prerequisites(assessment)
        self._boundaries(assessment)
        print()
        print("Expert details: --full-assessment, --reasoning, --actions, "
              "--evidence-plan-view PLAN_ID")
        print("=" * 60)

    @staticmethod
    def _measurement_status(assessment):
        print("\nMeasurement status")
        status = assessment.measurement_status
        if not status.experiment_states and not status.analysis_readiness:
            print("- No V1 measurement status is available.")
            return
        for experiment_id, state in status.experiment_states:
            print(f"- Experiment {experiment_id}: {state}")
        for readiness in status.analysis_readiness:
            print(f"- Analysis {readiness.family}: {readiness.status}")
            if readiness.blocking_issue_codes:
                print("  Blocking issues: " + ", ".join(readiness.blocking_issue_codes))
            if readiness.reservation_issue_codes:
                print("  Reservations: " + ", ".join(readiness.reservation_issue_codes))

    @staticmethod
    def _findings(label, findings):
        print(f"\n{label}")
        if not findings:
            print("- None established by the V1 report.")
            return
        for finding in findings:
            print(f"- {finding.title}")
            print(f"  Reasoning ID: {finding.reasoning_id}")
            print(f"  Conclusion: {finding.conclusion}")
            if finding.confidence is not None:
                print(f"  Confidence: {finding.confidence:.1f} / 100")
            for limitation in finding.limitations[:2]:
                print(f"  Limitation: {limitation}")

    @staticmethod
    def _actions(label, actions):
        print(f"\n{label}")
        if not actions:
            print("- None.")
            return
        for action in actions:
            print(f"- {action.action_id}: {action.title}")
            print(f"  Applicability: {action.applicability}")
            print(f"  {action.description}")
            if action.required_missing_parameters:
                print("  Missing parameters: " + ", ".join(action.required_missing_parameters))
            for limitation in action.limitations[:2]:
                print(f"  Limitation: {limitation}")

    @staticmethod
    def _uncertainties(findings):
        print("\nUncertainties and contradictions")
        if not findings:
            print("- None established by the V1 report.")
            return
        for finding in findings:
            print(f"- {finding.title} — {finding.conclusion}")
            print(f"  Reasoning ID: {finding.reasoning_id}")

    @staticmethod
    def _next_step(assessment):
        print("\nRecommended next step")
        step = assessment.recommended_next_step
        if step is None:
            print("- No plan is selected by the V1 report.")
            return
        print(f"- {step.objective}")
        print(f"  Plan ID: {step.plan_id}")
        print(f"  Planning status: {step.planning_status}")
        print(f"  Test type: {step.test_type}")
        print(f"  Prerequisite availability: {step.prerequisite_status}")
        print(f"  Priority: {step.priority}; estimated effort: {step.estimated_effort}")
        print(f"  Selection rationale: {step.selection_rationale}")
        for limitation in step.limitations[:2]:
            print(f"  Limitation: {limitation}")
        print(
            "  Inspect and prepare this existing plan with --guided-status "
            "before declaration or acquisition."
        )

    @staticmethod
    def _prerequisites(assessment):
        print("\nPrerequisites")
        step = assessment.recommended_next_step
        if step is None:
            print("- No selected plan prerequisites.")
            return
        print(f"- Status: {step.prerequisite_status}")
        if not assessment.prerequisites:
            print("- Required inputs: none")
            return
        for prerequisite in assessment.prerequisites:
            print(f"- {prerequisite}")

    @staticmethod
    def _boundaries(assessment):
        print("\nScientific boundaries")
        for boundary in assessment.scientific_boundaries:
            print(f"- {boundary}")
