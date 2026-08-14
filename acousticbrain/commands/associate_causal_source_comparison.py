import argparse

from acousticbrain.application import CausalSourceComparisonAssociationService


def parser():
    value = argparse.ArgumentParser(
        description=(
            "Explicitly associate a local comparison with a supported causal "
            "protocol and hypothesis."
        )
    )
    value.add_argument("measurement_root")
    value.add_argument("experiment_code")
    value.add_argument("--protocol", required=True)
    value.add_argument("--hypothesis", required=True)
    value.add_argument("--reference")
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    association = CausalSourceComparisonAssociationService().associate(
        arguments.measurement_root,
        experiment_code=arguments.experiment_code,
        source_protocol_id=arguments.protocol,
        source_hypothesis_code=arguments.hypothesis,
        reference_experiment_code=arguments.reference,
    )
    print(
        f"Associated {association.parent_experiment_code} -> "
        f"{association.experiment_code}: {association.source_protocol_id} / "
        f"{association.source_hypothesis_code} / "
        f"{association.causal_step_code}"
    )


if __name__ == "__main__":
    main()
