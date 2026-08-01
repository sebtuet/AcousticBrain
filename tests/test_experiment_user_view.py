from types import SimpleNamespace

import pytest

from acousticbrain.report import ExperimentUserViewPresenter


def value(**kwargs):
    return SimpleNamespace(**kwargs)


def experiment(**overrides):
    defaults = dict(
        experiment_id="exp-007",
        state="READY",
        file_count=2,
        source_evidence_acquisition_plan_id="plan-007",
        plan_contract_preservation_status="PLAN_COVERAGE_COMPLETE",
        evidence_acquisition_plan_coverage_status="PLAN_COVERAGE_COMPLETE",
        plan_contract_limitations=(),
        preserved_plan_contract_mode="EXPLORATORY",
        preserved_plan_objective="Test the declared temporary intervention against baseline.",
        preserved_plan_controlled_variables=("microphone position",),
        preserved_plan_expected_observations=("FACT_UP", "FACT_DOWN"),
        preserved_plan_limitations=("Temporary intervention only.",),
    )
    defaults.update(overrides)
    return value(**defaults)


def comparison(**overrides):
    defaults = dict(
        before_experiment_id="baseline",
        after_experiment_id="exp-007",
        comparison_type="LOCAL",
        eligibility="COMPARABLE",
        ineligibility_reasons=(),
        acoustic_outcome="MIXED",
        improved_fact_codes=("FACT_UP",),
        degraded_fact_codes=("FACT_DOWN",),
        changed_fact_codes=(),
        unchanged_fact_codes=(),
        unavailable_fact_codes=(),
        modified_variables=("temporary intervention",),
        controlled_variables=("microphone position",),
        source_protocol_id="protocol-1",
        source_hypothesis_code="hypothesis-1",
        trace_id="comparison-007",
    )
    defaults.update(overrides)
    return value(**defaults)


def plan():
    return value(
        plan_id="plan-007",
        objective="Test the declared temporary intervention against baseline.",
        expected_observations=("FACT_UP", "FACT_DOWN"),
        limitations=("Temporary intervention only.",),
    )


def report(experiments=None, comparisons=None, plans=None):
    return value(
        experiments_discovered=value(
            experiments=tuple(experiments if experiments is not None else (experiment(),))
        ),
        experiment_comparison=value(
            local_comparisons=tuple(
                comparisons if comparisons is not None else (comparison(),)
            ),
            cumulative_comparisons=(comparison(),),
        ),
        evidence_acquisition_plans=value(
            plans=tuple(plans if plans is not None else (plan(),))
        ),
    )


def test_preserves_mixed_and_all_source_identifiers():
    presented = ExperimentUserViewPresenter().present(report(), "exp-007")

    assert presented.lifecycle_state == "RESULT_INCONCLUSIVE"
    assert presented.observed_result == "MIXED"
    assert presented.causality_status == "NOT_ESTABLISHED"
    assert presented.reference_experiment_id == "baseline"
    assert presented.source_plan_id == "plan-007"
    assert presented.source_protocol_id == "protocol-1"
    assert presented.source_hypothesis_code == "hypothesis-1"
    assert presented.comparison_id == "comparison-007"
    assert presented.user_action_state == "REVIEW_OBSERVED_RESULT"


def test_unknown_experiment_is_explicitly_rejected():
    with pytest.raises(ValueError, match="Unknown experiment_id: exp-404"):
        ExperimentUserViewPresenter().present(report(), "exp-404")


def test_multiple_local_references_are_explicitly_rejected():
    other = comparison(before_experiment_id="other-reference")
    with pytest.raises(ValueError, match="Ambiguous local comparison"):
        ExperimentUserViewPresenter().present(
            report(comparisons=(comparison(), other)), "exp-007"
        )


def test_historical_manifest_remains_readable_without_reconstructed_intent():
    historical = experiment(
        source_evidence_acquisition_plan_id=None,
        preserved_plan_contract_mode=None,
        preserved_plan_objective=None,
        preserved_plan_controlled_variables=(),
        preserved_plan_expected_observations=(),
        preserved_plan_limitations=(),
    )
    presented = ExperimentUserViewPresenter().present(
        report(experiments=(historical,), plans=()), "exp-007"
    )

    assert presented.lifecycle_state == "CONTRACT_MISSING"
    assert presented.intent_lines[0] == "Original plan intent unavailable."
    assert presented.observed_result == "MIXED"
    assert presented.user_action_state == "NO_USER_ACTION"
    assert any("Historical limit" in line for line in presented.scientific_boundary_lines)


@pytest.mark.parametrize("outcome", ("IMPROVED", "DEGRADED", "UNCHANGED", "INCONCLUSIVE"))
def test_presenter_copies_each_existing_outcome_verbatim(outcome):
    presented = ExperimentUserViewPresenter().present(
        report(comparisons=(comparison(acoustic_outcome=outcome),)), "exp-007"
    )
    assert presented.observed_result == outcome


def test_missing_comparison_keeps_all_four_blocks_populated():
    presented = ExperimentUserViewPresenter().present(
        report(comparisons=()), "exp-007"
    )

    assert presented.intent_lines
    assert presented.user_action
    assert presented.observed_result == "NOT_AVAILABLE"
    assert presented.observed_result_lines
    assert presented.scientific_boundary_lines
    assert presented.user_action_state == "RESTORE_COMPARABILITY"


def test_collection_order_does_not_change_exact_experiment_resolution():
    unrelated = experiment(experiment_id="exp-008")
    first = ExperimentUserViewPresenter().present(
        report(experiments=(unrelated, experiment())), "exp-007"
    )
    second = ExperimentUserViewPresenter().present(
        report(experiments=(experiment(), unrelated)), "exp-007"
    )
    assert first == second
