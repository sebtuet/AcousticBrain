from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.analysis.campaign_reference_qualification import (
    CampaignReferenceQualificationBuilder,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.brain.stages.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerationStage,
)
from acousticbrain.brain.stages.campaign_reference_qualification import (
    CampaignReferenceQualificationStage,
)
from acousticbrain.brain.stages.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanStage,
)
from acousticbrain.models import (
    CampaignReferenceDeclarationStatus,
    CampaignReferenceQualificationStatus,
    ComparisonEligibilityStatus,
    ExperimentKind,
    ExperimentState,
    ListeningPositionCampaignPlanStatus,
)
from acousticbrain.persistence import (
    CampaignReferenceQualificationJsonLoader,
    ListeningPositionCampaignInstanceJsonLoader,
)
from acousticbrain.report import (
    AcousticHypothesisExperimentGenerationPresenter,
    CampaignReferenceQualificationPresenter,
    ConsoleReporter,
    ListeningPositionCampaignInstancePresenter,
    ListeningPositionCampaignPlanPresenter,
    Report,
)
from test_acoustic_hypothesis_experiment_generation import modal_context
from test_golden_report import reference_project
from test_listening_position_campaign_instance import (
    CONTROLS,
    MEASUREMENTS,
    valid_payload as valid_instance_payload,
)
from test_listening_position_campaign_plan import (
    comparable_sequence,
    structured_reference,
)
from test_main_cli import RecordingBrain, RecordingReporter


def valid_qualification_payload(
    *, experiment_id="exp-007", instance_id="listening-position-campaign-test"
):
    return {
        "schema_version": 1,
        "qualification_id": f"{experiment_id}-listening-position-reference",
        "experiment_id": experiment_id,
        "intended_protocol_id": "protocol.verify_modal_bass_persistence.v1",
        "intended_protocol_version": 1,
        "intended_campaign_instance_id": instance_id,
        "reference_role": "REFERENCE",
        "configuration_state": {code: "KNOWN" for code in CONTROLS},
        "required_measurements": list(MEASUREMENTS),
        "declaration_source": "USER_JSON_TEST",
        "declaration_version": 1,
        "notes": None,
    }


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_qualification(path):
    return CampaignReferenceQualificationJsonLoader().load(path)


def qualification_context(
    tmp_path,
    *,
    qualification_payload=None,
    descriptor=True,
    comparable=True,
):
    instance_path = write_json(
        tmp_path / "instance.json", valid_instance_payload()
    )
    instance_analysis = ListeningPositionCampaignInstanceJsonLoader().load(
        instance_path
    )
    qualification_path = write_json(
        tmp_path / "qualification.json",
        qualification_payload or valid_qualification_payload(),
    )
    declaration_analysis = load_qualification(qualification_path)
    value = modal_context(with_sampling_geometry=False)
    value.listening_position_campaign_instance_analysis = instance_analysis
    value.campaign_reference_qualification_declaration_analysis = (
        declaration_analysis
    )
    protocol = instance_analysis.instance.to_sampling_protocol()
    value.listening_position_sampling_protocol = protocol
    AcousticHypothesisExperimentGenerationStage().run(value)
    value.experiment_descriptors = (
        (structured_reference(protocol, "exp-007"),) if descriptor else ()
    )
    value.experiment_comparison_analysis = (
        comparable_sequence("exp-007") if comparable else None
    )
    CampaignReferenceQualificationStage().run(value)
    ListeningPositionCampaignPlanStage().run(value)
    return value, instance_path, qualification_path


def test_valid_json_loads_explicit_declaration(tmp_path):
    source = write_json(
        tmp_path / "qualification.json", valid_qualification_payload()
    )

    analysis = load_qualification(source)

    assert analysis.status is CampaignReferenceDeclarationStatus.VALID
    assert analysis.declaration.experiment_id == "exp-007"
    assert analysis.source_path == str(source.resolve())


