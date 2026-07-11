from pathlib import Path

from acousticbrain.models import ImpulseChannel, ImpulseResponse


class REWImpulseImporter:
    """Importe une réponse impulsionnelle REW sans transformer ses valeurs."""

    METADATA_LABELS = {
        "peak value before normalisation": ("peak_value", float),
        "peak index": ("peak_index", int),
        "response length": ("response_length", int),
        "sample interval (seconds)": ("sample_interval_s", float),
        "start time (seconds)": ("start_time_s", float),
    }

    def load(
        self,
        filename: str | Path,
        *,
        channel: ImpulseChannel,
    ) -> ImpulseResponse:
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(path)

        metadata: dict[str, float | int] = {}
        samples: list[float] = []
        source_id = None
        reading_data = False

        with path.open("r", encoding="utf-8", errors="strict") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                line = raw_line.strip()
                if not line:
                    continue

                if line.startswith("* Measurement:"):
                    source_id = line.removeprefix("* Measurement:").strip() or None
                    continue

                if line == "* Data start":
                    reading_data = True
                    continue

                if reading_data:
                    samples.append(self._sample(line, line_number))
                    continue

                self._read_metadata(line, metadata, line_number)

        self._validate(metadata, samples, reading_data)
        sample_interval_s = float(metadata["sample_interval_s"])

        return ImpulseResponse(
            channel=channel,
            sample_rate_hz=1.0 / sample_interval_s,
            samples=samples,
            time_offset_seconds=float(metadata["start_time_s"]),
            source_id=source_id,
            peak_value=float(metadata["peak_value"]),
            peak_index=int(metadata["peak_index"]),
            response_length=int(metadata["response_length"]),
            sample_interval_s=sample_interval_s,
            start_time_s=float(metadata["start_time_s"]),
        )

    @classmethod
    def _read_metadata(cls, line, metadata, line_number):
        if "//" not in line:
            return

        raw_value, raw_label = (part.strip() for part in line.split("//", 1))
        field = cls.METADATA_LABELS.get(raw_label.lower())
        if field is None:
            return

        field_name, converter = field
        if field_name in metadata:
            raise ValueError(f"Duplicate REW impulse metadata: {field_name}.")
        try:
            metadata[field_name] = converter(raw_value)
        except ValueError as error:
            raise ValueError(
                f"Invalid REW impulse metadata on line {line_number}: {line}"
            ) from error

    @staticmethod
    def _sample(line, line_number):
        try:
            return float(line)
        except ValueError as error:
            raise ValueError(
                f"Invalid REW impulse sample on line {line_number}: {line}"
            ) from error

    @classmethod
    def _validate(cls, metadata, samples, reading_data):
        if not reading_data:
            raise ValueError("Missing REW impulse data marker.")

        missing = {
            field_name
            for field_name, _ in cls.METADATA_LABELS.values()
            if field_name not in metadata
        }
        if missing:
            raise ValueError(
                "Missing REW impulse metadata: " + ", ".join(sorted(missing))
            )

        response_length = int(metadata["response_length"])
        peak_index = int(metadata["peak_index"])
        sample_interval_s = float(metadata["sample_interval_s"])

        if response_length < 1:
            raise ValueError("REW impulse response length must be positive.")
        if len(samples) != response_length:
            raise ValueError(
                "REW impulse sample count does not match response length: "
                f"expected {response_length}, got {len(samples)}."
            )
        if not 0 <= peak_index < response_length:
            raise ValueError("REW impulse peak index is outside the response.")
        if sample_interval_s <= 0:
            raise ValueError("REW impulse sample interval must be positive.")
