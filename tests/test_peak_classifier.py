from acousticbrain.analysis.peak_classifier import PeakClassifier
from acousticbrain.models import (
    EvidenceLevel,
    ModeMatch,
    Peak,
    PeakClassificationType,
    ReflectionSurface,
    RoomMode,
    SBIRAnalysis,
    SBIRCandidate,
)


def peak(frequency):
    return Peak(frequency=frequency, spl=80.0, index=0, prominence=8.0)


def test_classifies_a_confirmed_axial_mode_match():
    detected_peak = peak(63.5)
    mode = RoomMode(axis="Longueur", order=2, frequency=63.2)
    analysis = PeakClassifier().analyze(
        peaks=[detected_peak],
        mode_matches=[ModeMatch(detected_peak, mode, 0.3, 96)],
        room_modes=[mode],
    )

    classification = analysis.classifications[0]

    assert classification.classification is PeakClassificationType.ROOM_MODE
    assert classification.confidence == 96
    assert classification.evidence_level is EvidenceLevel.CONFIRMED
    assert classification.room_mode == mode
    assert analysis.score == 100


def test_classifies_an_sbir_candidate_when_no_modal_match_exists():
    detected_dip = peak(75)
    candidate = SBIRCandidate(
        surface=ReflectionSurface.FLOOR,
        measured_frequency=75,
        theoretical_frequency=74.6,
        distance_m=1.15,
        delay_ms=6.7,
        frequency_error_hz=0.4,
        match_score=88,
        peak=detected_dip,
    )
    sbir_analysis = SBIRAnalysis(
        candidates=[candidate],
        best_match=candidate,
        reflection_surface=ReflectionSurface.FLOOR,
        reflection_distance_m=1.15,
        delay_ms=6.7,
        confidence=88,
        score=12,
    )

    analysis = PeakClassifier().analyze(
        peaks=[detected_dip],
        mode_matches=[],
        room_modes=[],
        sbir_analysis=sbir_analysis,
    )

    classification = analysis.classifications[0]

    assert classification.classification is PeakClassificationType.SBIR
    assert classification.evidence_level is EvidenceLevel.CONFIRMED
    assert classification.sbir_candidate == candidate


def test_marks_a_feature_without_physical_evidence_as_unclassified():
    analysis = PeakClassifier().analyze(
        peaks=[peak(367)],
        mode_matches=[],
        room_modes=[],
    )

    classification = analysis.classifications[0]

    assert classification.classification is PeakClassificationType.UNCLASSIFIED
    assert classification.evidence_level is EvidenceLevel.OBSERVED
    assert analysis.score == 0
    assert analysis.confidence == 0


def test_marks_a_nearby_mode_without_a_match_as_a_hypothesis():
    mode = RoomMode(axis="Largeur", order=1, frequency=42)
    analysis = PeakClassifier().analyze(
        peaks=[peak(43)],
        mode_matches=[],
        room_modes=[mode],
    )

    classification = analysis.classifications[0]

    assert classification.classification is PeakClassificationType.ROOM_MODE
    assert classification.evidence_level is EvidenceLevel.HYPOTHESIS
    assert classification.confidence == 50
