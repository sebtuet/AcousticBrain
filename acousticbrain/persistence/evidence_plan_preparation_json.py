import json
from pathlib import Path

from acousticbrain.models import (
    EvidencePlanPreparationConfirmationInput,
    EvidencePlanPrerequisiteDeclaration,
    EvidencePlanPrerequisiteStatus,
)


class EvidencePlanPreparationConfirmationJsonLoader:
    SCHEMA_VERSION = 1
    REQUIRED_FIELDS = frozenset((
        "schema_version",
        "confirmation_id",
        "plan_id",
        "plan_contract_fingerprint",
        "prerequisites",
        "declaration_source",
    ))
    OPTIONAL_FIELDS = frozenset(("user_note",))
    PREREQUISITE_FIELDS = frozenset(("code", "status"))

    def dumps(self, value, *, indent=2):
        if not isinstance(value, EvidencePlanPreparationConfirmationInput):
            raise TypeError("Evidence-plan preparation input is required.")
        payload = {
            "schema_version": value.schema_version,
            "confirmation_id": value.confirmation_id,
            "plan_id": value.plan_id,
            "plan_contract_fingerprint": value.plan_contract_fingerprint,
            "prerequisites": [
                {"code": item.code, "status": item.status.value}
                for item in value.prerequisites
            ],
            "declaration_source": value.declaration_source,
            "user_note": value.user_note,
        }
        return json.dumps(
            payload,
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    def save_new(self, path, value):
        target = Path(path)
        if target.exists():
            raise ValueError(
                f"Evidence-plan preparation draft output already exists: {target}"
            )
        if not target.parent.exists() or not target.parent.is_dir():
            raise ValueError(
                "Evidence-plan preparation draft output parent is unavailable: "
                f"{target.parent}"
            )
        serialized = self.dumps(value) + "\n"
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(target)
        return target

    def load(self, path):
        source = Path(path)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Invalid evidence-plan preparation JSON: {error}"
            ) from error
        return self.decode(payload)

    def decode(self, payload):
        self._exact_fields(
            payload,
            self.REQUIRED_FIELDS,
            self.OPTIONAL_FIELDS,
            "input",
        )
        schema_version = payload["schema_version"]
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version != self.SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported evidence-plan preparation schema version."
            )
        raw_prerequisites = payload["prerequisites"]
        if not isinstance(raw_prerequisites, list):
            raise ValueError(
                "Evidence-plan preparation prerequisites must be a list."
            )
        prerequisites = []
        for index, raw in enumerate(raw_prerequisites):
            self._exact_fields(
                raw,
                self.PREREQUISITE_FIELDS,
                frozenset(),
                f"prerequisite[{index}]",
            )
            try:
                status = EvidencePlanPrerequisiteStatus(raw["status"])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid prerequisite[{index}] status."
                ) from error
            prerequisites.append(EvidencePlanPrerequisiteDeclaration(
                code=raw["code"],
                status=status,
            ))
        return EvidencePlanPreparationConfirmationInput(
            schema_version=schema_version,
            confirmation_id=payload["confirmation_id"],
            plan_id=payload["plan_id"],
            plan_contract_fingerprint=payload["plan_contract_fingerprint"],
            prerequisites=tuple(prerequisites),
            declaration_source=payload["declaration_source"],
            user_note=payload.get("user_note"),
        )

    @staticmethod
    def _exact_fields(value, required, optional, label):
        if not isinstance(value, dict):
            raise ValueError(
                f"Evidence-plan preparation {label} must be an object."
            )
        fields = frozenset(value)
        missing = tuple(sorted(required - fields))
        unknown = tuple(sorted(fields - required - optional))
        if missing:
            raise ValueError(
                f"Missing evidence-plan preparation {label} fields: "
                + ", ".join(missing)
            )
        if unknown:
            raise ValueError(
                f"Unknown evidence-plan preparation {label} fields: "
                + ", ".join(unknown)
            )
