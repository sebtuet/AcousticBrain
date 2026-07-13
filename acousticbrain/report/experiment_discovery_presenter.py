from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PresentedDiscoveredExperiment:
    experiment_id: str
    experiment_type: str
    state: str
    file_count: int
    timestamp: str
    available_channels: tuple[str, ...]


@dataclass(frozen=True)
class PresentedExperimentDiscovery:
    experiments: tuple[PresentedDiscoveredExperiment, ...]

    def to_dict(self):
        return asdict(self)


class ExperimentDiscoveryPresenter:
    """Projection directe des descripteurs découverts."""

    def present(self, context):
        descriptors = getattr(context, "experiment_descriptors", ())
        if not descriptors:
            return None
        return PresentedExperimentDiscovery(
            experiments=tuple(
                PresentedDiscoveredExperiment(
                    experiment_id=item.experiment_id,
                    experiment_type=item.experiment_type.value,
                    state=item.state.value,
                    file_count=len(item.available_files),
                    timestamp=item.timestamp,
                    available_channels=tuple(
                        channel.value for channel in item.available_channels
                    ),
                )
                for item in descriptors
            )
        )
