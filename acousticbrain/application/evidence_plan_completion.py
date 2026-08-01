from dataclasses import asdict, dataclass, replace
import hashlib
import json

from acousticbrain.models import (
    DeterministicCorrectiveAction,
    DerivedEvidenceAcquisitionPlan,
    DerivedEvidencePlanStatus,
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidenceBlockingFactor,
    EvidencePlanCompletionCompatibility,
    EvidencePlanCompletionCompatibilityStatus,
    EvidencePlanCompletionInput,
    EvidencePlanCompletionReferenceKind,
    EvidencePlanCompletionRecord,
    EvidencePlanCompletionResolution,
    EvidencePlanCompletionResolutionStatus,
    ListeningPositionSamplingProtocol,
)
from acousticbrain.persistence.evidence_plan_completion_registry_json import (
    EvidencePlanCompletionRegistryJsonRepository,
)


@dataclass(frozen=True)
class EvidencePlanCompletionWorkflowResult:
    record: EvidencePlanCompletionRecord
    registry_path: str
    persisted: bool


class EvidencePlanCompletionService:
    """Completes and atomically records one exact V1 derivation."""

    def __init__(
        self,
        resolver=None,
        validator=None,
        factory=None,
        repository=None,
    ):
        self.resolver = resolver or EvidencePlanCompletionReferenceResolver()
        self.validator = validator or EvidencePlanCompletionCompatibilityValidator()
        self.factory = factory or DerivedEvidenceAcquisitionPlanFactory()
        self.repository = repository or EvidencePlanCompletionRegistryJsonRepository()

    def complete(
        self,
        completion_input,
        *,
        registry_path,
        source_plans,
        blocking_factors,
        actions,
        protocol_references=(),
        plan_references=(),
    ):
        resolution = self.resolver.resolve(
            completion_input,
            source_plans=source_plans,
            blocking_factors=blocking_factors,
            protocol_references=protocol_references,
            plan_references=plan_references,
        )
        compatibility = self.validator.validate(resolution, actions=actions)
        derived = self.factory.create(compatibility)
        record = EvidencePlanCompletionRecord(
            completion_input=completion_input,
            resolution_status=resolution.status,
            compatibility_status=compatibility.status,
            derived_plan=derived,
        )
        registry = self.repository.load(registry_path)
        updated = registry.with_record(record)
        persisted = self.repository.save(registry_path, updated)
        return EvidencePlanCompletionWorkflowResult(
            record=record,
            registry_path=str(registry_path),
            persisted=persisted,
        )


class EvidencePlanCompletionReferenceResolver:
    """Resolves V1 identities without deciding compatibility or readiness."""

    MISSING_INPUT = "compatible_protocol_or_plan_id"

    def resolve(
        self,
        completion_input,
        *,
        source_plans,
        blocking_factors,
        protocol_references=(),
        plan_references=(),
    ):
        if not isinstance(completion_input, EvidencePlanCompletionInput):
            raise TypeError("EvidencePlanCompletionInput is required.")
        source_plans = self._typed(
            source_plans,
            EvidenceAcquisitionPlan,
            "source plans",
        )
        blocking_factors = self._typed(
            blocking_factors,
            EvidenceBlockingFactor,
            "blocking factors",
        )
        protocols = self._typed(
            protocol_references,
            ListeningPositionSamplingProtocol,
            "protocol references",
        )
        plans = self._typed(
            plan_references,
            EvidenceAcquisitionPlan,
            "plan references",
        )

        source = self._one(
            source_plans,
            key="plan_id",
            expected=completion_input.source_plan_id,
            unknown="SOURCE_PLAN_UNKNOWN",
            ambiguous="SOURCE_PLAN_AMBIGUOUS",
        )
        self._validate_source(source, blocking_factors)

        if (
            completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
        ):
            references = protocols
            key = "protocol_id"
        else:
            references = plans
            key = "plan_id"
        reference = self._one(
            references,
            key=key,
            expected=completion_input.reference_id,
            unknown="REFERENCE_UNKNOWN",
            ambiguous="REFERENCE_AMBIGUOUS",
        )
        if (
            completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PLAN
            and reference.plan_id == source.plan_id
        ):
            raise ValueError(
                f"REFERENCE_SELF_REFERENCE: {source.plan_id} cannot reference itself."
            )
        return EvidencePlanCompletionResolution(
            completion_input=completion_input,
            source_plan=source,
            reference=reference,
            status=(
                EvidencePlanCompletionResolutionStatus.REFERENCE_RESOLVED
            ),
        )

    def _validate_source(self, source, blocking_factors):
        if source.status is not EvidenceAcquisitionStatus.BLOCKED:
            raise ValueError(
                f"SOURCE_PLAN_NOT_BLOCKED: {source.plan_id} is {source.status.value}."
            )
        matching = tuple(
            factor
            for factor in blocking_factors
            if factor.factor_id in source.blocking_factor_ids
        )
        matched_ids = tuple(factor.factor_id for factor in matching)
        if (
            len(matched_ids) != len(set(matched_ids))
            or set(matched_ids) != set(source.blocking_factor_ids)
        ):
            raise ValueError(
                "SOURCE_PLAN_NOT_V1_COMPLETABLE: blocking-factor identity is "
                f"not exactly resolved for {source.plan_id}."
            )
        completable = tuple(
            factor
            for factor in matching
            if factor.code == "MISSING_PARAMETERS"
            and factor.source_object_ids == (self.MISSING_INPUT,)
        )
        if len(completable) != 1:
            raise ValueError(
                "SOURCE_PLAN_NOT_V1_COMPLETABLE: "
                f"{source.plan_id} is not blocked only by {self.MISSING_INPUT}."
            )
        if len(matching) != 1:
            raise ValueError(
                "SOURCE_PLAN_HAS_OTHER_BLOCKERS: "
                f"{source.plan_id} retains other blocking factors."
            )
        if self.MISSING_INPUT not in source.required_inputs:
            raise ValueError(
                "SOURCE_PLAN_NOT_V1_COMPLETABLE: "
                f"{source.plan_id} does not require {self.MISSING_INPUT}."
            )

    @staticmethod
    def _typed(values, expected_type, label):
        if not isinstance(values, tuple):
            raise TypeError(f"Evidence-plan completion {label} must be a tuple.")
        if any(not isinstance(value, expected_type) for value in values):
            raise TypeError(
                f"Evidence-plan completion {label} contain an invalid object."
            )
        return values

    @staticmethod
    def _one(values, *, key, expected, unknown, ambiguous):
        matches = tuple(
            value for value in values if getattr(value, key) == expected
        )
        if not matches:
            raise ValueError(f"{unknown}: {expected}.")
        if len(matches) != 1:
            raise ValueError(f"{ambiguous}: {expected}.")
        return matches[0]


