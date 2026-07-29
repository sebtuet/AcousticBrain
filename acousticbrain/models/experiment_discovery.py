from dataclasses import dataclass, field
from enum import Enum

from .impulse_channel import ImpulseChannel
from .causal_discrimination import CausalDiscriminationDecision, CausalProtocolStep
from .experiment_declaration import ExperimentDeclaration
from .channel_isolation_plan_coverage import ChannelIsolationDeclaration
from .channel_isolation_plan_result import ChannelIsolationResultDeclaration
from .room_description import RoomDescription


ExperimentParameterValue = str | int | float | bool


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
    comparison_parameters: tuple[tuple[str, ExperimentParameterValue], ...] = ()
    causal_protocol_step: CausalProtocolStep | None = None
    causal_discrimination_decisions: tuple[CausalDiscriminationDecision, ...] = ()
    experiment_declaration: ExperimentDeclaration = field(
        default_factory=ExperimentDeclaration.unknown
    )
    source_evidence_acquisition_plan_id: str | None = None
    channel_isolation_declaration: ChannelIsolationDeclaration | None = None
    channel_isolation_result_declaration: (
        ChannelIsolationResultDeclaration | None
    ) = None
    room_description: RoomDescription | None = None

    def __post_init__(self):
        collections = (
            self.available_files,
            self.available_channels,
            self.wav_files,
            self.txt_files,
            self.parent_experiment_ids,
            self.declared_change_codes,
            self.required_comparison_fact_codes,
            self.comparison_parameters,
            self.causal_discrimination_decisions,
        )
        if any(not isinstance(collection, tuple) for collection in collections):
            raise ValueError("Experiment descriptor collections must be tuples.")
        if not self.experiment_id or not self.directory or not self.content_hash:
            raise ValueError("Experiment descriptor identifiers are required.")
        if (
            self.source_evidence_acquisition_plan_id is not None
            and (
                not isinstance(self.source_evidence_acquisition_plan_id, str)
                or not self.source_evidence_acquisition_plan_id
            )
        ):
            raise ValueError(
                "Source evidence acquisition plan id must be absent or non-empty."
            )
        if (
            self.channel_isolation_declaration is not None
            and not isinstance(
                self.channel_isolation_declaration,
                ChannelIsolationDeclaration,
            )
        ):
            raise ValueError(
                "Channel isolation declaration has an invalid type."
            )
        if (
            self.channel_isolation_result_declaration is not None
            and not isinstance(
                self.channel_isolation_result_declaration,
                ChannelIsolationResultDeclaration,
            )
        ):
            raise ValueError(
                "Channel isolation result declaration has an invalid type."
            )
        if (
            self.room_description is not None
            and not isinstance(self.room_description, RoomDescription)
        ):
            raise ValueError("Experiment room description has an invalid type.")
        if any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or not isinstance(item[1], (str, int, float, bool))
            for item in self.comparison_parameters
        ):
            raise ValueError("Experiment comparison parameters are invalid.")
