import json
from pathlib import Path

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionPlanContract,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    ExperimentDeclaration,
    ExperimentContractMode,
    ExperimentKind,
    PlanCoverageResult,
    PlanCoverageStatus,
)
from acousticbrain.persistence.measurement_repository import MeasurementRepository

from .experiment_declaration import ExperimentDeclarationService


class EvidenceAcquisitionPlanContractService:
    """Preserves a READY plan in an experiment manifest without executing it."""

    def __init__(self, repository=None, declaration_service=None):
        self.repository = repository or MeasurementRepository()
        self.declaration_service = declaration_service or ExperimentDeclarationService(
            self.repository
        )

    def declare(
        self, measurement_root, *, experiment_code, reference_experiment_code, plan,
        mode=ExperimentContractMode.EXPLORATORY,
        declaration_source="EXPLICIT_USER_OPERATION",
        user_note=None,
    ):
        if not isinstance(plan, EvidenceAcquisitionPlan):
            raise TypeError("EvidenceAcquisitionPlan is required.")
        if plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError("Only a READY evidence-acquisition plan can be declared.")
        mode = mode if isinstance(mode, ExperimentContractMode) else ExperimentContractMode(mode)
        if mode is ExperimentContractMode.PRESCRIPTIVE:
            raise ValueError("PRESCRIPTIVE mode requires a future scientific contract.")
        contract = EvidenceAcquisitionPlanContract(plan, mode, declaration_source)
        directory = Path(measurement_root) / experiment_code
        if not directory.is_dir():
            raise ValueError(f"Unknown experiment directory: {experiment_code}")
        manifest = self.repository.load_manifest(directory) or {}
        existing = manifest.get("evidence_acquisition_plan_contract")
        payload = self._payload(contract)
        if existing is not None and existing != payload:
            incompatible = ", ".join(
                self._incompatible_fields(existing, payload)
            )
            raise ValueError(
                "Experiment already preserves a different plan contract; "
                f"incompatible fields: {incompatible}."
            )
        repeat = plan.test_type is EvidenceAcquisitionTestType.REPEAT_MEASUREMENT
        self.declaration_service.declare(
            measurement_root,
            experiment_code=experiment_code,
            experiment_kind=(
                ExperimentKind.MEASUREMENT_REPEAT
                if repeat else ExperimentKind.CONTROLLED_INTERVENTION
            ),
            reference_experiment_code=reference_experiment_code,
            modified_variables=(
                (ExperimentDeclaration.ACQUISITION_VARIABLE,)
                if repeat else plan.independent_variables
            ),
            controlled_variables=plan.controlled_variables,
            user_note=user_note,
            provenance_source="EVIDENCE_ACQUISITION_PLAN_CONTRACT",
        )
        manifest = self.repository.load_manifest(directory) or {}
        manifest["source_evidence_acquisition_plan_id"] = plan.plan_id
        manifest["evidence_acquisition_plan_contract"] = payload
        self.repository.save_manifest(directory, manifest)
        return contract

    @staticmethod
    def _payload(contract):
        plan = contract.source_plan
        return json.loads(json.dumps({
            "schema_version": 1,
            "mode": contract.mode.value,
            "declaration_source": contract.declaration_source,
            "plan": plan.to_dict(),
        }, allow_nan=False))

    @classmethod
    def _incompatible_fields(cls, existing, requested, prefix=""):
        if isinstance(existing, dict) and isinstance(requested, dict):
            fields = []
            for key in sorted(set(existing) | set(requested)):
                path = f"{prefix}.{key}" if prefix else key
                if key not in existing or key not in requested:
                    fields.append(path)
                else:
                    fields.extend(cls._incompatible_fields(
                        existing[key], requested[key], path
                    ))
            return tuple(fields)
        return () if existing == requested else (prefix,)


class EvidenceAcquisitionPlanContractValidator:
    """Checks identity and complete semantic continuity, not execution results."""

    LIMITATION = (
        "Contract validation proves plan preservation only; execution and "
        "comparison validity remain separate decisions."
    )

    def validate(self, contract, resolved_plan):
        if resolved_plan is None:
            return self._result(
                PlanCoverageStatus.NOT_APPLICABLE,
                limitations=("Validation requires an exactly resolved plan.",),
            )
        if contract is None:
            return self._result(
                PlanCoverageStatus.INSUFFICIENT_DECLARATION,
                missing=("plan_contract:complete_snapshot",),
                limitations=(self.LIMITATION,),
            )
        if contract.source_plan != resolved_plan:
            return self._result(
                PlanCoverageStatus.PARTIAL,
                missing=("plan_contract:exact_source_match",),
                limitations=(self.LIMITATION,),
            )
        return self._result(
            PlanCoverageStatus.COMPLETE,
            covered=(
                "plan_contract:identity",
                "plan_contract:objective",
                "plan_contract:variables",
                "plan_contract:measurements",
                "plan_contract:observations",
                "plan_contract:criteria",
                "plan_contract:limitations",
                "plan_contract:prerequisites",
                "plan_contract:provenance",
                "plan_contract:mode",
            ),
            unverifiable=("execution_conformance", "comparison_validity"),
            limitations=(self.LIMITATION,),
        )

    @staticmethod
    def _result(status, *, covered=(), missing=(), unverifiable=(), limitations=()):
        return PlanCoverageResult(
            status=status,
            covered_requirements=tuple(sorted(covered)),
            missing_requirements=tuple(sorted(missing)),
            unverifiable_requirements=tuple(sorted(unverifiable)),
            limitations=tuple(sorted(limitations)),
        )
