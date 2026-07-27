from dataclasses import dataclass
from math import isfinite
from re import sub

from acousticbrain.models import (
    LoudspeakerMovementAxis,
    LoudspeakerMovementDirection,
    LoudspeakerPositioningExperimentAnalysis,
    LoudspeakerPositioningExperimentProposal,
    LoudspeakerPositioningProposalStatus,
    LoudspeakerPositioningTarget,
    RecommendationStatus,
    RoomSurfaceKind,
)


@dataclass(frozen=True)
class _Source:
    source_id: str
    recommendation_ids: tuple[str, ...]
    hypothesis_codes: tuple[str, ...]
    target: LoudspeakerPositioningTarget | None
    direction: LoudspeakerMovementDirection | None
    distance_m: float | None
    observable_codes: tuple[str, ...]
    confidence: float
    priority: int
    controlled_codes: tuple[str, ...]
    planned: bool
    deferred: bool
    geometry_required: bool
    geometry_available: bool
    reversible: bool
    surface_id: str | None
    geometry_candidate_id: str | None
    surface_role: RoomSurfaceKind | None
    observation_ids: tuple[str, ...]


class LoudspeakerPositioningExperimentEngine:
    """Projette une seule expérience depuis des décisions déjà structurées."""

    EXPLORATORY_STEP_M = 0.05
    REQUIRED_MEASUREMENTS = ("L", "R", "L+R")
    STANDARD_OBSERVABLES = (
        "global.domain.stereo.score",
        "bass_decay.maximum_decay_time_s",
        "etc.channel_specific_event_count",
        "spatial.left_right.level_difference_abs_db",
    )
    BASE_CONTROLS = (
        "LISTENING_POSITION",
        "LOUDSPEAKER_ORIENTATION",
        "MEASUREMENT_LEVEL",
        "MICROPHONE_POSITION",
        "REW_MEASUREMENT_PARAMETERS",
        "ROOM_CONFIGURATION",
    )
    PLACEMENT_RECOMMENDATION_CODES = {
        "CHECK_STEREO_PLACEMENT",
        "TEST_SPEAKER_DISTANCE",
        "VERIFY_SBIR_PLACEMENT",
        "VERIFY_SPEAKER_ROOM_ASYMMETRY",
    }
    RECOMMENDATION_OBSERVABLES = {
        "CHECK_STEREO_PLACEMENT": (
            "stereo.symmetry_score",
            "spatial.left_right.level_difference_abs_db",
        ),
        "TEST_SPEAKER_DISTANCE": (
            "sbir.target_null_frequency_hz",
            "sbir.target_null_prominence_db",
        ),
        "VERIFY_SBIR_PLACEMENT": (
            "sbir.predicted_cancellation_frequency_hz",
            "SBIR_MOVES_WITH_SPEAKER",
            "SBIR_REMAINS_FIXED",
        ),
        "VERIFY_SPEAKER_ROOM_ASYMMETRY": (
            "stereo.symmetry_score",
            "spatial.left_right.level_difference_abs_db",
            "etc.channel_specific_event_difference",
        ),
    }
    RULE_CODES = (
        "POSITIONING_REQUIRE_EXPLICIT_SOURCE",
        "POSITIONING_PREFER_EXISTING_PLAN",
        "POSITIONING_REQUIRE_UNAMBIGUOUS_TARGET",
        "POSITIONING_REQUIRE_EXPLICIT_DIRECTION",
        "POSITIONING_REQUIRE_SINGLE_CHANGED_VARIABLE",
        "POSITIONING_REQUIRE_PROTOCOL_CONTROLS",
        "POSITIONING_REQUIRE_L_R_STEREO",
        "POSITIONING_REQUIRE_EXISTING_OBSERVABLES",
        "POSITIONING_REQUIRE_SOURCE_GEOMETRY_WHEN_APPLICABLE",
        "POSITIONING_BLOCK_USER_DEFERRED_SOURCE",
        "POSITIONING_REJECT_EQUAL_PRIORITY_TIE",
        "POSITIONING_REUSE_SOURCE_DISTANCE_OR_FIVE_CM_PROTOCOL_STEP",
        "POSITIONING_NEVER_ESTABLISH_CAUSALITY",
    )

    def analyze(
        self,
        *,
        experiment_planning=None,
        recommendation_analysis=None,
        room_geometry=None,
        measurements_available=True,
    ):
        planned = self._planned_source(experiment_planning, room_geometry)
        if planned is not None:
            return self._evaluate((planned,), measurements_available)

        sources = self._recommendation_sources(
            recommendation_analysis,
            room_geometry,
        )
        if not sources:
            return self._negative(
                LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE,
                ("NO_ACTIVE_LOUDSPEAKER_POSITIONING_SOURCE",),
                (),
            )
        active = tuple(item for item in sources if not item.deferred)
        if not active:
            return self._negative(
                LoudspeakerPositioningProposalStatus.BLOCKED_BY_USER_DECISION,
                ("SOURCE_DEFERRED_BY_USER",),
                tuple(item.source_id for item in sources),
            )
        highest = max(item.priority for item in active)
        peers = tuple(item for item in active if item.priority == highest)
        if len(peers) > 1:
            return self._negative(
                LoudspeakerPositioningProposalStatus.AMBIGUOUS,
                ("EQUAL_PRIORITY_POSITIONING_SOURCES",),
                tuple(sorted(item.source_id for item in peers)),
            )
        return self._evaluate(peers, measurements_available)

    def _evaluate(self, sources, measurements_available):
        source = sources[0]
        considered = tuple(item.source_id for item in sources)
        if source.deferred:
            return self._negative(
                LoudspeakerPositioningProposalStatus.BLOCKED_BY_USER_DECISION,
                ("SOURCE_DEFERRED_BY_USER",),
                considered,
            )
        if source.geometry_required and not source.geometry_available:
            return self._negative(
                LoudspeakerPositioningProposalStatus.MISSING_GEOMETRY,
                ("SOURCE_GEOMETRY_MISSING",),
                considered,
            )
        if source.target is None:
            return self._negative(
                LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE,
                ("LOUDSPEAKER_TARGET_AMBIGUOUS",),
                considered,
            )
        if source.direction is None:
            return self._negative(
                LoudspeakerPositioningProposalStatus.MISSING_DIRECTION,
                ("EXPLICIT_MOVEMENT_DIRECTION_MISSING",),
                considered,
            )
        if not source.reversible:
            return self._negative(
                LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE,
                ("SOURCE_NOT_REVERSIBLE",),
                considered,
            )
        if not measurements_available:
            return self._negative(
                LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE,
                ("L_R_STEREO_MEASUREMENTS_UNAVAILABLE",),
                considered,
            )
        if not source.observable_codes:
            return self._negative(
                LoudspeakerPositioningProposalStatus.NOT_ELIGIBLE,
                ("OBSERVABLE_FACTS_MISSING",),
                considered,
            )
        distance = (
            source.distance_m
            if self._positive_distance(source.distance_m)
            else self.EXPLORATORY_STEP_M
        )
        status = (
            LoudspeakerPositioningProposalStatus.ALREADY_PLANNED
            if source.planned
            else LoudspeakerPositioningProposalStatus.ELIGIBLE
        )
        controls = self._controls(source)
        proposal = LoudspeakerPositioningExperimentProposal(
            proposal_id=self._proposal_id(source, distance),
            source_recommendation_ids=source.recommendation_ids,
            source_hypothesis_codes=source.hypothesis_codes,
            target=source.target,
            movement_axis=self._axis(source.direction),
            movement_direction=source.direction,
            step_distance_m=distance,
            tested_variable="LOUDSPEAKER_POSITION",
            controlled_variables=controls,
            required_measurements=self.REQUIRED_MEASUREMENTS,
            expected_observables=tuple(dict.fromkeys((
                *self.STANDARD_OBSERVABLES,
                *source.observable_codes,
            ))),
            rationale=(
                "La source fournit une cible et une direction explicites.",
                "Le test modifie uniquement la position des enceintes ciblées.",
                "Le pas est une granularité expérimentale réversible, pas une "
                "position optimale prédite.",
                "La position physique doit être mesurée et consignée avant et "
                "après le déplacement.",
                "L’expérience contrôlée doit être déclarée explicitement avant "
                "ou après l’acquisition.",
            ),
            confidence=source.confidence,
            causality_status="NOT_ESTABLISHED",
            proposal_status=status,
            provenance=(
                ("source", source.source_id),
                ("target", "SOURCE_PARAMETER"),
                ("movement_direction", "SOURCE_PARAMETER"),
                (
                    "step_distance_m",
                    "SOURCE_PARAMETER"
                    if self._positive_distance(source.distance_m)
                    else "OPERATIONAL_FIVE_CM_POLICY",
                ),
                ("controlled_variables", "PR044_PROTOCOL_CONTRACT"),
                (
                    "expected_observables",
                    "PR044_EXISTING_COMPARISON_FACTS_AND_SOURCE_CODES",
                ),
                ("causality_status", "PR044_CAUSAL_LIMIT"),
            ),
            source_surface_id=source.surface_id,
            source_geometry_candidate_id=source.geometry_candidate_id,
            source_surface_role=source.surface_role,
            source_observation_ids=source.observation_ids,
        )
        return LoudspeakerPositioningExperimentAnalysis(
            proposal=proposal,
            proposal_status=status,
            blocking_reason_codes=(),
            considered_source_ids=considered,
            applied_rule_codes=self.RULE_CODES,
        )

    def _planned_source(self, analysis, room_geometry):
        plan = getattr(analysis, "plan", None)
        candidate = getattr(plan, "recommended_candidate", None)
        if candidate is None or candidate.changed_variable_codes != (
            "LOUDSPEAKER_POSITION",
        ):
            return None
        parameters = dict(candidate.parameters)
        geometry_required = (
            candidate.source_protocol_id == "protocol.temporary_move_speaker.v1"
        )
        surface_id = self._identifier(parameters.get("surface"))
        return _Source(
            source_id=candidate.candidate_id,
            recommendation_ids=(
                candidate.source_action_code
                if candidate.source_action_code is not None
                else candidate.candidate_id,
            ),
            hypothesis_codes=(candidate.hypothesis_code,),
            target=self._target(parameters.get("speaker_id")),
            direction=self._direction(parameters),
            distance_m=parameters.get("proposed_displacement_m"),
            observable_codes=tuple(candidate.observable_fact_codes),
            confidence=candidate.confidence,
            priority=10_000,
            controlled_codes=tuple(candidate.controlled_variable_codes),
            planned=True,
            deferred=False,
            geometry_required=geometry_required,
            geometry_available=(
                not geometry_required
                or self._candidate_geometry_available(parameters, room_geometry)
            ),
            reversible=getattr(candidate.reversibility, "name", None) == "HIGH",
            surface_id=surface_id,
            geometry_candidate_id=self._identifier(
                parameters.get("geometry_candidate_id")
            ),
            surface_role=self._surface_role(surface_id, room_geometry),
            observation_ids=(),
        )

    def _recommendation_sources(self, analysis, room_geometry):
        recommendations = getattr(analysis, "recommendations", ())
        return tuple(
            self._recommendation_source(item, room_geometry)
            for item in recommendations
            if item.code in self.PLACEMENT_RECOMMENDATION_CODES
        )

    def _recommendation_source(self, item, room_geometry):
        parameters = dict(item.parameters)
        geometry_required = item.code in {
            "TEST_SPEAKER_DISTANCE",
            "VERIFY_SBIR_PLACEMENT",
        }
        surface_id = self._identifier(parameters.get("surface"))
        return _Source(
            source_id=item.code,
            recommendation_ids=(item.code,),
            hypothesis_codes=tuple(item.hypothesis_codes),
            target=self._target(
                parameters.get("speaker_id")
                or ("STEREO" if item.target == "stereo_speakers" else None)
            ),
            direction=self._direction(parameters),
            distance_m=parameters.get("proposed_displacement_m"),
            observable_codes=self.RECOMMENDATION_OBSERVABLES.get(item.code, ()),
            confidence=float(item.confidence),
            priority=int(item.priority),
            controlled_codes=(),
            planned=False,
            deferred=item.status is RecommendationStatus.DEFERRED,
            geometry_required=geometry_required,
            geometry_available=(
                not geometry_required
                or self._candidate_geometry_available(parameters, room_geometry)
            ),
            reversible=True,
            surface_id=surface_id,
            geometry_candidate_id=self._identifier(
                parameters.get("geometry_candidate_id")
            ),
            surface_role=self._surface_role(surface_id, room_geometry),
            observation_ids=(),
        )

    @classmethod
    def _controls(cls, source):
        values = [*cls.BASE_CONTROLS, *source.controlled_codes]
        if source.target is not LoudspeakerPositioningTarget.BOTH_SPEAKERS:
            values.append("OTHER_LOUDSPEAKER_POSITION")
        else:
            values.append("LOUDSPEAKER_PAIR_SYMMETRY")
        if source.direction in {
            LoudspeakerMovementDirection.FORWARD,
            LoudspeakerMovementDirection.BACKWARD,
        }:
            values.append("LOUDSPEAKER_SEPARATION")
        return tuple(sorted(set(values)))

    @staticmethod
    def _target(value):
        if not isinstance(value, str):
            return None
        return {
            "LEFT": LoudspeakerPositioningTarget.LEFT_SPEAKER,
            "LEFT_SPEAKER": LoudspeakerPositioningTarget.LEFT_SPEAKER,
            "RIGHT": LoudspeakerPositioningTarget.RIGHT_SPEAKER,
            "RIGHT_SPEAKER": LoudspeakerPositioningTarget.RIGHT_SPEAKER,
            "STEREO": LoudspeakerPositioningTarget.BOTH_SPEAKERS,
            "BOTH": LoudspeakerPositioningTarget.BOTH_SPEAKERS,
            "BOTH_SPEAKERS": LoudspeakerPositioningTarget.BOTH_SPEAKERS,
        }.get(value.strip().upper())

    @staticmethod
    def _direction(parameters):
        aliases = {
            "FORWARD": LoudspeakerMovementDirection.FORWARD,
            "VERS L’AVANT": LoudspeakerMovementDirection.FORWARD,
            "VERS L'AVANT": LoudspeakerMovementDirection.FORWARD,
            "BACKWARD": LoudspeakerMovementDirection.BACKWARD,
            "VERS L’ARRIÈRE": LoudspeakerMovementDirection.BACKWARD,
            "VERS L'ARRIERE": LoudspeakerMovementDirection.BACKWARD,
            "INWARD": LoudspeakerMovementDirection.INWARD,
            "VERS L’INTÉRIEUR": LoudspeakerMovementDirection.INWARD,
            "VERS L'INTERIEUR": LoudspeakerMovementDirection.INWARD,
            "OUTWARD": LoudspeakerMovementDirection.OUTWARD,
            "VERS L’EXTÉRIEUR": LoudspeakerMovementDirection.OUTWARD,
            "VERS L'EXTERIEUR": LoudspeakerMovementDirection.OUTWARD,
        }
        for key in ("movement_direction", "proposed_direction", "direction"):
            value = parameters.get(key)
            if isinstance(value, str):
                result = aliases.get(value.strip().upper())
                if result is not None:
                    return result
        return None

    @staticmethod
    def _axis(direction):
        return (
            LoudspeakerMovementAxis.LONGITUDINAL
            if direction in {
                LoudspeakerMovementDirection.FORWARD,
                LoudspeakerMovementDirection.BACKWARD,
            }
            else LoudspeakerMovementAxis.LATERAL
        )

    @staticmethod
    def _candidate_geometry_available(parameters, room_geometry):
        required = (
            "geometry_candidate_id",
            "geometry_path_id",
            "surface",
            "speaker_id",
        )
        return (
            room_geometry is not None
            and bool(getattr(room_geometry, "speakers", ()))
            and all(parameters.get(key) is not None for key in required)
        )

    @staticmethod
    def _identifier(value):
        return value if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _surface_role(surface_id, room_geometry):
        if surface_id is None or room_geometry is None:
            return None
        for surface in getattr(room_geometry, "surfaces", ()):
            if (
                getattr(surface, "surface_id", None) == surface_id
                and isinstance(getattr(surface, "kind", None), RoomSurfaceKind)
            ):
                return surface.kind
        return None

    @staticmethod
    def _positive_distance(value):
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value > 0.0
        )

    @classmethod
    def _proposal_id(cls, source, distance):
        source_slug = sub(r"[^a-z0-9]+", "-", source.source_id.lower()).strip("-")
        millimeters = round(distance * 1000.0)
        return (
            "loudspeaker_positioning_proposal.v1."
            f"{source_slug}.{source.target.value.lower()}."
            f"{source.direction.value.lower()}.{millimeters}mm"
        )

    def _negative(self, status, reasons, sources):
        return LoudspeakerPositioningExperimentAnalysis(
            proposal=None,
            proposal_status=status,
            blocking_reason_codes=tuple(reasons),
            considered_source_ids=tuple(sources),
            applied_rule_codes=self.RULE_CODES,
        )
