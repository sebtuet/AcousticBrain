from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.analysis.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanBuilder,
)
from acousticbrain.brain import AcousticBrain
from acousticbrain.brain.stages.acoustic_hypothesis_experiment_generation import (
    AcousticHypothesisExperimentGenerationStage,
)
from acousticbrain.brain.stages.listening_position_campaign_plan import (
    ListeningPositionCampaignPlanStage,
)
from acousticbrain.models import (
    ListeningPositionCampaignInstanceStatus,
    ListeningPositionCampaignPlanStatus,
    MODAL_LISTENING_POSITION_COMPARABILITY_RULE,
    MODAL_LISTENING_POSITION_CONTROLLED_VARIABLES,
    MODAL_LISTENING_POSITION_PROTOCOL_ID,
)
from acousticbrain.persistence import ListeningPositionCampaignInstanceJsonLoader
from acousticbrain.report import (
    AcousticHypothesisExperimentGenerationPresenter,
    ConsoleReporter,
    ListeningPositionCampaignInstancePresenter,
    ListeningPositionCampaignPlanPresenter,
    Report,
)
from test_acoustic_hypothesis_experiment_generation import modal_context
from test_golden_report import reference_project
from test_listening_position_campaign_plan import (
    comparable_sequence,
    structured_reference,
)
from test_main_cli import RecordingBrain, RecordingReporter


MEASUREMENTS = ["LEFT", "RIGHT", "STEREO"]
CONTROLS = list(MODAL_LISTENING_POSITION_CONTROLLED_VARIABLES)


def valid_payload(*, reference="exp-007"):
    def position(
        code,
        role,
        order,
        longitudinal,
        parent,
        position_reference,
        modified,
    ):
        return {
            "position_code": code,
            "position_role": role,
            "order_index": order,
            "longitudinal_offset_m": longitudinal,
            "lateral_offset_m": None,
            "vertical_offset_m": None,
            "parent_position_code": parent,
            "reference_position_code": position_reference,
            "reference_experiment_id": reference,
            "modified_variables": modified,
            "controlled_variables": list(CONTROLS),
            "required_measurements": list(MEASUREMENTS),
        }

    return {
        "schema_version": 1,
        "instance_id": "listening-position-campaign-test",
        "protocol_id": MODAL_LISTENING_POSITION_PROTOCOL_ID,
        "protocol_version": 1,
        "reference_experiment_id": reference,
        "comparability_rule": MODAL_LISTENING_POSITION_COMPARABILITY_RULE,
        "controlled_variables": list(CONTROLS),
        "required_measurements": list(MEASUREMENTS),
        "declaration_source": "USER_JSON_TEST",
        "declaration_version": 1,
        "notes": None,
        "positions": [
            position("REFERENCE", "REFERENCE", 1, 0.0, None, "REFERENCE", []),
            position(
                "FORWARD", "FORWARD", 2, 0.125,
                "REFERENCE", "REFERENCE", ["LISTENING_POSITION"],
            ),
            position(
                "BACKWARD", "BACKWARD", 3, -0.075,
                "REFERENCE", "REFERENCE", ["LISTENING_POSITION"],
            ),
        ],
    }


def write_payload(path, payload=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload or valid_payload(), indent=2), encoding="utf-8"
    )
    return path


def load(path):
    return ListeningPositionCampaignInstanceJsonLoader().load(path)


def planned_context(analysis, *, reference=True):
    value = modal_context(with_sampling_geometry=False)
    value.listening_position_campaign_instance_analysis = analysis
    if analysis.status is ListeningPositionCampaignInstanceStatus.VALID:
        protocol = analysis.instance.to_sampling_protocol()
        value.listening_position_sampling_protocol = protocol
    AcousticHypothesisExperimentGenerationStage().run(value)
    if reference and analysis.instance is not None:
        value.experiment_descriptors = (
            structured_reference(
                value.listening_position_sampling_protocol,
                analysis.instance.reference_experiment_id,
            ),
        )
        value.experiment_comparison_analysis = comparable_sequence(
            analysis.instance.reference_experiment_id
        )
    else:
        value.experiment_descriptors = ()
        value.experiment_comparison_analysis = None
    ListeningPositionCampaignPlanStage().run(value)
    return value


