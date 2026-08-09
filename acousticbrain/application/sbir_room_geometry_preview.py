from acousticbrain.models import (
    SBIRRoomGeometryPreview,
    SBIRRoomGeometryResolution,
)
from acousticbrain.persistence import MeasurementRepository


class SBIRRoomGeometryPreviewService:
    """Compare declared geometry with the raw baseline manifest without writing."""

    LEGACY_SECTIONS = (
        "coordinate_system",
        "room",
        "loudspeakers",
        "listening_position",
    )

    def __init__(self, repository=None):
        self.repository = repository or MeasurementRepository()

    def preview(self, resolution):
        if not isinstance(resolution, SBIRRoomGeometryResolution):
            raise TypeError(
                "SBIR room-geometry preview requires an exact resolution."
            )
        baseline = resolution.baseline_experiment
        manifest = self.repository.load_manifest(baseline.directory)
        if manifest is None:
            raise ValueError(
                "SBIR_ROOM_GEOMETRY_BASELINE_MANIFEST_UNAVAILABLE: "
                f"{baseline.experiment_id}."
            )

        present = tuple(
            section for section in self.LEGACY_SECTIONS if section in manifest
        )
        if not present:
            return self._result(resolution, legacy_geometry_present=False)
        if len(present) != len(self.LEGACY_SECTIONS):
            missing = ",".join(
                section
                for section in self.LEGACY_SECTIONS
                if section not in manifest
            )
            raise ValueError(
                "SBIR_ROOM_GEOMETRY_LEGACY_GEOMETRY_INCOMPLETE: "
                f"missing={missing}."
            )

        expected = self._expected_values(resolution)
        incompatible = tuple(
            path
            for path, expected_value in expected
            if self._manifest_value(manifest, path) != expected_value
        )
        if incompatible:
            raise ValueError(
                "SBIR_ROOM_GEOMETRY_LEGACY_GEOMETRY_CONFLICT: "
                + ",".join(incompatible)
                + "."
            )
        return self._result(resolution, legacy_geometry_present=True)

    @staticmethod
    def _result(resolution, *, legacy_geometry_present):
        return SBIRRoomGeometryPreview(
            resolution=resolution,
            legacy_geometry_present=legacy_geometry_present,
            decisions=SBIRRoomGeometryPreview.EXPECTED_DECISIONS,
        )

    @staticmethod
    def _expected_values(resolution):
        description = resolution.declaration_input.room_description
        speakers = {item.speaker_id: item for item in description.speakers}
        positions = {
            item.position_id: item for item in description.listening_positions
        }
        dimensions = description.dimensions
        left = speakers["LEFT"]
        right = speakers["RIGHT"]
        listening = positions["LISTENING_POSITION"]
        return (
            ("room.dimensions.length", dimensions.length_m),
            ("room.dimensions.width", dimensions.width_m),
            ("room.dimensions.height", dimensions.height_m),
            ("loudspeakers.left.position.x", left.x_m),
            ("loudspeakers.left.position.y", left.y_m),
            ("loudspeakers.left.position.z", left.z_m),
            ("loudspeakers.right.position.x", right.x_m),
            ("loudspeakers.right.position.y", right.y_m),
            ("loudspeakers.right.position.z", right.z_m),
            ("listening_position.position.x", listening.x_m),
            ("listening_position.position.y", listening.y_m),
            ("listening_position.position.z", listening.z_m),
        )

    @staticmethod
    def _manifest_value(manifest, path):
        value = manifest
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                return _MISSING
            value = value[part]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            return _INVALID
        return value


_MISSING = object()
_INVALID = object()
