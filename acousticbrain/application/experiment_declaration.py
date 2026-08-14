from pathlib import Path

from acousticbrain.models import ExperimentDeclaration, ExperimentKind
from acousticbrain.persistence import MeasurementRepository


class ExperimentDeclarationService:
    """Persiste une déclaration utilisateur sans modifier les mesures."""

    REPEAT_CONTROLLED_VARIABLES = (
        "LISTENING_POSITION",
        "LOUDSPEAKER_POSITION",
        "MEASUREMENT_LEVEL",
        "MICROPHONE_POSITION",
        "REW_MEASUREMENT_PARAMETERS",
        "ROOM_CONFIGURATION",
    )
    DECLARATION_FIELDS = (
        "experiment_kind",
        "reference_experiment_code",
        "modified_variables",
        "controlled_variables",
        "user_note",
    )

    def __init__(self, repository=None):
        self.repository = repository or MeasurementRepository()

    def declare(
        self,
        measurement_root,
        *,
        experiment_code,
        experiment_kind,
        reference_experiment_code=None,
        modified_variables=(),
        controlled_variables=(),
        user_note=None,
        provenance_source="USER_CLI",
    ):
        kind = (
            experiment_kind
            if isinstance(experiment_kind, ExperimentKind)
            else ExperimentKind(experiment_kind)
        )
        modified_variables = tuple(modified_variables)
        controlled_variables = tuple(controlled_variables)
        root = Path(measurement_root)
        directory = root / experiment_code
        if not directory.is_dir():
            raise ValueError(f"Unknown experiment directory: {experiment_code}")
        if kind is not ExperimentKind.UNKNOWN:
            reference = root / str(reference_experiment_code or "")
            if not reference.is_dir():
                raise ValueError(
                    f"Unknown reference experiment: {reference_experiment_code}"
                )
        if kind is ExperimentKind.MEASUREMENT_REPEAT:
            if not modified_variables:
                modified_variables = (ExperimentDeclaration.ACQUISITION_VARIABLE,)
            if not controlled_variables:
                controlled_variables = self.REPEAT_CONTROLLED_VARIABLES
        declaration = ExperimentDeclaration(
            schema_version=ExperimentDeclaration.CURRENT_SCHEMA_VERSION,
            experiment_kind=kind,
            reference_experiment_code=self._optional_string(
                reference_experiment_code
            ),
            modified_variables=self._codes(modified_variables),
            controlled_variables=self._codes(controlled_variables),
            user_note=self._optional_string(user_note),
            field_provenance=tuple(
                (field, provenance_source) for field in self.DECLARATION_FIELDS
            ) if kind is not ExperimentKind.UNKNOWN else (
                ("experiment_kind", provenance_source),
            ),
        )
        manifest = self.repository.load_manifest(directory) or {}
        manifest["experiment_declaration"] = {
            "schema_version": declaration.schema_version,
            "experiment_kind": declaration.experiment_kind.value,
            "reference_experiment_code": declaration.reference_experiment_code,
            "modified_variables": list(declaration.modified_variables),
            "controlled_variables": list(declaration.controlled_variables),
            "user_note": declaration.user_note,
            "field_provenance": dict(declaration.field_provenance),
        }
        if declaration.reference_experiment_code:
            comparison = manifest.get("comparison", {})
            if not isinstance(comparison, dict):
                comparison = {}
            comparison["parent_experiment_ids"] = [
                declaration.reference_experiment_code
            ]
            manifest["comparison"] = comparison
        self.repository.save_manifest(directory, manifest)
        return declaration

    @staticmethod
    def _optional_string(value):
        return value.strip() if isinstance(value, str) and value.strip() else None

    @classmethod
    def _codes(cls, values):
        return tuple(sorted(set(
            item for raw in values
            if (item := cls._optional_string(raw)) is not None
        )))
