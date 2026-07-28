from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from math import isfinite, log2
from statistics import fmean, median

from acousticbrain.models import (
    FrequencyFeatureChannelClassification,
    FrequencyFeatureStereoClassification,
    FrequencyResponseBand,
    FrequencyResponseChannelAnalysis,
    FrequencyResponseFeature,
    FrequencyResponseFeatureAnalysis,
    FrequencyResponseFeatureComparison,
    FrequencyResponseFeatureType,
    FrequencyResponseStereoRelation,
    ImpulseChannel,
    Measurement,
)


@dataclass(frozen=True)
class _Candidate:
    feature_type: FrequencyResponseFeatureType
    center_index: int
    lower_index: int
    upper_index: int
    magnitude_db: float


class FrequencyResponseFeatureAnalyzer:
    """Detects descriptive frequency-response features on a log-frequency axis.

    The local reference is a rolling median over a physical octave interval.
    This avoids applying a linear-grid filter to REW's logarithmic sampling.
    Detection confidence describes numerical feature resolution only; it does
    not express confidence in any acoustic cause.
    """

    SOURCE_ANALYSIS_ID = "FrequencyResponseFeatureAnalysis"
    MINIMUM_FREQUENCY_HZ = 20.0
    MAXIMUM_FREQUENCY_HZ = 22000.0
    MINIMUM_SAMPLE_COUNT = 48
    # REW exports are logarithmic. A half-window of 1/4 octave estimates a
    # local tendency without introducing interpolation or assuming a Hz step.
    LOCAL_REFERENCE_HALF_WIDTH_OCTAVES = 0.25
    # Three dB is the explicit minimum departure from the local tendency.
    MINIMUM_MAGNITUDE_DB = 3.0
    # At 96 points/octave this requires at least two resolved samples.
    MINIMUM_BANDWIDTH_OCTAVES = 1.0 / 48.0
    # The input declares 1/12-octave smoothing, so closer extrema are treated
    # as one resolved feature rather than independent micro-features.
    MERGE_SEPARATION_OCTAVES = 1.0 / 12.0
    # Half of the declared smoothing width protects unresolved domain edges.
    DOMAIN_EDGE_GUARD_OCTAVES = 1.0 / 24.0
    # Matching uses a log-frequency tolerance equal to the declared smoothing
    # resolution, plus actual band overlap and a bounded width ratio.
    MATCH_TOLERANCE_OCTAVES = 1.0 / 12.0
    MINIMUM_OVERLAP_SCORE = 0.05
    MAXIMUM_WIDTH_RATIO = 4.0
    AMBIGUITY_SCORE_MARGIN = 0.10
    # A 1.5 dB magnitude difference is reported descriptively; it is not an
    # audibility threshold and carries no causal meaning.
    STEREO_MAGNITUDE_DIFFERENCE_DB = 1.5
    ANALYSIS_LIMITATIONS = (
        "Frequency-response features are descriptive and do not establish cause.",
        "Input responses may already include smoothing applied by the "
        "measurement tool.",
        "Phase is validated for structural integrity but is not used for "
        "feature detection.",
        "Domain-edge guards exclude features whose bounds cannot be resolved reliably.",
    )

    def analyze(self, left, right, stereo):
        measurements = (
            (ImpulseChannel.LEFT, left),
            (ImpulseChannel.RIGHT, right),
            (ImpulseChannel.STEREO, stereo),
        )
        channels = tuple(
            self._analyze_channel(channel, measurement)
            for channel, measurement in measurements
        )
        comparisons = self._compare_channels(channels[0], channels[1])
        relations = self._relate_stereo(comparisons, channels)
        confidence_values = [item.detection_confidence for item in channels]
        confidence_values.extend(
            item.match_confidence for item in comparisons
            if item.classification is FrequencyFeatureChannelClassification.COMMON
        )
        return FrequencyResponseFeatureAnalysis(
            channels=channels,
            left_right_comparisons=comparisons,
            stereo_relations=relations,
            confidence=fmean(confidence_values) if confidence_values else 0.0,
            limitations=self.ANALYSIS_LIMITATIONS,
        )

    def validate_measurement(self, measurement):
        if not isinstance(measurement, Measurement):
            raise TypeError("Frequency-response analysis requires Measurement.")
        if (
            len(measurement.frequency) != len(measurement.spl)
            or len(measurement.frequency) != len(measurement.phase)
        ):
            raise ValueError("Frequency, SPL, and phase lengths must match.")
        if len(measurement.frequency) < self.MINIMUM_SAMPLE_COUNT:
            raise ValueError("Frequency-response analysis has insufficient samples.")
        values = (*measurement.frequency, *measurement.spl, *measurement.phase)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            for value in values
        ):
            raise ValueError("Frequency-response data must be finite numbers.")
        if any(value <= 0.0 for value in measurement.frequency):
            raise ValueError("Frequency values must be positive.")
        if any(
            right <= left
            for left, right in zip(
                measurement.frequency,
                measurement.frequency[1:],
            )
        ):
            raise ValueError("Frequency values must be strictly increasing.")
        if (
            measurement.frequency[-1] < self.MINIMUM_FREQUENCY_HZ
            or measurement.frequency[0] > self.MAXIMUM_FREQUENCY_HZ
        ):
            raise ValueError("Frequency-response data do not cover the analysis band.")

    def _analyze_channel(self, channel, measurement):
        self.validate_measurement(measurement)
        source_indices = tuple(
            index
            for index, frequency in enumerate(measurement.frequency)
            if self.MINIMUM_FREQUENCY_HZ
            <= frequency
            <= self.MAXIMUM_FREQUENCY_HZ
        )
        if len(source_indices) < self.MINIMUM_SAMPLE_COUNT:
            raise ValueError("Analysis-band frequency data are insufficient.")
        frequencies = tuple(measurement.frequency[index] for index in source_indices)
        levels = tuple(measurement.spl[index] for index in source_indices)
        log_frequencies = tuple(log2(value) for value in frequencies)
        reference = self._local_reference(log_frequencies, levels)
        residual = tuple(
            level - local for level, local in zip(levels, reference)
        )
        candidates = self._candidates(log_frequencies, residual)
        candidates = self._merge_candidates(candidates, log_frequencies)
        features = tuple(
            self._feature(
                candidate,
                channel=channel,
                frequencies=frequencies,
                levels=levels,
                residual=residual,
                source_indices=source_indices,
            )
            for candidate in candidates
        )
        features = tuple(
            sorted(
                features,
                key=lambda item: (
                    item.center_frequency_hz,
                    item.feature_type.value,
                    item.feature_id,
                ),
            )
        )
        peaks = tuple(
            item
            for item in features
            if item.feature_type is FrequencyResponseFeatureType.PEAK
        )
        notches = tuple(
            item
            for item in features
            if item.feature_type is FrequencyResponseFeatureType.NOTCH
        )
        strongest = max(
            features,
            key=lambda item: (
                self._magnitude(item),
                -item.center_frequency_hz,
            ),
            default=None,
        )
        deepest = max(
            notches,
            key=lambda item: (
                item.depth_db,
                -item.center_frequency_hz,
            ),
            default=None,
        )
        confidence = (
            fmean(item.detection_confidence for item in features)
            if features
            else self._grid_confidence(log_frequencies)
        )
        return FrequencyResponseChannelAnalysis(
            channel=channel,
            features=features,
            sample_count=len(frequencies),
            minimum_frequency_hz=frequencies[0],
            maximum_frequency_hz=frequencies[-1],
            peak_count=len(peaks),
            notch_count=len(notches),
            most_prominent_feature_id=(
                strongest.feature_id if strongest is not None else None
            ),
            deepest_notch_feature_id=(
                deepest.feature_id if deepest is not None else None
            ),
            detection_confidence=confidence,
            limitations=self.ANALYSIS_LIMITATIONS,
        )

    def _local_reference(self, log_frequencies, levels):
        reference = []
        for center in log_frequencies:
            lower = bisect_left(
                log_frequencies,
                center - self.LOCAL_REFERENCE_HALF_WIDTH_OCTAVES,
            )
            upper = bisect_right(
                log_frequencies,
                center + self.LOCAL_REFERENCE_HALF_WIDTH_OCTAVES,
            )
            reference.append(median(levels[lower:upper]))
        return tuple(reference)

    def _candidates(self, log_frequencies, residual):
        candidates = []
        minimum_log = log_frequencies[0]
        maximum_log = log_frequencies[-1]
        for index in range(1, len(residual) - 1):
            distance_to_edge = min(
                log_frequencies[index] - minimum_log,
                maximum_log - log_frequencies[index],
            )
            if distance_to_edge < self.DOMAIN_EDGE_GUARD_OCTAVES:
                continue
            value = residual[index]
            feature_type = None
            magnitude = 0.0
            if (
                value >= self.MINIMUM_MAGNITUDE_DB
                and value > residual[index - 1]
                and value >= residual[index + 1]
            ):
                feature_type = FrequencyResponseFeatureType.PEAK
                magnitude = value
            elif (
                value <= -self.MINIMUM_MAGNITUDE_DB
                and value < residual[index - 1]
                and value <= residual[index + 1]
            ):
                feature_type = FrequencyResponseFeatureType.NOTCH
                magnitude = -value
            if feature_type is None:
                continue
            lower, upper = self._half_magnitude_bounds(
                residual,
                index,
                feature_type,
                magnitude / 2.0,
            )
            width = log_frequencies[upper] - log_frequencies[lower]
            if width < self.MINIMUM_BANDWIDTH_OCTAVES:
                continue
            candidates.append(
                _Candidate(
                    feature_type=feature_type,
                    center_index=index,
                    lower_index=lower,
                    upper_index=upper,
                    magnitude_db=magnitude,
                )
            )
        return tuple(candidates)

    @staticmethod
    def _half_magnitude_bounds(
        residual,
        center_index,
        feature_type,
        threshold,
    ):
        def within(value):
            return (
                value >= threshold
                if feature_type is FrequencyResponseFeatureType.PEAK
                else value <= -threshold
            )

        lower = center_index
        while lower > 0 and within(residual[lower - 1]):
            lower -= 1
        upper = center_index
        while upper < len(residual) - 1 and within(residual[upper + 1]):
            upper += 1
        return lower, upper

    def _merge_candidates(self, candidates, log_frequencies):
        merged = []
        for candidate in sorted(
            candidates,
            key=lambda item: (
                item.feature_type.value,
                log_frequencies[item.center_index],
                item.center_index,
            ),
        ):
            if (
                merged
                and merged[-1].feature_type is candidate.feature_type
                and log_frequencies[candidate.center_index]
                - log_frequencies[merged[-1].center_index]
                <= self.MERGE_SEPARATION_OCTAVES
            ):
                previous = merged[-1]
                strongest = max(
                    (previous, candidate),
                    key=lambda item: (item.magnitude_db, -item.center_index),
                )
                merged[-1] = _Candidate(
                    feature_type=strongest.feature_type,
                    center_index=strongest.center_index,
                    lower_index=min(previous.lower_index, candidate.lower_index),
                    upper_index=max(previous.upper_index, candidate.upper_index),
                    magnitude_db=strongest.magnitude_db,
                )
            else:
                merged.append(candidate)
        return tuple(merged)

    def _feature(
        self,
        candidate,
        *,
        channel,
        frequencies,
        levels,
        residual,
        source_indices,
    ):
        center = frequencies[candidate.center_index]
        lower = frequencies[candidate.lower_index]
        upper = frequencies[candidate.upper_index]
        bandwidth = upper - lower
        bandwidth_octaves = log2(upper / lower) if upper > lower else None
        estimated_q = center / bandwidth if bandwidth > 0.0 else None
        magnitude = candidate.magnitude_db
        sample_count = candidate.upper_index - candidate.lower_index + 1
        confidence = self._feature_confidence(
            magnitude=magnitude,
            sample_count=sample_count,
            bounds_resolved=(
                candidate.lower_index > 0
                and candidate.upper_index < len(frequencies) - 1
            ),
        )
        feature_type = candidate.feature_type
        original_center_index = source_indices[candidate.center_index]
        return FrequencyResponseFeature(
            feature_id=(
                f"FREQUENCY_FEATURE_{channel.value}_{feature_type.value}_"
                f"{original_center_index:04d}"
            ),
            feature_type=feature_type,
            band=self._band(center),
            channel=channel,
            center_frequency_hz=center,
            level_db=levels[candidate.center_index],
            relative_level_db=residual[candidate.center_index],
            prominence_db=(
                magnitude
                if feature_type is FrequencyResponseFeatureType.PEAK
                else None
            ),
            depth_db=(
                magnitude
                if feature_type is FrequencyResponseFeatureType.NOTCH
                else None
            ),
            lower_frequency_hz=lower,
            upper_frequency_hz=upper,
            bandwidth_hz=bandwidth,
            bandwidth_octaves=bandwidth_octaves,
            estimated_q=estimated_q,
            detection_confidence=confidence,
            supporting_sample_range=(
                source_indices[candidate.lower_index],
                source_indices[candidate.upper_index],
            ),
            limitations=self.ANALYSIS_LIMITATIONS,
        )

    def _compare_channels(self, left, right):
        left_features = left.features
        right_features = right.features
        candidates = []
        for left_index, left_feature in enumerate(left_features):
            for right_index, right_feature in enumerate(right_features):
                score = self._compatibility_score(left_feature, right_feature)
                if score is not None:
                    candidates.append((score, left_index, right_index))
        ambiguous_left = self._ambiguous_indices(candidates, position=1)
        ambiguous_right = self._ambiguous_indices(candidates, position=2)
        matched_left = set()
        matched_right = set()
        common = []
        for score, left_index, right_index in sorted(
            candidates,
            key=lambda item: (
                item[0],
                left_features[item[1]].feature_id,
                right_features[item[2]].feature_id,
            ),
        ):
            if (
                left_index in ambiguous_left
                or right_index in ambiguous_right
                or left_index in matched_left
                or right_index in matched_right
            ):
                continue
            left_feature = left_features[left_index]
            right_feature = right_features[right_index]
            matched_left.add(left_index)
            matched_right.add(right_index)
            common.append(
                self._common_comparison(left_feature, right_feature, score)
            )
        singles = []
        for index, feature in enumerate(left_features):
            if index not in matched_left:
                singles.append(
                    self._single_comparison(
                        feature,
                        FrequencyFeatureChannelClassification.LEFT_ONLY,
                        ambiguous=index in ambiguous_left,
                    )
                )
        for index, feature in enumerate(right_features):
            if index not in matched_right:
                singles.append(
                    self._single_comparison(
                        feature,
                        FrequencyFeatureChannelClassification.RIGHT_ONLY,
                        ambiguous=index in ambiguous_right,
                    )
                )
        return tuple(
            sorted(
                (*common, *singles),
                key=lambda item: (
                    self._comparison_frequency(item, left_features, right_features),
                    item.classification.value,
                    item.comparison_id,
                ),
            )
        )

    def _common_comparison(self, left, right, score):
        frequency_delta = abs(left.center_frequency_hz - right.center_frequency_hz)
        average_frequency = (
            left.center_frequency_hz + right.center_frequency_hz
        ) / 2.0
        overlap = self._overlap_score(left, right)
        magnitude_delta = abs(self._magnitude(left) - self._magnitude(right))
        return FrequencyResponseFeatureComparison(
            comparison_id=(
                f"FREQUENCY_COMPARISON_COMMON_{left.feature_id}_"
                f"{right.feature_id}"
            ),
            classification=FrequencyFeatureChannelClassification.COMMON,
            feature_type=left.feature_type,
            left_feature_id=left.feature_id,
            right_feature_id=right.feature_id,
            frequency_delta_hz=frequency_delta,
            frequency_delta_percent=100.0 * frequency_delta / average_frequency,
            level_or_depth_delta_db=magnitude_delta,
            overlap_score=overlap,
            match_confidence=max(0.0, 100.0 * (1.0 - score / 3.0)),
        )

    @staticmethod
    def _single_comparison(feature, classification, *, ambiguous):
        left = (
            feature.feature_id
            if classification is FrequencyFeatureChannelClassification.LEFT_ONLY
            else None
        )
        right = (
            feature.feature_id
            if classification is FrequencyFeatureChannelClassification.RIGHT_ONLY
            else None
        )
        return FrequencyResponseFeatureComparison(
            comparison_id=(
                f"FREQUENCY_COMPARISON_{classification.value}_{feature.feature_id}"
            ),
            classification=classification,
            feature_type=feature.feature_type,
            left_feature_id=left,
            right_feature_id=right,
            frequency_delta_hz=None,
            frequency_delta_percent=None,
            level_or_depth_delta_db=None,
            overlap_score=None,
            match_confidence=0.0 if ambiguous else feature.detection_confidence,
            limitations=(
                ("Ambiguous LEFT/RIGHT candidates were intentionally not matched.",)
                if ambiguous
                else ()
            ),
        )

    def _relate_stereo(self, comparisons, channels):
        features_by_id = {
            feature.feature_id: feature
            for channel in channels
            for feature in channel.features
        }
        stereo_features = channels[2].features
        relations = []
        for comparison in comparisons:
            source_features = tuple(
                features_by_id[identifier]
                for identifier in (
                    comparison.left_feature_id,
                    comparison.right_feature_id,
                )
                if identifier is not None
            )
            candidates = []
            for stereo_feature in stereo_features:
                scores = tuple(
                    score
                    for source in source_features
                    if (
                        score := self._compatibility_score(source, stereo_feature)
                    )
                    is not None
                )
                if scores:
                    candidates.append((fmean(scores), stereo_feature))
            candidates.sort(key=lambda item: (item[0], item[1].feature_id))
            if not candidates:
                relations.append(
                    self._unresolved_stereo_relation(comparison)
                )
                continue
            if (
                len(candidates) > 1
                and candidates[1][0] - candidates[0][0]
                <= self.AMBIGUITY_SCORE_MARGIN
            ):
                relations.append(
                    FrequencyResponseStereoRelation(
                        relation_id=f"STEREO_RELATION_{comparison.comparison_id}",
                        comparison_id=comparison.comparison_id,
                        stereo_feature_id=None,
                        classification=(
                            FrequencyFeatureStereoClassification.AMBIGUOUS
                        ),
                        frequency_delta_hz=None,
                        magnitude_delta_db=None,
                        bandwidth_delta_octaves=None,
                        match_confidence=0.0,
                        limitations=(
                            "Multiple compatible STEREO features remain ambiguous.",
                        ),
                    )
                )
                continue
            score, stereo_feature = candidates[0]
            relations.append(
                self._resolved_stereo_relation(
                    comparison,
                    source_features,
                    stereo_feature,
                    score,
                )
            )
        return tuple(relations)

    def _resolved_stereo_relation(
        self,
        comparison,
        sources,
        stereo,
        score,
    ):
        source_frequency = fmean(item.center_frequency_hz for item in sources)
        source_magnitude = fmean(self._magnitude(item) for item in sources)
        magnitude_delta = self._magnitude(stereo) - source_magnitude
        if magnitude_delta >= self.STEREO_MAGNITUDE_DIFFERENCE_DB:
            classification = (
                FrequencyFeatureStereoClassification.AMPLIFIED_IN_STEREO
            )
        elif magnitude_delta <= -self.STEREO_MAGNITUDE_DIFFERENCE_DB:
            classification = (
                FrequencyFeatureStereoClassification.ATTENUATED_IN_STEREO
            )
        else:
            classification = (
                FrequencyFeatureStereoClassification.PRESENT_IN_STEREO
            )
        source_widths = tuple(
            item.bandwidth_octaves
            for item in sources
            if item.bandwidth_octaves is not None
        )
        bandwidth_delta = (
            abs(stereo.bandwidth_octaves - fmean(source_widths))
            if stereo.bandwidth_octaves is not None and source_widths
            else None
        )
        return FrequencyResponseStereoRelation(
            relation_id=f"STEREO_RELATION_{comparison.comparison_id}",
            comparison_id=comparison.comparison_id,
            stereo_feature_id=stereo.feature_id,
            classification=classification,
            frequency_delta_hz=abs(stereo.center_frequency_hz - source_frequency),
            magnitude_delta_db=magnitude_delta,
            bandwidth_delta_octaves=bandwidth_delta,
            match_confidence=max(0.0, 100.0 * (1.0 - score / 3.0)),
            limitations=(
                "Stereo relation is descriptive and does not identify a cause.",
            ),
        )

    @staticmethod
    def _unresolved_stereo_relation(comparison):
        return FrequencyResponseStereoRelation(
            relation_id=f"STEREO_RELATION_{comparison.comparison_id}",
            comparison_id=comparison.comparison_id,
            stereo_feature_id=None,
            classification=(
                FrequencyFeatureStereoClassification.NOT_RESOLVED_IN_STEREO
            ),
            frequency_delta_hz=None,
            magnitude_delta_db=None,
            bandwidth_delta_octaves=None,
            match_confidence=0.0,
            limitations=("No compatible STEREO feature was resolved.",),
        )

    def _compatibility_score(self, left, right):
        if left.feature_type is not right.feature_type:
            return None
        delta_octaves = abs(
            log2(left.center_frequency_hz / right.center_frequency_hz)
        )
        if delta_octaves > self.MATCH_TOLERANCE_OCTAVES:
            return None
        overlap = self._overlap_score(left, right)
        if overlap < self.MINIMUM_OVERLAP_SCORE:
            return None
        widths = (left.bandwidth_octaves, right.bandwidth_octaves)
        if any(value is None or value <= 0.0 for value in widths):
            return None
        width_ratio = max(widths) / min(widths)
        if width_ratio > self.MAXIMUM_WIDTH_RATIO:
            return None
        return (
            delta_octaves / self.MATCH_TOLERANCE_OCTAVES
            + (1.0 - overlap)
            + abs(log2(width_ratio)) / log2(self.MAXIMUM_WIDTH_RATIO)
        )

    @classmethod
    def _overlap_score(cls, left, right):
        overlap = max(
            0.0,
            min(left.upper_frequency_hz, right.upper_frequency_hz)
            - max(left.lower_frequency_hz, right.lower_frequency_hz),
        )
        minimum_width = min(left.bandwidth_hz, right.bandwidth_hz)
        return overlap / minimum_width if minimum_width > 0.0 else 0.0

    def _ambiguous_indices(self, candidates, *, position):
        by_index = {}
        for candidate in candidates:
            by_index.setdefault(candidate[position], []).append(candidate[0])
        return {
            index
            for index, scores in by_index.items()
            if len(scores) > 1
            and sorted(scores)[1] - sorted(scores)[0]
            <= self.AMBIGUITY_SCORE_MARGIN
        }

    @staticmethod
    def _comparison_frequency(comparison, left_features, right_features):
        by_id = {
            item.feature_id: item
            for item in (*left_features, *right_features)
        }
        values = tuple(
            by_id[identifier].center_frequency_hz
            for identifier in (
                comparison.left_feature_id,
                comparison.right_feature_id,
            )
            if identifier is not None
        )
        return fmean(values)

    @classmethod
    def _feature_confidence(cls, *, magnitude, sample_count, bounds_resolved):
        """Score detection quality, never causal confidence.

        Strength contributes 50%, resolved sample support 30%, and complete
        half-magnitude bounds 20%. Each component is explicitly bounded.
        """
        strength = min(1.0, magnitude / (2.0 * cls.MINIMUM_MAGNITUDE_DB))
        support = min(1.0, sample_count / 8.0)
        bounds = 1.0 if bounds_resolved else 0.5
        return 100.0 * (0.5 * strength + 0.3 * support + 0.2 * bounds)

    @staticmethod
    def _grid_confidence(log_frequencies):
        steps = tuple(
            right - left
            for left, right in zip(log_frequencies, log_frequencies[1:])
        )
        average = fmean(steps)
        maximum_relative_deviation = max(
            abs(value - average) / average for value in steps
        )
        return max(0.0, 100.0 * (1.0 - maximum_relative_deviation))

    @staticmethod
    def _band(frequency):
        if frequency < 200.0:
            return FrequencyResponseBand.LOW
        if frequency < 2000.0:
            return FrequencyResponseBand.MID
        return FrequencyResponseBand.HIGH

    @staticmethod
    def _magnitude(feature):
        return (
            feature.prominence_db
            if feature.feature_type is FrequencyResponseFeatureType.PEAK
            else feature.depth_db
        )
