from pathlib import Path

from acousticbrain.project import (
    Project,
    Measurements,
)

from acousticbrain.models import ImpulseChannel, Room

from .rew_impulse import REWImpulseImporter
from .rew_txt import REWTxtImporter


class ImportEngine:

    def load_directory(

        self,

        directory: str,

    ) -> Project:

        directory = Path(directory)

        room = Room(

            name="Unknown Room",

            length=5.40,

            width=4.10,

            height=2.45,

        )

        project = Project(

            name=directory.name,

            room=room,

        )

        importer = REWTxtImporter()

        mapping = {

            "left.txt": Measurements.LEFT,

            "right.txt": Measurements.RIGHT,

            "sub.txt": Measurements.SUB,

            "l+r.txt": Measurements.STEREO,

            "lr.txt": Measurements.STEREO,

        }

        impulse_mapping = {
            "impulse_left.txt": ImpulseChannel.LEFT,
            "impulse_right.txt": ImpulseChannel.RIGHT,
            "impulse_l+r.txt": ImpulseChannel.STEREO,
        }

        for file in directory.iterdir():

            key = file.name.lower()

            if key in mapping:
                measurement = importer.load(file)
                project.add_measurement(mapping[key], measurement)

            if key in impulse_mapping:
                impulse = REWImpulseImporter().load(
                    file,
                    channel=impulse_mapping[key],
                )
                project.add_impulse_response(impulse)

        return project
