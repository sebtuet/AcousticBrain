from acousticbrain.brain import AcousticBrain

from acousticbrain.importers import ImportEngine

from acousticbrain.models import Speaker

from acousticbrain.report import ConsoleReporter


project = ImportEngine().load_directory(

    "measurements"

)

#
# Enceintes
#

project.add_speaker(

    Speaker(

        name="Left",

        distance_front_wall=0.82,

        distance_side_wall=0.55,

        height=1.05,

    )

)

project.add_speaker(

    Speaker(

        name="Right",

        distance_front_wall=0.82,

        distance_side_wall=0.55,

        height=1.05,

    )

)

brain = AcousticBrain()

report = brain.analyze(project)

ConsoleReporter().print(report)

