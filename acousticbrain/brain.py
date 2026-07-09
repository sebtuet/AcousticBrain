from .version import VERSION
from .config import BrainConfig
from .llm import LLM
from .planner.planner import Planner


class AcousticBrain:

    def __init__(self, config=None):

        self.config = config or BrainConfig()

        self.llm = LLM(self.config.llm_model)

        self.planner = Planner()

    def version(self):

        return VERSION

    def info(self):

        return {
            "version": VERSION,
            "llm": self.config.llm_model,
            "language": self.config.language,
        }

    def ask(self, question: str):

        # On demande d'abord au Planner si un Expert
        # peut répondre à la question.
        answer = self.planner.execute(question)

        # Si un Expert a répondu, on renvoie directement
        # sa réponse.
        if answer is not None:
            return answer

        # Sinon on interroge le LLM.
        return self.llm.ask(question)