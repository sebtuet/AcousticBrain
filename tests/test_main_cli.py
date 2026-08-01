from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import main as acousticbrain_main
from acousticbrain.application import ExploratoryFeasibilityRegistry
from acousticbrain.models import (
    ExperimentDescriptor,
    ExperimentState,
    ExperimentType,
    ExploratoryProposalInput,
)
from acousticbrain.persistence import ExploratoryFeasibilityJsonRepository
from acousticbrain.report import (
    ExperimentDiscoveryPresenter,
    PresentedAnalysisReadiness,
    PresentedAnalysisReadinessReport,
    PresentedAssessmentSummary,
    Report,
)


class RecordingBrain:
    def __init__(self, report=None):
        self.report = report or object()
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        return self.report


class RecordingReporter:
    def __init__(self):
        self.reports = []

    def print(self, report):
        self.reports.append(report)


class PlanReferenceRoutingBrain:
    EXISTING_PLAN_ID = "EVIDENCE_ACQUISITION_PLAN_EXISTING"

    def __init__(self, source_plan_id):
        self.source_plan_id = source_plan_id
        self.calls = []

    def analyze(self, **arguments):
        self.calls.append(arguments)
        context = SimpleNamespace(
            experiment_descriptors=(
                ExperimentDescriptor(
                    experiment_id="baseline",
                    directory="/measurements/baseline",
                    experiment_type=ExperimentType.BASELINE,
                    available_files=(),
                    available_channels=(),
                    wav_files=(),
                    txt_files=(),
                    mdat_file=None,
                    manifest_present=True,
                    content_hash="a" * 64,
                    timestamp="2026-07-28T18:43:41",
                    imported_at="2026-07-28T18:43:41",
                    state=ExperimentState.READY,
                    source_evidence_acquisition_plan_id=self.source_plan_id,
                ),
            ),
        )
        if arguments.get("synthesize_evidence_acquisition"):
            context.evidence_acquisition_plan_synthesis = SimpleNamespace(
                plans=(SimpleNamespace(plan_id=self.EXISTING_PLAN_ID),)
            )
        report = Report(project_name="routing")
        report.experiments_discovered = ExperimentDiscoveryPresenter().present(
            context
        )
        return report


def test_parser_uses_historical_measurements_default():
    arguments = acousticbrain_main.create_parser().parse_args([])

    assert arguments.measurements_root == Path("measurements")


def test_parser_accepts_full_assessment():
    arguments = acousticbrain_main.create_parser().parse_args(["--full-assessment"])

    assert arguments.full_assessment is True


def test_parser_accepts_full_assessment_output():
    arguments = acousticbrain_main.create_parser().parse_args(
        ["--full-assessment", "--full-assessment-output", "assessment.txt"]
    )

    assert arguments.full_assessment_output == Path("assessment.txt")


def test_parser_accepts_analysis_readiness():
    arguments = acousticbrain_main.create_parser().parse_args(
        ["--analysis-readiness"]
    )

    assert arguments.analysis_readiness is True


def test_parser_accepts_assessment_summary():
    arguments = acousticbrain_main.create_parser().parse_args(
        ["--assessment-summary"]
    )

    assert arguments.assessment_summary is True


def test_parser_accepts_exploratory_mode():
    arguments = acousticbrain_main.create_parser().parse_args(["--exploratory"])

    assert arguments.exploratory is True


def test_exploratory_cli_loads_explicit_input_and_decisions(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text("{}", encoding="utf-8")
    decisions_path = tmp_path / "decisions.json"
    expected_input = ExploratoryProposalInput(
        candidate_id="candidate.one", reference_experiment_id="baseline",
        reference_content_fingerprint="hash",
        reference_configuration=(("room", "reference"),),
        action_parameters=(("target", "LEFT_FIRST_REFLECTION_AREA"),),
        return_action="RESTORE_REFERENCE", feasibility_question="Can you?",
        limitations=("CAUSALITY_NOT_ESTABLISHED",),
        field_provenance=(("target", "USER_DECLARATION"),),
    )
    loader = SimpleNamespace(load=lambda path: expected_input)
    repository = ExploratoryFeasibilityJsonRepository()
    repository.save(ExploratoryFeasibilityRegistry(), decisions_path)
    brain = RecordingBrain()

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--exploratory",
         "--exploratory-proposal", str(proposal_path),
         "--exploratory-decisions", str(decisions_path)],
        brain=brain, reporter=RecordingReporter(),
        exploratory_proposal_loader=loader,
        exploratory_decision_repository=repository,
    )

    assert result == 0
    assert brain.calls[0]["analyze_exploratory"] is True
    assert brain.calls[0]["exploratory_proposal_inputs"] == (expected_input,)
    assert brain.calls[0]["exploratory_feasibility_decisions"].decisions == ()


