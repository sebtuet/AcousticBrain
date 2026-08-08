from dataclasses import dataclass
from pathlib import Path

from acousticbrain.models import EvidencePlanPreparationRegistry

from .channel_isolation_guided_execution import (
    ChannelIsolationGuidedExecutionService,
)


@dataclass(frozen=True)
class ChannelIsolationDeclarationReadiness:
    plan_id: str
    confirmation_id: str
    reference_experiment_id: str
    experiment_id: str
    statuses: tuple[str, ...] = (
        "PLAN_EXACTLY_RESOLVED",
        "PREPARATION_EXACTLY_RESOLVED",
        "ALL_PREREQUISITES_USER_CONFIRMED",
        "REFERENCE_EXACTLY_RESOLVED",
        "EXPERIMENT_TARGET_AVAILABLE",
        "DECLARATION_READY",
    )
    user_action_state: str = "DECLARE_EXPERIMENT_SEPARATELY"

    def __post_init__(self):
        if self.statuses[-1] != "DECLARATION_READY":
            raise ValueError("Channel-isolation declaration readiness is invalid.")
        if self.user_action_state != "DECLARE_EXPERIMENT_SEPARATELY":
            raise ValueError("Channel-isolation declaration action is invalid.")


class ChannelIsolationDeclarationReadinessService:
    """Qualifies exact declaration inputs without creating an experiment."""

    def __init__(self, journey_service=None):
        self.journey_service = journey_service or ChannelIsolationGuidedExecutionService()

    def qualify(
        self, measurement_root, plan_id, confirmation_id, reference_experiment_id,
        experiment_id, *, plans, registry,
    ):
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("EvidencePlanPreparationRegistry is required.")
        reference_experiment_id = self._identifier(
            reference_experiment_id, "reference experiment"
        )
        experiment_id = self._identifier(experiment_id, "experiment")
        if experiment_id == reference_experiment_id:
            raise ValueError("Experiment target must differ from its reference.")
        journey = self.journey_service.build(
            plan_id, confirmation_id, plans=plans, registry=registry
        )
        if journey.preparation_status != "PREPARATION_USER_CONFIRMED":
            raise ValueError("CHANNEL_ISOLATION_PREPARATION_INCOMPLETE.")
        root = Path(measurement_root)
        if not root.is_dir():
            raise ValueError("Channel-isolation measurement root is unavailable.")
        reference = root / reference_experiment_id
        if not reference.is_dir() or reference.resolve().parent != root.resolve():
            raise ValueError(
                f"CHANNEL_ISOLATION_REFERENCE_UNKNOWN: {reference_experiment_id}."
            )
        target = root / experiment_id
        if target.exists() or target.is_symlink():
            raise ValueError(
                f"CHANNEL_ISOLATION_EXPERIMENT_TARGET_EXISTS: {experiment_id}."
            )
        return ChannelIsolationDeclarationReadiness(
            plan_id=journey.plan.plan_id,
            confirmation_id=(
                journey.preparation_record.confirmation_input.confirmation_id
            ),
            reference_experiment_id=reference_experiment_id,
            experiment_id=experiment_id,
        )

    @staticmethod
    def _identifier(value, label):
        if (
            not isinstance(value, str)
            or not value
            or value != value.strip()
            or value in (".", "..")
            or "/" in value
            or "\\" in value
        ):
            raise ValueError(
                f"Channel-isolation {label} identifier must be exact safe text."
            )
        return value
