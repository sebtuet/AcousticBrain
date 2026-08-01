from types import SimpleNamespace

import pytest

from acousticbrain.application import ExploratoryResultService
from acousticbrain.models import (
    ComparisonEligibilityStatus,
    ExperimentAcousticOutcome,
    ReferenceStabilityStatus,
)


def comparison(outcome, *, required=("fact.a", "fact.b"), observed=None,
               protocol="proposal.one", eligibility=ComparisonEligibilityStatus.COMPARABLE):
    observed = required if observed is None else observed
    return SimpleNamespace(
        source_protocol_id=protocol,
        acoustic_outcome=ExperimentAcousticOutcome(outcome),
        eligibility=eligibility,
        required_fact_codes=required,
        fact_deltas=tuple(SimpleNamespace(fact_code=code) for code in observed),
    )


def analysis(*items):
    return SimpleNamespace(sequence=SimpleNamespace(local_comparisons=items))


@pytest.mark.parametrize(
    ("outcome", "next_step"),
    (
        ("DEGRADED", "RETURN_TO_REFERENCE"),
        ("UNCHANGED", "RETURN_THEN_CONSIDER_NEXT_ADMISSIBLE_CANDIDATE"),
        ("MIXED", "NO_PREFERENCE_RETURN_THEN_CONSIDER_EXISTING_CANDIDATE"),
        ("INCONCLUSIVE", "NO_PREFERENCE_RETURN_THEN_CONSIDER_EXISTING_CANDIDATE"),
    ),
)
def test_empirical_outcomes_are_preserved_without_causal_claim(outcome, next_step):
    result = ExploratoryResultService().project(
        "proposal.one", analysis(comparison(outcome))
    )
    assert result.acoustic_outcome == outcome
    assert result.next_step == next_step
    assert result.causality_status == "NOT_ESTABLISHED"
    assert result.robust_winner is False


def test_improvement_has_no_robust_winner_without_stable_return():
    result = ExploratoryResultService().project(
        "proposal.one", analysis(comparison("IMPROVED"))
    )
    assert result.acoustic_outcome == "IMPROVED"
    assert result.reference_stability is ReferenceStabilityStatus.NOT_EVALUATED
    assert result.robust_winner is False
    assert "NO_ROBUST_WINNER" in result.next_step


def test_improvement_can_select_winner_only_with_unchanged_return_control():
    result = ExploratoryResultService().project(
        "proposal.one",
        analysis(comparison("IMPROVED")),
        return_comparison=comparison("UNCHANGED", protocol="return.control"),
    )
    assert result.reference_stability is ReferenceStabilityStatus.ESTABLISHED
    assert result.robust_winner is True


def test_unstable_return_control_prevents_winner():
    result = ExploratoryResultService().project(
        "proposal.one",
        analysis(comparison("IMPROVED")),
        return_comparison=comparison("DEGRADED", protocol="return.control"),
    )
    assert result.reference_stability is ReferenceStabilityStatus.NOT_ESTABLISHED
    assert result.robust_winner is False


def test_missing_declared_observable_fact_forces_inconclusive():
    result = ExploratoryResultService().project(
        "proposal.one",
        analysis(comparison("MIXED", observed=("fact.a",))),
    )
    assert result.acoustic_outcome == "INCONCLUSIVE"
    assert result.observed_fact_codes == ("fact.a",)


def test_exactly_one_matching_comparison_is_required():
    with pytest.raises(ValueError, match="Exactly one"):
        ExploratoryResultService().project(
            "proposal.one", analysis(comparison("MIXED", protocol="other"))
        )


def test_historical_baseline_exp007_replay_preserves_mixed_and_prevents_repeat():
    historical = comparison("MIXED", protocol=None)
    historical.before_experiment_id = "baseline"
    historical.after_experiment_id = "exp-007"
    historical.modified_variables = (
        "TEMPORARY_LEFT_FIRST_REFLECTION_ABSORPTION",
    )
    result = ExploratoryResultService().project_historical_first_slice(
        analysis(historical)
    )
    assert result.acoustic_outcome == "MIXED"
    assert result.robust_winner is False
    assert result.next_step == "HISTORICAL_MIXED_INTERVENTION_NOT_PROPOSED_AGAIN"
    assert result.causality_status == "NOT_ESTABLISHED"
