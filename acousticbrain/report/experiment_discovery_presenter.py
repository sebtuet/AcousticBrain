from dataclasses import asdict, dataclass

from acousticbrain.application import ChannelIsolationPlanCoverageValidator


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
    evidence_acquisition_plan_coverage_status: str = (
        "PLAN_COVERAGE_NOT_APPLICABLE"
    )
    covered_plan_requirements: tuple[str, ...] = ()
    missing_plan_requirements: tuple[str, ...] = ()
    unverifiable_plan_requirements: tuple[str, ...] = ()
    plan_coverage_limitations: tuple[str, ...] = ()


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
        plans_by_id = {
            plan.plan_id: plan
            for plan in synthesis.plans
        } if synthesis is not None else {}
        return PresentedExperimentDiscovery(
            experiments=tuple(
                self._present_experiment(item, plans_by_id)
                for item in descriptors
            )
        )

    def _present_experiment(self, item, plans_by_id):
        source_plan_id = item.source_evidence_acquisition_plan_id
        reference_status = self._reference_status(
            source_plan_id,
            plans_by_id,
        )
        resolved_plan = (
            plans_by_id[source_plan_id]
            if reference_status == "PLAN_REFERENCE_RESOLVED"
            else None
        )
        coverage = ChannelIsolationPlanCoverageValidator().validate(
            item,
            resolved_plan,
        )
        return PresentedDiscoveredExperiment(
            experiment_id=item.experiment_id,
            experiment_type=item.experiment_type.value,
            state=item.state.value,
            file_count=len(item.available_files),
            timestamp=item.timestamp,
            available_channels=tuple(
                channel.value for channel in item.available_channels
            ),
            source_evidence_acquisition_plan_id=source_plan_id,
            evidence_acquisition_plan_reference_status=reference_status,
            evidence_acquisition_plan_coverage_status=coverage.status.value,
            covered_plan_requirements=coverage.covered_requirements,
            missing_plan_requirements=coverage.missing_requirements,
            unverifiable_plan_requirements=coverage.unverifiable_requirements,
            plan_coverage_limitations=coverage.limitations,
        )

    @staticmethod
    def _reference_status(source_plan_id, plans_by_id):
        if source_plan_id is None:
            return "PLAN_NOT_REFERENCED"
        if source_plan_id in plans_by_id:
            return "PLAN_REFERENCE_RESOLVED"
        return "PLAN_REFERENCE_UNKNOWN"
