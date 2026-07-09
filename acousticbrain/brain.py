from .version import VERSION

class AcousticBrain:
    def __init__(self):
        self.version = VERSION

    def get_version(self):
        return self.version
        