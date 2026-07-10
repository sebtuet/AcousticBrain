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

        self.measurements[name] = measurement

    def get_measurement(
        self,
        name: str,
    ):

        return self.measurements.get(name)

    def add_speaker(
        self,
        speaker: Speaker,
    ):

        self.speakers[speaker.name] = speaker

    def get_speaker(
        self,
        name: str,
    ):

        return self.speakers.get(name)

    def list_measurements(self):

        return list(self.measurements.keys())