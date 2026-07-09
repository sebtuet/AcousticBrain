from acousticbrain.brain import AcousticBrain

from acousticbrain.project import Project

from acousticbrain.importers import REWTxtImporter

from acousticbrain.report import ConsoleReporter


project = Project("Salle Home Cinema")

measurement = REWTxtImporter().load("LR.txt")

project.add_measurement(
    "L+R",
    measurement,
)

brain = AcousticBrain()

report = brain.analyze(project)

ConsoleReporter().print(report)
