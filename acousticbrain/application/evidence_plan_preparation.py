import hashlib
import json
from dataclasses import dataclass

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidencePlanAllPrerequisitesStatus,
    EvidencePlanPreparationConfirmationInput,
    EvidencePlanPreparationDeclaration,
    EvidencePlanPreparationDeclarationStatus,
    EvidencePlanPreparationResolution,
    EvidencePlanPreparationResolutionStatus,
    EvidencePlanPreparationRecord,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteDeclaration,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.persistence.evidence_plan_preparation_registry_json import (
    EvidencePlanPreparationRegistryJsonRepository,
)


@dataclass(frozen=True)
class EvidencePlanPreparationWorkflowResult:
    record: EvidencePlanPreparationRecord
    registry_path: str
    persisted: bool


@dataclass(frozen=True)
class EvidencePlanPreparationPreviewResult:
    declaration: EvidencePlanPreparationDeclaration
    record: EvidencePlanPreparationRecord
    registry_state: str

    def __post_init__(self):
        if self.registry_state not in ("NOT_RECORDED", "ALREADY_RECORDED"):
            raise ValueError("Evidence-plan preparation preview state is invalid.")


class EvidencePlanPreparationPreviewService:
    """Projects declaration decisions and registry identity without writing."""

    def __init__(self, resolver=None, declarer=None):
        self.resolver = resolver or EvidencePlanPreparationResolver()
        self.declarer = declarer or EvidencePlanPreparationDeclarationService()

    def preview(self, confirmation_input, *, plans, registry):
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("EvidencePlanPreparationRegistry is required.")
        resolution = self.resolver.resolve(confirmation_input, plans=plans)
        declaration = self.declarer.declare(resolution)
        record = EvidencePlanPreparationRecord.from_declaration(declaration)
        updated = registry.with_record(record)
        return EvidencePlanPreparationPreviewResult(
            declaration=declaration,
            record=record,
            registry_state=(
                "ALREADY_RECORDED" if updated is registry else "NOT_RECORDED"
            ),
        )


@dataclass(frozen=True)
class GuidedEvidencePlanPreparationDraft:
    plan: EvidenceAcquisitionPlan
    confirmation_input: EvidencePlanPreparationConfirmationInput

    def __post_init__(self):
        if not isinstance(self.plan, EvidenceAcquisitionPlan):
            raise TypeError("Guided preparation draft requires an evidence plan.")
        if not isinstance(
            self.confirmation_input, EvidencePlanPreparationConfirmationInput
        ):
            raise TypeError("Guided preparation draft requires a typed input.")
        if self.plan.plan_id != self.confirmation_input.plan_id:
            raise ValueError("Guided preparation draft plan identity is inconsistent.")


class GuidedEvidencePlanPreparationDraftService:
    """Builds a safe UNKNOWN-only input draft without recording it."""

    DECLARATION_SOURCE = "GUIDED_USER_CONFIRMATION"

    def generate(self, plan_id, *, plans, registry):
        if not isinstance(plan_id, str) or not plan_id:
            raise ValueError("An exact evidence plan_id is required.")
        if not isinstance(plans, tuple) or any(
            not isinstance(value, EvidenceAcquisitionPlan) for value in plans
        ):
            raise TypeError("Guided preparation plans must be a typed tuple.")
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("EvidencePlanPreparationRegistry is required.")
        matches = tuple(value for value in plans if value.plan_id == plan_id)
        if not matches:
            raise ValueError(f"GUIDED_PREPARATION_PLAN_UNKNOWN: {plan_id}.")
        if len(matches) != 1:
            raise ValueError(f"GUIDED_PREPARATION_PLAN_AMBIGUOUS: {plan_id}.")
        plan = matches[0]
        if plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError(
                f"GUIDED_PREPARATION_PLAN_NOT_READY: {plan_id} is "
                f"{plan.status.value}."
            )
        fingerprint = evidence_acquisition_plan_fingerprint(plan)
        prefix = f"preparation-{fingerprint[:12]}-"
        existing = {
            value.confirmation_input.confirmation_id for value in registry.records
        }
        ordinal = 1
        while f"{prefix}{ordinal}" in existing:
            ordinal += 1
        confirmation_input = EvidencePlanPreparationConfirmationInput(
            schema_version=1,
            confirmation_id=f"{prefix}{ordinal}",
            plan_id=plan.plan_id,
            plan_contract_fingerprint=fingerprint,
            prerequisites=tuple(
                EvidencePlanPrerequisiteDeclaration(
                    code=code,
                    status=EvidencePlanPrerequisiteStatus.UNKNOWN,
                )
                for code in plan.required_inputs
            ),
            declaration_source=self.DECLARATION_SOURCE,
        )
        return GuidedEvidencePlanPreparationDraft(
            plan=plan,
            confirmation_input=confirmation_input,
        )


