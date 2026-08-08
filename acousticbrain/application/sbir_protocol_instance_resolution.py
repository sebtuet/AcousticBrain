from acousticbrain.models import (
    EvidenceAcquisitionPlan,
    ExperimentDescriptor,
    GeometrySBIRCandidate,
    SBIRProtocolInstanceInput,
    SBIRProtocolInstanceResolution,
    SBIRProtocolInstanceResolutionDecision,
)

from .evidence_plan_preparation import evidence_acquisition_plan_fingerprint


class SBIRProtocolInstanceResolver:
    """Resolves exact existing identities without deciding compatibility."""

    def resolve(
        self,
        protocol_instance_input,
        *,
        plans,
        protocol_ids,
        experiments,
        geometry_candidates,
    ):
        if not isinstance(protocol_instance_input, SBIRProtocolInstanceInput):
            raise TypeError("SBIRProtocolInstanceInput is required.")

        plans = self._typed(plans, EvidenceAcquisitionPlan, "plans")
        source_plan = self._one(
            plans,
            key="plan_id",
            expected=protocol_instance_input.source_plan_id,
            unknown="SBIR_PROTOCOL_INSTANCE_PLAN_UNKNOWN",
            ambiguous="SBIR_PROTOCOL_INSTANCE_PLAN_AMBIGUOUS",
        )

        fingerprint = evidence_acquisition_plan_fingerprint(source_plan)
        if fingerprint != protocol_instance_input.source_plan_contract_fingerprint:
            raise ValueError(
                "SBIR_PROTOCOL_INSTANCE_PLAN_FINGERPRINT_MISMATCH: "
                f"{source_plan.plan_id}."
            )

        protocol_ids = self._protocol_ids(protocol_ids)
        protocol_id = self._one_value(
            protocol_ids,
            expected=protocol_instance_input.protocol_id,
            unknown="SBIR_PROTOCOL_INSTANCE_PROTOCOL_UNKNOWN",
            ambiguous="SBIR_PROTOCOL_INSTANCE_PROTOCOL_AMBIGUOUS",
        )

        experiments = self._typed(
            experiments,
            ExperimentDescriptor,
            "experiments",
        )
        reference = self._one(
            experiments,
            key="experiment_id",
            expected=protocol_instance_input.reference_experiment_id,
            unknown="SBIR_PROTOCOL_INSTANCE_REFERENCE_EXPERIMENT_UNKNOWN",
            ambiguous="SBIR_PROTOCOL_INSTANCE_REFERENCE_EXPERIMENT_AMBIGUOUS",
        )
        moved = self._one(
            experiments,
            key="experiment_id",
            expected=protocol_instance_input.moved_experiment_id,
            unknown="SBIR_PROTOCOL_INSTANCE_MOVED_EXPERIMENT_UNKNOWN",
            ambiguous="SBIR_PROTOCOL_INSTANCE_MOVED_EXPERIMENT_AMBIGUOUS",
        )

        geometry_candidates = self._typed(
            geometry_candidates,
            GeometrySBIRCandidate,
            "geometry candidates",
        )
        geometry_candidate = self._one(
            geometry_candidates,
            key="candidate_id",
            expected=protocol_instance_input.geometry_candidate_id,
            unknown="SBIR_PROTOCOL_INSTANCE_GEOMETRY_CANDIDATE_UNKNOWN",
            ambiguous="SBIR_PROTOCOL_INSTANCE_GEOMETRY_CANDIDATE_AMBIGUOUS",
        )

        return SBIRProtocolInstanceResolution(
            protocol_instance_input=protocol_instance_input,
            source_plan=source_plan,
            protocol_id=protocol_id,
            reference_experiment=reference,
            moved_experiment=moved,
            geometry_candidate=geometry_candidate,
            decisions=SBIRProtocolInstanceResolution.EXPECTED_DECISIONS,
        )

    @staticmethod
    def _typed(values, expected_type, label):
        if not isinstance(values, tuple):
            raise TypeError(
                f"SBIR protocol-instance {label} must be a typed tuple."
            )
        if any(not isinstance(value, expected_type) for value in values):
            raise TypeError(
                f"SBIR protocol-instance {label} contain an invalid object."
            )
        return values

    @staticmethod
    def _protocol_ids(values):
        if not isinstance(values, tuple):
            raise TypeError(
                "SBIR protocol-instance protocol ids must be a typed tuple."
            )
        if any(
            not isinstance(value, str)
            or not value
            or value != value.strip()
            for value in values
        ):
            raise TypeError(
                "SBIR protocol-instance protocol ids contain an invalid value."
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

    @staticmethod
    def _one_value(values, *, expected, unknown, ambiguous):
        matches = tuple(value for value in values if value == expected)
        if not matches:
            raise ValueError(f"{unknown}: {expected}.")
        if len(matches) != 1:
            raise ValueError(f"{ambiguous}: {expected}.")
        return matches[0]