def test_valid_json_file_loads_exact_declarative_instance(tmp_path):
    source = write_payload(tmp_path / "instance.json")

    analysis = load(source)

    assert analysis.status is ListeningPositionCampaignInstanceStatus.VALID
    assert analysis.instance.instance_id == "listening-position-campaign-test"
    assert analysis.instance.reference_experiment_id == "exp-007"
    assert analysis.source_path == str(source.resolve())


def test_absent_file_returns_structured_error(tmp_path):
    analysis = load(tmp_path / "missing.json")

    assert analysis.status is ListeningPositionCampaignInstanceStatus.INVALID
    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_SCHEMA_INVALID",)
    assert "does not exist" in analysis.validation_messages[0]


def test_invalid_json_returns_structured_error(tmp_path):
    source = tmp_path / "invalid.json"
    source.write_text("{invalid", encoding="utf-8")

    analysis = load(source)

    assert analysis.status is ListeningPositionCampaignInstanceStatus.INVALID
    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_SCHEMA_INVALID",)
    assert "Invalid campaign instance JSON" in analysis.validation_messages[0]


def test_unsupported_schema_is_rejected(tmp_path):
    payload = valid_payload()
    payload["schema_version"] = 2

    analysis = load(write_payload(tmp_path / "schema.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_SCHEMA_INVALID",)


def test_boolean_schema_version_is_not_accepted_as_integer_one(tmp_path):
    payload = valid_payload()
    payload["schema_version"] = True

    analysis = load(write_payload(tmp_path / "boolean-schema.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_SCHEMA_INVALID",)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("protocol_id", "protocol.unknown.v1"),
        ("protocol_version", 2),
    ),
)
def test_unknown_protocol_or_incompatible_version_is_rejected(
    tmp_path, field, value
):
    payload = valid_payload()
    payload[field] = value

    analysis = load(write_payload(tmp_path / f"{field}.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH",)


def test_duplicate_position_code_is_rejected(tmp_path):
    payload = valid_payload()
    payload["positions"][2]["position_code"] = "FORWARD"

    analysis = load(write_payload(tmp_path / "duplicate-code.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_POSITION_INVALID",)


def test_duplicate_order_is_rejected_without_reordering(tmp_path):
    payload = valid_payload()
    payload["positions"][2]["order_index"] = 2

    analysis = load(write_payload(tmp_path / "duplicate-order.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_POSITION_INVALID",)


@pytest.mark.parametrize(
    "mutation",
    ("unknown", "cycle"),
)
def test_unknown_or_cyclic_relation_is_rejected(tmp_path, mutation):
    payload = valid_payload()
    payload["positions"][1]["parent_position_code"] = (
        "MISSING" if mutation == "unknown" else "BACKWARD"
    )

    analysis = load(write_payload(tmp_path / f"relation-{mutation}.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_RELATION_INVALID",)


def test_missing_scientific_reference_is_rejected(tmp_path):
    payload = valid_payload()
    payload["reference_experiment_id"] = None
    for item in payload["positions"]:
        item["reference_experiment_id"] = None

    analysis = load(write_payload(tmp_path / "missing-reference.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_REFERENCE_INVALID",)


def test_declared_but_inadmissible_reference_is_not_substituted(tmp_path):
    analysis = load(write_payload(tmp_path / "instance.json"))
    value = planned_context(analysis, reference=False)

    plan = value.listening_position_campaign_plan

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.reference_experiment_id is None
    assert plan.source_instance_id == analysis.instance.instance_id
    assert plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


def test_requested_reference_is_not_replaced_by_another_admissible_one(tmp_path):
    analysis = load(write_payload(tmp_path / "instance.json"))
    value = modal_context(with_sampling_geometry=False)
    value.listening_position_campaign_instance_analysis = analysis
    protocol = analysis.instance.to_sampling_protocol()
    value.listening_position_sampling_protocol = protocol
    AcousticHypothesisExperimentGenerationStage().run(value)
    substitute = structured_reference(protocol, "exp-006")
    value.experiment_descriptors = (substitute,)
    value.experiment_comparison_analysis = SimpleNamespace(
        sequence=SimpleNamespace(
            chronology=("exp-006", "exp-007"),
            local_comparisons=(
                SimpleNamespace(
                    after_experiment_id="exp-006",
                    eligibility=comparable_sequence(
                        "exp-006"
                    ).sequence.local_comparisons[0].eligibility,
                ),
            ),
        )
    )

    plan = ListeningPositionCampaignPlanBuilder().build(value)
    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.reference_experiment_id is None
    assert plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


def test_admissible_requested_reference_without_qualification_stays_blocked(
    tmp_path,
):
    analysis = load(write_payload(tmp_path / "instance.json"))

    plan = planned_context(analysis).listening_position_campaign_plan

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.reference_experiment_id is None
    assert plan.blocking_reasons == (
        "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE",
    )


def test_offsets_and_none_values_are_preserved_without_transformation(tmp_path):
    analysis = load(write_payload(tmp_path / "instance.json"))
    instance = analysis.instance
    plan = planned_context(analysis).listening_position_campaign_plan

    assert tuple(item.longitudinal_offset_m for item in instance.positions) == (
        0.0,
        0.125,
        -0.075,
    )
    assert tuple(item.longitudinal_offset_m for item in plan.steps) == (
        0.0,
        0.125,
        -0.075,
    )
    assert all(item.lateral_offset_m is None for item in plan.steps)
    assert all(item.vertical_offset_m is None for item in plan.steps)


@pytest.mark.parametrize("missing", MEASUREMENTS)
def test_each_required_measurement_is_enforced(tmp_path, missing):
    payload = valid_payload()
    payload["required_measurements"].remove(missing)

    analysis = load(write_payload(tmp_path / f"missing-{missing}.json", payload))

    assert analysis.blocking_reasons == (
        "CAMPAIGN_INSTANCE_MEASUREMENTS_INCOMPLETE",
    )


@pytest.mark.parametrize("missing", MEASUREMENTS)
def test_each_position_requires_left_right_and_stereo(tmp_path, missing):
    payload = valid_payload()
    payload["positions"][1]["required_measurements"].remove(missing)

    analysis = load(
        write_payload(tmp_path / f"position-missing-{missing}.json", payload)
    )

    assert analysis.blocking_reasons == (
        "CAMPAIGN_INSTANCE_MEASUREMENTS_INCOMPLETE",
    )


def test_incompatible_controlled_variable_is_rejected(tmp_path):
    payload = valid_payload()
    payload["controlled_variables"] = payload["controlled_variables"][:-1]

    analysis = load(write_payload(tmp_path / "controls.json", payload))

    assert analysis.blocking_reasons == (
        "CAMPAIGN_INSTANCE_CONTROLLED_VARIABLES_INCOMPATIBLE",
    )


def test_incompatible_comparability_rule_is_rejected(tmp_path):
    payload = valid_payload()
    payload["comparability_rule"] = "UNDECLARED_RULE"

    analysis = load(write_payload(tmp_path / "comparability.json", payload))

    assert analysis.blocking_reasons == ("CAMPAIGN_INSTANCE_PROTOCOL_MISMATCH",)


def test_invalid_instance_produces_blocked_plan_with_specific_reason(tmp_path):
    payload = valid_payload()
    payload["positions"][1]["parent_position_code"] = "MISSING"
    analysis = load(write_payload(tmp_path / "invalid-instance.json", payload))

    plan = planned_context(analysis, reference=False).listening_position_campaign_plan

    assert plan.status is ListeningPositionCampaignPlanStatus.BLOCKED
    assert plan.blocking_reasons == ("CAMPAIGN_INSTANCE_RELATION_INVALID",)


def test_no_future_experiment_identity_is_invented(tmp_path):
    analysis = load(write_payload(tmp_path / "instance.json"))
    plan = planned_context(analysis).listening_position_campaign_plan

    assert all(item.step_id.startswith("campaign-step.") for item in plan.steps)
    assert "exp-008" not in repr(plan)
    assert "exp-009" not in repr(plan)


def test_loader_and_builder_write_nothing_change_no_cwd_and_preserve_source(tmp_path):
    source = write_payload(tmp_path / "instance with spaces.json")
    before_bytes = source.read_bytes()
    before_inventory = tuple(
        sorted((item.relative_to(tmp_path), item.stat().st_size) for item in tmp_path.rglob("*"))
    )
    before_cwd = Path.cwd()

    analysis = load(source)
    planned_context(analysis)

    after_inventory = tuple(
        sorted((item.relative_to(tmp_path), item.stat().st_size) for item in tmp_path.rglob("*"))
    )
    assert Path.cwd() == before_cwd
    assert source.read_bytes() == before_bytes
    assert after_inventory == before_inventory


@pytest.mark.parametrize("kind", ("relative", "absolute", "spaces"))
def test_cli_accepts_relative_absolute_and_space_paths(tmp_path, monkeypatch, kind):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    source = write_payload(tmp_path / "instance with spaces.json")
    monkeypatch.chdir(tmp_path)
    campaign_argument = Path("measurements") if kind == "relative" else campaign
    source_argument = (
        Path("instance with spaces.json") if kind in {"relative", "spaces"} else source
    )
    brain = RecordingBrain()

    result = acousticbrain_main.main(
        [
            "--measurements-root",
            str(campaign_argument),
            "--listening-position-campaign",
            str(source_argument),
        ],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert result == 0
    passed = brain.calls[0]["listening_position_campaign_instance_analysis"]
    assert passed.status is ListeningPositionCampaignInstanceStatus.VALID
    assert passed.source_path == str(source.resolve())


def test_cli_invalid_instance_is_clear_nonzero_and_has_no_traceback(tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    source = tmp_path / "invalid campaign.json"
    source.write_text("{invalid", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(Path(acousticbrain_main.__file__).resolve()),
            "--measurements-root",
            str(campaign),
            "--listening-position-campaign",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "CAMPAIGN_INSTANCE_SCHEMA_INVALID" in result.stderr
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
        }
    ]


def test_instance_preserves_scientific_and_historical_outputs(tmp_path):
    analysis = load(write_payload(tmp_path / "instance.json"))
    project = reference_project()
    baseline = AcousticBrain().analyze(project)
    enriched = AcousticBrain().analyze(
        project,
        listening_position_campaign_instance_analysis=analysis,
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


def test_valid_instance_report_without_qualification_is_blocked(tmp_path, capsys):
    analysis = load(write_payload(tmp_path / "instance.json"))
    value = planned_context(analysis)
    report = Report(project_name="instance-valid")
    report.acoustic_hypothesis_experiment_generation = (
        AcousticHypothesisExperimentGenerationPresenter().present(value)
    )
    report.listening_position_campaign_instance = (
        ListeningPositionCampaignInstancePresenter().present(value)
    )
    report.listening_position_campaign_plan = (
        ListeningPositionCampaignPlanPresenter().present(value)
    )

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "INSTANCE DE CAMPAGNE MULTI-POSITION" in output
    assert "Statut : VALID" in output
    assert "Référence demandée : exp-007" in output
    assert "PLAN DE CAMPAGNE MULTI-POSITION" in output
    assert "Statut : BLOCKED" in output
    assert "CAMPAIGN_REFERENCE_EXPERIMENT_UNAVAILABLE" in output
    presented = ListeningPositionCampaignInstancePresenter().present(value)
    assert "source_path" not in presented.to_dict()


def test_invalid_instance_report_is_readable(tmp_path, capsys):
    payload = valid_payload()
    payload["positions"][1]["parent_position_code"] = "MISSING"
    analysis = load(write_payload(tmp_path / "invalid.json", payload))
    value = planned_context(analysis, reference=False)
    report = Report(project_name="instance-invalid")
    report.acoustic_hypothesis_experiment_generation = (
        AcousticHypothesisExperimentGenerationPresenter().present(value)
    )
    report.listening_position_campaign_instance = (
        ListeningPositionCampaignInstancePresenter().present(value)
    )
    report.listening_position_campaign_plan = (
        ListeningPositionCampaignPlanPresenter().present(value)
    )

    ConsoleReporter().print(report)
    output = capsys.readouterr().out

    assert "Statut : INVALID" in output
    assert "CAMPAIGN_INSTANCE_RELATION_INVALID" in output
    assert "Statut : BLOCKED" in output
    assert "Expérience principale\nType : LISTENING_POSITION_MULTI_POINT" not in output
