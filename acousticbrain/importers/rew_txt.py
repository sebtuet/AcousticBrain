from pathlib import Path

from acousticbrain.models import Measurement


class REWTxtImporter:

    def load(self, filename: str) -> Measurement:

        filename = Path(filename)

        if not filename.exists():
            raise FileNotFoundError(filename)

        measurement_name = "Unknown"

        frequency = []
        spl = []
        phase = []

        reading_data = False

        with open(filename, "r", encoding="utf-8", errors="ignore") as f:

            for line in f:

                line = line.strip()

                # Nom de la mesure
                if line.startswith("* Measurement:"):
                    measurement_name = line.replace("* Measurement:", "").strip()

                # Début du tableau
                if line.startswith("* Freq(Hz)") or line.startswith("Freq(Hz)"):
                    reading_data = True
                    continue

                if not reading_data:
                    continue

                if not line:
                    continue

                values = line.split()

                if len(values) < 3:
                    continue

                try:

                    frequency.append(float(values[0]))
                    spl.append(float(values[1]))
                    phase.append(float(values[2]))

                except ValueError:
                    continue

        if (
            not frequency
            or not spl
            or not phase
            or len({len(frequency), len(spl), len(phase)}) != 1
        ):
            raise ValueError(
                f"Invalid REW frequency export '{filename}': the export does not "
                "contain the expected frequency, SPL, and phase data with matching "
                "non-empty lengths. Check that phase inclusion is enabled in the "
                "REW text export."
            )

        return Measurement(
            name=measurement_name,
            frequency=frequency,
            spl=spl,
            phase=phase,
        )
