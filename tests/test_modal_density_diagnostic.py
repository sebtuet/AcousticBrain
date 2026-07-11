from acousticbrain.analysis import AnalysisContext
from acousticbrain.diagnostics import ModalDensityDiagnostic
from acousticbrain.models import ModalBand, ModalDensityAnalysis, Measurement


def test_modal_density_diagnostic_interprets_sparse_band():
    context = AnalysisContext(measurement=Measurement(name="L+R"))
    sparse_band = ModalBand(100, 140, 1, 0.025, None, [120])
    context.modal_density = ModalDensityAnalysis(
        total_mode_count=5,
        axial_mode_count=2,
        tangential_mode_count=2,
        oblique_mode_count=1,
        average_spacing_hz=18,
        minimum_spacing_hz=8,
        maximum_spacing_hz=35,
        sparse_bands=[sparse_band],
        score=55,
        confidence=75,
    )

    diagnostic = ModalDensityDiagnostic().analyze(context)

    assert diagnostic.severity == "HIGH"
    assert diagnostic.score == 55
    assert "zones modales clairsemées" in diagnostic.conclusion
    assert "2 axiaux, 2 tangentiels, 1 obliques" in diagnostic.observations[1]
