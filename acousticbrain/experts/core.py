from .base import Expert

class CoreExpert(Expert):

    def can_handle(self, question):

        return "version" in question.lower()

    def execute(self, question):

        return "AcousticBrain 0.1.0"

        