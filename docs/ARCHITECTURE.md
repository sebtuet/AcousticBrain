# Architecture

## Principe de conception

> Toute connaissance acoustique est produite une seule fois par un analyseur
> et réutilisée partout ailleurs. Les diagnostics, rapports et synthèses ne
> font qu'interpréter ou présenter cette connaissance.

Ce principe sépare les faits physiques de leur interprétation destinée à
l'utilisateur. Il préserve aussi la possibilité de faire évoluer les textes,
les langues et les interfaces sans modifier les calculs.

### Invariant : un diagnostic ne crée jamais de preuve

Un `Diagnostic` ne fait que sélectionner, agréger et expliquer des preuves
existantes. Toute preuve acoustique (`ModeMatch`, `SBIRCandidate`,
`PeakClassification`, `ModalBand`, etc.) doit être produite une seule fois par
un analyseur et portée par une `*Analysis`.

Par conséquent, une règle physique telle qu'une proximité fréquentielle entre
un pic et un mode appartient à un `Analyzer`, jamais à un diagnostic.

```text
Mesure → Analyseur → *Analysis → AnalysisContext → Diagnostic → Rapport
                                      │
                                      └────────────→ GlobalSynthesizer
```

### Responsabilités

| Couche | Produit | Responsabilité |
| --- | --- | --- |
| `Analyzer` | `*Analysis` | Produit des faits, classifications, scores et preuves à partir de mesures ou de résultats physiques existants. Il ne génère ni recommandations ni texte utilisateur. |
| `AnalysisContext` | Transport | Transporte les analyses entre les étapes, sans logique métier. |
| `Diagnostic` | `Diagnostic` | Lit uniquement le contexte et transforme les preuves en impact, confiance, causes, recommandations et formulation. Il ne recalcule rien. |
| `Report` | Rendu | Affiche les diagnostics sans les modifier ni les recalculer. |
| `GlobalSynthesizer` | `GlobalAnalysis` | Analyseur de second niveau : croise les objets `*Analysis` et leurs preuves ; il ne dépend jamais des diagnostics ni de leurs textes. |

Ainsi, `SBIRAnalyzer → SBIRAnalysis`, `StereoAnalyzer → StereoAnalysis`,
`ModalDensityAnalyzer → ModalDensityAnalysis` et
`PeakClassifier → PeakClassificationAnalysis` suivent le même contrat.

### Tests

- Les tests physiques injectent des mesures, géométries ou preuves existantes
  dans un analyseur et vérifient une `*Analysis`.
- Les tests d'interprétation injectent une `*Analysis` simulée dans un
  diagnostic et vérifient uniquement l'impact, la formulation et les
  recommandations.

## Checklist bloquante de revue de PR

Une PR est architecturalement valide seulement si chaque point applicable est
respecté.

### 1. Modèle de domaine

- [ ] Le besoin produit ou exploite une `*Analysis` explicite.
- [ ] Son modèle est cohérent avec les `*Analysis` existantes.
- [ ] Les preuves produites sont suffisantes pour les futurs consommateurs.

### 2. Analyse physique

- [ ] Toute règle physique est localisée dans un `Analyzer`.
- [ ] Aucune règle n'est dupliquée entre analyseurs.
- [ ] Des tests unitaires vérifient la physique indépendamment du pipeline.

### 3. Orchestration

- [ ] `AnalysisContext` transporte uniquement les résultats.
- [ ] Le pipeline et `PhysicsStage` orchestrent sans logique métier.
- [ ] Aucun recalcul physique ne s'y produit.

### 4. Consommation

- [ ] Les diagnostics lisent les `*Analysis` sans créer de preuve.
- [ ] Les rapports, exports et interfaces restent de simples consommateurs.
- [ ] Le `GlobalSynthesizer` ne consomme que des `*Analysis`.

### 5. Qualité

- [ ] Les tests applicables passent.
- [ ] Les analyses existantes ne subissent aucun effet de bord non voulu.
- [ ] L'API interne `*Analysis` reste stable ou évolue de manière compatible.

AcousticBrain repose sur six composants.

## Core

Orchestration.

## Planner

Décide quels experts consulter.

## Experts

Chaque expert possède un domaine précis.

## Tools

Calculs physiques et DSP.

## Knowledge

Base documentaire.

## LLM

Dialogue avec l'utilisateur.
