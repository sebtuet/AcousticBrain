from abc import ABC, abstractmethod


class DiagnosticBase(ABC):

    @abstractmethod
    def analyze(self, context):
        pass

        