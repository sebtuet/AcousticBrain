import hashlib
import json

from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionStatus,
    EvidencePlanPreparationConfirmationInput,
    EvidencePlanPreparationResolution,
    EvidencePlanPreparationResolutionStatus,
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
