from statistics import fmean

from acousticbrain.models import ETCAnalysis, ETCChannelAnalysis, ImpulseChannel


class ETCAggregator:
    """Apparie les événements uniquement par proximité temporelle."""

    DEFAULT_DELAY_TOLERANCE_MS = 0.5

    def aggregate(
        self,
        channel_analyses: dict[ImpulseChannel, ETCChannelAnalysis],
        *,
        delay_tolerance_ms: float = DEFAULT_DELAY_TOLERANCE_MS,
    ) -> ETCAnalysis:
        self._validate(channel_analyses, delay_tolerance_ms)
        available_channels = [
            channel
            for channel in ImpulseChannel
            if channel in channel_analyses
        ]
        left = channel_analyses.get(ImpulseChannel.LEFT)
        right = channel_analyses.get(ImpulseChannel.RIGHT)
        common, left_only, right_only, timing_confidence = self._match(
            left.events if left else [],
            right.events if right else [],
            delay_tolerance_ms,
        )
        channel_confidences = [
            analysis.confidence for analysis in channel_analyses.values()
        ]
        channel_confidence = (
            fmean(channel_confidences) if channel_confidences else 0.0
        )
        confidence = (
            0.7 * channel_confidence + 0.3 * timing_confidence
            if common
            else channel_confidence
        )

        return ETCAnalysis(
            channels=dict(channel_analyses),
            available_channels=available_channels,
            common_events=common,
            left_only_events=left_only,
            right_only_events=right_only,
            common_event_count=len(common),
            left_only_event_count=len(left_only),
            right_only_event_count=len(right_only),
            confidence=confidence,
        )

    @staticmethod
    def _match(left_events, right_events, tolerance_ms):
        candidates = sorted(
            (
                abs(left.delay_ms - right.delay_ms),
                left_index,
                right_index,
            )
            for left_index, left in enumerate(left_events)
            for right_index, right in enumerate(right_events)
            if abs(left.delay_ms - right.delay_ms) <= tolerance_ms
        )
        matched_left = set()
        matched_right = set()
        matches = []

        for difference_ms, left_index, right_index in candidates:
            if left_index in matched_left or right_index in matched_right:
                continue
            matched_left.add(left_index)
            matched_right.add(right_index)
            matches.append((left_index, right_index, difference_ms))

        matches.sort(key=lambda match: match[0])
        common = [
            (left_events[left_index], right_events[right_index])
            for left_index, right_index, _ in matches
        ]
        left_only = [
            event
            for index, event in enumerate(left_events)
            if index not in matched_left
        ]
        right_only = [
            event
            for index, event in enumerate(right_events)
            if index not in matched_right
        ]
        timing_confidence = (
            fmean(
                100.0 * (1.0 - difference_ms / tolerance_ms)
                for _, _, difference_ms in matches
            )
            if matches
            else 0.0
        )
        return common, left_only, right_only, timing_confidence

    @staticmethod
    def _validate(channel_analyses, delay_tolerance_ms):
        if delay_tolerance_ms <= 0:
            raise ValueError("ETC delay tolerance must be positive.")
        for channel, analysis in channel_analyses.items():
            if channel is not analysis.channel:
                raise ValueError(
                    "ETC channel analysis does not match its channel key."
                )

