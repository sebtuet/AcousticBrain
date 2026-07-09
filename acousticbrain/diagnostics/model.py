from dataclasses import dataclass


@dataclass
class Diagnostic:

    title: str

    message: str

    confidence: int

    