class GuidedEvidencePlanPreparationRevisionService:
    """Creates a new explicit-status draft without mutating its source."""

    def __init__(self, resolver=None):
        self.resolver = resolver or EvidencePlanPreparationResolver()

    def revise(self, source_input, statuses, *, plans, registry):
        if not isinstance(statuses, dict) or any(
            not isinstance(code, str)
            or not isinstance(status, EvidencePlanPrerequisiteStatus)
            for code, status in statuses.items()
        ):
            raise TypeError("Guided preparation statuses must be an exact typed map.")
        if not isinstance(registry, EvidencePlanPreparationRegistry):
            raise TypeError("EvidencePlanPreparationRegistry is required.")
        resolution = self.resolver.resolve(source_input, plans=plans)
        expected = set(resolution.plan.required_inputs)
        supplied = set(statuses)
        if expected != supplied:
            missing = tuple(sorted(expected - supplied))
            extra = tuple(sorted(supplied - expected))
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if extra:
                details.append("extra: " + ", ".join(extra))
            raise ValueError("GUIDED_PREPARATION_STATUS_SET_MISMATCH: " + "; ".join(details))
        fingerprint = source_input.plan_contract_fingerprint
        prefix = f"preparation-{fingerprint[:12]}-"
        unavailable = {
            source_input.confirmation_id,
            *(value.confirmation_input.confirmation_id for value in registry.records),
        }
        ordinal = 1
        while f"{prefix}{ordinal}" in unavailable:
            ordinal += 1
        revised = EvidencePlanPreparationConfirmationInput(
            schema_version=source_input.schema_version,
            confirmation_id=f"{prefix}{ordinal}",
            plan_id=source_input.plan_id,
            plan_contract_fingerprint=fingerprint,
            prerequisites=tuple(
                EvidencePlanPrerequisiteDeclaration(code=code, status=statuses[code])
                for code in resolution.plan.required_inputs
            ),
            declaration_source=source_input.declaration_source,
            user_note=source_input.user_note,
        )
        return GuidedEvidencePlanPreparationDraft(
            plan=resolution.plan,
            confirmation_input=revised,
        )


def evidence_acquisition_plan_fingerprint(plan):
    if not isinstance(plan, EvidenceAcquisitionPlan):
        raise TypeError("EvidenceAcquisitionPlan is required.")
    canonical = json.dumps(
        plan.to_dict(),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EvidencePlanPreparationResolver:
    """Resolves one exact READY plan without verifying user declarations."""

    def resolve(self, confirmation_input, *, plans):
        if not isinstance(
            confirmation_input,
            EvidencePlanPreparationConfirmationInput,
        ):
            raise TypeError(
                "EvidencePlanPreparationConfirmationInput is required."
            )
        if not isinstance(plans, tuple) or any(
            not isinstance(value, EvidenceAcquisitionPlan) for value in plans
        ):
            raise TypeError("Evidence-plan preparation plans must be a typed tuple.")
        matches = tuple(
            value for value in plans if value.plan_id == confirmation_input.plan_id
        )
        if not matches:
            raise ValueError(f"PREPARATION_PLAN_UNKNOWN: {confirmation_input.plan_id}.")
        if len(matches) != 1:
            raise ValueError(
                f"PREPARATION_PLAN_AMBIGUOUS: {confirmation_input.plan_id}."
            )
        plan = matches[0]
        if plan.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError(
                f"PREPARATION_PLAN_NOT_READY: {plan.plan_id} is {plan.status.value}."
            )
        fingerprint = evidence_acquisition_plan_fingerprint(plan)
        if fingerprint != confirmation_input.plan_contract_fingerprint:
            raise ValueError(
                f"PLAN_CONTRACT_FINGERPRINT_MISMATCH: {plan.plan_id}."
            )
        expected = set(plan.required_inputs)
        declared = {
            value.code for value in confirmation_input.prerequisites
        }
        if expected != declared:
            missing = tuple(sorted(expected - declared))
            extra = tuple(sorted(declared - expected))
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if extra:
                details.append("extra: " + ", ".join(extra))
            raise ValueError(
                "PREREQUISITE_SET_MISMATCH: " + "; ".join(details) + "."
            )
        return EvidencePlanPreparationResolution(
            confirmation_input=confirmation_input,
            plan=plan,
            status=(
                EvidencePlanPreparationResolutionStatus.PLAN_EXACTLY_RESOLVED
            ),
        )


class EvidencePlanPreparationDeclarationService:
    """Records user statuses as declarations, never as independent proof."""

    def declare(self, resolution):
        if not isinstance(resolution, EvidencePlanPreparationResolution):
            raise TypeError("EvidencePlanPreparationResolution is required.")
        all_confirmed = all(
            value.status.value == "CONFIRMED"
            for value in resolution.confirmation_input.prerequisites
        )
        return EvidencePlanPreparationDeclaration(
            resolution=resolution,
            declaration_status=(
                EvidencePlanPreparationDeclarationStatus.PREPARATION_DECLARED
            ),
            all_prerequisites_status=(
                EvidencePlanAllPrerequisitesStatus.ALL_PREREQUISITES_USER_CONFIRMED
                if all_confirmed
                else None
            ),
        )


class EvidencePlanPreparationWorkflowService:
    """Resolves, declares and atomically records one preparation input."""

    def __init__(self, resolver=None, declarer=None, repository=None):
        self.resolver = resolver or EvidencePlanPreparationResolver()
        self.declarer = declarer or EvidencePlanPreparationDeclarationService()
        self.repository = (
            repository or EvidencePlanPreparationRegistryJsonRepository()
        )

    def record(self, confirmation_input, *, registry_path, plans):
        resolution = self.resolver.resolve(confirmation_input, plans=plans)
        declaration = self.declarer.declare(resolution)
        record = EvidencePlanPreparationRecord.from_declaration(declaration)
        registry = self.repository.load(registry_path)
        updated = registry.with_record(record)
        persisted = self.repository.save(registry_path, updated)
        return EvidencePlanPreparationWorkflowResult(
            record=record,
            registry_path=str(registry_path),
            persisted=persisted,
        )
