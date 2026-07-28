from dataclasses import FrozenInstanceError
from math import exp, log2

import pytest

from acousticbrain.analysis import FrequencyResponseFeatureAnalyzer
from acousticbrain.models import (
    FrequencyFeatureChannelClassification,
    FrequencyFeatureStereoClassification,
    FrequencyResponseBand,
    FrequencyResponseFeatureType,
    ImpulseChannel,
    Measurement,
)


def measurement(*features, point_count=481, name="synthetic"):
    frequencies = [20.0 * 2.0 ** (index / 96.0) for index in range(point_count)]
    levels = []
    for frequency in frequencies:
        coordinate = log2(frequency)
        level = 75.0
        for center_hz, amplitude_db, width_octaves in features:
            distance = (coordinate - log2(center_hz)) / width_octaves
            level += amplitude_db * exp(-0.5 * distance * distance)
        levels.append(level)
    return Measurement(
        name=name,
        frequency=frequencies,
        spl=levels,
        phase=[0.0] * point_count,
    )


def analyze(left, right=None, stereo=None):
    right = right or left
    stereo = stereo or left
    return FrequencyResponseFeatureAnalyzer().analyze(left, right, stereo)


def channel(result, value=ImpulseChannel.LEFT):
    return result.channel(value)


def test_flat_curve_contains_no_feature():
    result = channel(analyze(measurement()))

    assert result.features == ()
    assert result.peak_count == 0
    assert result.notch_count == 0


def test_isolated_peak_exposes_center_prominence_width_q_and_support():
    feature = channel(analyze(measurement((100.0, 8.0, 0.04)))).features[0]

    assert feature.feature_type is FrequencyResponseFeatureType.PEAK
    assert feature.center_frequency_hz == pytest.approx(100.0, rel=0.01)
    assert feature.prominence_db == pytest.approx(8.0, abs=0.2)
    assert feature.depth_db is None
    assert feature.bandwidth_octaves == pytest.approx(0.08, abs=0.02)
    assert feature.estimated_q == pytest.approx(
        feature.center_frequency_hz / feature.bandwidth_hz
    )
    assert feature.supporting_sample_range[0] < feature.supporting_sample_range[1]


def test_isolated_notch_exposes_center_depth_width_and_negative_relative_level():
    feature = channel(analyze(measurement((100.0, -8.0, 0.04)))).features[0]

    assert feature.feature_type is FrequencyResponseFeatureType.NOTCH
    assert feature.center_frequency_hz == pytest.approx(100.0, rel=0.01)
    assert feature.depth_db == pytest.approx(8.0, abs=0.2)
    assert feature.prominence_db is None
    assert feature.relative_level_db < 0.0
    assert feature.bandwidth_hz > 0.0


def test_peak_inside_minimum_domain_edge_guard_is_not_retained():
    result = channel(analyze(measurement((20.3, 12.0, 0.015))))

    assert result.features == ()
    assert "Domain-edge guards" in " ".join(result.limitations)


def test_notch_inside_maximum_domain_edge_guard_is_not_retained():
    curve = measurement((19700.0, -12.0, 0.015), point_count=958)
    result = channel(analyze(curve))

    assert result.features == ()


def test_separated_peak_and_notch_are_both_retained_in_frequency_order():
    result = channel(
        analyze(measurement((100.0, 8.0, 0.04), (180.0, -7.0, 0.05)))
    )

    assert tuple(item.feature_type for item in result.features) == (
        FrequencyResponseFeatureType.PEAK,
        FrequencyResponseFeatureType.NOTCH,
    )
    assert (
        result.features[0].center_frequency_hz
        < result.features[1].center_frequency_hz
    )


def test_nearby_same_type_features_are_merged_deterministically():
    result = channel(
        analyze(measurement((100.0, 8.0, 0.04), (106.0, 7.0, 0.025)))
    )

    assert result.peak_count == 1
    assert result.features[0].center_frequency_hz == pytest.approx(100.0, rel=0.02)


def test_feature_below_minimum_magnitude_is_not_retained():
    result = channel(analyze(measurement((100.0, 2.9, 0.04))))

    assert result.features == ()


def test_feature_too_narrow_for_available_resolution_is_not_retained():
    result = channel(analyze(measurement((100.0, 12.0, 0.003))))

    assert result.features == ()


@pytest.mark.parametrize(
    ("center_hz", "expected_band"),
    (
        (100.0, FrequencyResponseBand.LOW),
        (1000.0, FrequencyResponseBand.MID),
        (5000.0, FrequencyResponseBand.HIGH),
    ),
)
def test_features_are_assigned_to_explicit_analysis_bands(
    center_hz,
    expected_band,
):
    feature = channel(
        analyze(measurement((center_hz, 8.0, 0.04), point_count=958))
    ).features[0]

    assert feature.band is expected_band


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("frequency", float("nan"), "finite"),
        ("spl", float("inf"), "finite"),
        ("phase", float("-inf"), "finite"),
    ),
)
def test_non_finite_data_are_rejected(field, value, message):
    curve = measurement()
    getattr(curve, field)[10] = value

    with pytest.raises(ValueError, match=message):
        analyze(curve)


