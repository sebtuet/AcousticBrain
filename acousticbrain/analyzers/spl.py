from acousticbrain.models import Measurement


class SPLAnalyzer:

    def analyze(self, measurement: Measurement):

        if len(measurement.frequency) == 0:
            raise ValueError("Measurement vide")

        return {

            "points": len(measurement.frequency),

            "min_frequency": min(measurement.frequency),

            "max_frequency": max(measurement.frequency),

            "min_spl": min(measurement.spl),

            "max_spl": max(measurement.spl),

            "average_spl": sum(measurement.spl) / len(measurement.spl),

        }