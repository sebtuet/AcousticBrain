from acousticbrain.models import FrequencyBand


class RuleEngine:

    def strongest_peak(self, band: FrequencyBand):

        if len(band.peaks) == 0:
            return None

        return max(
            band.peaks,
            key=lambda peak: peak.prominence
        )
        