from dataclasses import dataclass

from .evidence import EvidenceLevel
from .peak import Peak
from .room_mode import RoomMode
from .sbir_candidate import SBIRCandidate
from .peak_classification_type import PeakClassificationType


@dataclass
class PeakClassification:
    peak: Peak
    classification: PeakClassificationType
    confidence: float
    evidence_level: EvidenceLevel
    explanation: str
    room_mode: RoomMode | None = None
    sbir_candidate: SBIRCandidate | None = None
