import argparse
from pathlib import Path

from acousticbrain.application import EvidenceAcquisitionPlanContractService
from acousticbrain.brain import AcousticBrain
from acousticbrain.persistence import (
    EvidenceAcquisitionPlanContractJsonCodec,
    EvidencePlanCompletionRegistryJsonRepository,
)


def parser():
    value = argparse.ArgumentParser(
        description=(
            "Declare one READY evidence-acquisition plan while preserving its "
            "complete experimental contract."
        )
    )
    value.add_argument("measurement_root")
    value.add_argument("--plan-id", required=True)
    value.add_argument("--experiment", required=True)
    value.add_argument("--reference", required=True)
    value.add_argument(
        "--completion-registry",
        type=Path,
        help="optional derived evidence-plan completion registry JSON",
    )
    value.add_argument("--note")
    return value


def main(
    argv=None,
    *,
    brain=None,
    contract_service=None,
    completion_repository=None,
):
    arguments = parser().parse_args(argv)
    root = Path(arguments.measurement_root)
    if not (root / arguments.reference).is_dir():
        raise ValueError(f"Unknown reference experiment: {arguments.reference}")
    report = (brain or AcousticBrain()).analyze(
        measurement_root=root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
    )
    current_plans = tuple(
        EvidenceAcquisitionPlanContractJsonCodec.decode_plan(item.to_dict())
        for item in report.evidence_acquisition_plans.plans
    )
    derived_records = (
        (completion_repository or EvidencePlanCompletionRegistryJsonRepository())
        .load(arguments.completion_registry).records
        if arguments.completion_registry is not None
        else ()
    )
    matches = tuple(
        (item, None)
        for item in current_plans
        if item.plan_id == arguments.plan_id
    ) + tuple(
        (record.derived_plan.plan, record)
        for record in derived_records
        if record.derived_plan.plan.plan_id == arguments.plan_id
    )
    if len(matches) != 1 or matches[0][0].status.value != "READY":
        raise ValueError("The requested evidence-acquisition plan is not uniquely READY.")
    source, completion_record = matches[0]
    directory = root / arguments.experiment
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"Experiment path is not a directory: {arguments.experiment}")
    directory.mkdir(exist_ok=True)
    contract = EvidenceAcquisitionPlanContractJsonCodec().loads({
        "schema_version": 1,
        "mode": "EXPLORATORY",
        "declaration_source": (
            "RESOLVED_DERIVED_EVIDENCE_ACQUISITION_PLAN:"
            + completion_record.completion_input.completion_input_id
            if completion_record is not None
            else "RESOLVED_EVIDENCE_ACQUISITION_PLAN"
        ),
        "reference_experiment_code": arguments.reference,
        "declaration_user_note": arguments.note,
        "plan": EvidenceAcquisitionPlanContractJsonCodec.encode_plan(source),
    })
    (contract_service or EvidenceAcquisitionPlanContractService()).declare(
        root,
        experiment_code=arguments.experiment,
        reference_experiment_code=arguments.reference,
        plan=contract.source_plan,
        declaration_source=contract.declaration_source,
        user_note=arguments.note,
    )
    print(
        f"Declared {arguments.experiment} from evidence-acquisition plan "
        f"{arguments.plan_id}; complete contract preserved."
    )


if __name__ == "__main__":
    main()
