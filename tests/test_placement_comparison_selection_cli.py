from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.report import Report


class _Brain:
    def __init__(self, report):
        self.report = report
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return self.report


def report():
    value = Report(project_name="selection-cli")
    value.experiment_comparison = SimpleNamespace(
        local_comparisons=(SimpleNamespace(
            trace_id="trace:comparison:local:position-a:position-b",
            before_experiment_id="position-a",
            after_experiment_id="position-b",
            comparison_type="LOCAL",
            eligibility="COMPARABLE",
        ),),
        cumulative_comparisons=(),
    )
    return value


def test_main_selects_one_exact_placement_comparison_read_only(capsys, tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = _Brain(report())

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
    assert brain.calls == [{
        "measurement_root": campaign,
        "compare_experiments": True,
        "analyze_causal_discrimination": True,
    }]


def test_main_rejects_unknown_placement_comparison(capsys, tmp_path):
    campaign = tmp_path / "measurements"
    campaign.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root", str(campaign),
                "--placement-comparison", "trace:missing",
            ],
            brain=_Brain(report()),
        )

    assert error.value.code == 2
    assert "COMPARISON_UNKNOWN: trace:missing" in capsys.readouterr().err


def test_main_rejects_placement_comparison_mode_combinations_before_analysis(
    tmp_path,
):
    campaign = tmp_path / "measurements"
    campaign.mkdir()
    brain = _Brain(report())

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
