import argparse

from acousticbrain.application import ExperimentDeclarationService
from acousticbrain.models import ExperimentKind


def parser():
    value = argparse.ArgumentParser(
        description="Declare an AcousticBrain experiment without modifying measurements."
    )
    value.add_argument("measurement_root")
    value.add_argument("experiment_code")
    value.add_argument("--kind", required=True, choices=[item.value for item in ExperimentKind])
    value.add_argument("--reference")
    value.add_argument("--modified-variable", action="append", default=[])
    value.add_argument("--controlled-variable", action="append", default=[])
    value.add_argument("--note")
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    declaration = ExperimentDeclarationService().declare(
        arguments.measurement_root,
        experiment_code=arguments.experiment_code,
        experiment_kind=arguments.kind,
        reference_experiment_code=arguments.reference,
        modified_variables=arguments.modified_variable,
        controlled_variables=arguments.controlled_variable,
        user_note=arguments.note,
    )
    print(
        f"Declared {arguments.experiment_code}: "
        f"{declaration.experiment_kind.value}"
    )


if __name__ == "__main__":
    main()
