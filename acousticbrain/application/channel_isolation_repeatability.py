"""Descriptive repeatability facts for declared channel-isolation captures."""

from dataclasses import dataclass
from pathlib import Path
import re

from acousticbrain.importers import REWTxtImporter
from acousticbrain.models import (
    EvidenceAcquisitionTestType,
    ExperimentFileType,
    ImpulseChannel,
)


@dataclass(frozen=True)
class ChannelIsolationRepeatability:
    experiment_id: str
    reference_experiment_id: str | None
    labels: tuple[str, str]
    left_maximum_difference_db: float | None
    right_maximum_difference_db: float | None
    left_right_difference_maximum_change_db: float | None
    baseline_differences: tuple["ChannelIsolationBaselineDifference", ...] = ()


@dataclass(frozen=True)
class ChannelIsolationBaselineDifference:
    label: str
    left_maximum_difference_db: float | None
    right_maximum_difference_db: float | None
    left_right_difference_maximum_change_db: float | None


class ChannelIsolationRepeatabilityService:
    """Reads two explicitly labelled REW pairs without deriving a verdict."""

    REQUIRED_LABELS = ("A", "B")

    def __init__(self, txt_importer=None):
        self.txt_importer = txt_importer or REWTxtImporter()

    def analyze(self, descriptors):
        descriptors_by_id = {item.experiment_id: item for item in descriptors}
        results = []
        for descriptor in descriptors:
            pairs = self._pairs(descriptor)
            if pairs is None:
                continue
            left_a, right_a = pairs["A"]
            left_b, right_b = pairs["B"]
            results.append(ChannelIsolationRepeatability(
                experiment_id=descriptor.experiment_id,
                reference_experiment_id=getattr(
                    descriptor.evidence_acquisition_plan_contract,
                    "reference_experiment_code",
                    None,
                ),
                labels=self.REQUIRED_LABELS,
                left_maximum_difference_db=self._maximum_difference(
                    left_a.spl, left_b.spl, left_a.frequency, left_b.frequency,
                ),
                right_maximum_difference_db=self._maximum_difference(
                    right_a.spl, right_b.spl, right_a.frequency, right_b.frequency,
                ),
                left_right_difference_maximum_change_db=self._maximum_difference(
                    self._difference(left_a.spl, right_a.spl),
                    self._difference(left_b.spl, right_b.spl),
                    left_a.frequency,
                    left_b.frequency,
                ),
                baseline_differences=self._baseline_differences(
                    pairs,
                    descriptors_by_id.get(
                        getattr(
                            descriptor.evidence_acquisition_plan_contract,
                            "reference_experiment_code",
                            None,
                        )
                    ),
                ),
            ))
        return tuple(results)

    def _pairs(self, descriptor):
        contract = descriptor.evidence_acquisition_plan_contract
        if (
            descriptor.channel_isolation_declaration is None
            or contract is None
            or contract.source_plan.test_type
            is not EvidenceAcquisitionTestType.CHANNEL_ISOLATION
        ):
            return None
        pairs = {label: {} for label in self.REQUIRED_LABELS}
        for item in descriptor.available_files:
            if (
                item.file_type is not ExperimentFileType.TXT_MEASUREMENT
                or item.channel not in {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}
            ):
                continue
            measurement = self.txt_importer.load(
                str(Path(descriptor.directory) / item.relative_path)
            )
            label = self._label(measurement.name)
            if label is None or item.channel in pairs[label]:
                return None
            pairs[label][item.channel] = measurement
        if any(
            set(pair) != {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}
            for pair in pairs.values()
        ):
            return None
        if any(
            pair[ImpulseChannel.LEFT].frequency != pair[ImpulseChannel.RIGHT].frequency
            for pair in pairs.values()
        ):
            return None
        return {
            label: (pair[ImpulseChannel.LEFT], pair[ImpulseChannel.RIGHT])
            for label, pair in pairs.items()
        }

    def _baseline_differences(self, pairs, reference):
        baseline = self._single_pair(reference)
        if baseline is None:
            return ()
        baseline_left, baseline_right = baseline
        values = []
        for label in self.REQUIRED_LABELS:
            left, right = pairs[label]
            values.append(ChannelIsolationBaselineDifference(
                label=label,
                left_maximum_difference_db=self._maximum_difference(
                    left.spl, baseline_left.spl, left.frequency, baseline_left.frequency,
                ),
                right_maximum_difference_db=self._maximum_difference(
                    right.spl, baseline_right.spl, right.frequency, baseline_right.frequency,
                ),
                left_right_difference_maximum_change_db=self._maximum_difference(
                    self._difference(left.spl, right.spl),
                    self._difference(baseline_left.spl, baseline_right.spl),
                    left.frequency,
                    baseline_left.frequency,
                ),
            ))
        return tuple(values)

    def _single_pair(self, descriptor):
        if descriptor is None:
            return None
        values = {}
        for item in descriptor.available_files:
            if (
                item.file_type is not ExperimentFileType.TXT_MEASUREMENT
                or item.channel not in {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}
            ):
                continue
            if item.channel in values:
                return None
            values[item.channel] = self.txt_importer.load(
                str(Path(descriptor.directory) / item.relative_path)
            )
        if set(values) != {ImpulseChannel.LEFT, ImpulseChannel.RIGHT}:
            return None
        left, right = values[ImpulseChannel.LEFT], values[ImpulseChannel.RIGHT]
        return (left, right) if left.frequency == right.frequency else None

    @staticmethod
    def _label(value):
        labels = {
            token for token in re.findall(r"[A-Z0-9]+", value.upper())
            if token in {"A", "B"}
        }
        return next(iter(labels)) if len(labels) == 1 else None

    @staticmethod
    def _difference(left, right):
        if len(left) != len(right):
            return ()
        return tuple(a - b for a, b in zip(left, right))

    @staticmethod
    def _maximum_difference(first, second, first_frequency, second_frequency):
        if (
            not first
            or len(first) != len(second)
            or tuple(first_frequency) != tuple(second_frequency)
        ):
            return None
        return max(abs(a - b) for a, b in zip(first, second))