class EvidencePlanCompletionCompatibilityValidator:
    """Uses existing action associations without inferring compatibility."""

    AUTHORITY_ID = EvidencePlanCompletionCompatibility.AUTHORITY_ID
    AUTHORITY_VERSION = EvidencePlanCompletionCompatibility.AUTHORITY_VERSION

    def validate(self, resolution, *, actions):
        if not isinstance(resolution, EvidencePlanCompletionResolution):
            raise TypeError("EvidencePlanCompletionResolution is required.")
        actions = EvidencePlanCompletionReferenceResolver._typed(
            actions,
            DeterministicCorrectiveAction,
            "corrective actions",
        )
        action = EvidencePlanCompletionReferenceResolver._one(
            actions,
            key="action_id",
            expected=resolution.source_plan.corrective_action_id,
            unknown="SOURCE_ACTION_UNKNOWN",
            ambiguous="SOURCE_ACTION_AMBIGUOUS",
        )
        if resolution.source_plan.reasoning_id not in action.source_reasoning_ids:
            raise ValueError(
                "REFERENCE_COMPATIBILITY_NOT_ESTABLISHED: source reasoning "
                f"is inconsistent for {resolution.source_plan.plan_id}."
            )
        completion_input = resolution.completion_input
        compatible_ids = (
            action.compatible_protocol_ids
            if completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
            else action.compatible_plan_ids
        )
        if completion_input.reference_id not in compatible_ids:
            raise ValueError(
                "REFERENCE_COMPATIBILITY_NOT_ESTABLISHED: "
                f"{completion_input.reference_kind.value} "
                f"{completion_input.reference_id} is not associated with "
                f"action {action.action_id}."
            )
        return EvidencePlanCompletionCompatibility(
            resolution=resolution,
            source_action=action,
            authority_id=self.AUTHORITY_ID,
            authority_version=self.AUTHORITY_VERSION,
            status=(
                EvidencePlanCompletionCompatibilityStatus.REFERENCE_COMPATIBLE
            ),
        )


