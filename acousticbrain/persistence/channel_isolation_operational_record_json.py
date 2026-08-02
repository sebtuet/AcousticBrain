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

    @staticmethod
    def dumps_worksheet(value, *, indent=2):
        if not isinstance(value, dict):
            raise TypeError("Channel-isolation worksheet must be an object.")
        return json.dumps(
            value,
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def save_new_worksheet(cls, path, value):
        target = Path(path)
        if target.exists():
            raise ValueError(
                f"Channel-isolation worksheet output already exists: {target}"
            )
        if not target.parent.exists() or not target.parent.is_dir():
            raise ValueError(
                f"Channel-isolation worksheet parent is unavailable: {target.parent}"
            )
        serialized = cls.dumps_worksheet(value) + "\n"
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(target)
        return target


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
