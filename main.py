from acousticbrain.brain import AcousticBrain

from acousticbrain.importers import REWTxtImporter
from acousticbrain.models import Room
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

measurement = REWTxtImporter().load("LR.txt")

project.add_measurement(

    "L+R",

    measurement,

)

brain = AcousticBrain()

report = brain.analyze(project)

ConsoleReporter().print(report)