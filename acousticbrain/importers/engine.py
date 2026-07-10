from pathlib import Path

from acousticbrain.project import (
    Project,
    Measurements,
)

from acousticbrain.models import Room

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

        for file in directory.iterdir():

            key = file.name.lower()

            if key not in mapping:
                continue

            measurement = importer.load(file)

            project.add_measurement(

                mapping[key],

                measurement,

            )

        return project