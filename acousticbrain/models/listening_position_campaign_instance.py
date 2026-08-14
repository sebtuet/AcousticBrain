from dataclasses import dataclass
from enum import Enum
from math import isfinite
import re

from .listening_position_sampling_protocol import (
    ListeningPositionSamplingPosition,
    ListeningPositionSamplingProtocol,
    REQUIRED_COMPLETION_CONDITION_CODES,
    REQUIRED_POSITION_MEASUREMENTS,
    SUPPORTED_POSITION_ROLES,
)


MODAL_LISTENING_POSITION_PROTOCOL_ID = "protocol.verify_modal_bass_persistence.v1"
MODAL_LISTENING_POSITION_CONTROLLED_VARIABLES = (
    "LOUDSPEAKER_POSITION",
    "LOUDSPEAKER_ASSIGNMENT",
    "SIGNAL_CHAIN_ASSIGNMENT",
    "ROOM_CONFIGURATION",
    "MICROPHONE_ORIENTATION",
    "MEASUREMENT_LEVEL",
    "REW_PARAMETERS",
)
MODAL_LISTENING_POSITION_COMPARABILITY_RULE = (
    "LISTENING_POSITION_ORDERED_REFERENCE_BRANCH"
)


@dataclass(frozen=True)
class ListeningPositionCampaignProtocolContract:
    protocol_id: str
    protocol_version: int
    allowed_roles: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    comparability_rule: str
    completion_condition_codes: tuple[str, ...]


KNOWN_LISTENING_POSITION_CAMPAIGN_PROTOCOLS = (
    ListeningPositionCampaignProtocolContract(
        protocol_id=MODAL_LISTENING_POSITION_PROTOCOL_ID,
        protocol_version=1,
        allowed_roles=SUPPORTED_POSITION_ROLES,
        controlled_variables=MODAL_LISTENING_POSITION_CONTROLLED_VARIABLES,
        required_measurements=REQUIRED_POSITION_MEASUREMENTS,
        comparability_rule=MODAL_LISTENING_POSITION_COMPARABILITY_RULE,
        completion_condition_codes=REQUIRED_COMPLETION_CONDITION_CODES,
    ),
)


class ListeningPositionCampaignInstanceStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class ListeningPositionCampaignInstanceValidationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ListeningPositionCampaignInstancePosition:
    position_code: str
    position_role: str
    order_index: int
    longitudinal_offset_m: float | None
    lateral_offset_m: float | None
    vertical_offset_m: float | None
    parent_position_code: str | None
    reference_position_code: str | None
    reference_experiment_id: str | None
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.position_code, str) or not self.position_code:
            self._invalid("CAMPAIGN_INSTANCE_POSITION_INVALID", "Position code is required.")
        if re.fullmatch(r"exp-\d+", self.position_code, flags=re.IGNORECASE):
            self._invalid(
                "CAMPAIGN_INSTANCE_POSITION_INVALID",
                "Position codes cannot be future experiment identities.",
            )
        if self.position_role not in SUPPORTED_POSITION_ROLES:
            self._invalid("CAMPAIGN_INSTANCE_POSITION_INVALID", "Position role is unknown.")
        if (
            not isinstance(self.order_index, int)
            or isinstance(self.order_index, bool)
            or self.order_index < 1
        ):
            self._invalid(
                "CAMPAIGN_INSTANCE_POSITION_INVALID",
                "Position order must be a positive integer.",
            )
        for value in (
            self.longitudinal_offset_m,
            self.lateral_offset_m,
            self.vertical_offset_m,
        ):
            if value is not None and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(value)
            ):
                self._invalid(
                    "CAMPAIGN_INSTANCE_POSITION_INVALID",
                    "Position offsets must be finite numbers or null.",
                )
        for value in (
            self.parent_position_code,
            self.reference_position_code,
            self.reference_experiment_id,
        ):
            if value is not None and (not isinstance(value, str) or not value):
                self._invalid(
                    "CAMPAIGN_INSTANCE_RELATION_INVALID",
                    "Position relations must be non-empty strings or null.",
                )
        for value in (
            self.modified_variables,
            self.controlled_variables,
            self.required_measurements,
        ):
            if not isinstance(value, tuple):
                self._invalid(
                    "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                    "Position collections must be explicit arrays.",
                )

    @staticmethod
    def _invalid(code, message):
        raise ListeningPositionCampaignInstanceValidationError(code, message)


