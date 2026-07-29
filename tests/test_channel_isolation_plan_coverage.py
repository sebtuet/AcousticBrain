from acousticbrain.application import ChannelIsolationPlanCoverageValidator
from acousticbrain.models import (
    ChannelIsolationDeclaration,
    EvidenceAcquisitionEffort,
    EvidenceAcquisitionPlan,
    EvidenceAcquisitionPriority,
    EvidenceAcquisitionStatus,
    EvidenceAcquisitionTestType,
    ExperimentDeclaration,
    ExperimentDescriptor,
    ExperimentKind,
    ExperimentState,
    ExperimentType,
    ImpulseChannel,
    PlanCoverageStatus,
)


def plan(test_type=EvidenceAcquisitionTestType.CHANNEL_ISOLATION):
    return EvidenceAcquisitionPlan(
        plan_id="PLAN",
        reasoning_id="REASONING",
        corrective_action_id="ACTION",
        evidence_weight_id="WEIGHT",
        blocking_factor_ids=("FACTOR",),
        objective="Acquire evidence.",
        test_type=test_type,
        instructions=("Measure declared channels separately.",),
        required_inputs=("input_b", "input_a"),
        controlled_variables=("control_b", "control_a"),
        independent_variables=("active_channel",),
        measurements_to_capture=("measurement_b", "measurement_a"),
        expected_observations=("observation",),
        success_criteria=("Acquire comparable evidence.",),
        failure_criteria=(),
        resulting_evidence_targets=("TARGET",),
        priority=EvidenceAcquisitionPriority.HIGH,
        estimated_effort=EvidenceAcquisitionEffort.MEDIUM,
        status=EvidenceAcquisitionStatus.READY,
        limitations=("No result interpretation.",),
    )


def experimental_declaration(
    *,
    modified_variables=("active_channel",),
    controlled_variables=("control_b", "control_a"),
):
    return ExperimentDeclaration(
        schema_version=1,
        experiment_kind=ExperimentKind.CONTROLLED_INTERVENTION,
        reference_experiment_code="baseline",
        modified_variables=modified_variables,
        controlled_variables=controlled_variables,
        user_note=None,
        field_provenance=(
            ("controlled_variables", "USER_MANIFEST"),
            ("experiment_kind", "USER_MANIFEST"),
            ("modified_variables", "USER_MANIFEST"),
            ("reference_experiment_code", "USER_MANIFEST"),
            ("user_note", "USER_MANIFEST"),
        ),
    )


def experiment(
    *,
    channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
    declaration=None,
    channel_declaration=None,
    filenames=("left.txt", "right.txt", "repeat.txt"),
):
    return ExperimentDescriptor(
        experiment_id="exp-001",
        directory="/measurements/exp-001",
        experiment_type=ExperimentType.EXPERIMENT,
        available_files=(),
        available_channels=channels,
        wav_files=(),
        txt_files=filenames,
        mdat_file=None,
        manifest_present=True,
        content_hash="a" * 64,
        timestamp="2026-07-29T10:00:00",
        imported_at="2026-07-29T10:00:00",
        state=ExperimentState.READY,
        experiment_declaration=declaration or ExperimentDeclaration.unknown(),
        channel_isolation_declaration=channel_declaration,
    )


def complete_channel_declaration(
    *,
    repeated_channels=(ImpulseChannel.RIGHT, ImpulseChannel.LEFT),
    available_inputs=("input_b", "input_a"),
    controlled_variables=("control_b", "control_a"),
    independent_variables=("active_channel",),
    measurements=("measurement_b", "measurement_a"),
):
    return ChannelIsolationDeclaration(
        repeated_channels=repeated_channels,
        available_inputs=available_inputs,
        controlled_variables=controlled_variables,
        independent_variables=independent_variables,
        measurements=measurements,
    )


def validate(experiment_value, plan_value):
    return ChannelIsolationPlanCoverageValidator().validate(
        experiment_value,
        plan_value,
    )


def test_coverage_is_not_applicable_without_resolved_plan():
    result = validate(experiment(), None)

    assert result.status is PlanCoverageStatus.NOT_APPLICABLE
    assert result.covered_requirements == ()
    assert result.missing_requirements == ()


