import json
from pathlib import Path

from acousticbrain.models import (
    EvidencePlanAllPrerequisitesStatus,
    EvidencePlanPreparationDeclarationStatus,
    EvidencePlanPreparationRecord,
    EvidencePlanPreparationRegistry,
    EvidencePlanPreparationResolutionStatus,
)

from .evidence_plan_preparation_json import (
    EvidencePlanPreparationConfirmationJsonLoader,
)


class EvidencePlanPreparationRegistryJsonCodec:
    SCHEMA_VERSION = 1
    ROOT_FIELDS = frozenset(("schema_version", "records"))
    RECORD_FIELDS = frozenset((
        "confirmation_input",
        "resolution_status",
        "declaration_status",
        "all_prerequisites_status",
    ))

    def dumps(self, registry, *, indent=2):
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("Evidence-plan preparation registry is required.")
        return json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                "records": [
                    self._encode_record(value)
                    for value in sorted(
                        registry.records,
                        key=lambda item: item.confirmation_input.confirmation_id,
                    )
                ],
            },
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    def loads(self, payload):
        try:
            value = json.loads(payload)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError("Invalid evidence-plan preparation registry JSON.") from error
        self._exact_fields(value, self.ROOT_FIELDS, "registry")
        if (
            not isinstance(value["schema_version"], int)
            or isinstance(value["schema_version"], bool)
            or value["schema_version"] != self.SCHEMA_VERSION
        ):
            raise ValueError("Unsupported evidence-plan preparation registry version.")
        if not isinstance(value["records"], list):
            raise ValueError("Evidence-plan preparation records must be a list.")
        try:
            registry = EvidencePlanPreparationRegistry()
            for raw in value["records"]:
                registry = registry.with_record(self._decode_record(raw))
            return registry
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid evidence-plan preparation registry: {error}"
            ) from error

    @staticmethod
    def _encode_record(record):
        value = record.confirmation_input
        confirmation_input = {
            "schema_version": value.schema_version,
            "confirmation_id": value.confirmation_id,
            "plan_id": value.plan_id,
            "plan_contract_fingerprint": value.plan_contract_fingerprint,
            "prerequisites": [
                {"code": item.code, "status": item.status.value}
                for item in sorted(value.prerequisites, key=lambda item: item.code)
            ],
            "declaration_source": value.declaration_source,
        }
        if value.user_note is not None:
            confirmation_input["user_note"] = value.user_note
        return {
            "confirmation_input": confirmation_input,
            "resolution_status": record.resolution_status.value,
            "declaration_status": record.declaration_status.value,
            "all_prerequisites_status": (
                record.all_prerequisites_status.value
                if record.all_prerequisites_status is not None
                else None
            ),
        }

    @classmethod
    def _decode_record(cls, raw):
        cls._exact_fields(raw, cls.RECORD_FIELDS, "record")
        all_status = raw["all_prerequisites_status"]
        return EvidencePlanPreparationRecord(
            confirmation_input=(
                EvidencePlanPreparationConfirmationJsonLoader().decode(
                    raw["confirmation_input"]
                )
            ),
            resolution_status=EvidencePlanPreparationResolutionStatus(
                raw["resolution_status"]
            ),
            declaration_status=EvidencePlanPreparationDeclarationStatus(
                raw["declaration_status"]
            ),
            all_prerequisites_status=(
                EvidencePlanAllPrerequisitesStatus(all_status)
                if all_status is not None
                else None
            ),
        )

    @staticmethod
    def _exact_fields(value, expected, label):
        if not isinstance(value, dict):
            raise ValueError(f"Evidence-plan preparation {label} must be an object.")
        actual = frozenset(value)
        missing = tuple(sorted(expected - actual))
        unknown = tuple(sorted(actual - expected))
        if missing:
            raise ValueError(f"Missing {label} fields: " + ", ".join(missing))
        if unknown:
            raise ValueError(f"Unknown {label} fields: " + ", ".join(unknown))


class EvidencePlanPreparationRegistryJsonRepository:
    def __init__(self, codec=None):
        self.codec = codec or EvidencePlanPreparationRegistryJsonCodec()

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
            return EvidencePlanPreparationRegistry()
        return self.codec.loads(target.read_text(encoding="utf-8"))