@dataclass(frozen=True)
class ListeningPositionCampaignInstance:
    instance_id: str
    protocol_id: str
    protocol_version: int
    reference_experiment_id: str | None
    positions: tuple[ListeningPositionCampaignInstancePosition, ...]
    comparability_rule: str
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    declaration_source: str
    declaration_version: int
    notes: str | None

    def __post_init__(self):
        if not isinstance(self.instance_id, str) or not self.instance_id:
            self._invalid("CAMPAIGN_INSTANCE_SCHEMA_INVALID", "Instance id is required.")
        if not isinstance(self.protocol_id, str) or not self.protocol_id:
            self._invalid("CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH", "Protocol id is required.")
        if (
            not isinstance(self.protocol_version, int)
            or isinstance(self.protocol_version, bool)
        ):
            self._invalid(
                "CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH",
                "Protocol version must be an integer.",
            )
        if not isinstance(self.positions, tuple) or any(
            not isinstance(item, ListeningPositionCampaignInstancePosition)
            for item in self.positions
        ):
            self._invalid(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                "Positions must use the campaign-instance model.",
            )
        for value in (self.controlled_variables, self.required_measurements):
            if not isinstance(value, tuple):
                self._invalid(
                    "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                    "Instance collections must be explicit arrays.",
                )
        if (
            not isinstance(self.declaration_source, str)
            or not self.declaration_source
            or not isinstance(self.declaration_version, int)
            or isinstance(self.declaration_version, bool)
            or self.declaration_version < 1
            or (self.notes is not None and not isinstance(self.notes, str))
        ):
            self._invalid(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                "Declaration provenance is invalid.",
            )
        if self.reference_experiment_id is None:
            self._invalid(
                "CAMPAIGN_INSTANCE_REFERENCE_INVALID",
                "A scientific reference experiment is required.",
            )
        if not isinstance(self.reference_experiment_id, str) or not self.reference_experiment_id:
            self._invalid(
                "CAMPAIGN_INSTANCE_REFERENCE_INVALID",
                "Reference experiment identity is invalid.",
            )
        contract = self.protocol_contract
        self._validate_protocol(contract)
        self._validate_positions(contract)

    @property
    def protocol_contract(self):
        matching_id = tuple(
            item
            for item in KNOWN_LISTENING_POSITION_CAMPAIGN_PROTOCOLS
            if item.protocol_id == self.protocol_id
        )
        if not matching_id:
            self._invalid(
                "CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH",
                f"Unknown listening-position protocol: {self.protocol_id}",
            )
        compatible = tuple(
            item for item in matching_id if item.protocol_version == self.protocol_version
        )
        if not compatible:
            self._invalid(
                "CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH",
                f"Unsupported protocol version: {self.protocol_version}",
            )
        return compatible[0]

    def _validate_protocol(self, contract):
        if self.controlled_variables != contract.controlled_variables:
            self._invalid(
                "CAMPAIGN_INSTANCE_CONTROLLED_VARIABLES_INCOMPATIBLE",
                "Controlled variables do not match the protocol contract.",
            )
        if self.required_measurements != contract.required_measurements:
            self._invalid(
                "CAMPAIGN_INSTANCE_MEASUREMENTS_INCOMPLETE",
                "Instance measurements must be LEFT, RIGHT and STEREO.",
            )
        if self.comparability_rule != contract.comparability_rule:
            self._invalid(
                "CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH",
                "Comparability rule does not match the protocol contract.",
            )

    def _validate_positions(self, contract):
        codes = tuple(item.position_code for item in self.positions)
        orders = tuple(item.order_index for item in self.positions)
        if not codes or len(codes) != len(set(codes)):
            self._invalid(
                "CAMPAIGN_INSTANCE_POSITION_INVALID",
                "Position codes must be present and unique.",
            )
        if len(orders) != len(set(orders)) or orders != tuple(
            range(1, len(orders) + 1)
        ):
            self._invalid(
                "CAMPAIGN_INSTANCE_POSITION_INVALID",
                "Position order must be unique, contiguous and already sorted.",
            )
        references = tuple(
            item for item in self.positions if item.position_role == "REFERENCE"
        )
        if len(references) != 1:
            self._invalid(
                "CAMPAIGN_INSTANCE_REFERENCE_INVALID",
                "Exactly one REFERENCE position is required.",
            )
        known = set(codes)
        order_by_code = {
            item.position_code: item.order_index for item in self.positions
        }
        reference = references[0]
        if (
            reference.longitudinal_offset_m != 0.0
            or reference.lateral_offset_m not in (None, 0.0)
            or reference.vertical_offset_m not in (None, 0.0)
            or reference.parent_position_code is not None
            or reference.reference_position_code != reference.position_code
            or reference.reference_experiment_id != self.reference_experiment_id
            or reference.modified_variables
        ):
            self._invalid(
                "CAMPAIGN_INSTANCE_REFERENCE_INVALID",
                "REFERENCE position structure is incompatible.",
            )
        roles = {item.position_role for item in self.positions}
        if not {"REFERENCE", "FORWARD", "BACKWARD"}.issubset(roles):
            self._invalid(
                "CAMPAIGN_INSTANCE_POSITION_INVALID",
                "REFERENCE, FORWARD and BACKWARD positions are required.",
            )
        for position in self.positions:
            if position.position_role not in contract.allowed_roles:
                self._invalid(
                    "CAMPAIGN_INSTANCE_POSITION_INVALID", "Position role is not allowed."
                )
            if position.controlled_variables != contract.controlled_variables:
                self._invalid(
                    "CAMPAIGN_INSTANCE_CONTROLLED_VARIABLES_INCOMPATIBLE",
                    "Position controls do not match the protocol.",
                )
            if position.required_measurements != contract.required_measurements:
                self._invalid(
                    "CAMPAIGN_INSTANCE_MEASUREMENTS_INCOMPLETE",
                    "Every position requires LEFT, RIGHT and STEREO.",
                )
            if position.reference_experiment_id != self.reference_experiment_id:
                self._invalid(
                    "CAMPAIGN_INSTANCE_REFERENCE_INVALID",
                    "Position reference experiment does not match the instance.",
                )
            parent = position.parent_position_code
            relation = position.reference_position_code
            if parent is not None and (
                parent not in known or order_by_code[parent] >= position.order_index
            ):
                self._invalid(
                    "CAMPAIGN_INSTANCE_RELATION_INVALID",
                    "Parent relation is unknown, cyclic or out of order.",
                )
            if relation is not None and relation not in known:
                self._invalid(
                    "CAMPAIGN_INSTANCE_RELATION_INVALID",
                    "Reference relation targets an unknown position.",
                )
            if position.position_role == "FORWARD" and not (
                position.longitudinal_offset_m is not None
                and position.longitudinal_offset_m > 0.0
            ):
                self._invalid(
                    "CAMPAIGN_INSTANCE_POSITION_INVALID",
                    "FORWARD position requires an explicit positive offset.",
                )
            if position.position_role == "BACKWARD" and not (
                position.longitudinal_offset_m is not None
                and position.longitudinal_offset_m < 0.0
            ):
                self._invalid(
                    "CAMPAIGN_INSTANCE_POSITION_INVALID",
                    "BACKWARD position requires an explicit negative offset.",
                )
            if position.position_role != "REFERENCE" and (
                position.parent_position_code is None
                or position.reference_position_code != reference.position_code
                or position.modified_variables != ("LISTENING_POSITION",)
            ):
                self._invalid(
                    "CAMPAIGN_INSTANCE_RELATION_INVALID",
                    "Moved branches require explicit parent, reference and variable.",
                )

    def to_sampling_protocol(self):
        contract = self.protocol_contract
        return ListeningPositionSamplingProtocol(
            protocol_id=self.protocol_id,
            version=self.protocol_version,
            positions=tuple(
                ListeningPositionSamplingPosition(
                    position_code=item.position_code,
                    position_role=item.position_role,
                    longitudinal_offset_m=item.longitudinal_offset_m,
                    lateral_offset_m=item.lateral_offset_m,
                    vertical_offset_m=item.vertical_offset_m,
                    parent_position_code=item.parent_position_code,
                    reference_position_code=item.reference_position_code,
                    acquisition_order=item.order_index,
                    required_measurements=item.required_measurements,
                )
                for item in self.positions
            ),
            modified_variables=("LISTENING_POSITION",),
            controlled_variables=self.controlled_variables,
            comparability_rule_code=self.comparability_rule,
            completion_condition_codes=contract.completion_condition_codes,
        )

    @staticmethod
    def _invalid(code, message):
        raise ListeningPositionCampaignInstanceValidationError(code, message)


@dataclass(frozen=True)
class ListeningPositionCampaignInstanceAnalysis:
    status: ListeningPositionCampaignInstanceStatus
    instance: ListeningPositionCampaignInstance | None
    blocking_reasons: tuple[str, ...]
    validation_messages: tuple[str, ...]
    source_path: str | None

    def __post_init__(self):
        if not isinstance(self.blocking_reasons, tuple) or not isinstance(
            self.validation_messages, tuple
        ):
            raise ValueError("Campaign-instance validation details must be tuples.")
        if self.status is ListeningPositionCampaignInstanceStatus.VALID and (
            self.instance is None or self.blocking_reasons or self.validation_messages
        ):
            raise ValueError("A VALID campaign instance requires a model and no errors.")
        if self.status is ListeningPositionCampaignInstanceStatus.INVALID and (
            not self.blocking_reasons or not self.validation_messages
        ):
            raise ValueError("An INVALID campaign instance requires structured errors.")
