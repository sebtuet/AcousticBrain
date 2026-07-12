from acousticbrain.analysis import GlobalSynthesizer, RecommendationEngine
from acousticbrain.diagnostics import MeasurementQualityDiagnostic
from acousticbrain.models import (
    AnalysisReadiness,
    GlobalDomainKind,
    ImpulseChannel,
    MeasurementAnalysisFamily,
    MeasurementChannelQuality,
    MeasurementQualityAnalysis,
    MeasurementQualityIssue,
    MeasurementQualityIssueCode,
    MeasurementQualityScope,
    MeasurementReadinessAnalysis,
    MeasurementReadinessStatus,
    ModalDensityAnalysis,
)


def clipping_issue():
    return MeasurementQualityIssue(
        code=MeasurementQualityIssueCode.CLIPPING_DETECTED,
        scope=MeasurementQualityScope.CHANNEL,
        channel=ImpulseChannel.LEFT,
        observed_metrics={"clipped_sample_count": 4},
        applied_thresholds={"clipping_level": 0.999},
        confidence=95.0,
        source_ids=("left",),
    )


def analyses():
    issue = clipping_issue()
    quality = MeasurementQualityAnalysis(
        channel_qualities=(
            MeasurementChannelQuality(
                channel=ImpulseChannel.LEFT,
                issues=(issue,),
                confidence=90.0,
                source_id="left",
            ),
        ),
        confidence=90.0,
        source_analyses=("MeasurementChannelQuality",),
    )
    readiness = MeasurementReadinessAnalysis(
        analyses=(
            AnalysisReadiness(
                family=MeasurementAnalysisFamily.RT60,
                status=MeasurementReadinessStatus.BLOCKED,
                blocking_issues=(issue,),
                required_channels=(ImpulseChannel.LEFT,),
                confidence=90.0,
                applied_rule_codes=("RT60_VALID_CHANNEL",),
            ),
        ),
        confidence=90.0,
    )
    return quality, readiness


def test_measurement_quality_domain_is_visible_but_not_acoustic():
    quality, _ = analyses()
    result = GlobalSynthesizer().synthesize(
        modal_density=ModalDensityAnalysis(score=70.0, confidence=80.0),
        measurement_quality=quality,
    )

    domain = result.domains[-1]
    assert domain.kind is GlobalDomainKind.MEASUREMENT_QUALITY
    assert not domain.contributes_to_acoustic_score
    assert result.score == 70.0
    assert result.priority_domains == ("MODAL_DENSITY",)


def test_blocked_readiness_creates_retake_action_not_acoustic_penalty():
    quality, readiness = analyses()
    result = RecommendationEngine().analyze(
        measurement_quality=quality,
        measurement_readiness=readiness,
    )

    recommendation = result.recommendations[0]
    assert recommendation.code == "RETAKE_CLIPPED_MEASUREMENT"
    assert recommendation.parameters["issue_count"] == 1
    assert recommendation.parameters["blocked_family_count"] == 1


def test_measurement_diagnostic_has_no_acoustic_score():
    quality, readiness = analyses()
    context = type(
        "Context",
        (),
        {
            "measurement_quality_analysis": quality,
            "measurement_readiness_analysis": readiness,
        },
    )()

    diagnostic = MeasurementQualityDiagnostic().analyze(context)

    assert diagnostic.score is None
    assert diagnostic.severity == "HIGH"
    assert "RT60_BLOCKED" in diagnostic.causes
