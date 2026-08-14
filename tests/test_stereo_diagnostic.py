from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import StereoDiagnostic
from acousticbrain.models import Measurement, Peak, StereoAnalysis


def peak(frequency):
    return Peak(frequency=frequency, spl=80.0, index=0, prominence=5.0)


def test_stereo_diagnostic_reports_asymmetry():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.stereo = StereoAnalysis(
        common_peaks=[(peak(50), peak(50))],
        left_only_peaks=[peak(70), peak(90)],
        right_only_peaks=[peak(110)],
    )

    diagnostic = StereoDiagnostic().analyze(context)

    assert diagnostic.severity == "LOW"
    assert diagnostic.confidence == 90
    assert 30 < diagnostic.score <= 60
    assert "2 spécifiques à gauche" in diagnostic.observations[0]


def test_stereo_diagnostic_reports_nominal_symmetry():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    context.stereo = StereoAnalysis(
        common_peaks=[(peak(50), peak(50))],
    )

    diagnostic = StereoDiagnostic().analyze(context)

    assert diagnostic.severity == "OK"
    assert diagnostic.message == "Comportement stéréo globalement homogène."


def test_stereo_diagnostic_requires_channel_measurements():
    context = AnalysisContext(measurement=Measurement(name="L+R"))

    diagnostic = StereoDiagnostic().analyze(context)

    assert diagnostic.severity == "INFO"
    assert diagnostic.confidence == 0
    assert "indisponible" in diagnostic.message
