from acousticbrain.brain import AcousticBrain

from acousticbrain.importers import REWTxtImporter

from acousticbrain.models import (
    Room,
    Speaker,
)

from acousticbrain.project import Project

from acousticbrain.report import ConsoleReporter


room = Room(

    name="Salle Home Cinema",

    length=5.40,

    width=4.10,

    height=2.45,

)

project = Project(

    name="Salle Home Cinema",

    room=room,

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

#
# Mesure
#

measurement = REWTxtImporter().load("LR.txt")

project.add_measurement(

    "L+R",

    measurement,

)

brain = AcousticBrain()

report = brain.analyze(project)

ConsoleReporter().print(report)
