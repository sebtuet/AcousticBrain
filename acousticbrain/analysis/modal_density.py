from acousticbrain.models import (
    ModalBand,
    ModalDensityAnalysis,
    RoomModesAnalysis,
    RoomModeType,
)


class ModalDensityAnalyzer:
    MINIMUM_FREQUENCY_HZ = 20.0

    def analyze(
        self,
        room_modes_analysis: RoomModesAnalysis,
        schroeder_frequency: float,
    ) -> ModalDensityAnalysis:
        if schroeder_frequency <= self.MINIMUM_FREQUENCY_HZ:
            return ModalDensityAnalysis()

        modes = sorted(
            (
                mode
                for mode in room_modes_analysis.modes
                if self.MINIMUM_FREQUENCY_HZ <= mode.frequency <= schroeder_frequency
            ),
            key=lambda mode: mode.frequency,
        )
        bands = self._bands(modes, schroeder_frequency)
        spacings = self._spacings([mode.frequency for mode in modes])
        average_density = len(modes) / (schroeder_frequency - self.MINIMUM_FREQUENCY_HZ)

        return ModalDensityAnalysis(
            bands=bands,
            total_mode_count=len(modes),
            axial_mode_count=self._count_type(modes, RoomModeType.AXIAL),
            tangential_mode_count=self._count_type(
                modes,
                RoomModeType.TANGENTIAL,
            ),
            oblique_mode_count=self._count_type(modes, RoomModeType.OBLIQUE),
            average_spacing_hz=self._average(spacings),
            minimum_spacing_hz=min(spacings) if spacings else None,
            maximum_spacing_hz=max(spacings) if spacings else None,
            sparse_bands=[
                band for band in bands if band.density_per_hz < average_density * 0.5
            ],
            dense_bands=[
                band for band in bands if band.density_per_hz > average_density * 1.5
            ],
            score=self._score(bands, spacings),
            confidence=self._confidence(len(modes)),
        )

    def _bands(self, modes, schroeder_frequency):
        boundaries = [self.MINIMUM_FREQUENCY_HZ]
        boundaries.extend(
            boundary
            for boundary in (50.0, 100.0)
            if boundary < schroeder_frequency
        )
        boundaries.append(schroeder_frequency)

        bands = []
        for minimum, maximum in zip(boundaries, boundaries[1:]):
            band_modes = [
                mode
                for mode in modes
                if minimum <= mode.frequency < maximum
            ]
            frequencies = [mode.frequency for mode in band_modes]
            bands.append(
                ModalBand(
                    minimum_hz=minimum,
                    maximum_hz=maximum,
                    mode_count=len(band_modes),
                    density_per_hz=len(band_modes) / (maximum - minimum),
                    average_spacing_hz=self._average(self._spacings(frequencies)),
                    frequencies=frequencies,
                    modes=band_modes,
                )
            )
        return bands

    def _score(self, bands, spacings):
        if not spacings:
            return 0.0

        average_spacing = self._average(spacings)
        spacing_variation = self._average(
            [abs(spacing - average_spacing) / average_spacing for spacing in spacings]
        )
        spacing_score = max(0.0, 100.0 * (1 - spacing_variation))
        gap_score = max(0.0, 100.0 * average_spacing / max(spacings))

        densities = [band.density_per_hz for band in bands]
        average_density = self._average(densities)
        density_variation = self._average(
            [abs(density - average_density) / average_density for density in densities]
        ) if average_density else 1.0
        density_score = max(0.0, 100.0 * (1 - density_variation))

        return (spacing_score + gap_score + density_score) / 3

    @staticmethod
    def _spacings(frequencies):
        return [
            right - left
            for left, right in zip(frequencies, frequencies[1:])
        ]

    @staticmethod
    def _average(values):
        return sum(values) / len(values) if values else None

    @staticmethod
    def _confidence(mode_count):
        if mode_count == 0:
            return 0.0
        return min(75.0, 50.0 + mode_count * 5.0)

    @staticmethod
    def _count_type(modes, mode_type):
        return sum(mode.mode_type is mode_type for mode in modes)
