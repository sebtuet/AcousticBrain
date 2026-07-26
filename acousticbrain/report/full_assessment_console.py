from .acoustic_observation_console import AcousticObservationConsoleReporter
from .deterministic_acoustic_reasoning_console import (
    DeterministicAcousticReasoningConsoleReporter,
)
from .deterministic_corrective_action_console import (
    DeterministicCorrectiveActionConsoleReporter,
)
from .evidence_acquisition_console import EvidenceAcquisitionPlanConsoleReporter
from .evidence_weighting_console import (
    DeterministicEvidenceWeightingConsoleReporter,
)
from .report import Report


class FullAssessmentConsoleReporter:
    """Delegates the complete workflow to the historical console reporters."""

    def __init__(self, reporters=None):
        self.reporters = reporters or (
            AcousticObservationConsoleReporter(),
            DeterministicAcousticReasoningConsoleReporter(),
            DeterministicCorrectiveActionConsoleReporter(),
            DeterministicEvidenceWeightingConsoleReporter(),
            EvidenceAcquisitionPlanConsoleReporter(),
        )

    def print(self, report: Report):
        for reporter in self.reporters:
            reporter.print(report)
