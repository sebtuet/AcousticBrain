from ollama import chat


class LLM:

    def __init__(self, model="qwen3:8b"):
        self.model = model

    def ask(self, question: str):

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
        