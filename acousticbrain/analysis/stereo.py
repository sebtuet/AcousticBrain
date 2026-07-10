from acousticbrain.models import StereoAnalysis


class StereoAnalyzer:

    def analyze(
        self,
        left_peaks,
        right_peaks,
        tolerance_hz=2.0,
    ):

        result = StereoAnalysis(
            tolerance_hz=tolerance_hz
        )

        matched_right = set()

        for left_peak in left_peaks:

            best_index = None
            best_error = None

            for index, right_peak in enumerate(right_peaks):

                if index in matched_right:
                    continue

                error = abs(
                    left_peak.frequency
                    - right_peak.frequency
                )

                if error > tolerance_hz:
                    continue

                if (
                    best_error is None
                    or error < best_error
                ):
                    best_error = error
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

        return result