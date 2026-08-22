from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    ChannelIsolationRepeatabilityEvaluationService,
    ChannelIsolationRepeatabilityQualificationService,
    ChannelIsolationRepeatabilityService,
    RepeatabilityEvaluationContract,
    RepeatabilityEvaluationStatus,
)
from acousticbrain.application.channel_isolation_repeatability_evaluation import (
    ChannelIsolationRepeatabilityEvaluation,
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


def _evaluations(*, contract=None):
    return ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_BandImporter())
    ).evaluate((_descriptor(),), contract=contract)


def test_repeatability_qualification_preserves_acceptable_source_verdict_and_metrics():
    source = _evaluations()

    result = ChannelIsolationRepeatabilityQualificationService().qualify(source)

    assert len(result) == 1
    value = result[0]
    assert value.repeatability_contract_id == "repeatability_contract.v1"
    assert value.repeatability_contract_version == "v1"
    assert value.left_channel_metric.maximum_difference_db == source[0].left_maximum_difference_db
    assert value.right_channel_metric.maximum_difference_db == source[0].right_maximum_difference_db
    assert value.source_numeric_verdict is RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
    assert value.qualification_status.value == "QUALIFIED"
    assert value.reason_codes == ("REPEATABILITY_ACCEPTABLE_IN_BAND",)
    assert value.provenance.experiment_id == "test-canaux-002"
    assert value.provenance.capture_labels == ("A", "B")
    assert value.provenance.threshold_db == 3.0
    assert value.causality_status == "NOT_ESTABLISHED"


def test_repeatability_qualification_maps_uncertain_source_verdict_without_recalculation():
    source = _evaluations(contract=RepeatabilityEvaluationContract(threshold_db=1.0))

    value = ChannelIsolationRepeatabilityQualificationService().qualify(source)[0]

    assert value.source_numeric_verdict is RepeatabilityEvaluationStatus.REPEATABILITY_UNCERTAIN
    assert value.qualification_status.value == "NOT_QUALIFIED"
    assert value.reason_codes == ("REPEATABILITY_UNCERTAIN",)


def test_repeatability_qualification_preserves_inclusive_limit_as_qualified():
    source = ChannelIsolationRepeatabilityEvaluationService(
        ChannelIsolationRepeatabilityService(_Importer())
    ).evaluate(
        (_descriptor(),),
        contract=RepeatabilityEvaluationContract(threshold_db=2.0),
    )

    value = ChannelIsolationRepeatabilityQualificationService().qualify(source)[0]

    assert value.source_numeric_verdict is RepeatabilityEvaluationStatus.REPEATABILITY_ACCEPTABLE_IN_BAND
    assert value.qualification_status.value == "QUALIFIED"


def test_repeatability_qualification_maps_not_evaluable_source_to_indeterminate():
    source = ChannelIsolationRepeatabilityEvaluation(
        experiment_id="test-incomplete",
        contract_id="repeatability_contract.v1",
        contract_version="v1",
        labels=("A", "B"),
        lower_hz=40.0,
        upper_hz=200.0,
        threshold_db=3.0,
        left_maximum_difference_db=None,
        left_maximum_difference_frequency_hz=None,
        right_maximum_difference_db=None,
        right_maximum_difference_frequency_hz=None,
        status=RepeatabilityEvaluationStatus.NOT_EVALUABLE,
    )

    value = ChannelIsolationRepeatabilityQualificationService().qualify((source,))[0]

    assert value.qualification_status.value == "INDETERMINATE"
    assert value.reason_codes == ("NOT_EVALUABLE",)


def test_repeatability_qualification_is_immutable_and_does_not_mutate_source():
    source = _evaluations()
    before = repr(source)
    value = ChannelIsolationRepeatabilityQualificationService().qualify(source)[0]

    with pytest.raises(FrozenInstanceError):
        value.reason_codes = ()

    assert repr(source) == before


def test_repeatability_qualification_is_independent_of_source_collection_order():
    source = _evaluations()[0]
    reversed_sources = (
        replace(source, experiment_id="test-b"),
        replace(source, experiment_id="test-a"),
    )

    values = ChannelIsolationRepeatabilityQualificationService().qualify(reversed_sources)

    assert tuple(value.provenance.experiment_id for value in values) == (
        "test-a", "test-b",
    )
