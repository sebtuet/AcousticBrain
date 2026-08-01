import argparse
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys

from acousticbrain.advisor import (
    AdvisorConfigurationError,
    AdvisorError,
    AdvisorService,
    MockAdvisorProvider,
    OllamaAdvisorProvider,
    OpenAIAdvisorProvider,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.application import (
    EvidencePlanCompletionService,
    EvidencePlanPreparationWorkflowService,
    GuidedEvidencePlanPreparationDraftService,
    ExploratoryExperimentDeclarationService,
)
from acousticbrain.report import (
    AcousticObservationConsoleReporter,
    ConsoleReporter,
    DeterministicAcousticReasoningConsoleReporter,
    DeterministicCorrectiveActionConsoleReporter,
    DeterministicEvidenceWeightingConsoleReporter,
    EvidenceAcquisitionPlanConsoleReporter,
    FullAssessmentConsoleReporter,
    FullAssessmentTextExportError,
    FullAssessmentTextExporter,
    AnalysisReadinessConsoleReporter,
    AssessmentSummaryConsoleReporter,
    AdvisorConsoleReporter,
    ExploratoryConsoleReporter,
    ExperimentUserViewConsoleReporter,
    ExperimentUserViewPresenter,
    EvidencePlanUserViewConsoleReporter,
    EvidencePlanUserViewPresenter,
    EvidencePlanOverviewConsoleReporter,
    EvidencePlanOverviewPresenter,
    EvidencePlanPreparationUserViewConsoleReporter,
    EvidencePlanPreparationUserViewPresenter,
)
from acousticbrain.models import (
    AdvisorAudience,
    AdvisorDetailLevel,
    AdvisorResponseLanguage,
    CampaignReferenceDeclarationStatus,
    ListeningPositionCampaignInstanceStatus,
    ExploratoryFeasibilityDecision,
    FeasibilityAnswer,
)
from acousticbrain.persistence import (
    CampaignReferenceQualificationJsonLoader,
    ListeningPositionCampaignInstanceJsonLoader,
    ExploratoryFeasibilityJsonRepository,
    ExploratoryProposalInputJsonLoader,
    EvidencePlanCompletionInputJsonLoader,
    EvidencePlanCompletionRegistryJsonRepository,
    EvidencePlanPreparationConfirmationJsonLoader,
    EvidencePlanPreparationRegistryJsonRepository,
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
    parser.add_argument(
        "--full-assessment",
        action="store_true",
        help="print the complete deterministic assessment workflow",
    )
    parser.add_argument(
        "--full-assessment-output",
        type=Path,
        default=None,
        metavar="PATH",
        help="write the complete deterministic assessment to a new text file",
    )
    parser.add_argument(
        "--analysis-readiness",
        action="store_true",
        help="print existing technical analysis readiness decisions",
    )
    parser.add_argument(
        "--assessment-summary",
        action="store_true",
        help="print a concise summary of existing deterministic report content",
    )
    parser.add_argument(
        "--exploratory",
        action="store_true",
        help="print the deterministic Exploratory V1 proposal and feasibility state",
    )
    parser.add_argument(
        "--experiment-view",
        default=None,
        metavar="EXPERIMENT_ID",
        help="print the read-only four-block view for one exact experiment",
    )
    parser.add_argument(
        "--evidence-plan-view",
        default=None,
        metavar="PLAN_ID",
        help="explain one exact evidence plan without changing it",
    )
    parser.add_argument(
        "--evidence-plan-overview",
        action="store_true",
        help="list every evidence plan and its safe user action",
    )
    parser.add_argument(
        "--complete-evidence-plan",
        type=Path,
        default=None,
        metavar="INPUT_JSON",
        help="complete one exact BLOCKED evidence plan from structured input",
    )
    parser.add_argument(
        "--evidence-plan-completion-registry",
        type=Path,
        default=None,
        metavar="PATH",
        help="dedicated completion registry JSON (required for completion)",
    )
    parser.add_argument(
        "--confirm-evidence-plan-preparation",
        type=Path,
        default=None,
        metavar="INPUT_JSON",
        help="record explicit prerequisite statuses for one exact READY plan",
    )
    parser.add_argument(
        "--evidence-plan-preparation-registry",
        type=Path,
        default=None,
        metavar="PATH",
        help="dedicated preparation registry JSON (required for confirmation)",
    )
    parser.add_argument(
        "--evidence-plan-preparation-view",
        default=None,
        metavar="CONFIRMATION_ID",
        help="show one exact persisted preparation confirmation read-only",
    )
    parser.add_argument(
        "--generate-evidence-plan-preparation",
        default=None,
        metavar="PLAN_ID",
        help="preview an UNKNOWN-only preparation draft for one exact READY plan",
    )
    parser.add_argument(
        "--evidence-plan-preparation-output",
        type=Path,
        default=None,
        metavar="PATH",
        help="write the generated preparation draft to a new JSON file",
    )
    parser.add_argument(
        "--exploratory-proposal",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help="explicit structured proposal-input JSON (repeatable)",
    )
    parser.add_argument(
        "--exploratory-decisions",
        type=Path,
        default=None,
        metavar="PATH",
        help="versioned feasibility-decision JSON",
    )
    parser.add_argument(
        "--record-exploratory-feasibility",
        choices=tuple(value.value for value in FeasibilityAnswer),
        default=None,
        metavar="ANSWER",
        help="record an explicit FEASIBLE or INFEASIBLE decision and exit",
    )
    parser.add_argument("--exploratory-proposal-id", default=None)
    parser.add_argument("--exploratory-reference-scope-id", default=None)
    parser.add_argument("--exploratory-rule-version", type=int, default=1)
    parser.add_argument("--exploratory-note", default=None)
    parser.add_argument(
        "--declare-exploratory-experiment",
        default=None,
        metavar="EXPERIMENT_ID",
        help="explicitly declare the READY proposal for an existing experiment directory",
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
    parser.add_argument(
        "--advisor-language",
        choices=("auto", "fr", "en"),
        default="auto",
        help="advisor response language (default: deterministic detection)",
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


def validate_full_assessment_output(path):
    if path.exists():
        raise ValueError(f"Full assessment output already exists: {path}")
    if not path.parent.exists():
        raise ValueError(
            f"Full assessment output parent does not exist: {path.parent}"
        )
    if not path.parent.is_dir():
        raise ValueError(
            f"Full assessment output parent is not a directory: {path.parent}"
        )
    return path


def write_full_assessment_stdout(data):
    output = getattr(sys.stdout, "buffer", None)
    if output is None:
        raise FullAssessmentTextExportError(
            "Binary stdout is required for full assessment export."
        )
    output.write(data)
    output.flush()


def complete_evidence_plan(
    measurements_root,
    completion_input,
    registry_path,
    *,
    campaign_instance_analysis=None,
    brain=None,
    service=None,
    registry_repository=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        listening_position_campaign_instance_analysis=campaign_instance_analysis,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Evidence-plan completion requires an exact analysis context.")
    _, context = analysis
    plan_synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    weighting = getattr(context, "deterministic_evidence_weighting_synthesis", None)
    action_synthesis = getattr(
        context, "deterministic_corrective_action_synthesis", None
    )
    if plan_synthesis is None or weighting is None or action_synthesis is None:
        raise ValueError("Evidence-plan completion analysis contracts are unavailable.")
    repository = (
        registry_repository or EvidencePlanCompletionRegistryJsonRepository()
    )
    persisted = repository.load(registry_path)
    existing_derived_plans = tuple(
        item.derived_plan.plan for item in persisted.records
    )
    protocol = getattr(context, "listening_position_sampling_protocol", None)
    result = (service or EvidencePlanCompletionService(
        repository=repository
    )).complete(
        completion_input,
        registry_path=registry_path,
        source_plans=plan_synthesis.plans,
        blocking_factors=tuple(
            factor
            for weight in weighting.weights
            for factor in weight.blocking_factors
        ),
        actions=action_synthesis.actions,
        protocol_references=((protocol,) if protocol is not None else ()),
        plan_references=tuple((
            *plan_synthesis.plans,
            *existing_derived_plans,
        )),
    )
    state = "recorded" if result.persisted else "already recorded"
    print(
        "Evidence plan completion " + state + ": "
        + result.record.derived_plan.plan.plan_id
    )
    print("REFERENCE_RESOLVED")
    print("REFERENCE_COMPATIBLE")
    print("DERIVED_PLAN_READY")
    print(f"Registry: {Path(result.registry_path).resolve()}")
    return result


def confirm_evidence_plan_preparation(
    measurements_root,
    confirmation_input,
    registry_path,
    *,
    campaign_instance_analysis=None,
    brain=None,
    service=None,
    registry_repository=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        listening_position_campaign_instance_analysis=campaign_instance_analysis,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError(
            "Evidence-plan preparation requires an exact analysis context."
        )
    _, context = analysis
    plan_synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if plan_synthesis is None:
        raise ValueError(
            "Evidence-plan preparation analysis contracts are unavailable."
        )
    repository = (
        registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    )
    result = (service or EvidencePlanPreparationWorkflowService(
        repository=repository
    )).record(
        confirmation_input,
        registry_path=registry_path,
        plans=plan_synthesis.plans,
    )
    state = "recorded" if result.persisted else "already recorded"
    print("Evidence plan preparation " + state + ": " + confirmation_input.plan_id)
    print("PLAN_EXACTLY_RESOLVED")
    print("PREPARATION_DECLARED")
    if result.record.all_prerequisites_status is not None:
        print("ALL_PREREQUISITES_USER_CONFIRMED")
    else:
        print("ALL_PREREQUISITES_USER_CONFIRMED: unavailable")
    print("No experiment was declared or executed.")
    print(f"Registry: {Path(result.registry_path).resolve()}")
    return result


def view_evidence_plan_preparation(
    measurements_root,
    confirmation_id,
    registry_path,
    *,
    campaign_instance_analysis=None,
    brain=None,
    registry_repository=None,
    presenter=None,
    reporter=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        listening_position_campaign_instance_analysis=campaign_instance_analysis,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError(
            "Evidence-plan preparation view requires an exact analysis context."
        )
    _, context = analysis
    plan_synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if plan_synthesis is None:
        raise ValueError(
            "Evidence-plan preparation view analysis contracts are unavailable."
        )
    repository = (
        registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    )
    registry = repository.load(registry_path)
    view = (presenter or EvidencePlanPreparationUserViewPresenter()).present(
        registry, plan_synthesis.plans, confirmation_id
    )
    (reporter or EvidencePlanPreparationUserViewConsoleReporter()).print(view)
    return view


def generate_evidence_plan_preparation(
    measurements_root,
    plan_id,
    registry_path,
    *,
    output_path=None,
    campaign_instance_analysis=None,
    brain=None,
    service=None,
    registry_repository=None,
    serializer=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        listening_position_campaign_instance_analysis=campaign_instance_analysis,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Guided preparation requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Guided preparation analysis contracts are unavailable.")
    repository = (
        registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    )
    registry = repository.load(registry_path)
    draft = (service or GuidedEvidencePlanPreparationDraftService()).generate(
        plan_id, plans=synthesis.plans, registry=registry
    )
    codec = serializer or EvidencePlanPreparationConfirmationJsonLoader()
    value = draft.confirmation_input
    print(f"EVIDENCE PLAN PREPARATION DRAFT — {value.confirmation_id}")
    print()
    print(EvidencePlanUserViewPresenter._user_label(draft.plan))
    print(f"Plan : {value.plan_id}")
    print()
    print("Statuts proposés")
    if value.prerequisites:
        for item in value.prerequisites:
            print(f"{item.code} : {item.status.value}")
    else:
        print("Aucun prérequis déclaré.")
    print()
    print("JSON canonique")
    print(codec.dumps(value))
    print()
    if output_path is not None:
        codec.save_new(output_path, value)
        print(f"Brouillon écrit : {output_path.resolve()}")
    else:
        print("Brouillon non écrit : aucun chemin de sortie demandé.")
    print("Aucune préparation enregistrée et aucune expérience exécutée.")
    return draft


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
    full_assessment=False,
    full_assessment_output=None,
    analysis_readiness=False,
    assessment_summary=False,
    exploratory=False,
    experiment_view=None,
    evidence_plan_view=None,
    evidence_plan_overview=False,
    exploratory_proposal_inputs=(),
    exploratory_feasibility_decisions=None,
    advisor=False,
    question=None,
    advisor_audience=AdvisorAudience.GENERAL,
    advisor_detail_level=AdvisorDetailLevel.STANDARD,
    advisor_response_language=AdvisorResponseLanguage.EN,
    advisor_provider=None,
    advisor_service=None,
    brain=None,
    reporter=None,
):
    brain = brain or AcousticBrain()
    reporter = reporter or (
        EvidencePlanOverviewConsoleReporter()
        if evidence_plan_overview
        else EvidencePlanUserViewConsoleReporter()
        if evidence_plan_view is not None
        else ExperimentUserViewConsoleReporter()
        if experiment_view is not None
        else AdvisorConsoleReporter()
        if advisor
        else ExploratoryConsoleReporter()
        if exploratory
        else AssessmentSummaryConsoleReporter()
        if assessment_summary
        else AnalysisReadinessConsoleReporter()
        if analysis_readiness
        else FullAssessmentConsoleReporter()
        if full_assessment
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
    if exploratory:
        arguments["analyze_exploratory"] = True
        arguments["exploratory_proposal_inputs"] = tuple(
            exploratory_proposal_inputs
        )
        arguments["exploratory_feasibility_decisions"] = (
            exploratory_feasibility_decisions
        )
    if observations:
        arguments["synthesize_observations"] = True
    if reasoning:
        arguments["synthesize_reasoning"] = True
    if actions:
        arguments["synthesize_actions"] = True
    if weighting:
        arguments["synthesize_weighting"] = True
    standard_report = not any((
        observations,
        reasoning,
        actions,
        weighting,
        evidence_acquisition,
        full_assessment,
        analysis_readiness,
        assessment_summary,
        advisor,
        exploratory,
        experiment_view is not None,
        evidence_plan_view is not None,
        evidence_plan_overview,
    ))
    if (
        evidence_acquisition
        or full_assessment
        or assessment_summary
        or standard_report
        or experiment_view is not None
        or evidence_plan_view is not None
        or evidence_plan_overview
    ):
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
    if evidence_plan_overview:
        report.evidence_plan_overview = EvidencePlanOverviewPresenter().present(
            report
        )
    if evidence_plan_view is not None:
        report.evidence_plan_user_view = EvidencePlanUserViewPresenter().present(
            report, evidence_plan_view
        )
    if experiment_view is not None:
        report.experiment_user_view = ExperimentUserViewPresenter().present(
            report, experiment_view
        )
    if advisor:
        report.advisor_response = (advisor_service or AdvisorService()).advise(
            report,
            question=question,
            audience=advisor_audience,
            detail_level=advisor_detail_level,
            provider=advisor_provider,
            expected_response_language=advisor_response_language,
        )
    if full_assessment_output is None:
        if not analysis_readiness and not assessment_summary:
            print(f"Measurement root: {measurements_root.resolve()}")
            print()
        reporter.print(report)
    else:
        rendered_output = StringIO()
        with redirect_stdout(rendered_output):
            print(f"Measurement root: {measurements_root.resolve()}")
            print()
            reporter.print(report)
        text = rendered_output.getvalue()
        data = text.encode("utf-8")
        write_full_assessment_stdout(data)
        FullAssessmentTextExporter(full_assessment_output).write(data)
    return report


def main(
    argv=None,
    *,
    brain=None,
    reporter=None,
    campaign_loader=None,
    reference_qualification_loader=None,
    exploratory_proposal_loader=None,
    exploratory_decision_repository=None,
    exploratory_declaration_service=None,
    evidence_plan_completion_loader=None,
    evidence_plan_completion_service=None,
    evidence_plan_completion_registry_repository=None,
    evidence_plan_preparation_loader=None,
    evidence_plan_preparation_service=None,
    evidence_plan_preparation_registry_repository=None,
    evidence_plan_preparation_view_presenter=None,
    evidence_plan_preparation_view_reporter=None,
    guided_preparation_draft_service=None,
    guided_preparation_draft_serializer=None,
    advisor_provider_instance=None,
    advisor_service=None,
):
    parser = create_parser()
    arguments = parser.parse_args(argv)
    decision_repository = (
        exploratory_decision_repository or ExploratoryFeasibilityJsonRepository()
    )
    if arguments.record_exploratory_feasibility is not None:
        required = {
            "--exploratory-decisions": arguments.exploratory_decisions,
            "--exploratory-proposal-id": arguments.exploratory_proposal_id,
            "--exploratory-reference-scope-id": arguments.exploratory_reference_scope_id,
        }
        missing = tuple(option for option, value in required.items() if not value)
        if missing:
            parser.error(
                "--record-exploratory-feasibility requires " + ", ".join(missing)
            )
        try:
            registry = decision_repository.load(arguments.exploratory_decisions)
            registry = registry.record(ExploratoryFeasibilityDecision(
                proposal_id=arguments.exploratory_proposal_id,
                reference_scope_id=arguments.exploratory_reference_scope_id,
                rule_version=arguments.exploratory_rule_version,
                answer=FeasibilityAnswer(arguments.record_exploratory_feasibility),
                user_note=arguments.exploratory_note,
            ))
            decision_repository.save(registry, arguments.exploratory_decisions)
        except (OSError, ValueError, TypeError) as error:
            parser.error(str(error))
        print("Exploratory feasibility decision recorded.")
        return 0
    try:
        measurements_root = validate_measurements_root(arguments.measurements_root)
        if arguments.question is not None and not arguments.advisor:
            raise ValueError("--question requires --advisor.")
        if (
            arguments.complete_evidence_plan is None
            and arguments.evidence_plan_completion_registry is not None
        ):
            raise ValueError(
                "--evidence-plan-completion-registry requires "
                "--complete-evidence-plan."
            )
        if arguments.complete_evidence_plan is not None:
            if arguments.evidence_plan_completion_registry is None:
                raise ValueError(
                    "--complete-evidence-plan requires "
                    "--evidence-plan-completion-registry."
                )
            conflicting = (
                ("--observations", arguments.observations),
                ("--reasoning", arguments.reasoning),
                ("--actions", arguments.actions),
                ("--weighting", arguments.weighting),
                ("--evidence-acquisition", arguments.evidence_acquisition),
                ("--full-assessment", arguments.full_assessment),
                ("--analysis-readiness", arguments.analysis_readiness),
                ("--assessment-summary", arguments.assessment_summary),
                ("--exploratory", arguments.exploratory),
                ("--advisor", arguments.advisor),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        f"--complete-evidence-plan cannot be combined with {option}."
                    )
        if (
            arguments.confirm_evidence_plan_preparation is None
            and arguments.evidence_plan_preparation_view is None
            and arguments.generate_evidence_plan_preparation is None
            and arguments.evidence_plan_preparation_registry is not None
        ):
            raise ValueError(
                "--evidence-plan-preparation-registry requires "
                "--confirm-evidence-plan-preparation or "
                "--evidence-plan-preparation-view or "
                "--generate-evidence-plan-preparation."
            )
        if (
            arguments.evidence_plan_preparation_output is not None
            and arguments.generate_evidence_plan_preparation is None
        ):
            raise ValueError(
                "--evidence-plan-preparation-output requires "
                "--generate-evidence-plan-preparation."
            )
        if arguments.generate_evidence_plan_preparation is not None:
            if arguments.evidence_plan_preparation_registry is None:
                raise ValueError(
                    "--generate-evidence-plan-preparation requires "
                    "--evidence-plan-preparation-registry."
                )
            conflicting = (
                ("--confirm-evidence-plan-preparation", arguments.confirm_evidence_plan_preparation is not None),
                ("--evidence-plan-preparation-view", arguments.evidence_plan_preparation_view is not None),
                ("--complete-evidence-plan", arguments.complete_evidence_plan is not None),
                ("--full-assessment", arguments.full_assessment),
                ("--exploratory", arguments.exploratory),
                ("--advisor", arguments.advisor),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        "--generate-evidence-plan-preparation cannot be combined "
                        f"with {option}."
                    )
        if arguments.confirm_evidence_plan_preparation is not None:
            if arguments.evidence_plan_preparation_registry is None:
                raise ValueError(
                    "--confirm-evidence-plan-preparation requires "
                    "--evidence-plan-preparation-registry."
                )
            conflicting = (
                ("--complete-evidence-plan", arguments.complete_evidence_plan is not None),
                ("--observations", arguments.observations),
                ("--reasoning", arguments.reasoning),
                ("--actions", arguments.actions),
                ("--weighting", arguments.weighting),
                ("--evidence-acquisition", arguments.evidence_acquisition),
                ("--full-assessment", arguments.full_assessment),
                ("--analysis-readiness", arguments.analysis_readiness),
                ("--assessment-summary", arguments.assessment_summary),
                ("--exploratory", arguments.exploratory),
                ("--advisor", arguments.advisor),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        "--confirm-evidence-plan-preparation cannot be combined "
                        f"with {option}."
                    )
        if arguments.evidence_plan_preparation_view is not None:
            if arguments.evidence_plan_preparation_registry is None:
                raise ValueError(
                    "--evidence-plan-preparation-view requires "
                    "--evidence-plan-preparation-registry."
                )
            conflicting = (
                (
                    "--confirm-evidence-plan-preparation",
                    arguments.confirm_evidence_plan_preparation is not None,
                ),
                ("--complete-evidence-plan", arguments.complete_evidence_plan is not None),
                ("--observations", arguments.observations),
                ("--reasoning", arguments.reasoning),
                ("--actions", arguments.actions),
                ("--weighting", arguments.weighting),
                ("--evidence-acquisition", arguments.evidence_acquisition),
                ("--full-assessment", arguments.full_assessment),
                ("--analysis-readiness", arguments.analysis_readiness),
                ("--assessment-summary", arguments.assessment_summary),
                ("--exploratory", arguments.exploratory),
                ("--advisor", arguments.advisor),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        "--evidence-plan-preparation-view cannot be combined "
                        f"with {option}."
                    )
        if arguments.exploratory_proposal and not arguments.exploratory:
            raise ValueError("--exploratory-proposal requires --exploratory.")
        if arguments.exploratory_decisions is not None and not arguments.exploratory:
            raise ValueError("--exploratory-decisions requires --exploratory.")
        if (
            arguments.declare_exploratory_experiment is not None
            and not arguments.exploratory
        ):
            raise ValueError(
                "--declare-exploratory-experiment requires --exploratory."
            )
        incompatible_exploratory_options = (
            ("--observations", arguments.observations),
            ("--reasoning", arguments.reasoning),
            ("--actions", arguments.actions),
            ("--weighting", arguments.weighting),
            ("--evidence-acquisition", arguments.evidence_acquisition),
            ("--full-assessment", arguments.full_assessment),
            ("--analysis-readiness", arguments.analysis_readiness),
            ("--assessment-summary", arguments.assessment_summary),
            ("--advisor", arguments.advisor),
            ("--experiment-view", arguments.experiment_view is not None),
            ("--evidence-plan-view", arguments.evidence_plan_view is not None),
            ("--evidence-plan-overview", arguments.evidence_plan_overview),
        )
        for option, enabled in incompatible_exploratory_options:
            if arguments.exploratory and enabled:
                raise ValueError(f"--exploratory cannot be combined with {option}.")
        incompatible_full_assessment_options = (
            ("--observations", arguments.observations),
            ("--reasoning", arguments.reasoning),
            ("--actions", arguments.actions),
            ("--weighting", arguments.weighting),
            ("--evidence-acquisition", arguments.evidence_acquisition),
            ("--advisor", arguments.advisor),
            ("--experiment-view", arguments.experiment_view is not None),
            ("--evidence-plan-view", arguments.evidence_plan_view is not None),
            ("--evidence-plan-overview", arguments.evidence_plan_overview),
        )
        for option, enabled in incompatible_full_assessment_options:
            if arguments.full_assessment and enabled:
                raise ValueError(f"--full-assessment cannot be combined with {option}.")
        incompatible_analysis_readiness_options = (
            ("--observations", arguments.observations),
            ("--reasoning", arguments.reasoning),
            ("--actions", arguments.actions),
            ("--weighting", arguments.weighting),
            ("--evidence-acquisition", arguments.evidence_acquisition),
            ("--full-assessment", arguments.full_assessment),
            (
                "--full-assessment-output",
                arguments.full_assessment_output is not None,
            ),
            ("--advisor", arguments.advisor),
            ("--experiment-view", arguments.experiment_view is not None),
            ("--evidence-plan-view", arguments.evidence_plan_view is not None),
            ("--evidence-plan-overview", arguments.evidence_plan_overview),
        )
        for option, enabled in incompatible_analysis_readiness_options:
            if arguments.analysis_readiness and enabled:
                raise ValueError(
                    f"--analysis-readiness cannot be combined with {option}."
                )
        incompatible_assessment_summary_options = (
            ("--observations", arguments.observations),
            ("--reasoning", arguments.reasoning),
            ("--actions", arguments.actions),
            ("--weighting", arguments.weighting),
            ("--evidence-acquisition", arguments.evidence_acquisition),
            ("--analysis-readiness", arguments.analysis_readiness),
            ("--full-assessment", arguments.full_assessment),
            (
                "--full-assessment-output",
                arguments.full_assessment_output is not None,
            ),
            ("--advisor", arguments.advisor),
            ("--experiment-view", arguments.experiment_view is not None),
            ("--evidence-plan-view", arguments.evidence_plan_view is not None),
            ("--evidence-plan-overview", arguments.evidence_plan_overview),
        )
        for option, enabled in incompatible_assessment_summary_options:
            if arguments.assessment_summary and enabled:
                raise ValueError(
                    f"--assessment-summary cannot be combined with {option}."
                )
        if (
            arguments.full_assessment_output is not None
            and not arguments.full_assessment
        ):
            raise ValueError(
                "--full-assessment-output requires --full-assessment."
            )
        full_assessment_output = (
            validate_full_assessment_output(arguments.full_assessment_output)
            if arguments.full_assessment_output is not None
            else None
        )
        if arguments.advisor and not arguments.question:
            raise ValueError("--advisor requires --question.")
        dedicated_modes = (
            ("--observations", arguments.observations),
            ("--reasoning", arguments.reasoning),
            ("--actions", arguments.actions),
            ("--weighting", arguments.weighting),
            ("--evidence-acquisition", arguments.evidence_acquisition),
            ("--advisor", arguments.advisor),
        )
        for option, enabled in dedicated_modes:
            if arguments.experiment_view is not None and enabled:
                raise ValueError(f"--experiment-view cannot be combined with {option}.")
        if (
            arguments.experiment_view is not None
            and arguments.evidence_plan_view is not None
        ):
            raise ValueError(
                "--evidence-plan-view cannot be combined with --experiment-view."
            )
        if arguments.evidence_plan_overview and (
            arguments.experiment_view is not None
            or arguments.evidence_plan_view is not None
        ):
            raise ValueError(
                "--evidence-plan-overview cannot be combined with another "
                "user view."
            )
        for option, enabled in dedicated_modes:
            if arguments.evidence_plan_view is not None and enabled:
                raise ValueError(
                    f"--evidence-plan-view cannot be combined with {option}."
                )
            if arguments.evidence_plan_overview and enabled:
                raise ValueError(
                    f"--evidence-plan-overview cannot be combined with {option}."
                )
        campaign_instance_analysis = None
        reference_qualification_declaration_analysis = None
        proposal_inputs = ()
        feasibility_decisions = None
        if arguments.exploratory:
            loader = exploratory_proposal_loader or ExploratoryProposalInputJsonLoader()
            proposal_inputs = tuple(
                loader.load(path) for path in arguments.exploratory_proposal
            )
            if arguments.exploratory_decisions is not None:
                feasibility_decisions = decision_repository.load(
                    arguments.exploratory_decisions
                )
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
        if arguments.complete_evidence_plan is not None:
            completion_input = (
                evidence_plan_completion_loader
                or EvidencePlanCompletionInputJsonLoader()
            ).load(arguments.complete_evidence_plan)
            complete_evidence_plan(
                measurements_root,
                completion_input,
                arguments.evidence_plan_completion_registry,
                campaign_instance_analysis=campaign_instance_analysis,
                brain=brain,
                service=evidence_plan_completion_service,
                registry_repository=(
                    evidence_plan_completion_registry_repository
                ),
            )
            return 0
        if arguments.generate_evidence_plan_preparation is not None:
            generate_evidence_plan_preparation(
                measurements_root,
                arguments.generate_evidence_plan_preparation,
                arguments.evidence_plan_preparation_registry,
                output_path=arguments.evidence_plan_preparation_output,
                campaign_instance_analysis=campaign_instance_analysis,
                brain=brain,
                service=guided_preparation_draft_service,
                registry_repository=(
                    evidence_plan_preparation_registry_repository
                ),
                serializer=guided_preparation_draft_serializer,
            )
            return 0
        if arguments.confirm_evidence_plan_preparation is not None:
            confirmation_input = (
                evidence_plan_preparation_loader
                or EvidencePlanPreparationConfirmationJsonLoader()
            ).load(arguments.confirm_evidence_plan_preparation)
            confirm_evidence_plan_preparation(
                measurements_root,
                confirmation_input,
                arguments.evidence_plan_preparation_registry,
                campaign_instance_analysis=campaign_instance_analysis,
                brain=brain,
                service=evidence_plan_preparation_service,
                registry_repository=(
                    evidence_plan_preparation_registry_repository
                ),
            )
            return 0
        if arguments.evidence_plan_preparation_view is not None:
            view_evidence_plan_preparation(
                measurements_root,
                arguments.evidence_plan_preparation_view,
                arguments.evidence_plan_preparation_registry,
                campaign_instance_analysis=campaign_instance_analysis,
                brain=brain,
                registry_repository=(
                    evidence_plan_preparation_registry_repository
                ),
                presenter=evidence_plan_preparation_view_presenter,
                reporter=evidence_plan_preparation_view_reporter,
            )
            return 0
    except (OSError, TypeError, ValueError) as error:
        parser.error(str(error))
    try:
        report = run(
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
            full_assessment=arguments.full_assessment,
            full_assessment_output=full_assessment_output,
            analysis_readiness=arguments.analysis_readiness,
            assessment_summary=arguments.assessment_summary,
            exploratory=arguments.exploratory,
            experiment_view=arguments.experiment_view,
            evidence_plan_view=arguments.evidence_plan_view,
            evidence_plan_overview=arguments.evidence_plan_overview,
            exploratory_proposal_inputs=proposal_inputs,
            exploratory_feasibility_decisions=feasibility_decisions,
            advisor=arguments.advisor,
            question=arguments.question,
            advisor_audience=AdvisorAudience(arguments.advisor_audience),
            advisor_detail_level=AdvisorDetailLevel(arguments.advisor_detail),
            advisor_response_language=resolve_advisor_language(
                arguments.advisor_language, arguments.question or ""
            ),
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
        if arguments.declare_exploratory_experiment is not None:
            (exploratory_declaration_service or
             ExploratoryExperimentDeclarationService()).declare(
                measurements_root,
                experiment_code=arguments.declare_exploratory_experiment,
                analysis=report.exploratory_analysis,
                user_note=arguments.exploratory_note,
            )
            print(
                "Exploratory experiment declared: "
                + arguments.declare_exploratory_experiment
            )
    except (AdvisorError, FullAssessmentTextExportError, ValueError) as error:
        parser.error(str(error))
    return 0


def resolve_advisor_language(configured, question):
    if configured != "auto":
        return AdvisorResponseLanguage(configured)
    normalized = question.casefold()
    french_markers = (
        "é", "è", "à", "ç", "ù", "résume", "explique", "pourquoi",
        "aucune", "quels", "quelles", "prêts", "bloqués", "français",
    )
    return (
        AdvisorResponseLanguage.FR
        if any(value in normalized for value in french_markers)
        else AdvisorResponseLanguage.EN
    )


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
