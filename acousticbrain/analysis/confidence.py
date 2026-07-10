from acousticbrain.models import ConfidenceAnalysis, ConfidenceFactor


class ConfidenceEngine:
    """Agrège des confiances locales sans recalculer les preuves acoustiques."""

    def analyze(self, analyses: dict[str, object | None]) -> ConfidenceAnalysis:
        """Retourne une confiance fondée sur des objets ``*Analysis`` explicites.

        Une analyse disponible doit exposer une propriété ``confidence`` entre
        0 et 100. L'accord mesure la dispersion de ces confiances : il ne
        représente pas une nouvelle preuve acoustique.
        """
        if not analyses:
            return ConfidenceAnalysis()

        factors = []
        local_confidences = []

        for source, analysis in analyses.items():
            confidence = self._confidence_of(analysis)
            if confidence is None:
                factors.append(
                    ConfidenceFactor(
                        source=source,
                        score=0.0,
                        weight=1.0,
                        available=False,
                        explanation="Confiance locale indisponible.",
                    )
                )
                continue

            local_confidences.append(confidence)
            factors.append(
                ConfidenceFactor(
                    source=source,
                    score=confidence,
                    weight=1.0,
                    available=True,
                    explanation=f"Confiance locale disponible : {confidence:.1f}/100.",
                )
            )

        available_count = len(local_confidences)
        missing_count = len(analyses) - available_count
        coverage_score = 100.0 * available_count / len(analyses)
        agreement_score = self._agreement_score(local_confidences)
        local_average = (
            sum(local_confidences) / available_count if available_count else 0.0
        )
        score = (
            0.50 * local_average
            + 0.25 * coverage_score
            + 0.25 * agreement_score
        )

        factors.extend(
            [
                ConfidenceFactor(
                    source="coverage",
                    score=coverage_score,
                    weight=0.25,
                    available=available_count > 0,
                    explanation=(
                        f"{available_count}/{len(analyses)} analyses fournissent "
                        "une confiance locale."
                    ),
                ),
                ConfidenceFactor(
                    source="agreement",
                    score=agreement_score,
                    weight=0.25,
                    available=available_count > 0,
                    explanation=self._agreement_explanation(local_confidences),
                ),
            ]
        )

        return ConfidenceAnalysis(
            score=score,
            factors=factors,
            available_evidence_count=available_count,
            missing_evidence_count=missing_count,
            agreement_score=agreement_score,
            coverage_score=coverage_score,
        )

    @staticmethod
    def _confidence_of(analysis):
        if analysis is None:
            return None

        confidence = getattr(analysis, "confidence", None)
        if not isinstance(confidence, (int, float)):
            return None

        return min(100.0, max(0.0, float(confidence)))

    @staticmethod
    def _agreement_score(confidences):
        if not confidences:
            return 0.0
        if len(confidences) == 1:
            return 100.0

        return 100.0 - (max(confidences) - min(confidences))

    @staticmethod
    def _agreement_explanation(confidences):
        if not confidences:
            return "Aucune confiance locale ne permet d'évaluer l'accord."
        if len(confidences) == 1:
            return "Une seule confiance locale est disponible."

        spread = max(confidences) - min(confidences)
        return f"Dispersion des confiances locales : {spread:.1f} point(s)."
