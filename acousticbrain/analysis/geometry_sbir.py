from math import cos, radians, sin

from acousticbrain.models import (
    GeometrySBIRAnalysis,
    GeometrySBIRCandidate,
    ReflectionSurface,
)


class GeometrySBIRPredictionEngine:
    """Projette des fréquences SBIR depuis les trajets PR-030, sans mesure."""

    SPEED_OF_SOUND_M_S = 343.0
    RULE_CODES = (
        "SBIR_GEOMETRY_CONSUME_FIRST_ORDER_PATHS",
        "SBIR_GEOMETRY_FIRST_CANCELLATION_V1",
        "SBIR_GEOMETRY_PRESERVE_PATH_UNCERTAINTY",
        "SBIR_GEOMETRY_RECTANGULAR_SURFACES_ONLY",
    )
    _BASE_RELATIONSHIPS = {
        ReflectionSurface.FRONT_WALL: "FRONT_WALL",
        ReflectionSurface.REAR_WALL: "REAR_WALL",
        ReflectionSurface.LEFT_WALL: "LEFT_SIDE_WALL",
        ReflectionSurface.RIGHT_WALL: "RIGHT_SIDE_WALL",
        ReflectionSurface.FLOOR: "FLOOR",
        ReflectionSurface.CEILING: "CEILING",
    }

    def analyze(self, geometry_reflections, room_geometry):
        paths = tuple(getattr(geometry_reflections, "paths", ()))
        if not paths or room_geometry is None:
            return GeometrySBIRAnalysis(
                candidates=(),
                source_analysis_codes=("GeometryEarlyReflectionAnalysis",),
                applied_rule_codes=self.RULE_CODES,
            )
        speakers = {item.point_id: item for item in room_geometry.speakers}
        orientations = {
            item.speaker_id: item.yaw_degrees
            for item in room_geometry.speaker_orientations
        }
        candidates = []
        for path in paths:
            speaker = speakers.get(path.speaker_id)
            if speaker is None or path.acoustic_path_difference_m <= 0.0:
                continue
            extra = path.acoustic_path_difference_m
            frequency = self.SPEED_OF_SOUND_M_S / (2.0 * extra)
            distance_uncertainty = (
                path.uncertainty_ms / 1000.0 * self.SPEED_OF_SOUND_M_S
                if path.uncertainty_ms is not None
                else None
            )
            frequency_uncertainty = (
                frequency * distance_uncertainty / extra
                if distance_uncertainty is not None
                else None
            )
            candidates.append(GeometrySBIRCandidate(
                candidate_id=f"geometry_sbir.{path.path_id}",
                geometry_path_id=path.path_id,
                speaker_id=path.speaker_id,
                listening_position_id=path.listening_position_id,
                surface_id=path.surface_id,
                base_surface_id=path.base_surface_id,
                surface=path.surface,
                relationship_code=self._relationship(
                    path.surface,
                    orientations.get(path.speaker_id),
                ),
                impact_point=path.impact_point,
                direct_path_m=path.direct_path_m,
                reflected_path_m=path.reflected_path_m,
                extra_distance_m=extra,
                speaker_boundary_distance_m=self._boundary_distance(
                    path.surface, speaker, room_geometry.dimensions
                ),
                expected_cancellation_frequency_hz=frequency,
                distance_uncertainty_m=distance_uncertainty,
                frequency_uncertainty_hz=frequency_uncertainty,
                confidence=path.confidence,
                provenance_codes=path.provenance_codes,
            ))
        return GeometrySBIRAnalysis(
            candidates=tuple(sorted(candidates, key=lambda item: item.candidate_id)),
            source_analysis_codes=(
                "GeometryEarlyReflectionAnalysis",
                "RoomGeometry",
            ),
            applied_rule_codes=self.RULE_CODES,
        )

    @classmethod
    def _relationship(cls, surface, yaw_degrees):
        relationship = cls._BASE_RELATIONSHIPS[surface]
        if yaw_degrees is None or surface in {
            ReflectionSurface.FLOOR,
            ReflectionSurface.CEILING,
        }:
            return relationship
        forward = (cos(radians(yaw_degrees)), sin(radians(yaw_degrees)))
        direction = {
            ReflectionSurface.FRONT_WALL: (-1.0, 0.0),
            ReflectionSurface.REAR_WALL: (1.0, 0.0),
            ReflectionSurface.LEFT_WALL: (0.0, -1.0),
            ReflectionSurface.RIGHT_WALL: (0.0, 1.0),
        }[surface]
        return (
            "WALL_BEHIND_SPEAKER"
            if forward[0] * direction[0] + forward[1] * direction[1] < -0.707
            else relationship
        )

    @staticmethod
    def _boundary_distance(surface, speaker, dimensions):
        return {
            ReflectionSurface.FRONT_WALL: speaker.x_m,
            ReflectionSurface.REAR_WALL: dimensions.length_m - speaker.x_m,
            ReflectionSurface.LEFT_WALL: speaker.y_m,
            ReflectionSurface.RIGHT_WALL: dimensions.width_m - speaker.y_m,
            ReflectionSurface.FLOOR: speaker.z_m,
            ReflectionSurface.CEILING: dimensions.height_m - speaker.z_m,
        }[surface]


