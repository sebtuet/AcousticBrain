from statistics import fmean

from acousticbrain.models import (
    ImpulseChannel,
    RT60Analysis,
    RT60BandAnalysis,
    RT60ChannelAnalysis,
)


class RT60Aggregator:
    """Agrège des analyses RT60 de canaux sans accéder aux réponses brutes."""

    def aggregate(
        self,
        channel_analyses: dict[ImpulseChannel, RT60ChannelAnalysis],
    ) -> RT60Analysis:
        self._validate(channel_analyses)
        available_channels = tuple(
            channel
            for channel in ImpulseChannel
            if channel in channel_analyses
        )
        analyses = [channel_analyses[channel] for channel in available_channels]
        band_maps = [self._available_bands(analysis) for analysis in analyses]
        common_centers = self._common_centers(band_maps)
        aggregate_bands = [
            self._aggregate_band(center, band_maps)
            for center in common_centers
        ]
        broadband_values = [
            analysis.broadband_rt60_seconds
            for analysis in analyses
            if analysis.broadband_rt60_seconds is not None
        ]

        return RT60Analysis(
            channel_analyses=analyses,
            available_channels=available_channels,
            aggregate_bands=aggregate_bands,
            common_center_frequencies_hz=common_centers,
            left_right_band_differences_seconds=self._left_right_differences(
                channel_analyses
            ),
            interchannel_homogeneity=self._homogeneity(band_maps, common_centers),
            broadband_rt60_seconds=(
                fmean(broadband_values) if broadband_values else None
            ),
            minimum_rt60_seconds=(min(broadband_values) if broadband_values else None),
            maximum_rt60_seconds=(max(broadband_values) if broadband_values else None),
            confidence=self._confidence(analyses, band_maps, common_centers),
        )

    @staticmethod
    def _validate(channel_analyses):
        for channel, analysis in channel_analyses.items():
            if channel is not analysis.channel:
                raise ValueError(
                    "RT60 channel analysis does not match its channel key."
                )

    @staticmethod
    def _available_bands(analysis):
        return {
            band.center_frequency_hz: band
            for band in analysis.band_analyses
            if band.rt60_seconds is not None
        }

    @staticmethod
    def _common_centers(band_maps):
        if not band_maps:
            return ()
        common = set(band_maps[0])
        for band_map in band_maps[1:]:
            common.intersection_update(band_map)
        return tuple(sorted(common))

    @staticmethod
    def _aggregate_band(center, band_maps):
        bands = [band_map[center] for band_map in band_maps]

        def average(field):
            values = [getattr(band, field) for band in bands]
            available = [value for value in values if value is not None]
            return fmean(available) if available else None

        reference = bands[0]
        return RT60BandAnalysis(
            center_frequency_hz=center,
            minimum_frequency_hz=reference.minimum_frequency_hz,
            maximum_frequency_hz=reference.maximum_frequency_hz,
            rt60_seconds=fmean(band.rt60_seconds for band in bands),
            decay_range_db=(0.0, 0.0),
            fit_correlation=average("fit_correlation"),
            confidence=fmean(band.confidence for band in bands),
            edt_seconds=average("edt_seconds"),
            t20_seconds=average("t20_seconds"),
            t30_seconds=average("t30_seconds"),
            selected_estimate="CHANNEL_MEAN",
            noise_floor_db=average("noise_floor_db"),
        )

    @classmethod
    def _left_right_differences(cls, channel_analyses):
        left = channel_analyses.get(ImpulseChannel.LEFT)
        right = channel_analyses.get(ImpulseChannel.RIGHT)
        if left is None or right is None:
            return {}

        left_bands = cls._available_bands(left)
        right_bands = cls._available_bands(right)
        return {
            center: left_bands[center].rt60_seconds - right_bands[center].rt60_seconds
            for center in sorted(set(left_bands).intersection(right_bands))
        }

    @staticmethod
    def _homogeneity(band_maps, common_centers):
        if len(band_maps) < 2 or not common_centers:
            return None

        relative_spreads = []
        for center in common_centers:
            values = [band_map[center].rt60_seconds for band_map in band_maps]
            average = fmean(values)
            if average > 0:
                relative_spreads.append((max(values) - min(values)) / average)
        if not relative_spreads:
            return None
        return max(0.0, 100.0 * (1.0 - fmean(relative_spreads)))

    @staticmethod
    def _confidence(analyses, band_maps, common_centers):
        if not analyses:
            return 0.0
        union = set().union(*(set(band_map) for band_map in band_maps))
        coverage = len(common_centers) / len(union) if union else 0.0
        return fmean(analysis.confidence for analysis in analyses) * coverage

