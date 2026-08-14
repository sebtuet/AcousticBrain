from acousticbrain.analysis import DeterministicEvidenceWeightingEngine


class DeterministicEvidenceWeightingStage:
    def __init__(self, engine=None):
        self.engine = engine or DeterministicEvidenceWeightingEngine()

    def run(self, context):
        context.deterministic_evidence_weighting_synthesis = self.engine.weigh(
            context.acoustic_observation_synthesis,
            context.deterministic_acoustic_reasoning_synthesis,
            context.deterministic_corrective_action_synthesis,
        )
