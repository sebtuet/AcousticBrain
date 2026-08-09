import hashlib
import json
from pathlib import Path

from acousticbrain.models import (
    SBIRRoomGeometryDeclarationInput,
    SBIRRoomGeometryResolutionDecision,
)

from .room_description_json import RoomDescriptionJsonCodec


class SBIRRoomGeometryDeclarationInputJsonLoader:
    FIELDS = frozenset((
        "schema_version",
        "declaration_input_id",
        "target_experiment_id",
        "declaration_source",
        "room_description_document",
        "user_note",
    ))
    CONTRACT_FIELDS = frozenset(
        (
            *FIELDS,
            "room_description_fingerprint",
            "validation_decisions",
        )
    )

    def __init__(self, room_codec=None):
        self.room_codec = room_codec or RoomDescriptionJsonCodec()

    def dumps(self, value, *, indent=2):
        if not isinstance(value, SBIRRoomGeometryDeclarationInput):
            raise TypeError("SBIR room-geometry declaration input is required.")
        return json.dumps(
            {
                "schema_version": value.schema_version,
                "declaration_input_id": value.declaration_input_id,
                "target_experiment_id": value.target_experiment_id,
                "declaration_source": value.declaration_source,
                "room_description_document": self.room_codec.to_dict(
                    value.room_description
                ),
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
            raise ValueError(f"Invalid SBIR room-geometry JSON: {error}") from error
        return self.decode(payload)

    def decode(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("SBIR room-geometry input must be an object.")
        fields = frozenset(payload)
        missing = tuple(sorted(self.FIELDS - fields))
        unknown = tuple(sorted(fields - self.FIELDS))
        if missing:
            raise ValueError(
                "Missing SBIR room-geometry fields: " + ", ".join(missing)
            )
        if unknown:
            raise ValueError(
                "Unknown SBIR room-geometry fields: " + ", ".join(unknown)
            )
        document = payload["room_description_document"]
        if not isinstance(document, dict):
            raise ValueError(
                "SBIR room-geometry room_description_document must be an object."
            )
        room_schema_version = document.get("schema_version")
        if (
            not isinstance(room_schema_version, int)
            or isinstance(room_schema_version, bool)
            or room_schema_version != self.room_codec.SCHEMA_VERSION
        ):
            raise ValueError(
                "SBIR room-geometry room_description_document must use schema "
                "version 5."
            )
        loaded = self.room_codec.from_dict(document)
        if not loaded.is_success:
            details = "; ".join(
                value.code.value
                + (" at " + ".".join(map(str, value.path)) if value.path else "")
                for value in loaded.errors
            )
            raise ValueError(
                "Invalid SBIR room-geometry room_description_document: " + details
            )
        if self.room_codec.to_dict(loaded.description) != document:
            raise ValueError(
                "SBIR room-geometry room_description_document must be canonical "
                "RoomDescription v5."
            )
        return SBIRRoomGeometryDeclarationInput(
            schema_version=payload["schema_version"],
            declaration_input_id=payload["declaration_input_id"],
            target_experiment_id=payload["target_experiment_id"],
            declaration_source=payload["declaration_source"],
            room_description=loaded.description,
            user_note=payload["user_note"],
        )

    def contract_payload(self, value, decisions):
        if not isinstance(value, SBIRRoomGeometryDeclarationInput):
            raise TypeError("SBIR room-geometry declaration input is required.")
        decisions = tuple(decisions)
        if decisions != tuple(SBIRRoomGeometryResolutionDecision):
            raise ValueError("SBIR room-geometry contract decisions must be exact.")
        document = self.room_codec.to_dict(value.room_description)
        payload = json.loads(self.dumps(value))
        payload["room_description_fingerprint"] = self._fingerprint(document)
        payload["validation_decisions"] = [item.value for item in decisions]
        return payload

    def decode_contract(self, payload):
        if not isinstance(payload, dict):
            raise ValueError(
                "SBIR room-geometry manifest contract must be an object."
            )
        fields = frozenset(payload)
        if fields != self.CONTRACT_FIELDS:
            missing = ", ".join(sorted(self.CONTRACT_FIELDS - fields)) or "none"
            unknown = ", ".join(sorted(fields - self.CONTRACT_FIELDS)) or "none"
            raise ValueError(
                "SBIR room-geometry manifest contract fields are invalid: "
                f"missing={missing}; unknown={unknown}."
            )
        expected_decisions = [
            item.value for item in SBIRRoomGeometryResolutionDecision
        ]
        if payload["validation_decisions"] != expected_decisions:
            raise ValueError(
                "SBIR room-geometry manifest contract decisions are invalid."
            )
        value = self.decode({field: payload[field] for field in self.FIELDS})
        expected_fingerprint = self._fingerprint(
            payload["room_description_document"]
        )
        if payload["room_description_fingerprint"] != expected_fingerprint:
            raise ValueError(
                "SBIR room-geometry manifest contract fingerprint is invalid."
            )
        return value

    @staticmethod
    def _fingerprint(document):
        canonical = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

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
