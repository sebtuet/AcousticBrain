from dataclasses import dataclass

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
)

from .evidence_plan_preparation import evidence_acquisition_plan_fingerprint


@dataclass(frozen=True)
class ChannelIsolationOperationalWorksheets:
    plan: EvidenceAcquisitionPlan
    microphone_position: dict
    acquisition_settings: dict


class ChannelIsolationOperationalWorksheetService:
    """Generates explicit fill-in worksheets without asserting prerequisites."""

    PLACEHOLDER = "REPLACE_WITH_EXPLICIT_USER_VALUE"

    def generate(self, plan_id, *, plans):
        if not isinstance(plans, tuple) or any(
            not isinstance(value, EvidenceAcquisitionPlan) for value in plans
        ):
            raise TypeError("Channel-isolation worksheet plans must be typed.")
        matches = tuple(value for value in plans if value.plan_id == plan_id)
        if not matches:
            raise ValueError(f"CHANNEL_ISOLATION_WORKSHEET_PLAN_UNKNOWN: {plan_id}.")
        if len(matches) != 1:
            raise ValueError(
                f"CHANNEL_ISOLATION_WORKSHEET_PLAN_AMBIGUOUS: {plan_id}."
            )
        plan = matches[0]
        if plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError(
                f"CHANNEL_ISOLATION_WORKSHEET_PLAN_NOT_READY: {plan_id}."
            )
        if plan.test_type is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION:
            raise ValueError(
                f"CHANNEL_ISOLATION_WORKSHEET_PLAN_TYPE_INVALID: {plan_id}."
            )
        fingerprint = evidence_acquisition_plan_fingerprint(plan)
        common = {
            "schema_version": 1,
            "plan_id": plan.plan_id,
            "plan_contract_fingerprint": fingerprint,
            "documentation_source": "USER_JSON",
            "user_note": None,
        }
        return ChannelIsolationOperationalWorksheets(
            plan=plan,
            microphone_position={
                **common,
                "record_id": f"channel-isolation-microphone-{fingerprint[:12]}-1",
                "reference_geometry": self.PLACEHOLDER,
                "position_description": self.PLACEHOLDER,
                "orientation_description": self.PLACEHOLDER,
            },
            acquisition_settings={
                **common,
                "record_id": f"channel-isolation-settings-{fingerprint[:12]}-1",
                "gain": self.PLACEHOLDER,
                "time_window": self.PLACEHOLDER,
                "signal_chain": self.PLACEHOLDER,
                "reuse_declaration": (
                    "REPLACE_WITH_INTENDED_UNCHANGED_OR_NOT_INTENDED_UNCHANGED"
                ),
            },
        )
