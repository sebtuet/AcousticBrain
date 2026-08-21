from types import SimpleNamespace

from acousticbrain.application import ChannelIsolationRepeatabilityService
from acousticbrain.models import (
    EvidenceAcquisitionTestType,
    ExperimentFileType,
    ImpulseChannel,
    Measurement,
)


class _Importer:
    def load(self, path):
        name = str(path)
        values = {
            "left-a": ("L test A", (70.0, 71.0)),
            "right-a": ("R test A", (68.0, 70.0)),
            "left-b": ("L test B", (71.0, 69.0)),
            "right-b": ("R test B", (67.0, 71.0)),
        }
        label, spl = values[name.rsplit("/", 1)[-1]]
        return Measurement(label, [20.0, 100.0], list(spl), [0.0, 0.0])


def test_repeatability_reads_two_explicit_rew_pairs_without_a_verdict():
    files = tuple(
        SimpleNamespace(
            file_type=ExperimentFileType.TXT_MEASUREMENT,
            channel=channel,
            relative_path=path,
        )
        for path, channel in (
            ("left-a", ImpulseChannel.LEFT),
            ("right-a", ImpulseChannel.RIGHT),
            ("left-b", ImpulseChannel.LEFT),
            ("right-b", ImpulseChannel.RIGHT),
        )
    )
    descriptor = SimpleNamespace(
        experiment_id="test-canaux-001",
        directory="/capture",
        available_files=files,
        channel_isolation_declaration=object(),
        evidence_acquisition_plan_contract=SimpleNamespace(
            source_plan=SimpleNamespace(
                test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
            )
        ),
    )

    result = ChannelIsolationRepeatabilityService(_Importer()).analyze((descriptor,))

    assert len(result) == 1
    value = result[0]
    assert value.experiment_id == "test-canaux-001"
    assert value.left_maximum_difference_db == 2.0
    assert value.right_maximum_difference_db == 1.0
    assert value.left_right_difference_maximum_change_db == 3.0
