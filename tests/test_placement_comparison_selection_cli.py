from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.models import ComparisonEligibilityStatus
from acousticbrain.report import Report


class _Brain:
    def __init__(self, report, context):
        self.report = report
        self.context = context
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return (
            (self.report, self.context)
            if arguments.get("return_context")
            else self.report
        )


def report_and_context():
    trace_id = "trace:comparison:local:position-a:position-b"
    value = Report(project_name="selection-cli")
    value.experiment_comparison = SimpleNamespace(
        local_comparisons=(SimpleNamespace(
            trace_id=trace_id,
            before_experiment_id="position-a",
            after_experiment_id="position-b",
            comparison_type="LOCAL",
            eligibility="COMPARABLE",
        ),),
        cumulative_comparisons=(),
    )
    raw = SimpleNamespace(
        trace=SimpleNamespace(trace_id=trace_id),
        before_experiment_id="position-a",
        after_experiment_id="position-b",
        eligibility=ComparisonEligibilityStatus.COMPARABLE,
        ineligibility_reasons=(),
    )
    return value, SimpleNamespace(
        experiment_comparison_analysis=SimpleNamespace(
            sequence=SimpleNamespace(
                local_comparisons=(raw,), cumulative_comparisons=(),
            )
        )
    )


def test_main_selects_one_exact_placement_comparison_read_only(capsys, tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = _Brain(*report_and_context())

    result = acousticbrain_main.main(
        [
            "--measurements-root", str(campaign),
            "--placement-comparison",
            "trace:comparison:local:position-a:position-b",
        ],
        brain=brain,
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "COMPARAISON SÉLECTIONNÉE" in output
    assert "Référence : position-a" in output
    assert "Cible : position-b" in output
    assert "BETTER" not in output
    assert len(brain.calls) == 1
    assert brain.calls[0]["measurement_root"] == campaign
    assert brain.calls[0]["compare_experiments"] is True
    assert brain.calls[0]["analyze_causal_discrimination"] is True
    assert brain.calls[0]["return_context"] is True
    assert brain.calls[0]["channel_isolation_repeatability_qualifications"] == ()


def test_main_rejects_unknown_placement_comparison(capsys, tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root", str(campaign),
                "--placement-comparison", "trace:missing",
            ],
            brain=_Brain(*report_and_context()),
        )

    assert error.value.code == 2
    assert "COMPARISON_UNKNOWN: trace:missing" in capsys.readouterr().err


def test_main_rejects_placement_comparison_mode_combinations_before_analysis(
    tmp_path,
):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = _Brain(*report_and_context())

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root", str(campaign),
                "--placement-comparison", "trace:comparison:local:position-a:position-b",
                "--actions",
            ],
            brain=brain,
        )

    assert error.value.code == 2
    assert brain.calls == []
