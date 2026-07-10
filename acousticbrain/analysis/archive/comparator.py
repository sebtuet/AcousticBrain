from acousticbrain.models import FrequencyDifference


class MeasurementComparator:

    def compare(

        self,

        measurement_a,

        measurement_b,

    ):

        result = []

        count = min(

            len(measurement_a.frequency),

            len(measurement_b.frequency),

        )

        for i in range(count):

            result.append(

                FrequencyDifference(

                    frequency=measurement_a.frequency[i],

                    spl_a=measurement_a.spl[i],

                    spl_b=measurement_b.spl[i],

                    difference=(

                        measurement_a.spl[i]

                        - measurement_b.spl[i]

                    ),

                )

            )

        return result