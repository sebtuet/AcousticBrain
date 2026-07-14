from .pipeline import BrainPipeline

from acousticbrain.application import (
    AcousticSession,
    AutomaticExperimentComparisonService,
    CausalDiscriminationService,
    ExperimentCampaignSynthesisService,
)
from acousticbrain.report import (
    ExperimentComparisonPresenter,
    CausalDiscriminationPresenter,
    ExperimentDiscoveryPresenter,
    ExperimentCampaignPresenter,
    Report,
)


class AcousticBrain:

    def __init__(self):

        self.pipeline = BrainPipeline()

    def analyze(
        self,
        project=None,
        *,
        session_context=None,
        plan_experiments=False,
        measurement_root=None,
        compare_experiments=False,
        detailed_comparison_traceability=False,
        analyze_causal_discrimination=False,
    ):

        experiment_descriptors = ()
        if measurement_root is not None:
            if project is not None or (session_context is not None and not compare_experiments):
                raise ValueError(
                    "measurement_root cannot be combined with project or session_context."
                )
            acoustic_session = AcousticSession.auto_open(measurement_root)
            project = acoustic_session.current_project
            experiment_descriptors = acoustic_session.descriptors
            plan_experiments = True
            if compare_experiments:
                return self._analyze_experiments(
                    acoustic_session,
                    plan_experiments=plan_experiments,
                    detailed_traceability=detailed_comparison_traceability,
                    optimization_session=(
                        session_context.session if session_context is not None else None
                    ),
                    analyze_causal_discrimination=analyze_causal_discrimination,
                )
            if project is None:
                report = Report(project_name=str(measurement_root))
                context = type(
                    "DiscoveryContext",
                    (),
                    {"experiment_descriptors": experiment_descriptors},
                )()
                report.experiments_discovered = (
                    ExperimentDiscoveryPresenter().present(context)
                )
                return report
        if project is None:
            raise ValueError("A project or measurement_root is required.")
        if compare_experiments:
            raise ValueError("compare_experiments requires measurement_root.")
        if analyze_causal_discrimination:
            raise ValueError(
                "analyze_causal_discrimination requires measurement_root and "
                "compare_experiments=True."
            )

        return self.pipeline.run(
            project,
            session_context=session_context,
            plan_experiments=plan_experiments,
            experiment_descriptors=experiment_descriptors,
        )

    def _analyze_experiments(
        self,
        acoustic_session,
        *,
        plan_experiments,
        detailed_traceability,
        optimization_session,
        analyze_causal_discrimination,
    ):
        contexts = {}
        current_report = None
        current_context = None
        ready = [item for item in acoustic_session.experiments if item.project is not None]
        current = ready[-1] if ready else None
        for imported in ready:
            report, context = self.pipeline.run(
                imported.project,
                plan_experiments=plan_experiments and imported is current,
                experiment_descriptors=acoustic_session.descriptors,
                return_context=True,
            )
            contexts[imported.descriptor.experiment_id] = context
            if imported is current:
                current_report, current_context = report, context
        comparison = AutomaticExperimentComparisonService().analyze(
            acoustic_session,
            contexts,
            optimization_session=optimization_session,
            detailed_traceability=detailed_traceability,
        )
        if current_context is None:
            current_context = type(
                "ExperimentComparisonContext",
                (),
                {
                    "experiment_descriptors": acoustic_session.descriptors,
                    "experiment_comparison_analysis": comparison,
                },
            )()
            current_report = Report(project_name=acoustic_session.measurement_root)
            current_report.experiments_discovered = (
                ExperimentDiscoveryPresenter().present(current_context)
            )
        else:
            current_context.experiment_comparison_analysis = comparison
        campaign_analyses = ExperimentCampaignSynthesisService().analyze(
            acoustic_session.descriptors,
            comparison,
            detailed_traceability=detailed_traceability,
        )
        current_context.experiment_campaign_analyses = campaign_analyses
        causal_analysis = None
        if analyze_causal_discrimination:
            causal_analysis = CausalDiscriminationService().analyze(
                acoustic_session.descriptors,
                comparison,
                detailed_traceability=detailed_traceability,
            )
            current_context.causal_discrimination_analysis = causal_analysis
        current_report.experiment_comparison = (
            ExperimentComparisonPresenter().present(current_context)
        )
        current_report.experiment_campaigns = (
            ExperimentCampaignPresenter().present(current_context)
        )
        current_report.causal_discrimination = (
            CausalDiscriminationPresenter().present(current_context)
        )
        return current_report
