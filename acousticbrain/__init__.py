from .brain import AcousticBrain


def __getattr__(name):
    if name == "AcousticAssistant":
        from .assistant import AcousticBrain as AcousticAssistant

        return AcousticAssistant
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