def test_non_strictly_increasing_frequencies_are_rejected():
    curve = measurement()
    curve.frequency[20], curve.frequency[21] = (
        curve.frequency[21],
        curve.frequency[20],
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        analyze(curve)


def test_duplicate_frequencies_are_rejected():
    curve = measurement()
    curve.frequency[20] = curve.frequency[19]

    with pytest.raises(ValueError, match="strictly increasing"):
        analyze(curve)


def test_insufficient_sample_count_is_rejected():
    curve = measurement(point_count=47)

    with pytest.raises(ValueError, match="insufficient"):
        analyze(curve)


def test_mismatched_frequency_spl_and_phase_lengths_are_rejected():
    curve = measurement()
    curve.phase.pop()

    with pytest.raises(ValueError, match="lengths must match"):
        analyze(curve)


def test_same_notch_on_left_and_right_is_common():
    result = analyze(
        measurement((100.0, -8.0, 0.04)),
        measurement((100.0, -7.5, 0.04)),
        measurement((100.0, -7.0, 0.04)),
    )

    assert result.common_count == 1
    comparison = result.left_right_comparisons[0]
    assert comparison.classification is FrequencyFeatureChannelClassification.COMMON
    assert comparison.frequency_delta_hz == pytest.approx(0.0)
    assert comparison.overlap_score == pytest.approx(1.0)


def test_near_but_non_identical_notches_match_on_log_frequency():
    result = analyze(
        measurement((100.0, -8.0, 0.05)),
        measurement((103.0, -7.0, 0.05)),
        measurement(),
    )

    comparison = result.left_right_comparisons[0]
    assert comparison.classification is FrequencyFeatureChannelClassification.COMMON
    assert comparison.frequency_delta_hz > 0.0
    assert comparison.frequency_delta_percent < 5.0


def test_left_only_feature_is_classified_without_positional_matching():
    result = analyze(
        measurement((100.0, -8.0, 0.04)),
        measurement(),
        measurement(),
    )

    assert result.left_only_count == 1
    assert result.right_only_count == 0
    assert result.left_right_comparisons[0].right_feature_id is None


def test_right_only_feature_is_classified_without_positional_matching():
    result = analyze(
        measurement(),
        measurement((100.0, -8.0, 0.04)),
        measurement(),
    )

    assert result.left_only_count == 0
    assert result.right_only_count == 1
    assert result.left_right_comparisons[0].left_feature_id is None


def test_ambiguous_channel_candidates_are_not_forced_into_a_match():
    center = 100.06854605623964
    result = analyze(
        measurement((center, -8.0, 0.055)),
        measurement(
            (center / 2.0**0.05, -8.0, 0.025),
            (center * 2.0**0.05, -8.0, 0.025),
        ),
        measurement(),
    )

    assert result.common_count == 0
    assert any(
        "Ambiguous" in limitation
        for item in result.left_right_comparisons
        for limitation in item.limitations
    )


@pytest.mark.parametrize(
    ("stereo_amplitude", "classification"),
    (
        (-8.0, FrequencyFeatureStereoClassification.PRESENT_IN_STEREO),
        (-4.0, FrequencyFeatureStereoClassification.ATTENUATED_IN_STEREO),
        (-12.0, FrequencyFeatureStereoClassification.AMPLIFIED_IN_STEREO),
    ),
)
def test_stereo_relation_is_descriptive(stereo_amplitude, classification):
    result = analyze(
        measurement((100.0, -8.0, 0.04)),
        measurement((100.0, -8.0, 0.04)),
        measurement((100.0, stereo_amplitude, 0.04)),
    )

    relation = result.stereo_relations[0]
    assert relation.classification is classification
    assert relation.stereo_feature_id is not None
    assert any(
        "does not identify a cause" in limitation
        for limitation in relation.limitations
    )


def test_missing_stereo_feature_is_explicitly_not_resolved():
    result = analyze(
        measurement((100.0, -8.0, 0.04)),
        measurement((100.0, -8.0, 0.04)),
        measurement(),
    )

    assert result.stereo_relations[0].classification is (
        FrequencyFeatureStereoClassification.NOT_RESOLVED_IN_STEREO
    )
    assert result.stereo_relations[0].magnitude_delta_db is None


def test_identifiers_and_order_are_stable_and_results_are_immutable():
    curves = (
        measurement((180.0, -7.0, 0.05), (100.0, 8.0, 0.04)),
        measurement((181.0, -7.0, 0.05), (101.0, 8.0, 0.04)),
        measurement((180.0, -7.0, 0.05), (100.0, 8.0, 0.04)),
    )
    analyzer = FrequencyResponseFeatureAnalyzer()

    first = analyzer.analyze(*curves)
    second = analyzer.analyze(*curves)

    assert first == second
    assert tuple(
        item.center_frequency_hz for item in first.channels[0].features
    ) == tuple(
        sorted(item.center_frequency_hz for item in first.channels[0].features)
    )
    with pytest.raises(FrozenInstanceError):
        first.confidence = 0.0
