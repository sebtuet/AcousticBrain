from .report import Report


class DeterministicAcousticReasoningConsoleReporter:
    """Prints the opt-in structured reasoning report only."""

    def print(self, report: Report):
        print()
        print("=" * 60)
        print("DETERMINISTIC ACOUSTIC REASONING")
        print("=" * 60)
        print()
        print(f"Project: {report.project_name}")
        presented = report.deterministic_acoustic_reasoning
        if presented is None or not presented.reasonings:
            print()
            print("No deterministic acoustic reasoning is available.")
            print()
            print("=" * 60)
            return
        for reasoning in presented.reasonings:
            print()
            print("Reasoning")
            print(reasoning.reasoning_id)
            print()
            print("Conclusion")
            print(reasoning.conclusion)
            print()
            print("Confidence")
            print(
                "UNAVAILABLE"
                if reasoning.confidence is None
                else f"{reasoning.confidence:.1f} / 100"
            )
            print()
            print("Premises")
            for premise in reasoning.premises:
                print(
                    f"- {premise.premise_id} [{premise.role}] "
                    f"{premise.source_type}:{premise.source_id} — "
                    f"{premise.statement}"
                )
            print()
            print("Inference steps")
            for index, step in enumerate(reasoning.inference_steps, start=1):
                print(
                    f"{index}. {step.step_id} [{step.rule_id}] "
                    f"{step.output_code} — {step.statement}"
                )
            self._collection("Supporting evidence", reasoning.supporting_evidence)
            self._collection(
                "Contradicting evidence", reasoning.contradicting_evidence
            )
            self._collection("Limitations", reasoning.limitations)
            self._collection("Source observations", reasoning.observation_ids)
            self._collection("Upstream sources", reasoning.upstream_source_ids)
            self._collection(
                "Compatible existing hypotheses",
                reasoning.compatible_hypothesis_ids,
            )
            self._collection("Excluded conclusions", reasoning.excluded_conclusions)
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
