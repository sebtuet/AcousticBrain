# Scientific Assertion Model Inventory

## Nature

**AUDIT — NON NORMATIF**

Ce document cartographie les objets métier qui produisent ou transportent une
affirmation scientifique. Il n’a aucune autorité normative.

Cet audit ne crée aucune règle, aucune capacité et aucune Scientific Question.
Il ne définit aucun modèle cible et ne propose aucune migration.

## Métadonnées

- Date : `2026-07-26`
- Commit du dépôt audité :
  `0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8`
- Branche auditée : `agent/scientific-normative-foundations`
- Nature : inventaire technique des modèles d’affirmation

## Base normative

- `docs/scientific/SCIENTIFIC_CONTRACT.md`
- `docs/scientific/KNOWLEDGE_MODEL.md`
- `docs/scientific/EVIDENCE_MODEL.md`
- `docs/scientific/SCIENTIFIC_ASSERTION_CONTRACT.md`

Base normative observée au commit audité.

## Périmètre

- dataclasses de `acousticbrain/models/` ;
- objets d’analyse, diagnostic, hypothèse, observation, reasoning, action,
  preuve, résultat et acquisition ;
- conteneurs de synthèse ;
- `AnalysisContext`, `Report` et projections ;
- objets de contexte et de réponse Advisor.

## Exclusions

- aucune modification ou proposition de migration ;
- aucune décision sur une représentation commune ;
- aucune évaluation algorithmique des calculs acoustiques ;
- aucun présentateur considéré comme autorité scientifique ;
- aucune inférence de Scientific Question.

## Méthode

- extraction des dataclasses et de leurs champs par inspection de l’AST Python ;
- recherche lexicale des signaux correspondant aux 14 attributs ;
- lecture sémantique des principaux objets ;
- vérification des conteneurs et transporteurs ;
- distinction entre proximité lexicale et équivalence normative.

Commandes représentatives :

```text
rg -l '@dataclass' acousticbrain/models acousticbrain/analysis
rg -n '^class ' acousticbrain/models
rg -n 'provenance|source_|scope|domain|strength|evidence_level' acousticbrain/models
rg -n 'hypothesis|limitation|contradict|revision|refut|withdraw|status' acousticbrain/models
python -c '<inspection AST en lecture seule>'
git status --short
git diff --check
```

## Reproductibilité

Rejouer l’extraction et l’inspection sur :

```text
0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8
```

Comparer chaque information avec les quatorze attributs de
`SCIENTIFIC_ASSERTION_CONTRACT.md`. Une correspondance de nom ne doit pas être
assimilée automatiquement à une équivalence sémantique.

## Observations et preuves

### Résultat quantitatif

État observé :

- 151 fichiers contenant des dataclasses métier ;
- 115 dataclasses portant au moins un signal contractuel.

| Signal structurel | Nombre d’objets |
|---|---:|
| Provenance ou sources | 89 |
| Portée ou cible | 18 |
| Domaine explicite | 3 |
| Force ou niveau de preuve | 3 |
| Hypothèses | 18 |
| Limitations | 12 |
| Contradictions ou contre-preuves | 14 |
| Statut | 35 |
| Conditions de révision | 0 |
| Conditions de réfutation | 0 |
| Conditions de retrait | 0 |
| Portée maximale autorisée | 0 |

La seule mention structurelle de réfutation était l’agrégat
`refuted_hypotheses` de `OptimizationSessionAnalysis`. Elle ne constitue pas
une condition normative de réfutation.

## Objets exprimant directement une connaissance

### Observation, hypothèse et reasoning

- `AcousticObservation`
- `AcousticHypothesis`
- `DeterministicReasoningPremise`
- `DeterministicInferenceStep`
- `DeterministicAcousticReasoning`
- `ReasoningEvidence`
- `MissingReasoningFact`

Informations fréquemment présentes :

- contenu ;
- sources ;
- preuves favorables ou défavorables ;
- règles ;
- limitations pour les objets récents ;
- confiance ou support numérique ;
- statuts métier.

Lacunes transversales :

- type épistémique explicite ;
- portée et domaine ;
- force probante normative ;
- conditions de révision, réfutation et retrait ;
- portée maximale.

### Preuves et qualifications probantes

- `EvidenceReference`
- `ReasoningEvidence`
- `WeightedObjectReference`
- `EvidenceBlockingFactor`
- `EvidenceDimensionCeiling`
- `EvidenceWeightRuleApplication`
- `DeterministicEvidenceWeight`

`EvidenceReference` identifie un fait et une source, sans hypothèse cible,
direction, règle d’interprétation ni domaine.

`ReasoningEvidence` ajoute un rôle, des règles indirectes, une force et une
confiance numériques, mais ne satisfait pas le contrat complet d’une preuve
orientée.

`DeterministicEvidenceWeight` conserve références, contradictions,
limitations, blocages, plafonds et règles. Sa force utilise
`UNAVAILABLE / LOW / MEDIUM / HIGH`, vocabulaire différent de l’ordre normatif.

### Actions, décisions et acquisitions

- `Recommendation`
- `VerificationAction`
- `DeterministicCorrectiveAction`
- `EvidenceAcquisitionPlan`
- `ExperimentCandidate`
- `ExperimentPlan`
- `CausalDiscriminationDecision`
- `ReflectionCandidateVerificationProposal`
- `LoudspeakerPositioningExperimentProposal`
- `ListeningPositionCampaignPlan`

