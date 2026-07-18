import argparse
from pathlib import Path

from acousticbrain.brain import AcousticBrain
from acousticbrain.report import AcousticObservationConsoleReporter, ConsoleReporter
from acousticbrain.models import (
    CampaignReferenceDeclarationStatus,
    ListeningPositionCampaignInstanceStatus,
)
from acousticbrain.persistence import (
    CampaignReferenceQualificationJsonLoader,
    ListeningPositionCampaignInstanceJsonLoader,
)


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
    parser.add_argument(
        "--listening-position-campaign",
        type=Path,
        default=None,
        metavar="PATH",
        help="explicit versioned multi-position campaign instance JSON",
    )
    parser.add_argument(
        "--campaign-reference-qualification",
        type=Path,
        default=None,
        metavar="PATH",
        help="explicit versioned campaign reference qualification JSON",
    )
    parser.add_argument(
        "--observations",
        action="store_true",
        help="print the deterministic acoustic observation report",
    )
    return parser


def validate_measurements_root(path):
    if not path.exists():
        raise ValueError(f"Measurements root does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Measurements root is not a directory: {path}")
    return path


def validate_listening_position_campaign(path):
    if not path.exists():
        raise ValueError(f"Campaign instance does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Campaign instance is not a file: {path}")
    return path


def validate_campaign_reference_qualification(path):
    if not path.exists():
        raise ValueError(
            f"Campaign reference qualification does not exist: {path}"
        )
    if not path.is_file():
        raise ValueError(
            f"Campaign reference qualification is not a file: {path}"
        )
    return path


def run(
    measurements_root,
    *,
    campaign_instance_analysis=None,
    reference_qualification_declaration_analysis=None,
    observations=False,
    brain=None,
    reporter=None,
):
    brain = brain or AcousticBrain()
    reporter = reporter or (
        AcousticObservationConsoleReporter() if observations else ConsoleReporter()
    )
    arguments = dict(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )
    if observations:
        arguments["synthesize_observations"] = True
    if campaign_instance_analysis is not None:
        arguments["listening_position_campaign_instance_analysis"] = (
            campaign_instance_analysis
        )
    if reference_qualification_declaration_analysis is not None:
        arguments["campaign_reference_qualification_declaration_analysis"] = (
            reference_qualification_declaration_analysis
        )
    report = brain.analyze(**arguments)
    print(f"Measurement root: {measurements_root.resolve()}")
    print()
    reporter.print(report)
    return report


def main(
    argv=None,
    *,
    brain=None,
    reporter=None,
    campaign_loader=None,
    reference_qualification_loader=None,
):
    parser = create_parser()
    arguments = parser.parse_args(argv)
    try:
        measurements_root = validate_measurements_root(arguments.measurements_root)
        campaign_instance_analysis = None
        reference_qualification_declaration_analysis = None
        if arguments.listening_position_campaign is not None:
            campaign_path = validate_listening_position_campaign(
                arguments.listening_position_campaign
            )
            loader = campaign_loader or ListeningPositionCampaignInstanceJsonLoader()
            campaign_instance_analysis = loader.load(campaign_path)
            if (
                campaign_instance_analysis.status
                is ListeningPositionCampaignInstanceStatus.INVALID
            ):
                details = "; ".join(
                    f"{code}: {message}"
                    for code, message in zip(
                        campaign_instance_analysis.blocking_reasons,
                        campaign_instance_analysis.validation_messages,
                    )
                )
                raise ValueError(details)
        if arguments.campaign_reference_qualification is not None:
            qualification_path = validate_campaign_reference_qualification(
                arguments.campaign_reference_qualification
            )
            loader = (
                reference_qualification_loader
                or CampaignReferenceQualificationJsonLoader()
            )
            reference_qualification_declaration_analysis = loader.load(
                qualification_path
            )
            if (
                reference_qualification_declaration_analysis.status
                is CampaignReferenceDeclarationStatus.INVALID
            ):
                details = "; ".join(
                    f"{code}: {message}"
                    for code, message in zip(
                        reference_qualification_declaration_analysis.blocking_reasons,
                        reference_qualification_declaration_analysis.validation_messages,
                    )
                )
                raise ValueError(details)
    except ValueError as error:
        parser.error(str(error))
    run(
        measurements_root,
        campaign_instance_analysis=campaign_instance_analysis,
        reference_qualification_declaration_analysis=(
            reference_qualification_declaration_analysis
        ),
        observations=arguments.observations,
        brain=brain,
        reporter=reporter,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