def test_invalid_json_returns_structured_error(tmp_path):
    source = tmp_path / "invalid.json"
    source.write_text("{invalid", encoding="utf-8")

    analysis = load_qualification(source)

    assert analysis.status is CampaignReferenceDeclarationStatus.INVALID
    assert analysis.blocking_reasons == (
        "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
    )


def test_absent_file_returns_structured_error(tmp_path):
    analysis = load_qualification(tmp_path / "missing.json")

    assert analysis.blocking_reasons == (
        "CAMPAIGN_REFERENCE_DECLARATION_UNAVAILABLE",
    )


@pytest.mark.parametrize("schema_version", (2, True, "1"))
def test_unsupported_schema_is_rejected(tmp_path, schema_version):
    payload = valid_qualification_payload()
    payload["schema_version"] = schema_version

    analysis = load_qualification(
        write_json(tmp_path / "schema.json", payload)
    )

    assert analysis.status is CampaignReferenceDeclarationStatus.INVALID


def test_nonexistent_experiment_blocks_qualification(tmp_path):
    value, _, _ = qualification_context(tmp_path, descriptor=False)

    qualification = value.campaign_reference_qualification
    assert qualification.status is CampaignReferenceQualificationStatus.BLOCKED
    assert "CAMPAIGN_REFERENCE_EXPERIMENT_NOT_FOUND" in qualification.blocking_reasons


def test_non_ready_experiment_blocks_qualification(tmp_path):
    value, _, _ = qualification_context(tmp_path)
    value.experiment_descriptors[0].state = ExperimentState.INCOMPLETE

    qualification = CampaignReferenceQualificationBuilder().build(value)

    assert "CAMPAIGN_REFERENCE_EXPERIMENT_NOT_READY" in qualification.blocking_reasons


@pytest.mark.parametrize("missing", MEASUREMENTS)
def test_actual_left_right_and_stereo_are_required(tmp_path, missing):
    value, _, _ = qualification_context(tmp_path)
    descriptor = value.experiment_descriptors[0]
    descriptor.available_channels = tuple(
        item
        for item in descriptor.available_channels
        if getattr(item, "value", str(item)) != missing
    )

    qualification = CampaignReferenceQualificationBuilder().build(value)

    assert "CAMPAIGN_REFERENCE_MEASUREMENTS_INCOMPLETE" in (
        qualification.blocking_reasons
    )
    assert qualification.contradicting_fact_codes == (
        "campaign_reference.measurement_assertion_contradicted",
    )


def test_unknown_historical_declaration_blocks_qualification(tmp_path):
    value, _, _ = qualification_context(tmp_path)
    value.experiment_descriptors[0].experiment_declaration.experiment_kind = (
        ExperimentKind.UNKNOWN
    )

    qualification = CampaignReferenceQualificationBuilder().build(value)

    assert "CAMPAIGN_REFERENCE_DECLARATION_UNKNOWN" in qualification.blocking_reasons


def test_non_comparable_reference_blocks_qualification(tmp_path):
    value, _, _ = qualification_context(tmp_path, comparable=False)

    qualification = value.campaign_reference_qualification
    assert "CAMPAIGN_REFERENCE_COMPARABILITY_UNAVAILABLE" in (
        qualification.blocking_reasons
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("intended_protocol_id", "protocol.other.v1"),
        ("intended_protocol_version", 2),
    ),
)
def test_protocol_identity_must_match(tmp_path, field, value):
    payload = valid_qualification_payload()
    payload[field] = value

    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )

    assert "CAMPAIGN_REFERENCE_PROTOCOL_MISMATCH" in (
        context.campaign_reference_qualification.blocking_reasons
    )


def test_campaign_instance_identity_must_match(tmp_path):
    payload = valid_qualification_payload(instance_id="another-instance")

    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )

    assert "CAMPAIGN_REFERENCE_INSTANCE_MISMATCH" in (
        context.campaign_reference_qualification.blocking_reasons
    )


