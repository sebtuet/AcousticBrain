from acousticbrain.experts.greeting import GreetingExpert
from acousticbrain.experts.core import CoreExpert


class Planner:

    def __init__(self):

        self.experts = [

            GreetingExpert(),

            CoreExpert(),

        ]

    def execute(self, question):

        for expert in self.experts:

            if expert.can_handle(question):

                return expert.execute(question)

        return None

        