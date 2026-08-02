from dataclasses import dataclass

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
)
from acousticbrain.persistence import (
    ChannelIsolationAcquisitionSettingsRecordJsonLoader,
    ChannelIsolationMicrophonePositionRecordJsonLoader,
)

from .evidence_plan_preparation import evidence_acquisition_plan_fingerprint


@dataclass(frozen=True)
class ChannelIsolationOperationalRecordPreview:
    status: str
    missing_fields: tuple[str, ...]
    microphone_position: object | None
    acquisition_settings: object | None
    user_action_state: str


class ChannelIsolationOperationalRecordPreviewService:
    PLACEHOLDER_PREFIX = "REPLACE_WITH_"

    def preview(self, plan_id, microphone, settings, *, plans):
        plan = self._plan(plan_id, plans)
        fingerprint = evidence_acquisition_plan_fingerprint(plan)
        self._structure(
            microphone,
            ChannelIsolationMicrophonePositionRecordJsonLoader.fields,
            "microphone_position",
        )
        self._structure(
            settings,
            ChannelIsolationAcquisitionSettingsRecordJsonLoader.fields,
            "acquisition_settings",
        )
        for label, value in (("microphone_position", microphone), ("acquisition_settings", settings)):
            if value["plan_id"] != plan.plan_id:
                raise ValueError(f"{label} plan identity is inconsistent.")
            if value["plan_contract_fingerprint"] != fingerprint:
                raise ValueError(f"{label} plan fingerprint is stale.")
        missing = tuple(sorted(
            f"{label}.{field}"
            for label, value in (("microphone_position", microphone), ("acquisition_settings", settings))
            for field, content in value.items()
            if isinstance(content, str) and content.startswith(self.PLACEHOLDER_PREFIX)
        ))
        if missing:
            return ChannelIsolationOperationalRecordPreview(
                status="DOCUMENTATION_INCOMPLETE",
                missing_fields=missing,
                microphone_position=None,
                acquisition_settings=None,
                user_action_state="COMPLETE_OPERATIONAL_DOCUMENTATION",
            )
        position = ChannelIsolationMicrophonePositionRecordJsonLoader().decode(microphone)
        acquisition = ChannelIsolationAcquisitionSettingsRecordJsonLoader().decode(settings)
        return ChannelIsolationOperationalRecordPreview(
            status="DOCUMENTATION_COMPLETE",
            missing_fields=(),
            microphone_position=position,
            acquisition_settings=acquisition,
            user_action_state="REVIEW_PREPARATION_STATUS_SEPARATELY",
        )

    @staticmethod
    def _structure(value, fields, label):
        if not isinstance(value, dict):
            raise ValueError(f"{label} worksheet must be an object.")
        expected = set(fields)
        actual = set(value)
        if expected != actual:
            missing = ", ".join(sorted(expected - actual))
            unknown = ", ".join(sorted(actual - expected))
            raise ValueError(
                f"{label} worksheet fields are invalid; missing: {missing}; unknown: {unknown}."
            )

    @staticmethod
    def _plan(plan_id, plans):
        matches = tuple(value for value in plans if value.plan_id == plan_id)
        if len(matches) != 1:
            raise ValueError(f"Operational record preview requires one exact plan: {plan_id}.")
        plan = matches[0]
        if plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError("Operational record preview plan is not READY.")
        if plan.test_type is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION:
            raise ValueError("Operational record preview plan is not CHANNEL_ISOLATION.")
        return plan
