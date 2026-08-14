from statistics import fmean

from acousticbrain.models import (
    ETCAnalysis,
    ETCReflectionCorrelation,
    ETCReflectionCorrelationAnalysis,
    ReflectionSurface,
    SBIRAnalysis,
)


class ETCReflectionCorrelationEngine:
    """Rapproche des faits ETC et SBIR sans attribuer de surface implicitement."""

    MAXIMUM_TIMING_ERROR_MS = 1.0
    MINIMUM_SBIR_MATCH_SCORE = 60.0
    MINIMUM_CORRELATION_SCORE = 60.0

    def analyze(
        self,
        etc_analysis: ETCAnalysis,
        sbir_analysis: SBIRAnalysis | None,
        *,
        surfaces: tuple[ReflectionSurface, ...] | None = None,
        geometry_reflections=None,
        maximum_timing_error_ms: float = MAXIMUM_TIMING_ERROR_MS,
        minimum_sbir_match_score: float = MINIMUM_SBIR_MATCH_SCORE,
        minimum_correlation_score: float = MINIMUM_CORRELATION_SCORE,
    ) -> ETCReflectionCorrelationAnalysis:
        self._validate(
            maximum_timing_error_ms,
            minimum_sbir_match_score,
            minimum_correlation_score,
        )
        sbir_candidates = sbir_analysis.candidates if sbir_analysis else []
        allowed_surfaces = (
            set(surfaces)
            if surfaces is not None
            else {candidate.surface for candidate in sbir_candidates}
        )
        candidates = [
            candidate
            for candidate in sbir_candidates
            if candidate.surface in allowed_surfaces
            and candidate.match_score >= minimum_sbir_match_score
        ]
        available_surfaces = tuple(
            surface
            for surface in ReflectionSurface
            if any(candidate.surface is surface for candidate in candidates)
        )
        geometry_paths = tuple(
            path for path in getattr(geometry_reflections, "paths", ())
            if surfaces is None or path.surface in allowed_surfaces
        )
        available_surfaces = tuple(
            surface for surface in ReflectionSurface
            if surface in available_surfaces
            or any(path.surface is surface for path in geometry_paths)
        )
        correlations = []
        unmatched_events = {}
        evaluated_event_count = 0

        for channel in etc_analysis.available_channels:
            channel_analysis = etc_analysis.channels.get(channel)
            if channel_analysis is None:
                continue
            unmatched_events[channel] = []
            for event in channel_analysis.events:
                evaluated_event_count += 1
                correlation = self._best_correlation(
                    channel,
                    event,
                    candidates,
                    sbir_analysis,
                    maximum_timing_error_ms,
                    minimum_correlation_score,
                )
                geometry_correlation = self._best_geometry_correlation(
                    channel,
                    event,
                    geometry_paths,
                    maximum_timing_error_ms,
                    minimum_correlation_score,
                )
                if geometry_correlation is not None and (
                    correlation is None
                    or geometry_correlation.match_score > correlation.match_score
                ):
                    correlation = geometry_correlation
                if correlation is None:
                    unmatched_events[channel].append(event)
                else:
                    correlations.append(correlation)

        return ETCReflectionCorrelationAnalysis(
            correlations=correlations,
            unmatched_events=unmatched_events,
            available_surfaces=available_surfaces,
            evaluated_event_count=evaluated_event_count,
            matched_event_count=len(correlations),
            confidence=(
                fmean(item.confidence for item in correlations)
                if correlations
                else 0.0
            ),
            available_surface_ids=tuple(sorted({
                path.surface_id for path in geometry_paths
            })),
            geometry_candidate_count=len(geometry_paths),
        )

    @classmethod
    def _best_geometry_correlation(
        cls,
        channel,
        event,
        paths,
        maximum_timing_error_ms,
        minimum_correlation_score,
    ):
        matches = []
        for path in paths:
            if not cls._speaker_matches_channel(path.speaker_id, channel):
                continue
            if (
                path.confidence is None
                or path.uncertainty_ms is None
                or not path.provenance_codes
            ):
                continue
            timing_error_ms = abs(event.delay_ms - path.theoretical_delay_ms)
            if timing_error_ms > maximum_timing_error_ms:
                continue
            timing_score = 100.0 * (
                1.0 - timing_error_ms / maximum_timing_error_ms
            )
            geometry_score = path.confidence if path.confidence is not None else 0.0
            match_score = 0.7 * timing_score + 0.3 * geometry_score
            if match_score < minimum_correlation_score:
                continue
            confidence = (
                0.4 * event.confidence
                + 0.3 * geometry_score
                + 0.3 * match_score
            )
            matches.append(ETCReflectionCorrelation(
                code=(
                    "etc_geometry_reflection."
                    f"{channel.value.lower()}.{event.sample_index}."
                    f"{path.surface_id.lower()}"
                ),
                channel=channel,
                event=event,
                surface=path.surface,
                theoretical_delay_ms=path.theoretical_delay_ms,
                measured_delay_ms=event.delay_ms,
                timing_error_ms=timing_error_ms,
                acoustic_path_difference_m=event.acoustic_path_difference_m,
                match_score=match_score,
                confidence=confidence,
                source_analyses=(
                    "ETCAnalysis", "GeometryEarlyReflectionAnalysis"
                ),
                surface_id=path.surface_id,
                impact_point=path.impact_point,
                geometric_uncertainty_ms=path.uncertainty_ms,
                geometry_confidence=path.confidence,
                geometry_path_id=path.path_id,
                provenance_codes=path.provenance_codes,
            ))
        return max(matches, key=lambda item: item.match_score, default=None)

    @staticmethod
    def _speaker_matches_channel(speaker_id, channel):
        normalized = speaker_id.upper().replace("-", "_")
        if channel.value == "LEFT":
            return normalized in {"LEFT", "L", "SPEAKER_LEFT", "LEFT_SPEAKER"}
        if channel.value == "RIGHT":
            return normalized in {"RIGHT", "R", "SPEAKER_RIGHT", "RIGHT_SPEAKER"}
        return normalized in {"STEREO", "L_R", "LR", "SPEAKER_STEREO"}

    @classmethod
    def _best_correlation(
        cls,
        channel,
        event,
        candidates,
        sbir_analysis,
        maximum_timing_error_ms,
        minimum_correlation_score,
    ):
        matches = []
        for candidate in candidates:
            timing_error_ms = abs(event.delay_ms - candidate.delay_ms)
            if timing_error_ms > maximum_timing_error_ms:
                continue
            timing_score = 100.0 * (
                1.0 - timing_error_ms / maximum_timing_error_ms
            )
            match_score = 0.7 * timing_score + 0.3 * candidate.match_score
            if match_score < minimum_correlation_score:
                continue
            confidence = (
                0.4 * event.confidence
                + 0.3 * (sbir_analysis.confidence if sbir_analysis else 0.0)
                + 0.3 * match_score
            )
            matches.append(
                ETCReflectionCorrelation(
                    code=(
                        "etc_reflection."
                        f"{channel.value.lower()}."
                        f"{event.sample_index}."
                        f"{candidate.surface.name.lower()}"
                    ),
                    channel=channel,
                    event=event,
                    surface=candidate.surface,
                    theoretical_delay_ms=candidate.delay_ms,
                    measured_delay_ms=event.delay_ms,
                    timing_error_ms=timing_error_ms,
                    acoustic_path_difference_m=(
                        event.acoustic_path_difference_m
                    ),
                    match_score=match_score,
                    confidence=confidence,
                    source_analyses=("ETCAnalysis", "SBIRAnalysis"),
                )
            )
        return max(matches, key=lambda item: item.match_score, default=None)

    @staticmethod
    def _validate(
        maximum_timing_error_ms,
        minimum_sbir_match_score,
        minimum_correlation_score,
    ):
        if maximum_timing_error_ms <= 0:
            raise ValueError("ETC-SBIR timing tolerance must be positive.")
        for value in (minimum_sbir_match_score, minimum_correlation_score):
            if not 0 <= value <= 100:
                raise ValueError("ETC-SBIR score thresholds must be within 0..100.")
