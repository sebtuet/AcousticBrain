from acousticbrain.models import FrequencyBand


class FrequencyBandClassifier:

    def classify(self, peaks):

        bands = [

            FrequencyBand(
                name="Grave",
                minimum=20,
                maximum=200,
            ),

            FrequencyBand(
                name="Bas Médium",
                minimum=200,
                maximum=500,
            ),

            FrequencyBand(
                name="Médium",
                minimum=500,
                maximum=2000,
            ),

            FrequencyBand(
                name="Aigu",
                minimum=2000,
                maximum=20000,
            ),

        ]

        for peak in peaks:

            for band in bands:

                if band.contains(peak.frequency):

                    band.peaks.append(peak)

                    break

        return bands
        