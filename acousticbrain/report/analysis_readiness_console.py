from .report import Report


class AnalysisReadinessConsoleReporter:
    """Prints existing technical analysis readiness decisions only."""

    def print(self, report: Report):
        print()
        print("=" * 60)
        print("TECHNICAL ANALYSIS READINESS")
        print("=" * 60)

        discovered = report.experiments_discovered
        if discovered is not None and discovered.experiments:
            print()
            print("Discovered Experiments")
            for experiment in discovered.experiments:
                print(f"- {experiment.experiment_id}: {experiment.state}")

        presented = report.analysis_readiness
        if presented is None:
            print()
            print("No technical analysis readiness information is available.")
        else:
            print()
            print("Analysis Families")
            for analysis in presented.analyses:
                print()
                print(analysis.family)
                print(f"Status: {analysis.status}")
                self._issues("Blocking issues", analysis.blocking_issue_codes)
                self._issues("Reservations", analysis.reservation_issue_codes)
                self._issues("Missing facts", analysis.missing_facts)

        print()
        print("These statuses describe technical analysis readiness.")
        print("They do not establish scientific validity.")
        print("BLOCKED does not mean that the current pipeline skipped computation.")
        print()
        print("=" * 60)

    @staticmethod
    def _issues(label, codes):
        if not codes:
            return
        print(label)
        for code in codes:
            print(f"- {code}")
