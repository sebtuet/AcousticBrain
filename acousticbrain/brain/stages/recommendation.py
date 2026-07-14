from dataclasses import replace

from acousticbrain.analysis import RecommendationEngine
from acousticbrain.models import CausalDiscriminationDecisionStatus, RecommendationStatus


class RecommendationStage:
    """Orchestre le moteur une fois toutes les analyses disponibles."""

    def __init__(self, engine=None):
        self.engine = engine or RecommendationEngine()

    def run(self, context):
        analysis = self.engine.analyze(
            stereo=context.stereo,
            sbir=context.sbir,
            modal_density=context.modal_density,
            peak_classification=getattr(context, "peak_classification", None),
            rt60=context.rt60_analysis,
            etc=context.etc_analysis,
            spatial=context.spatial_analysis,
            clarity_correlations=context.clarity_correlation_analysis,
            spatial_correlations=context.spatial_correlation_analysis,
            etc_reflection_correlations=(
                context.etc_reflection_correlation_analysis
            ),
            direct_reverberant=context.direct_reverberant_analysis,
            direct_reverberant_correlations=(
                context.direct_reverberant_correlation_analysis
            ),
            bass_decay=context.bass_decay_analysis,
            bass_decay_correlations=context.bass_decay_correlation_analysis,
            confidence=getattr(context, "confidence_analysis", None),
            measurement_quality=context.measurement_quality_analysis,
            measurement_readiness=context.measurement_readiness_analysis,
            acoustic_reasoning=context.acoustic_reasoning_analysis,
        )
        deferred_actions = self._deferred_action_reasons(
            context.experiment_descriptors
        )
        completed_actions = self._completed_action_reasons(
            context.experiment_descriptors
        )
        analysis.recommendations = [
            replace(
                item,
                status=RecommendationStatus.DEFERRED,
                status_reason=deferred_actions[item.code],
            )
            if item.code in deferred_actions
            else replace(
                item,
                status=RecommendationStatus.COMPLETED,
                status_reason=completed_actions[item.code],
            )
            if item.code in completed_actions
            else item
            for item in analysis.recommendations
        ]
        context.recommendation_analysis = analysis

    @staticmethod
    def _deferred_action_reasons(descriptors):
        action_by_discrimination = {
            "LOUDSPEAKER_VS_ROOM_SIDE": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
        }
        reasons = {}
        for descriptor in descriptors:
            for decision in descriptor.causal_discrimination_decisions:
                action = action_by_discrimination.get(decision.discrimination_code)
                if (
                    action is not None
                    and decision.status is CausalDiscriminationDecisionStatus.DEFERRED
                ):
                    reasons[action] = decision.reason.value
        return reasons

    @staticmethod
    def _completed_action_reasons(descriptors):
        actions_by_protocol = {
            "protocol.verify_modal_bass_persistence.v1": (
                "MEASURE_MULTIPLE_POSITIONS",
                "VERIFY_MODAL_BASS_PERSISTENCE",
            ),
        }
        completed_protocols = {
            getattr(descriptor, "source_protocol_id", None)
            for descriptor in descriptors
            if "MULTIPLE_LISTENING_POSITIONS"
            in getattr(descriptor, "declared_change_codes", ())
        }
        return {
            action: "EXPERIMENT_PROTOCOL_COMPLETED"
            for protocol in completed_protocols
            for action in actions_by_protocol.get(protocol, ())
        }
