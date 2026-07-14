from math import isfinite
from pathlib import Path

from acousticbrain.persistence import MeasurementRepository


class ExperimentProtocolDeclarationService:
    """Traduit une confirmation utilisateur explicite en manifests structurés."""

    MODAL_PROTOCOL_ID = "protocol.verify_modal_bass_persistence.v1"
    MODAL_HYPOTHESIS_CODE = "MODAL_BASS_PERSISTENCE"
    REQUIRED_FACT_CODES = ("bass_decay.maximum_decay_time_s",)
    SBIR_PROTOCOL_ID = "protocol.temporary_move_speaker.v1"
    SBIR_HYPOTHESIS_CODE = "SBIR_PLACEMENT_INTERACTION"
    SBIR_REQUIRED_FACT_CODES = (
        "sbir.target_null_frequency_hz",
        "sbir.target_null_prominence_db",
    )

    def __init__(self, repository=None):
        self.repository = repository or MeasurementRepository()

    def confirm_modal_multi_position(
        self,
        measurement_root,
        *,
        reference_experiment_id,
        reference_parent_experiment_id,
        listening_position_offsets_m,
    ):
        offsets = dict(listening_position_offsets_m)
        self._validate(
            reference_experiment_id,
            reference_parent_experiment_id,
            offsets,
        )
        root = Path(measurement_root)
        experiment_ids = tuple(offsets)
        directories = {item: root / item for item in experiment_ids}
        missing = tuple(
            item for item, directory in directories.items()
            if not directory.is_dir()
        )
        if missing:
            raise ValueError(
                "Unknown experiment directories: " + ", ".join(missing)
            )

        for experiment_id, offset in offsets.items():
            directory = directories[experiment_id]
            manifest = self.repository.load_manifest(directory) or {}
            reference = experiment_id == reference_experiment_id
            manifest["comparison"] = {
                "parent_experiment_ids": [
                    reference_parent_experiment_id
                    if reference
                    else reference_experiment_id
                ],
                "source_protocol_id": self.MODAL_PROTOCOL_ID,
                "source_hypothesis_code": self.MODAL_HYPOTHESIS_CODE,
                "declared_change_codes": (
                    ["LISTENING_POSITION_REFERENCE"]
                    if reference
                    else [
                        "CONTROLLED_LISTENING_POSITION_OFFSET",
                        "MULTIPLE_LISTENING_POSITIONS",
                    ]
                ),
                "required_fact_codes": list(self.REQUIRED_FACT_CODES),
                "parameters": {
                    "listening_position_offset_m": float(offset),
                    "position_role": self._position_role(offset),
                },
            }
            self.repository.save_manifest(directory, manifest)

        return experiment_ids

    def confirm_temporary_speaker_move(
        self,
        measurement_root,
        *,
        reference_experiment_id,
        moved_experiment_id,
        speaker_id,
        surface_id,
        geometry_candidate_id,
        displacement_m,
    ):
        values = (
            reference_experiment_id,
            moved_experiment_id,
            speaker_id,
            surface_id,
            geometry_candidate_id,
        )
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("SBIR protocol identifiers are required.")
        if (
            not isinstance(displacement_m, (int, float))
            or isinstance(displacement_m, bool)
            or not isfinite(displacement_m)
            or displacement_m == 0.0
        ):
            raise ValueError("Speaker displacement must be finite and non-zero.")
        root = Path(measurement_root)
        reference = root / reference_experiment_id
        moved = root / moved_experiment_id
        missing = tuple(
            experiment_id
            for experiment_id, directory in (
                (reference_experiment_id, reference),
                (moved_experiment_id, moved),
            )
            if not directory.is_dir()
        )
        if missing:
            raise ValueError(
                "Unknown experiment directories: " + ", ".join(missing)
            )
        manifest = self.repository.load_manifest(moved) or {}
        manifest["comparison"] = {
            "parent_experiment_ids": [reference_experiment_id],
            "source_protocol_id": self.SBIR_PROTOCOL_ID,
            "source_hypothesis_code": self.SBIR_HYPOTHESIS_CODE,
            "declared_change_codes": [
                "CONTROLLED_SPEAKER_POSITION",
                "TEMPORARY_SPEAKER_MOVE",
            ],
            "required_fact_codes": list(self.SBIR_REQUIRED_FACT_CODES),
            "parameters": {
                "speaker_id": speaker_id,
                "surface_id": surface_id,
                "geometry_candidate_id": geometry_candidate_id,
                "speaker_displacement_m": float(displacement_m),
                "controlled_variable_codes": [
                    "MICROPHONE_POSITION",
                    "LOUDSPEAKER_ORIENTATION",
                    "OTHER_LOUDSPEAKER_POSITIONS",
                    "SIGNAL_CHAIN_ASSIGNMENT",
                    "MEASUREMENT_LEVEL",
                    "ROOM_CONFIGURATION",
                ],
                "changed_variable_codes": ["LOUDSPEAKER_POSITION"],
                "expected_observation_codes": [
                    "SBIR_MOVES_WITH_SPEAKER",
                    "SBIR_REMAINS_FIXED",
                ],
            },
        }
        self.repository.save_manifest(moved, manifest)
        return moved_experiment_id

    @staticmethod
    def _validate(reference_id, parent_id, offsets):
        if not isinstance(reference_id, str) or not reference_id.strip():
            raise ValueError("Reference experiment id is required.")
        if not isinstance(parent_id, str) or not parent_id.strip():
            raise ValueError("Reference parent experiment id is required.")
        if reference_id not in offsets:
            raise ValueError("Reference experiment must belong to the campaign.")
        if len(offsets) < 2:
            raise ValueError("A multi-position campaign requires another position.")
        if offsets[reference_id] != 0.0:
            raise ValueError("Reference listening-position offset must be zero.")
        if any(
            not isinstance(experiment_id, str)
            or not experiment_id.strip()
            or not isinstance(offset, (int, float))
            or isinstance(offset, bool)
            or not isfinite(offset)
            for experiment_id, offset in offsets.items()
        ):
            raise ValueError("Listening-position declarations are invalid.")

    @staticmethod
    def _position_role(offset):
        if offset == 0.0:
            return "REFERENCE"
        return "FORWARD" if offset > 0.0 else "BACKWARD"
