# Architecture AcousticBrain

AcousticBrain transforme des mesures acoustiques en connaissances structurées,
puis en présentations. Les couches métier ne dépendent ni de la console, ni
d'un fournisseur de LLM.

## Pipeline

```text
Project / Measurement
        ↓
AnalysisStage
        ↓
PhysicsStage
  ├─ StereoAnalysis
  ├─ SBIRAnalysis
  ├─ ModalDensityAnalysis
  └─ ConfidenceAnalysis
        ↓
TemporalAnalysisStage
  ├─ RT60Analysis
  └─ ETCAnalysis
        ↓
GlobalSynthesisStage
  └─ GlobalAnalysis + GlobalCorrelation
        ↓
RecommendationStage
  └─ RecommendationAnalysis
        ↓
TraceabilityStage
  └─ TraceabilityAnalysis
        ↓
ReportBuilder
        ↓
DiagnosticsStage
        ↓
PrioritizationStage
        ↓
Report / ConsoleReporter
```

Chaque stage orchestre uniquement son moteur. Les règles de calcul, de
corrélation, de recommandation et de traçabilité restent dans leurs moteurs
respectifs.

## Couches de connaissance

### 1. Analyses physiques

Les objets `*Analysis` contiennent des faits, mesures, scores et confiances.
Ils ne produisent aucun texte utilisateur et ne dépendent pas des diagnostics.
Les connaissances temporelles comme `RT60Analysis` sont orchestrées dans un
stage distinct des calculs géométriques et spectraux de `PhysicsStage`.

### 2. Synthèse globale

`GlobalSynthesizer` croise les analyses physiques. `GlobalAnalysis` conserve
les contributions par domaine, les priorités, les provenances et les
`GlobalCorrelation` structurées.

### 3. Actions

`RecommendationEngine` reçoit explicitement les analyses utiles et produit une
`RecommendationAnalysis`. Les actions utilisent des codes stables, des cibles,
des paramètres scalaires, une priorité, une confiance et leurs provenances.

### 4. Explicabilité

`TraceabilityEngine` relie `GlobalAnalysis` et `RecommendationAnalysis` au
moyen d'`EvidenceReference` et d'`ExplanationLink`. Une chaîne incomplète ne
crée jamais de preuve ou de lien artificiel.

## Diagnostics et présentation

Les diagnostics interprètent les analyses pour l'utilisateur, sans être une
source des moteurs de synthèse, de recommandation ou de traçabilité. Les
présentateurs copient les connaissances structurées vers le rapport sans les
trier, filtrer, dédupliquer ou recalculer.

`PrioritizationStage` ordonne les diagnostics après leur production. Il ne
modifie pas les connaissances physiques ou structurées.

## Invariants

- aucun moteur métier ne parse un texte de diagnostic ;
- `AnalysisContext` transporte les résultats sans les interpréter ;
- les dépendances entre moteurs sont explicites ;
- les identifiants de recommandation, corrélation et explication sont stables ;
- toute valeur absente reste absente, sans connaissance inventée ;
- les projections destinées au JSON ou à la console sont des consommateurs
  purs.
- un consommateur ne dépend jamais d'un format historique lorsqu'une
  `Analysis` équivalente existe.

## Rapport de référence

Le jeu de mesures versionné dans `measurements/` alimente le test
`tests/test_golden_report.py`. Sa sortie console complète est figée dans
`tests/golden/reference_report.txt`. Toute modification intentionnelle du
comportement visible doit mettre à jour le snapshot dans le même changement et
être expliquée lors de la revue.
