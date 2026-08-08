from dataclasses import replace
from types import SimpleNamespace

import pytest

from acousticbrain.application import (
    ChannelIsolationDeclarationReadiness,
    ChannelIsolationOperationalRecordPreview,
    evidence_acquisition_plan_fingerprint,
)
from acousticbrain.models import (
    EvidenceAcquisitionPlanSynthesis,
    EvidenceAcquisitionStatus,
    EvidencePlanPreparationRegistry,
    EvidencePlanPrerequisiteStatus,
)
from acousticbrain.report import (
    EvidenceAcquisitionPlanPresenter,
    GuidedGlobalStatusConsoleReporter,
    GuidedGlobalStatusPresenter,
    PresentedDiscoveredExperiment,
    PresentedExperimentUserView,
)
from test_evidence_plan_preparation_registry import record
from test_evidence_plan_preparation_resolution import ready_plan


def report_for(*plans, experiments=None):
    context = SimpleNamespace(
        evidence_acquisition_plan_synthesis=EvidenceAcquisitionPlanSynthesis(plans)
    )
    return SimpleNamespace(
        evidence_acquisition_plans=EvidenceAcquisitionPlanPresenter().present(context),
        experiments_discovered=SimpleNamespace(
            experiments=(
                tuple(experiments)
                if experiments is not None
                else (object(), object())
            )
        ),
    )


def registry_with(*records):
    value = EvidencePlanPreparationRegistry()
    for item in records:
        value = value.with_record(item)
    return value


def preparation(left, right, *, confirmation_id=None):
    value = record(left, right)
    if confirmation_id is not None:
        value = replace(
            value,
            confirmation_input=replace(
                value.confirmation_input,
                confirmation_id=confirmation_id,
            ),
        )
    return value


def discovered_experiment(
    plan, confirmation, *, experiment_id="exp-008", source_plan_id=None,
    fingerprint=None, qualification="ALL_PREREQUISITES_USER_CONFIRMED",
    coverage="PLAN_COVERAGE_PARTIAL",
):
    return PresentedDiscoveredExperiment(
        experiment_id=experiment_id,
        experiment_type="EXPERIMENT",
        state="INCOMPLETE",
        file_count=0,
        timestamp="2026-08-08T00:00:00Z",
        available_channels=(),
        source_evidence_acquisition_plan_id=(source_plan_id or plan.plan_id),
        evidence_acquisition_plan_coverage_status=coverage,
        channel_isolation_preparation_confirmation_id=(
            confirmation.confirmation_input.confirmation_id
        ),
        channel_isolation_preparation_plan_fingerprint=(
            fingerprint
            or confirmation.confirmation_input.plan_contract_fingerprint
        ),
        channel_isolation_preparation_qualification_status=qualification,
    )


def test_existing_recommendation_is_reused_when_registry_is_unavailable():
    plan = ready_plan()
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan), plans=(plan,)
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_UNAVAILABLE"
    assert any(plan.plan_id in line for line in result.current_state_lines)
    assert result.user_action_state == "REVIEW_RECOMMENDED_PLAN"


def test_no_plan_and_no_ready_plan_remain_distinct():
    no_plan = GuidedGlobalStatusPresenter().present(
        report_for(), plans=()
    )
    blocked = ready_plan(status=EvidenceAcquisitionStatus.BLOCKED)
    no_ready = GuidedGlobalStatusPresenter().present(
        report_for(blocked), plans=(blocked,)
    )
    assert no_plan.workflow_state == "NO_EVIDENCE_PLAN"
    assert no_ready.workflow_state == "NO_READY_EVIDENCE_PLAN"


def test_missing_preparation_routes_to_existing_draft_workflow():
    plan = ready_plan()
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=EvidencePlanPreparationRegistry(),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_NOT_DECLARED"
    assert result.user_action_state == "GENERATE_PREPARATION_DRAFT"


