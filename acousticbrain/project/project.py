from dataclasses import dataclass, field

from acousticbrain.models import Measurement


@dataclass
class Project:

    name: str

    measurements: dict[str, Measurement] = field(default_factory=dict)

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

    def list_measurements(self):

        return list(self.measurements.keys())
        