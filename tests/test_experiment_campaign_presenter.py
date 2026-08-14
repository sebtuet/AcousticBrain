from pathlib import Path
from types import SimpleNamespace

from acousticbrain.models import (
    ExperimentCampaignAnalysis,
    ExperimentCampaignBranchResult,
    ExperimentCampaignMeasurement,
    ExperimentCampaignMetric,
    ExperimentCampaignStatus,
    ExperimentCampaignTrace,
)
from acousticbrain.report import ConsoleReporter, ExperimentCampaignPresenter, Report


ROOT = Path(__file__).resolve().parents[1]


def analysis():
    return ExperimentCampaignAnalysis(
        campaign_code="VERIFY_MODAL_BASS_PERSISTENCE",
        protocol_id="protocol.verify_modal_bass_persistence.v1",
        hypothesis_code="MODAL_BASS_PERSISTENCE",
        objective_code="DETERMINE_BASS_DECAY_LISTENING_POSITION_DEPENDENCE",
        status=ExperimentCampaignStatus.PARTIALLY_RESOLVED,
        reference_experiment_id="exp-003",
        measurements=(
            ExperimentCampaignMeasurement("exp-003", "REFERENCE", 0.0, "READY"),
            ExperimentCampaignMeasurement("exp-004", "BACKWARD", -0.3, "READY"),
            ExperimentCampaignMeasurement("exp-005", "FORWARD", 0.3, "READY"),
        ),
        branch_results=(
            ExperimentCampaignBranchResult(
                "exp-004", "BACKWARD", -0.3, "UNCHANGED",
                ("BASS_DECAY_STABLE_AT_TARGET_BANDS",), 0.790, 0.790,
            ),
            ExperimentCampaignBranchResult(
                "exp-005", "FORWARD", 0.3, "IMPROVED",
                (
                    "BASS_DECAY_REDUCED_AT_TARGET_BANDS",
                    "BASS_DECAY_VARIES_BY_LISTENING_POSITION",
                    "LOCAL_POSITION_EFFECT_SUPPORTED",
                ),
                0.790, 0.636,
            ),
        ),
        result_codes=(
            "BASS_DECAY_VARIES_BY_LISTENING_POSITION",
            "LOCAL_POSITION_EFFECT_SUPPORTED",
            "GLOBAL_MODAL_COMPONENT_NOT_DISCRIMINATED",
        ),
        unresolved_discrimination_codes=(
            "LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE",
        ),
        metrics=(ExperimentCampaignMetric(
            code="MAXIMUM_BASS_DECAY_REDUCTION",
            reference_value=0.790,
            best_value=0.636,
            improvement=0.154,
            improvement_percent=19.5,
            unit="SECONDS",
            best_experiment_id="exp-005",
        ),),
        next_discrimination_code=(
            "CONTROLLED_SOURCE_VARIATION_WITH_FIXED_LISTENER"
        ),
        trace=ExperimentCampaignTrace(
            trace_id="campaign-trace:verify-modal-bass-persistence",
            experiment_ids=("exp-003", "exp-004", "exp-005"),
            comparison_result_ids=(
                "comparison:local:exp-003:exp-004",
                "comparison:local:exp-003:exp-005",
            ),
            observation_codes=(
                "BASS_DECAY_VARIES_BY_LISTENING_POSITION",
                "LOCAL_POSITION_EFFECT_SUPPORTED",
            ),
            applied_rule_codes=("CAMPAIGN_AGGREGATE_EXISTING_COMPARISONS_ONLY",),
        ),
        detailed_traceability=False,
    )


def test_campaign_presenter_is_a_pure_projection():
    source = analysis()
    context = SimpleNamespace(experiment_campaign_analyses=(source,))

    first = ExperimentCampaignPresenter().present(context)
    second = ExperimentCampaignPresenter().present(context)

    assert first == second
    assert first[0].status == "PARTIALLY_RESOLVED"
    assert first[0].metrics[0].best_experiment_id == "exp-005"
    assert first[0].conclusions[-1].established is False
    assert first[0].next_discrimination_label == (
        "variation contrôlée de la position de la source, microphone fixe"
    )


def test_campaign_report_matches_golden(capsys):
    context = SimpleNamespace(experiment_campaign_analyses=(analysis(),))
    report = Report(project_name="campaign-fixture")
    report.experiment_campaigns = ExperimentCampaignPresenter().present(context)

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/experiment_campaign_report.txt").read_text()
    assert capsys.readouterr().out == expected
