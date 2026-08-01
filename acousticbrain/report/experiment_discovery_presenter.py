from dataclasses import asdict, dataclass

from acousticbrain.application import (
    ChannelIsolationPlanCoverageValidator,
    ChannelIsolationPlanResultEvaluator,
    EvidenceAcquisitionPlanContractValidator,
)


@dataclass(frozen=True)
class PresentedCriterionEvaluation:
    criterion_id: str
    result_id: str
    evaluation_status: str
    reason_code: str


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
    plan_contract_preservation_status: str = "PLAN_COVERAGE_NOT_APPLICABLE"
    preserved_plan_contract_fields: tuple[str, ...] = ()
    missing_plan_contract_fields: tuple[str, ...] = ()
    unverifiable_plan_contract_fields: tuple[str, ...] = ()
    plan_contract_limitations: tuple[str, ...] = ()
    plan_result_evaluation_status: str = "PLAN_RESULT_NOT_APPLICABLE"
    criterion_evaluations: tuple[PresentedCriterionEvaluation, ...] = ()
    compatible_criteria: tuple[str, ...] = ()
    incompatible_criteria: tuple[str, ...] = ()
    unevaluable_criteria: tuple[str, ...] = ()
    missing_results: tuple[str, ...] = ()
    unused_results: tuple[str, ...] = ()
    plan_result_evaluation_limitations: tuple[str, ...] = ()


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
        contract_coverage = EvidenceAcquisitionPlanContractValidator().validate(
            item.evidence_acquisition_plan_contract,
            resolved_plan,
        )
        result_evaluation = ChannelIsolationPlanResultEvaluator().evaluate(
            item,
            resolved_plan,
        )
        criterion_evaluations = tuple(
            PresentedCriterionEvaluation(
                criterion_id=value.criterion_id,
                result_id=value.result_id,
                evaluation_status=value.evaluation_status.value,
                reason_code=value.reason_code.value,
            )
            for value in result_evaluation.criteria
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
            plan_contract_preservation_status=contract_coverage.status.value,
            preserved_plan_contract_fields=contract_coverage.covered_requirements,
            missing_plan_contract_fields=contract_coverage.missing_requirements,
            unverifiable_plan_contract_fields=(
                contract_coverage.unverifiable_requirements
            ),
            plan_contract_limitations=contract_coverage.limitations,
            plan_result_evaluation_status=result_evaluation.status.value,
            criterion_evaluations=criterion_evaluations,
            compatible_criteria=tuple(
                value.criterion_id
                for value in criterion_evaluations
                if value.evaluation_status == "COMPATIBLE"
            ),
            incompatible_criteria=tuple(
                value.criterion_id
                for value in criterion_evaluations
                if value.evaluation_status == "INCOMPATIBLE"
            ),
            unevaluable_criteria=tuple(
                value.criterion_id
                for value in criterion_evaluations
                if value.evaluation_status == "UNEVALUABLE"
            ),
            missing_results=result_evaluation.missing_results,
            unused_results=result_evaluation.unused_results,
            plan_result_evaluation_limitations=result_evaluation.limitations,
        )

    @staticmethod
    def _reference_status(source_plan_id, plans_by_id):
        if source_plan_id is None:
            return "PLAN_NOT_REFERENCED"
        if source_plan_id in plans_by_id:
            return "PLAN_REFERENCE_RESOLVED"
        return "PLAN_REFERENCE_UNKNOWN"
