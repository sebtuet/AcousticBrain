from acousticbrain.models import (
    ReflectionSurface,
    SBIRAnalysis,
    SBIRCandidate,
)


class SBIRAnalyzer:
    SPEED_OF_SOUND = 343.0

    def analyze(self, measurement, dips, room, speaker):
        candidates = []

        for surface, distance_m in self._surface_distances(room, speaker).items():
            theoretical_frequency = self.SPEED_OF_SOUND / (4 * distance_m)
            dip = self._nearest_dip(dips, theoretical_frequency)

            if dip is None:
                continue

            frequency_error_hz = abs(dip.frequency - theoretical_frequency)
            match_score = self._match_score(dip, theoretical_frequency)

            candidates.append(
                SBIRCandidate(
                    surface=surface,
                    measured_frequency=dip.frequency,
                    theoretical_frequency=theoretical_frequency,
                    distance_m=distance_m,
                    delay_ms=(2 * distance_m / self.SPEED_OF_SOUND) * 1000,
                    frequency_error_hz=frequency_error_hz,
                    match_score=match_score,
                    peak=dip,
                )
            )

        best_match = max(
            candidates,
            key=lambda candidate: candidate.match_score,
            default=None,
        )

        if best_match is None:
            return SBIRAnalysis(
                candidates=candidates,
                best_match=None,
                reflection_surface=None,
                reflection_distance_m=None,
                delay_ms=None,
                confidence=0.0,
                score=100.0,
            )

        return SBIRAnalysis(
            candidates=candidates,
            best_match=best_match,
            reflection_surface=best_match.surface,
            reflection_distance_m=best_match.distance_m,
            delay_ms=best_match.delay_ms,
            confidence=best_match.match_score,
            score=100.0 - best_match.match_score,
        )

    def _surface_distances(self, room, speaker):
        distances = {
            ReflectionSurface.FRONT_WALL: speaker.distance_front_wall,
            ReflectionSurface.REAR_WALL: room.length - speaker.distance_front_wall,
            ReflectionSurface.FLOOR: speaker.height,
            ReflectionSurface.CEILING: room.height - speaker.height,
        }
        return {
            surface: distance
            for surface, distance in distances.items()
            if distance > 0
        }

    @staticmethod
    def _nearest_dip(dips, frequency):
        if not dips:
            return None

        return min(dips, key=lambda dip: abs(dip.frequency - frequency))

    @staticmethod
    def _match_score(dip, theoretical_frequency):
        frequency_error_percent = (
            abs(dip.frequency - theoretical_frequency)
            / theoretical_frequency
        ) * 100
        prominence_penalty = max(0.0, 10.0 - dip.prominence) * 2
        return max(0.0, 100.0 - frequency_error_percent - prominence_penalty)
