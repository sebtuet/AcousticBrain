from dataclasses import dataclass
from enum import Enum

from .evidence_acquisition import EvidenceAcquisitionPlan


class ExperimentContractMode(Enum):
    EXPLORATORY = "EXPLORATORY"
    PRESCRIPTIVE = "PRESCRIPTIVE"


@dataclass(frozen=True)
class EvidenceAcquisitionPlanContract:
    source_plan: EvidenceAcquisitionPlan
    mode: ExperimentContractMode
    declaration_source: str
    reference_experiment_code: str
    declaration_user_note: str | None = None

    def __post_init__(self):
        if not isinstance(self.source_plan, EvidenceAcquisitionPlan):
            raise ValueError("An evidence-acquisition source plan is required.")
        if not isinstance(self.mode, ExperimentContractMode):
            raise ValueError("Experiment contract mode is invalid.")
        if not isinstance(self.declaration_source, str) or not self.declaration_source:
            raise ValueError("Experiment contract declaration source is required.")
        if (
            not isinstance(self.reference_experiment_code, str)
            or not self.reference_experiment_code
        ):
            raise ValueError("Experiment contract reference is required.")
        if self.declaration_user_note is not None and not isinstance(
            self.declaration_user_note, str
        ):
            raise ValueError("Experiment contract user note must be text or absent.")
