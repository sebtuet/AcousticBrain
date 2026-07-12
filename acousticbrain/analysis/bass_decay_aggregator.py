from statistics import fmean

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayBandAnalysis,
    BassDecayBandDifference,
    BassDecayChannelAnalysis,
    DecayUsability,
    ImpulseChannel,
)


class BassDecayAggregator:
    """Agrège uniquement des analyses Bass Decay mono-canal."""

    AGGREGATE_METHOD = "CHANNEL_MEAN"

    def aggregate(
        self,
        channel_analyses: dict[ImpulseChannel, BassDecayChannelAnalysis],
    ) -> BassDecayAnalysis:
        self._validate(channel_analyses)
        available_channels = tuple(
            channel for channel in ImpulseChannel if channel in channel_analyses
        )
        analyses = [channel_analyses[channel] for channel in available_channels]
        usable_maps = [self._usable_bands(analysis) for analysis in analyses]
        common_centers = self._common_centers(usable_maps)
        coverage = self._coverage(analyses, common_centers)

        return BassDecayAnalysis(
            channel_analyses={
                channel: channel_analyses[channel]
                for channel in available_channels
            },
            available_channels=available_channels,
            aggregate_bands=[
                self._aggregate_band(center, usable_maps)
                for center in common_centers
            ],
            common_center_frequencies_hz=common_centers,
            left_right_band_differences=self._left_right_differences(
                channel_analyses
            ),
            coverage=coverage,
            confidence=self._confidence(analyses, coverage),
        )

    @classmethod
    def _validate(cls, channel_analyses):
        methods = set()
        bounds_by_center = {}
        for channel, analysis in channel_analyses.items():
            if channel is not analysis.channel:
                raise ValueError(
                    "Bass decay channel analysis does not match its channel key."
                )
            methods.add(analysis.method)
            seen = set()
            for band in analysis.band_analyses:
                center = band.center_frequency_hz
                if center in seen:
                    raise ValueError(
                        "Bass decay channel contains a duplicate band center."
                    )
                seen.add(center)
                bounds = (
                    band.minimum_frequency_hz,
                    band.maximum_frequency_hz,
                )
                reference = bounds_by_center.setdefault(center, bounds)
                if bounds != reference:
                    raise ValueError(
                        "Bass decay band bounds must match across channels."
                    )
        if len(methods) > 1:
            raise ValueError("Bass decay channel methods must match.")

    @staticmethod
    def _usable_bands(analysis):
        return {
            band.center_frequency_hz: band
            for band in analysis.band_analyses
            if band.usability is DecayUsability.USABLE
        }

    @staticmethod
    def _common_centers(band_maps):
        if not band_maps:
            return ()
        common = set(band_maps[0])
        for band_map in band_maps[1:]:
            common.intersection_update(band_map)
        return tuple(sorted(common))

    @classmethod
    def _aggregate_band(cls, center, band_maps):
        bands = [band_map[center] for band_map in band_maps]
        reference = bands[0]

        def average(field):
            return fmean(getattr(band, field) for band in bands)

        return BassDecayBandAnalysis(
            center_frequency_hz=center,
            minimum_frequency_hz=reference.minimum_frequency_hz,
            maximum_frequency_hz=reference.maximum_frequency_hz,
            start_level_db=average("start_level_db"),
            end_level_db=average("end_level_db"),
            observed_decay_range_db=average("observed_decay_range_db"),
            observed_duration_seconds=average("observed_duration_seconds"),
            decay_slope_db_per_second=average("decay_slope_db_per_second"),
            estimated_decay_time_seconds=average(
                "estimated_decay_time_seconds"
            ),
            noise_floor_db=average("noise_floor_db"),
            noise_margin_db=average("noise_margin_db"),
            fit_correlation=average("fit_correlation"),
            confidence=average("confidence"),
            method=cls.AGGREGATE_METHOD,
            usability=DecayUsability.USABLE,
        )

    @classmethod
    def _left_right_differences(cls, channel_analyses):
        left = channel_analyses.get(ImpulseChannel.LEFT)
        right = channel_analyses.get(ImpulseChannel.RIGHT)
        if left is None or right is None:
            return []
        left_bands = cls._usable_bands(left)
        right_bands = cls._usable_bands(right)
        return [
            BassDecayBandDifference(
                center_frequency_hz=center,
                difference_seconds=(
                    left_bands[center].estimated_decay_time_seconds
                    - right_bands[center].estimated_decay_time_seconds
                ),
                left_decay_time_seconds=(
                    left_bands[center].estimated_decay_time_seconds
                ),
                right_decay_time_seconds=(
                    right_bands[center].estimated_decay_time_seconds
                ),
                confidence=min(
                    left_bands[center].confidence,
                    right_bands[center].confidence,
                ),
                left_method=left_bands[center].method,
                right_method=right_bands[center].method,
            )
            for center in sorted(set(left_bands).intersection(right_bands))
        ]

    @staticmethod
    def _coverage(analyses, common_centers):
        if not analyses:
            return 0.0
        all_centers = {
            band.center_frequency_hz
            for analysis in analyses
            for band in analysis.band_analyses
        }
        if not all_centers:
            return 0.0
        return 100.0 * len(common_centers) / len(all_centers)

    @staticmethod
    def _confidence(analyses, coverage):
        if not analyses:
            return 0.0
        return fmean(analysis.confidence for analysis in analyses) * coverage / 100.0
