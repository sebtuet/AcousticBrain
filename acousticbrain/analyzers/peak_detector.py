from scipy.signal import find_peaks

from acousticbrain.models import Peak


class PeakDetector:

    def detect(
        self,
        measurement,
        prominence=3.0,
        distance=10,
    ):

        indices, properties = find_peaks(
            measurement.spl,
            prominence=prominence,
            distance=distance,
        )

        peaks = []

        for i, index in enumerate(indices):

            peaks.append(
                Peak(
                    frequency=measurement.frequency[index],
                    spl=measurement.spl[index],
                    index=index,
                    prominence=properties["prominences"][i],
                )
            )

        return peaks
        