from scipy.signal import find_peaks

from acousticbrain.models import Peak


class DipDetector:

    def detect(
        self,
        measurement,
        prominence=6.0,
        distance=10,
    ):

        inverted = [-value for value in measurement.spl]

        indices, properties = find_peaks(
            inverted,
            prominence=prominence,
            distance=distance,
        )

        dips = []

        for i, index in enumerate(indices):

            dips.append(

                Peak(

                    frequency=measurement.frequency[index],

                    spl=measurement.spl[index],

                    index=index,

                    prominence=properties["prominences"][i],

                )

            )

        return dips