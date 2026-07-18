from .report import Report


class DeterministicCorrectiveActionConsoleReporter:
    """Prints declarative corrective-action objects without executing them."""

    def print(self, report: Report):
        print()
        print("=" * 60)
        print("DETERMINISTIC CORRECTIVE ACTIONS")
        print("=" * 60)
        print()
        print(f"Project: {report.project_name}")
        presented = report.deterministic_corrective_actions
        if presented is None or not presented.actions:
            print()
            print("No deterministic corrective action is available.")
            print()
            print("=" * 60)
            return
        for action in presented.actions:
            print()
            print("Action")
            print(action.action_id)
            print()
            print("Type")
            print(action.action_type)
            print()
            print("Applicability")
            print(action.applicability)
            print()
            print("Priority")
            print(action.priority)
            print()
            print("Objective")
            print(action.objective)
            print()
            print("Confidence")
            print("UNAVAILABLE" if action.confidence is None else f"{action.confidence:.1f} / 100")
            self._collection("Source reasoning", action.source_reasoning_ids)
            self._collection("Source observations", action.source_observation_ids)
            self._collection("Upstream sources", action.upstream_source_ids)
            self._collection(
                "Justification",
                tuple(
                    f"{item.rule_id}:{item.reasoning_id}:{item.conclusion_code}"
                    for item in action.justifications
                ),
            )
            self._collection("Preconditions", action.preconditions)
            self._collection(
                "Known parameters",
                tuple(f"{name}={value}" for name, value in action.known_parameters),
            )
            self._collection("Derivable parameters", action.derivable_parameters)
            self._collection("Missing parameters", action.required_missing_parameters)
            self._collection(
                "Forbidden to invent", action.forbidden_to_invent_parameters
            )
            self._collection("Risks", action.known_risks)
            self._collection("Constraints", action.constraints)
            self._collection("Success criteria", action.success_criteria)
            self._collection("Stop criteria", action.stop_criteria)
            self._collection("Contradictions", action.contradictions)
            self._collection("Limitations", action.limitations)
            self._collection("Compatible protocols", action.compatible_protocol_ids)
            self._collection("Compatible plans", action.compatible_plan_ids)
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
