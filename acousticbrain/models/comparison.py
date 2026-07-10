from dataclasses import dataclass


@dataclass
class FrequencyDifference:

    frequency: float

    spl_a: float

    spl_b: float

    difference: float