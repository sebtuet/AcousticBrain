import json
from pathlib import Path

from acousticbrain.models import (
    SBIRProtocolInstanceCompatibilityDecision,
    SBIRProtocolInstanceRecord,
    SBIRProtocolInstanceRegistry,
    SBIRProtocolInstanceResolutionDecision,
)

from .sbir_protocol_instance_json import SBIRProtocolInstanceInputJsonLoader


class SBIRProtocolInstanceRegistryJsonCodec:
    SCHEMA_VERSION = 1
    ROOT_FIELDS = frozenset(("schema_version", "records"))
    RECORD_FIELDS = frozenset((
        "protocol_instance_input",
        "source_plan_id",
        "source_plan_contract_fingerprint",
        "protocol_id",
        "reference_experiment_id",
        "moved_experiment_id",
        "geometry_candidate_id",
        "displacement_proposal_id",
        "resolution_decisions",
        "compatibility_decisions",
    ))

    def dumps(self, registry, *, indent=2):
        if not isinstance(registry, SBIRProtocolInstanceRegistry):
            raise TypeError("SBIR protocol-instance registry is required.")
        return json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                "records": [
                    self._encode_record(value)
                    for value in sorted(
                        registry.records,
                        key=lambda item: (
                            item.protocol_instance_input.protocol_instance_id
                        ),
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
            raise ValueError("Invalid SBIR protocol-instance registry JSON.") from error
        self._exact_fields(value, self.ROOT_FIELDS, "registry")
        version = value["schema_version"]
        if (
            not isinstance(version, int)
            or isinstance(version, bool)
            or version != self.SCHEMA_VERSION
        ):
            raise ValueError("Unsupported SBIR protocol-instance registry version.")
        records = value["records"]
        if not isinstance(records, list):
            raise ValueError("SBIR protocol-instance records must be a list.")
        try:
            registry = SBIRProtocolInstanceRegistry()
            for raw in records:
                registry = registry.with_record(self._decode_record(raw))
            return registry
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid SBIR protocol-instance registry: {error}"
            ) from error

    @classmethod
    def _encode_record(cls, record):
        loader = SBIRProtocolInstanceInputJsonLoader()
        return {
            "protocol_instance_input": json.loads(
                loader.dumps(record.protocol_instance_input)
            ),
            "source_plan_id": record.source_plan_id,
            "source_plan_contract_fingerprint": (
                record.source_plan_contract_fingerprint
            ),
            "protocol_id": record.protocol_id,
            "reference_experiment_id": record.reference_experiment_id,
            "moved_experiment_id": record.moved_experiment_id,
            "geometry_candidate_id": record.geometry_candidate_id,
            "displacement_proposal_id": record.displacement_proposal_id,
            "resolution_decisions": [
                value.value for value in record.resolution_decisions
            ],
            "compatibility_decisions": [
                value.value for value in record.compatibility_decisions
            ],
        }

    @classmethod
    def _decode_record(cls, raw):
        cls._exact_fields(raw, cls.RECORD_FIELDS, "record")
        return SBIRProtocolInstanceRecord(
            protocol_instance_input=(
                SBIRProtocolInstanceInputJsonLoader().decode(
                    raw["protocol_instance_input"]
                )
            ),
            source_plan_id=raw["source_plan_id"],
            source_plan_contract_fingerprint=(
                raw["source_plan_contract_fingerprint"]
            ),
            protocol_id=raw["protocol_id"],
            reference_experiment_id=raw["reference_experiment_id"],
            moved_experiment_id=raw["moved_experiment_id"],
            geometry_candidate_id=raw["geometry_candidate_id"],
            displacement_proposal_id=raw["displacement_proposal_id"],
            resolution_decisions=tuple(
                SBIRProtocolInstanceResolutionDecision(value)
                for value in raw["resolution_decisions"]
            ),
            compatibility_decisions=tuple(
                SBIRProtocolInstanceCompatibilityDecision(value)
                for value in raw["compatibility_decisions"]
            ),
        )

    @staticmethod
    def _exact_fields(value, expected, label):
        if not isinstance(value, dict):
            raise ValueError(
                f"SBIR protocol-instance {label} must be an object."
            )
        actual = frozenset(value)
        missing = tuple(sorted(expected - actual))
        unknown = tuple(sorted(actual - expected))
        if missing:
            raise ValueError(f"Missing {label} fields: " + ", ".join(missing))
        if unknown:
            raise ValueError(f"Unknown {label} fields: " + ", ".join(unknown))


class SBIRProtocolInstanceRegistryJsonRepository:
    def __init__(self, codec=None):
        self.codec = codec or SBIRProtocolInstanceRegistryJsonCodec()

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
            return SBIRProtocolInstanceRegistry()
        return self.codec.loads(target.read_text(encoding="utf-8"))
