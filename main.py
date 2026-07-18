import argparse
import os
from pathlib import Path

from acousticbrain.advisor import (
    AdvisorConfigurationError,
    AdvisorError,
    AdvisorService,
    MockAdvisorProvider,
    OllamaAdvisorProvider,
    OpenAIAdvisorProvider,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.report import (
    AcousticObservationConsoleReporter,
    ConsoleReporter,
    DeterministicAcousticReasoningConsoleReporter,
    DeterministicCorrectiveActionConsoleReporter,
    DeterministicEvidenceWeightingConsoleReporter,
    EvidenceAcquisitionPlanConsoleReporter,
    AdvisorConsoleReporter,
)
from acousticbrain.models import (
    AdvisorAudience,
    AdvisorDetailLevel,
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
    parser.add_argument(
        "--reasoning",
        action="store_true",
        help="print the deterministic acoustic reasoning report",
    )
    parser.add_argument(
        "--actions",
        action="store_true",
        help="print the deterministic corrective-action report",
    )
    parser.add_argument(
        "--weighting",
        action="store_true",
        help="print the deterministic multidimensional evidence weighting report",
    )
    parser.add_argument(
        "--evidence-acquisition",
        action="store_true",
        help="print deterministic plans for acquiring missing evidence",
    )
    parser.add_argument("--advisor", action="store_true", help="enable the optional read-only advisor")
    parser.add_argument("--question", default=None, help="question for the enabled advisor")
    parser.add_argument(
        "--advisor-provider",
        choices=("mock", "ollama", "openai"),
        default="mock",
    )
    parser.add_argument(
        "--advisor-audience",
        choices=tuple(value.value for value in AdvisorAudience),
        default=AdvisorAudience.GENERAL.value,
    )
    parser.add_argument(
        "--advisor-detail",
        choices=tuple(value.value for value in AdvisorDetailLevel),
        default=AdvisorDetailLevel.STANDARD.value,
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
    reasoning=False,
    actions=False,
    weighting=False,
    evidence_acquisition=False,
    advisor=False,
    question=None,
    advisor_audience=AdvisorAudience.GENERAL,
    advisor_detail_level=AdvisorDetailLevel.STANDARD,
    advisor_provider=None,
    advisor_service=None,
    brain=None,
    reporter=None,
):
    brain = brain or AcousticBrain()
    reporter = reporter or (
        AdvisorConsoleReporter()
        if advisor
        else EvidenceAcquisitionPlanConsoleReporter()
        if evidence_acquisition
        else DeterministicEvidenceWeightingConsoleReporter()
        if weighting
        else DeterministicCorrectiveActionConsoleReporter()
        if actions
        else DeterministicAcousticReasoningConsoleReporter()
        if reasoning
        else AcousticObservationConsoleReporter()
        if observations
        else ConsoleReporter()
    )
    arguments = dict(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )
    if observations:
        arguments["synthesize_observations"] = True
    if reasoning:
        arguments["synthesize_reasoning"] = True
    if actions:
        arguments["synthesize_actions"] = True
    if weighting:
        arguments["synthesize_weighting"] = True
    if evidence_acquisition:
        arguments["synthesize_evidence_acquisition"] = True
    if advisor:
        if evidence_acquisition:
            arguments["synthesize_evidence_acquisition"] = True
        else:
            arguments["synthesize_weighting"] = True
    if campaign_instance_analysis is not None:
        arguments["listening_position_campaign_instance_analysis"] = (
            campaign_instance_analysis
        )
    if reference_qualification_declaration_analysis is not None:
        arguments["campaign_reference_qualification_declaration_analysis"] = (
            reference_qualification_declaration_analysis
        )
    report = brain.analyze(**arguments)
    if advisor:
        report.advisor_response = (advisor_service or AdvisorService()).advise(
            report,
            question=question,
            audience=advisor_audience,
            detail_level=advisor_detail_level,
            provider=advisor_provider,
        )
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
    advisor_provider_instance=None,
    advisor_service=None,
):
    parser = create_parser()
    arguments = parser.parse_args(argv)
    try:
        measurements_root = validate_measurements_root(arguments.measurements_root)
        if arguments.question is not None and not arguments.advisor:
            raise ValueError("--question requires --advisor.")
        if arguments.advisor and not arguments.question:
            raise ValueError("--advisor requires --question.")
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
    try:
        run(
            measurements_root,
            campaign_instance_analysis=campaign_instance_analysis,
            reference_qualification_declaration_analysis=(
                reference_qualification_declaration_analysis
            ),
            observations=arguments.observations,
            reasoning=arguments.reasoning,
            actions=arguments.actions,
            weighting=arguments.weighting,
            evidence_acquisition=arguments.evidence_acquisition,
            advisor=arguments.advisor,
            question=arguments.question,
            advisor_audience=AdvisorAudience(arguments.advisor_audience),
            advisor_detail_level=AdvisorDetailLevel(arguments.advisor_detail),
            advisor_provider=(
                advisor_provider_instance
                if advisor_provider_instance is not None
                else create_advisor_provider(arguments.advisor_provider)
                if arguments.advisor
                else None
            ),
            advisor_service=advisor_service,
            brain=brain,
            reporter=reporter,
        )
    except AdvisorError as error:
        parser.error(str(error))
    return 0


def create_advisor_provider(provider_id):
    try:
        timeout = float(os.environ.get("ADVISOR_TIMEOUT_SECONDS", "30"))
    except ValueError as error:
        raise AdvisorConfigurationError(
            "ADVISOR_TIMEOUT_SECONDS must be numeric."
        ) from error
    if provider_id == "mock":
        return MockAdvisorProvider()
    if provider_id == "ollama":
        return OllamaAdvisorProvider(
            endpoint=os.environ.get("OLLAMA_ADVISOR_ENDPOINT"),
            model_id=os.environ.get("OLLAMA_ADVISOR_MODEL"),
            timeout_seconds=timeout,
        )
    if provider_id == "openai":
        return OpenAIAdvisorProvider(
            api_key=os.environ.get("OPENAI_API_KEY"),
            endpoint=os.environ.get(
                "OPENAI_ADVISOR_ENDPOINT", "https://api.openai.com/v1/responses"
            ),
            model_id=os.environ.get("OPENAI_ADVISOR_MODEL"),
            timeout_seconds=timeout,
        )
    raise ValueError(f"Unknown advisor provider: {provider_id}")


if __name__ == "__main__":
    raise SystemExit(main())
