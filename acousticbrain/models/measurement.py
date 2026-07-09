from dataclasses import dataclass, field
from typing import List


@dataclass
class Measurement:
    name: str

    frequency: List[float] = field(default_factory=list)

    spl: List[float] = field(default_factory=list)

    phase: List[float] = field(default_factory=list)
    