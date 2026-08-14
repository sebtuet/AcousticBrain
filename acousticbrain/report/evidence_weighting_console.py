from .report import Report


class DeterministicEvidenceWeightingConsoleReporter:
    """Projects an existing multidimensional evidence qualification."""

    def print(self, report: Report):
        print()
        print("=" * 60)
        print("DETERMINISTIC EVIDENCE WEIGHTING")
        print("=" * 60)
        print()
        print(f"Project: {report.project_name}")
        presented = report.deterministic_evidence_weighting
        if presented is None or not presented.weights:
            print()
            print("No existing evidence object is available for weighting.")
            print()
            print("=" * 60)
            return
        for weight in presented.weights:
            print()
            print("Evidence Weight")
            print(weight.weight_id)
            self._value("Evidence Strength", weight.evidence_strength)
            self._value("Source Consistency", weight.source_consistency)
            self._value("Discriminative Power", weight.discriminative_power)
            self._value("Parameter Completeness", weight.parameter_completeness)
            self._value("Action Applicability", weight.action_applicability)
            self._collection("Action References", weight.action_references)
            self._collection("Reasoning References", weight.reasoning_references)
            self._collection("Observation References", weight.observation_references)
            self._collection("Supporting Evidence", weight.supporting_evidence)
            self._collection("Contradicting Evidence", weight.contradicting_evidence)
            self._collection(
                "Blocking Factors",
                tuple(
                    f"{value.code}:{','.join(value.source_object_ids)}"
                    for value in weight.blocking_factors
                ),
            )
            self._collection(
                "Ceilings",
                tuple(
                    f"{value.dimension}<={value.maximum}:{value.rule_id}"
                    for value in weight.ceilings
                ),
            )
            self._collection("Limitations", weight.limitations)
            self._collection("Applied Rules", weight.applied_rule_ids)
            print()
            print("-" * 60)
        print("=" * 60)

    @staticmethod
    def _value(label, value):
        print()
        print(label)
        print(value)

    @staticmethod
    def _collection(label, values):
        print()
        print(label)
        if values:
            for value in values:
                print(f"- {value}")
        else:
            print("- none")
