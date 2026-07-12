from dataclasses import dataclass

from acousticbrain.models import (
    RoomDescription,
    RoomDescriptionPersistenceError,
    RoomDescriptionPersistenceErrorCode,
)
from acousticbrain.persistence import RoomDescriptionJsonCodec


@dataclass(frozen=True)
class SpeakerPositionFormRow:
    speaker_id: str = ""
    x_m: str = ""
    y_m: str = ""
    z_m: str = ""


@dataclass(frozen=True)
class ListeningPositionFormRow:
    position_id: str = ""
    x_m: str = ""
    y_m: str = ""
    z_m: str = ""


@dataclass(frozen=True)
class RoomOpeningFormRow:
    opening_id: str = ""
    surface: str = "FRONT_WALL"
    horizontal_offset_m: str = ""
    vertical_offset_m: str = ""
    width_m: str = ""
    height_m: str = ""


@dataclass(frozen=True)
class RoomDescriptionFormState:
    name: str = ""
    length_m: str = ""
    width_m: str = ""
    height_m: str = ""
    speakers: tuple[SpeakerPositionFormRow, ...] = ()
    listening_positions: tuple[ListeningPositionFormRow, ...] = ()
    openings: tuple[RoomOpeningFormRow, ...] = ()


@dataclass(frozen=True)
class RoomDescriptionFormResult:
    description: RoomDescription | None = None
    errors: tuple[RoomDescriptionPersistenceError, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.description is not None and not self.errors


@dataclass(frozen=True)
class RoomDescriptionSerializationResult:
    payload: str | None = None
    errors: tuple[RoomDescriptionPersistenceError, ...] = ()

    @property
    def is_success(self) -> bool:
        return self.payload is not None and not self.errors


@dataclass(frozen=True)
class RoomDescriptionLoadFormResult:
    state: RoomDescriptionFormState | None = None
    errors: tuple[RoomDescriptionPersistenceError, ...] = ()

    @property
    def is_success(self) -> bool:
        return self.state is not None and not self.errors


class RoomDescriptionEditorAdapter:
    """Adapte un état de formulaire sans contourner le codec du domaine."""

    def __init__(self, codec=None):
        self.codec = codec or RoomDescriptionJsonCodec()

    def validate(
        self,
        state: RoomDescriptionFormState,
    ) -> RoomDescriptionFormResult:
        payload, errors = self._payload(state)
        if errors:
            return RoomDescriptionFormResult(errors=errors)
        loaded = self.codec.from_dict(payload)
        return RoomDescriptionFormResult(
            description=loaded.description,
            errors=loaded.errors,
        )

    def serialize(
        self,
        state: RoomDescriptionFormState,
        *,
        indent=2,
    ) -> RoomDescriptionSerializationResult:
        validated = self.validate(state)
        if not validated.is_valid:
            return RoomDescriptionSerializationResult(errors=validated.errors)
        return RoomDescriptionSerializationResult(
            payload=self.codec.dumps(validated.description, indent=indent)
        )

    def load(self, payload: str) -> RoomDescriptionLoadFormResult:
        loaded = self.codec.loads(payload)
        if not loaded.is_success:
            return RoomDescriptionLoadFormResult(errors=loaded.errors)
        return RoomDescriptionLoadFormResult(
            state=self.from_description(loaded.description)
        )

    @staticmethod
    def from_description(description: RoomDescription):
        return RoomDescriptionFormState(
            name=description.name,
            length_m=str(description.dimensions.length_m),
            width_m=str(description.dimensions.width_m),
            height_m=str(description.dimensions.height_m),
            speakers=tuple(
                SpeakerPositionFormRow(
                    item.speaker_id,
                    str(item.x_m),
                    str(item.y_m),
                    str(item.z_m),
                )
                for item in description.speakers
            ),
            listening_positions=tuple(
                ListeningPositionFormRow(
                    item.position_id,
                    str(item.x_m),
                    str(item.y_m),
                    str(item.z_m),
                )
                for item in description.listening_positions
            ),
            openings=tuple(
                RoomOpeningFormRow(
                    item.opening_id,
                    item.surface.value,
                    str(item.horizontal_offset_m),
                    str(item.vertical_offset_m),
                    str(item.width_m),
                    str(item.height_m),
                )
                for item in description.openings
            ),
        )

    def _payload(self, state):
        if not isinstance(state, RoomDescriptionFormState):
            raise TypeError("Editor adapter requires RoomDescriptionFormState.")
        errors = []

        def number(value, path):
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                errors.append(self._invalid(path))
                return None
            return parsed

        room = {
            "name": state.name,
            "dimensions": {
                "length_m": number(
                    state.length_m,
                    ("room_description", "dimensions", "length_m"),
                ),
                "width_m": number(
                    state.width_m,
                    ("room_description", "dimensions", "width_m"),
                ),
                "height_m": number(
                    state.height_m,
                    ("room_description", "dimensions", "height_m"),
                ),
            },
            "speakers": [
                {
                    "speaker_id": item.speaker_id,
                    "x_m": number(
                        item.x_m,
                        ("room_description", "speakers", index, "x_m"),
                    ),
                    "y_m": number(
                        item.y_m,
                        ("room_description", "speakers", index, "y_m"),
                    ),
                    "z_m": number(
                        item.z_m,
                        ("room_description", "speakers", index, "z_m"),
                    ),
                }
                for index, item in enumerate(state.speakers)
            ],
            "listening_positions": [
                {
                    "position_id": item.position_id,
                    "x_m": number(
                        item.x_m,
                        (
                            "room_description",
                            "listening_positions",
                            index,
                            "x_m",
                        ),
                    ),
                    "y_m": number(
                        item.y_m,
                        (
                            "room_description",
                            "listening_positions",
                            index,
                            "y_m",
                        ),
                    ),
                    "z_m": number(
                        item.z_m,
                        (
                            "room_description",
                            "listening_positions",
                            index,
                            "z_m",
                        ),
                    ),
                }
                for index, item in enumerate(state.listening_positions)
            ],
            "openings": [
                {
                    "opening_id": item.opening_id,
                    "surface": item.surface,
                    "horizontal_offset_m": number(
                        item.horizontal_offset_m,
                        (
                            "room_description",
                            "openings",
                            index,
                            "horizontal_offset_m",
                        ),
                    ),
                    "vertical_offset_m": number(
                        item.vertical_offset_m,
                        (
                            "room_description",
                            "openings",
                            index,
                            "vertical_offset_m",
                        ),
                    ),
                    "width_m": number(
                        item.width_m,
                        ("room_description", "openings", index, "width_m"),
                    ),
                    "height_m": number(
                        item.height_m,
                        ("room_description", "openings", index, "height_m"),
                    ),
                }
                for index, item in enumerate(state.openings)
            ],
        }
        return (
            {
                "schema_version": self.codec.SCHEMA_VERSION,
                "room_description": room,
            },
            tuple(errors),
        )

    @staticmethod
    def _invalid(path):
        return RoomDescriptionPersistenceError(
            code=RoomDescriptionPersistenceErrorCode.INVALID_VALUE,
            path=path,
        )
