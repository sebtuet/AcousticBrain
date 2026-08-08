from dataclasses import dataclass
from enum import Enum

from .impulse_channel import ImpulseChannel


class PlanCoverageStatus(Enum):
    NOT_APPLICABLE = "PLAN_COVERAGE_NOT_APPLICABLE"
    INSUFFICIENT_DECLARATION = "PLAN_COVERAGE_INSUFFICIENT_DECLARATION"
    PARTIAL = "PLAN_COVERAGE_PARTIAL"
    COMPLETE = "PLAN_COVERAGE_COMPLETE"


@dataclass(frozen=True)
class ChannelIsolationDeclaration:
    repeated_channels: tuple[ImpulseChannel, ...]
    available_inputs: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    independent_variables: tuple[str, ...]
    measurements: tuple[str, ...]

    def __post_init__(self):
        if not all(
            isinstance(values, tuple)
            for values in (
                self.repeated_channels,
                self.available_inputs,
                self.controlled_variables,
                self.independent_variables,
                self.measurements,
            )
        ):
            raise ValueError("Channel isolation declaration values must be tuples.")
        if len(self.repeated_channels) != len(set(self.repeated_channels)):
            raise ValueError("Repeated channel declarations must be unique.")
        if any(
            channel not in (ImpulseChannel.LEFT, ImpulseChannel.RIGHT)
            for channel in self.repeated_channels
        ):
            raise ValueError(
                "Channel isolation repetitions support LEFT and RIGHT only."
            )
        for values in (
            self.available_inputs,
            self.controlled_variables,
            self.independent_variables,
            self.measurements,
        ):
            if (
                len(values) != len(set(values))
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ValueError(
                    "Channel isolation declaration identifiers must be unique "
                    "non-empty strings."
                )


@dataclass(frozen=True)
class ChannelIsolationPreparationProvenance:
    schema_version: int
    confirmation_id: str
    plan_id: str
    plan_contract_fingerprint: str
    qualification_status: str

    def __post_init__(self):
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != 1
        ):
            raise ValueError(
                "Unsupported channel-isolation preparation provenance version."
            )
        for label, value in (
            ("confirmation_id", self.confirmation_id),
            ("plan_id", self.plan_id),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError(
                    f"Channel-isolation preparation {label} must be exact text."
                )
        if (
            not isinstance(self.plan_contract_fingerprint, str)
            or len(self.plan_contract_fingerprint) != 64
            or any(
                value not in "0123456789abcdef"
                for value in self.plan_contract_fingerprint
            )
        ):
            raise ValueError(
                "Channel-isolation preparation fingerprint is invalid."
            )
        if self.qualification_status != "ALL_PREREQUISITES_USER_CONFIRMED":
            raise ValueError(
                "Channel-isolation preparation qualification is invalid."
            )


@dataclass(frozen=True)
class PlanCoverageResult:
    status: PlanCoverageStatus
    covered_requirements: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    unverifiable_requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        collections = (
            self.covered_requirements,
            self.missing_requirements,
            self.unverifiable_requirements,
            self.limitations,
        )
        if any(not isinstance(values, tuple) for values in collections):
            raise ValueError("Plan coverage result collections must be tuples.")
        if any(
            values != tuple(sorted(set(values)))
            or any(not isinstance(value, str) or not value for value in values)
            for values in collections
        ):
            raise ValueError(
                "Plan coverage result values must be sorted unique strings."
            )
