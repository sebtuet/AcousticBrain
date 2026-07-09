from acousticbrain.importers import REWTxtImporter
from acousticbrain.analyzers.peak_detector import PeakDetector

measurement = REWTxtImporter().load("LR.txt")

detector = PeakDetector()

peaks = detector.detect(
    measurement,
    prominence=3,
    distance=10,
)

print()
print(f"{len(peaks)} pics détectés")
print()

for peak in peaks:

    print(
        f"{peak.frequency:8.2f} Hz"
        f"   {peak.spl:6.2f} dB"
        f"   prominence={peak.prominence:.2f}"
    )

    