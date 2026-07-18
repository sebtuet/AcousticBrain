import json
from pathlib import Path

from acousticbrain.models import (
    CampaignReferenceAssertionStatus,
    CampaignReferenceDeclarationStatus,
    CampaignReferenceQualificationDeclaration,
    CampaignReferenceQualificationDeclarationAnalysis,
    CampaignReferenceQualificationValidationError,
)


class CampaignReferenceQualificationJsonLoader:
    SCHEMA_VERSION = 1

    def load(self, path):
        source = Path(path)
        source_path = str(source.resolve())
        if not source.exists():
            return self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_UNAVAILABLE",
                f"Campaign reference qualification does not exist: {source}",
                source_path,
            )
        if not source.is_file():
            return self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                f"Campaign reference qualification is not a file: {source}",
                source_path,
            )
        try:
            value = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            return self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                f"Invalid campaign reference qualification JSON: {error}",
                source_path,
            )
        try:
            declaration = self._decode(value)
        except CampaignReferenceQualificationValidationError as error:
            return self._invalid(error.code, str(error), source_path)
        except (KeyError, TypeError, ValueError) as error:
            return self._invalid(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                str(error),
                source_path,
            )
        return CampaignReferenceQualificationDeclarationAnalysis(
            status=CampaignReferenceDeclarationStatus.VALID,
            declaration=declaration,
            blocking_reasons=(),
            validation_messages=(),
            source_path=source_path,
        )

    def _decode(self, value):
        self._object(value, "Campaign reference qualification")
        schema_version = self._required(value, "schema_version")
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version != self.SCHEMA_VERSION
        ):
            raise CampaignReferenceQualificationValidationError(
                "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
                f"Unsupported qualification schema version: {schema_version}",
            )
        configuration_state = self._assertions(
            self._required(value, "configuration_state")
        )
        return CampaignReferenceQualificationDeclaration(
            schema_version=schema_version,
            qualification_id=self._required(value, "qualification_id"),
            experiment_id=self._required(value, "experiment_id"),
            intended_protocol_id=self._required(value, "intended_protocol_id"),
            intended_protocol_version=self._required(
                value, "intended_protocol_version"
            ),
            intended_campaign_instance_id=self._required(
                value, "intended_campaign_instance_id"
            ),
            reference_role=self._required(value, "reference_role"),
            configuration_state=configuration_state,
            controlled_variable_assertions=configuration_state,
            required_measurement_assertions=self._strings(
                self._required(value, "required_measurements"),
                "required_measurements",
            ),
            declaration_source=self._required(value, "declaration_source"),
            declaration_version=self._required(value, "declaration_version"),
            notes=value.get("notes"),
        )

    @staticmethod
    def _assertions(value):
        if not isinstance(value, dict) or not value:
            raise TypeError(
                "Campaign reference configuration_state must be a non-empty object."
            )
        assertions = []
        for code, raw_status in value.items():
            if not isinstance(code, str) or not code or not isinstance(raw_status, str):
                raise TypeError(
                    "Campaign reference configuration assertions are invalid."
                )
            try:
                status = CampaignReferenceAssertionStatus(raw_status)
            except ValueError as error:
                raise TypeError(
                    f"Unsupported configuration assertion status: {raw_status}"
                ) from error
            assertions.append((code, status))
        return tuple(assertions)

    @staticmethod
    def _strings(value, label):
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(item, str) or not item for item in value)
            or len(value) != len(set(value))
        ):
            raise TypeError(
                f"Campaign reference {label} must contain unique strings."
            )
        return tuple(value)

    @staticmethod
    def _required(value, key):
        if key not in value:
            raise KeyError(f"Campaign reference field is required: {key}")
        return value[key]

    @staticmethod
    def _object(value, label):
        if not isinstance(value, dict):
            raise TypeError(f"{label} must be an object.")

    @staticmethod
    def _invalid(code, message, source_path):
        return CampaignReferenceQualificationDeclarationAnalysis(
            status=CampaignReferenceDeclarationStatus.INVALID,
            declaration=None,
            blocking_reasons=(code,),
            validation_messages=(message,),
            source_path=source_path,
        )
