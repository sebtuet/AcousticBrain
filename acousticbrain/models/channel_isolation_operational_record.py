from dataclasses import dataclass
from enum import Enum


class AcquisitionSettingsReuseDeclaration(Enum):
    INTENDED_UNCHANGED = "INTENDED_UNCHANGED"
    NOT_INTENDED_UNCHANGED = "NOT_INTENDED_UNCHANGED"


def _exact_text(label, value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be exact non-empty text.")


def _fingerprint(value):
    if not isinstance(value, str) or len(value) != 64 or any(
        item not in "0123456789abcdef" for item in value
    ):
        raise ValueError("Operational record fingerprint must be canonical SHA-256.")


@dataclass(frozen=True)
class ChannelIsolationMicrophonePositionRecord:
    schema_version: int
    record_id: str
    plan_id: str
    plan_contract_fingerprint: str
    reference_geometry: str
    position_description: str
    orientation_description: str
    documentation_source: str
    user_note: str | None = None

    def __post_init__(self):
        if self.schema_version != 1 or isinstance(self.schema_version, bool):
            raise ValueError("Unsupported microphone-position record schema version.")
        for label in ("record_id", "plan_id", "reference_geometry", "position_description", "orientation_description", "documentation_source"):
            _exact_text(label, getattr(self, label))
        _fingerprint(self.plan_contract_fingerprint)
        if self.user_note is not None:
            _exact_text("user_note", self.user_note)


@dataclass(frozen=True)
class ChannelIsolationAcquisitionSettingsRecord:
    schema_version: int
    record_id: str
    plan_id: str
    plan_contract_fingerprint: str
    gain: str
    time_window: str
    signal_chain: str
    reuse_declaration: AcquisitionSettingsReuseDeclaration
    documentation_source: str
    user_note: str | None = None

    def __post_init__(self):
        if self.schema_version != 1 or isinstance(self.schema_version, bool):
            raise ValueError("Unsupported acquisition-settings record schema version.")
        for label in ("record_id", "plan_id", "gain", "time_window", "signal_chain", "documentation_source"):
            _exact_text(label, getattr(self, label))
        _fingerprint(self.plan_contract_fingerprint)
        if not isinstance(self.reuse_declaration, AcquisitionSettingsReuseDeclaration):
            raise ValueError("Acquisition settings reuse declaration is invalid.")
        if self.user_note is not None:
            _exact_text("user_note", self.user_note)