def test_record_feasibility_is_a_separate_command_and_does_not_analyze(tmp_path):
    path = tmp_path / "decisions.json"
    brain = RecordingBrain()

    result = acousticbrain_main.main([
        "--record-exploratory-feasibility", "FEASIBLE",
        "--exploratory-decisions", str(path),
        "--exploratory-proposal-id", "proposal.one",
        "--exploratory-reference-scope-id", "reference.one",
        "--exploratory-note", "Possible this weekend",
    ], brain=brain)

    assert result == 0
    assert brain.calls == []
    decision = ExploratoryFeasibilityJsonRepository().load(path).decisions[0]
    assert decision.answer.value == "FEASIBLE"
    assert decision.user_note == "Possible this weekend"


@pytest.mark.parametrize(
    "value",
    (
        "relative/campaign",
        "/tmp/absolute-campaign",
        "campaign with spaces",
    ),
)
def test_parser_preserves_explicit_path(value):
    arguments = acousticbrain_main.create_parser().parse_args(
        ["--measurements-root", value]
    )

    assert arguments.measurements_root == Path(value)


def test_validation_rejects_missing_path(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="Measurements root does not exist"):
        acousticbrain_main.validate_measurements_root(missing)


def test_validation_rejects_file(tmp_path):
    file_path = tmp_path / "campaign.txt"
    file_path.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ValueError, match="Measurements root is not a directory"):
        acousticbrain_main.validate_measurements_root(file_path)


@pytest.mark.parametrize(
    ("path_kind", "message"),
    (
        ("missing", "Measurements root does not exist"),
        ("file", "Measurements root is not a directory"),
    ),
)
def test_main_returns_nonzero_for_invalid_root(
    tmp_path, capsys, path_kind, message
):
    path = tmp_path / "invalid campaign"
    if path_kind == "file":
        path.write_text("not a directory", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(["--measurements-root", str(path)])

    assert error.value.code == 2
    assert message in capsys.readouterr().err


def test_main_passes_exact_relative_path_without_changing_cwd(tmp_path, monkeypatch):
    campaign = tmp_path / "campaign with spaces"
    campaign.mkdir()
    relative = Path("campaign with spaces")
    monkeypatch.chdir(tmp_path)
    original_cwd = Path.cwd()
    brain = RecordingBrain()
    reporter = RecordingReporter()

    result = acousticbrain_main.main(
        ["--measurements-root", str(relative)],
        brain=brain,
        reporter=reporter,
    )

    assert result == 0
    assert Path.cwd() == original_cwd
    assert brain.calls == [
        {
            "measurement_root": relative,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_evidence_acquisition": True,
        }
    ]
    assert reporter.reports == [brain.report]


@pytest.mark.parametrize(
    ("source_plan_id", "expected_source", "expected_status"),
    (
        (None, "none", "PLAN_NOT_REFERENCED"),
        (
            PlanReferenceRoutingBrain.EXISTING_PLAN_ID,
            PlanReferenceRoutingBrain.EXISTING_PLAN_ID,
            "PLAN_REFERENCE_RESOLVED",
        ),
        (
            "EVIDENCE_ACQUISITION_PLAN_UNKNOWN",
            "EVIDENCE_ACQUISITION_PLAN_UNKNOWN",
            "PLAN_REFERENCE_UNKNOWN",
        ),
    ),
)
def test_standard_cli_resolves_explicit_plan_references_without_printing_plan_report(
    tmp_path,
    capsys,
    source_plan_id,
    expected_source,
    expected_status,
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = PlanReferenceRoutingBrain(source_plan_id)

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=brain,
    )

    assert result == 0
    assert brain.calls[0]["synthesize_evidence_acquisition"] is True
    output = capsys.readouterr().out
    assert f"Source evidence acquisition plan : {expected_source}" in output
    assert f"Plan reference status : {expected_status}" in output
    assert "NEXT RECOMMENDED EXPERIMENT" not in output


@pytest.mark.parametrize(
    ("case", "expected_status"),
    (
        ("criteria_absent", "PLAN_RESULT_CRITERIA_NOT_EVALUABLE"),
        ("results_absent", "PLAN_RESULT_INSUFFICIENT_EVIDENCE"),
        ("compatible", "PLAN_RESULT_COMPATIBLE"),
        ("incompatible", "PLAN_RESULT_INCOMPATIBLE"),
        ("mixed", "PLAN_RESULT_MIXED"),
    ),
)
def test_standard_cli_exposes_channel_isolation_result_evaluation_states(
    tmp_path,
    capsys,
    case,
    expected_status,
):
    from acousticbrain.models import ChannelIsolationResultDeclaration
    from test_channel_isolation_plan_result import criterion, plan, result

    criteria = ()
    results = ()
    if case != "criteria_absent":
        criteria = (criterion("A", "result_a"),)
    if case == "compatible":
        results = (result("result_a", "0"),)
    elif case == "incompatible":
        results = (result("result_a", "1"),)
    elif case == "mixed":
        criteria = (
            criterion("A", "result_a"),
            criterion("B", "result_b"),
        )
        results = (
            result("result_a", "0"),
            result("result_b", "1"),
        )
    elif case == "criteria_absent":
        results = (result("result_a", "0"),)
    source_plan = plan(*criteria)
    descriptor = ExperimentDescriptor(
        experiment_id="baseline",
        directory="/measurements/baseline",
        experiment_type=ExperimentType.BASELINE,
        available_files=(),
        available_channels=(),
        wav_files=(),
        txt_files=(),
        mdat_file=None,
        manifest_present=True,
        content_hash="a" * 64,
        timestamp="2026-07-28T18:43:41",
        imported_at="2026-07-28T18:43:41",
        state=ExperimentState.READY,
        source_evidence_acquisition_plan_id=source_plan.plan_id,
        channel_isolation_result_declaration=(
            ChannelIsolationResultDeclaration(results)
            if results
            else None
        ),
    )
    context = SimpleNamespace(
        experiment_descriptors=(descriptor,),
        evidence_acquisition_plan_synthesis=SimpleNamespace(
            plans=(source_plan,)
        ),
    )
    report = Report(project_name="routing")
    report.experiments_discovered = ExperimentDiscoveryPresenter().present(context)
    campaign = tmp_path / "campaign"
    campaign.mkdir()

    result_code = acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=RecordingBrain(report),
    )

    assert result_code == 0
    output = capsys.readouterr().out
    assert f"Plan result evaluation status : {expected_status}" in output
    assert "NEXT RECOMMENDED EXPERIMENT" not in output


