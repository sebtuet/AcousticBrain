from dataclasses import dataclass, field

from acousticbrain.models import (
    Measurement,
    Room,
    Speaker,
)


@dataclass
class Project:

    name: str

    room: Room

    measurements: dict[str, Measurement] = field(default_factory=dict)

    speakers: dict[str, Speaker] = field(default_factory=dict)

    def add_measurement(
        self,
        name: str,
        measurement: Measurement,
    ):

        measurement.name = name

        self.measurements[name] = measurement

    def get_measurement(
        self,
        name: str,
    ) -> Measurement | None:

        return self.measurements.get(name)

    def has_measurement(
        self,
        name: str,
    ) -> bool:

        return name in self.measurements

    def list_measurements(self) -> list[str]:

        return sorted(self.measurements.keys())

    def add_speaker(
        self,
        speaker: Speaker,
    ):

        self.speakers[speaker.name] = speaker

    def get_speaker(
        self,
        name: str,
    ) -> Speaker | None:

        return self.speakers.get(name)
        