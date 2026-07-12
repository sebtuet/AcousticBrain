from dataclasses import dataclass

from .listening_position import ListeningPosition
from .room_dimensions import RoomDimensions
from .room_opening import RoomOpening
from .speaker_position import SpeakerPosition
from .surface_material_description import SurfaceMaterialDescription
from .surface_covering_zone import SurfaceCoveringZone
from .room_furniture_description import RoomFurnitureDescription
from .acoustic_treatment_description import AcousticTreatmentDescription


@dataclass(frozen=True)
class RoomDescription:
    """Description utilisateur d'une salle, indépendante des analyses."""

    name: str
    dimensions: RoomDimensions
    speakers: tuple[SpeakerPosition, ...] = ()
    listening_positions: tuple[ListeningPosition, ...] = ()
    openings: tuple[RoomOpening, ...] = ()
    surface_materials: tuple[SurfaceMaterialDescription, ...] = ()
    covering_zones: tuple[SurfaceCoveringZone, ...] = ()
    furniture: tuple[RoomFurnitureDescription, ...] = ()
    acoustic_treatments: tuple[AcousticTreatmentDescription, ...] = ()

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Room-description name is required.")
        if not isinstance(self.dimensions, RoomDimensions):
            raise ValueError("Room description requires RoomDimensions.")
        for name, collection in (
            ("speakers", self.speakers),
            ("listening_positions", self.listening_positions),
            ("openings", self.openings),
            ("surface_materials", self.surface_materials),
            ("covering_zones", self.covering_zones),
            ("furniture", self.furniture),
            ("acoustic_treatments", self.acoustic_treatments),
        ):
            if not isinstance(collection, tuple):
                raise ValueError(f"Room-description {name} must be a tuple.")
        for name, collection, expected_type in (
            ("speakers", self.speakers, SpeakerPosition),
            ("listening_positions", self.listening_positions, ListeningPosition),
            ("openings", self.openings, RoomOpening),
            ("surface_materials", self.surface_materials, SurfaceMaterialDescription),
            ("covering_zones", self.covering_zones, SurfaceCoveringZone),
            ("furniture", self.furniture, RoomFurnitureDescription),
            ("acoustic_treatments", self.acoustic_treatments, AcousticTreatmentDescription),
        ):
            if any(not isinstance(item, expected_type) for item in collection):
                raise ValueError(f"Room-description {name} contain an invalid type.")
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
        self._require_unique(
            (material.surface for material in self.surface_materials),
            "surface-material",
        )
        self._require_unique(
            (zone.zone_id for zone in self.covering_zones),
            "covering-zone",
        )
        self._require_unique(
            (item.furniture_id for item in self.furniture),
            "furniture",
        )
        self._require_unique(
            (item.treatment_id for item in self.acoustic_treatments),
            "acoustic-treatment",
        )

    @staticmethod
    def _require_unique(values, kind):
        identifiers = tuple(values)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                f"Room description contains a duplicate {kind} identifier."
            )
