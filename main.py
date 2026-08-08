import argparse
import json
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
    EvidencePlanPreparationPreviewService,
    GuidedEvidencePlanPreparationDraftService,
    GuidedEvidencePlanPreparationRevisionService,
    ChannelIsolationGuidedExecutionService,
    ChannelIsolationOperationalWorksheetService,
    ChannelIsolationOperationalRecordPreviewService,
    ChannelIsolationDocumentationReviewService,
    ChannelIsolationDeclarationReadinessService,
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
    GuidedGlobalStatusConsoleReporter,
    GuidedGlobalStatusPresenter,
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
    EvidencePlanPrerequisiteStatus,
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
    ChannelIsolationMicrophonePositionRecordJsonLoader,
    ChannelIsolationAcquisitionSettingsRecordJsonLoader,
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
        "--guided-status",
        action="store_true",
        help="show the current workflow state and exactly one safe next action",
    )
    parser.add_argument(
        "--guided-preparation-registry",
        type=Path,
        default=None,
        metavar="PATH",
        help="optional explicit preparation registry for --guided-status",
    )
    parser.add_argument(
        "--guided-preparation",
        default=None,
        metavar="CONFIRMATION_ID",
        help="optional exact preparation selection for --guided-status",
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
        "--preview-evidence-plan-preparation",
        type=Path,
        default=None,
        metavar="INPUT_JSON",
        help="preview declaration decisions without recording them",
    )
    parser.add_argument(
        "--channel-isolation-journey",
        default=None,
        metavar="PLAN_ID",
        help="show the read-only guided checklist for one CHANNEL_ISOLATION plan",
    )
    parser.add_argument(
        "--revise-evidence-plan-preparation",
        type=Path,
        default=None,
        metavar="SOURCE_JSON",
        help="derive a new preparation draft from explicit prerequisite statuses",
    )
    parser.add_argument(
        "--preparation-status",
        action="append",
        default=[],
        metavar="CODE=STATUS",
        help="exact prerequisite status assignment (repeat for every code)",
    )
    parser.add_argument(
        "--channel-isolation-preparation",
        default=None,
        metavar="CONFIRMATION_ID",
        help="exact preparation confirmation for the channel-isolation journey",
    )
    parser.add_argument(
        "--generate-channel-isolation-records",
        default=None,
        metavar="PLAN_ID",
        help="generate fill-in operational worksheets for one exact plan",
    )
    parser.add_argument(
        "--microphone-position-output", type=Path, default=None, metavar="PATH"
    )
    parser.add_argument(
        "--acquisition-settings-output", type=Path, default=None, metavar="PATH"
    )
    parser.add_argument(
        "--preview-channel-isolation-records",
        default=None,
        metavar="PLAN_ID",
        help="preview two operational worksheet files without writing",
    )
    parser.add_argument(
        "--microphone-position-record", type=Path, default=None, metavar="PATH"
    )
    parser.add_argument(
        "--acquisition-settings-record", type=Path, default=None, metavar="PATH"
    )
    parser.add_argument(
        "--review-channel-isolation-documentation",
        default=None,
        metavar="PLAN_ID",
        help="review complete operational records against a preparation draft",
    )
    parser.add_argument(
        "--channel-isolation-source-preparation",
        type=Path,
        default=None,
        metavar="PATH",
    )
    parser.add_argument(
        "--channel-isolation-declaration-readiness",
        default=None,
        metavar="PLAN_ID",
        help="qualify exact inputs for a separate CHANNEL_ISOLATION declaration",
    )
    parser.add_argument(
        "--channel-isolation-reference", default=None, metavar="EXPERIMENT_ID"
    )
    parser.add_argument(
        "--channel-isolation-experiment", default=None, metavar="EXPERIMENT_ID"
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


def preview_evidence_plan_preparation(
    measurements_root, confirmation_input, registry_path, *, brain=None,
    service=None, registry_repository=None, input_path=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Preparation preview requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Preparation preview analysis contracts are unavailable.")
    repository = registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    registry = repository.load(registry_path)
    result = (service or EvidencePlanPreparationPreviewService()).preview(
        confirmation_input, plans=synthesis.plans, registry=registry
    )
    print(f"EVIDENCE PLAN PREPARATION PREVIEW — {confirmation_input.confirmation_id}")
    print()
    print("Statuts déclarés")
    for item in confirmation_input.prerequisites:
        print(f"{item.code} : {item.status.value}")
    print()
    print("Décisions projetées")
    print(result.record.resolution_status.value)
    print(result.record.declaration_status.value)
    print(result.record.all_prerequisites_status.value if result.record.all_prerequisites_status else "ALL_PREREQUISITES_USER_CONFIRMED : indisponible")
    print(f"État du registre : {result.registry_state}")
    print()
    print("Action utilisateur")
    if result.registry_state == "ALREADY_RECORDED":
        print("Aucune action : cette déclaration identique est déjà enregistrée.")
    elif input_path is None:
        print("Enregistrer séparément ce brouillon avec la commande de confirmation explicite.")
    else:
        print("Après vérification, enregistrer explicitement avec :")
        print(
            "python main.py --measurements-root "
            f"{measurements_root} --confirm-evidence-plan-preparation "
            f"{input_path} --evidence-plan-preparation-registry {registry_path}"
        )
    print("Aucune préparation enregistrée et aucune expérience exécutée.")
    print("Causality status: NOT_ESTABLISHED")
    return result


def show_channel_isolation_journey(
    measurements_root, plan_id, confirmation_id, registry_path, *, brain=None,
    service=None, registry_repository=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("CHANNEL_ISOLATION journey requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("CHANNEL_ISOLATION journey analysis contracts are unavailable.")
    repository = registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    journey = (service or ChannelIsolationGuidedExecutionService()).build(
        plan_id, confirmation_id, plans=synthesis.plans,
        registry=repository.load(registry_path),
    )
    checklist = journey.checklist
    preparation = journey.preparation_record.confirmation_input
    print(f"CHANNEL ISOLATION JOURNEY — {plan_id}")
    print()
    print("Provenance")
    print(f"Préparation : {confirmation_id}")
    print(f"Empreinte du plan : {preparation.plan_contract_fingerprint}")
    print()
    print("Qualification de préparation")
    print(journey.preparation_status)
    for item in preparation.prerequisites:
        print(f"{item.code} : {item.status.value}")
    print()
    print("Aide aux prérequis")
    for guidance in journey.prerequisite_guidance:
        print(guidance.code)
        print("Signification : " + guidance.meaning)
        print("CONFIRMED si : " + guidance.confirmed_when)
        print("NOT_CONFIRMED si : " + guidance.not_confirmed_when)
        print("UNKNOWN si : " + guidance.unknown_when)
        print("Limite : " + guidance.limitation)
    print()
    print("Checklist d’acquisition")
    print("Canaux à acquérir : " + ", ".join(checklist.required_acquired_channels))
    print("Canaux à répéter : " + ", ".join(checklist.required_repeated_channels))
    print("Variables modifiées : " + ", ".join(checklist.independent_variables))
    print("Variables contrôlées : " + ", ".join(checklist.controlled_variables))
    print("Mesures : " + ", ".join(checklist.measurements))
    print("Observations attendues : " + ", ".join(checklist.expected_observations))
    for index, instruction in enumerate(checklist.instructions, start=1):
        print(f"Étape {index} : {instruction}")
    print("Critères de réussite : " + ", ".join(checklist.success_criteria))
    print("Critères d’échec : " + ", ".join(checklist.failure_criteria))
    print("Limites : " + ", ".join(checklist.limitations))
    print()
    print("Action utilisateur")
    if journey.user_action_state == "REVIEW_PREPARATION_DECLARATION":
        print("Revoir les prérequis non confirmés ; aucune déclaration d’expérience n’est disponible.")
    else:
        print("Déclarer séparément l’expérience depuis ce plan exact avant toute acquisition.")
    print()
    print("Frontière scientifique")
    print("Cette checklist ne vérifie aucune condition physique et n’exécute aucune mesure.")
    print("Aucune expérience n’a été déclarée ou exécutée par cette vue.")
    print("Causality status: NOT_ESTABLISHED")
    return journey


def revise_evidence_plan_preparation(
    measurements_root, source_input, statuses, registry_path, output_path, *,
    brain=None, service=None, registry_repository=None, serializer=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root, compare_experiments=True,
        analyze_causal_discrimination=True, synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Guided preparation revision requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Guided preparation revision analysis contracts are unavailable.")
    repository = registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    draft = (service or GuidedEvidencePlanPreparationRevisionService()).revise(
        source_input, statuses, plans=synthesis.plans, registry=repository.load(registry_path)
    )
    codec = serializer or EvidencePlanPreparationConfirmationJsonLoader()
    codec.save_new(output_path, draft.confirmation_input)
    print(f"PREPARATION DRAFT REVISED — {draft.confirmation_input.confirmation_id}")
    for item in draft.confirmation_input.prerequisites:
        print(f"{item.code} : {item.status.value}")
    print(f"Nouveau brouillon : {output_path.resolve()}")
    print("Le brouillon source et le registre restent inchangés.")
    print("Aucune préparation enregistrée et aucune expérience exécutée.")
    return draft


def generate_channel_isolation_records(
    measurements_root, plan_id, microphone_path, settings_path, *, brain=None,
    service=None,
):
    targets = (microphone_path, settings_path)
    if microphone_path == settings_path:
        raise ValueError("Channel-isolation worksheet output paths must differ.")
    for target in targets:
        if target.exists():
            raise ValueError(f"Channel-isolation worksheet output already exists: {target}")
        if not target.parent.exists() or not target.parent.is_dir():
            raise ValueError(f"Channel-isolation worksheet parent is unavailable: {target.parent}")
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root, compare_experiments=True,
        analyze_causal_discrimination=True, synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Worksheet generation requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Worksheet generation analysis contracts are unavailable.")
    result = (service or ChannelIsolationOperationalWorksheetService()).generate(
        plan_id, plans=synthesis.plans
    )
    ChannelIsolationMicrophonePositionRecordJsonLoader.save_new_worksheet(
        microphone_path, result.microphone_position
    )
    ChannelIsolationAcquisitionSettingsRecordJsonLoader.save_new_worksheet(
        settings_path, result.acquisition_settings
    )
    print("CHANNEL ISOLATION OPERATIONAL WORKSHEETS")
    print(f"Fiche microphone : {microphone_path.resolve()}")
    print(f"Fiche réglages : {settings_path.resolve()}")
    print("Remplacer chaque marqueur explicite avant prévisualisation.")
    print("Aucun prérequis confirmé et aucune expérience exécutée.")
    return result


def preview_channel_isolation_records(
    measurements_root, plan_id, microphone_path, settings_path, *, brain=None,
    service=None,
):
    try:
        microphone = json.loads(microphone_path.read_text(encoding="utf-8"))
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid channel-isolation worksheet JSON: {error}") from error
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root, compare_experiments=True,
        analyze_causal_discrimination=True, synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Worksheet preview requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Worksheet preview analysis contracts are unavailable.")
    result = (service or ChannelIsolationOperationalRecordPreviewService()).preview(
        plan_id, microphone, settings, plans=synthesis.plans
    )
    print("CHANNEL ISOLATION OPERATIONAL RECORDS PREVIEW")
    print(result.status)
    print()
    print("Champs restant à documenter")
    if result.missing_fields:
        print("\n".join(result.missing_fields))
    else:
        print("aucun")
    print()
    print("Action utilisateur")
    if result.status == "DOCUMENTATION_INCOMPLETE":
        print("Renseigner explicitement les champs listés, ou conserver les fiches incomplètes.")
    else:
        print("Examiner séparément si ces documents soutiennent une nouvelle déclaration de préparation.")
    print("Aucun prérequis confirmé et aucune expérience exécutée.")
    print("Causality status: NOT_ESTABLISHED")
    return result


def review_channel_isolation_documentation(
    measurements_root, plan_id, microphone_path, settings_path, source_path, *,
    brain=None, service=None, preparation_loader=None,
):
    try:
        microphone = json.loads(microphone_path.read_text(encoding="utf-8"))
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid channel-isolation worksheet JSON: {error}") from error
    source = (
        preparation_loader or EvidencePlanPreparationConfirmationJsonLoader()
    ).load(source_path)
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root, compare_experiments=True,
        analyze_causal_discrimination=True, synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Documentation review requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Documentation review analysis contracts are unavailable.")
    result = (service or ChannelIsolationDocumentationReviewService()).review(
        plan_id, microphone, settings, source, plans=synthesis.plans
    )
    print(f"CHANNEL ISOLATION DOCUMENTATION REVIEW — {plan_id}")
    print(f"Brouillon source : {result.source_confirmation_id}")
    print()
    print("Revue des prérequis")
    for row in result.rows:
        print(row.prerequisite_code)
        print(f"Documentation : {row.documentation_state} — {row.documentation_record_id}")
        print(f"Décision de préparation : {row.decision_state}")
    print()
    print("Action utilisateur")
    print("Choisir explicitement un statut pour chaque prérequis, puis créer un nouveau brouillon avec :")
    command = (
        f"python main.py --measurements-root {measurements_root} "
        f"--revise-evidence-plan-preparation {source_path}"
    )
    for row in result.rows:
        command += f" --preparation-status {row.prerequisite_code}=<STATUS>"
    command += (
        " --evidence-plan-preparation-registry <REGISTRY_PATH>"
        " --evidence-plan-preparation-output <NEW_DRAFT_PATH>"
    )
    print(command)
    print("Valeurs autorisées : CONFIRMED, NOT_CONFIRMED, UNKNOWN.")
    print("Aucun statut choisi, aucun brouillon écrit et aucune expérience exécutée.")
    print("Causality status: NOT_ESTABLISHED")
    return result


def show_channel_isolation_declaration_readiness(
    measurements_root, plan_id, confirmation_id, registry_path,
    reference_experiment_id, experiment_id, *, brain=None, service=None,
    registry_repository=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root, compare_experiments=True,
        analyze_causal_discrimination=True, synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Declaration readiness requires an exact analysis context.")
    _, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Declaration readiness analysis contracts are unavailable.")
    repository = registry_repository or EvidencePlanPreparationRegistryJsonRepository()
    result = (service or ChannelIsolationDeclarationReadinessService()).qualify(
        measurements_root,
        plan_id,
        confirmation_id,
        reference_experiment_id,
        experiment_id,
        plans=synthesis.plans,
        registry=repository.load(registry_path),
    )
    print(f"CHANNEL ISOLATION DECLARATION READINESS — {plan_id}")
    print()
    print("Qualification")
    for status in result.statuses:
        print(status)
    print()
    print("Provenance")
    print(f"Préparation : {result.confirmation_id}")
    print(f"Référence : {result.reference_experiment_id}")
    print(f"Nouvelle expérience : {result.experiment_id}")
    print()
    print("Action utilisateur")
    print("Déclarer séparément le contrat expérimental avec :")
    print(
        "python -m acousticbrain.commands.declare_evidence_plan_experiment "
        f"{measurements_root} --plan-id {result.plan_id} "
        f"--experiment {result.experiment_id} "
        f"--reference {result.reference_experiment_id}"
    )
    print()
    print("Frontière scientifique")
    print("La préparation reste une déclaration utilisateur non vérifiée indépendamment.")
    print("Aucun dossier, manifeste, mesure ou résultat n’a été créé par cette vue.")
    print("DECLARATION_READY ne signifie pas EXECUTED.")
    print("Causality status: NOT_ESTABLISHED")
    return result


def show_guided_status(
    measurements_root, preparation_registry_path=None, preparation_id=None, *, brain=None,
    presenter=None, reporter=None, registry_repository=None,
):
    analysis = (brain or AcousticBrain()).analyze(
        measurement_root=measurements_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
        synthesize_evidence_acquisition=True,
        return_context=True,
    )
    if not isinstance(analysis, tuple) or len(analysis) != 2:
        raise ValueError("Guided status requires an exact analysis context.")
    report, context = analysis
    synthesis = getattr(context, "evidence_acquisition_plan_synthesis", None)
    if synthesis is None:
        raise ValueError("Guided status evidence-plan contracts are unavailable.")
    registry = None
    if preparation_registry_path is not None:
        repository = (
            registry_repository or EvidencePlanPreparationRegistryJsonRepository()
        )
        registry = repository.load(preparation_registry_path)
    view = (presenter or GuidedGlobalStatusPresenter()).present(
        report,
        plans=synthesis.plans,
        preparation_registry=registry,
        preparation_id=preparation_id,
    )
    print(f"Measurement root: {measurements_root.resolve()}")
    print()
    (reporter or GuidedGlobalStatusConsoleReporter()).print(view)
    return view


def parse_preparation_statuses(values):
    result = {}
    for value in values:
        if not isinstance(value, str) or value.count("=") != 1:
            raise ValueError("Preparation statuses must use exact CODE=STATUS syntax.")
        code, raw_status = value.split("=", 1)
        if not code or code in result:
            raise ValueError(f"Duplicate or empty preparation status code: {code}.")
        try:
            result[code] = EvidencePlanPrerequisiteStatus(raw_status)
        except ValueError as error:
            raise ValueError(f"Invalid preparation status for {code}: {raw_status}.") from error
    return result


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
    evidence_plan_preparation_preview_service=None,
    channel_isolation_guided_execution_service=None,
    guided_preparation_revision_service=None,
    channel_isolation_operational_worksheet_service=None,
    channel_isolation_operational_record_preview_service=None,
    channel_isolation_documentation_review_service=None,
    channel_isolation_declaration_readiness_service=None,
    guided_global_status_presenter=None,
    guided_global_status_reporter=None,
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
        if arguments.guided_preparation_registry is not None and not arguments.guided_status:
            raise ValueError(
                "--guided-preparation-registry requires --guided-status."
            )
        if arguments.guided_preparation is not None:
            if not arguments.guided_status:
                raise ValueError("--guided-preparation requires --guided-status.")
            if arguments.guided_preparation_registry is None:
                raise ValueError(
                    "--guided-preparation requires --guided-preparation-registry."
                )
        if arguments.guided_status:
            conflicting = (
                ("--listening-position-campaign", arguments.listening_position_campaign is not None),
                ("--campaign-reference-qualification", arguments.campaign_reference_qualification is not None),
                ("--observations", arguments.observations),
                ("--reasoning", arguments.reasoning),
                ("--actions", arguments.actions),
                ("--weighting", arguments.weighting),
                ("--evidence-acquisition", arguments.evidence_acquisition),
                ("--full-assessment", arguments.full_assessment),
                ("--analysis-readiness", arguments.analysis_readiness),
                ("--assessment-summary", arguments.assessment_summary),
                ("--exploratory", arguments.exploratory),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
                ("--complete-evidence-plan", arguments.complete_evidence_plan is not None),
                ("--confirm-evidence-plan-preparation", arguments.confirm_evidence_plan_preparation is not None),
                ("--evidence-plan-preparation-view", arguments.evidence_plan_preparation_view is not None),
                ("--generate-evidence-plan-preparation", arguments.generate_evidence_plan_preparation is not None),
                ("--preview-evidence-plan-preparation", arguments.preview_evidence_plan_preparation is not None),
                ("--revise-evidence-plan-preparation", arguments.revise_evidence_plan_preparation is not None),
                ("--channel-isolation-journey", arguments.channel_isolation_journey is not None),
                ("--generate-channel-isolation-records", arguments.generate_channel_isolation_records is not None),
                ("--preview-channel-isolation-records", arguments.preview_channel_isolation_records is not None),
                ("--review-channel-isolation-documentation", arguments.review_channel_isolation_documentation is not None),
                ("--channel-isolation-declaration-readiness", arguments.channel_isolation_declaration_readiness is not None),
                ("--advisor", arguments.advisor),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        f"--guided-status cannot be combined with {option}."
                    )
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
            and arguments.preview_evidence_plan_preparation is None
            and arguments.channel_isolation_journey is None
            and arguments.channel_isolation_declaration_readiness is None
            and arguments.revise_evidence_plan_preparation is None
            and arguments.evidence_plan_preparation_registry is not None
        ):
            raise ValueError(
                "--evidence-plan-preparation-registry requires "
                "--confirm-evidence-plan-preparation or "
                "--evidence-plan-preparation-view or "
                "--generate-evidence-plan-preparation."
            )
        if arguments.preview_evidence_plan_preparation is not None and arguments.evidence_plan_preparation_registry is None:
            raise ValueError("--preview-evidence-plan-preparation requires --evidence-plan-preparation-registry.")
        if arguments.channel_isolation_journey is not None:
            if arguments.channel_isolation_preparation is None:
                raise ValueError("--channel-isolation-journey requires --channel-isolation-preparation.")
            if arguments.evidence_plan_preparation_registry is None:
                raise ValueError("--channel-isolation-journey requires --evidence-plan-preparation-registry.")
        elif (
            arguments.channel_isolation_declaration_readiness is None
            and arguments.channel_isolation_preparation is not None
        ):
            raise ValueError(
                "--channel-isolation-preparation requires a CHANNEL_ISOLATION journey or declaration-readiness mode."
            )
        if arguments.channel_isolation_declaration_readiness is not None:
            required = (
                ("--channel-isolation-preparation", arguments.channel_isolation_preparation),
                ("--evidence-plan-preparation-registry", arguments.evidence_plan_preparation_registry),
                ("--channel-isolation-reference", arguments.channel_isolation_reference),
                ("--channel-isolation-experiment", arguments.channel_isolation_experiment),
            )
            missing = tuple(option for option, value in required if value is None)
            if missing:
                raise ValueError(
                    "--channel-isolation-declaration-readiness requires "
                    + ", ".join(missing)
                    + "."
                )
            conflicting = (
                ("--channel-isolation-journey", arguments.channel_isolation_journey is not None),
                ("--full-assessment", arguments.full_assessment),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        "--channel-isolation-declaration-readiness cannot be combined "
                        f"with {option}."
                    )
        elif (
            arguments.channel_isolation_reference is not None
            or arguments.channel_isolation_experiment is not None
        ):
            raise ValueError(
                "CHANNEL_ISOLATION declaration identifiers require "
                "--channel-isolation-declaration-readiness."
            )
        if arguments.generate_channel_isolation_records is not None:
            if arguments.microphone_position_output is None or arguments.acquisition_settings_output is None:
                raise ValueError("--generate-channel-isolation-records requires both worksheet output paths.")
        elif arguments.microphone_position_output is not None or arguments.acquisition_settings_output is not None:
            raise ValueError("Worksheet output paths require --generate-channel-isolation-records.")
        if arguments.preview_channel_isolation_records is not None:
            if arguments.microphone_position_record is None or arguments.acquisition_settings_record is None:
                raise ValueError("--preview-channel-isolation-records requires both operational record paths.")
            conflicting = (
                ("--generate-channel-isolation-records", arguments.generate_channel_isolation_records is not None),
                ("--full-assessment", arguments.full_assessment),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        "--preview-channel-isolation-records cannot be combined "
                        f"with {option}."
                    )
        if arguments.review_channel_isolation_documentation is not None:
            if arguments.microphone_position_record is None or arguments.acquisition_settings_record is None:
                raise ValueError("--review-channel-isolation-documentation requires both operational record paths.")
            if arguments.channel_isolation_source_preparation is None:
                raise ValueError("--review-channel-isolation-documentation requires --channel-isolation-source-preparation.")
            conflicting = (
                ("--preview-channel-isolation-records", arguments.preview_channel_isolation_records is not None),
                ("--generate-channel-isolation-records", arguments.generate_channel_isolation_records is not None),
                ("--full-assessment", arguments.full_assessment),
                ("--experiment-view", arguments.experiment_view is not None),
                ("--evidence-plan-view", arguments.evidence_plan_view is not None),
                ("--evidence-plan-overview", arguments.evidence_plan_overview),
            )
            for option, enabled in conflicting:
                if enabled:
                    raise ValueError(
                        "--review-channel-isolation-documentation cannot be combined "
                        f"with {option}."
                    )
        elif arguments.channel_isolation_source_preparation is not None:
            raise ValueError("--channel-isolation-source-preparation requires --review-channel-isolation-documentation.")
        if (
            arguments.preview_channel_isolation_records is None
            and arguments.review_channel_isolation_documentation is None
            and (arguments.microphone_position_record is not None or arguments.acquisition_settings_record is not None)
        ):
            raise ValueError("Operational record paths require a channel-isolation preview or review mode.")
        if (
            arguments.evidence_plan_preparation_output is not None
            and arguments.generate_evidence_plan_preparation is None
            and arguments.revise_evidence_plan_preparation is None
        ):
            raise ValueError(
                "--evidence-plan-preparation-output requires "
                "--generate-evidence-plan-preparation."
            )
        if arguments.revise_evidence_plan_preparation is not None:
            if arguments.evidence_plan_preparation_registry is None:
                raise ValueError("--revise-evidence-plan-preparation requires --evidence-plan-preparation-registry.")
            if arguments.evidence_plan_preparation_output is None:
                raise ValueError("--revise-evidence-plan-preparation requires --evidence-plan-preparation-output.")
            if not arguments.preparation_status:
                raise ValueError("--revise-evidence-plan-preparation requires --preparation-status.")
        elif arguments.preparation_status:
            raise ValueError("--preparation-status requires --revise-evidence-plan-preparation.")
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
        if arguments.guided_status:
            show_guided_status(
                measurements_root,
                arguments.guided_preparation_registry,
                arguments.guided_preparation,
                brain=brain,
                presenter=guided_global_status_presenter,
                reporter=guided_global_status_reporter,
                registry_repository=evidence_plan_preparation_registry_repository,
            )
            return 0
        if arguments.preview_evidence_plan_preparation is not None:
            confirmation_input = (
                evidence_plan_preparation_loader
                or EvidencePlanPreparationConfirmationJsonLoader()
            ).load(arguments.preview_evidence_plan_preparation)
            preview_evidence_plan_preparation(
                measurements_root,
                confirmation_input,
                arguments.evidence_plan_preparation_registry,
                brain=brain,
                service=evidence_plan_preparation_preview_service,
                registry_repository=evidence_plan_preparation_registry_repository,
                input_path=arguments.preview_evidence_plan_preparation,
            )
            return 0
        if arguments.revise_evidence_plan_preparation is not None:
            loader = evidence_plan_preparation_loader or EvidencePlanPreparationConfirmationJsonLoader()
            revise_evidence_plan_preparation(
                measurements_root,
                loader.load(arguments.revise_evidence_plan_preparation),
                parse_preparation_statuses(arguments.preparation_status),
                arguments.evidence_plan_preparation_registry,
                arguments.evidence_plan_preparation_output,
                brain=brain,
                service=guided_preparation_revision_service,
                registry_repository=evidence_plan_preparation_registry_repository,
                serializer=guided_preparation_draft_serializer,
            )
            return 0
        if arguments.channel_isolation_journey is not None:
            show_channel_isolation_journey(
                measurements_root,
                arguments.channel_isolation_journey,
                arguments.channel_isolation_preparation,
                arguments.evidence_plan_preparation_registry,
                brain=brain,
                service=channel_isolation_guided_execution_service,
                registry_repository=evidence_plan_preparation_registry_repository,
            )
            return 0
        if arguments.channel_isolation_declaration_readiness is not None:
            show_channel_isolation_declaration_readiness(
                measurements_root,
                arguments.channel_isolation_declaration_readiness,
                arguments.channel_isolation_preparation,
                arguments.evidence_plan_preparation_registry,
                arguments.channel_isolation_reference,
                arguments.channel_isolation_experiment,
                brain=brain,
                service=channel_isolation_declaration_readiness_service,
                registry_repository=evidence_plan_preparation_registry_repository,
            )
            return 0
        if arguments.generate_channel_isolation_records is not None:
            generate_channel_isolation_records(
                measurements_root,
                arguments.generate_channel_isolation_records,
                arguments.microphone_position_output,
                arguments.acquisition_settings_output,
                brain=brain,
                service=channel_isolation_operational_worksheet_service,
            )
            return 0
        if arguments.preview_channel_isolation_records is not None:
            preview_channel_isolation_records(
                measurements_root,
                arguments.preview_channel_isolation_records,
                arguments.microphone_position_record,
                arguments.acquisition_settings_record,
                brain=brain,
                service=channel_isolation_operational_record_preview_service,
            )
            return 0
        if arguments.review_channel_isolation_documentation is not None:
            review_channel_isolation_documentation(
                measurements_root,
                arguments.review_channel_isolation_documentation,
                arguments.microphone_position_record,
                arguments.acquisition_settings_record,
                arguments.channel_isolation_source_preparation,
                brain=brain,
                service=channel_isolation_documentation_review_service,
                preparation_loader=evidence_plan_preparation_loader,
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
