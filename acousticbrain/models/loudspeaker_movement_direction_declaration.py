from dataclasses import dataclass

from .loudspeaker_positioning_experiment import LoudspeakerMovementDirection


class MovementDirectionDeclarationResolutionError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class LoudspeakerMovementDirectionDeclaration:
    declaration_id: str
    target_geometry_candidate_id: str
    direction: LoudspeakerMovementDirection
    provenance_code: str
    source_id: str

    def __post_init__(self):
        for value in (
            self.declaration_id,
            self.target_geometry_candidate_id,
            self.source_id,
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Movement-direction declaration identifiers are required.")
        if not isinstance(self.direction, LoudspeakerMovementDirection):
            raise ValueError("Movement-direction declaration direction is invalid.")
        if self.provenance_code != "USER_DECLARATION":
            raise ValueError(
                "Movement-direction declaration provenance must be USER_DECLARATION."
            )
