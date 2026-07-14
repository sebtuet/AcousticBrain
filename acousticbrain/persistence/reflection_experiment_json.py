import json
from pathlib import Path

from acousticbrain.models import (
    ControlledReflectionExperimentDeclaration,
    ControlledReflectionExperimentDeclarationRegistry,
    ReflectionDeclarationFieldProvenance,
    ReflectionDeclarationProvenanceSource,
    ReflectionExperimentConditionDeclaration,
    ReflectionExperimentDeclarationStatus,
    ReflectionExperimentMeasurementReference,
)


class ControlledReflectionExperimentJsonCodec:
    SCHEMA_VERSION = 1

    def dumps(self, registry, *, indent=2):
        return json.dumps(
            self.to_dict(registry),
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    def loads(self, payload):
        try:
            value = json.loads(payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError("Invalid reflection experiment declaration JSON.") from error
        return self.from_dict(value)

    def to_dict(self, registry):
        if not isinstance(registry, ControlledReflectionExperimentDeclarationRegistry):
            raise TypeError("Reflection declaration registry is required.")
        return {
            "schema_version": self.SCHEMA_VERSION,
            "declarations": [
                self._declaration(item)
                for item in sorted(
                    registry.declarations,
                    key=lambda item: item.declaration_id,
                )
            ],
        }

    def from_dict(self, value):
        if not isinstance(value, dict):
            raise ValueError("Reflection declaration payload must be an object.")
        if value.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Unsupported reflection declaration schema version.")
        declarations = value.get("declarations")
        if not isinstance(declarations, list):
            raise ValueError("Reflection declarations must be a list.")
        return ControlledReflectionExperimentDeclarationRegistry(
            declarations=tuple(
                sorted(
                    (self._decode_declaration(item) for item in declarations),
                    key=lambda item: item.declaration_id,
                )
            ),
            schema_version=self.SCHEMA_VERSION,
        )

    @classmethod
    def _declaration(cls, item):
        return {
            "declaration_id": item.declaration_id,
            "proposal_id": item.proposal_id,
            "status": item.status.value,
            "reference_condition": cls._condition(item.reference_condition),
            "intervention_condition": cls._condition(
                item.intervention_condition
            ),
            "status_reason_code": item.status_reason_code,
            "field_provenance": cls._provenance_list(item.field_provenance),
        }

    @classmethod
    def _condition(cls, item):
        return {
            "condition_code": item.condition_code,
            "measurement_references": [
                cls._measurement(reference)
                for reference in sorted(
                    item.measurement_references,
                    key=lambda reference: reference.reference_id,
                )
            ],
            "field_provenance": cls._provenance_list(item.field_provenance),
        }

    @classmethod
    def _measurement(cls, item):
        return {
            "reference_id": item.reference_id,
            "experiment_id": item.experiment_id,
            "measurement_name": item.measurement_name,
            "content_hash": item.content_hash,
            "field_provenance": cls._provenance_list(item.field_provenance),
        }

    @staticmethod
    def _provenance_list(values):
        return [
            {
                "field_code": item.field_code,
                "source": item.source.value,
                "source_id": item.source_id,
                "provenance_codes": list(item.provenance_codes),
            }
            for item in sorted(values, key=lambda item: item.field_code)
        ]

    @classmethod
    def _decode_declaration(cls, value):
        cls._object(value, "Reflection declaration")
        try:
            status = ReflectionExperimentDeclarationStatus(value.get("status"))
        except (TypeError, ValueError) as error:
            raise ValueError("Unsupported reflection declaration status.") from error
        return ControlledReflectionExperimentDeclaration(
            declaration_id=cls._string(value, "declaration_id"),
            proposal_id=cls._string(value, "proposal_id"),
            status=status,
            reference_condition=cls._decode_condition(
                value.get("reference_condition")
            ),
            intervention_condition=cls._decode_condition(
                value.get("intervention_condition")
            ),
            status_reason_code=cls._optional_string(
                value.get("status_reason_code")
            ),
            field_provenance=cls._decode_provenance(
                value.get("field_provenance")
            ),
        )

    @classmethod
    def _decode_condition(cls, value):
        cls._object(value, "Reflection experiment condition")
        measurements = value.get("measurement_references")
        if not isinstance(measurements, list):
            raise ValueError("Reflection measurement references must be a list.")
        return ReflectionExperimentConditionDeclaration(
            condition_code=cls._string(value, "condition_code"),
            measurement_references=tuple(
                sorted(
                    (cls._decode_measurement(item) for item in measurements),
                    key=lambda item: item.reference_id,
                )
            ),
            field_provenance=cls._decode_provenance(
                value.get("field_provenance")
            ),
        )

    @classmethod
    def _decode_measurement(cls, value):
        cls._object(value, "Reflection measurement reference")
        return ReflectionExperimentMeasurementReference(
            reference_id=cls._string(value, "reference_id"),
            experiment_id=cls._string(value, "experiment_id"),
            measurement_name=cls._string(value, "measurement_name"),
            content_hash=cls._optional_string(value.get("content_hash")),
            field_provenance=cls._decode_provenance(
                value.get("field_provenance")
            ),
        )

    @classmethod
    def _decode_provenance(cls, values):
        if not isinstance(values, list):
            raise ValueError("Declaration field provenance must be a list.")
        result = []
        for value in values:
            cls._object(value, "Declaration field provenance")
            try:
                source = ReflectionDeclarationProvenanceSource(
                    value.get("source")
                )
            except (TypeError, ValueError) as error:
                raise ValueError("Unsupported declaration provenance source.") from error
            codes = value.get("provenance_codes")
            if not isinstance(codes, list) or any(
                not isinstance(item, str) or not item for item in codes
            ):
                raise ValueError("Declaration provenance codes must be a list.")
            result.append(ReflectionDeclarationFieldProvenance(
                field_code=cls._string(value, "field_code"),
                source=source,
                source_id=cls._string(value, "source_id"),
                provenance_codes=tuple(codes),
            ))
        return tuple(sorted(result, key=lambda item: item.field_code))

    @staticmethod
    def _object(value, label):
        if not isinstance(value, dict):
            raise ValueError(f"{label} must be an object.")

    @staticmethod
    def _string(value, key):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Reflection declaration field {key} is required.")
        return item

    @staticmethod
    def _optional_string(value):
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Optional reflection declaration strings cannot be empty.")
        return value


class ControlledReflectionExperimentJsonRepository:
    def __init__(self, codec=None):
        self.codec = codec or ControlledReflectionExperimentJsonCodec()

    def save(self, path, registry):
        target = Path(path)
        serialized = self.codec.dumps(registry) + "\n"
        if target.is_file() and target.read_text(encoding="utf-8") == serialized:
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(target)
        return True

    def load(self, path):
        target = Path(path)
        if not target.is_file():
            return ControlledReflectionExperimentDeclarationRegistry(())
        return self.codec.loads(target.read_text(encoding="utf-8"))