def test_main_passes_exact_absolute_path(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign)],
        brain=brain,
        reporter=RecordingReporter(),
    )

    assert brain.calls[0]["measurement_root"] == campaign


def test_full_assessment_activates_only_evidence_acquisition_synthesis(tmp_path):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()

    acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--full-assessment"],
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


def test_full_assessment_output_requires_full_assessment(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root",
                str(campaign),
                "--full-assessment-output",
                str(tmp_path / "assessment.txt"),
            ],
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert "--full-assessment-output requires --full-assessment." in (
        capsys.readouterr().err
    )


def test_full_assessment_output_rejects_missing_parent(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    output = tmp_path / "missing" / "assessment.txt"

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root",
                str(campaign),
                "--full-assessment",
                "--full-assessment-output",
                str(output),
            ],
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert "Full assessment output parent does not exist" in capsys.readouterr().err
    assert not output.exists()


def test_full_assessment_output_rejects_parent_file(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    parent = tmp_path / "not-a-directory"
    parent.write_text("content", encoding="utf-8")
    output = parent / "assessment.txt"

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root",
                str(campaign),
                "--full-assessment",
                "--full-assessment-output",
                str(output),
            ],
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert "Full assessment output parent is not a directory" in (
        capsys.readouterr().err
    )
    assert not output.exists()