def test_multiple_preparations_are_never_selected_implicitly():
    plan = ready_plan()
    first = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        confirmation_id="preparation-001",
    )
    second = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-002",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(second, first),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_AMBIGUOUS"
    assert result.user_action_state == "SELECT_EXACT_PREPARATION"
    assert "preparation-001, preparation-002" in result.blocker_lines[0]
    assert "--guided-preparation CONFIRMATION_ID" in result.user_action


def test_explicit_preparation_resolves_one_record_without_using_recency():
    plan = ready_plan()
    first = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        confirmation_id="preparation-001",
    )
    second = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-002",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(second, first),
        preparation_id="preparation-001",
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_INCOMPLETE"
    assert "existing_acquisition_settings=UNKNOWN" in result.blocker_lines[0]


def test_unknown_explicit_preparation_is_rejected():
    plan = ready_plan()
    with pytest.raises(ValueError, match="one exact preparation"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=EvidencePlanPreparationRegistry(),
            preparation_id="unknown-preparation",
        )


@pytest.mark.parametrize(
    "unresolved",
    (
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        EvidencePlanPrerequisiteStatus.NOT_CONFIRMED,
    ),
)
def test_incomplete_preparation_preserves_exact_user_status(unresolved):
    plan = ready_plan()
    value = preparation(EvidencePlanPrerequisiteStatus.CONFIRMED, unresolved)
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_INCOMPLETE"
    assert f"existing_acquisition_settings={unresolved.value}" in result.blocker_lines[0]
    assert result.user_action_state == "REVIEW_EXACT_PREPARATION"


def test_stale_preparation_is_shown_and_not_ignored():
    current = replace(ready_plan(), objective="Current exact objective")
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    assert value.confirmation_input.plan_contract_fingerprint != (
        evidence_acquisition_plan_fingerprint(current)
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(current),
        plans=(current,),
        preparation_registry=registry_with(value),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_STALE"
    assert result.user_action_state == "GENERATE_CURRENT_PREPARATION_DRAFT"


def test_all_confirmed_routes_only_to_existing_readiness_preflight():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_CONFIRMED"
    assert result.user_action_state == "RUN_DECLARATION_READINESS"


def test_one_declared_experiment_requires_explicit_selection():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    candidate = discovered_experiment(plan, value)
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan, experiments=(candidate,)),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
    )
    assert result.workflow_state == (
        "READY_PLAN_DECLARED_EXPERIMENT_SELECTION_REQUIRED"
    )
    assert result.user_action_state == "SELECT_EXACT_DECLARED_EXPERIMENT"
    assert "exp-008" in result.blocker_lines[0]
    assert result.user_action.endswith("--guided-declared-experiment exp-008.")


def test_multiple_declared_experiments_are_sorted_and_never_selected():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    later = discovered_experiment(plan, value, experiment_id="exp-010")
    earlier = discovered_experiment(plan, value, experiment_id="exp-008")
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan, experiments=(later, earlier)),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
    )
    assert result.workflow_state == (
        "READY_PLAN_DECLARED_EXPERIMENT_SELECTION_AMBIGUOUS"
    )
    assert "exp-008, exp-010" in result.blocker_lines[0]
    assert result.user_action.endswith("--guided-declared-experiment EXPERIMENT_ID.")


def test_another_preparation_candidate_does_not_change_current_navigation():
    plan = ready_plan()
    selected = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    other = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-002",
    )
    candidate = discovered_experiment(plan, other)
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan, experiments=(candidate,)),
        plans=(plan,),
        preparation_registry=registry_with(selected),
        preparation_id="preparation-001",
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_CONFIRMED"


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"source_plan_id": "another-plan"}, "targets another plan"),
        ({"fingerprint": "different"}, "provenance is inconsistent"),
        ({"qualification": "PREPARATION_DECLARED"}, "provenance is inconsistent"),
        (
            {"coverage": "PLAN_COVERAGE_INSUFFICIENT_DECLARATION"},
            "specialized declaration is insufficient",
        ),
    ),
)
def test_declared_experiment_candidate_rejects_incompatible_provenance(
    overrides, message
):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    candidate = discovered_experiment(plan, value, **overrides)
    with pytest.raises(ValueError, match=message):
        GuidedGlobalStatusPresenter().present(
            report_for(plan, experiments=(candidate,)),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
        )


