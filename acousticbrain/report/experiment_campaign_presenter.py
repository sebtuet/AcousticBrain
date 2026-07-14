from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedCampaignMeasurement:
    experiment_id: str
    role: str
    offset_m: float
    state: str


@dataclass(frozen=True)
class PresentedCampaignMetric:
    code: str
    reference_value: float
    best_value: float
    improvement: float
    improvement_percent: float
    unit: str
    best_experiment_id: str


@dataclass(frozen=True)
class PresentedCampaignBranchResult:
    experiment_id: str
    role: str
    offset_m: float
    acoustic_outcome: str
    result_labels: tuple[str, ...]
    reference_value: float | None
    observed_value: float | None


@dataclass(frozen=True)
class PresentedCampaignConclusion:
    label: str
    established: bool


@dataclass(frozen=True)
class PresentedExperimentCampaign:
    campaign_code: str
    protocol_id: str
    hypothesis_code: str
    objective_label: str
    status: str
    reference_experiment_id: str | None
    measurements: tuple[PresentedCampaignMeasurement, ...]
    branch_results: tuple[PresentedCampaignBranchResult, ...]
    result_labels: tuple[str, ...]
    conclusions: tuple[PresentedCampaignConclusion, ...]
    unresolved_discrimination_labels: tuple[str, ...]
    metrics: tuple[PresentedCampaignMetric, ...]
    next_discrimination_label: str | None
    trace_id: str
    trace_comparison_result_ids: tuple[str, ...]
    trace_observation_codes: tuple[str, ...]
    trace_applied_rule_codes: tuple[str, ...]
    detailed_traceability: bool

    def to_dict(self):
        return asdict(self)


class ExperimentCampaignPresenter:
    """Projette les synthèses de campagne sans agréger ni conclure."""

    RESULT_LABELS = {
        "BASS_DECAY_REDUCED_AT_TARGET_BANDS": (
            "la décroissance diminue dans les bandes ciblées"
        ),
        "BASS_DECAY_STABLE_AT_TARGET_BANDS": (
            "la décroissance reste stable dans les bandes ciblées"
        ),
        "BASS_DECAY_VARIES_BY_LISTENING_POSITION": (
            "la décroissance grave varie selon la position d’écoute"
        ),
        "LOCAL_POSITION_EFFECT_SUPPORTED": (
            "un effet local de position est soutenu"
        ),
        "GLOBAL_MODAL_COMPONENT_NOT_DISCRIMINATED": (
            "la composante modale globale reste non discriminée"
        ),
    }
    DISCRIMINATION_LABELS = {
        "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE": (
            "effet local de position vs composante modale globale"
        ),
        "SOURCE_EXCITATION_VS_LISTENER_POSITION": (
            "excitation par la source vs position d’écoute"
        ),
    }
    OBJECTIVE_LABELS = {
        "DETERMINE_BASS_DECAY_LISTENING_POSITION_DEPENDENCE": (
            "déterminer si la persistance du grave dépend du point d’écoute"
        ),
    }
    NEXT_DISCRIMINATION_LABELS = {
        "CONTROLLED_SOURCE_VARIATION_WITH_FIXED_LISTENER": (
            "variation contrôlée de la position de la source, microphone fixe"
        ),
        "CONTROLLED_SOURCE_AND_LISTENER_MATRIX": (
            "matrice contrôlée de positions de source et d’écoute"
        ),
    }
    OPEN_RESULT_CODES = {"GLOBAL_MODAL_COMPONENT_NOT_DISCRIMINATED"}

    def present(self, context):
        analyses = getattr(context, "experiment_campaign_analyses", ())
        return tuple(self._campaign(item) for item in analyses)

    def _campaign(self, analysis):
        return PresentedExperimentCampaign(
            campaign_code=analysis.campaign_code,
            protocol_id=analysis.protocol_id,
            hypothesis_code=analysis.hypothesis_code,
            objective_label=self.OBJECTIVE_LABELS.get(
                analysis.objective_code, analysis.objective_code
            ),
            status=analysis.status.value,
            reference_experiment_id=analysis.reference_experiment_id,
            measurements=tuple(
                PresentedCampaignMeasurement(
                    experiment_id=item.experiment_id,
                    role=item.role,
                    offset_m=item.offset_m,
                    state=item.state,
                )
                for item in analysis.measurements
            ),
            branch_results=tuple(
                PresentedCampaignBranchResult(
                    experiment_id=item.experiment_id,
                    role=item.role,
                    offset_m=item.offset_m,
                    acoustic_outcome=item.acoustic_outcome,
                    result_labels=tuple(
                        self.RESULT_LABELS.get(code, code)
                        for code in item.result_codes
                    ),
                    reference_value=item.reference_value,
                    observed_value=item.observed_value,
                )
                for item in analysis.branch_results
            ),
            result_labels=tuple(
                self.RESULT_LABELS.get(code, code)
                for code in analysis.result_codes
            ),
            conclusions=tuple(
                PresentedCampaignConclusion(
                    label=self.RESULT_LABELS.get(code, code),
                    established=code not in self.OPEN_RESULT_CODES,
                )
                for code in analysis.result_codes
            ),
            unresolved_discrimination_labels=tuple(
                self.DISCRIMINATION_LABELS.get(code, code)
                for code in analysis.unresolved_discrimination_codes
            ),
            metrics=tuple(
                PresentedCampaignMetric(
                    code=item.code,
                    reference_value=item.reference_value,
                    best_value=item.best_value,
                    improvement=item.improvement,
                    improvement_percent=item.improvement_percent,
                    unit=item.unit,
                    best_experiment_id=item.best_experiment_id,
                )
                for item in analysis.metrics
            ),
            next_discrimination_label=(
                self.NEXT_DISCRIMINATION_LABELS.get(
                    analysis.next_discrimination_code,
                    analysis.next_discrimination_code,
                )
                if analysis.next_discrimination_code is not None
                else None
            ),
            trace_id=analysis.trace.trace_id,
            trace_comparison_result_ids=analysis.trace.comparison_result_ids,
            trace_observation_codes=analysis.trace.observation_codes,
            trace_applied_rule_codes=analysis.trace.applied_rule_codes,
            detailed_traceability=analysis.detailed_traceability,
        )
