import argparse
import json

from acousticbrain.application import RoomDescriptionProjectLoader
from acousticbrain.importers import ImportEngine
from acousticbrain.persistence import RoomDescriptionJsonCodec


def build_parser():
    parser = argparse.ArgumentParser(
        description="Charge une description de salle validée dans un projet."
    )
    parser.add_argument("--measurements", required=True)
    parser.add_argument("--room-description", required=True)
    return parser


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    project = ImportEngine().load_directory(arguments.measurements)
    result = RoomDescriptionProjectLoader().load(
        project,
        arguments.room_description,
    )
    if not result.is_success:
        print(
            json.dumps(
                {
                    "loaded": False,
                    "errors": [
                        {
                            "code": error.code.value,
                            "path": list(error.path),
                            "validation_code": (
                                error.validation_code.value
                                if error.validation_code is not None
                                else None
                            ),
                            "entity_ids": list(error.entity_ids),
                        }
                        for error in result.errors
                    ],
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "loaded": True,
                "project": project.name,
                "room_description": project.room_description.name,
                "source_schema_version": result.source_schema_version,
                "target_schema_version": RoomDescriptionJsonCodec.SCHEMA_VERSION,
                "requires_migration": result.requires_migration,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
