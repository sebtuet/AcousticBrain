import json
from pathlib import Path

from acousticbrain.models import (
    AcquisitionSettingsReuseDeclaration,
    ChannelIsolationAcquisitionSettingsRecord,
    ChannelIsolationMicrophonePositionRecord,
)


class _StrictLoader:
    model = None
    fields = ()

    def load(self, path):
        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid channel-isolation operational record JSON: {error}") from error
        return self.decode(value)

    def decode(self, value):
        if not isinstance(value, dict):
            raise ValueError("Channel-isolation operational record must be an object.")
        expected = set(self.fields)
        actual = set(value)
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        if missing:
            raise ValueError("Missing operational record fields: " + ", ".join(missing))
        if unknown:
            raise ValueError("Unknown operational record fields: " + ", ".join(unknown))
        return self._model(value)


class ChannelIsolationMicrophonePositionRecordJsonLoader(_StrictLoader):
    fields = ("schema_version", "record_id", "plan_id", "plan_contract_fingerprint", "reference_geometry", "position_description", "orientation_description", "documentation_source", "user_note")

    def _model(self, value):
        return ChannelIsolationMicrophonePositionRecord(**value)


class ChannelIsolationAcquisitionSettingsRecordJsonLoader(_StrictLoader):
    fields = ("schema_version", "record_id", "plan_id", "plan_contract_fingerprint", "gain", "time_window", "signal_chain", "reuse_declaration", "documentation_source", "user_note")

    def _model(self, value):
        return ChannelIsolationAcquisitionSettingsRecord(
            **{**value, "reuse_declaration": AcquisitionSettingsReuseDeclaration(value["reuse_declaration"])}
        )
