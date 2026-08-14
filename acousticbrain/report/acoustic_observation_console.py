from .report import Report


class AcousticObservationConsoleReporter:
    """Prints the opt-in descriptive observation report only."""

    def print(self, report: Report):
        print()
        print("=" * 60)
        print("DETERMINISTIC ACOUSTIC OBSERVATIONS")
        print("=" * 60)
        print()
        print(f"Project: {report.project_name}")
        presented = report.acoustic_observations
        if presented is None or not presented.observations:
            print()
            print("No deterministic acoustic observation is available.")
            print()
            print("=" * 60)
            return
        for observation in presented.observations:
            print()
            print("Observation")
            print(observation.observation_id)
            print()
            print("Category")
            print(observation.category)
            print()
            print("Title")
            print(observation.title)
            print()
            print("Description")
            print(observation.description)
            print()
            print("Confidence")
            print(
                "UNAVAILABLE"
                if observation.confidence is None
                else f"{observation.confidence:.1f} / 100"
            )
            self._collection("Supporting evidence", observation.supporting_evidence)
            self._collection(
                "Contradicting evidence", observation.contradicting_evidence
            )
            self._collection("Limitations", observation.limitations)
            self._collection("Source analyses", observation.source_analysis_ids)
            print()
            print("-" * 60)
        print("=" * 60)

    @staticmethod
    def _collection(label, values):
        print()
        print(label)
        if values:
            for value in values:
                print(f"- {value}")
        else:
            print("- none")
