from .base import Expert

class GreetingExpert(Expert):

    def can_handle(self, question):

        q = question.lower()

        return any(word in q for word in [
            "bonjour",
            "salut",
            "hello"
        ])

    def execute(self, question):

        return "Bonjour 😊"
        