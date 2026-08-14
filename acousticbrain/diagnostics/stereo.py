from acousticbrain.models import EvidenceLevel

from .base import DiagnosticBase
from .diagnostic import Diagnostic


class StereoDiagnostic(DiagnosticBase):
    """Évalue la symétrie des pics détectés entre les deux canaux."""

    def analyze(self, context):
        analysis = context.stereo

        if analysis is None:
            return Diagnostic(
                title="Symétrie stéréo",
                severity="INFO",
                confidence=0,
                evidence_level=EvidenceLevel.OBSERVED,
                message="Analyse stéréo indisponible : les mesures gauche et droite sont requises.",
            )

        score = self._asymmetry_score(analysis)
        severity = self._severity(score)
        observations = self._observations(analysis)
        conclusion = self._conclusion(analysis, severity)

        return Diagnostic(
            title="Symétrie stéréo",
            severity=severity,
            score=score,
            confidence=90,
            evidence_level=EvidenceLevel.OBSERVED,
            message=conclusion,
            observations=observations,
            conclusion=conclusion,
            causes=[
                "Placement asymétrique des enceintes",
                "Influence de la pièce sur un seul canal",
                "Différence de position ou de câblage d'une enceinte",
            ],
            recommendations=[
                "Comparer les mesures gauche et droite",
                "Vérifier le positionnement des enceintes",
                "Contrôler la symétrie de la zone d'écoute",
            ],
        )

    def _asymmetry_score(self, analysis):
        peak_score = 100 - analysis.symmetry_score

        balances = (
            (analysis.balance_low, 0.5),
            (analysis.balance_mid, 0.3),
            (analysis.balance_high, 0.2),
        )
        available_balances = [
            (abs(balance), weight)
            for balance, weight in balances
            if balance is not None
        ]
        balance_score = 0.0
        if available_balances:
            weight_total = sum(weight for _, weight in available_balances)
            balance_score = sum(
                min(100.0, balance / 6.0 * 100.0) * weight
                for balance, weight in available_balances
            ) / weight_total

        observed_modes = (
            len(analysis.common_modes)
            + len(analysis.left_only_modes)
            + len(analysis.right_only_modes)
        )
        mode_score = 0.0
        if observed_modes:
            mode_score = 100.0 * (
                len(analysis.left_only_modes) + len(analysis.right_only_modes)
            ) / observed_modes

        return min(100.0, 0.55 * peak_score + 0.35 * balance_score + 0.10 * mode_score)

    @staticmethod
    def _severity(score):
        if score <= 30:
            return "OK"
        if score <= 60:
            return "LOW"
        if score <= 80:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _observations(analysis):
        observations = [
            (
                f"Pics : {analysis.common_count} communs, "
                f"{analysis.left_only_count} spécifiques à gauche, "
                f"{analysis.right_only_count} spécifiques à droite."
            ),
            (
                f"Modes axiaux : {len(analysis.common_modes)} communs, "
                f"{len(analysis.left_only_modes)} spécifiques à gauche, "
                f"{len(analysis.right_only_modes)} spécifiques à droite."
            ),
        ]

        for name, balance in (
            ("Grave", analysis.balance_low),
            ("Médium", analysis.balance_mid),
            ("Aigu", analysis.balance_high),
        ):
            if balance is not None:
                observations.append(f"Écart G-D {name.lower()} : {balance:+.1f} dB.")

        return observations

    @staticmethod
    def _conclusion(analysis, severity):
        if severity == "OK":
            return "Comportement stéréo globalement homogène."

        severity_label = {
            "LOW": "légère",
            "MEDIUM": "modérée",
            "HIGH": "forte",
        }[severity]
        notable_balances = [
            (name, balance)
            for name, balance in (
                ("grave", analysis.balance_low),
                ("médium", analysis.balance_mid),
                ("aigu", analysis.balance_high),
            )
            if balance is not None and abs(balance) > 1.0
        ]

        if notable_balances:
            name, balance = max(notable_balances, key=lambda item: abs(item[1]))
            return (
                f"Asymétrie {severity_label} principalement localisée dans le "
                f"{name} ({balance:+.1f} dB)."
            )

        return (
            f"Asymétrie {severity_label} due principalement à des phénomènes "
            "différents entre les deux canaux."
        )
