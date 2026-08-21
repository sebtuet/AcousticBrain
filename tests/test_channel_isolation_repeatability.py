from types import SimpleNamespace

from acousticbrain.application import (
    ChannelIsolationRepeatabilityEvaluationService,
    ChannelIsolationRepeatabilityService,
    RepeatabilityEvaluationContract,
    RepeatabilityEvaluationStatus,
)
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


class _BandImporter:
    def load(self, path):
        name = str(path).rsplit("/", 1)[-1]
        values = {
            "left-a": ("L test A", (70.0, 70.00)),
            "right-a": ("R test A", (70.0, 70.00)),
            "left-b": ("L test B", (79.7, 70.26)),
            "right-b": ("R test B", (79.5, 71.82)),
        }
        label, spl = values[name]
        return Measurement(label, [21.0, 100.0], list(spl), [0.0, 0.0])


def _descriptor():
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
    return SimpleNamespace(
        experiment_id="test-canaux-002",
        directory="/capture",
        available_files=files,
        channel_isolation_declaration=object(),
        evidence_acquisition_plan_contract=SimpleNamespace(
            reference_experiment_code="baseline",
            source_plan=SimpleNamespace(
                test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
            )
        ),
    )


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
            reference_experiment_code="baseline",
            source_plan=SimpleNamespace(
                test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION,
            )
        ),
    )

    result = ChannelIsolationRepeatabilityService(_Importer()).analyze((descriptor,))

    assert len(result) == 1
    value = result[0]
    assert value.experiment_id == "test-canaux-001"
    assert value.reference_experiment_id == "baseline"
    assert value.left_maximum_difference_db == 2.0
    assert value.right_maximum_difference_db == 1.0
    assert value.left_right_difference_maximum_change_db == 3.0


def test_repeatability_evaluation_uses_declared_default_band_and_threshold():
    service = ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_BandImporter())
    )

    result = service.evaluate((_descriptor(),))

    assert len(result) == 1
    value = result[0]
    assert value.contract_id == "repeatability_contract.v1"
    assert (value.lower_hz, value.upper_hz, value.threshold_db) == (40.0, 200.0, 3.0)
    assert value.left_maximum_difference_db == 0.2600000000000051
    assert value.right_maximum_difference_db == 1.8199999999999932
    assert value.status is RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
    assert value.causality_status == "NOT_ESTABLISHED"


def test_repeatability_evaluation_ignores_out_of_band_peak_and_is_deterministic():
    service = ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_BandImporter())
    )

    first = service.evaluate((_descriptor(),))
    second = service.evaluate((_descriptor(),))

    assert first == second
    assert first[0].left_maximum_difference_db < 3.0
    assert first[0].right_maximum_difference_db < 3.0


def test_repeatability_evaluation_is_uncertain_above_custom_threshold():
    service = ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_BandImporter())
    )
    contract = RepeatabilityEvaluationContract(threshold_db=1.0)

    result = service.evaluate((_descriptor(),), contract=contract)

    assert result[0].status is RepeatabilityEvaluationStatus.REPEATABILITY_UNCERTAIN


def test_repeatability_evaluation_accepts_a_value_exactly_at_threshold():
    service = ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_Importer())
    )
    contract = RepeatabilityEvaluationContract(lower_hz=40.0, upper_hz=200.0, threshold_db=2.0)

    result = service.evaluate((_descriptor(),), contract=contract)

    assert result[0].left_maximum_difference_db == 2.0
    assert result[0].status is RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND


def test_repeatability_evaluation_uses_custom_band_without_code_changes():
    service = ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_BandImporter())
    )
    contract = RepeatabilityEvaluationContract(lower_hz=20.0, upper_hz=30.0, threshold_db=10.0)

    result = service.evaluate((_descriptor(),), contract=contract)

    assert result[0].left_maximum_difference_db == 9.700000000000003
    assert result[0].right_maximum_difference_db == 9.5
    assert result[0].status is RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
