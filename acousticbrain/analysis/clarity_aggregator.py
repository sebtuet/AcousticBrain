from statistics import fmean

from acousticbrain.models import (
    ClarityAnalysis,
    ClarityBandAnalysis,
    ClarityChannelAnalysis,
    ImpulseChannel,
)


class ClarityAggregator:
    """Agrège des analyses de clarté sans accéder aux impulsions brutes."""

    def aggregate(
        self,
        channel_analyses: dict[ImpulseChannel, ClarityChannelAnalysis],
    ) -> ClarityAnalysis:
        self._validate(channel_analyses)
        available_channels = tuple(
            channel for channel in ImpulseChannel if channel in channel_analyses
        )
        analyses = [channel_analyses[channel] for channel in available_channels]
        band_maps = [self._bands_by_center(analysis) for analysis in analyses]
        common_centers = self._common_centers(band_maps)

        return ClarityAnalysis(
            channel_analyses={
                channel: channel_analyses[channel]
                for channel in available_channels
            },
            available_channels=available_channels,
            aggregate_bands=[
                self._aggregate_band(center, band_maps)
                for center in common_centers
            ],
            common_center_frequencies_hz=common_centers,
            left_right_c50_differences_db=self._left_right_differences(
                channel_analyses, "c50_db"
            ),
            left_right_c80_differences_db=self._left_right_differences(
                channel_analyses, "c80_db"
            ),
            left_right_d50_differences_percent=self._left_right_differences(
                channel_analyses, "d50_percent"
            ),
            left_right_ts_differences_s=self._left_right_differences(
                channel_analyses, "ts_s"
            ),
            confidence=self._confidence(analyses, band_maps, common_centers),
        )

    @staticmethod
    def _validate(channel_analyses):
        for channel, analysis in channel_analyses.items():
            if channel is not analysis.channel:
                raise ValueError(
                    "Clarity channel analysis does not match its channel key."
                )

    @staticmethod
    def _bands_by_center(analysis):
        return {
            band.center_frequency_hz: band
            for band in analysis.band_analyses
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
        return ClarityBandAnalysis(
            center_frequency_hz=center,
            c50_db=cls._average(bands, "c50_db"),
            c80_db=cls._average(bands, "c80_db"),
            d50_percent=cls._average(bands, "d50_percent"),
            ts_s=cls._average(bands, "ts_s"),
            confidence=fmean(band.confidence for band in bands),
            method="CHANNEL_MEAN",
        )

    @staticmethod
    def _average(bands, attribute):
        values = [
            value
            for band in bands
            if (value := getattr(band, attribute)) is not None
        ]
        return fmean(values) if values else None

    @classmethod
    def _left_right_differences(cls, channel_analyses, attribute):
        left = channel_analyses.get(ImpulseChannel.LEFT)
        right = channel_analyses.get(ImpulseChannel.RIGHT)
        if left is None or right is None:
            return {}
        left_bands = cls._bands_by_center(left)
        right_bands = cls._bands_by_center(right)
        common = sorted(set(left_bands).intersection(right_bands))
        return {
            center: left_value - right_value
            for center in common
            if (left_value := getattr(left_bands[center], attribute)) is not None
            and (right_value := getattr(right_bands[center], attribute)) is not None
        }

    @classmethod
    def _confidence(cls, analyses, band_maps, common_centers):
        if not analyses:
            return 0.0
        union = set().union(*(set(band_map) for band_map in band_maps))
        coverage = len(common_centers) / len(union) if union else 0.0
        coherence = cls._coherence(band_maps, common_centers)
        return fmean(analysis.confidence for analysis in analyses) * coverage * coherence

    @classmethod
    def _coherence(cls, band_maps, common_centers):
        if len(band_maps) < 2 or not common_centers:
            return 1.0
        agreements = []
        for center in common_centers:
            bands = [band_map[center] for band_map in band_maps]
            for attribute in ("c50_db", "c80_db", "d50_percent", "ts_s"):
                values = [
                    value
                    for band in bands
                    if (value := getattr(band, attribute)) is not None
                ]
                if len(values) < 2:
                    continue
                scale = max(fmean(abs(value) for value in values), 1e-12)
                relative_spread = (max(values) - min(values)) / scale
                agreements.append(max(0.0, 1.0 - relative_spread))
        return fmean(agreements) if agreements else 0.0
