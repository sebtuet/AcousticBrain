from dataclasses import dataclass
from typing import List


@dataclass
class Knowledge:

    title: str

    category: str

    summary: str

    symptoms: List[str]

    causes: List[str]

    diagnostics: List[str]

    solutions: List[str]

    references: List[str]
    