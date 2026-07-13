from types import SimpleNamespace

import pytest

from acousticbrain.application import CausalDiscriminationService
from acousticbrain.models import (
    CausalProtocolStatus,
    CausalProtocolStep,
    CausalTrajectoryCode,
    CausalTrajectoryStatus,
    UnresolvedDiscrimination,
)


PROTOCOL = "VERIFY_SPEAKER_ROOM_ASYMMETRY"


def step(
    index,
    code,
    experiment_id,
    *,
    controlled=(),
    changed=(),
    unknown=(),
    observations=(),
):
    return CausalProtocolStep(
        protocol_code=PROTOCOL,
        step_code=code,
        step_index=index,
        experiment_id=experiment_id,
        controlled_variable_codes=controlled,
        changed_variable_codes=changed,
        unknown_variable_codes=unknown,
        observation_codes=observations,
    )


def baseline():
    return step(
        0,
        "STEP_0_BASELINE",
        "baseline",
        controlled=("ROOM_CONFIGURATION", "MEASUREMENT_LEVEL"),
    )


def remeasurement(observations=("LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE",)):
    return step(
        1,
        "STEP_1_LEFT_RIGHT_REMEASUREMENT",
        "exp-001",
        controlled=(
            "LOUDSPEAKER_ASSIGNMENT",
            "SIGNAL_CHAIN_ASSIGNMENT",
            "ROOM_SIDE",
            "MICROPHONE_POSITION",
        ),
        changed=("MEASUREMENT_ACQUISITION",),
        observations=observations,
    )


def speaker_swap(*observations, controlled=None):
    return step(
        2,
        "STEP_2_SPEAKER_SWAP",
        "exp-002",
        controlled=controlled or (
            "ROOM_SIDE",
            "SIGNAL_CHAIN_ASSIGNMENT",
            "MICROPHONE_POSITION",
        ),
        changed=("LOUDSPEAKER_ASSIGNMENT",),
        observations=observations,
    )


def signal_swap(*observations):
    return step(
        3,
        "STEP_3_SIGNAL_CHAIN_SWAP",
        "exp-003",
        controlled=(
            "ROOM_SIDE",
            "LOUDSPEAKER_ASSIGNMENT",
            "MICROPHONE_POSITION",
        ),
        changed=("SIGNAL_CHAIN_ASSIGNMENT",),
        observations=observations,
    )


def descriptor(value):
    return SimpleNamespace(causal_protocol_step=value)


def comparison():
    unresolved = tuple(
        UnresolvedDiscrimination(code)
        for code in CausalDiscriminationService.INITIAL_DISCRIMINATIONS
    )
    result = SimpleNamespace(unresolved_discriminations=unresolved)
    return SimpleNamespace(sequence=SimpleNamespace(local_comparisons=(result,)))


def analyze(*steps):
    return CausalDiscriminationService().analyze(
        tuple(descriptor(item) for item in steps),
        comparison(),
        detailed_traceability=True,
    )


def trajectory(result, code):
    return next(
        item for item in result.trajectory_assessments
        if item.trajectory_code is code
    )


def test_no_explicit_step_means_no_causal_protocol_is_created():
    assert CausalDiscriminationService().analyze(
        (descriptor(None),), comparison()
    ) is None


def test_steps_without_source_comparison_do_not_invent_discriminations():
    result = CausalDiscriminationService().analyze(
        (descriptor(baseline()), descriptor(remeasurement())),
        None,
    )

    assert result.resolved_discrimination_codes == ()
    assert result.remaining_discrimination_codes == ()
    assert result.new_ambiguity_codes == ("SOURCE_COMPARISON_UNAVAILABLE",)


def test_incomplete_remeasurement_keeps_ambiguities_and_recommends_speaker_swap():
    result = analyze(baseline(), remeasurement())

    assert result.status is CausalProtocolStatus.INCOMPLETE
    assert result.resolved_discrimination_codes == ()
    assert result.remaining_discrimination_codes == (
        "LOUDSPEAKER_VS_ROOM_SIDE",
        "LOUDSPEAKER_VS_SIGNAL_CHAIN",
        "SIGNAL_CHAIN_VS_ROOM_SIDE",
    )
    assert result.recommended_next_protocol == "STEP_2_SPEAKER_SWAP"
    assert all(item.status is CausalTrajectoryStatus.COMPATIBLE
               for item in result.trajectory_assessments)


def test_speaker_swap_following_loudspeaker_reduces_only_observed_ambiguity():
    result = analyze(
        baseline(),
        remeasurement(),
        speaker_swap("ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"),
    )

    loudspeaker = trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER
    )
    room = trajectory(
        result, CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE
    )
    signal = trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN
    )
    assert loudspeaker.support_score == 100.0
    assert loudspeaker.status is CausalTrajectoryStatus.COMPATIBLE
    assert room.status is CausalTrajectoryStatus.CONTRADICTED
    assert signal.status is CausalTrajectoryStatus.COMPATIBLE
    assert result.resolved_discrimination_codes == (
        "LOUDSPEAKER_VS_ROOM_SIDE",
    )
    assert result.recommended_next_protocol == "STEP_3_SIGNAL_CHAIN_SWAP"


