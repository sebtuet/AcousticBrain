import argparse

from acousticbrain.application import CausalProtocolStepDeclarationService


def parser():
    value = argparse.ArgumentParser(
        description=(
            "Declare an executed causal protocol step without inferring an observation."
        )
    )
    value.add_argument("measurement_root")
    value.add_argument("experiment_code")
    value.add_argument("--protocol", required=True)
    value.add_argument("--step", required=True)
    value.add_argument("--step-index", type=int)
    value.add_argument("--changed-variable", action="append", default=[])
    value.add_argument("--controlled-variable", action="append", default=[])
    value.add_argument("--unknown-variable", action="append", default=[])
    value.add_argument("--observation", action="append", default=[])
    value.add_argument("--note")
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    step = CausalProtocolStepDeclarationService().declare(
        arguments.measurement_root,
        experiment_code=arguments.experiment_code,
        protocol_code=arguments.protocol,
        step_code=arguments.step,
        step_index=arguments.step_index,
        changed_variable_codes=arguments.changed_variable,
        controlled_variable_codes=arguments.controlled_variable,
        unknown_variable_codes=arguments.unknown_variable,
        observation_codes=arguments.observation,
        user_note=arguments.note,
    )
    print(
        f"Declared {arguments.experiment_code}: {step.protocol_code} / "
        f"{step.step_code}; observations replaced: {len(step.observation_codes)}"
    )


if __name__ == "__main__":
    main()
