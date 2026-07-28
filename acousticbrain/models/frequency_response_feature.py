from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .impulse_channel import ImpulseChannel


class FrequencyResponseFeatureType(Enum):
    PEAK = "PEAK"
    NOTCH = "NOTCH"


class FrequencyResponseBand(Enum):
    LOW = "LOW"
    MID = "MID"
    HIGH = "HIGH"


class FrequencyFeatureChannelClassification(Enum):
    COMMON = "COMMON"
    LEFT_ONLY = "LEFT_ONLY"
    RIGHT_ONLY = "RIGHT_ONLY"


class FrequencyFeatureStereoClassification(Enum):
    PRESENT_IN_STEREO = "PRESENT_IN_STEREO"
    ATTENUATED_IN_STEREO = "ATTENUATED_IN_STEREO"
    AMPLIFIED_IN_STEREO = "AMPLIFIED_IN_STEREO"
    NOT_RESOLVED_IN_STEREO = "NOT_RESOLVED_IN_STEREO"
    AMBIGUOUS = "AMBIGUOUS"


def _finite_number(value, label, *, minimum=None, maximum=None):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or (minimum is not None and value < minimum)
        or (maximum is not None and value > maximum)
    ):
        raise ValueError(f"{label} is invalid.")


def _optional_finite_number(value, label, *, minimum=None, maximum=None):
    if value is not None:
        _finite_number(value, label, minimum=minimum, maximum=maximum)


def _immutable_strings(values, label):
    if not isinstance(values, tuple) or any(
        not isinstance(value, str) or not value for value in values
    ):
        raise ValueError(f"{label} must contain immutable non-empty strings.")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique.")


@dataclass(frozen=True)
class FrequencyResponseFeature:
    feature_id: str
    feature_type: FrequencyResponseFeatureType
    band: FrequencyResponseBand
    channel: ImpulseChannel
    center_frequency_hz: float
    level_db: float
    relative_level_db: float
    prominence_db: float | None
    depth_db: float | None
    lower_frequency_hz: float
    upper_frequency_hz: float
    bandwidth_hz: float
    bandwidth_octaves: float | None
    estimated_q: float | None
    detection_confidence: float
    supporting_sample_range: tuple[int, int]
    limitations: tuple[str, ...] = ()
    source_analysis_id: str = "FrequencyResponseFeatureAnalysis"

    def __post_init__(self):
        if not isinstance(self.feature_id, str) or not self.feature_id:
            raise ValueError("A frequency-response feature requires a stable id.")
        if not isinstance(self.feature_type, FrequencyResponseFeatureType):
            raise ValueError("A frequency-response feature requires a type.")
        if not isinstance(self.band, FrequencyResponseBand):
            raise ValueError("A frequency-response feature requires a band.")
        if not isinstance(self.channel, ImpulseChannel):
            raise ValueError("A frequency-response feature requires a channel.")
        for value, label, minimum in (
            (self.center_frequency_hz, "Center frequency", 0.0),
            (self.lower_frequency_hz, "Lower frequency", 0.0),
            (self.upper_frequency_hz, "Upper frequency", 0.0),
            (self.bandwidth_hz, "Bandwidth", 0.0),
        ):
            _finite_number(value, label, minimum=minimum)
        for value, label in (
            (self.level_db, "Level"),
            (self.relative_level_db, "Relative level"),
        ):
            _finite_number(value, label)
        _optional_finite_number(self.prominence_db, "Prominence", minimum=0.0)
        _optional_finite_number(self.depth_db, "Depth", minimum=0.0)
        _optional_finite_number(
            self.bandwidth_octaves,
            "Octave bandwidth",
            minimum=0.0,
        )
        _optional_finite_number(self.estimated_q, "Estimated Q", minimum=0.0)
        _finite_number(
            self.detection_confidence,
            "Detection confidence",
            minimum=0.0,
            maximum=100.0,
        )
        if not (
            self.lower_frequency_hz
            <= self.center_frequency_hz
            <= self.upper_frequency_hz
        ):
            raise ValueError("Feature bounds must contain the center frequency.")
        if self.bandwidth_hz != (
            self.upper_frequency_hz - self.lower_frequency_hz
        ):
            raise ValueError("Feature bandwidth must match its frequency bounds.")
        if self.feature_type is FrequencyResponseFeatureType.PEAK:
            if self.prominence_db is None or self.depth_db is not None:
                raise ValueError("A peak requires prominence and cannot expose depth.")
            if self.relative_level_db <= 0.0:
                raise ValueError("A peak requires a positive relative level.")
        elif self.depth_db is None or self.prominence_db is not None:
            raise ValueError("A notch requires depth and cannot expose prominence.")
        elif self.relative_level_db >= 0.0:
            raise ValueError("A notch requires a negative relative level.")
        if (
            not isinstance(self.supporting_sample_range, tuple)
            or len(self.supporting_sample_range) != 2
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in self.supporting_sample_range
            )
            or self.supporting_sample_range[0] > self.supporting_sample_range[1]
        ):
            raise ValueError("Supporting sample range is invalid.")
        _immutable_strings(self.limitations, "Feature limitations")
        if not isinstance(self.source_analysis_id, str) or not self.source_analysis_id:
            raise ValueError("A frequency-response feature requires provenance.")