def test_speaker_swap_remaining_with_room_side_counters_loudspeaker_trajectory():
    result = analyze(
        baseline(),
        remeasurement(),
        speaker_swap("ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP"),
    )

    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE
    ).support_score == 100.0
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER
    ).status is CausalTrajectoryStatus.CONTRADICTED


def test_signal_chain_swap_supports_signal_trajectory_without_confirmation():
    result = analyze(
        baseline(),
        remeasurement(),
        signal_swap("ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN"),
    )

    signal = trajectory(result, CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN)
    assert signal.support_score == 100.0
    assert signal.status is CausalTrajectoryStatus.COMPATIBLE
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER
    ).status is CausalTrajectoryStatus.CONTRADICTED
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE
    ).status is CausalTrajectoryStatus.CONTRADICTED
    assert "CONFIRMED" not in {item.value for item in CausalTrajectoryStatus}


def test_signal_chain_swap_remaining_with_room_side_counters_signal_trajectory():
    result = analyze(
        baseline(),
        remeasurement(),
        signal_swap("ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SIGNAL_CHAIN_SWAP"),
    )

    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE
    ).support_score == 100.0
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_SIGNAL_CHAIN
    ).status is CausalTrajectoryStatus.CONTRADICTED


def test_two_controlled_swaps_can_resolve_all_declared_discriminations():
    result = analyze(
        baseline(),
        remeasurement(),
        speaker_swap("ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"),
        signal_swap("ANOMALY_REMAINED_WITH_LOUDSPEAKER_AFTER_SIGNAL_CHAIN_SWAP"),
    )

    assert result.resolved_discrimination_codes == (
        "LOUDSPEAKER_VS_ROOM_SIDE",
        "LOUDSPEAKER_VS_SIGNAL_CHAIN",
        "SIGNAL_CHAIN_VS_ROOM_SIDE",
    )
    assert result.remaining_discrimination_codes == ()
    assert result.recommended_next_protocol is None
    assert trajectory(
        result, CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE
    ).status is CausalTrajectoryStatus.CONTRADICTED
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER
    ).support_score == 100.0


def test_contradictory_observations_make_protocol_structurally_contradictory():
    result = analyze(
        baseline(),
        remeasurement(),
        speaker_swap(
            "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",
            "ANOMALY_REMAINED_WITH_ROOM_SIDE_AFTER_SPEAKER_SWAP",
        ),
    )

    assert result.status is CausalProtocolStatus.CONTRADICTORY
    assert "LOUDSPEAKER_VS_ROOM_SIDE" in result.remaining_discrimination_codes
    assert "CONTRADICTORY_OBSERVATIONS" in result.new_ambiguity_codes
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER
    ).counter_evidence_codes
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_REMAINS_WITH_ROOM_SIDE
    ).counter_evidence_codes


def test_incomplete_controls_never_apply_swap_observation():
    result = analyze(
        baseline(),
        remeasurement(),
        speaker_swap(
            "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",
            controlled=("ROOM_SIDE",),
        ),
    )

    assert result.resolved_discrimination_codes == ()
    assert "CONTROLLED_VARIABLES_INCOMPLETE" in result.new_ambiguity_codes
    assert trajectory(
        result, CausalTrajectoryCode.ANOMALY_FOLLOWS_LOUDSPEAKER
    ).support_score == 0.0


def test_non_reproducible_observation_creates_new_ambiguity():
    result = analyze(
        baseline(), remeasurement(("ANOMALY_NOT_REPRODUCIBLE",))
    )

    assert "MEASUREMENT_VARIABILITY_VS_CAUSAL_PATTERN" in result.new_ambiguity_codes
    assert trajectory(
        result, CausalTrajectoryCode.DISCRIMINATION_INCONCLUSIVE
    ).support_score == 100.0


def test_trace_preserves_steps_observations_rules_and_reductions():
    result = analyze(
        baseline(),
        remeasurement(),
        speaker_swap("ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"),
    )

    assert result.trace.experiment_ids == ("baseline", "exp-001", "exp-002")
    assert result.trace.observation_codes == (
        "LEFT_RIGHT_DIFFERENCE_REPRODUCIBLE",
        "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER",
    )
    assert "SPEAKER_SWAP_ANOMALY_FOLLOWS_LOUDSPEAKER" in (
        result.trace.applied_rule_codes
    )
    assert result.trace.resolved_discrimination_codes == (
        "LOUDSPEAKER_VS_ROOM_SIDE",
    )


def test_step_rejects_overlapping_controlled_and_changed_variables():
    with pytest.raises(ValueError, match="must be disjoint"):
        step(
            2,
            "STEP_2_SPEAKER_SWAP",
            "exp-002",
            controlled=("LOUDSPEAKER_ASSIGNMENT",),
            changed=("LOUDSPEAKER_ASSIGNMENT",),
        )