def test_declared_experiment_candidate_conflicts_with_incomplete_preparation():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        confirmation_id="preparation-001",
    )
    candidate = discovered_experiment(plan, value)
    with pytest.raises(ValueError, match="conflict with an incomplete preparation"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan, experiments=(candidate,)),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
        )


def test_duplicate_declared_experiment_candidate_identity_is_rejected():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    candidate = discovered_experiment(plan, value)
    with pytest.raises(ValueError, match="candidate identity is ambiguous"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan, experiments=(candidate, candidate)),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
        )


@pytest.mark.parametrize("experiment_id", ("", " exp-008"))
def test_declared_experiment_candidate_id_must_be_exact(experiment_id):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    candidate = discovered_experiment(
        plan,
        value,
        experiment_id=experiment_id,
    )
    with pytest.raises(ValueError, match="candidate id must be exact text"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan, experiments=(candidate,)),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
        )


def test_incomplete_operational_documentation_lists_exact_missing_fields():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        EvidencePlanPrerequisiteStatus.NOT_CONFIRMED,
        confirmation_id="preparation-001",
    )
    preview = ChannelIsolationOperationalRecordPreview(
        status="DOCUMENTATION_INCOMPLETE",
        missing_fields=(
            "acquisition_settings.gain",
            "microphone_position.reference_geometry",
        ),
        microphone_position=None,
        acquisition_settings=None,
        user_action_state="COMPLETE_OPERATIONAL_DOCUMENTATION",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
        operational_record_preview=preview,
    )
    assert result.workflow_state == (
        "READY_PLAN_OPERATIONAL_DOCUMENTATION_INCOMPLETE"
    )
    assert result.user_action_state == "REVISE_OPERATIONAL_WORKSHEETS"
    assert "acquisition_settings.gain" in result.blocker_lines[0]
    assert "microphone_position.reference_geometry" in result.blocker_lines[0]
    assert "documented_microphone_position=UNKNOWN" in result.blocker_lines[1]
    assert "existing_acquisition_settings=NOT_CONFIRMED" in result.blocker_lines[1]


def test_complete_documentation_never_confirms_incomplete_preparation():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        EvidencePlanPrerequisiteStatus.UNKNOWN,
        confirmation_id="preparation-001",
    )
    preview = ChannelIsolationOperationalRecordPreview(
        status="DOCUMENTATION_COMPLETE",
        missing_fields=(),
        microphone_position=object(),
        acquisition_settings=object(),
        user_action_state="REVIEW_PREPARATION_STATUS_SEPARATELY",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
        operational_record_preview=preview,
    )
    assert result.workflow_state == (
        "READY_PLAN_OPERATIONAL_DOCUMENTATION_COMPLETE_PREPARATION_INCOMPLETE"
    )
    assert result.user_action_state == "REVIEW_EXACT_PREPARATION"
    assert "documentation opérationnelle complète" in " ".join(
        result.validated_step_lines
    ).lower()
    assert "UNKNOWN" in result.blocker_lines[0]
    assert result.causality_status == "NOT_ESTABLISHED"


def test_operational_documentation_requires_one_explicit_preparation():
    plan = ready_plan()
    preview = ChannelIsolationOperationalRecordPreview(
        status="DOCUMENTATION_INCOMPLETE",
        missing_fields=("acquisition_settings.gain",),
        microphone_position=None,
        acquisition_settings=None,
        user_action_state="COMPLETE_OPERATIONAL_DOCUMENTATION",
    )
    with pytest.raises(ValueError, match="one exact preparation selection"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(preparation(
                EvidencePlanPrerequisiteStatus.UNKNOWN,
                EvidencePlanPrerequisiteStatus.UNKNOWN,
            )),
            operational_record_preview=preview,
        )