def test_non_reference_role_is_invalid_at_declaration_level(tmp_path):
    payload = valid_qualification_payload()
    payload["reference_role"] = "FORWARD"

    analysis = load_qualification(
        write_json(tmp_path / "role.json", payload)
    )

    assert analysis.status is CampaignReferenceDeclarationStatus.INVALID
    assert analysis.blocking_reasons == (
        "CAMPAIGN_REFERENCE_DECLARATION_INVALID",
    )


def test_unknown_controlled_variable_blocks_and_does_not_become_known(tmp_path):
    payload = valid_qualification_payload()
    payload["configuration_state"]["MICROPHONE_ORIENTATION"] = "UNKNOWN"

    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )
    qualification = context.campaign_reference_qualification

    assert "CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE" in (
        qualification.blocking_reasons
    )
    assert "MICROPHONE_ORIENTATION" not in (
        qualification.qualified_controlled_variables
    )


def test_absent_controlled_variable_blocks_qualification(tmp_path):
    payload = valid_qualification_payload()
    del payload["configuration_state"]["MICROPHONE_ORIENTATION"]

    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )

    assert "CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE" in (
        context.campaign_reference_qualification.blocking_reasons
    )


def test_assertion_contradicting_historical_fact_is_rejected(tmp_path):
    payload = valid_qualification_payload()
    payload["configuration_state"]["REW_PARAMETERS"] = "UNKNOWN"

    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )
    qualification = context.campaign_reference_qualification

    assert "CAMPAIGN_REFERENCE_HISTORICAL_CONTRADICTION" in (
        qualification.blocking_reasons
    )
    assert (
        "campaign_reference.assertion_conflicts_history.REW_PARAMETERS"
        in qualification.contradicting_fact_codes
    )


def test_valid_declaration_can_be_scientifically_blocked(tmp_path):
    payload = valid_qualification_payload()
    payload["configuration_state"]["MICROPHONE_ORIENTATION"] = "UNKNOWN"

    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )

    assert (
        context.campaign_reference_qualification_declaration_analysis.status
        is CampaignReferenceDeclarationStatus.VALID
    )
    assert (
        context.campaign_reference_qualification.status
        is CampaignReferenceQualificationStatus.BLOCKED
    )


def test_complete_cross_checked_qualification_is_qualified(tmp_path):
    context, _, _ = qualification_context(tmp_path)
    qualification = context.campaign_reference_qualification

    assert qualification.status is CampaignReferenceQualificationStatus.QUALIFIED
    assert qualification.blocking_reasons == ()
    assert qualification.contradicting_fact_codes == ()
    assert qualification.missing_fact_codes == ()
    assert qualification.causality_status == "NOT_ESTABLISHED"


def test_qualification_for_another_experiment_is_refused_without_substitution(tmp_path):
    payload = valid_qualification_payload(experiment_id="exp-008")
    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )
    protocol = context.listening_position_sampling_protocol
    alternative = structured_reference(protocol, "exp-008")
    context.experiment_descriptors = (
        context.experiment_descriptors[0],
        alternative,
    )
    context.experiment_comparison_analysis = SimpleNamespace(
        sequence=SimpleNamespace(
            chronology=("exp-007", "exp-008"),
            local_comparisons=(
                SimpleNamespace(
                    after_experiment_id="exp-007",
                    eligibility=ComparisonEligibilityStatus.COMPARABLE,
                ),
                SimpleNamespace(
                    after_experiment_id="exp-008",
                    eligibility=ComparisonEligibilityStatus.COMPARABLE,
                ),
            ),
        )
    )
    CampaignReferenceQualificationStage().run(context)
    ListeningPositionCampaignPlanStage().run(context)

    assert context.listening_position_campaign_plan.status is (
        ListeningPositionCampaignPlanStatus.BLOCKED
    )
    assert context.listening_position_campaign_plan.reference_experiment_id is None


def test_plan_ready_only_with_qualified_reference(tmp_path):
    context, _, _ = qualification_context(tmp_path)

    assert context.listening_position_campaign_plan.status is (
        ListeningPositionCampaignPlanStatus.READY
    )
    assert context.listening_position_campaign_plan.reference_experiment_id == "exp-007"


