from dataclasses import dataclass

from acousticbrain.models import EvidencePlanPreparationConfirmationInput

from .channel_isolation_operational_record_preview import (
    ChannelIsolationOperationalRecordPreviewService,
)
from .evidence_plan_preparation import EvidencePlanPreparationResolver


@dataclass(frozen=True)
class ChannelIsolationDocumentationReviewRow:
    prerequisite_code: str
    documentation_record_id: str
    documentation_state: str = "DOCUMENTATION_AVAILABLE"
    decision_state: str = "USER_PREPARATION_DECISION_REQUIRED"

    def __post_init__(self):
        if self.documentation_state != "DOCUMENTATION_AVAILABLE":
            raise ValueError("Documentation review availability state is invalid.")
        if self.decision_state != "USER_PREPARATION_DECISION_REQUIRED":
            raise ValueError("Documentation review decision state is invalid.")


@dataclass(frozen=True)
class ChannelIsolationDocumentationReview:
    plan_id: str
    plan_contract_fingerprint: str
    source_confirmation_id: str
    rows: tuple[ChannelIsolationDocumentationReviewRow, ...]
    user_action_state: str = "EXPLICIT_PREPARATION_REVISION_REQUIRED"

    def __post_init__(self):
        if self.user_action_state != "EXPLICIT_PREPARATION_REVISION_REQUIRED":
            raise ValueError("Documentation review user action is invalid.")


class ChannelIsolationDocumentationReviewService:
    """Relates complete documentation to prerequisites without deciding statuses."""

    PREREQUISITES = (
        "documented_microphone_position",
        "existing_acquisition_settings",
    )

    def __init__(self, record_previewer=None, preparation_resolver=None):
        self.record_previewer = (
            record_previewer or ChannelIsolationOperationalRecordPreviewService()
        )
        self.preparation_resolver = (
            preparation_resolver or EvidencePlanPreparationResolver()
        )

    def review(self, plan_id, microphone, settings, source_input, *, plans):
        if not isinstance(source_input, EvidencePlanPreparationConfirmationInput):
            raise TypeError("Documentation review requires a strict preparation draft.")
        record_preview = self.record_previewer.preview(
            plan_id, microphone, settings, plans=plans
        )
        if record_preview.status != "DOCUMENTATION_COMPLETE":
            raise ValueError("CHANNEL_ISOLATION_DOCUMENTATION_INCOMPLETE.")
        resolution = self.preparation_resolver.resolve(source_input, plans=plans)
        if resolution.plan.plan_id != plan_id:
            raise ValueError("Documentation review source plan identity is inconsistent.")
        if tuple(sorted(resolution.plan.required_inputs)) != self.PREREQUISITES:
            raise ValueError(
                "Documentation review requires the exact V1 prerequisite set."
            )
        return ChannelIsolationDocumentationReview(
            plan_id=resolution.plan.plan_id,
            plan_contract_fingerprint=source_input.plan_contract_fingerprint,
            source_confirmation_id=source_input.confirmation_id,
            rows=(
                ChannelIsolationDocumentationReviewRow(
                    prerequisite_code="documented_microphone_position",
                    documentation_record_id=(
                        record_preview.microphone_position.record_id
                    ),
                ),
                ChannelIsolationDocumentationReviewRow(
                    prerequisite_code="existing_acquisition_settings",
                    documentation_record_id=(
                        record_preview.acquisition_settings.record_id
                    ),
                ),
            ),
        )
