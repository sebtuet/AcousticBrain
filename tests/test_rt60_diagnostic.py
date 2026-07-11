from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import RT60Diagnostic
from acousticbrain.models import (
    ImpulseChannel,
    Measurement,
    RT60Analysis,
    RT60BandAnalysis,
)


def analysis(rt60=0.35, homogeneity=90.0, confidence=88.0):
    band = RT60BandAnalysis(
        center_frequency_hz=1000.0,
        minimum_frequency_hz=890.0,
        maximum_frequency_hz=1122.0,
        rt60_seconds=rt60,
        decay_range_db=(-5.0, -35.0),
        fit_correlation=0.99,
        confidence=confidence,
        t30_seconds=rt60,
        selected_estimate="T30",
    )
    return RT60Analysis(
        available_channels=(ImpulseChannel.LEFT, ImpulseChannel.RIGHT),
        aggregate_bands=[band],
        common_center_frequencies_hz=(1000.0,),
        left_right_band_differences_seconds={1000.0: -0.04},
        interchannel_homogeneity=homogeneity,
        broadband_rt60_seconds=rt60,
        minimum_rt60_seconds=rt60 - 0.02,
        maximum_rt60_seconds=rt60 + 0.02,
        confidence=confidence,
    )


def test_interprets_rt60_aggregation_without_recalculating_bands():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.rt60_analysis = analysis()

    diagnostic = RT60Diagnostic().analyze(context)

    assert diagnostic.severity == "LOW"
    assert diagnostic.score == 97.0
    assert diagnostic.confidence == 88
    assert "0.350 s" in diagnostic.observations[2]
    assert "Écart G-D à 1000 Hz : -0.040 s." in diagnostic.observations
    assert "maîtrisées" in diagnostic.conclusion


def test_reports_long_and_heterogeneous_decay():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.rt60_analysis = analysis(rt60=0.8, homogeneity=40.0)

    diagnostic = RT60Diagnostic().analyze(context)

    assert diagnostic.severity == "HIGH"
    assert diagnostic.score < 60
    assert "longue" in diagnostic.conclusion
    assert "Décroissance énergétique prolongée" in diagnostic.causes
    assert len(diagnostic.recommendations) == 2


def test_handles_missing_or_unusable_rt60_analysis():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    missing = RT60Diagnostic().analyze(context)
    context.rt60_analysis = RT60Analysis()
    unusable = RT60Diagnostic().analyze(context)

    assert missing.severity == "INFO"
    assert missing.confidence == 0
    assert unusable.severity == "INFO"
    assert "insuffisante" in unusable.message

