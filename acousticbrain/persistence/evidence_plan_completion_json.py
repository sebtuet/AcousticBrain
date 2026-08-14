import json
from pathlib import Path

from acousticbrain.models import (
    EvidencePlanCompletionInput,
    EvidencePlanCompletionReferenceKind,
)


class EvidencePlanCompletionInputJsonLoader:
    SCHEMA_VERSION = 1
    REQUIRED_FIELDS = frozenset((
        "schema_version",
        "completion_input_id",
        "source_plan_id",
        "reference_kind",
        "reference_id",
        "declaration_source",
    ))
    OPTIONAL_FIELDS = frozenset(("user_note",))

    def load(self, path):
        source = Path(path)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Invalid evidence-plan completion JSON: {error}"
            ) from error
        return self.decode(payload)

    def decode(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("Evidence-plan completion input must be an object.")
        fields = frozenset(payload)
        missing = tuple(sorted(self.REQUIRED_FIELDS - fields))
        unknown = tuple(sorted(
            fields - self.REQUIRED_FIELDS - self.OPTIONAL_FIELDS
        ))
        if missing:
            raise ValueError(
                "Missing evidence-plan completion fields: " + ", ".join(missing)
            )
        if unknown:
            raise ValueError(
                "Unknown evidence-plan completion fields: " + ", ".join(unknown)
            )
        schema_version = payload["schema_version"]
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version != self.SCHEMA_VERSION
        ):
            raise ValueError("Unsupported evidence-plan completion schema version.")
        try:
            reference_kind = EvidencePlanCompletionReferenceKind(
                payload["reference_kind"]
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Evidence-plan completion reference_kind must be PROTOCOL or PLAN."
            ) from error
        return EvidencePlanCompletionInput(
            schema_version=schema_version,
            completion_input_id=payload["completion_input_id"],
            source_plan_id=payload["source_plan_id"],
            reference_kind=reference_kind,
            reference_id=payload["reference_id"],
            declaration_source=payload["declaration_source"],
            user_note=payload.get("user_note"),
        )
