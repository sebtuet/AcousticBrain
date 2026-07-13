from dataclasses import dataclass
from enum import Enum

from .impulse_channel import ImpulseChannel


class ExperimentType(Enum):
    BASELINE = "BASELINE"
    EXPERIMENT = "EXPERIMENT"


class ExperimentState(Enum):
    READY = "READY"
    INCOMPLETE = "INCOMPLETE"


class ExperimentFileType(Enum):
    WAV = "WAV"
    TXT_MEASUREMENT = "TXT_MEASUREMENT"
    TXT_IMPULSE = "TXT_IMPULSE"
    TXT_UNKNOWN = "TXT_UNKNOWN"
    MDAT = "MDAT"


@dataclass(frozen=True)
class ExperimentFileDescriptor:
    relative_path: str
    file_type: ExperimentFileType
    sha256: str
    channel: ImpulseChannel | None = None


@dataclass(frozen=True)
class ExperimentDescriptor:
    experiment_id: str
    directory: str
    experiment_type: ExperimentType
    available_files: tuple[ExperimentFileDescriptor, ...]
    available_channels: tuple[ImpulseChannel, ...]
    wav_files: tuple[str, ...]
    txt_files: tuple[str, ...]
    mdat_file: str | None
    manifest_present: bool
    content_hash: str
    timestamp: str
    imported_at: str
    state: ExperimentState
    parent_experiment_ids: tuple[str, ...] = ()
    source_protocol_id: str | None = None
    source_hypothesis_code: str | None = None
    declared_change_codes: tuple[str, ...] = ()
    required_comparison_fact_codes: tuple[str, ...] = ()

    def __post_init__(self):
        collections = (
            self.available_files,
            self.available_channels,
            self.wav_files,
            self.txt_files,
            self.parent_experiment_ids,
            self.declared_change_codes,
            self.required_comparison_fact_codes,
        )
        if any(not isinstance(collection, tuple) for collection in collections):
            raise ValueError("Experiment descriptor collections must be tuples.")
        if not self.experiment_id or not self.directory or not self.content_hash:
            raise ValueError("Experiment descriptor identifiers are required.")
