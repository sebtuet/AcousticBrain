from dataclasses import dataclass, field

from acousticbrain.diagnostics import Diagnostic
from acousticbrain.models import DiagnosticPriorityAnalysis

from .recommendation import PresentedRecommendation

from .global_presenter import PresentedGlobalAnalysis

from .traceability_presenter import PresentedTraceabilityAnalysis
from .room_geometry_presenter import PresentedRoomGeometry
from .optimization_session_presenter import PresentedOptimizationSession
from .experiment_planning_presenter import PresentedExperimentPlanning
from .experiment_discovery_presenter import PresentedExperimentDiscovery
from .experiment_comparison_presenter import PresentedExperimentComparison
from .causal_discrimination_presenter import PresentedCausalDiscrimination
from .experiment_campaign_presenter import PresentedExperimentCampaign
from .surface_material_presenter import PresentedSurfaceMaterialAnalysis


@dataclass
class Report:

    project_name: str

    room_properties = None

    diagnostics: list[Diagnostic] = field(default_factory=list)

    diagnostic_priority: DiagnosticPriorityAnalysis | None = None

    recommendations: list[PresentedRecommendation] = field(default_factory=list)

    global_analysis: PresentedGlobalAnalysis | None = None

    traceability_analysis: PresentedTraceabilityAnalysis | None = None

    room_geometry: PresentedRoomGeometry | None = None

    optimization_session: PresentedOptimizationSession | None = None

    experiment_planning: PresentedExperimentPlanning | None = None

    experiments_discovered: PresentedExperimentDiscovery | None = None

    experiment_comparison: PresentedExperimentComparison | None = None

    experiment_campaigns: tuple[PresentedExperimentCampaign, ...] = ()

    causal_discrimination: PresentedCausalDiscrimination | None = None

    surface_materials: PresentedSurfaceMaterialAnalysis | None = None

    def add(self, diagnostic):

        self.diagnostics.append(diagnostic)