@dataclass(frozen=True)
class FrequencyResponseChannelAnalysis:
    channel: ImpulseChannel
    features: tuple[FrequencyResponseFeature, ...]
    sample_count: int
    minimum_frequency_hz: float
    maximum_frequency_hz: float
    peak_count: int
    notch_count: int
    most_prominent_feature_id: str | None
    deepest_notch_feature_id: str | None
    detection_confidence: float
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.channel, ImpulseChannel):
            raise ValueError("Channel analysis requires an impulse channel.")
        if not isinstance(self.features, tuple) or any(
            not isinstance(item, FrequencyResponseFeature)
            or item.channel is not self.channel
            for item in self.features
        ):
            raise ValueError("Channel features must be immutable and channel-specific.")
        if tuple(
            (item.center_frequency_hz, item.feature_type.value, item.feature_id)
            for item in self.features
        ) != tuple(
            sorted(
                (
                    item.center_frequency_hz,
                    item.feature_type.value,
                    item.feature_id,
                )
                for item in self.features
            )
        ):
            raise ValueError("Channel features must be deterministically ordered.")
        if (
            isinstance(self.sample_count, bool)
            or not isinstance(self.sample_count, int)
            or self.sample_count <= 0
        ):
            raise ValueError("Channel analysis requires a positive sample count.")
        _finite_number(
            self.minimum_frequency_hz,
            "Minimum frequency",
            minimum=0.0,
        )
        _finite_number(
            self.maximum_frequency_hz,
            "Maximum frequency",
            minimum=self.minimum_frequency_hz,
        )
        if self.peak_count != sum(
            item.feature_type is FrequencyResponseFeatureType.PEAK
            for item in self.features
        ) or self.notch_count != sum(
            item.feature_type is FrequencyResponseFeatureType.NOTCH
            for item in self.features
        ):
            raise ValueError(
                "Channel feature counts must match the feature collection."
            )
        identifiers = {item.feature_id for item in self.features}
        for value in (
            self.most_prominent_feature_id,
            self.deepest_notch_feature_id,
        ):
            if value is not None and value not in identifiers:
                raise ValueError("Channel summary feature ids must resolve.")
        _finite_number(
            self.detection_confidence,
            "Channel detection confidence",
            minimum=0.0,
            maximum=100.0,
        )
        _immutable_strings(self.limitations, "Channel limitations")


@dataclass(frozen=True)
class FrequencyResponseFeatureComparison:
    comparison_id: str
    classification: FrequencyFeatureChannelClassification
    feature_type: FrequencyResponseFeatureType
    left_feature_id: str | None
    right_feature_id: str | None
    frequency_delta_hz: float | None
    frequency_delta_percent: float | None
    level_or_depth_delta_db: float | None
    overlap_score: float | None
    match_confidence: float
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.comparison_id, str) or not self.comparison_id:
            raise ValueError("A feature comparison requires a stable id.")
        if not isinstance(self.classification, FrequencyFeatureChannelClassification):
            raise ValueError("A feature comparison requires a classification.")
        if not isinstance(self.feature_type, FrequencyResponseFeatureType):
            raise ValueError("A feature comparison requires a feature type.")
        if self.classification is FrequencyFeatureChannelClassification.COMMON:
            if self.left_feature_id is None or self.right_feature_id is None:
                raise ValueError("A common comparison requires both feature ids.")
            for value, label in (
                (self.frequency_delta_hz, "Frequency delta"),
                (self.frequency_delta_percent, "Frequency delta percent"),
                (self.level_or_depth_delta_db, "Magnitude delta"),
                (self.overlap_score, "Overlap score"),
            ):
                _optional_finite_number(value, label, minimum=0.0)
                if value is None:
                    raise ValueError("A common comparison requires complete metrics.")
        elif self.classification is FrequencyFeatureChannelClassification.LEFT_ONLY:
            if self.left_feature_id is None or self.right_feature_id is not None:
                raise ValueError("A left-only comparison requires only a left id.")
        elif self.right_feature_id is None or self.left_feature_id is not None:
            raise ValueError("A right-only comparison requires only a right id.")
        _finite_number(
            self.match_confidence,
            "Match confidence",
            minimum=0.0,
            maximum=100.0,
        )
        _optional_finite_number(
            self.overlap_score,
            "Overlap score",
            minimum=0.0,
            maximum=1.0,
        )
        _immutable_strings(self.limitations, "Comparison limitations")


