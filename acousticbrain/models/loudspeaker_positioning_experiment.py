from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .room_surface import RoomSurfaceKind


class LoudspeakerPositioningTarget(Enum):
    LEFT_SPEAKER = "LEFT_SPEAKER"
    RIGHT_SPEAKER = "RIGHT_SPEAKER"
    BOTH_SPEAKERS = "BOTH_SPEAKERS"


class LoudspeakerMovementAxis(Enum):
    LONGITUDINAL = "LONGITUDINAL"
    LATERAL = "LATERAL"


class LoudspeakerMovementDirection(Enum):
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"


class LoudspeakerPositioningProposalStatus(Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED_BY_USER_DECISION = "BLOCKED_BY_USER_DECISION"
    MISSING_GEOMETRY = "MISSING_GEOMETRY"
    MISSING_DIRECTION = "MISSING_DIRECTION"
    ALREADY_PLANNED = "ALREADY_PLANNED"


@dataclass(frozen=True)
class LoudspeakerPositioningExperimentProposal:
    proposal_id: str
    source_recommendation_ids: tuple[str, ...]
    source_hypothesis_codes: tuple[str, ...]
    target: LoudspeakerPositioningTarget
    movement_axis: LoudspeakerMovementAxis
    movement_direction: LoudspeakerMovementDirection
    step_distance_m: float
    tested_variable: str
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    expected_observables: tuple[str, ...]
    rationale: tuple[str, ...]
    confidence: float
    causality_status: str
    proposal_status: LoudspeakerPositioningProposalStatus
    provenance: tuple[tuple[str, str], ...]
    source_surface_id: str | None = None
    source_geometry_candidate_id: str | None = None
    source_surface_role: RoomSurfaceKind | None = None
    source_observation_ids: tuple[str, ...] = ()

    def __post_init__(self):
        tuple_fields = (
            self.source_recommendation_ids,
            self.source_hypothesis_codes,
            self.controlled_variables,
            self.required_measurements,
            self.expected_observables,
            self.rationale,
            self.provenance,
            self.source_observation_ids,
        )
        if not all(isinstance(value, tuple) for value in tuple_fields):
            raise ValueError("Positioning-proposal collections must be tuples.")
        for value in (
            self.source_surface_id,
            self.source_geometry_candidate_id,
        ):
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(
                    "Positioning-proposal source identifiers must be non-empty."
                )
        if (
            self.source_surface_role is not None
            and not isinstance(self.source_surface_role, RoomSurfaceKind)
        ):
            raise ValueError("Positioning-proposal surface role is invalid.")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in self.source_observation_ids
        ):
            raise ValueError(
                "Positioning-proposal observation identifiers must be non-empty."
            )
        if not self.proposal_id or not self.source_recommendation_ids:
            raise ValueError("A positioning proposal requires stable source identifiers.")
        if self.tested_variable != "LOUDSPEAKER_POSITION":
            raise ValueError("A positioning proposal may test only loudspeaker position.")
        if self.required_measurements != ("L", "R", "L+R"):
            raise ValueError("A positioning proposal requires L, R and L+R measurements.")
        if not self.controlled_variables or not self.expected_observables:
            raise ValueError("A positioning proposal requires controls and observables.")
        if (
            not isfinite(self.step_distance_m)
            or self.step_distance_m <= 0.0
        ):
            raise ValueError("The experimental positioning step must be positive.")
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 100.0:
            raise ValueError("Positioning-proposal confidence must be bounded.")
        if self.causality_status != "NOT_ESTABLISHED":
            raise ValueError("Positioning proposals cannot establish causality.")
        expected_axis = (
            LoudspeakerMovementAxis.LONGITUDINAL
            if self.movement_direction in {
                LoudspeakerMovementDirection.FORWARD,
                LoudspeakerMovementDirection.BACKWARD,
            }
            else LoudspeakerMovementAxis.LATERAL
        )
        if self.movement_axis is not expected_axis:
            raise ValueError("Movement direction and axis are inconsistent.")
        if self.proposal_status not in {
            LoudspeakerPositioningProposalStatus.ELIGIBLE,
            LoudspeakerPositioningProposalStatus.ALREADY_PLANNED,
        }:
            raise ValueError("Only positive statuses may carry a precise proposal.")


@dataclass(frozen=True)
class LoudspeakerPositioningExperimentAnalysis:
    proposal: LoudspeakerPositioningExperimentProposal | None
    proposal_status: LoudspeakerPositioningProposalStatus
    blocking_reason_codes: tuple[str, ...]
    considered_source_ids: tuple[str, ...]
    applied_rule_codes: tuple[str, ...]

    def __post_init__(self):
        if not all(isinstance(value, tuple) for value in (
            self.blocking_reason_codes,
            self.considered_source_ids,
            self.applied_rule_codes,
        )):
            raise ValueError("Positioning-analysis collections must be tuples.")
        positive = self.proposal_status in {
            LoudspeakerPositioningProposalStatus.ELIGIBLE,
            LoudspeakerPositioningProposalStatus.ALREADY_PLANNED,
        }
        if positive != (self.proposal is not None):
            raise ValueError("Positioning analysis status and proposal disagree.")
        if self.proposal is not None and (
            self.proposal.proposal_status is not self.proposal_status
        ):
            raise ValueError("Positioning proposal status must be preserved.")
