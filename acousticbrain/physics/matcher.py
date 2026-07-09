from acousticbrain.models import ModeMatch


class ModeMatcher:

    def match(
        self,
        peaks,
        modes,
        tolerance=2.0,
    ):

        matches = []

        for peak in peaks:

            best = None

            best_error = None

            for mode in modes:

                error = abs(
                    peak.frequency - mode.frequency
                )

                if error > tolerance:
                    continue

                if best_error is None or error < best_error:

                    best = mode
                    best_error = error

            if best is None:
                continue

            confidence = max(
                0.0,
                100.0 * (1 - best_error / tolerance)
            )

            matches.append(

                ModeMatch(

                    peak=peak,

                    mode=best,

                    error_hz=best_error,

                    confidence=confidence,

                )

            )

        return matches