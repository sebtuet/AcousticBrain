from dataclasses import dataclass


@dataclass
class Peak:
    frequency: float
    spl: float
    index: int
    prominence: float
    