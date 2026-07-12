from statistics import fmean

from acousticbrain.models import (
    BassDecayAnalysis,
    BassDecayCorrelation,
    BassDecayCorrelationAnalysis,
    DirectReverberantAnalysis,
    ModalDensityAnalysis,
    RoomModesAnalysis,
    RT60Analysis,
)


class BassDecayCorrelationEngine:
    """Croise Bass Decay avec des analyses structurées existantes."""

    LONG_BASS_DECAY_SECONDS = 0.8
    HIGH_RT60_SECONDS = 0.6
    LOW_DRR_DB = 0.0
    ASYMMETRIC_DECAY_SECONDS = 0.25

    def correlate(
        self,
        bass_decay: BassDecayAnalysis,
        room_modes: RoomModesAnalysis,
        modal_density: ModalDensityAnalysis,
        rt60: RT60Analysis,
        direct_reverberant: DirectReverberantAnalysis,
    ) -> BassDecayCorrelationAnalysis:
        correlations = [
            item
            for item in (
                self._slow_decay_modal(
                    bass_decay, room_modes, modal_density
                ),
                self._slow_decay_rt60(bass_decay, rt60),
                self._low_drr_long_decay(bass_decay, direct_reverberant),
                self._asymmetric_decay(bass_decay),
            )
            if item is not None
        ]
        return BassDecayCorrelationAnalysis(
            correlations=correlations,
            source_analyses=(
                "BassDecayAnalysis",
                "RoomModesAnalysis",
                "ModalDensityAnalysis",
                "RT60Analysis",
                "DirectReverberantAnalysis",
            ),
            confidence=(
                fmean(item.confidence for item in correlations)
                if correlations
                else 0.0
            ),
        )

    @classmethod
    def _slow_decay_modal(cls, bass_decay, room_modes, modal_density):
        slow = cls._slow_bands(bass_decay)
        matched = {
            center: [
                mode.frequency
                for mode in room_modes.modes
                if band.minimum_frequency_hz
                <= mode.frequency
                <= band.maximum_frequency_hz
            ]
            for center, band in slow.items()
        }
        matched = {
            center: frequencies
            for center, frequencies in matched.items()
            if frequencies
            and any(
                modal_band.minimum_hz <= center <= modal_band.maximum_hz
                for modal_band in modal_density.bands
            )
        }
        if not matched:
            return None
        centers = tuple(sorted(matched))
        maximum_decay = max(
            slow[center].estimated_decay_time_seconds for center in centers
        )
        modal_bands = [
            modal_band
            for center in centers
            for modal_band in modal_density.bands
            if modal_band.minimum_hz <= center <= modal_band.maximum_hz
        ]
        return BassDecayCorrelation(
            code="SLOW_DECAY_MODAL_INTERACTION",
            center_frequencies_hz=centers,
            source_metrics={
                "maximum_decay_time_s": maximum_decay,
                "matched_mode_count": float(
                    sum(len(frequencies) for frequencies in matched.values())
                ),
                "maximum_local_mode_count": float(
                    max(
                        (band.mode_count for band in modal_bands),
                        default=0,
                    )
                ),
            },
            source_analyses=(
                "BassDecayAnalysis",
                "RoomModesAnalysis",
                "ModalDensityAnalysis",
            ),
            score=cls._paired_score(
                maximum_decay / cls.LONG_BASS_DECAY_SECONDS - 1.0,
                sum(len(frequencies) for frequencies in matched.values())
                / len(centers)
                - 1.0,
            ),
            confidence=min(
                fmean(slow[center].confidence for center in centers),
                room_modes.confidence,
                modal_density.confidence,
            ),
            technical_basis_codes=(
                "BASS_DECAY_ABOVE_THRESHOLD",
                "ROOM_MODE_WITHIN_DECAY_BAND",
                "MODAL_DENSITY_BAND_AVAILABLE",
            ),
        )

    @classmethod
    def _slow_decay_rt60(cls, bass_decay, rt60):
        slow = cls._slow_bands(bass_decay)
        rt60_bands = {
            band.center_frequency_hz: band
            for band in rt60.aggregate_bands
            if band.rt60_seconds is not None
        }
        centers = tuple(
            center
            for center in sorted(set(slow).intersection(rt60_bands))
            if rt60_bands[center].rt60_seconds > cls.HIGH_RT60_SECONDS
        )
        if not centers:
            return None
        maximum_decay = max(
            slow[center].estimated_decay_time_seconds for center in centers
        )
        maximum_rt60 = max(rt60_bands[center].rt60_seconds for center in centers)
        return BassDecayCorrelation(
            code="SLOW_DECAY_RT60_INTERACTION",
            center_frequencies_hz=centers,
            source_metrics={
                "maximum_decay_time_s": maximum_decay,
                "maximum_rt60_s": maximum_rt60,
                "matched_band_count": float(len(centers)),
            },
            source_analyses=("BassDecayAnalysis", "RT60Analysis"),
            score=cls._paired_score(
                maximum_decay / cls.LONG_BASS_DECAY_SECONDS - 1.0,
                maximum_rt60 / cls.HIGH_RT60_SECONDS - 1.0,
            ),
            confidence=min(
                fmean(slow[center].confidence for center in centers),
                fmean(rt60_bands[center].confidence for center in centers),
            ),
            technical_basis_codes=(
                "BASS_DECAY_ABOVE_THRESHOLD",
                "RT60_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _low_drr_long_decay(cls, bass_decay, direct_reverberant):
        slow = cls._slow_bands(bass_decay)
        drr_bands = {
            band.center_frequency_hz: band
            for band in direct_reverberant.aggregate_bands
            if band.direct_to_reverberant_db is not None
        }
        centers = tuple(
            center
            for center in sorted(set(slow).intersection(drr_bands))
            if drr_bands[center].direct_to_reverberant_db < cls.LOW_DRR_DB
        )
        if not centers:
            return None
        maximum_decay = max(
            slow[center].estimated_decay_time_seconds for center in centers
        )
        minimum_drr = min(
            drr_bands[center].direct_to_reverberant_db for center in centers
        )
        return BassDecayCorrelation(
            code="LOW_DRR_LONG_BASS_DECAY",
            center_frequencies_hz=centers,
            source_metrics={
                "maximum_decay_time_s": maximum_decay,
                "minimum_drr_db": minimum_drr,
                "matched_band_count": float(len(centers)),
            },
            source_analyses=(
                "BassDecayAnalysis",
                "DirectReverberantAnalysis",
            ),
            score=cls._paired_score(
                maximum_decay / cls.LONG_BASS_DECAY_SECONDS - 1.0,
                (cls.LOW_DRR_DB - minimum_drr) / 6.0,
            ),
            confidence=min(
                fmean(slow[center].confidence for center in centers),
                fmean(drr_bands[center].confidence for center in centers),
            ),
            technical_basis_codes=(
                "BASS_DECAY_ABOVE_THRESHOLD",
                "DRR_BELOW_THRESHOLD",
            ),
        )

    @classmethod
    def _asymmetric_decay(cls, bass_decay):
        differences = [
            item
            for item in bass_decay.left_right_band_differences
            if abs(item.difference_seconds) >= cls.ASYMMETRIC_DECAY_SECONDS
        ]
        if not differences:
            return None
        maximum = max(abs(item.difference_seconds) for item in differences)
        return BassDecayCorrelation(
            code="ASYMMETRIC_BASS_DECAY",
            center_frequencies_hz=tuple(
                sorted(item.center_frequency_hz for item in differences)
            ),
            source_metrics={
                "maximum_left_right_difference_s": maximum,
                "asymmetric_band_count": float(len(differences)),
            },
            source_analyses=("BassDecayAnalysis",),
            score=min(
                100.0,
                50.0
                + 50.0
                * min(
                    1.0,
                    maximum / cls.ASYMMETRIC_DECAY_SECONDS - 1.0,
                ),
            ),
            confidence=min(item.confidence for item in differences),
            technical_basis_codes=(
                "BASS_DECAY_LEFT_RIGHT_DIFFERENCE_ABOVE_THRESHOLD",
            ),
        )

    @classmethod
    def _slow_bands(cls, analysis):
        return {
            band.center_frequency_hz: band
            for band in analysis.aggregate_bands
            if band.estimated_decay_time_seconds is not None
            and band.estimated_decay_time_seconds > cls.LONG_BASS_DECAY_SECONDS
        }

    @staticmethod
    def _paired_score(first_excess, second_excess):
        return min(
            100.0,
            50.0
            + 25.0
            * (
                min(1.0, max(0.0, first_excess))
                + min(1.0, max(0.0, second_excess))
            ),
        )
