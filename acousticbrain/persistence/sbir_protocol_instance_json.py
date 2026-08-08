import json
from pathlib import Path

from acousticbrain.models import SBIRProtocolInstanceInput


class SBIRProtocolInstanceInputJsonLoader:
    FIELDS = frozenset((
        "schema_version",
        "protocol_instance_id",
        "protocol_id",
        "source_plan_id",
        "source_plan_contract_fingerprint",
        "reference_experiment_id",
        "moved_experiment_id",
        "speaker_id",
        "surface_id",
        "geometry_candidate_id",
        "speaker_displacement_m",
        "declaration_source",
        "user_note",
    ))

    def dumps(self, value, *, indent=2):
        if not isinstance(value, SBIRProtocolInstanceInput):
            raise TypeError("SBIR protocol-instance input is required.")
        return json.dumps(
            {
                "schema_version": value.schema_version,
                "protocol_instance_id": value.protocol_instance_id,
                "protocol_id": value.protocol_id,
                "source_plan_id": value.source_plan_id,
                "source_plan_contract_fingerprint": (
                    value.source_plan_contract_fingerprint
                ),
                "reference_experiment_id": value.reference_experiment_id,
                "moved_experiment_id": value.moved_experiment_id,
                "speaker_id": value.speaker_id,
                "surface_id": value.surface_id,
                "geometry_candidate_id": value.geometry_candidate_id,
                "speaker_displacement_m": value.speaker_displacement_m,
                "declaration_source": value.declaration_source,
                "user_note": value.user_note,
            },
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    def load(self, path):
        source = Path(path)
        try:
            payload = json.loads(
                source.read_text(encoding="utf-8"),
                object_pairs_hook=self._object_without_duplicate_fields,
                parse_constant=self._reject_non_json_number,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"Invalid SBIR protocol-instance JSON: {error}") from error
        return self.decode(payload)

    def decode(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("SBIR protocol-instance input must be an object.")
        fields = frozenset(payload)
        missing = tuple(sorted(self.FIELDS - fields))
        unknown = tuple(sorted(fields - self.FIELDS))
        if missing:
            raise ValueError(
                "Missing SBIR protocol-instance fields: " + ", ".join(missing)
            )
        if unknown:
            raise ValueError(
                "Unknown SBIR protocol-instance fields: " + ", ".join(unknown)
            )
        return SBIRProtocolInstanceInput(**payload)

    @staticmethod
    def _object_without_duplicate_fields(pairs):
        value = {}
        for field, item in pairs:
            if field in value:
                raise ValueError(f"Duplicate JSON field: {field}")
            value[field] = item
        return value

    @staticmethod
    def _reject_non_json_number(value):
        raise ValueError(f"Non-standard JSON number: {value}")
