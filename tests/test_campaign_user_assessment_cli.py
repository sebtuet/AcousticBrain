import hashlib
from pathlib import Path

import main as acousticbrain_main
import pytest


BASELINE = Path(__file__).resolve().parents[1] / "measurements"


def hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_parser_exposes_user_assessment():
    arguments = acousticbrain_main.create_parser().parse_args(["--user-assessment"])

    assert arguments.user_assessment is True


@pytest.mark.parametrize(
    "arguments, option",
    (
        (("--full-assessment",), "--full-assessment"),
        (("--assessment-summary",), "--assessment-summary"),
        (("--reasoning",), "--reasoning"),
        (("--actions",), "--actions"),
        (("--weighting",), "--weighting"),
        (("--guided-status",), "--guided-status"),
        (("--advisor", "--question", "explain"), "--advisor"),
        (("--declare-evidence-plan-experiment", "exp-008"), "--declare-evidence-plan-experiment"),
        (("--record-exploratory-feasibility", "FEASIBLE"), "--record-exploratory-feasibility"),
    ),
)
def test_user_assessment_rejects_incompatible_modes_before_analysis(
    tmp_path, capsys, arguments, option
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            ["--measurements-root", str(campaign), "--user-assessment", *arguments]
        )

    assert error.value.code == 2
    assert f"--user-assessment cannot be combined with {option}." in capsys.readouterr().err


def test_user_assessment_real_fixture_is_read_only_and_uses_no_advisor(
    monkeypatch, capsys
):
    before = hashes(BASELINE)

    def unexpected_advisor(*args, **kwargs):
        raise AssertionError("The user assessment must not initialize an advisor")

    monkeypatch.setattr(acousticbrain_main, "create_advisor_provider", unexpected_advisor)

    assert acousticbrain_main.main(
        ["--measurements-root", str(BASELINE), "--user-assessment"]
    ) == 0

    output = capsys.readouterr().out
    assert "USER ASSESSMENT" in output
    assert "Key findings" in output
    assert "Scientific boundaries" in output
    assert "Causality status: NOT_ESTABLISHED." in output
    assert before == hashes(BASELINE)
