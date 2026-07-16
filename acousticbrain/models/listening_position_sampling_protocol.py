from dataclasses import dataclass
from math import isfinite


SUPPORTED_POSITION_ROLES = ("REFERENCE", "FORWARD", "BACKWARD")
REQUIRED_POSITION_MEASUREMENTS = ("LEFT", "RIGHT", "STEREO")
REQUIRED_COMPLETION_CONDITION_CODES = (
    "REFERENCE_POSITION_PRESENT",
    "FORWARD_POSITION_PRESENT",
    "BACKWARD_POSITION_PRESENT",
    "STRUCTURED_GEOMETRY_AVAILABLE",
    "REQUIRED_MEASUREMENTS_AVAILABLE",
    "COMPARABILITY_RULE_SATISFIED",
)


@dataclass(frozen=True)
class ListeningPositionSamplingPosition:
    position_code: str
    position_role: str
    longitudinal_offset_m: float | None
    lateral_offset_m: float | None
    vertical_offset_m: float | None
    parent_position_code: str | None
    reference_position_code: str | None
    acquisition_order: int
    required_measurements: tuple[str, ...]

    def __post_init__(self):
        if (
            not isinstance(self.position_code, str)
            or not self.position_code
            or self.position_role not in SUPPORTED_POSITION_ROLES
        ):
            raise ValueError("Listening-position sampling identity and role are required.")
        for value in (self.parent_position_code, self.reference_position_code):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError("Listening-position relations are invalid.")
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
                raise ValueError("Listening-position offsets must be finite when present.")
        if (
            not isinstance(self.acquisition_order, int)
            or isinstance(self.acquisition_order, bool)
            or self.acquisition_order < 1
        ):
            raise ValueError("Listening-position acquisition order must be positive.")
        if not isinstance(self.required_measurements, tuple):
            raise ValueError("Listening-position required measurements must be a tuple.")
        if not self.required_measurements or any(
            not isinstance(item, str) or not item
            for item in self.required_measurements
        ) or len(self.required_measurements) != len(set(self.required_measurements)):
            raise ValueError("Listening-position required measurements are invalid.")


@dataclass(frozen=True)
class ListeningPositionSamplingAcquisition:
    position_code: str
    available_measurements: tuple[str, ...]
    parent_position_code: str | None
    reference_position_code: str | None

    def __post_init__(self):
        if not isinstance(self.position_code, str) or not self.position_code:
            raise ValueError("Acquired listening-position code is required.")
        if not isinstance(self.available_measurements, tuple) or any(
            not isinstance(item, str) or not item
            for item in self.available_measurements
        ) or len(self.available_measurements) != len(set(self.available_measurements)):
            raise ValueError("Acquired listening-position measurements are invalid.")


@dataclass(frozen=True)
class ListeningPositionSamplingCompleteness:
    reference_present: bool
    forward_present: bool
    backward_present: bool
    structured_geometry_available: bool
    required_measurements_available: bool
    comparability_respected: bool
    missing_condition_codes: tuple[str, ...]

    @property
    def complete(self):
        return not self.missing_condition_codes


