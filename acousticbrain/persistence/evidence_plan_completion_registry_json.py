import json
from pathlib import Path

from acousticbrain.models import (
    DerivedEvidenceAcquisitionPlan,
    DerivedEvidencePlanStatus,
    EvidencePlanCompletionCompatibilityStatus,
    EvidencePlanCompletionRecord,
    EvidencePlanCompletionReferenceKind,
    EvidencePlanCompletionRegistry,
    EvidencePlanCompletionResolutionStatus,
)

from .evidence_acquisition_contract_json import (
    EvidenceAcquisitionPlanContractJsonCodec,
)
from .evidence_plan_completion_json import EvidencePlanCompletionInputJsonLoader


class EvidencePlanCompletionRegistryJsonCodec:
    SCHEMA_VERSION = 1
    ROOT_FIELDS = frozenset(("schema_version", "records"))
    RECORD_FIELDS = frozenset((
        "completion_input",
        "resolution_status",
        "compatibility_status",
        "derived_plan",
    ))
    DERIVATION_FIELDS = frozenset((
        "plan",
        "source_plan",
        "source_plan_id",
        "completion_input_id",
        "reference_kind",
        "reference_id",
        "compatibility_authority_id",
        "compatibility_authority_version",
        "reference_parameter_codes",
        "reference_contract_fingerprint",
        "contract_id",
        "contract_version",
        "status",
    ))

    def dumps(self, registry, *, indent=2):
        if not isinstance(registry, EvidencePlanCompletionRegistry):
            raise TypeError("Evidence-plan completion registry is required.")
        return json.dumps(
            {
                "schema_version": self.SCHEMA_VERSION,
                "records": [
                    self._encode_record(value)
                    for value in sorted(
                        registry.records,
                        key=lambda item: item.completion_input.completion_input_id,
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
            raise ValueError("Invalid evidence-plan completion registry JSON.") from error
        self._exact_fields(value, self.ROOT_FIELDS, "registry")
        if (
            not isinstance(value["schema_version"], int)
            or isinstance(value["schema_version"], bool)
            or value["schema_version"] != self.SCHEMA_VERSION
        ):
            raise ValueError("Unsupported evidence-plan completion registry version.")
        records = value["records"]
        if not isinstance(records, list):
            raise ValueError("Evidence-plan completion records must be a list.")
        try:
            registry = EvidencePlanCompletionRegistry()
            for raw in records:
                registry = registry.with_record(self._decode_record(raw))
            return registry
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid evidence-plan completion registry: {error}"
            ) from error

    @classmethod
    def _encode_record(cls, record):
        value = record.completion_input
        derived = record.derived_plan
        completion_input = {
            "schema_version": value.schema_version,
            "completion_input_id": value.completion_input_id,
            "source_plan_id": value.source_plan_id,
            "reference_kind": value.reference_kind.value,
            "reference_id": value.reference_id,
            "declaration_source": value.declaration_source,
        }
        if value.user_note is not None:
            completion_input["user_note"] = value.user_note
        return {
            "completion_input": completion_input,
            "resolution_status": record.resolution_status.value,
            "compatibility_status": record.compatibility_status.value,
            "derived_plan": {
                "plan": EvidenceAcquisitionPlanContractJsonCodec.encode_plan(
                    derived.plan
                ),
                "source_plan": EvidenceAcquisitionPlanContractJsonCodec.encode_plan(
                    derived.source_plan
                ),
                "source_plan_id": derived.source_plan_id,
                "completion_input_id": derived.completion_input_id,
                "reference_kind": derived.reference_kind.value,
                "reference_id": derived.reference_id,
                "compatibility_authority_id": derived.compatibility_authority_id,
                "compatibility_authority_version": (
                    derived.compatibility_authority_version
                ),
                "reference_parameter_codes": list(
                    derived.reference_parameter_codes
                ),
                "reference_contract_fingerprint": (
                    derived.reference_contract_fingerprint
                ),
                "contract_id": derived.contract_id,
                "contract_version": derived.contract_version,
                "status": derived.status.value,
            },
        }

    @classmethod
    def _decode_record(cls, raw):
        cls._exact_fields(raw, cls.RECORD_FIELDS, "record")
        derived = raw["derived_plan"]
        cls._exact_fields(derived, cls.DERIVATION_FIELDS, "derived_plan")
        completion_input = EvidencePlanCompletionInputJsonLoader().decode(
            raw["completion_input"]
        )
        return EvidencePlanCompletionRecord(
            completion_input=completion_input,
            resolution_status=EvidencePlanCompletionResolutionStatus(
                raw["resolution_status"]
            ),
            compatibility_status=EvidencePlanCompletionCompatibilityStatus(
                raw["compatibility_status"]
            ),
            derived_plan=DerivedEvidenceAcquisitionPlan(
                plan=EvidenceAcquisitionPlanContractJsonCodec.decode_plan(
                    derived["plan"]
                ),
                source_plan=EvidenceAcquisitionPlanContractJsonCodec.decode_plan(
                    derived["source_plan"]
                ),
                source_plan_id=derived["source_plan_id"],
                completion_input_id=derived["completion_input_id"],
                reference_kind=EvidencePlanCompletionReferenceKind(
                    derived["reference_kind"]
                ),
                reference_id=derived["reference_id"],
                compatibility_authority_id=derived["compatibility_authority_id"],
                compatibility_authority_version=(
                    derived["compatibility_authority_version"]
                ),
                reference_parameter_codes=tuple(
                    derived["reference_parameter_codes"]
                ),
                reference_contract_fingerprint=(
                    derived["reference_contract_fingerprint"]
                ),
                contract_id=derived["contract_id"],
                contract_version=derived["contract_version"],
                status=DerivedEvidencePlanStatus(derived["status"]),
            ),
        )

    @staticmethod
    def _exact_fields(value, expected, label):
        if not isinstance(value, dict):
            raise ValueError(f"Evidence-plan completion {label} must be an object.")
        actual = frozenset(value)
        missing = tuple(sorted(expected - actual))
        unknown = tuple(sorted(actual - expected))
        if missing:
            raise ValueError(f"Missing {label} fields: " + ", ".join(missing))
        if unknown:
            raise ValueError(f"Unknown {label} fields: " + ", ".join(unknown))


class EvidencePlanCompletionRegistryJsonRepository:
    def __init__(self, codec=None):
        self.codec = codec or EvidencePlanCompletionRegistryJsonCodec()

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
            return EvidencePlanCompletionRegistry()
        return self.codec.loads(target.read_text(encoding="utf-8"))
