import json
from pathlib import Path

from acousticbrain.models import (
    ListeningPositionCampaignInstance,
    ListeningPositionCampaignInstanceAnalysis,
    ListeningPositionCampaignInstancePosition,
    ListeningPositionCampaignInstanceStatus,
    ListeningPositionCampaignInstanceValidationError,
)


class ListeningPositionCampaignInstanceJsonLoader:
    SCHEMA_VERSION = 1

    def load(self, path):
        source = Path(path)
        source_path = str(source.resolve())
        if not source.exists():
            return self._invalid(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                f"Campaign instance does not exist: {source}",
                source_path,
            )
        if not source.is_file():
            return self._invalid(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                f"Campaign instance is not a file: {source}",
                source_path,
            )
        try:
            value = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            return self._invalid(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                f"Invalid campaign instance JSON: {error}",
                source_path,
            )
        try:
            instance = self._decode(value)
        except ListeningPositionCampaignInstanceValidationError as error:
            return self._invalid(error.code, str(error), source_path)
        except (KeyError, TypeError, ValueError) as error:
            return self._invalid(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID", str(error), source_path
            )
        return ListeningPositionCampaignInstanceAnalysis(
            status=ListeningPositionCampaignInstanceStatus.VALID,
            instance=instance,
            blocking_reasons=(),
            validation_messages=(),
            source_path=source_path,
        )

    def _decode(self, value):
        self._object(value, "Campaign instance")
        schema_version = self._required(value, "schema_version")
        if (
            not isinstance(schema_version, int)
            or isinstance(schema_version, bool)
            or schema_version != self.SCHEMA_VERSION
        ):
            raise ListeningPositionCampaignInstanceValidationError(
                "CAMPAIGN_INSTANCE_SCHEMA_INVALID",
                f"Unsupported campaign instance schema version: {schema_version}",
            )
        positions = self._required(value, "positions")
        if not isinstance(positions, list):
            raise TypeError("Campaign instance positions must be an array.")
        return ListeningPositionCampaignInstance(
            instance_id=self._required(value, "instance_id"),
            protocol_id=self._required(value, "protocol_id"),
            protocol_version=self._required(value, "protocol_version"),
            reference_experiment_id=self._required(
                value, "reference_experiment_id"
            ),
            positions=tuple(self._position(item) for item in positions),
            comparability_rule=self._required(value, "comparability_rule"),
            controlled_variables=self._strings(
                self._required(value, "controlled_variables"),
                "controlled_variables",
            ),
            required_measurements=self._strings(
                self._required(value, "required_measurements"),
                "required_measurements",
            ),
            declaration_source=self._required(value, "declaration_source"),
            declaration_version=self._required(value, "declaration_version"),
            notes=value["notes"] if "notes" in value else None,
        )

    def _position(self, value):
        self._object(value, "Campaign instance position")
        return ListeningPositionCampaignInstancePosition(
            position_code=self._required(value, "position_code"),
            position_role=self._required(value, "position_role"),
            order_index=self._required(value, "order_index"),
            longitudinal_offset_m=self._required(value, "longitudinal_offset_m"),
            lateral_offset_m=self._required(value, "lateral_offset_m"),
            vertical_offset_m=self._required(value, "vertical_offset_m"),
            parent_position_code=self._required(value, "parent_position_code"),
            reference_position_code=self._required(
                value, "reference_position_code"
            ),
            reference_experiment_id=self._required(
                value, "reference_experiment_id"
            ),
            modified_variables=self._strings(
                self._required(value, "modified_variables"),
                "modified_variables",
            ),
            controlled_variables=self._strings(
                self._required(value, "controlled_variables"),
                "controlled_variables",
            ),
            required_measurements=self._strings(
                self._required(value, "required_measurements"),
                "required_measurements",
            ),
        )

    @staticmethod
    def _required(value, key):
        if key not in value:
            raise KeyError(f"Campaign instance field is required: {key}")
        return value[key]

    @staticmethod
    def _object(value, label):
        if not isinstance(value, dict):
            raise TypeError(f"{label} must be an object.")

    @staticmethod
    def _strings(value, label):
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item for item in value
        ) or len(value) != len(set(value)):
            raise TypeError(f"Campaign instance {label} must contain unique strings.")
        return tuple(value)

    @staticmethod
    def _invalid(code, message, source_path):
        return ListeningPositionCampaignInstanceAnalysis(
            status=ListeningPositionCampaignInstanceStatus.INVALID,
            instance=None,
            blocking_reasons=(code,),
            validation_messages=(message,),
            source_path=source_path,
        )
