from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedExpectedExperimentalObservation:
    observation_code: str
    outcome: str
    measured_fact_codes: tuple[str, ...]


@dataclass(frozen=True)
class PresentedGeneratedAcquisitionPosition:
    position_id: str
    role: str
    longitudinal_offset_m: float
    lateral_offset_m: float | None
    required_measurements: tuple[str, ...]
    acquisition_order: int


@dataclass(frozen=True)
class PresentedGeneratedAcousticExperiment:
    candidate_id: str
    hypothesis_code: str
    experiment_type: str
    target: str
    movement_axis: str | None
    movement_direction: str | None
    step_distance_m: float | None
    modified_variables: tuple[str, ...]
    controlled_variables: tuple[str, ...]
    required_measurements: tuple[str, ...]
    expected_observations: tuple[PresentedExpectedExperimentalObservation, ...]
    expected_frequency_regions: tuple[tuple[float, float], ...]
    expected_time_regions: tuple[tuple[float, float], ...]
    information_value: float
    reversibility: str
    difficulty: str
    blocking_reasons: tuple[str, ...]
    rationale_codes: tuple[str, ...]
    acquisition_positions: tuple[PresentedGeneratedAcquisitionPosition, ...]
    reference_position_id: str | None
    comparability_rule_code: str | None
    causality_status: str


@dataclass(frozen=True)
class PresentedGeneratedAcousticHypothesis:
    hypothesis_code: str
    status: str
    supporting_fact_codes: tuple[str, ...]
    contradicting_fact_codes: tuple[str, ...]
    missing_fact_codes: tuple[str, ...]
    experiment_candidate_ids: tuple[str, ...]
    expected_observation_codes: tuple[str, ...]
    rationale_codes: tuple[str, ...]
    uncertainty_reasons: tuple[str, ...]
    causality_status: str


@dataclass(frozen=True)
class PresentedAcousticHypothesisExperimentGeneration:
    hypotheses: tuple[PresentedGeneratedAcousticHypothesis, ...]
    experiments: tuple[PresentedGeneratedAcousticExperiment, ...]
    recommended_candidate_id: str | None
    applied_rule_codes: tuple[str, ...]
    source_analysis_codes: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


class AcousticHypothesisExperimentGenerationPresenter:
    def present(self, context):
        analysis = getattr(
            context, "acoustic_hypothesis_experiment_generation_analysis", None
        )
        if analysis is None:
            return None
        return PresentedAcousticHypothesisExperimentGeneration(
            hypotheses=tuple(
                PresentedGeneratedAcousticHypothesis(
                    hypothesis_code=item.hypothesis_code,
                    status=item.status.value,
                    supporting_fact_codes=item.supporting_fact_codes,
                    contradicting_fact_codes=item.contradicting_fact_codes,
                    missing_fact_codes=item.missing_fact_codes,
                    experiment_candidate_ids=item.experiment_candidate_ids,
                    expected_observation_codes=item.expected_observation_codes,
                    rationale_codes=item.rationale_codes,
                    uncertainty_reasons=item.uncertainty_reasons,
                    causality_status=item.causality_status,
                )
                for item in analysis.hypotheses
            ),
            experiments=tuple(self._experiment(item) for item in analysis.ordered_experiments),
            recommended_candidate_id=analysis.recommended_candidate_id,
            applied_rule_codes=analysis.applied_rule_codes,
            source_analysis_codes=analysis.source_analysis_codes,
        )

    @staticmethod
    def _experiment(item):
        return PresentedGeneratedAcousticExperiment(
            candidate_id=item.candidate_id,
            hypothesis_code=item.hypothesis_code,
            experiment_type=item.experiment_type.value,
            target=item.target,
            movement_axis=item.movement_axis,
            movement_direction=item.movement_direction,
            step_distance_m=item.step_distance_m,
            modified_variables=item.modified_variables,
            controlled_variables=item.controlled_variables,
            required_measurements=item.required_measurements,
            expected_observations=tuple(
                PresentedExpectedExperimentalObservation(
                    observation_code=observation.observation_code,
                    outcome=observation.outcome.value,
                    measured_fact_codes=observation.measured_fact_codes,
                )
                for observation in item.expected_observations
            ),
            expected_frequency_regions=item.expected_frequency_regions,
            expected_time_regions=item.expected_time_regions,
            information_value=item.information_value,
            reversibility=item.reversibility.name,
            difficulty=item.difficulty.name,
            blocking_reasons=item.blocking_reasons,
            rationale_codes=item.rationale_codes,
            acquisition_positions=tuple(
                PresentedGeneratedAcquisitionPosition(
                    position_id=position.position_id,
                    role=position.role,
                    longitudinal_offset_m=position.longitudinal_offset_m,
                    lateral_offset_m=position.lateral_offset_m,
                    required_measurements=position.required_measurements,
                    acquisition_order=position.acquisition_order,
                )
                for position in item.acquisition_positions
            ),
            reference_position_id=item.reference_position_id,
            comparability_rule_code=item.comparability_rule_code,
            causality_status=item.causality_status,
        )
