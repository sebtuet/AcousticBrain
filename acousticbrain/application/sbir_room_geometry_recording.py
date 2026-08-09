from dataclasses import dataclass

from acousticbrain.models import SBIRRoomGeometryPreview
from acousticbrain.persistence import (
    MeasurementRepository,
    SBIRRoomGeometryDeclarationInputJsonLoader,
)

from .sbir_room_geometry_preview import SBIRRoomGeometryPreviewService


@dataclass(frozen=True)
class SBIRRoomGeometryRecordingResult:
    target_experiment_id: str
    room_description_fingerprint: str
    persisted: bool


class SBIRRoomGeometryRecordingService:
    FIELD = "room_description_contract"

    def __init__(self, repository=None, preview_service=None, input_codec=None):
        self.repository = repository or MeasurementRepository()
        self.preview_service = preview_service or SBIRRoomGeometryPreviewService(
            self.repository
        )
        self.input_codec = (
            input_codec or SBIRRoomGeometryDeclarationInputJsonLoader()
        )

    def record(self, preview):
        if not isinstance(preview, SBIRRoomGeometryPreview):
            raise TypeError("SBIRRoomGeometryPreview is required.")
        refreshed = self.preview_service.preview(preview.resolution)
        if refreshed != preview:
            raise ValueError("SBIR_ROOM_GEOMETRY_PREVIEW_STALE.")

        baseline = preview.resolution.baseline_experiment
        manifest = self.repository.load_manifest(baseline.directory)
        if manifest is None:
            raise ValueError(
                "SBIR_ROOM_GEOMETRY_BASELINE_MANIFEST_UNAVAILABLE: baseline."
            )
        payload = self._payload(preview)
        existing = manifest.get(self.FIELD)
        if existing is not None and existing != payload:
            paths = ",".join(self._differences(existing, payload))
            raise ValueError(
                "SBIR_ROOM_GEOMETRY_DECLARATION_DIVERGENT: " + paths + "."
            )
        persisted = False
        if existing is None:
            manifest[self.FIELD] = payload
            persisted = self.repository.save_manifest(
                baseline.directory, manifest
            )
        return SBIRRoomGeometryRecordingResult(
            target_experiment_id=baseline.experiment_id,
            room_description_fingerprint=payload[
                "room_description_fingerprint"
            ],
            persisted=persisted,
        )

    def _payload(self, preview):
        value = preview.resolution.declaration_input
        return self.input_codec.contract_payload(value, preview.decisions)

    @classmethod
    def _differences(cls, existing, requested, prefix=""):
        if not isinstance(existing, dict) or not isinstance(requested, dict):
            return (prefix or cls.FIELD,)
        paths = []
        for key in sorted(set(existing) | set(requested)):
            path = f"{prefix}.{key}" if prefix else key
            if key not in existing or key not in requested:
                paths.append(path)
            elif existing[key] != requested[key]:
                if isinstance(existing[key], dict) and isinstance(requested[key], dict):
                    paths.extend(cls._differences(existing[key], requested[key], path))
                else:
                    paths.append(path)
        return tuple(paths)
