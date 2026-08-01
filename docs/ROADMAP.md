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

## ✅ Digital Room Description

- description utilisateur indépendante des mesures ;
- dimensions, enceintes, positions d'écoute et ouvertures typées ;
- validation géométrique relationnelle structurée ;
- persistance JSON versionnée ;
- interface locale découplée du domaine ;
- chargement optionnel et explicite dans `Project` ;
- adaptateur historique disponible sans branchement automatique.

## ✅ Physics

- détection déterministe des pics et creux ;
- classification par bandes fréquentielles ;
- caractéristiques fréquentielles descriptives LEFT, RIGHT et STEREO ;
- comparaisons `COMMON`, `LEFT_ONLY` et `RIGHT_ONLY`, sans attribution
  causale ;
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
  - corrélations structurées ETC-SBIR ;
- clarté :
  - C50 ;
  - C80 ;
  - D50 ;
  - temps central Ts ;
- rapport direct/réverbéré ;
- décroissance du grave.

## ✅ Current Diagnostics

- réponse dans le grave ;
- creux importants ;
- stéréo ;
- SBIR ;
- modes propres complets ;
- densité modale complète ;
- confiance ;
- RT60 ;
- ETC et corrélations de réflexions précoces ;
- clarté ;
- rapport direct/réverbéré ;
- décroissance du grave.

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

## ✅ Deterministic Evidence and Experimental Planning

- plans déterministes d'acquisition de preuves ;
- statuts `PROPOSED`, `READY` et `BLOCKED` ;
- génération de candidats expérimentaux lorsque leurs paramètres sont déjà
  explicitement structurés ;
- planification de campagne multi-position lorsqu'un protocole complet est
  fourni ;
- proposition de déplacement temporaire d'enceinte lorsque la cible, la
  direction et les contrôles requis existent ;
- absence d'invention des paramètres manquants et causalité conservée comme
  non établie.

## 🚧 Remaining Acoustic Metrics

- IACC ;
- analyse LEDE ;
- diffusion.

Ces métriques devront être produites comme des `*Analysis` structurées avant
toute interprétation ou présentation.

## 🚧 Executable Experiment Completion

- relier un `EvidenceAcquisitionPlan` incomplet à une déclaration expérimentale
  entièrement paramétrée lorsque toutes les données requises sont fournies ;
- conserver le blocage lorsqu'un protocole, une position, une répétition, un
  canal, un réglage ou un critère requis manque ;
- ne jamais transformer une compatibilité fréquentielle en causalité ni
  inventer une règle scientifique.

Le dépôt sait déjà projeter certains candidats, propositions et plans
exécutables à partir de déclarations complètes. Cette étape future concerne la
liaison générique depuis un plan d'acquisition incomplet, pas le remplacement
des contrats expérimentaux existants.

La continuité contractuelle d'un plan `READY` vers le manifeste expérimental
est maintenant disponible : le snapshot complet du plan et sa provenance sont
préservés sans dupliquer le moteur de planification. La conformité de
l'exécution et la validité de la comparaison restent des décisions séparées.

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
