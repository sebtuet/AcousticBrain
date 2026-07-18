from .report import Report


class AdvisorConsoleReporter:
    """Renders a validated advisor response without scientific logic."""

    def print(self, report: Report):
        response = report.advisor_response
        print()
        print("=" * 60)
        print("OPTIONAL LLM ADVISOR")
        print("=" * 60)
        self._value("Provider", response.provider_id)
        self._value("Model", response.model_id or "UNAVAILABLE")
        self._value("Question", response.original_question)
        self._value("Answer", response.answer_text)
        self._collection("Referenced Objects", response.referenced_object_ids)
        self._collection(
            "Preserved Blocking Factors", response.preserved_blocking_factors
        )
        self._collection(
            "Preserved Contradictions", response.preserved_contradictions
        )
        self._collection("Preserved Limitations", response.preserved_limitations)
        self._collection("Unsupported Claims", response.unsupported_claims)
        self._value("Validation", response.validation_status.value)
        self._collection("Warnings", response.warnings)
        print()
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
