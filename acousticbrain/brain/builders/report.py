from acousticbrain.report import (
    GlobalPresenter,
    RecommendationPresenter,
    Report,
    TraceabilityPresenter,
    RoomGeometryPresenter,
    OptimizationSessionPresenter,
    ExperimentPlanningPresenter,
    ExperimentDiscoveryPresenter,
    ExperimentComparisonPresenter,
    CausalDiscriminationPresenter,
    ExperimentCampaignPresenter,
    SurfaceMaterialPresenter,
    MaterialAwareReflectionCandidatePresenter,
    ControlledReflectionVerificationPlanningPresenter,
    ControlledReflectionExperimentDeclarationPresenter,
    ControlledReflectionExperimentComparisonPresenter,
    ControlledReflectionHypothesisStatusPresenter,
    LoudspeakerPositioningExperimentPresenter,
    LongitudinalExperimentalLearningPresenter,
    AcousticHypothesisExperimentGenerationPresenter,
)


class ReportBuilder:
    """
    Construit le rapport d'analyse.
    """

    def build(self, project, context):

        report = Report(
            project_name=project.name
        )

        report.room_properties = (
            context.room_properties
        )

        report.recommendations = RecommendationPresenter().present(context)
        report.global_analysis = GlobalPresenter().present(context)
        report.traceability_analysis = TraceabilityPresenter().present(context)
        report.room_geometry = RoomGeometryPresenter().present(context)
        report.optimization_session = OptimizationSessionPresenter().present(context)
        report.experiment_planning = ExperimentPlanningPresenter().present(context)
        report.loudspeaker_positioning_experiment = (
            LoudspeakerPositioningExperimentPresenter().present(context)
        )
        report.experiments_discovered = ExperimentDiscoveryPresenter().present(context)
        report.experiment_comparison = ExperimentComparisonPresenter().present(context)
        report.experiment_campaigns = ExperimentCampaignPresenter().present(context)
        report.causal_discrimination = CausalDiscriminationPresenter().present(context)
        report.longitudinal_experimental_learning = (
            LongitudinalExperimentalLearningPresenter().present(context)
        )
        report.acoustic_hypothesis_experiment_generation = (
            AcousticHypothesisExperimentGenerationPresenter().present(context)
        )
        report.surface_materials = SurfaceMaterialPresenter().present(context)
        report.material_aware_reflection_candidates = (
            MaterialAwareReflectionCandidatePresenter().present(context)
        )
        report.controlled_reflection_verification_planning = (
            ControlledReflectionVerificationPlanningPresenter().present(context)
        )
        report.controlled_reflection_experiment_declarations = (
            ControlledReflectionExperimentDeclarationPresenter().present(context)
        )
        report.controlled_reflection_experiment_comparisons = (
            ControlledReflectionExperimentComparisonPresenter().present(context)
        )
        report.controlled_reflection_hypothesis_status_updates = (
            ControlledReflectionHypothesisStatusPresenter().present(context)
        )

        return report
