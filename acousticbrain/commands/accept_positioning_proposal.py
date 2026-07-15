import argparse
from pathlib import Path

from acousticbrain.application import PositioningProposalDeclarationService
from acousticbrain.brain import AcousticBrain


def parser():
    value = argparse.ArgumentParser(
        description=(
            "Accept one eligible PR-044 proposal and create its PR-043 declaration."
        )
    )
    value.add_argument("measurement_root")
    value.add_argument("--proposal-id", required=True)
    value.add_argument("--experiment", required=True)
    value.add_argument("--reference", required=True)
    value.add_argument("--note")
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    root = Path(arguments.measurement_root)
    reference = root / arguments.reference
    if not reference.is_dir():
        raise ValueError(f"Unknown reference experiment: {arguments.reference}")

    report = AcousticBrain().analyze(
        measurement_root=root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )
    analysis = report.loudspeaker_positioning_experiment
    proposal = analysis.proposal if analysis is not None else None
    if proposal is None or proposal.proposal_id != arguments.proposal_id:
        raise ValueError("The requested positioning proposal is not currently eligible.")

    directory = root / arguments.experiment
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"Experiment path is not a directory: {arguments.experiment}")
    directory.mkdir(exist_ok=True)
    declaration = PositioningProposalDeclarationService().declare(
        root,
        experiment_code=arguments.experiment,
        reference_experiment_code=arguments.reference,
        proposal=proposal,
        user_note=arguments.note,
    )
    print(
        f"Accepted {proposal.proposal_id}; declared {arguments.experiment}: "
        f"{declaration.experiment_kind.value}"
    )


if __name__ == "__main__":
    main()
