from statistics import fmean

from acousticbrain.analysis import FrequencyResponseFeatureAnalyzer
from acousticbrain.models import (
    AnalysisReadiness,
    ImpulseChannel,
    MeasurementAnalysisFamily,
    MeasurementReadinessAnalysis,
    MeasurementReadinessStatus,
)
from acousticbrain.project import Measurements


class FrequencyResponseFeatureStage:
    """Runs descriptive TXT analysis and enriches existing FREQUENCY readiness."""

    REQUIRED = (
        (ImpulseChannel.LEFT, Measurements.LEFT),
        (ImpulseChannel.RIGHT, Measurements.RIGHT),
        (ImpulseChannel.STEREO, Measurements.STEREO),
    )
    REQUIRED_RULE = "REQUIRE_FREQUENCY_RESPONSE_TXT_LEFT_RIGHT_STEREO"
    GRID_RULE = "REQUIRE_VALID_FREQUENCY_RESPONSE_GRID"

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or FrequencyResponseFeatureAnalyzer()

    def run(self, project, context):
        measurements = {}
        missing_facts = []
        for channel, name in self.REQUIRED:
            measurement = project.get_measurement(name)
            if measurement is None:
                missing_facts.append(f"FREQUENCY_RESPONSE_TXT_{channel.value}")
                continue
            try:
                self.analyzer.validate_measurement(measurement)
            except (TypeError, ValueError):
                missing_facts.append(
                    f"VALID_FREQUENCY_RESPONSE_DATA_{channel.value}"
                )
                continue
            measurements[channel] = measurement

        self._update_readiness(context, tuple(missing_facts))
        if missing_facts:
            context.frequency_response_feature_analysis = None
            return
        context.frequency_response_feature_analysis = self.analyzer.analyze(
            measurements[ImpulseChannel.LEFT],
            measurements[ImpulseChannel.RIGHT],
            measurements[ImpulseChannel.STEREO],
        )

    def _update_readiness(self, context, missing_facts):
        readiness = context.measurement_readiness_analysis
        if readiness is None:
            return
        existing = next(
            (
                item
                for item in readiness.analyses
                if item.family is MeasurementAnalysisFamily.FREQUENCY
            ),
            None,
        )
        if existing is None:
            return
        combined_missing = tuple(
            dict.fromkeys((*existing.missing_facts, *missing_facts))
        )
        status = (
            MeasurementReadinessStatus.BLOCKED
            if existing.blocking_issues or combined_missing
            else MeasurementReadinessStatus.AVAILABLE_WITH_RESERVATIONS
            if existing.non_blocking_issues
            else MeasurementReadinessStatus.AVAILABLE
        )
        updated = AnalysisReadiness(
            family=existing.family,
            status=status,
            blocking_issues=existing.blocking_issues,
            non_blocking_issues=existing.non_blocking_issues,
            required_channels=tuple(channel for channel, _ in self.REQUIRED),
            missing_facts=combined_missing,
            confidence=existing.confidence,
            applied_rule_codes=tuple(
                dict.fromkeys(
                    (
                        *existing.applied_rule_codes,
                        self.REQUIRED_RULE,
                        self.GRID_RULE,
                    )
                )
            ),
        )
        analyses = tuple(
            updated
            if item.family is MeasurementAnalysisFamily.FREQUENCY
            else item
            for item in readiness.analyses
        )
        context.measurement_readiness_analysis = MeasurementReadinessAnalysis(
            analyses=analyses,
            confidence=(
                fmean(item.confidence for item in analyses)
                if analyses
                else 0.0
            ),
            source_analysis=readiness.source_analysis,
        )
