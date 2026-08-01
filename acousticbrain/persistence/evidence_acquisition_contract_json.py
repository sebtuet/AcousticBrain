from decimal import Decimal

from acousticbrain.models import (
    ChannelIsolationCriterionOperator,
    ChannelIsolationEvaluationCriterion,
    EvidenceAcquisitionEffort,
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionPlanContract,
    EvidenceAcquisitionPriority,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    ExperimentContractMode,
)


class EvidenceAcquisitionPlanContractJsonCodec:
    SCHEMA_VERSION = 1

    def loads(self, value):
        if value is None:
            return None
        if not isinstance(value, dict) or value.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("Invalid evidence-acquisition plan contract.")
        raw = value.get("plan")
        if not isinstance(raw, dict):
            raise ValueError("Evidence-acquisition plan contract requires a plan.")
        try:
            plan = self.decode_plan(raw)
            return EvidenceAcquisitionPlanContract(
                source_plan=plan,
                mode=ExperimentContractMode(value["mode"]),
                declaration_source=value["declaration_source"],
                reference_experiment_code=value["reference_experiment_code"],
                declaration_user_note=value.get("declaration_user_note"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Invalid evidence-acquisition plan contract.") from error

    @classmethod
    def decode_plan(cls, raw):
        if not isinstance(raw, dict):
            raise ValueError("Evidence-acquisition plan must be an object.")
        return EvidenceAcquisitionPlan(
                plan_id=raw["plan_id"], reasoning_id=raw["reasoning_id"],
                corrective_action_id=raw["corrective_action_id"],
                evidence_weight_id=raw["evidence_weight_id"],
                blocking_factor_ids=cls._strings(raw, "blocking_factor_ids"),
                objective=raw["objective"],
                test_type=EvidenceAcquisitionTestType(raw["test_type"]),
                instructions=cls._strings(raw, "instructions"),
                required_inputs=cls._strings(raw, "required_inputs"),
                controlled_variables=cls._strings(raw, "controlled_variables"),
                independent_variables=cls._strings(raw, "independent_variables"),
                measurements_to_capture=cls._strings(raw, "measurements_to_capture"),
                expected_observations=cls._strings(raw, "expected_observations"),
                success_criteria=cls._strings(raw, "success_criteria"),
                failure_criteria=cls._strings(raw, "failure_criteria"),
                resulting_evidence_targets=cls._strings(raw, "resulting_evidence_targets"),
                priority=EvidenceAcquisitionPriority(raw["priority"]),
                estimated_effort=EvidenceAcquisitionEffort(raw["estimated_effort"]),
                status=EvidenceAcquisitionStatus(raw["status"]),
                limitations=cls._strings(raw, "limitations"),
                channel_isolation_evaluation_criteria=tuple(
                    cls._criterion(item)
                    for item in raw.get("channel_isolation_evaluation_criteria", ())
                ),
            )

    @staticmethod
    def encode_plan(plan):
        if not isinstance(plan, EvidenceAcquisitionPlan):
            raise TypeError("Evidence-acquisition plan is required.")
        value = plan.to_dict()
        return {
            key: list(item) if isinstance(item, tuple) else item
            for key, item in value.items()
        }

    @staticmethod
    def _strings(raw, field):
        value = raw.get(field, ())
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"Plan field {field} must be a collection.")
        return tuple(value)

    @staticmethod
    def _criterion(raw):
        if not isinstance(raw, dict):
            raise ValueError("Invalid channel-isolation criterion.")
        return ChannelIsolationEvaluationCriterion(
            criterion_id=raw["criterion_id"], result_id=raw["result_id"],
            operator=ChannelIsolationCriterionOperator(raw["operator"]),
            expected_value=Decimal(raw["expected_value"]), unit=raw["unit"],
            tolerance=(Decimal(raw["tolerance"])
                       if raw.get("tolerance") is not None else None),
        )
