from .report import Report


class EvidenceAcquisitionPlanConsoleReporter:
    def print(self, report: Report):
        print()
        print("=" * 60)
        print("NEXT RECOMMENDED EXPERIMENT")
        print("=" * 60)
        presented = report.evidence_acquisition_plans
        if presented is None or presented.recommendation_status == "NO_PLAN":
            print()
            print("No evidence acquisition plan was produced.")
            print(
                "Next scientific step: continue the current analysis; "
                "there is no plan to execute."
            )
            print()
            print("=" * 60)
            return
        if presented.recommendation_status == "ALL_PLANS_BLOCKED":
            print()
            print("Evidence acquisition plans exist, but all are blocked.")
            print("Next scientific step: satisfy the required inputs listed below.")
            for plan in sorted(presented.plans, key=lambda value: value.plan_id):
                self._value("Blocked Plan", plan.plan_id)
                self._value("Objective", plan.objective)
                self._collection("Required Inputs", plan.required_inputs)
                self._collection("Limitations", plan.limitations)
                print()
                print("-" * 60)
            print("=" * 60)
            return
        plan = presented.recommended_plan
        self._value("Plan", plan.plan_id)
        self._value("Objective", plan.objective)
        self._value("Justification", presented.selection_justification)
        self._value("Protocol", "Not specified by the evidence acquisition plan.")
        self._value("Test Type", plan.test_type)
        self._collection("Instructions", plan.instructions, numbered=True)
        self._collection("Controlled Variables", plan.controlled_variables)
        self._collection("Measurements To Capture", plan.measurements_to_capture)
        self._collection("Success Criteria", plan.success_criteria)
        self._collection("Failure Criteria", plan.failure_criteria)
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