@dataclass(frozen=True)
class ListeningPositionSamplingProtocol:
    protocol_id: str
    version: int
    positions: tuple[ListeningPositionSamplingPosition, ...]
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    comparability_rule_code: str
    completion_condition_codes: tuple[str, ...]

    def __post_init__(self):
        collections = (
            self.positions,
            self.modified_variables,
            self.controlled_variables,
            self.completion_condition_codes,
        )
        if not isinstance(self.protocol_id, str) or not self.protocol_id or any(
            not isinstance(collection, tuple) for collection in collections
        ):
            raise ValueError("Listening-position sampling protocol is invalid.")
        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
        ):
            raise ValueError("Listening-position sampling version must be positive.")
        if self.modified_variables != ("LISTENING_POSITION",):
            raise ValueError("The sampling protocol modifies LISTENING_POSITION only.")
        if (
            not self.controlled_variables
            or any(
                not isinstance(item, str) or not item
                for item in self.controlled_variables
            )
            or len(self.controlled_variables) != len(set(self.controlled_variables))
            or set(self.modified_variables) & set(self.controlled_variables)
        ):
            raise ValueError("Sampling protocol variables are invalid.")
        if (
            not isinstance(self.comparability_rule_code, str)
            or not self.comparability_rule_code
        ):
            raise ValueError("A sampling comparability rule is required.")
        if self.completion_condition_codes != REQUIRED_COMPLETION_CONDITION_CODES:
            raise ValueError("Sampling completion conditions must be explicit.")
        self._validate_positions()

    def _validate_positions(self):
        if any(
            not isinstance(item, ListeningPositionSamplingPosition)
            for item in self.positions
        ):
            raise ValueError("Sampling positions must use the structured model.")
        codes = tuple(item.position_code for item in self.positions)
        orders = tuple(item.acquisition_order for item in self.positions)
        if len(codes) != len(set(codes)):
            raise ValueError("Sampling position codes must be unique.")
        if orders != tuple(range(1, len(orders) + 1)):
            raise ValueError("Sampling positions must follow their declared order.")
        known_codes = set(codes)
        order_by_code = {
            item.position_code: item.acquisition_order for item in self.positions
        }
        for position in self.positions:
            parent = position.parent_position_code
            reference = position.reference_position_code
            if parent is not None and (
                parent not in known_codes
                or order_by_code[parent] >= position.acquisition_order
            ):
                raise ValueError("Sampling parent relations must be explicit and ordered.")
            if reference is not None and reference not in known_codes:
                raise ValueError("Sampling reference relations must be explicit.")

    @property
    def reference_position(self):
        references = tuple(
            item for item in self.positions if item.position_role == "REFERENCE"
        )
        return references[0] if len(references) == 1 else None

    @property
    def definition_completeness(self):
        return self._completeness(
            tuple(
                ListeningPositionSamplingAcquisition(
                    position_code=item.position_code,
                    available_measurements=item.required_measurements,
                    parent_position_code=item.parent_position_code,
                    reference_position_code=item.reference_position_code,
                )
                for item in self.positions
            )
        )

    def assess(self, acquisitions):
        if not isinstance(acquisitions, tuple) or any(
            not isinstance(item, ListeningPositionSamplingAcquisition)
            for item in acquisitions
        ):
            raise ValueError("Sampling acquisitions must be a tuple.")
        codes = tuple(item.position_code for item in acquisitions)
        if len(codes) != len(set(codes)):
            raise ValueError("Sampling acquisitions must have unique positions.")
        return self._completeness(acquisitions)

    def _completeness(self, acquisitions):
        acquired = {item.position_code: item for item in acquisitions}
        positions_by_role = {
            role: tuple(
                item for item in self.positions if item.position_role == role
            )
            for role in SUPPORTED_POSITION_ROLES
        }
        reference_present = bool(
            len(positions_by_role["REFERENCE"]) == 1
            and positions_by_role["REFERENCE"][0].position_code in acquired
        )
        forward_present = bool(
            positions_by_role["FORWARD"]
            and all(item.position_code in acquired for item in positions_by_role["FORWARD"])
        )
        backward_present = bool(
            positions_by_role["BACKWARD"]
            and all(item.position_code in acquired for item in positions_by_role["BACKWARD"])
        )
        structured_geometry_available = self._structured_geometry_available()
        required_measurements_available = bool(
            self.positions
            and all(
                position.required_measurements == REQUIRED_POSITION_MEASUREMENTS
                and position.position_code in acquired
                and set(position.required_measurements).issubset(
                    acquired[position.position_code].available_measurements
                )
                for position in self.positions
            )
        )
        comparability_respected = bool(
            self.positions
            and self._comparability_structure_valid()
            and all(
                position.position_code in acquired
                and acquired[position.position_code].parent_position_code
                == position.parent_position_code
                and acquired[position.position_code].reference_position_code
                == position.reference_position_code
                for position in self.positions
            )
        )
        values = (
            ("REFERENCE_POSITION_PRESENT", reference_present),
            ("FORWARD_POSITION_PRESENT", forward_present),
            ("BACKWARD_POSITION_PRESENT", backward_present),
            ("STRUCTURED_GEOMETRY_AVAILABLE", structured_geometry_available),
            ("REQUIRED_MEASUREMENTS_AVAILABLE", required_measurements_available),
            ("COMPARABILITY_RULE_SATISFIED", comparability_respected),
        )
        return ListeningPositionSamplingCompleteness(
            reference_present=reference_present,
            forward_present=forward_present,
            backward_present=backward_present,
            structured_geometry_available=structured_geometry_available,
            required_measurements_available=required_measurements_available,
            comparability_respected=comparability_respected,
            missing_condition_codes=tuple(
                code for code, satisfied in values if not satisfied
            ),
        )

    def _comparability_structure_valid(self):
        reference = self.reference_position
        if reference is None:
            return False
        if (
            reference.parent_position_code is not None
            or reference.reference_position_code != reference.position_code
        ):
            return False
        return all(
            position.parent_position_code is not None
            and position.reference_position_code == reference.position_code
            for position in self.positions
            if position.position_code != reference.position_code
        )

    def _structured_geometry_available(self):
        reference = self.reference_position
        if reference is None or reference.longitudinal_offset_m != 0.0:
            return False
        if any(
            value not in (None, 0.0)
            for value in (reference.lateral_offset_m, reference.vertical_offset_m)
        ):
            return False
        for position in self.positions:
            if position.position_role == "FORWARD" and not (
                position.longitudinal_offset_m is not None
                and position.longitudinal_offset_m > 0.0
            ):
                return False
            if position.position_role == "BACKWARD" and not (
                position.longitudinal_offset_m is not None
                and position.longitudinal_offset_m < 0.0
            ):
                return False
        return True
