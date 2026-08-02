import pytest

from acousticbrain.models import AcquisitionSettingsReuseDeclaration
from acousticbrain.persistence import (
    ChannelIsolationAcquisitionSettingsRecordJsonLoader,
    ChannelIsolationMicrophonePositionRecordJsonLoader,
)


FINGERPRINT = "a" * 64


def microphone(**changes):
    value = {
        "schema_version": 1, "record_id": "position-001", "plan_id": "PLAN",
        "plan_contract_fingerprint": FINGERPRINT,
        "reference_geometry": "Front wall and room centerline.",
        "position_description": "At the documented listening point.",
        "orientation_description": "Vertical, capsule upward.",
        "documentation_source": "USER_JSON", "user_note": None,
    }
    value.update(changes)
    return value


def settings(**changes):
    value = {
        "schema_version": 1, "record_id": "settings-001", "plan_id": "PLAN",
        "plan_contract_fingerprint": FINGERPRINT, "gain": "Recorded interface gain.",
        "time_window": "Recorded REW window.", "signal_chain": "Recorded routing.",
        "reuse_declaration": "INTENDED_UNCHANGED",
        "documentation_source": "USER_JSON", "user_note": None,
    }
    value.update(changes)
    return value


def test_strict_loaders_preserve_exact_user_documentation():
    position = ChannelIsolationMicrophonePositionRecordJsonLoader().decode(microphone())
    acquisition = ChannelIsolationAcquisitionSettingsRecordJsonLoader().decode(settings())
    assert position.reference_geometry == "Front wall and room centerline."
    assert acquisition.reuse_declaration is AcquisitionSettingsReuseDeclaration.INTENDED_UNCHANGED


@pytest.mark.parametrize("loader,value", (
    (ChannelIsolationMicrophonePositionRecordJsonLoader(), microphone(extra=True)),
    (ChannelIsolationAcquisitionSettingsRecordJsonLoader(), settings(extra=True)),
))
def test_unknown_fields_are_rejected(loader, value):
    with pytest.raises(ValueError, match="Unknown operational record fields"):
        loader.decode(value)


def test_closed_reuse_declaration_and_exact_text_are_enforced():
    with pytest.raises(ValueError):
        ChannelIsolationAcquisitionSettingsRecordJsonLoader().decode(settings(reuse_declaration="MAYBE"))
    with pytest.raises(ValueError, match="exact non-empty"):
        ChannelIsolationMicrophonePositionRecordJsonLoader().decode(microphone(position_description=" unknown "))
