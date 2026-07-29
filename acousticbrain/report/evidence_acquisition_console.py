from .report import Report


class EvidenceAcquisitionPlanConsoleReporter:
    def print(self, report: Report):
        print()
        print("=" * 60)
        print("NEXT RECOMMENDED EXPERIMENT")
        print("=" * 60)
        presented = report.evidence_acquisition_plans
        if presented is None or presented.recommendation_status == "NO_PLANS":
            print()
            print("No evidence acquisition plan was produced.")
            print(
                "Next scientific step: continue the current analysis; "
                "there is no plan to execute."
            )
            print()
            print("=" * 60)
            return
        if (
            presented.recommendation_status
            == "PLANS_PROPOSED_BUT_NOT_READY"
        ):
            print()
            print("Experiments are proposed, but none is READY.")
            if any(value.status == "BLOCKED" for value in presented.plans):
                print("Some additional plans are blocked.")
            print("Next scientific step: review the prerequisites listed below.")
            self._unready_plans(presented.plans)
            print("=" * 60)
            return
        if presented.recommendation_status == "ALL_PLANS_BLOCKED":
            print()
            print("Evidence acquisition plans exist, but all are blocked.")
            print("Next scientific step: satisfy the required inputs listed below.")
            self._unready_plans(presented.plans)
            print("=" * 60)
            return
        plan = presented.recommended_plan
        self._value("Plan", plan.plan_id)
        self._value("Objective", plan.objective)
        self._value("Why This Experiment", plan.scientific_justification)
        self._collection(
            "Protocol",
            plan.compatible_protocol_ids,
            empty="not specified",
        )
        self._collection("Required Inputs", plan.required_inputs)
        if plan.required_inputs:
            self._value(
                "Prerequisite Availability",
                "Not verified by the evidence acquisition plan; "
                "confirm before execution.",
            )
        self._value("Test Type", plan.test_type)
        self._collection("Procedure", plan.instructions, numbered=True)
        self._collection("Keep Constant", plan.controlled_variables)
        self._collection("Variables Under Test", plan.independent_variables)
        self._collection("Measurements", plan.measurements_to_capture)
        self._collection("Expected Observations", plan.expected_observations)
        self._collection("Success Criteria", plan.success_criteria)
        self._collection("Failure Criteria", plan.failure_criteria)
        self._collection("Limitations", plan.limitations)
        self._value("Selection Rationale", presented.selection_justification)
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
    def _collection(label, values, numbered=False, empty=None):
        print()
        print(label)
        if not values:
            print(f"- {empty or 'none'}")
            return
        for index, value in enumerate(values, 1):
            prefix = f"{index}." if numbered else "-"
            print(f"{prefix} {value}")

    def _unready_plans(self, plans):
        for plan in sorted(plans, key=lambda value: value.plan_id):
            self._value(f"{plan.status.title()} Plan", plan.plan_id)
            self._value("Objective", plan.objective)
            self._collection("Required Inputs", plan.required_inputs)
            self._collection("Limitations", plan.limitations)
            print()
            print("-" * 60)