def test_full_assessment_output_rejects_existing_path(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    output = tmp_path / "assessment.txt"
    output.write_text("preserve", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            [
                "--measurements-root",
                str(campaign),
                "--full-assessment",
                "--full-assessment-output",
                str(output),
            ],
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert "Full assessment output already exists" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == "preserve"


@pytest.mark.parametrize(
    "option",
    (
        "--observations",
        "--reasoning",
        "--actions",
        "--weighting",
        "--evidence-acquisition",
        "--advisor",
    ),
)
def test_full_assessment_rejects_each_incompatible_option(
    tmp_path, capsys, option
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            ["--measurements-root", str(campaign), "--full-assessment", option],
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert f"--full-assessment cannot be combined with {option}." in (
        capsys.readouterr().err
    )


@pytest.mark.parametrize(
    "option",
    (
        "--observations",
        "--reasoning",
        "--actions",
        "--weighting",
        "--evidence-acquisition",
        "--full-assessment",
        "--full-assessment-output",
        "--advisor",
    ),
)
def test_analysis_readiness_rejects_each_incompatible_option(
    tmp_path, capsys, option
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    arguments = [
        "--measurements-root",
        str(campaign),
        "--analysis-readiness",
        option,
    ]
    if option == "--full-assessment-output":
        arguments.append(str(tmp_path / "assessment.txt"))

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            arguments,
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert f"--analysis-readiness cannot be combined with {option}." in (
        capsys.readouterr().err
    )


def test_analysis_readiness_runs_pipeline_once_without_advisor_or_network(
    tmp_path, monkeypatch
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()
    reporter = RecordingReporter()

    def unexpected_call(*args, **kwargs):
        raise AssertionError("Advisor or network access was initialized")

    monkeypatch.setattr(acousticbrain_main, "create_advisor_provider", unexpected_call)
    monkeypatch.setattr("socket.create_connection", unexpected_call)

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--analysis-readiness"],
        brain=brain,
        reporter=reporter,
    )

    assert result == 0
    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
        }
    ]
    assert reporter.reports == [brain.report]


def test_analysis_readiness_returns_zero_with_blocked_family(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    report = Report(project_name="fixture")
    report.analysis_readiness = PresentedAnalysisReadinessReport(
        analyses=(
            PresentedAnalysisReadiness(
                family="CLARITY",
                status="BLOCKED",
                blocking_issue_codes=("INVALID_DIRECT_PEAK",),
            ),
        )
    )

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--analysis-readiness"],
        brain=RecordingBrain(report),
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "Status: BLOCKED" in output
    assert str(campaign) not in output


def test_analysis_readiness_returns_zero_without_readiness(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--analysis-readiness"],
        brain=RecordingBrain(Report(project_name="fixture")),
    )

    assert result == 0
    assert (
        "No technical analysis readiness information is available."
        in capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "option",
    (
        "--observations",
        "--reasoning",
        "--actions",
        "--weighting",
        "--evidence-acquisition",
        "--analysis-readiness",
        "--full-assessment",
        "--full-assessment-output",
        "--advisor",
    ),
)
def test_assessment_summary_rejects_each_incompatible_option(
    tmp_path, capsys, option
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    arguments = [
        "--measurements-root",
        str(campaign),
        "--assessment-summary",
        option,
    ]
    if option == "--full-assessment-output":
        arguments.append(str(tmp_path / "assessment.txt"))

    with pytest.raises(SystemExit) as error:
        acousticbrain_main.main(
            arguments,
            brain=RecordingBrain(),
            reporter=RecordingReporter(),
        )

    assert error.value.code == 2
    assert f"--assessment-summary cannot be combined with {option}." in (
        capsys.readouterr().err
    )


def test_assessment_summary_runs_pipeline_once_without_advisor_network_or_export(
    tmp_path, monkeypatch
):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    brain = RecordingBrain()
    reporter = RecordingReporter()

    def unexpected_call(*args, **kwargs):
        raise AssertionError("Advisor, network, or export access was initialized")

    monkeypatch.setattr(acousticbrain_main, "create_advisor_provider", unexpected_call)
    monkeypatch.setattr(acousticbrain_main, "FullAssessmentTextExporter", unexpected_call)
    monkeypatch.setattr("socket.create_connection", unexpected_call)

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--assessment-summary"],
        brain=brain,
        reporter=reporter,
    )

    assert result == 0
    assert brain.calls == [
        {
            "measurement_root": campaign,
            "compare_experiments": True,
            "analyze_causal_discrimination": True,
            "synthesize_evidence_acquisition": True,
        }
    ]
    assert reporter.reports == [brain.report]


def test_assessment_summary_returns_zero_with_empty_report(tmp_path, capsys):
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    report = Report(project_name="fixture")
    report.assessment_summary = PresentedAssessmentSummary(
        experiments=(),
        readiness_statuses=(),
        findings=(),
        applicable_actions=(),
        blocked_actions=(),
        recommended_experiments=(),
    )

    result = acousticbrain_main.main(
        ["--measurements-root", str(campaign), "--assessment-summary"],
        brain=RecordingBrain(report),
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "No assessment findings are available." in output
    assert str(campaign) not in output


def test_default_and_explicit_historical_path_are_invariant(tmp_path, monkeypatch):
    (tmp_path / "measurements").mkdir()
    monkeypatch.chdir(tmp_path)
    default_brain = RecordingBrain(report="same-report")
    explicit_brain = RecordingBrain(report="same-report")

    acousticbrain_main.main(
        [], brain=default_brain, reporter=RecordingReporter()
    )
    acousticbrain_main.main(
        ["--measurements-root", "measurements"],
        brain=explicit_brain,
        reporter=RecordingReporter(),
    )

    assert default_brain.calls == explicit_brain.calls


def test_cli_reports_invalid_path_without_traceback(tmp_path):
    missing = tmp_path / "missing campaign"

    result = subprocess.run(
        [
            sys.executable,
            str(Path(acousticbrain_main.__file__).resolve()),
            "--measurements-root",
            str(missing),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert f"Measurements root does not exist: {missing}" in result.stderr
    assert "Traceback" not in result.stderr
