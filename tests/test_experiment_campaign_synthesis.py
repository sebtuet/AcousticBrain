from types import SimpleNamespace

import pytest

from acousticbrain.application import ExperimentCampaignSynthesisService
from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentAcousticOutcome,
    ExperimentFactChange,
    ExperimentFactDelta,
    ExperimentState,
    ObservedExperimentFact,
    UnresolvedDiscrimination,
)


PROTOCOL = "protocol.verify_modal_bass_persistence.v1"
DECAY_FACT = "bass_decay.maximum_decay_time_s"


def descriptor(experiment_id, role, offset):
    return SimpleNamespace(
        experiment_id=experiment_id,
        source_protocol_id=PROTOCOL,
        comparison_parameters=(
            ("listening_position_offset_m", offset),
            ("position_role", role),
        ),
        state=ExperimentState.READY,
    )


def branch(experiment_id, observed_value, *, supports_local_effect):
    observations = []
    if supports_local_effect:
        observations.extend((
            ObservedExperimentFact(
                code="BASS_DECAY_VARIES_BY_LISTENING_POSITION",
                source_fact_codes=(DECAY_FACT,),
                provenance_codes=("comparison",),
            ),
            ObservedExperimentFact(
                code="LOCAL_POSITION_EFFECT_SUPPORTED",
                source_fact_codes=(DECAY_FACT,),
                provenance_codes=("comparison",),
            ),
        ))
    return SimpleNamespace(
        result_id=f"comparison:exp-003:{experiment_id}",
        source_protocol_id=PROTOCOL,
        before_experiment_id="exp-003",
        after_experiment_id=experiment_id,
        eligibility=ComparisonEligibilityStatus.COMPARABLE,
        fact_deltas=(ExperimentFactDelta(
            fact_code=DECAY_FACT,
            before=0.790,
            after=observed_value,
            delta=observed_value - 0.790,
            unit="SECONDS",
            change=(
                ExperimentFactChange.IMPROVED
                if observed_value < 0.790
                else ExperimentFactChange.UNCHANGED
            ),
            threshold=0.05,
            source_analysis_codes=("BassDecayAnalysis",),
        ),),
        observed_facts=tuple(observations),
        unresolved_discriminations=(
            UnresolvedDiscrimination("LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE"),
            UnresolvedDiscrimination(
                "SOURCE_EXCITATION_VS_LISTENER_POSITION"
            ),
        ),
        acoustic_outcome=(
            ExperimentAcousticOutcome.IMPROVED
            if observed_value < 0.790
            else ExperimentAcousticOutcome.UNCHANGED
        ),
    )


def test_synthesizes_modal_campaign_from_existing_comparisons_only():
    descriptors = (
        descriptor("exp-003", "REFERENCE", 0.0),
        descriptor("exp-004", "BACKWARD", -0.3),
        descriptor("exp-005", "FORWARD", 0.3),
    )
    comparisons = SimpleNamespace(
        sequence=SimpleNamespace(local_comparisons=(
            branch("exp-004", 0.817, supports_local_effect=False),
            branch("exp-005", 0.636, supports_local_effect=True),
        ))
    )

    campaign = ExperimentCampaignSynthesisService().analyze(
        descriptors, comparisons, detailed_traceability=True
    )[0]

    assert campaign.status.value == "PARTIALLY_RESOLVED"
    assert campaign.reference_experiment_id == "exp-003"
    assert tuple(item.experiment_id for item in campaign.measurements) == (
        "exp-003", "exp-004", "exp-005"
    )
    assert campaign.result_codes == (
        "BASS_DECAY_VARIES_BY_LISTENING_POSITION",
        "LOCAL_POSITION_EFFECT_SUPPORTED",
        "GLOBAL_MODAL_COMPONENT_NOT_DISCRIMINATED",
    )
    metric = campaign.metrics[0]
    assert metric.reference_value == pytest.approx(0.790)
    assert metric.best_value == pytest.approx(0.636)
    assert metric.best_experiment_id == "exp-005"
    assert campaign.next_discrimination_code == (
        "CONTROLLED_SOURCE_VARIATION_WITH_FIXED_LISTENER"
    )
