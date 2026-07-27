from .report import Report
from .assessment_summary_presenter import AssessmentSummaryPresenter


class AssessmentSummaryConsoleReporter:
    """Prints the deterministic assessment summary already projected in Report."""

    def print(self, report: Report):
        print()
        print("=" * 60)
        print("ASSESSMENT SUMMARY")
        print("=" * 60)
        summary = report.assessment_summary
        if summary is None:
            summary = AssessmentSummaryPresenter().present(report)

        self._measurement_status(summary)
        self._findings(summary)
        self._actions("Applicable Actions", summary.applicable_actions)
        self._actions("Blocked Actions", summary.blocked_actions, blocked=True)
        self._recommended_experiments(summary)
        self._technical_notice()

        print()
        print("=" * 60)

    @staticmethod
    def _measurement_status(summary):
        print()
        print("Measurement Status")
        for experiment in summary.experiments:
            print(f"- {experiment.experiment_id}: {experiment.state}")
        if summary.readiness_statuses:
            for family, status in summary.readiness_statuses:
                print(f"- {family}: {status}")
        else:
            print("No technical analysis readiness information is available.")

    @staticmethod
    def _findings(summary):
        print()
        print("Main Findings")
        if not summary.findings:
            print("No assessment findings are available.")
            return
        for finding in summary.findings:
            print(f"- {finding.finding_id}: {finding.title}")
            print(f"  {finding.description}")

    @staticmethod
    def _actions(label, actions, *, blocked=False):
        print()
        print(label)
        if not actions:
            print(
                "No blocked actions are available."
                if blocked
                else "No applicable actions are available."
            )
            return
        for action in actions:
            print(f"- {action.action_id}: {action.title}")
            print(f"  Applicability: {action.applicability}")
            for justification in action.justifications:
                print(f"  Justification: {justification}")

    @staticmethod
    def _recommended_experiments(summary):
        print()
        print("Recommended Experiments")
        if not summary.recommended_experiments:
            print("No recommended experiments are available.")
            return
        for experiment in summary.recommended_experiments:
            print(f"- {experiment.plan_id}: {experiment.objective}")
            print(f"  Status: {experiment.status}")

    @staticmethod
    def _technical_notice():
        print()
        print("Technical Notice")
        print("This summary presents existing deterministic report content.")
        print(
            "It does not add scientific analysis or establish scientific validity."
        )
        print(
            "For complete identifiers, evidence and technical detail, "
            "use --full-assessment."
        )
        print(
            "For technical analysis readiness details, use --analysis-readiness."
        )
