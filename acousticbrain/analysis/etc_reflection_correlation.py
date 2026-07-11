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
        )

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
