from acousticbrain.brain import AcousticBrain
from acousticbrain.report import ConsoleReporter

brain = AcousticBrain()
report = brain.analyze(
    measurement_root="measurements",
    compare_experiments=True,
    analyze_causal_discrimination=True,
)

ConsoleReporter().print(report)
