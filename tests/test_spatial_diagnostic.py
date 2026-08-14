from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import SpatialDiagnostic
from acousticbrain.models import (
    Measurement,
    SpatialAlignmentStatus,
    SpatialAnalysis,
    SpatialBalanceStatus,
    SpatialCoherenceStatus,
    SpatialCorrelation,
    SpatialCorrelationAnalysis,
    SpatialMeasurementType,
    SpatialStabilityStatus,
    SpeakerPairSpatialInterpretation,
)


def test_presents_only_existing_speaker_pair_interpretation_and_correlations():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.spatial_analysis = SpatialAnalysis(
        source_measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR
    )
    context.spatial_interpretation = SpeakerPairSpatialInterpretation(
        measurement_type=SpatialMeasurementType.SPEAKER_CHANNEL_PAIR,
        broadband_level_difference_db=2.0,
        broadband_time_difference_ms=0.3,
        broadband_cross_correlation=0.65,
        level_symmetry=SpatialBalanceStatus.ASYMMETRIC,
        relative_time_alignment=SpatialAlignmentStatus.OFFSET,
        pair_coherence=SpatialCoherenceStatus.WEAK,
        technical_center_stability=SpatialStabilityStatus.UNSTABLE,
        most_asymmetric_center_frequencies_hz=(500.0, 1000.0),
        confidence=88.0,
    )
    context.spatial_correlation_analysis = SpatialCorrelationAnalysis(
        correlations=[
            SpatialCorrelation(
                code="SPATIAL_LEVEL_STEREO_IMBALANCE",
                score=80.0,
                confidence=85.0,
            )
        ]
    )

    diagnostic = SpatialDiagnostic().analyze(context)

    assert diagnostic.severity == "HIGH"
    assert diagnostic.score == 50.0
    assert diagnostic.confidence == 88
    assert any("+2.00 dB" in item for item in diagnostic.observations)
    assert any("500 Hz, 1000 Hz" in item for item in diagnostic.observations)
    assert all("IACC" not in item for item in diagnostic.observations)


def test_handles_absent_spatial_pair_explicitly():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = SpatialDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.score is None
