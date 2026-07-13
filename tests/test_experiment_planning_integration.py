from acousticbrain.brain import AcousticBrain

from test_golden_report import reference_project


def test_pipeline_planning_is_opt_in_and_extends_traceability():
    project = reference_project()
    brain = AcousticBrain()

    historical = brain.analyze(project)
    planned = brain.analyze(project, plan_experiments=True)

    assert historical.experiment_planning is None
    assert historical.optimization_session is None
    assert planned.experiment_planning.status == "READY"
    assert planned.experiment_planning.recommended_candidate is not None
    planning_links = [
        item
        for item in planned.traceability_analysis.links
        if item.candidate_codes
    ]
    assert len(planning_links) == 4
    recommended = next(
        item for item in planning_links if item.recommended_candidate_codes
    )
    assert recommended.fact_codes
    assert recommended.evidence_codes
    assert recommended.hypothesis_codes
    assert recommended.protocol_codes
    assert recommended.candidate_codes
    assert recommended.ranking_codes == ("experiment_rank.1",)
    evidence_codes = {
        item.code
        for item in planned.traceability_analysis.evidence_references
    }
    assert set(recommended.evidence_codes).issubset(evidence_codes)
