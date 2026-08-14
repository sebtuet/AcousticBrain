from dataclasses import replace

import pytest

from acousticbrain.brain import AcousticBrain
from acousticbrain.models import (
    ListeningPositionSamplingAcquisition,
    ListeningPositionSamplingPosition,
    ListeningPositionSamplingProtocol,
    REQUIRED_COMPLETION_CONDITION_CODES,
)
from test_golden_report import reference_project


MEASUREMENTS = ("LEFT", "RIGHT", "STEREO")
CONTROLLED_VARIABLES = (
    "LOUDSPEAKER_POSITION",
    "LOUDSPEAKER_ASSIGNMENT",
    "SIGNAL_CHAIN_ASSIGNMENT",
    "ROOM_CONFIGURATION",
    "MICROPHONE_ORIENTATION",
    "MEASUREMENT_LEVEL",
    "REW_PARAMETERS",
)


def position(
    code,
    role,
    longitudinal_offset_m,
    parent,
    reference,
    order,
    *,
    lateral_offset_m=None,
    vertical_offset_m=None,
    required_measurements=MEASUREMENTS,
):
    return ListeningPositionSamplingPosition(
        position_code=code,
        position_role=role,
        longitudinal_offset_m=longitudinal_offset_m,
        lateral_offset_m=lateral_offset_m,
        vertical_offset_m=vertical_offset_m,
        parent_position_code=parent,
        reference_position_code=reference,
        acquisition_order=order,
        required_measurements=required_measurements,
    )


def protocol(*, positions=None):
    return ListeningPositionSamplingProtocol(
        protocol_id="protocol.listening_position_sampling.v1",
        version=1,
        positions=positions or (
            position("REFERENCE", "REFERENCE", 0.0, None, "REFERENCE", 1),
            position(
                "FORWARD_100MM", "FORWARD", 0.10,
                "REFERENCE", "REFERENCE", 2,
            ),
            position(
                "BACKWARD_100MM", "BACKWARD", -0.10,
                "FORWARD_100MM", "REFERENCE", 3,
            ),
        ),
        modified_variables=("LISTENING_POSITION",),
        controlled_variables=CONTROLLED_VARIABLES,
        comparability_rule_code="LISTENING_POSITION_ORDERED_REFERENCE_BRANCH",
        completion_condition_codes=REQUIRED_COMPLETION_CONDITION_CODES,
    )


def acquisitions(value):
    return tuple(
        ListeningPositionSamplingAcquisition(
            position_code=item.position_code,
            available_measurements=item.required_measurements,
            parent_position_code=item.parent_position_code,
            reference_position_code=item.reference_position_code,
        )
        for item in value.positions
    )


def test_valid_protocol_preserves_declared_order_offsets_and_relations():
    value = protocol()

    assert value.definition_completeness.complete is True
    assert tuple(item.position_code for item in value.positions) == (
        "REFERENCE",
        "FORWARD_100MM",
        "BACKWARD_100MM",
    )
    assert tuple(item.longitudinal_offset_m for item in value.positions) == (
        0.0,
        0.10,
        -0.10,
    )
    assert tuple(item.parent_position_code for item in value.positions) == (
        None,
        "REFERENCE",
        "FORWARD_100MM",
    )
    assert value.modified_variables == ("LISTENING_POSITION",)
    assert value.controlled_variables == CONTROLLED_VARIABLES


def test_optional_offsets_remain_none_without_implicit_values():
    value = protocol()

    assert all(item.lateral_offset_m is None for item in value.positions)
    assert all(item.vertical_offset_m is None for item in value.positions)


def test_incomplete_definition_reports_missing_backward_position():
    value = protocol(
        positions=(
            position("REFERENCE", "REFERENCE", 0.0, None, "REFERENCE", 1),
            position(
                "FORWARD_100MM", "FORWARD", 0.10,
                "REFERENCE", "REFERENCE", 2,
            ),
        )
    )

    completeness = value.definition_completeness
    assert completeness.complete is False
    assert completeness.backward_present is False
    assert "BACKWARD_POSITION_PRESENT" in completeness.missing_condition_codes


