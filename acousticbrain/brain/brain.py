from .pipeline import BrainPipeline


class AcousticBrain:

    def __init__(self):

        self.pipeline = BrainPipeline()

    def analyze(self, project, *, session_context=None):

        return self.pipeline.run(project, session_context=session_context)