def test_operational_documentation_never_demotes_confirmed_preparation():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    preview = ChannelIsolationOperationalRecordPreview(
        status="DOCUMENTATION_INCOMPLETE",
        missing_fields=("acquisition_settings.gain",),
        microphone_position=None,
        acquisition_settings=None,
        user_action_state="COMPLETE_OPERATIONAL_DOCUMENTATION",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
        operational_record_preview=preview,
    )
    assert result.workflow_state == "READY_PLAN_PREPARATION_CONFIRMED"
    assert result.user_action_state == "RUN_DECLARATION_READINESS"


def test_exact_declaration_readiness_routes_to_separate_declaration(tmp_path):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    readiness = ChannelIsolationDeclarationReadiness(
        plan_id=plan.plan_id,
        confirmation_id="preparation-001",
        preparation_contract_fingerprint=(
            evidence_acquisition_plan_fingerprint(plan)
        ),
        reference_experiment_id="baseline",
        experiment_id="channel-isolation-001",
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
        declaration_readiness=readiness,
        measurement_root=tmp_path,
        preparation_registry_path=tmp_path / "preparations.json",
    )
    assert result.workflow_state == "READY_PLAN_DECLARATION_READY"
    assert result.user_action_state == "DECLARE_EXPERIMENT_SEPARATELY"
    assert "DECLARATION_READY" in " ".join(result.validated_step_lines)
    assert "--experiment channel-isolation-001" in result.user_action
    assert "--reference baseline" in result.user_action
    assert "--preparation-registry" in result.user_action
    assert "--preparation preparation-001" in result.user_action
    assert str(tmp_path.resolve()) in result.user_action
    assert result.causality_status == "NOT_ESTABLISHED"


def test_declaration_readiness_must_match_exact_selected_preparation(tmp_path):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    readiness = ChannelIsolationDeclarationReadiness(
        plan_id=plan.plan_id,
        confirmation_id="preparation-002",
        preparation_contract_fingerprint=(
            evidence_acquisition_plan_fingerprint(plan)
        ),
        reference_experiment_id="baseline",
        experiment_id="channel-isolation-001",
    )
    with pytest.raises(ValueError, match="another preparation"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declaration_readiness=readiness,
            measurement_root=tmp_path,
            preparation_registry_path=tmp_path / "preparations.json",
        )


def declared_experiment_view(
    plan, confirmation_id, fingerprint, lifecycle, *, coverage_status=None,
    observed_result=None, comparison_id=None, causality_status="NOT_ESTABLISHED",
):
    comparison_pending = lifecycle == "COMPARISON_UNAVAILABLE"
    result_available = lifecycle in ("RESULT_INCONCLUSIVE", "RESULT_AVAILABLE")
    if observed_result is None:
        observed_result = (
            "MIXED"
            if lifecycle == "RESULT_INCONCLUSIVE"
            else "IMPROVED"
            if lifecycle == "RESULT_AVAILABLE"
            else "NOT_AVAILABLE"
        )
    return PresentedExperimentUserView(
        experiment_id="exp-008",
        lifecycle_state=lifecycle,
        intent_lines=(plan.objective,),
        user_action_state=(
            "REVIEW_OBSERVED_RESULT"
            if result_available
            else "RESTORE_COMPARABILITY"
            if comparison_pending
            else "COMPLETE_REQUIRED_ACQUISITION"
        ),
        user_action=(
            "Examiner le résultat observé."
            if result_available
            else "Rétablir la comparabilité à partir de la déclaration existante."
            if comparison_pending
            else "Compléter l’acquisition requise déjà déclarée."
        ),
        observed_result=observed_result,
        observed_result_lines=("Aucune comparaison locale unique n’est disponible.",),
        scientific_boundary_lines=("Comparaison locale indisponible.",),
        causality_status=causality_status,
        reference_experiment_id="baseline" if result_available else None,
        comparison_id=(
            comparison_id
            if comparison_id is not None
            else "comparison-008"
            if result_available
            else None
        ),
        source_plan_id=plan.plan_id,
        preparation_confirmation_id=confirmation_id,
        preparation_plan_fingerprint=fingerprint,
        preparation_qualification_status="ALL_PREREQUISITES_USER_CONFIRMED",
        declared_plan_coverage_status=(
            coverage_status
            or (
                "PLAN_COVERAGE_COMPLETE"
                if comparison_pending or result_available
                else "PLAN_COVERAGE_PARTIAL"
            )
        ),
    )