def test_plan_blocked_without_qualification(tmp_path):
    context, _, _ = qualification_context(tmp_path)
    context.campaign_reference_qualification = None

    ListeningPositionCampaignPlanStage().run(context)

    assert context.listening_position_campaign_plan.status is (
        ListeningPositionCampaignPlanStatus.BLOCKED
    )
    assert context.listening_position_campaign_plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


@pytest.mark.parametrize(
    "qualification_status",
    (
        CampaignReferenceQualificationStatus.INVALID,
        CampaignReferenceQualificationStatus.BLOCKED,
    ),
)
def test_plan_blocked_with_invalid_or_blocked_qualification(
    tmp_path, qualification_status
):
    context, _, _ = qualification_context(tmp_path)
    qualification = context.campaign_reference_qualification
    reason = (
        "CAMPAIGN_REFERENCE_DECLARATION_INVALID"
        if qualification_status is CampaignReferenceQualificationStatus.INVALID
        else "CAMPAIGN_REFERENCE_CONFIGURATION_INCOMPLETE"
    )
    context.campaign_reference_qualification = type(qualification)(
        **{
            **qualification.__dict__,
            "status": qualification_status,
            "blocking_reasons": (reason,),
            "missing_fact_codes": ("campaign_reference.test",),
        }
    )

    ListeningPositionCampaignPlanStage().run(context)

    assert context.listening_position_campaign_plan.status is (
        ListeningPositionCampaignPlanStatus.BLOCKED
    )


def test_blocked_plan_never_makes_candidate_main(tmp_path):
    payload = valid_qualification_payload()
    payload["configuration_state"]["MICROPHONE_ORIENTATION"] = "UNKNOWN"
    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )

    analysis = context.acoustic_hypothesis_experiment_generation_analysis
    assert analysis.recommended_candidate_id is None
    assert context.listening_position_campaign_plan.status is (
        ListeningPositionCampaignPlanStatus.BLOCKED
    )


@pytest.mark.parametrize(
    ("kind", "expected_status"),
    (
        ("qualified", "QUALIFIED"),
        ("blocked", "BLOCKED"),
        ("invalid", "INVALID"),
    ),
)
def test_report_distinguishes_qualified_blocked_and_invalid(
    tmp_path, capsys, kind, expected_status
):
    payload = valid_qualification_payload()
    if kind == "blocked":
        payload["configuration_state"]["MICROPHONE_ORIENTATION"] = "UNKNOWN"
    context, _, _ = qualification_context(
        tmp_path, qualification_payload=payload
    )
    if kind == "invalid":
        source = write_json(tmp_path / "invalid.json", {"schema_version": 1})
        context.campaign_reference_qualification_declaration_analysis = (
            load_qualification(source)
        )
        CampaignReferenceQualificationStage().run(context)
        ListeningPositionCampaignPlanStage().run(context)
    report = Report(project_name=f"reference-{kind}")
    report.acoustic_hypothesis_experiment_generation = (
        AcousticHypothesisExperimentGenerationPresenter().present(context)
    )
    report.listening_position_campaign_instance = (
        ListeningPositionCampaignInstancePresenter().present(context)
    )
    report.campaign_reference_qualification = (
        CampaignReferenceQualificationPresenter().present(context)
    )
    report.listening_position_campaign_plan = (
        ListeningPositionCampaignPlanPresenter().present(context)
    )

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "QUALIFICATION DE RÉFÉRENCE DE CAMPAGNE" in output
    assert f"Statut : {expected_status}" in output
    if expected_status == "QUALIFIED":
        assert "PLAN DE CAMPAGNE MULTI-POSITION\n\nStatut : READY" in output
    else:
        assert "PLAN DE CAMPAGNE MULTI-POSITION\n\nStatut : BLOCKED" in output