def test_complete_acquisition_satisfies_every_condition():
    value = protocol()

    completeness = value.assess(acquisitions(value))

    assert completeness.complete is True
    assert completeness.missing_condition_codes == ()


def test_missing_measurement_and_position_are_reported_deterministically():
    value = protocol()
    partial = acquisitions(value)[:2]
    partial = (
        partial[0],
        replace(partial[1], available_measurements=("LEFT", "RIGHT")),
    )

    completeness = value.assess(partial)

    assert completeness.complete is False
    assert completeness.backward_present is False
    assert completeness.required_measurements_available is False
    assert completeness.comparability_respected is False
    assert completeness.missing_condition_codes == (
        "BACKWARD_POSITION_PRESENT",
        "REQUIRED_MEASUREMENTS_AVAILABLE",
        "COMPARABILITY_RULE_SATISFIED",
    )


def test_additional_offsets_are_data_and_require_no_protocol_engine_change():
    value = protocol(
        positions=(
            position("REFERENCE", "REFERENCE", 0.0, None, "REFERENCE", 1),
            position(
                "FORWARD_100MM", "FORWARD", 0.10,
                "REFERENCE", "REFERENCE", 2,
            ),
            position(
                "BACKWARD_100MM", "BACKWARD", -0.10,
                "FORWARD_100MM", "REFERENCE", 3,
            ),
            position(
                "FORWARD_200MM", "FORWARD", 0.20,
                "BACKWARD_100MM", "REFERENCE", 4,
            ),
            position(
                "BACKWARD_200MM", "BACKWARD", -0.20,
                "FORWARD_200MM", "REFERENCE", 5,
            ),
        )
    )

    assert value.definition_completeness.complete is True
    assert value.positions[-2].longitudinal_offset_m == pytest.approx(0.20)
    assert value.positions[-1].longitudinal_offset_m == pytest.approx(-0.20)


def test_protocol_rejects_positions_outside_declared_order():
    with pytest.raises(ValueError, match="declared order"):
        protocol(
            positions=(
                position("REFERENCE", "REFERENCE", 0.0, None, "REFERENCE", 1),
                position(
                    "FORWARD_100MM", "FORWARD", 0.10,
                    "REFERENCE", "REFERENCE", 3,
                ),
                position(
                    "BACKWARD_100MM", "BACKWARD", -0.10,
                    "FORWARD_100MM", "REFERENCE", 2,
                ),
            )
        )


def test_protocol_does_not_change_scientific_results_or_historical_recommendations():
    project = reference_project()

    baseline = AcousticBrain().analyze(project)
    enriched = AcousticBrain().analyze(
        project,
        listening_position_sampling_protocol=protocol(),
    )

    assert enriched.global_analysis == baseline.global_analysis
    assert enriched.recommendations == baseline.recommendations
    assert enriched.causal_discrimination == baseline.causal_discrimination
    assert (
        enriched.longitudinal_experimental_learning
        == baseline.longitudinal_experimental_learning
    )


def test_protocol_preserves_real_causal_and_longitudinal_analyses(
    historical_campaign_root,
):
    arguments = dict(
        measurement_root=historical_campaign_root,
        compare_experiments=True,
        analyze_causal_discrimination=True,
    )

    baseline = AcousticBrain().analyze(**arguments)
    enriched = AcousticBrain().analyze(
        **arguments,
        listening_position_sampling_protocol=protocol(),
    )

    assert enriched.global_analysis == baseline.global_analysis
    assert enriched.recommendations == baseline.recommendations
    assert enriched.causal_discrimination == baseline.causal_discrimination
    assert (
        enriched.longitudinal_experimental_learning
        == baseline.longitudinal_experimental_learning
    )
