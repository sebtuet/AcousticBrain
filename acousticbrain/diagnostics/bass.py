from acousticbrain.analyzers import PeakDetector
from .model import Diagnostic


class BassDiagnostic:

    def analyze(self, measurement):

        detector = PeakDetector()

        peaks = detector.detect(measurement)

        bass_peaks = []

        for peak in peaks:

            if peak.kind == "peak" and peak.frequency < 300:

                bass_peaks.append(peak)

        if len(bass_peaks) == 0:

            return Diagnostic(

                title="Grave",

                message="Aucun pic important détecté.",

                confidence=90,

            )

        strongest = max(bass_peaks, key=lambda p: p.level)

        return Diagnostic(

            title="Grave",

            message=f"Pic détecté à {strongest.frequency:.1f} Hz ({strongest.level:.1f} dB)",

            confidence=90,

        )

        