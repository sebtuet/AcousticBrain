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