@pytest.mark.parametrize("kind", ("relative", "absolute", "spaces"))
def test_cli_accepts_relative_absolute_and_space_paths(
    tmp_path, monkeypatch, kind
):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    instance = write_json(
        tmp_path / "campaign instance.json", valid_instance_payload()
    )
    qualification = write_json(
        tmp_path / "reference qualification.json",
        valid_qualification_payload(),
    )
    monkeypatch.chdir(tmp_path)
    campaign_arg = Path("measurements") if kind == "relative" else campaign
    instance_arg = (
        Path("campaign instance.json") if kind != "absolute" else instance
    )
    qualification_arg = (
        Path("reference qualification.json")
        if kind != "absolute"
        else qualification
    )
    brain = RecordingBrain()

    result = acousticbrain_main.main(
        [
            "--measurements-root",
            str(campaign_arg),
            "--listening-position-campaign",
            str(instance_arg),
            "--campaign-reference-qualification",
            str(qualification_arg),
        ],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert result == 0
    passed = brain.calls[0][
        "campaign_reference_qualification_declaration_analysis"
    ]
    assert passed.status is CampaignReferenceDeclarationStatus.VALID
    assert passed.source_path == str(qualification.resolve())


def test_cli_invalid_file_is_clear_nonzero_without_traceback(tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    qualification = tmp_path / "invalid qualification.json"
    qualification.write_text("{invalid", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(Path(acousticbrain_main.__file__).resolve()),
            "--measurements-root",
            str(campaign),
            "--campaign-reference-qualification",
            str(qualification),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "CAMPAIGN_REFERENCE_DECLARATION_INVALID" in result.stderr
    assert "Traceback" not in result.stderr


def test_without_cli_argument_historical_call_is_strictly_unchanged(tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_evidence_acquisition": True,
        }
    ]


def test_loader_and_pipeline_are_read_only_and_preserve_cwd(tmp_path):
    before_cwd = Path.cwd()
    context, instance, qualification = qualification_context(tmp_path)
    before = {
        path: (path.read_bytes(), path.stat().st_size, path.stat().st_mtime_ns)
        for path in (instance, qualification)
    }

    CampaignReferenceQualificationStage().run(context)
    ListeningPositionCampaignPlanStage().run(context)

    assert Path.cwd() == before_cwd
    for path, expected in before.items():
        assert (path.read_bytes(), path.stat().st_size, path.stat().st_mtime_ns) == expected


def test_no_future_experiment_is_created_or_named(tmp_path):
    context, _, _ = qualification_context(tmp_path)

    assert "exp-008" not in repr(context.listening_position_campaign_plan)
    assert all(
        step.step_id.startswith("campaign-step.")
        for step in context.listening_position_campaign_plan.steps
    )


def test_scientific_outputs_remain_invariant(tmp_path):
    declaration = load_qualification(
        write_json(
            tmp_path / "qualification.json", valid_qualification_payload()
        )
    )
    instance = ListeningPositionCampaignInstanceJsonLoader().load(
        write_json(tmp_path / "instance.json", valid_instance_payload())
    )
    project = reference_project()
    baseline = AcousticBrain().analyze(project)
    enriched = AcousticBrain().analyze(
        project,
        listening_position_campaign_instance_analysis=instance,
        campaign_reference_qualification_declaration_analysis=declaration,
    )

    assert enriched.global_analysis == baseline.global_analysis
    assert enriched.recommendations == baseline.recommendations
    assert enriched.causal_discrimination == baseline.causal_discrimination
    assert (
        enriched.longitudinal_experimental_learning
        == baseline.longitudinal_experimental_learning
    )
    assert tuple(
        item.hypothesis_code
        for item in enriched.acoustic_hypothesis_experiment_generation.hypotheses
    ) == tuple(
        item.hypothesis_code
        for item in baseline.acoustic_hypothesis_experiment_generation.hypotheses
    )


def test_presented_source_path_is_technical_only(tmp_path):
    context, _, _ = qualification_context(tmp_path)

    presented = CampaignReferenceQualificationPresenter().present(context)

    assert "source_path" not in presented.to_dict()
