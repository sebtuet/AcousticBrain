from dataclasses import dataclass

from .listening_position import ListeningPosition
from .room_dimensions import RoomDimensions
from .room_opening import RoomOpening
from .speaker_position import SpeakerPosition


@dataclass(frozen=True)
class RoomDescription:
    """Description utilisateur d'une salle, indépendante des analyses."""

    name: str
    dimensions: RoomDimensions
    speakers: tuple[SpeakerPosition, ...] = ()
    listening_positions: tuple[ListeningPosition, ...] = ()
    openings: tuple[RoomOpening, ...] = ()

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Room-description name is required.")
        if not isinstance(self.dimensions, RoomDimensions):
            raise ValueError("Room description requires RoomDimensions.")
        for name, collection in (
            ("speakers", self.speakers),
            ("listening_positions", self.listening_positions),
            ("openings", self.openings),
        ):
            if not isinstance(collection, tuple):
                raise ValueError(f"Room-description {name} must be a tuple.")
        self._require_unique(
            (speaker.speaker_id for speaker in self.speakers),
            "speaker",
        )
        self._require_unique(
            (position.position_id for position in self.listening_positions),
            "listening-position",
        )
        self._require_unique(
            (opening.opening_id for opening in self.openings),
            "opening",
        )

    @staticmethod
    def _require_unique(values, kind):
        identifiers = tuple(values)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                f"Room description contains a duplicate {kind} identifier."
            )
