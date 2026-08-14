from acousticbrain.models import StereoAnalysis


class StereoAnalyzer:
    """Associe les pics gauche/droite qui représentent le même phénomène."""

    BANDS = (
        (20.0, 200.0),
        (200.0, 500.0),
        (500.0, 2000.0),
        (2000.0, 20000.0),
    )

    def analyze(
        self,
        left_peaks,
        right_peaks,
        tolerance_hz=2.0,
        relative_tolerance=0.02,
        maximum_tolerance_hz=30.0,
        prominence_tolerance_db=3.0,
        room_modes=None,
        left_measurement=None,
        right_measurement=None,
        weight_power=2.0,
    ):
        """Compare les pics avec des tolérances adaptées à leur fréquence.

        Deux pics ne peuvent être associés que s'ils appartiennent à la même
        bande, que leur écart fréquentiel est inférieur à ``max(tolerance_hz,
        fréquence * relative_tolerance)`` et que leurs prominences sont proches.
        Les mêmes règles servent aussi à constater les modes axiaux présents
        dans chaque canal. Les balances sont des écarts moyens gauche-droite,
        exprimés en dB.
        """
        if tolerance_hz < 0 or relative_tolerance < 0 or maximum_tolerance_hz < 0:
            raise ValueError("Les tolérances de fréquence doivent être positives.")
        if maximum_tolerance_hz < tolerance_hz:
            raise ValueError("La tolérance maximale doit être supérieure au minimum.")
        if prominence_tolerance_db < 0:
            raise ValueError("La tolérance de prominence doit être positive.")
        if weight_power <= 0:
            raise ValueError("La puissance de pondération doit être positive.")

        result = StereoAnalysis(
            tolerance_hz=tolerance_hz,
            relative_tolerance=relative_tolerance,
            maximum_tolerance_hz=maximum_tolerance_hz,
            weight_power=weight_power,
        )

        matched_right = set()

        for left_peak in left_peaks:

            best_index = None
            best_score = None

            for index, right_peak in enumerate(right_peaks):

                if index in matched_right:
                    continue

                left_band = self._band(left_peak.frequency)
                right_band = self._band(right_peak.frequency)

                if left_band is None or left_band != right_band:
                    continue

                frequency_error = abs(left_peak.frequency - right_peak.frequency)
                frequency_tolerance = self._frequency_tolerance(
                    left_peak.frequency,
                    right_peak.frequency,
                    tolerance_hz,
                    relative_tolerance,
                    maximum_tolerance_hz,
                )

                if frequency_error > frequency_tolerance:
                    continue

                prominence_error = abs(
                    left_peak.prominence - right_peak.prominence
                )

                if prominence_error > prominence_tolerance_db:
                    continue

                score = self._match_score(
                    frequency_error,
                    frequency_tolerance,
                    prominence_error,
                    prominence_tolerance_db,
                )

                if best_score is None or score < best_score:
                    best_score = score
                    best_index = index

            if best_index is None:

                result.left_only_peaks.append(
                    left_peak
                )

                continue

            matched_right.add(best_index)

            result.common_peaks.append(
                (
                    left_peak,
                    right_peaks[best_index],
                )
            )

        for index, right_peak in enumerate(right_peaks):

            if index not in matched_right:

                result.right_only_peaks.append(
                    right_peak
                )

        self._classify_modes(result, left_peaks, right_peaks, room_modes or [])
        self._calculate_balances(result, left_measurement, right_measurement)

        return result

    def _classify_modes(self, result, left_peaks, right_peaks, room_modes):
        for mode in room_modes:
            left_present = self._has_peak_near(mode.frequency, left_peaks, result)
            right_present = self._has_peak_near(mode.frequency, right_peaks, result)

            if left_present and right_present:
                result.common_modes.append(mode)
            elif left_present:
                result.left_only_modes.append(mode)
            elif right_present:
                result.right_only_modes.append(mode)

    def _has_peak_near(self, frequency, peaks, result):
        tolerance = self._frequency_tolerance(
            frequency,
            frequency,
            result.tolerance_hz,
            result.relative_tolerance,
            result.maximum_tolerance_hz,
        )
        return any(abs(peak.frequency - frequency) <= tolerance for peak in peaks)

    def _calculate_balances(self, result, left_measurement, right_measurement):
        if left_measurement is None or right_measurement is None:
            return

        balances = []
        for minimum, maximum in (
            self.BANDS[0],
            (200.0, 2000.0),
            self.BANDS[-1],
        ):
            left_values = [
                spl for frequency, spl in zip(left_measurement.frequency, left_measurement.spl)
                if minimum <= frequency < maximum
            ]
            right_values = [
                spl for frequency, spl in zip(right_measurement.frequency, right_measurement.spl)
                if minimum <= frequency < maximum
            ]
            if not left_values or not right_values:
                balances.append(None)
                continue
            balances.append(sum(left_values) / len(left_values) - sum(right_values) / len(right_values))

        result.balance_low, result.balance_mid, result.balance_high = balances

    def _band(self, frequency):
        for index, (minimum, maximum) in enumerate(self.BANDS):
            if minimum <= frequency < maximum:
                return index
        return None

    @staticmethod
    def _match_score(
        frequency_error,
        frequency_tolerance,
        prominence_error,
        prominence_tolerance_db,
    ):
        frequency_score = (
            frequency_error / frequency_tolerance
            if frequency_tolerance else frequency_error
        )
        prominence_score = (
            prominence_error / prominence_tolerance_db
            if prominence_tolerance_db else prominence_error
        )
        return frequency_score + prominence_score

    @staticmethod
    def _frequency_tolerance(
        left_frequency,
        right_frequency,
        minimum_tolerance_hz,
        relative_tolerance,
        maximum_tolerance_hz,
    ):
        return max(
            minimum_tolerance_hz,
            min(
                maximum_tolerance_hz,
                ((left_frequency + right_frequency) / 2) * relative_tolerance,
            ),
        )
