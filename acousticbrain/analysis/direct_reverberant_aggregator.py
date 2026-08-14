from statistics import fmean

from acousticbrain.models import (
    DirectReverberantAnalysis,
    DirectReverberantBandAnalysis,
    DirectReverberantChannelAnalysis,
    EnergyWindowAnalysis,
    ImpulseChannel,
)


class DirectReverberantAggregator:
    """Agrège uniquement des analyses D/R de canaux déjà calculées."""

    def aggregate(
        self,
        channel_analyses: dict[
            ImpulseChannel, DirectReverberantChannelAnalysis
        ],
    ) -> DirectReverberantAnalysis:
        self._validate(channel_analyses)
        available_channels = tuple(
            channel for channel in ImpulseChannel if channel in channel_analyses
        )
        analyses = [channel_analyses[channel] for channel in available_channels]
        band_maps = [self._available_bands(analysis) for analysis in analyses]
        common_centers = self._common_centers(band_maps)
        broadband_values = [
            analysis.broadband_direct_to_reverberant_db
            for analysis in analyses
            if analysis.broadband_direct_to_reverberant_db is not None
        ]

        return DirectReverberantAnalysis(
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
            left_right_direct_to_reverberant_differences_db=(
                self._left_right_differences(channel_analyses)
            ),
            broadband_direct_to_reverberant_db=(
                fmean(broadband_values) if broadband_values else None
            ),
            minimum_broadband_direct_to_reverberant_db=(
                min(broadband_values) if broadband_values else None
            ),
            maximum_broadband_direct_to_reverberant_db=(
                max(broadband_values) if broadband_values else None
            ),
            confidence=self._confidence(analyses, band_maps, common_centers),
        )

    @classmethod
    def _validate(cls, channel_analyses):
        configurations = set()
        for channel, analysis in channel_analyses.items():
            if channel is not analysis.channel:
                raise ValueError(
                    "D/R channel analysis does not match its channel key."
                )
            configurations.add(cls._configuration(analysis))
        if len(configurations) > 1:
            raise ValueError("D/R channel window configurations must match.")

    @staticmethod
    def _configuration(analysis):
        return (
            analysis.window_start_ms,
            analysis.direct_end_ms,
            analysis.early_end_ms,
            analysis.analysis_end_ms,
        )

    @staticmethod
    def _available_bands(analysis):
        return {
            band.center_frequency_hz: band
            for band in analysis.band_analyses
            if band.direct_to_reverberant_db is not None
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
        return DirectReverberantBandAnalysis(
            center_frequency_hz=center,
            direct_window=cls._aggregate_window(
                "DIRECT", [band.direct_window for band in bands]
            ),
            early_window=cls._aggregate_window(
                "EARLY", [band.early_window for band in bands]
            ),
            late_window=cls._aggregate_window(
                "LATE", [band.late_window for band in bands]
            ),
            total_window=cls._aggregate_window(
                "TOTAL", [band.total_window for band in bands]
            ),
            direct_to_reverberant_db=fmean(
                band.direct_to_reverberant_db for band in bands
            ),
            confidence=fmean(band.confidence for band in bands),
            method="CHANNEL_MEAN",
        )

    @staticmethod
    def _aggregate_window(name, windows):
        reference = windows[0]

        def average(attribute):
            values = [
                value
                for window in windows
                if (value := getattr(window, attribute)) is not None
            ]
            return fmean(values) if values else None

        return EnergyWindowAnalysis(
            name=name,
            start_ms=reference.start_ms,
            end_ms=reference.end_ms,
            energy=average("energy"),
            relative_energy_db=average("relative_energy_db"),
            confidence=fmean(window.confidence for window in windows),
            method="CHANNEL_MEAN",
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
            center: (
                left_bands[center].direct_to_reverberant_db
                - right_bands[center].direct_to_reverberant_db
            )
            for center in sorted(set(left_bands).intersection(right_bands))
        }

    @staticmethod
    def _confidence(analyses, band_maps, common_centers):
        if not analyses:
            return 0.0
        union = set().union(*(set(band_map) for band_map in band_maps))
        coverage = len(common_centers) / len(union) if union else 0.0
        return fmean(analysis.confidence for analysis in analyses) * coverage
