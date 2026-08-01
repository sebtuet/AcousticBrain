import argparse
from pathlib import Path

from acousticbrain.application import EvidenceAcquisitionPlanContractService
from acousticbrain.brain import AcousticBrain
from acousticbrain.persistence import EvidenceAcquisitionPlanContractJsonCodec


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
    value.add_argument("--note")
    return value


def main(argv=None, *, brain=None, contract_service=None):
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
    plans = tuple(
        item for item in report.evidence_acquisition_plans.plans
        if item.plan_id == arguments.plan_id
    )
    if len(plans) != 1 or plans[0].status != "READY":
        raise ValueError("The requested evidence-acquisition plan is not uniquely READY.")
    directory = root / arguments.experiment
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"Experiment path is not a directory: {arguments.experiment}")
    directory.mkdir(exist_ok=True)
    presented = plans[0]
    contract = EvidenceAcquisitionPlanContractJsonCodec().loads({
        "schema_version": 1,
        "mode": "EXPLORATORY",
        "declaration_source": "RESOLVED_EVIDENCE_ACQUISITION_PLAN",
        "reference_experiment_code": arguments.reference,
        "declaration_user_note": arguments.note,
        "plan": presented.to_dict(),
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
