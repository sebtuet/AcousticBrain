import argparse
from pathlib import Path

from acousticbrain.brain import AcousticBrain
from acousticbrain.report import ConsoleReporter


DEFAULT_MEASUREMENTS_ROOT = Path("measurements")


def create_parser():
    parser = argparse.ArgumentParser(description="Analyze an AcousticBrain campaign.")
    parser.add_argument(
        "--measurements-root",
        type=Path,
        default=DEFAULT_MEASUREMENTS_ROOT,
        metavar="PATH",
        help="campaign root directory (default: measurements)",
    )
    return parser


def validate_measurements_root(path):
    if not path.exists():
        raise ValueError(f"Measurements root does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Measurements root is not a directory: {path}")
    return path


def run(measurements_root, *, brain=None, reporter=None):
    brain = brain or AcousticBrain()
    reporter = reporter or ConsoleReporter()
    report = brain.analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )
    print(f"Measurement root: {measurements_root.resolve()}")
    print()
    reporter.print(report)
    return report


def main(argv=None, *, brain=None, reporter=None):
    parser = create_parser()
    arguments = parser.parse_args(argv)
    try:
        measurements_root = validate_measurements_root(arguments.measurements_root)
    except ValueError as error:
        parser.error(str(error))
    run(measurements_root, brain=brain, reporter=reporter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
