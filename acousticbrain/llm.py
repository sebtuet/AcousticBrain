class OllamaIntegrationUnavailableError(RuntimeError):
    """Raised when the explicitly requested legacy Ollama integration is absent."""


class LLM:

    def __init__(self, model="qwen3:8b"):
        self.model = model

    def ask(self, question: str):
        try:
            from ollama import chat
        except ModuleNotFoundError as error:
            if error.name != "ollama":
                raise
            raise OllamaIntegrationUnavailableError(
                "The optional Ollama integration is not installed. "
                "AcousticBrain's deterministic runtime does not require it; "
                "install the 'ollama' package only to use this LLM integration."
            ) from error

        response = chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": question,
                }
            ],
        )

        return response.message.content
