from pathlib import Path

from acousticbrain.report import (
    ConsoleReporter,
    PresentedExperimentComparison,
    PresentedExperimentEvolution,
    Report,
)


ROOT = Path(__file__).resolve().parents[1]


def presented_evolution(comparison_type):
    return PresentedExperimentEvolution(
        before_experiment_id="baseline",
        after_experiment_id="exp-001",
        comparison_type=comparison_type,
        eligibility="COMPARABLE",
        ineligibility_reasons=(),
        source_protocol_id="protocol.repeat-pair",
        source_hypothesis_code="ASYMMETRIC_SPEAKER_ROOM_INTERACTION",
        experiment_parameters=(),
        outcome="STRONGER",
        acoustic_outcome="IMPROVED",
        experimental_result_labels=("un effet local est soutenu",),
        improved_fact_codes=("global.domain.spatial.score",),
        degraded_fact_codes=(),
        changed_fact_codes=(),
        unchanged_fact_codes=("global.domain.sbir.score",),
        unavailable_fact_codes=(),
        observation_labels=("l’asymétrie spatiale diminue",),
        counter_fact_codes=(),
        unresolved_discrimination_labels=(
            "la mesure ne distingue pas encore l’enceinte du côté de la pièce",
        ),
        technical_confidence=82.0,
        trace_id=f"trace:{comparison_type.lower()}:baseline:exp-001",
        trace_before_file_hash="baseline-hash",
        trace_after_file_hash="experiment-hash",
        trace_before_fact_codes=("global.domain.spatial.score",),
        trace_after_fact_codes=("global.domain.spatial.score",),
        trace_delta_fact_codes=("global.domain.spatial.score",),
        trace_observed_fact_codes=("SPATIAL_ASYMMETRY_DECREASED",),
        trace_unresolved_discrimination_codes=("LOUDSPEAKER_VS_ROOM_SIDE",),
    )


def test_comparison_report_matches_golden(capsys):
    report = Report(project_name="comparison-fixture")
    report.experiment_comparison = PresentedExperimentComparison(
        chronology=("baseline", "exp-001"),
        local_comparisons=(presented_evolution("LOCAL"),),
        cumulative_comparisons=(presented_evolution("CUMULATIVE"),),
        detailed_traceability=True,
    )

    ConsoleReporter().print(report)

    expected = (ROOT / "tests/golden/experiment_comparison_report.txt").read_text()
    assert capsys.readouterr().out == expected
