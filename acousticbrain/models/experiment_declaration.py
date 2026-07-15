from dataclasses import dataclass
from enum import Enum


class ExperimentKind(Enum):
    CONTROLLED_INTERVENTION = "CONTROLLED_INTERVENTION"
    MEASUREMENT_REPEAT = "MEASUREMENT_REPEAT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExperimentDeclaration:
    schema_version: int
    experiment_kind: ExperimentKind
    reference_experiment_code: str | None
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    user_note: str | None
    field_provenance: tuple[tuple[str, str], ...]

    CURRENT_SCHEMA_VERSION = 1
    ACQUISITION_VARIABLE = "MEASUREMENT_ACQUISITION"

    @classmethod
    def unknown(cls):
        return cls(
            schema_version=cls.CURRENT_SCHEMA_VERSION,
            experiment_kind=ExperimentKind.UNKNOWN,
            reference_experiment_code=None,
            modified_variables=(),
            controlled_variables=(),
            user_note=None,
            field_provenance=(("experiment_kind", "DEFAULT_ABSENT_DECLARATION"),),
        )

    def __post_init__(self):
        if self.schema_version != self.CURRENT_SCHEMA_VERSION:
            raise ValueError("Unsupported experiment declaration schema version.")
        if not all(isinstance(value, tuple) for value in (
            self.modified_variables,
            self.controlled_variables,
            self.field_provenance,
        )):
            raise ValueError("Experiment declaration collections must be tuples.")
        if set(self.modified_variables) & set(self.controlled_variables):
            raise ValueError("Modified and controlled variables must be disjoint.")
        if self.experiment_kind is ExperimentKind.UNKNOWN and any((
            self.reference_experiment_code,
            self.modified_variables,
            self.controlled_variables,
        )):
            raise ValueError("UNKNOWN experiments cannot declare experimental variables.")
        if self.experiment_kind is not ExperimentKind.UNKNOWN:
            if not self.reference_experiment_code:
                raise ValueError("A declared experiment requires a reference experiment.")
        if self.experiment_kind is ExperimentKind.CONTROLLED_INTERVENTION:
            if not self.modified_variables:
                raise ValueError("A controlled intervention requires a modified variable.")
        if self.experiment_kind is ExperimentKind.MEASUREMENT_REPEAT:
            if self.modified_variables != (self.ACQUISITION_VARIABLE,):
                raise ValueError(
                    "A measurement repeat may only repeat MEASUREMENT_ACQUISITION."
                )
        required_fields = {
            "experiment_kind",
            "reference_experiment_code",
            "modified_variables",
            "controlled_variables",
            "user_note",
        }
        provenance = dict(self.field_provenance)
        if self.experiment_kind is not ExperimentKind.UNKNOWN and (
            set(provenance) != required_fields
            or any(not value for value in provenance.values())
        ):
            raise ValueError("Experiment declaration provenance must cover every field.")
