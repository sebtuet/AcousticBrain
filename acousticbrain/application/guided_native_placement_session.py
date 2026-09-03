"""Guided native placement workflow orchestration without acoustic rules."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from acousticbrain.models import ComparisonEligibilityStatus, ExperimentKind

from .channel_isolation_repeatability_evaluation import (
    ChannelIsolationRepeatabilityEvaluationService,
)
from .channel_isolation_repeatability_qualification import (
    ChannelIsolationRepeatabilityQualificationService,
    ChannelIsolationRepeatabilityQualificationStatus,
)
from .experiment_declaration import ExperimentDeclarationService
from .experiment_discovery import ExperimentDiscoveryService
from .placement_comparison_qualification import (
    PlacementComparisonStatus,
)
from .placement_comparison_selection_qualification import (
    PlacementComparisonSelectionQualificationService,
)


class GuidedNativePlacementVerdict(str, Enum):
    KEEP = "KEEP"
    REVERT = "REVERT"
    INDETERMINATE = "INDETERMINATE"


class GuidedNativePlacementSessionStatus(str, Enum):
    KEEP = "KEEP"
    REVERT = "REVERT"
    INDETERMINATE = "INDETERMINATE"
    REFERENCE_CAPTURE_INVALID = "REFERENCE_CAPTURE_INVALID"
    REFERENCE_NOT_QUALIFIED = "REFERENCE_NOT_QUALIFIED"
    CANDIDATE_CAPTURE_INVALID = "CANDIDATE_CAPTURE_INVALID"
    CANDIDATE_NOT_QUALIFIED = "CANDIDATE_NOT_QUALIFIED"
    COMPARISON_NOT_COMPARABLE = "COMPARISON_NOT_COMPARABLE"


@dataclass(frozen=True)
class GuidedNativePlacementSessionConfig:
    measurements_root: Path
    input_device: str
    output_device: str
    calibration_file: Path
    sample_rate_hz: int = 44100
    sweep_duration_s: float = 5.0
    sweep_level_dbfs: float = -24.0
    reference_experiment_id: str | None = None
    candidate_experiment_id: str | None = None


@dataclass(frozen=True)
class GuidedNativePlacementSessionResult:
    status: GuidedNativePlacementSessionStatus
    verdict: GuidedNativePlacementVerdict
    reference_experiment_id: str | None
    candidate_experiment_id: str | None
    comparison_id: str | None
    placement_status: PlacementComparisonStatus | None
    reference_repeatability_qualification: object | None
    candidate_repeatability_qualification: object | None
    comparison_eligibility: ComparisonEligibilityStatus | None
    blocking_reason_codes: tuple[str, ...]
    displacement_description: str | None
    causality_status: str = "NOT_ESTABLISHED"


class GuidedNativePlacementVerdictProjector:
    """Projects existing placement statuses to product wording only."""

    _VERDICT_BY_STATUS = {
        PlacementComparisonStatus.BETTER: GuidedNativePlacementVerdict.KEEP,
        PlacementComparisonStatus.WORSE: GuidedNativePlacementVerdict.REVERT,
        PlacementComparisonStatus.EQUIVALENT: (
            GuidedNativePlacementVerdict.INDETERMINATE
        ),
        PlacementComparisonStatus.INDETERMINATE: (
            GuidedNativePlacementVerdict.INDETERMINATE
        ),
    }

    def project(self, placement_status):
        if placement_status is None:
            return GuidedNativePlacementVerdict.INDETERMINATE
        return self._VERDICT_BY_STATUS[placement_status]


class GuidedNativePlacementSessionService:
    """Orchestrates native capture and existing comparison/qualification services."""

    def __init__(
        self,
        *,
        capture_service=None,
        discovery_service=None,
        repeatability_evaluation_service=None,
        repeatability_qualification_service=None,
        experiment_declaration_service=None,
        brain=None,
        selection_qualification_service=None,
        verdict_projector=None,
        clock=None,
        input_func=input,
        output_func=print,
    ):
        if capture_service is None:
            from acousticbrain.acquisition import NativePlacementCaptureService

            capture_service = NativePlacementCaptureService()
        self.capture_service = capture_service
        self.discovery_service = discovery_service or ExperimentDiscoveryService()
        self.repeatability_evaluation_service = (
            repeatability_evaluation_service
            or ChannelIsolationRepeatabilityEvaluationService()
        )
        self.repeatability_qualification_service = (
            repeatability_qualification_service
            or ChannelIsolationRepeatabilityQualificationService()
        )
        self.experiment_declaration_service = (
            experiment_declaration_service or ExperimentDeclarationService()
        )
        if brain is None:
            from acousticbrain.brain import AcousticBrain

            brain = AcousticBrain()
        self.brain = brain
        self.selection_qualification_service = (
            selection_qualification_service
            or PlacementComparisonSelectionQualificationService()
        )
        self.verdict_projector = verdict_projector or GuidedNativePlacementVerdictProjector()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.input_func = input_func
        self.output_func = output_func

    def run(
        self, config: GuidedNativePlacementSessionConfig
    ) -> GuidedNativePlacementSessionResult:
        root = Path(config.measurements_root)
        reference_id, candidate_id = self._experiment_ids(config)

        self.output_func("AcousticBrain — Placement guidé expérimental")
        self.output_func("")
        self.output_func("Étape 1/3 — Référence")
        self.output_func("Ne déplacez ni le microphone ni les enceintes.")
        self.output_func("Mesure de la position actuelle...")
        reference_summary = self._capture(config, reference_id)
        reference_qualification = self._qualified_capture(reference_summary)
        if reference_qualification is None:
            return self._stopped(
                GuidedNativePlacementSessionStatus.REFERENCE_CAPTURE_INVALID,
                reference_id,
                None,
                "REFERENCE_CAPTURE_INVALID",
            )
        if not self._is_qualified(reference_qualification):
            self.output_func("Référence non suffisamment répétable.")
            self.output_func("La session est arrêtée avant comparaison.")
            return self._stopped(
                GuidedNativePlacementSessionStatus.REFERENCE_NOT_QUALIFIED,
                reference_id,
                None,
                *reference_qualification.reason_codes,
                reference_qualification=reference_qualification,
            )
        self.output_func(f"Référence validée : {reference_id}")
        self.output_func("")
        self.output_func("Étape 2/3 — Déplacement")
        self.output_func("Déplacez une seule enceinte.")
        self.output_func("Ne déplacez pas le microphone.")
        self.output_func("Ne changez pas le volume.")
        description = self._ask_displacement_description()
        self._wait_for_displacement()

        self.output_func("")
        self.output_func("Étape 3/3 — Candidate")
        self.output_func("Mesure de la position candidate...")
        candidate_summary = self._capture(config, candidate_id)
        candidate_qualification = self._qualified_capture(candidate_summary)
        if candidate_qualification is None:
            return self._stopped(
                GuidedNativePlacementSessionStatus.CANDIDATE_CAPTURE_INVALID,
                reference_id,
                candidate_id,
                "CANDIDATE_CAPTURE_INVALID",
                reference_qualification=reference_qualification,
                displacement_description=description,
            )
        self._declare_candidate(root, candidate_id, reference_id, description)
        if not self._is_qualified(candidate_qualification):
            self.output_func("Mesure candidate non suffisamment répétable.")
            self.output_func("Impossible de conclure sur le placement.")
            return self._stopped(
                GuidedNativePlacementSessionStatus.CANDIDATE_NOT_QUALIFIED,
                reference_id,
                candidate_id,
                *candidate_qualification.reason_codes,
                reference_qualification=reference_qualification,
                candidate_qualification=candidate_qualification,
                displacement_description=description,
            )

        qualifications = (reference_qualification, candidate_qualification)
        try:
            comparison_analysis = self._comparison_analysis(root, qualifications)
        except ValueError as error:
            return self._stopped(
                GuidedNativePlacementSessionStatus.COMPARISON_NOT_COMPARABLE,
                reference_id,
                candidate_id,
                "MEASURED_STEREO_UNAVAILABLE",
                reference_qualification=reference_qualification,
                candidate_qualification=candidate_qualification,
                displacement_description=description,
            )
        comparison_id = self._local_comparison_id(
            comparison_analysis, reference_id, candidate_id
        )
        selection = self.selection_qualification_service.qualify(
            comparison_analysis,
            comparison_id,
            qualifications,
        )
        if selection.placement_qualification is None:
            eligibility = getattr(selection.comparison, "eligibility", None)
            return self._stopped(
                GuidedNativePlacementSessionStatus.COMPARISON_NOT_COMPARABLE,
                reference_id,
                candidate_id,
                *selection.blocking_reason_codes,
                reference_qualification=reference_qualification,
                candidate_qualification=candidate_qualification,
                comparison_id=comparison_id,
                comparison_eligibility=eligibility,
                displacement_description=description,
            )
        placement_status = selection.placement_qualification.comparison_status
        verdict = self.verdict_projector.project(placement_status)
        status = {
            GuidedNativePlacementVerdict.KEEP: GuidedNativePlacementSessionStatus.KEEP,
            GuidedNativePlacementVerdict.REVERT: GuidedNativePlacementSessionStatus.REVERT,
            GuidedNativePlacementVerdict.INDETERMINATE: (
                GuidedNativePlacementSessionStatus.INDETERMINATE
            ),
        }[verdict]
        return GuidedNativePlacementSessionResult(
            status=status,
            verdict=verdict,
            reference_experiment_id=reference_id,
            candidate_experiment_id=candidate_id,
            comparison_id=comparison_id,
            placement_status=placement_status,
            reference_repeatability_qualification=reference_qualification,
            candidate_repeatability_qualification=candidate_qualification,
            comparison_eligibility=selection.comparison.eligibility,
            blocking_reason_codes=selection.blocking_reason_codes,
            displacement_description=description,
        )

    def _capture(self, config, experiment_id):
        from acousticbrain.acquisition import NativePlacementCaptureConfig

        return self.capture_service.capture(NativePlacementCaptureConfig(
            measurements_root=Path(config.measurements_root),
            input_device=config.input_device,
            output_device=config.output_device,
            calibration_file=Path(config.calibration_file),
            sample_rate_hz=config.sample_rate_hz,
            sweep_duration_s=config.sweep_duration_s,
            sweep_level_dbfs=config.sweep_level_dbfs,
            experiment_id=experiment_id,
        ))

    def _qualified_capture(self, summary):
        qualifications = self._qualifications_for(
            summary.experiment_directory.parent, summary.experiment_id
        )
        matches = tuple(
            item
            for item in qualifications
            if item.provenance.experiment_id == summary.experiment_id
        )
        return matches[0] if len(matches) == 1 else None

    def _qualifications_for(self, measurements_root, experiment_id):
        descriptors = tuple(
            item
            for item in self.discovery_service.discover(measurements_root)
            if item.experiment_id == experiment_id
        )
        evaluations = self.repeatability_evaluation_service.evaluate(descriptors)
        return self.repeatability_qualification_service.qualify(evaluations)

    def _comparison_analysis(self, measurements_root, qualifications):
        result = self.brain.analyze(
            measurement_root=Path(measurements_root),
            compare_experiments=True,
            analyze_causal_discrimination=True,
            channel_isolation_repeatability_qualifications=qualifications,
            return_context=True,
        )
        if not isinstance(result, tuple) or len(result) != 2:
            raise ValueError("Guided native placement requires an analysis context.")
        _, context = result
        analysis = getattr(context, "experiment_comparison_analysis", None)
        if analysis is None:
            raise ValueError("Guided native placement comparison is unavailable.")
        return analysis

    @staticmethod
    def _local_comparison_id(comparison_analysis, reference_id, candidate_id):
        matches = tuple(
            item
            for item in comparison_analysis.sequence.local_comparisons
            if item.before_experiment_id == reference_id
            and item.after_experiment_id == candidate_id
        )
        if len(matches) != 1:
            raise ValueError(
                "Guided native placement requires one explicit local "
                f"comparison: {reference_id} -> {candidate_id}."
            )
        return matches[0].trace.trace_id

    def _declare_candidate(self, measurements_root, candidate_id, reference_id, description):
        self.experiment_declaration_service.declare(
            measurements_root,
            experiment_code=candidate_id,
            experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
            reference_experiment_code=reference_id,
            modified_variables=("LOUDSPEAKER_POSITION",),
            controlled_variables=("MEASUREMENT_LEVEL", "MICROPHONE_POSITION"),
            user_note=description,
            provenance_source="USER_NATIVE_PLACEMENT_SESSION",
        )
        self.discovery_service.discover(measurements_root)

    def _ask_displacement_description(self):
        try:
            return self.input_func("Déplacement effectué : ").strip() or None
        except EOFError as error:
            raise ValueError("La description du déplacement est requise.") from error

    def _wait_for_displacement(self):
        try:
            self.input_func("Appuyez sur Entrée lorsque le déplacement est terminé.")
        except EOFError as error:
            raise ValueError("La confirmation du déplacement est requise.") from error

    def _experiment_ids(self, config):
        timestamp = self.clock().strftime("%Y%m%d-%H%M%S")
        reference = config.reference_experiment_id or (
            f"exp-native-reference-{timestamp}"
        )
        candidate = config.candidate_experiment_id or (
            f"exp-native-candidate-{timestamp}"
        )
        if reference == candidate:
            raise ValueError("Reference and candidate experiment ids must differ.")
        return reference, candidate

    @staticmethod
    def _is_qualified(qualification):
        return (
            qualification.qualification_status
            is ChannelIsolationRepeatabilityQualificationStatus.QUALIFIED
        )

    @staticmethod
    def _stopped(
        status,
        reference_id,
        candidate_id,
        *reason_codes,
        reference_qualification=None,
        candidate_qualification=None,
        comparison_id=None,
        comparison_eligibility=None,
        displacement_description=None,
    ):
        return GuidedNativePlacementSessionResult(
            status=status,
            verdict=GuidedNativePlacementVerdict.INDETERMINATE,
            reference_experiment_id=reference_id,
            candidate_experiment_id=candidate_id,
            comparison_id=comparison_id,
            placement_status=None,
            reference_repeatability_qualification=reference_qualification,
            candidate_repeatability_qualification=candidate_qualification,
            comparison_eligibility=comparison_eligibility,
            blocking_reason_codes=tuple(reason_codes),
            displacement_description=displacement_description,
        )