@pytest.mark.parametrize(
    ("lifecycle", "workflow", "action_state"),
    (
        (
            "ACQUISITION_PENDING",
            "READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_PENDING",
            "COMPLETE_REQUIRED_ACQUISITION",
        ),
        (
            "ACQUISITION_INCOMPLETE",
            "READY_PLAN_EXPERIMENT_DECLARED_ACQUISITION_INCOMPLETE",
            "COMPLETE_REQUIRED_ACQUISITION",
        ),
        (
            "COMPARISON_UNAVAILABLE",
            "READY_PLAN_EXPERIMENT_ACQUISITION_COMPLETE_"
            "COMPARISON_UNAVAILABLE",
            "RESTORE_COMPARABILITY",
        ),
    ),
)
def test_declared_experiment_projects_exact_stage(
    lifecycle, workflow, action_state
):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-001",
        value.confirmation_input.plan_contract_fingerprint,
        lifecycle,
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
        declared_experiment_view=view,
    )
    assert result.workflow_state == workflow
    assert result.user_action_state == action_state
    if lifecycle == "COMPARISON_UNAVAILABLE":
        assert any(
            line.startswith("Acquisition spécialisée complète")
            for line in result.validated_step_lines
        )
        assert "comparaison locale unique indisponible" in result.blocker_lines[0]
    else:
        assert "LEFT, RIGHT" in result.blocker_lines[0]
    assert result.causality_status == "NOT_ESTABLISHED"


