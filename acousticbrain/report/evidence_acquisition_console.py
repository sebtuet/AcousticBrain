from .report import Report


class EvidenceAcquisitionPlanConsoleReporter:
    def print(self, report: Report):
        print()
        print("=" * 60)
        print("EVIDENCE ACQUISITION PLANS")
        print("=" * 60)
        presented = report.evidence_acquisition_plans
        if presented is None or not presented.plans:
            print()
            print("No blocking factor justifies an evidence acquisition plan.")
            print()
            print("=" * 60)
            return
        for plan in presented.plans:
            self._value("Plan", plan.plan_id)
            self._value("Objective", plan.objective)
            self._value("Target Reasoning", plan.reasoning_id)
            self._value("Corrective Action", plan.corrective_action_id)
            self._collection("Blocking Factors", plan.blocking_factor_ids)
            self._value("Test Type", plan.test_type)
            self._collection("Instructions", plan.instructions, numbered=True)
            self._collection("Required Inputs", plan.required_inputs)
            self._collection("Controlled Variables", plan.controlled_variables)
            self._collection("Independent Variables", plan.independent_variables)
            self._collection("Measurements To Capture", plan.measurements_to_capture)
            self._collection("Success Criteria", plan.success_criteria)
            self._collection("Limitations", plan.limitations)
            self._value("Priority", plan.priority)
            self._value("Estimated Effort", plan.estimated_effort)
            self._value("Status", plan.status)
            print()
            print("-" * 60)
        print("=" * 60)

    @staticmethod
    def _value(label, value):
        print()
        print(label)
        print(value)

    @staticmethod
    def _collection(label, values, numbered=False):
        print()
        print(label)
        if not values:
            print("- none")
            return
        for index, value in enumerate(values, 1):
            prefix = f"{index}." if numbered else "-"
            print(f"{prefix} {value}")
