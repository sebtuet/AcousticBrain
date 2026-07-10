from .pipeline import BrainPipeline


class AcousticBrain:

    def __init__(self):

        self.pipeline = BrainPipeline()

    def analyze(self, project):

        return self.pipeline.run(project)