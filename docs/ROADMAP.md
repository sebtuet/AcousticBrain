# AcousticBrain Roadmap

Cette roadmap décrit l'évolution métier du moteur. Toute PR doit respecter
[ARCHITECTURE.md](ARCHITECTURE.md), [SCORING.md](SCORING.md) et
[ANALYSIS_CONTRACT.md](ANALYSIS_CONTRACT.md).

## ✅ PR-001 — Brain Pipeline

- **Inputs :** projet, mesure stéréo, salle.
- **Outputs :** contexte d'analyse et rapport.
- **Models :** `AnalysisContext`, `Report`.
- **Diagnostics :** orchestration des diagnostics existants.
- **Tests :** pipeline et import des mesures.

## ✅ PR-002 — Stereo Analysis

- **Inputs :** pics gauche/droite, modes et mesures des canaux.
- **Outputs :** faits de symétrie, modes communs et balances par bande.
- **Models :** `StereoAnalysis`.
- **Diagnostics :** aucun texte produit par l'analyzer.
- **Tests :** appariement, tolérances et balances.

## ✅ PR-003 — Stereo Interpretation

- **Inputs :** `StereoAnalysis`.
- **Outputs :** observations, conclusion, impact et recommandations.
- **Models :** `Diagnostic` structuré.
- **Diagnostics :** `StereoDiagnostic`.
- **Tests :** scores, impacts et texte de conclusion.

## 🔄 PR-004 — SBIR Analysis

- **Inputs :** mesure, creux détectés, salle et enceinte.
- **Outputs :** candidats de réflexion et meilleure correspondance.
- **Models :** `ReflectionSurface`, `SBIRCandidate`, `SBIRAnalysis`.
- **Diagnostics :** `SBIRDiagnostic` / « Réflexions précoces » à finaliser.
- **Tests :** calcul des distances, délais et correspondances de creux.

## 🔜 PR-005 — Modal Density

- **Inputs :** dimensions de salle et modes propres.
- **Outputs :** densité modale et zones problématiques.
- **Models :** `ModalAnalysis`.
- **Diagnostics :** interprétation de la densité modale.
- **Tests :** calcul de densité et seuils de fréquence.

## 🔜 PR-006 — Peak Classification

- **Inputs :** pics, creux et bandes fréquentielles.
- **Outputs :** classification des phénomènes mesurés.
- **Models :** `PeakAnalysis`.
- **Diagnostics :** interprétation par famille de phénomène.
- **Tests :** règles et classifications limites.

## 🔜 PR-007 — Confidence Engine

- **Inputs :** preuves, correspondances et disponibilité des mesures.
- **Outputs :** confiance normalisée de chaque analyse.
- **Models :** données de preuve et de confiance.
- **Diagnostics :** aucun recalcul local de confiance.
- **Tests :** cohérence, données manquantes et seuils.

## 🔜 PR-008 — Diagnostic Prioritization

- **Inputs :** diagnostics structurés et impacts.
- **Outputs :** liste de diagnostics ordonnée.
- **Models :** priorité de diagnostic.
- **Diagnostics :** aucun nouveau diagnostic métier.
- **Tests :** ordre et égalités de priorité.

## ✅ PR-009 — Recommendation Engine

- **Inputs :** analyses physiques structurées.
- **Outputs :** recommandations fusionnées et priorisées.
- **Models :** recommandation structurée.
- **Diagnostics :** aucune dépendance aux diagnostics existants.
- **Tests :** contrat, règles, déduplication, intégration et présentation.

## 🔜 PR-010 — Global Acoustic Summary

- **Inputs :** analyses physiques et structurées de tous les domaines.
- **Outputs :** synthèse acoustique globale et domaines prioritaires.
- **Models :** `GlobalAnalysis`, contributions et provenances par domaine.
- **Diagnostics :** aucune dépendance aux diagnostics ni à leurs textes.
- **Tests :** agrégation de scores et liens inter-domaines.

## 🔄 PR-011 — Explainability

- **Inputs :** analyses globales, recommandations et confiance structurées.
- **Outputs :** traçabilité complète d'une conclusion.
- **Models :** `EvidenceReference`, `ExplanationLink`, `TraceabilityAnalysis`.
- **Diagnostics :** aucune dépendance aux diagnostics ni à leurs textes.
- **Tests :** provenance des preuves et reproductibilité.
