from pathlib import Path

from acousticbrain.models import ExperimentFileType, ImpulseChannel, Room
from acousticbrain.project import Measurements, Project

from .rew_impulse import REWImpulseImporter
from .rew_txt import REWTxtImporter
from .wav_impulse import WavImpulseImporter


class ExperimentImporter:
    """Transforme un descripteur validé en Project AcousticBrain."""

    MEASUREMENT_NAMES = {
        ImpulseChannel.LEFT: Measurements.LEFT,
        ImpulseChannel.RIGHT: Measurements.RIGHT,
        ImpulseChannel.STEREO: Measurements.STEREO,
        ImpulseChannel.SUB: Measurements.SUB,
    }

    def __init__(self, txt_importer=None, impulse_importer=None, wav_importer=None):
        self.txt_importer = txt_importer or REWTxtImporter()
        self.impulse_importer = impulse_importer or REWImpulseImporter()
        self.wav_importer = wav_importer or WavImpulseImporter()

    def load(self, descriptor):
        measurement_files_by_channel = {}
        for item in descriptor.available_files:
            if (
                item.file_type is ExperimentFileType.TXT_MEASUREMENT
                and item.channel is not None
            ):
                measurement_files_by_channel.setdefault(item.channel, []).append(
                    item.relative_path
                )
        collisions = {
            channel: paths
            for channel, paths in measurement_files_by_channel.items()
            if len(paths) > 1
        }
        if collisions:
            details = "; ".join(
                f"{channel.value}: {', '.join(paths)}"
                for channel, paths in sorted(
                    collisions.items(), key=lambda entry: entry[0].value
                )
            )
            raise ValueError(
                "Ambiguous REW measurement channel assignment: multiple frequency "
                f"TXT files are assigned to the same channel ({details})."
            )

        project = Project(
            name=descriptor.experiment_id,
            room=Room(
                name="Unknown Room",
                length=5.84,
                width=5.51,
                height=2.60,
            ),
        )
        directory = Path(descriptor.directory)
        impulse_channels = set()
        for item in descriptor.available_files:
            if item.channel is None:
                continue
            path = directory / item.relative_path
            if item.file_type is ExperimentFileType.TXT_MEASUREMENT:
                project.add_measurement(
                    self.MEASUREMENT_NAMES[item.channel],
                    self.txt_importer.load(path),
                )
            elif item.file_type is ExperimentFileType.TXT_IMPULSE:
                project.add_impulse_response(
                    self.impulse_importer.load(path, channel=item.channel)
                )
                impulse_channels.add(item.channel)
        for item in descriptor.available_files:
            if (
                item.file_type is ExperimentFileType.WAV
                and item.channel is not None
                and item.channel not in impulse_channels
            ):
                project.add_impulse_response(
                    self.wav_importer.load(
                        directory / item.relative_path,
                        channel=item.channel,
                    )
                )
                impulse_channels.add(item.channel)
        return project
