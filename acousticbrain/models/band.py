from dataclasses import dataclass, field

from .peak import Peak


@dataclass
class FrequencyBand:

    name: str

    minimum: float

    maximum: float

    peaks: list[Peak] = field(default_factory=list)

    def contains(self, frequency: float):

        return self.minimum <= frequency < self.maximum

        