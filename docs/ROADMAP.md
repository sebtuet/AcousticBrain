# AcousticBrain Roadmap

Cette roadmap présente les capacités du moteur plutôt que l'historique des PR.
Toute évolution doit respecter [ARCHITECTURE.md](ARCHITECTURE.md),
[SCORING.md](SCORING.md) et [ANALYSIS_CONTRACT.md](ANALYSIS_CONTRACT.md).

## ✅ Core Platform

- import des mesures SPL REW ;
- import des réponses impulsionnelles REW ;
- modèle `Project` ;
- pipeline d'analyse déterministe ;
- golden report de non-régression ;
- `ConfidenceEngine` ;
- `GlobalSynthesizer` ;
- `RecommendationEngine` ;
- `TraceabilityEngine` ;
- priorisation structurée des diagnostics.

## ✅ Physics

- détection des pics et creux ;
- classification par bandes fréquentielles ;
- propriétés géométriques de la salle ;
- fréquence de Schroeder ;
- modes propres complets :
  - axiaux ;
  - tangentiels ;
  - obliques ;
- correspondance entre pics et modes propres ;
- densité modale complète.

## ✅ Spatial Analysis

- analyse de symétrie stéréo ;
- analyse SBIR ;
- surfaces de réflexion structurées ;
- correspondances entre phénomènes mesurés et géométrie disponible.

## ✅ Temporal Analysis

- RT60 :
  - EDT ;
  - T20 ;
  - T30 ;
  - filtrage en tiers d'octave ;
  - agrégation multi-canal ;
  - écarts gauche-droite qualifiés par leur confiance ;
- ETC :
  - détection du son direct ;
  - détection des réflexions précoces ;
  - agrégation multi-canal ;
  - événements communs et spécifiques ;
  - corrélations structurées ETC-SBIR.

## ✅ Current Diagnostics

- réponse dans le grave ;
- creux importants ;
- stéréo ;
- SBIR ;
- modes propres complets ;
- densité modale complète ;
- confiance ;
- RT60 ;
- ETC et corrélations de réflexions précoces.

Les diagnostics interprètent les connaissances existantes. Ils ne détectent
pas de nouvelles features et ne recalculent aucune analyse.

## 🚧 Advanced Room Analysis

- classification physique complète des pics ;
- flutter echo ;
- validation par méthode des sources images ;
- regroupement des réflexions ;
- classement des réflexions ;
- symétrie des réflexions ;
- validation croisée ETC, SBIR et géométrie complète.

## 🚧 Additional Acoustic Metrics

- clarté C50 et C80 ;
- définition D50 ;
- temps central Ts ;
- IACC ;
- analyse LEDE ;
- diffusion ;
- décroissance du grave.

Ces métriques devront être produites comme des `*Analysis` structurées avant
toute interprétation ou présentation.

## 🚧 Recommendations

- recommandations temporelles ;
- recommandations de traitement des réflexions ;
- priorisation structurée des surfaces ;
- stratégies de recommandation configurables ;
- prise en compte explicite des nouvelles analyses RT60 et ETC.

Les recommandations sont déduites des connaissances structurées, jamais des
diagnostics ni de leurs textes.

## 🚧 Explainability Extensions

- provenance RT60 et ETC dans `GlobalAnalysis` ;
- recommandations temporelles dans `TraceabilityAnalysis` ;
- export JSON complet du graphe de connaissance ;
- navigation d'une action vers les preuves physiques sources.

## 🚧 AI Layer — Optional

Un LLM ne réalise jamais une mesure ou un calcul acoustique. Il peut uniquement
consommer les connaissances déterministes déjà produites pour fournir :

- un rapport en langage naturel ;
- un résumé exécutif ;
- des explications pédagogiques ;
- un assistant interactif, notamment via Ollama.

La logique métier reste indépendante de tout fournisseur de modèle.

## Guiding Principles

- Physics before interpretation.
- Structured analyses before synthesis.
- Structured knowledge before recommendations.
- Recommendations derive from knowledge, never diagnostics.
- Presentation and AI consume facts without recalculating them.
- LLMs never replace deterministic acoustic calculations.
- Missing evidence remains missing; no layer invents knowledge.