Ces objets expriment souvent :

- contenu et cible ;
- priorité ;
- provenance amont ;
- préconditions ;
- paramètres ;
- blocages ;
- statut ou applicabilité.

Ils n’expriment pas uniformément la force probante, le domaine, les conditions
de révision et de retrait ni la portée maximale.

### Résultats expérimentaux et états longitudinaux

- `ComparableExperimentFact`
- `ExperimentFactDelta`
- `ObservedExperimentFact`
- `ExperimentCounterFact`
- `ExperimentEvolutionResult`
- `ExperimentCampaignAnalysis`
- `CausalTrajectoryAssessment`
- `CausalDiscriminationAnalysis`
- `LongitudinalExperimentalLearningState`
- `CampaignReferenceQualification`
- `ControlledReflectionHypothesisStatusUpdate`

Ces objets présentent une provenance et des statuts riches. Les statuts
`outcome`, `eligibility`, `causality`, `applicability` et `learning_status`
répondent à des questions différentes et ne constituent pas un statut
transversal unique.

## Faits et analyses physiques

### Faits élémentaires observés

- `Measurement`
- `ImpulseResponse`
- `Peak`
- `ReflectionEvent`
- `RoomMode`
- `ModeMatch`
- `BassDecayModalMatch`
- `EnergyWindowAnalysis`
- analyses de bande RT60, bass decay, clarté, direct/réverbéré et spatial ;
- faits et différences d’expériences ;
- observations de comparaison de réflexion.

Le contenu quantitatif est généralement explicite. L’unité, la méthode et la
confiance sont parfois présentes. Le type épistémique, la portée, le domaine,
les conditions de révision et la portée maximale ne sont pas uniformes.

### Agrégats d’analyse observés

- `MeasurementQualityAnalysis`
- `MeasurementReadinessAnalysis`
- `RoomModesAnalysis`
- `ModalDensityAnalysis`
- `StereoAnalysis`
- `SBIRAnalysis`
- `RT60Analysis`
- `ETCAnalysis`
- `ClarityAnalysis`
- `DirectReverberantAnalysis`
- `BassDecayAnalysis`
- `SpatialAnalysis`
- `GeometryEarlyReflectionAnalysis`
- `GeometrySBIRAnalysis`
- `SurfaceMaterialAnalysis`
- `PropagationGeometryAnalysis`
- `ConfidenceAnalysis`
- `GlobalAnalysis`

Le suffixe `Analysis` ne permet pas à lui seul de savoir si le contenu est un
fait, un diagnostic, une hypothèse ou une qualification.

### Corrélations observées

- `BassDecayCorrelation`
- `ClarityCorrelation`
- `DirectReverberantCorrelation`
- `ETCReflectionCorrelation`
- `SpatialCorrelation`
- `SBIRGeometryCorrelation`
- `GlobalCorrelation`

Elles conservent un contenu relationnel, des sources, des scores et parfois une
base technique. Elles ne déclarent pas uniformément une hypothèse cible, une
direction probante, un domaine ou une force normative.

## Transporteurs

### Conteneurs métier

- synthèses d’observations, reasonings, actions, weighting et acquisition ;
- `RecommendationAnalysis` ;
- `TraceabilityAnalysis` ;
- analyses de comparaison, campagne et apprentissage longitudinal ;
- registres de déclarations, comparaisons et mises à jour de réflexion.

Ils préservent les objets contenus mais ne définissent pas un contrat commun
des attributs normatifs.

### AnalysisContext

`AnalysisContext` transporte environ 60 familles de résultats. Il juxtapose
les modèles historiques et modernes sans imposer de contrat transversal.

### Report et présentateurs

`Report` agrège les diagnostics, analyses, observations, reasonings, actions,
pondérations et plans. Trente-deux fichiers de présentation produisent des
projections.

Ces objets sont des consommateurs. Ils ne sont pas une source légitime
d’attributs scientifiques absents en amont.

### Advisor

Les objets Advisor préservent de nombreuses références, limitations,
contradictions et blocages. Une `AdvisorClaim` reste une affirmation de
fournisseur soumise à validation, pas une affirmation scientifique autorisée.

Les statuts de langue, couverture, intégrité et dégénérescence concernent la
communication, pas le statut épistémique.

## Divergences sémantiques observées

- confiance différente de la force probante ;
- catégorie différente du type épistémique ;
- outcome ou applicabilité différents d’un statut transversal ;
- identifiants de sources insuffisants pour une provenance complète ;
- cible différente de la portée ;
- référence favorable ou défavorable insuffisante pour une preuve conforme ;
- historique différent de conditions explicites de révision ;
- blocage différent d’une limitation scientifique complète.

## Limites

- Le comptage structurel dépend des noms de champs et a été complété par une
  revue manuelle des objets principaux.
- Cet inventaire ne décide pas quels objets doivent à terme porter directement
  le contrat.
- Il ne définit aucune stratégie de représentation ou de migration.
- Il n’évalue pas la vérité physique des contenus.
- Il ne s’applique pas automatiquement à une révision ultérieure.
