from abc import ABC, abstractmethod

class Expert(ABC):

    @abstractmethod
    def can_handle(self, question: str) -> bool:
        pass

    @abstractmethod
    def execute(self, question: str) -> str:
        pass
        