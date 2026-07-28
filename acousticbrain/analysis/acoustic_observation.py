from acousticbrain.models import (
    AcousticObservation,
    AcousticObservationCategory,
    AcousticObservationSynthesis,
    FrequencyFeatureChannelClassification,
    FrequencyFeatureStereoClassification,
    FrequencyResponseFeatureType,
)


class DeterministicAcousticObservationSynthesizer:
    """Copies established analysis facts into ordered descriptive observations."""

    def synthesize(self, context):
        observations = []
        for builder in (
            self._measurement_quality,
            self._frequency_response_features,
            self._left_right_frequency_features,
            self._stereo_frequency_features,
            self._low_frequency_decay,
            self._rt60,
            self._early_reflections,
            self._clarity,
            self._stereo,
        ):
            observation = builder(context)
            if observation is not None:
                observations.append(observation)
        return AcousticObservationSynthesis(tuple(observations))

    @staticmethod
    def _number(value):
        return f"{value:.6g}"

    def _measurement_quality(self, context):
        analysis = getattr(context, "measurement_quality_analysis", None)
        if analysis is None or not (
            analysis.channel_qualities or analysis.measurement_set_quality is not None
        ):
            return None
        issues = []
        for channel in analysis.channel_qualities:
            issues.extend(
                f"measurement_quality.{channel.channel.value}.{issue.code.value}"
                for issue in channel.issues
            )
        if analysis.measurement_set_quality is not None:
            issues.extend(
                f"measurement_quality.set.{issue.code.value}"
                for issue in analysis.measurement_set_quality.issues
            )
        channel_codes = tuple(
            item.channel.value for item in analysis.channel_qualities
        )
        evidence = (
            f"measurement_quality.channel_count={len(channel_codes)}",
            f"measurement_quality.channels={','.join(channel_codes)}",
        )
        return AcousticObservation(
            observation_id="MEASUREMENT_QUALITY_FACTS",
            category=AcousticObservationCategory.MEASUREMENT_QUALITY,
            title="Measurement quality facts",
            description=(
                f"Quality analysis contains {len(channel_codes)} channel records "
                f"and {len(issues)} reported technical issues."
            ),
            confidence=analysis.confidence,
            supporting_evidence=evidence,
            contradicting_evidence=tuple(issues),
            limitations=(),
            source_analysis_ids=("MeasurementQualityAnalysis",),
        )

    def _frequency_response_features(self, context):
        analysis = getattr(context, "frequency_response_feature_analysis", None)
        if analysis is None:
            return None
        evidence = []
        all_features = []
        for channel in analysis.channels:
            evidence.extend(
                (
                    f"frequency_features.{channel.channel.value.lower()}."
                    f"peak_count={channel.peak_count}",
                    f"frequency_features.{channel.channel.value.lower()}."
                    f"notch_count={channel.notch_count}",
                    f"frequency_features.{channel.channel.value.lower()}."
                    f"sample_count={channel.sample_count}",
                )
            )
            all_features.extend(channel.features)
        deepest = max(
            (
                item
                for item in all_features
                if item.feature_type is FrequencyResponseFeatureType.NOTCH
            ),
            key=lambda item: (
                item.depth_db,
                -item.center_frequency_hz,
                item.feature_id,
            ),
            default=None,
        )
        if deepest is not None:
            evidence.extend(
                (
                    "frequency_features.deepest_notch.center_hz="
                    f"{self._number(deepest.center_frequency_hz)}",
                    "frequency_features.deepest_notch.depth_db="
                    f"{self._number(deepest.depth_db)}",
                    "frequency_features.deepest_notch.channel="
                    f"{deepest.channel.value}",
                )
            )
        peak_count = sum(item.peak_count for item in analysis.channels)
        notch_count = sum(item.notch_count for item in analysis.channels)
        return AcousticObservation(
            observation_id="FREQUENCY_RESPONSE_FEATURE_FACTS",
            category=AcousticObservationCategory.FREQUENCY_RESPONSE,
            title="Frequency-response feature facts",
            description=(
                f"Frequency-response analysis detected {peak_count} peaks and "
                f"{notch_count} notches across LEFT, RIGHT and STEREO."
            ),
            confidence=analysis.confidence,
            supporting_evidence=tuple(evidence),
            contradicting_evidence=(),
            limitations=analysis.limitations,
            source_analysis_ids=("FrequencyResponseFeatureAnalysis",),
        )

    def _left_right_frequency_features(self, context):
        analysis = getattr(context, "frequency_response_feature_analysis", None)
        if analysis is None:
            return None
        counts = {
            classification: sum(
                item.classification is classification
                for item in analysis.left_right_comparisons
            )
            for classification in FrequencyFeatureChannelClassification
        }
        common = tuple(
            item
            for item in analysis.left_right_comparisons
            if item.classification
            is FrequencyFeatureChannelClassification.COMMON
        )
        confidence = (
            min(item.match_confidence for item in common)
            if common
            else analysis.confidence
        )
        return AcousticObservation(
            observation_id="LEFT_RIGHT_FREQUENCY_FEATURE_COMPARISON_FACTS",
            category=AcousticObservationCategory.FREQUENCY_RESPONSE,
            title="LEFT/RIGHT frequency-feature comparison facts",
            description=(
                f"Channel comparison contains "
                f"{counts[FrequencyFeatureChannelClassification.COMMON]} common, "
                f"{counts[FrequencyFeatureChannelClassification.LEFT_ONLY]} "
                "left-only and "
                f"{counts[FrequencyFeatureChannelClassification.RIGHT_ONLY]} "
                "right-only features."
            ),
            confidence=confidence,
            supporting_evidence=(
                "frequency_features.common_count="
                f"{counts[FrequencyFeatureChannelClassification.COMMON]}",
                "frequency_features.left_only_count="
                f"{counts[FrequencyFeatureChannelClassification.LEFT_ONLY]}",
                "frequency_features.right_only_count="
                f"{counts[FrequencyFeatureChannelClassification.RIGHT_ONLY]}",
            ),
            contradicting_evidence=(),
            limitations=analysis.limitations,
            source_analysis_ids=("FrequencyResponseFeatureAnalysis",),
        )

    def _stereo_frequency_features(self, context):
        analysis = getattr(context, "frequency_response_feature_analysis", None)
        if analysis is None:
            return None
        counts = {
            classification: sum(
                item.classification is classification
                for item in analysis.stereo_relations
            )
            for classification in FrequencyFeatureStereoClassification
        }
        resolved = tuple(
            item
            for item in analysis.stereo_relations
            if item.stereo_feature_id is not None
        )
        confidence = (
            min(item.match_confidence for item in resolved)
            if resolved
            else analysis.confidence
        )
        evidence = tuple(
            "frequency_features.stereo."
            f"{classification.value.lower()}_count={counts[classification]}"
            for classification in FrequencyFeatureStereoClassification
        )
        return AcousticObservation(
            observation_id="STEREO_FREQUENCY_FEATURE_RELATION_FACTS",
            category=AcousticObservationCategory.FREQUENCY_RESPONSE,
            title="STEREO frequency-feature relation facts",
            description=(
                f"Stereo comparison resolved {len(resolved)} of "
                f"{len(analysis.stereo_relations)} descriptive feature relations."
            ),
            confidence=confidence,
            supporting_evidence=evidence,
            contradicting_evidence=(),
            limitations=analysis.limitations,
            source_analysis_ids=("FrequencyResponseFeatureAnalysis",),
        )

    def _low_frequency_decay(self, context):
        analysis = getattr(context, "bass_decay_analysis", None)
        if analysis is None:
            return None
        usable = tuple(
            band
            for band in analysis.aggregate_bands
            if band.estimated_decay_time_seconds is not None
        )
        if not usable:
            return None
        evidence = tuple(
            "bass_decay."
            f"{self._number(band.center_frequency_hz)}Hz="
            f"{self._number(band.estimated_decay_time_seconds)}s"
            for band in usable
        ) + (f"bass_decay.coverage_percent={self._number(analysis.coverage)}",)
        return AcousticObservation(
            observation_id="LOW_FREQUENCY_DECAY_FACTS",
            category=AcousticObservationCategory.LOW_FREQUENCY,
            title="Low-frequency decay facts",
            description=(
                f"Estimated decay times are available for {len(usable)} "
                "low-frequency bands."
            ),
            confidence=analysis.confidence,
            supporting_evidence=evidence,
            contradicting_evidence=(),
            limitations=(),
            source_analysis_ids=("BassDecayAnalysis",),
        )

    def _rt60(self, context):
        analysis = getattr(context, "rt60_analysis", None)
        if analysis is None or analysis.broadband_rt60_seconds is None:
            return None
        evidence = (
            "rt60.broadband_seconds="
            f"{self._number(analysis.broadband_rt60_seconds)}",
        ) + tuple(
            f"rt60.left_right.{self._number(center)}Hz="
            f"{self._number(value)}s"
            for center, value in sorted(
                analysis.left_right_band_differences_seconds.items()
            )
        )
        if analysis.minimum_rt60_seconds is not None:
            evidence += (
                f"rt60.minimum_seconds={self._number(analysis.minimum_rt60_seconds)}",
            )
        if analysis.maximum_rt60_seconds is not None:
            evidence += (
                f"rt60.maximum_seconds={self._number(analysis.maximum_rt60_seconds)}",
            )
        limitations = ()
        if analysis.minimum_rt60_seconds is None or analysis.maximum_rt60_seconds is None:
            limitations = ("RT60 aggregate range is unavailable.",)
        return AcousticObservation(
            observation_id="DECAY_RT60_FACTS",
            category=AcousticObservationCategory.DECAY,
            title="RT60 decay facts",
            description=(
                "Broadband RT60 is "
                f"{self._number(analysis.broadband_rt60_seconds)} seconds."
            ),
            confidence=analysis.confidence,
            supporting_evidence=evidence,
            contradicting_evidence=(),
            limitations=limitations,
            source_analysis_ids=("RT60Analysis",),
        )

    def _early_reflections(self, context):
        analysis = getattr(context, "etc_analysis", None)
        if analysis is None:
            return None
        total = (
            analysis.common_event_count
            + analysis.left_only_event_count
            + analysis.right_only_event_count
        )
        if total == 0:
            return None
        return AcousticObservation(
            observation_id="EARLY_REFLECTION_EVENT_FACTS",
            category=AcousticObservationCategory.EARLY_REFLECTIONS,
            title="Early-reflection event facts",
            description=f"ETC analysis contains {total} detected reflection events.",
            confidence=analysis.confidence,
            supporting_evidence=(
                f"etc.common_event_count={analysis.common_event_count}",
                f"etc.left_only_event_count={analysis.left_only_event_count}",
                f"etc.right_only_event_count={analysis.right_only_event_count}",
            ),
            contradicting_evidence=(),
            limitations=(),
            source_analysis_ids=("ETCAnalysis",),
        )

    def _clarity(self, context):
        analysis = getattr(context, "clarity_analysis", None)
        if analysis is None or not analysis.aggregate_bands:
            return None
        bands = tuple(
            band for band in analysis.aggregate_bands if band.c80_db is not None
        )
        if not bands:
            return None
        evidence = tuple(
            f"clarity.c80.{self._number(band.center_frequency_hz)}Hz="
            f"{self._number(band.c80_db)}dB"
            for band in bands
        )
        return AcousticObservation(
            observation_id="CLARITY_C80_FACTS",
            category=AcousticObservationCategory.CLARITY,
            title="C80 clarity facts",
            description=f"C80 values are available for {len(bands)} frequency bands.",
            confidence=analysis.confidence,
            supporting_evidence=evidence,
            contradicting_evidence=(),
            limitations=(),
            source_analysis_ids=("ClarityAnalysis",),
        )

    def _stereo(self, context):
        analysis = getattr(context, "stereo", None)
        if analysis is None or not (
            analysis.common_count or analysis.left_only_count or analysis.right_only_count
        ):
            return None
        return AcousticObservation(
            observation_id="STEREO_PEAK_DISTRIBUTION_FACTS",
            category=AcousticObservationCategory.STEREO,
            title="Stereo peak-distribution facts",
            description=(
                f"Stereo analysis contains {analysis.common_count} shared peaks, "
                f"{analysis.left_only_count} left-only peaks and "
                f"{analysis.right_only_count} right-only peaks."
            ),
            confidence=None,
            supporting_evidence=(
                f"stereo.common_peak_count={analysis.common_count}",
                f"stereo.left_only_peak_count={analysis.left_only_count}",
                f"stereo.right_only_peak_count={analysis.right_only_count}",
                f"stereo.symmetry_score={self._number(analysis.symmetry_score)}",
            ),
            contradicting_evidence=(),
            limitations=("StereoAnalysis exposes no confidence value.",),
            source_analysis_ids=("StereoAnalysis",),
        )