class SBIRGeometryCorrelationEngine:
    """Rapproche prédictions géométriques et creux observés, sans causalité."""

    MAXIMUM_FREQUENCY_ERROR_PERCENT = 15.0
    MINIMUM_MATCH_SCORE = 60.0
    RULE_CODES = (
        "SBIR_CORRELATE_EXISTING_PREDICTIONS_AND_DIPS",
        "SBIR_COMPATIBILITY_IS_NOT_CAUSAL_PROOF",
        "SBIR_DETERMINISTIC_BEST_MATCH_V1",
    )

    def analyze(
        self,
        geometry_analysis,
        observed_dips,
        *,
        maximum_frequency_error_percent=MAXIMUM_FREQUENCY_ERROR_PERCENT,
        minimum_match_score=MINIMUM_MATCH_SCORE,
    ):
        from acousticbrain.models import (
            SBIRGeometryCorrelation,
            SBIRGeometryCorrelationAnalysis,
        )

        if maximum_frequency_error_percent <= 0.0:
            raise ValueError("SBIR frequency tolerance must be positive.")
        if not 0.0 <= minimum_match_score <= 100.0:
            raise ValueError("SBIR minimum match score must be bounded.")
        candidates = tuple(getattr(geometry_analysis, "candidates", ()))
        dips = tuple(observed_dips or ())
        correlations = []
        matched_ids = set()
        for candidate in candidates:
            if not dips:
                continue
            dip = min(
                dips,
                key=lambda item: (
                    abs(
                        item.frequency
                        - candidate.expected_cancellation_frequency_hz
                    ),
                    item.frequency,
                    item.index,
                ),
            )
            error_hz = abs(
                dip.frequency - candidate.expected_cancellation_frequency_hz
            )
            error_percent = (
                error_hz / candidate.expected_cancellation_frequency_hz * 100.0
            )
            if error_percent > maximum_frequency_error_percent:
                continue
            frequency_score = 100.0 * (
                1.0 - error_percent / maximum_frequency_error_percent
            )
            prominence_score = min(100.0, max(0.0, dip.prominence) * 10.0)
            match_score = 0.8 * frequency_score + 0.2 * prominence_score
            if match_score < minimum_match_score:
                continue
            geometry_confidence = candidate.confidence
            confidence = (
                (match_score + geometry_confidence) / 2.0
                if geometry_confidence is not None
                else match_score
            )
            correlations.append(SBIRGeometryCorrelation(
                code=(
                    f"sbir_geometry.{candidate.speaker_id.lower()}."
                    f"{candidate.surface_id.lower()}.{dip.index}"
                ),
                candidate=candidate,
                observed_dip=dip,
                frequency_error_hz=error_hz,
                frequency_error_percent=error_percent,
                match_score=match_score,
                confidence=confidence,
                source_analysis_codes=(
                    "GeometrySBIRAnalysis",
                    "PeakDetectionAnalysis",
                ),
                provenance_codes=candidate.provenance_codes,
            ))
            matched_ids.add(candidate.candidate_id)
        ordered = tuple(sorted(correlations, key=lambda item: item.code))
        best = max(
            ordered,
            key=lambda item: (
                item.match_score,
                item.observed_dip.prominence,
                -item.frequency_error_percent,
                item.code,
            ),
            default=None,
        )
        return SBIRGeometryCorrelationAnalysis(
            correlations=ordered,
            best_match=best,
            unmatched_candidate_ids=tuple(
                item.candidate_id
                for item in candidates
                if item.candidate_id not in matched_ids
            ),
            evaluated_candidate_count=len(candidates),
            observed_dip_count=len(dips),
            confidence=(
                sum(item.confidence for item in ordered) / len(ordered)
                if ordered else 0.0
            ),
            source_analysis_codes=(
                "GeometrySBIRAnalysis",
                "PeakDetectionAnalysis",
            ),
            applied_rule_codes=self.RULE_CODES,
        )
