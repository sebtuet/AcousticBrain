from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedDiscoveredExperiment:
    experiment_id: str
    experiment_type: str
    state: str
    file_count: int
    timestamp: str
    available_channels: tuple[str, ...]
    source_evidence_acquisition_plan_id: str | None = None
    evidence_acquisition_plan_reference_status: str = "PLAN_NOT_REFERENCED"


@dataclass(frozen=True)
class PresentedExperimentDiscovery:
    experiments: tuple[PresentedDiscoveredExperiment, ...]

    def to_dict(self):
        return asdict(self)


class ExperimentDiscoveryPresenter:
    """Projection directe des descripteurs découverts."""

    def present(self, context):
        descriptors = getattr(context, "experiment_descriptors", ())
        if not descriptors:
            return None
        synthesis = getattr(
            context,
            "evidence_acquisition_plan_synthesis",
            None,
        )
        available_plan_ids = frozenset(
            plan.plan_id
            for plan in synthesis.plans
        ) if synthesis is not None else frozenset()
        return PresentedExperimentDiscovery(
            experiments=tuple(
                PresentedDiscoveredExperiment(
                    experiment_id=item.experiment_id,
                    experiment_type=item.experiment_type.value,
                    state=item.state.value,
                    file_count=len(item.available_files),
                    timestamp=item.timestamp,
                    available_channels=tuple(
                        channel.value for channel in item.available_channels
                    ),
                    source_evidence_acquisition_plan_id=(
                        item.source_evidence_acquisition_plan_id
                    ),
                    evidence_acquisition_plan_reference_status=(
                        self._reference_status(
                            item.source_evidence_acquisition_plan_id,
                            available_plan_ids,
                        )
                    ),
                )
                for item in descriptors
            )
        )

    @staticmethod
    def _reference_status(source_plan_id, available_plan_ids):
        if source_plan_id is None:
            return "PLAN_NOT_REFERENCED"
        if source_plan_id in available_plan_ids:
            return "PLAN_REFERENCE_RESOLVED"
        return "PLAN_REFERENCE_UNKNOWN"