class DerivedEvidenceAcquisitionPlanFactory:
    """Creates one immutable READY derivation without persistence or execution."""

    def create(self, compatibility):
        if not isinstance(compatibility, EvidencePlanCompletionCompatibility):
            raise TypeError("EvidencePlanCompletionCompatibility is required.")
        resolution = compatibility.resolution
        source = resolution.source_plan
        completion_input = resolution.completion_input
        reference = resolution.reference
        parameters = self._reference_parameters(reference, completion_input)
        reference_fingerprint = self._reference_fingerprint(
            reference,
            completion_input.reference_kind,
        )
        plan_id = self._plan_id(compatibility)
        required_inputs = tuple(sorted((
            *(
                value for value in source.required_inputs
                if value != DerivedEvidenceAcquisitionPlan.MISSING_INPUT
            ),
            (
                f"resolved_reference:{completion_input.reference_kind.value}:"
                f"{completion_input.reference_id}"
            ),
        )))
        derived = replace(
            source,
            plan_id=plan_id,
            required_inputs=required_inputs,
            status=EvidenceAcquisitionStatus.READY,
        )
        return DerivedEvidenceAcquisitionPlan(
            plan=derived,
            source_plan=source,
            source_plan_id=source.plan_id,
            completion_input_id=completion_input.completion_input_id,
            reference_kind=completion_input.reference_kind,
            reference_id=completion_input.reference_id,
            compatibility_authority_id=compatibility.authority_id,
            compatibility_authority_version=compatibility.authority_version,
            reference_parameter_codes=parameters,
            reference_contract_fingerprint=reference_fingerprint,
            contract_id=DerivedEvidenceAcquisitionPlan.CONTRACT_ID,
            contract_version=DerivedEvidenceAcquisitionPlan.CONTRACT_VERSION,
            status=DerivedEvidencePlanStatus.DERIVED_PLAN_READY,
        )

    @staticmethod
    def _reference_parameters(reference, completion_input):
        if (
            completion_input.reference_kind
            is EvidencePlanCompletionReferenceKind.PROTOCOL
        ):
            completeness = reference.definition_completeness
            if not completeness.complete:
                raise ValueError(
                    "REFERENCE_CONTRACT_INCOMPLETE: "
                    f"{reference.protocol_id} is missing "
                    + ", ".join(completeness.missing_condition_codes)
                    + "."
                )
            values = {
                f"protocol_version:{reference.version}",
                f"comparability_rule:{reference.comparability_rule_code}",
            }
            values.update(
                "position:"
                f"{value.position_code}:"
                f"role={value.position_role}:"
                f"longitudinal_m={value.longitudinal_offset_m}:"
                f"lateral_m={value.lateral_offset_m}:"
                f"vertical_m={value.vertical_offset_m}:"
                f"parent={value.parent_position_code}:"
                f"reference={value.reference_position_code}:"
                f"order={value.acquisition_order}"
                for value in reference.positions
            )
            values.update(
                f"position_measurement:{position.position_code}:{measurement}"
                for position in reference.positions
                for measurement in position.required_measurements
            )
            values.update(
                f"modified_variable:{value}"
                for value in reference.modified_variables
            )
            values.update(
                f"controlled_variable:{value}"
                for value in reference.controlled_variables
            )
            values.update(
                f"completion_condition:{value}"
                for value in reference.completion_condition_codes
            )
            return tuple(sorted(values))
        if reference.status is not EvidenceAcquisitionStatus.READY:
            raise ValueError(
                "REFERENCE_CONTRACT_INCOMPLETE: "
                f"{reference.plan_id} is {reference.status.value}."
            )
        return tuple(sorted((
            f"plan_status:{reference.status.value}",
            f"plan_test_type:{reference.test_type.value}",
            *(f"required_input:{value}" for value in reference.required_inputs),
            *(
                f"controlled_variable:{value}"
                for value in reference.controlled_variables
            ),
            *(
                f"independent_variable:{value}"
                for value in reference.independent_variables
            ),
            *(
                f"measurement:{value}"
                for value in reference.measurements_to_capture
            ),
        )))

    @staticmethod
    def _reference_snapshot(reference, reference_kind):
        return (
            asdict(reference)
            if reference_kind is EvidencePlanCompletionReferenceKind.PROTOCOL
            else reference.to_dict()
        )

    @classmethod
    def _reference_fingerprint(cls, reference, reference_kind):
        canonical = json.dumps(
            cls._reference_snapshot(reference, reference_kind),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _plan_id(compatibility):
        resolution = compatibility.resolution
        completion_input = resolution.completion_input
        reference = resolution.reference
        reference_snapshot = DerivedEvidenceAcquisitionPlanFactory._reference_snapshot(
            reference,
            completion_input.reference_kind,
        )
        payload = {
            "contract_id": DerivedEvidenceAcquisitionPlan.CONTRACT_ID,
            "contract_version": DerivedEvidenceAcquisitionPlan.CONTRACT_VERSION,
            "source_plan": resolution.source_plan.to_dict(),
            "completion_input": {
                "schema_version": completion_input.schema_version,
                "completion_input_id": completion_input.completion_input_id,
                "source_plan_id": completion_input.source_plan_id,
                "reference_kind": completion_input.reference_kind.value,
                "reference_id": completion_input.reference_id,
                "declaration_source": completion_input.declaration_source,
                "user_note": completion_input.user_note,
            },
            "reference": reference_snapshot,
            "compatibility_authority_id": compatibility.authority_id,
            "compatibility_authority_version": compatibility.authority_version,
        }
        canonical = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
        return f"DERIVED_EVIDENCE_ACQUISITION_{digest}"