@dataclass(frozen=True)
class FrequencyResponseStereoRelation:
    relation_id: str
    comparison_id: str
    stereo_feature_id: str | None
    classification: FrequencyFeatureStereoClassification
    frequency_delta_hz: float | None
    magnitude_delta_db: float | None
    bandwidth_delta_octaves: float | None
    match_confidence: float
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.relation_id, str) or not self.relation_id:
            raise ValueError("A stereo relation requires a stable id.")
        if not isinstance(self.comparison_id, str) or not self.comparison_id:
            raise ValueError("A stereo relation requires a comparison id.")
        if not isinstance(self.classification, FrequencyFeatureStereoClassification):
            raise ValueError("A stereo relation requires a classification.")
        if (
            self.classification
            in (
                FrequencyFeatureStereoClassification.PRESENT_IN_STEREO,
                FrequencyFeatureStereoClassification.ATTENUATED_IN_STEREO,
                FrequencyFeatureStereoClassification.AMPLIFIED_IN_STEREO,
            )
            and self.stereo_feature_id is None
        ):
            raise ValueError("A resolved stereo relation requires a stereo feature.")
        for value, label in (
            (self.frequency_delta_hz, "Stereo frequency delta"),
            (self.magnitude_delta_db, "Stereo magnitude delta"),
            (self.bandwidth_delta_octaves, "Stereo bandwidth delta"),
        ):
            _optional_finite_number(value, label)
        _finite_number(
            self.match_confidence,
            "Stereo match confidence",
            minimum=0.0,
            maximum=100.0,
        )
        _immutable_strings(self.limitations, "Stereo relation limitations")


@dataclass(frozen=True)
class FrequencyResponseFeatureAnalysis:
    channels: tuple[FrequencyResponseChannelAnalysis, ...]
    left_right_comparisons: tuple[FrequencyResponseFeatureComparison, ...]
    stereo_relations: tuple[FrequencyResponseStereoRelation, ...]
    confidence: float
    limitations: tuple[str, ...]
    source_analysis_id: str = "FrequencyResponseFeatureAnalysis"

    def __post_init__(self):
        if not isinstance(self.channels, tuple) or any(
            not isinstance(item, FrequencyResponseChannelAnalysis)
            for item in self.channels
        ):
            raise ValueError("Frequency-response channels must be immutable.")
        expected_channels = (
            ImpulseChannel.LEFT,
            ImpulseChannel.RIGHT,
            ImpulseChannel.STEREO,
        )
        if tuple(item.channel for item in self.channels) != expected_channels:
            raise ValueError("Frequency-response channels must be LEFT, RIGHT, STEREO.")
        if not isinstance(self.left_right_comparisons, tuple) or any(
            not isinstance(item, FrequencyResponseFeatureComparison)
            for item in self.left_right_comparisons
        ):
            raise ValueError("Frequency-response comparisons must be immutable.")
        if not isinstance(self.stereo_relations, tuple) or any(
            not isinstance(item, FrequencyResponseStereoRelation)
            for item in self.stereo_relations
        ):
            raise ValueError("Frequency-response stereo relations must be immutable.")
        comparison_ids = tuple(
            item.comparison_id for item in self.left_right_comparisons
        )
        if len(comparison_ids) != len(set(comparison_ids)):
            raise ValueError("Frequency-response comparison ids must be unique.")
        relation_ids = tuple(item.relation_id for item in self.stereo_relations)
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("Frequency-response relation ids must be unique.")
        if any(
            item.comparison_id not in set(comparison_ids)
            for item in self.stereo_relations
        ):
            raise ValueError("Stereo relations must resolve to comparisons.")
        _finite_number(
            self.confidence,
            "Frequency-response analysis confidence",
            minimum=0.0,
            maximum=100.0,
        )
        _immutable_strings(self.limitations, "Analysis limitations")
        if not isinstance(self.source_analysis_id, str) or not self.source_analysis_id:
            raise ValueError("Frequency-response analysis requires provenance.")

    def channel(self, channel):
        return next(item for item in self.channels if item.channel is channel)

    @property
    def common_count(self):
        return sum(
            item.classification is FrequencyFeatureChannelClassification.COMMON
            for item in self.left_right_comparisons
        )

    @property
    def left_only_count(self):
        return sum(
            item.classification is FrequencyFeatureChannelClassification.LEFT_ONLY
            for item in self.left_right_comparisons
        )

    @property
    def right_only_count(self):
        return sum(
            item.classification is FrequencyFeatureChannelClassification.RIGHT_ONLY
            for item in self.left_right_comparisons
        )