def test_coverage_is_not_applicable_for_non_channel_isolation_plan():
    result = validate(
        experiment(),
        plan(EvidenceAcquisitionTestType.REPEAT_MEASUREMENT),
    )

    assert result.status is PlanCoverageStatus.NOT_APPLICABLE
    assert result.limitations == (
        "Plan coverage validation supports CHANNEL_ISOLATION only.",
    )


def test_resolved_plan_without_structured_declaration_is_insufficient():
    result = validate(experiment(), plan())

    assert result.status is PlanCoverageStatus.INSUFFICIENT_DECLARATION
    assert result.covered_requirements == ()
    assert result.missing_requirements == ()
    assert "acquired_channel:LEFT" in result.unverifiable_requirements


def test_partial_declaration_distinguishes_covered_and_missing_requirements():
    result = validate(
        experiment(
            channels=(ImpulseChannel.LEFT,),
            channel_declaration=complete_channel_declaration(
                repeated_channels=(ImpulseChannel.LEFT,),
                available_inputs=("input_a",),
                controlled_variables=("control_a",),
                measurements=("measurement_a",),
            ),
        ),
        plan(),
    )

    assert result.status is PlanCoverageStatus.PARTIAL
    assert result.covered_requirements == tuple(sorted((
        "acquired_channel:LEFT",
        "controlled_variable:control_a",
        "independent_variable:active_channel",
        "measurement:measurement_a",
        "repeated_channel:LEFT",
        "required_input:input_a",
    )))
    assert result.missing_requirements == tuple(sorted((
        "acquired_channel:RIGHT",
        "controlled_variable:control_b",
        "measurement:measurement_b",
        "repeated_channel:RIGHT",
        "required_input:input_b",
    )))


def test_complete_declaration_covers_every_verifiable_requirement():
    result = validate(
        experiment(
            channel_declaration=complete_channel_declaration(),
        ),
        plan(),
    )

    assert result.status is PlanCoverageStatus.COMPLETE
    assert result.missing_requirements == ()
    assert result.unverifiable_requirements == (
        "expected_observation_results",
        "procedure_execution",
    )


def test_stereo_does_not_cover_separate_left_and_right_acquisitions():
    result = validate(
        experiment(
            channels=(ImpulseChannel.STEREO,),
            channel_declaration=complete_channel_declaration(),
        ),
        plan(),
    )

    assert result.status is PlanCoverageStatus.PARTIAL
    assert "acquired_channel:LEFT" in result.missing_requirements
    assert "acquired_channel:RIGHT" in result.missing_requirements


def test_file_names_never_cover_channels_or_repetitions():
    result = validate(
        experiment(
            channels=(),
            channel_declaration=complete_channel_declaration(
                repeated_channels=(),
            ),
            filenames=("left.txt", "right.txt", "repeat.txt"),
        ),
        plan(),
    )

    assert "acquired_channel:LEFT" in result.missing_requirements
    assert "acquired_channel:RIGHT" in result.missing_requirements
    assert "repeated_channel:LEFT" in result.missing_requirements
    assert "repeated_channel:RIGHT" in result.missing_requirements


def test_declaration_identifiers_are_compared_without_normalization():
    result = validate(
        experiment(
            channel_declaration=complete_channel_declaration(
                controlled_variables=(" control_a ", "control_b"),
            ),
        ),
        plan(),
    )

    assert "controlled_variable:control_a" in result.missing_requirements
    assert (
        "controlled_variable: control_a "
        not in result.covered_requirements
    )


def test_coverage_result_is_stable_independently_of_declaration_order():
    first = validate(
        experiment(
            channel_declaration=complete_channel_declaration(),
        ),
        plan(),
    )
    second = validate(
        experiment(
            channels=(ImpulseChannel.RIGHT, ImpulseChannel.LEFT),
            channel_declaration=complete_channel_declaration(
                repeated_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
                available_inputs=("input_a", "input_b"),
                controlled_variables=("control_a", "control_b"),
                measurements=("measurement_a", "measurement_b"),
            ),
        ),
        plan(),
    )

    assert first == second