def test_declared_experiment_rejects_divergent_preparation_provenance():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-002",
        value.confirmation_input.plan_contract_fingerprint,
        "ACQUISITION_PENDING",
    )
    with pytest.raises(ValueError, match="provenance is inconsistent"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_declared_experiment_requires_specialized_declaration_coverage():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = replace(
        declared_experiment_view(
            plan,
            "preparation-001",
            value.confirmation_input.plan_contract_fingerprint,
            "ACQUISITION_PENDING",
        ),
        declared_plan_coverage_status="PLAN_COVERAGE_INSUFFICIENT_DECLARATION",
    )
    with pytest.raises(ValueError, match="specialized declaration is insufficient"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_comparison_pending_requires_complete_specialized_coverage():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-001",
        value.confirmation_input.plan_contract_fingerprint,
        "COMPARISON_UNAVAILABLE",
        coverage_status="PLAN_COVERAGE_PARTIAL",
    )
    with pytest.raises(ValueError, match="specialized declaration is insufficient"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_comparison_pending_rejects_an_acquisition_action():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = replace(
        declared_experiment_view(
            plan,
            "preparation-001",
            value.confirmation_input.plan_contract_fingerprint,
            "COMPARISON_UNAVAILABLE",
        ),
        user_action_state="COMPLETE_REQUIRED_ACQUISITION",
    )
    with pytest.raises(ValueError, match="lifecycle action is inconsistent"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_contract_failure_stage_remains_outside_guided_projection():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-001",
        value.confirmation_input.plan_contract_fingerprint,
        "CONTRACT_MISSING",
        coverage_status="PLAN_COVERAGE_COMPLETE",
    )
    with pytest.raises(ValueError, match="outside the guided experiment lifecycle"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


@pytest.mark.parametrize(
    ("lifecycle", "outcome", "workflow"),
    (
        (
            "RESULT_INCONCLUSIVE",
            "MIXED",
            "READY_PLAN_EXPERIMENT_RESULT_INCONCLUSIVE",
        ),
        (
            "RESULT_INCONCLUSIVE",
            "INCONCLUSIVE",
            "READY_PLAN_EXPERIMENT_RESULT_INCONCLUSIVE",
        ),
        (
            "RESULT_AVAILABLE",
            "IMPROVED",
            "READY_PLAN_EXPERIMENT_RESULT_AVAILABLE",
        ),
        (
            "RESULT_AVAILABLE",
            "DEGRADED",
            "READY_PLAN_EXPERIMENT_RESULT_AVAILABLE",
        ),
        (
            "RESULT_AVAILABLE",
            "UNCHANGED",
            "READY_PLAN_EXPERIMENT_RESULT_AVAILABLE",
        ),
    ),
)
def test_result_stage_preserves_existing_outcome(lifecycle, outcome, workflow):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-001",
        value.confirmation_input.plan_contract_fingerprint,
        lifecycle,
        observed_result=outcome,
    )
    result = GuidedGlobalStatusPresenter().present(
        report_for(plan),
        plans=(plan,),
        preparation_registry=registry_with(value),
        preparation_id="preparation-001",
        declared_experiment_view=view,
    )
    assert result.workflow_state == workflow
    assert result.user_action_state == "REVIEW_OBSERVED_RESULT"
    assert f"Résultat observé : {outcome}." in result.blocker_lines
    assert "Comparaison locale : comparison-008." in result.current_state_lines
    assert result.causality_status == "NOT_ESTABLISHED"


@pytest.mark.parametrize("invalid_id", (None, "", " comparison-008"))
def test_result_stage_requires_exact_comparison_identity(invalid_id):
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = replace(
        declared_experiment_view(
            plan,
            "preparation-001",
            value.confirmation_input.plan_contract_fingerprint,
            "RESULT_INCONCLUSIVE",
        ),
        comparison_id=invalid_id,
    )
    with pytest.raises(ValueError, match="one exact local comparison"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_result_stage_rejects_a_rewritten_action():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = replace(
        declared_experiment_view(
            plan,
            "preparation-001",
            value.confirmation_input.plan_contract_fingerprint,
            "RESULT_INCONCLUSIVE",
        ),
        user_action="Interpréter ce résultat comme une amélioration.",
    )
    with pytest.raises(ValueError, match="lifecycle action is inconsistent"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_result_stage_rejects_inconsistent_outcome():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-001",
        value.confirmation_input.plan_contract_fingerprint,
        "RESULT_AVAILABLE",
        observed_result="MIXED",
    )
    with pytest.raises(ValueError, match="outcome are inconsistent"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_result_stage_never_promotes_causality():
    plan = ready_plan()
    value = preparation(
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        EvidencePlanPrerequisiteStatus.CONFIRMED,
        confirmation_id="preparation-001",
    )
    view = declared_experiment_view(
        plan,
        "preparation-001",
        value.confirmation_input.plan_contract_fingerprint,
        "RESULT_AVAILABLE",
        causality_status="ESTABLISHED",
    )
    with pytest.raises(ValueError, match="cannot promote experiment causality"):
        GuidedGlobalStatusPresenter().present(
            report_for(plan),
            plans=(plan,),
            preparation_registry=registry_with(value),
            preparation_id="preparation-001",
            declared_experiment_view=view,
        )


def test_console_always_renders_five_blocks_and_one_action(capsys):
    plan = ready_plan()
    view = GuidedGlobalStatusPresenter().present(report_for(plan), plans=(plan,))
    GuidedGlobalStatusConsoleReporter().print(view)
    output = capsys.readouterr().out
    for heading in (
        "État actuel",
        "Dernière étape validée",
        "Blocage actuel",
        "Action utilisateur",
        "Frontière scientifique",
    ):
        assert output.count(heading) == 1
    assert "Causality status: NOT_ESTABLISHED" in output
