# Architecture proposée pour la planification d'ajustements géométriques

> Statut : proposition d'architecture, non normative et non implémentée.
>
> Ce document décrit une frontière de domaine possible. Il ne crée aucune règle
> scientifique, aucune capacité, aucune Scientific Question et aucun engagement
> de livraison.

## 1. Résumé exécutif

AcousticBrain sait déjà analyser une campagne, construire des observations,
raisonner sur des hypothèses, déclarer des actions correctives, pondérer leurs
preuves et planifier l'acquisition de preuves manquantes. Il possède aussi une
capacité plus spécifique : `LoudspeakerPositioningExperimentEngine` peut
projeter une expérience de déplacement temporaire d'enceinte lorsque la cible,
la direction et les conditions de contrôle existent déjà.

Cette capacité existante ne calcule pas une position optimale et ne recommande
pas une correction permanente. Elle conserve explicitement
`causality_status = NOT_ESTABLISHED`. Le nouveau chantier ne doit donc pas la
dupliquer.

La valeur fonctionnelle recherchée est une étape ultérieure et plus stricte :
exprimer une prochaine modification géométrique limitée, opérable, réversible
et vérifiable, ou expliquer pourquoi aucune modification ne peut être
recommandée. Le périmètre initial ne doit viser ni l'optimum global d'une pièce,
ni une recherche numérique, ni une amélioration garantie.

La séparation fonctionnelle est la suivante :

```text
Evidence Acquisition Plan:
Que faut-il mesurer pour réduire l'incertitude ?

Geometry Adjustment Plan:
Quelle modification géométrique limitée faut-il tester ensuite, ou conserver
après une validation explicite ?
```

Une acquisition de preuves peut précéder un ajustement. Une expérience
géométrique teste une modification sans promettre d'amélioration. Une
recommandation corrective exige en plus une comparaison avant/après et une
règle scientifique approuvée.

## 2. État actuel d'AcousticBrain

### 2.1 Flux observé

Le flux moderne et les stages historiques coexistent dans
`acousticbrain/brain/pipeline.py`. Une vue centrée sur ce chantier est :

```text
Measurements
    ↓
Physical, temporal, spatial and geometry analyses
    ↓
AcousticObservationStage
    ↓
AcousticReasoningStage / DeterministicAcousticReasoningStage
    ↓
DeterministicCorrectiveActionStage
    ↓
DeterministicEvidenceWeightingStage
    ↓
EvidenceAcquisitionPlanningStage
    ↓
ExperimentPlanningStage (opt-in)
    ↓
GlobalSynthesisStage
    ↓
RecommendationStage
    ↓
LoudspeakerPositioningExperimentStage
    ↓
TraceabilityStage
    ↓
ReportBuilder
    ↓
Assessment / reporting
```

`LoudspeakerPositioningExperimentStage` intervient déjà après les
recommandations historiques. Il consomme `experiment_planning_analysis`,
`recommendation_analysis`, `room_geometry` et la disponibilité des mesures
L/R/L+R. Il produit une proposition expérimentale ou un blocage, puis
`LoudspeakerPositioningExperimentPresenter` la projette dans `Report`.

### 2.2 Ce qui existe déjà

- `RoomGeometry` contient les dimensions, surfaces, enceintes, positions
  d'écoute, orientations, obstacles et qualité des données.
- `GeometryPoint` fournit des coordonnées `x_m`, `y_m`, `z_m`.
- `GeometrySpeakerOrientation` fournit un lacet optionnel en degrés.
- `GeometryEarlyReflectionEngine`, `GeometrySBIRPredictionEngine` et
  `SBIRGeometryCorrelationEngine` produisent des faits géométriques et des
  compatibilités, sans établir seuls une causalité.
- `DeterministicCorrectiveAction` porte provenance, paramètres connus ou
  manquants, risques, contraintes, critères d'arrêt, contradictions et
  limitations.
- `DeterministicEvidenceWeight` sépare force, cohérence, pouvoir discriminant,
  complétude des paramètres, applicabilité et facteurs de blocage.
- `EvidenceAcquisitionPlan` sait décrire une acquisition et inclut déjà les
  types `CONTROLLED_SPEAKER_DISPLACEMENT`,
  `CONTROLLED_MICROPHONE_DISPLACEMENT` et `GEOMETRY_ACQUISITION`.
- `LoudspeakerPositioningExperimentProposal` porte cible, axe, direction, pas,
  contrôles, mesures requises, observables, confiance, provenance et limite
  causale.
- `PositioningProposalDeclarationService` permet de convertir explicitement une
  proposition éligible en déclaration d'expérience ; l'analyse elle-même reste
  en lecture seule.

### 2.3 Point d'insertion proposé

Un futur producteur de plan géométrique doit travailler dans le domaine, sur
`AnalysisContext`, après disponibilité des actions, poids, plans d'acquisition,
géométrie et propositions expérimentales. Il ne doit pas lire un texte de
diagnostic ni un objet présenté.

Pour un simple plan expérimental, la projection peut réutiliser le résultat de
`LoudspeakerPositioningExperimentStage`. Pour une recommandation corrective,
elle doit aussi consommer une comparaison avant/après explicitement reliée à
l'expérience. Cette dernière preuve n'est pas encore un contrat scientifique
général du dépôt.

Le plan finalisé serait ensuite projeté par `ReportBuilder`, avant la
construction de `assessment_summary`. La finalisation multi-expériences doit
respecter le même invariant que le résumé actuel : toute projection dérivée
doit être reconstruite après remplacement des collections finales du `Report`.

## 3. Définition du nouveau concept

### 3.1 Noms comparés

| Nom | Avantage | Risque |
| --- | --- | --- |
| `GeometryOptimizationPlan` | couvre enceintes et auditeur | suggère un optimum calculé |
| `AcousticOptimizationPlan` | large | mélange géométrie, traitement et DSP |
| `PlacementAdjustmentPlan` | concret | ne rend pas explicitement le repère géométrique |
| `SpeakerPlacementRecommendation` | lisible | exclut l'auditeur et promet une recommandation |
| `GeometryAdjustmentPlan` | limité, neutre, extensible | nécessite un champ d'intention explicite |

Le nom principal proposé est `GeometryAdjustmentPlan`.

Le terme « adjustment » décrit une modification bornée, sans prétendre
optimiser globalement la pièce. Un champ d'intention doit distinguer :

- `EXPERIMENTAL_TEST` : modification temporaire destinée à produire une preuve ;
- `VALIDATED_CORRECTIVE_ADJUSTMENT` : modification soutenue par une
  comparaison avant/après et une règle scientifique approuvée.

Tant que le second contrat scientifique n'existe pas, seule l'intention
`EXPERIMENTAL_TEST` peut être produite.

### 3.2 Propriétés

Le concept doit être :

- déterministe : mêmes entrées et même version de règles, mêmes sorties ;
- explicable : chaque champ décisionnel possède une provenance ;
- traçable : observations, raisonnements, actions, poids et expérience source
  restent référencés ;
- conservateur : l'absence de preuve produit un blocage, pas une estimation ;
- opérable : cible, repère, unité, plage et contrôles sont explicites ;
- réversible : état initial et procédure de retour sont obligatoires ;
- vérifiable : une acquisition de validation est associée au plan ;
- indépendant de l'Advisor.

### 3.3 Frontières avec les objets existants

- Une **hypothèse** exprime une explication causale à éprouver. Elle ne doit
  contenir ni trajectoire de déplacement ni consigne opérable.
- Une **corrective action** déclare une famille d'action justifiée, conditionnelle
  ou bloquée. Elle ne doit pas inventer les paramètres géométriques qui lui
  manquent.
- Un **Evidence Acquisition Plan** décrit les preuves à acquérir. Même lorsqu'il
  emploie un déplacement temporaire, il ne conclut pas qu'il faut conserver la
  nouvelle géométrie.
- Un **LoudspeakerPositioningExperimentProposal** est déjà un protocole
  expérimental opérable pour les enceintes. Le nouveau plan doit le référencer,
  pas refaire sa sélection.
- Un **GeometryAdjustmentPlan** relie une modification bornée à son état
  initial, ses contraintes, son rollback et sa validation. Son intention
  indique s'il s'agit seulement d'un test ou d'une correction déjà validée.
- L'**Advisor** peut expliquer un plan existant. Il ne choisit jamais la cible,
  la direction, l'amplitude, le statut ou les critères de validation.

## 4. Périmètre fonctionnel initial

« MVP » désigne ici le premier modèle et la première projection expérimentale,
pas une recommandation corrective.

| Ajustement | MVP | Données requises | Risques et symétrie | Confiance et blocage |
| --- | :---: | --- | --- | --- |
| Translation symétrique avant/arrière des deux enceintes | Oui, comme test | deux coordonnées, repère, direction structurée, marges, L/R/L+R | conserver écartement, orientation et symétrie | pas de seuil numérique nouveau ; blocage si contradiction, géométrie ou direction absente |
| Translation indépendante d'une enceinte | Oui, comme test conditionnel | enceinte identifiée, autre enceinte contrôlée, preuve d'asymétrie localisée | peut dégrader image et symétrie | blocage si cible ambiguë ou phénomène non localisé |
| Augmentation/diminution de l'écartement | Oui, comme test conditionnel | deux positions, déplacement bilatéral symétrique, position d'écoute fixe | trajectoires miroir obligatoires | blocage si repère ou contrainte de symétrie incomplet |
| Modification du toe-in | Non | orientations fiables, cible angulaire, méthode de mesure pertinente | modifie directivité, scène et réflexions simultanément | aucun moteur observé ne justifie encore un sens ou une plage angulaire |
| Déplacement longitudinal de la position d'écoute | Non au premier incrément | position actuelle, positions admissibles, protocole multi-position | modes et réflexions changent ensemble | les campagnes existantes acquièrent des preuves mais ne prescrivent pas un déplacement |
| Déplacement latéral de la position d'écoute | Non | localisation du défaut, symétrie de la pièce, zone admissible | peut masquer une asymétrie ou créer un cas non représentatif | blocage tant qu'une règle causale dédiée n'est pas approuvée |
| Déplacement vertical | Exclu | hauteur et contraintes physiques | hors usages initiaux | `UNSUPPORTED_ADJUSTMENT_TYPE` |

Le moteur existant couvre déjà les quatre directions d'enceintes
`FORWARD`, `BACKWARD`, `INWARD`, `OUTWARD` et les cibles gauche, droite ou les
deux. Le MVP doit les réutiliser plutôt que créer une seconde taxonomie.

## 5. Cas scientifiques admissibles

Les lignes suivantes définissent des conditions d'étude, pas des règles de
production approuvées.

| Phénomène | Observations et causalité nécessaires | Ajustement envisageable | Limites et refus |
| --- | --- | --- | --- |
| SBIR avec mur avant | creux mesuré, prédiction géométrique, surface et enceinte identifiées, protocole discriminant | translation longitudinale temporaire de l'enceinte concernée ou de la paire | une compatibilité fréquentielle n'est pas une preuve causale ; refuser sans géométrie et comparaison |
| Interaction avec mur latéral | événement/candidat associé à une surface et un canal, géométrie complète | translation latérale expérimentale ou, plus tard, rotation | plusieurs trajets changent ensemble ; refuser sans localisation |
| Mode axial dominant | persistance mesurée, correspondance modale robuste, variation multi-position | balayage de position d'écoute ou d'enceinte | un déplacement peut déplacer le problème ; aucune direction normative observée |
| Asymétrie gauche/droite | observations multi-domaines cohérentes et cible localisée | test indépendant d'une enceinte | contradictions actuelles restent bloquantes |
| Sensibilité excessive à la position d'écoute | comparaison de positions sous protocole identique | balayage longitudinal limité | ne pas confondre meilleure position mesurée et optimum général |
| Problème cohérent multi-position | stabilité du phénomène et contrôles documentés | test d'enceinte plus plausible qu'un simple déplacement du micro | cohérence ne démontre pas la cause |
| Problème localisé à une position | mesure répétable et voisinage échantillonné | acquisition supplémentaire avant ajustement | refuser une correction globale à partir d'un cas local |

Pour tous les cas, les preuves minimales doivent être définies par une
spécification scientifique dédiée. Ni ce document ni une règle acoustique
générale ne peuvent transformer automatiquement une plausibilité en
recommandation.

## 6. Modèle de domaine proposé

### 6.1 Agrégat

```text
GeometryAdjustmentPlan
- plan_id
- rule_set_id
- intent
- status
- target
- action_type
- coordinate_frame
- axis
- direction
- initial_state_reference
- magnitude_specification
- safety_ceiling
- source_corrective_action_ids
- source_evidence_weight_ids
- source_positioning_proposal_id
- supporting_observation_ids
- supporting_reasoning_ids
- supporting_hypothesis_ids
- expected_effects
- constraints
- controlled_variables
- blocked_reason_codes
- limitations
- rollback_instructions
- validation_plan
- scientific_status
- provenance
```

Les références sources doivent pointer vers des objets existants et non vers
leurs textes rendus. `expected_effects` décrit des effets à vérifier, pas des
résultats garantis.

### 6.2 Cibles

Réutiliser les cibles d'enceintes existantes et étendre seulement lorsqu'un
mandat l'autorise :

```text
LEFT_SPEAKER
RIGHT_SPEAKER
BOTH_SPEAKERS
LISTENING_POSITION  # futur, hors MVP
```

### 6.3 Types d'action

```text
TRANSLATE
ROTATE             # futur, hors MVP
CHANGE_SEPARATION  # représentation spécialisée d'une translation symétrique
```

`CHANGE_SEPARATION` peut être une vue métier utile, mais sa primitive physique
reste deux translations latérales symétriques. Le modèle doit empêcher qu'elle
soit appliquée à une seule enceinte.

### 6.4 Repère

Réutiliser exactement le repère de `RoomGeometry` :

- origine : coin avant-gauche du sol ;
- `x` positif : mur avant vers mur arrière ;
- `y` positif : mur gauche vers mur droit ;
- `z` positif : sol vers plafond ;
- unité linéaire : mètre ;
- orientation : lacet en degrés.

Les termes utilisateur `FORWARD`, `BACKWARD`, `INWARD`, `OUTWARD` doivent être
résolus en un vecteur signé dans ce repère. La provenance de cette résolution
doit être conservée. Aucun référentiel « auditeur » implicite ne doit coexister
avec le référentiel pièce.

### 6.5 Amplitude

```text
MagnitudeSpecification
- kind: EXACT | RANGE | SWEEP | UNKNOWN
- minimum_m
- maximum_m
- step_m
- exact_m
- source
```

Les invariants sont :

- une valeur exacte, une plage et un balayage sont mutuellement exclusifs ;
- toute valeur est finie, positive et exprimée en mètres ;
- une plage est ordonnée et divisible en pas déterministes ;
- le plafond de sécurité borne chaque point ;
- `UNKNOWN` ne peut jamais produire un plan `READY`.

La première version doit préférer un `SWEEP` borné ou le pas expérimental
existant à une valeur pseudo-précise. Le pas de 5 cm existant est une politique
opérationnelle de `LoudspeakerPositioningExperimentEngine`, pas une vérité
acoustique ni un plafond de sécurité universel.

### 6.6 Plan de validation

```text
GeometryValidationPlan
- baseline_experiment_id
- adjusted_experiment_id
- required_measurements
- controlled_variables
- compared_observable_ids
- favorable_criteria
- adverse_criteria
- unchanged_criteria
- inconclusive_criteria
- rollback_required
```

Les critères doivent provenir d'un protocole ou d'une règle versionnée. Le plan
ne doit pas inventer un seuil de succès.

## 7. Politique de confiance et de blocage

La politique doit réutiliser les dimensions de `DeterministicEvidenceWeight`
et ne pas les réduire à un score global.

| Décision | Conditions architecturales |
| --- | --- |
| Produire un test géométrique | cible, direction, amplitude/protocole, contrôles, géométrie et validation disponibles ; aucune contradiction bloquante |
| Produire une correction validée | conditions précédentes, résultat avant/après favorable et règle scientifique approuvée |
| Demander une acquisition de preuves | paramètre, géométrie, protocole ou discrimination manquant |
| Refuser | contradiction, cible ambiguë, phénomène non localisé, plage irréalisable ou type non supporté |

Une force de preuve élevée ne compense jamais une complétude de paramètres
faible. Aucun seuil de confiance numérique nouveau n'est proposé. Les niveaux
minimaux par phénomène nécessitent une validation humaine et une règle
scientifique versionnée.

Motifs de blocage initiaux proposés :

```text
MISSING_ROOM_GEOMETRY
MISSING_CURRENT_SPEAKER_POSITION
MISSING_LISTENER_POSITION
MISSING_SPEAKER_ORIENTATION
INSUFFICIENT_CAUSAL_EVIDENCE
CONFLICTING_HYPOTHESES
NON_LOCALIZED_PHENOMENON
AMBIGUOUS_TARGET
MISSING_DIRECTION
MISSING_ADJUSTMENT_RANGE
UNSUPPORTED_ADJUSTMENT_TYPE
UNSAFE_OR_INFEASIBLE_RANGE
VALIDATION_PROTOCOL_UNAVAILABLE
MISSING_BASELINE_REFERENCE
```

Un statut bloqué ne doit contenir ni vecteur applicable ni amplitude partielle.

## 8. Géométrie requise

| Donnée | Niveau | État observé |
| --- | --- | --- |
| Dimensions de la pièce | Obligatoire | disponible dans `RoomGeometry.dimensions` |
| Repère et unités | Obligatoire | définis par le contrat `RoomGeometry` |
| Coordonnées des enceintes ciblées | Obligatoire | disponibles si `RoomGeometry.speakers` est renseigné |
| Position d'écoute actuelle | Obligatoire | disponible si `RoomGeometry.listening_positions` est renseigné |
| Orientation des enceintes | Obligatoire pour rotation, contrôle sinon | optionnelle dans `speaker_orientations` |
| Distances aux parois | Dérivable | dérivables des coordonnées et surfaces rectangulaires |
| Marges physiques de déplacement | Obligatoire pour rendre le plan opérable | absentes comme contrat dédié |
| Zones interdites | Obligatoire si elles contraignent le trajet | partiellement descriptibles via ouvertures/meubles, sans évaluateur de trajectoire |
| Tolérances de saisie | Obligatoire pour la confiance géométrique | `data_quality` existe, mais aucune politique d'ajustement n'est définie |
| Zone d'écoute admissible | Obligatoire pour déplacer l'auditeur | absente comme domaine opérable |
| Identité baseline/état initial | Obligatoire | disponible au niveau campagne, pas encore liée à un plan géométrique générique |

Une complétude globale de `RoomGeometry` ne suffit pas. Le plan doit vérifier
les données requises champ par champ pour sa cible et son action.

## 9. Relation avec les Corrective Actions

`DeterministicCorrectiveAction` reste l'autorité déclarative qui répond à
« quelle famille d'action est justifiée ou bloquée ? ». Elle peut rester
qualitative :

```text
Investigate front-wall interference.
```

`GeometryAdjustmentPlan` répond à « quel changement borné, dans quel repère et
avec quelle validation ? » :

```text
Tester le déplacement symétrique des deux enceintes sur une plage autorisée,
avec retour à l'état initial et comparaison des observables déclarés.
```

Le plan doit référencer au moins une corrective action compatible. Il ne la
remplace pas et ne modifie ni son applicabilité ni son poids. Il constitue une
projection plus opérable, produite seulement lorsque les paramètres nécessaires
sont complets.

Le moteur historique `RecommendationEngine` ne doit pas devenir une source
alternative silencieuse lorsque la chaîne moderne dispose d'une action
incompatible ou bloquée. Toute compatibilité entre une recommandation
historique et une action moderne doit être explicite et testée.

## 10. Relation avec les Evidence Acquisition Plans

```text
Evidence plan:
mesurer pour comprendre.

Geometry adjustment plan:
modifier temporairement pour tester, ou appliquer une correction déjà validée.

Validation plan:
remesurer pour vérifier l'effet.
```

Un `EvidenceAcquisitionPlan` demeure nécessaire lorsqu'un facteur de blocage
doit être levé. Une proposition expérimentale de positionnement peut être
considérée comme une spécialisation opérable d'acquisition de preuve, mais elle
ne doit pas être dupliquée dans deux collections sans lien d'identité.

Tout `GeometryAdjustmentPlan` positif doit inclure un
`GeometryValidationPlan`. Pour `EXPERIMENTAL_TEST`, la validation produit de
nouvelles preuves. Pour `VALIDATED_CORRECTIVE_ADJUSTMENT`, elle vérifie que
l'effet favorable reste présent et qu'aucun critère adverse n'est déclenché.

## 11. Planification conservatrice

La stratégie initiale est :

```text
prochaine modification limitée et scientifiquement justifiée
```

Invariants :

1. une seule variable indépendante par plan ;
2. état initial enregistré ;
3. déplacement borné par des contraintes physiques explicites ;
4. pas mesurable et unité explicite ;
5. mêmes mesures avant et après ;
6. contrôles déclarés et conservés ;
7. retour à l'état initial possible ;
8. critères d'arrêt avant le premier déplacement ;
9. arrêt sur effet adverse, résultat inconclusif ou violation de contrainte ;
10. aucune action lorsque plusieurs causes ou actions de même autorité restent
    indépartageables.

La sélection ne doit jamais optimiser une seule métrique en ignorant les autres
observables déclarés.

## 12. Exemples de sortie attendue

### 12.1 Test admissible, sans promesse corrective

```text
Intent:
Experimental test

Target:
Both speakers

Adjustment:
Move forward symmetrically

Test range:
10-30 cm

Step:
5 cm

Reason:
Existing evidence is compatible with front-wall SBIR and the source protocol
provides an explicit direction and range.

Expected effect to test:
Shift the candidate cancellation frequency and compare the target band.

Scientific status:
Causality not established

Validation:
Repeat L, R and L+R measurements at every declared step, preserve controlled
variables, compare the declared observables, then return to the initial state.
```

Cette sortie n'est valide que si la plage provient d'une source structurée ;
elle ne peut pas être inventée à partir de cet exemple.

### 12.2 Blocage géométrique

```text
No geometry adjustment plan produced.

Reason:
MISSING_CURRENT_SPEAKER_POSITION
MISSING_LISTENER_POSITION

Next action:
Acquire geometry with explicit coordinates, units and provenance.
```

### 12.3 Expérience seulement

```text
Intent:
Experimental test

Decision:
Test adjustment, not corrective recommendation.

Reason:
Causal evidence is plausible, but no validated before/after comparison proves
that retaining the adjustment improves the declared outcome.
```

### 12.4 Recommandation refusée

```text
No validated corrective adjustment produced.

Reason:
CONFLICTING_HYPOTHESES
VALIDATION_PROTOCOL_UNAVAILABLE
```

## 13. Intégration au pipeline

Flux cible proposé :

```text
Measurements
    ↓
Observations
    ↓
Hypotheses
    ↓
Causal reasoning
    ↓
Corrective actions
    ├── Evidence acquisition plans
    └── Existing loudspeaker positioning experiment proposal
             ↓
      Geometry adjustment planning
             ↓
      Geometry validation plan
             ↓
      Assessment / reporting
```

### Producteur

Un futur `GeometryAdjustmentPlanner` consommerait :

- `RoomGeometry` ;
- `DeterministicCorrectiveActionSynthesis` ;
- `DeterministicEvidenceWeightingSynthesis` ;
- `EvidenceAcquisitionPlanSynthesis` ;
- `LoudspeakerPositioningExperimentAnalysis` ;
- une comparaison avant/après explicitement qualifiée, lorsqu'une correction
  validée est demandée.

Il produirait un agrégat immutable, sans mutation des sources.

### Finalisation

Le stage doit être exécuté après les producteurs sources. Dans le parcours
multi-expériences, la projection finale doit être reconstruite après que les
collections de la campagne finale ont remplacé celles du rapport initial.

### `Report`, summary et CLI

Une future propriété présentée pourrait être ajoutée à `Report`. Elle ne doit
entrer dans `assessment_summary` qu'après stabilisation de son contrat et sans
recalcul scientifique dans le presenter. Une option CLI dédiée est une phase
ultérieure ; le premier incrément peut se limiter au modèle et à l'intégration
interne.

La sérialisation, si elle est ajoutée, doit conserver les identifiants, unités,
repères, règles appliquées et blocages avec un ordre stable. Aucune écriture de
campagne ne doit être implicite.

## 14. Architecture logicielle proposée

| Composant | Responsabilité | Dépendances autorisées | Alternative minimale |
| --- | --- | --- | --- |
| `GeometryAdjustmentPlanner` | produire un plan ou un blocage depuis les objets déterministes | modèles de domaine et règles approuvées | commencer comme un seul moteur pur |
| `GeometryAdjustmentPolicy` | règles d'éligibilité par phénomène | actions, poids, géométrie, comparaison validée | méthodes privées du planner en phase A/B |
| `GeometryConstraintEvaluator` | vérifier repère, limites et trajectoire | `RoomGeometry`, contraintes explicites | validation champ par champ sans moteur séparé au MVP |
| `GeometryValidationPlanner` | projeter mesures, contrôles et critères existants | proposition expérimentale et protocole | sous-objet construit par le planner |
| `GeometryAdjustmentPresenter` | copier le résultat dans `Report` | agrégat uniquement | nécessaire lors de l'intégration au rapport |
| reporter CLI | afficher sans calcul | objet présenté | attendre une phase produit distincte |

Pour éviter la sur-architecture, les quatre premières responsabilités peuvent
commencer dans un modèle immutable et un unique planner pur. Des composants
séparés ne deviennent justifiés que lorsque plusieurs règles scientifiques
approuvées partagent réellement des politiques.

## 15. Déterminisme et gouvernance scientifique

Invariants :

- mêmes objets sources et même version de règles, même résultat ;
- aucune dépendance à un LLM ou à un fournisseur réseau ;
- aucun texte de diagnostic utilisé comme entrée ;
- aucune mutation de `RoomGeometry`, action, poids, plan ou proposition source ;
- identifiants stables et provenance champ par champ ;
- unités et repère explicites ;
- contradiction et limitation préservées ;
- action bloquée jamais rendue applicable par le planner ;
- force probante jamais résumée en score global ;
- paramètre absent jamais remplacé par une valeur par défaut silencieuse ;
- aucune direction déduite d'un score ;
- aucune plage inventée ;
- aucune recommandation corrective sans validation avant/après ;
- règles scientifiques identifiées, versionnées et testables ;
- Advisor limité à la reformulation de l'objet final.

Le document ne définit aucune règle acoustique normative. L'autorité
scientifique doit approuver séparément les conditions qui permettent de passer
de `EXPERIMENTAL_TEST` à `VALIDATED_CORRECTIVE_ADJUSTMENT`.

## 16. Stratégie de tests future

### Modèle

- rejeter identifiant, cible, unité ou repère absent ;
- rejeter plage inversée, pas nul, valeur non finie ou champs d'amplitude
  concurrents ;
- rejeter une recommandation positive contenant un blocage ;
- exiger rollback et plan de validation.

### Règles et blocages

- géométrie legacy sans enceintes : `MISSING_CURRENT_SPEAKER_POSITION` ;
- direction absente : aucun plan partiel ;
- hypothèses contradictoires : refus ;
- preuve forte mais paramètres incomplets : refus ;
- type `ROTATE` sans règle dédiée : `UNSUPPORTED_ADJUSTMENT_TYPE`.

### Repère et symétrie

- `FORWARD/BACKWARD` résolus sur l'axe `x` avec signe documenté ;
- `INWARD/OUTWARD` produisent des vecteurs miroir pour deux enceintes ;
- `CHANGE_SEPARATION` ne déplace jamais une seule enceinte ;
- aucun déplacement vertical au MVP.

### Intégration

- véritable `AcousticBrain` et corpus versionné ;
- une proposition PR-044 éligible est référencée, pas recréée ;
- cas réel sans direction reste bloqué ;
- plan final identique en mono et multi-expériences à sources équivalentes ;
- finalisation après remplacement du rapport multi-expériences ;
- presenter et reporter ne mutent aucune source.

### Déterminisme et non-régression

- deux exécutions byte-for-byte identiques ;
- ordre stable des plans et références ;
- sorties CLI historiques inchangées sans option future ;
- Advisor non initialisé ;
- aucun accès réseau ;
- aucun fichier de campagne écrit.

### Scénarios scientifiques

- compatibilité SBIR sans preuve causale : test uniquement ;
- comparaison favorable mais effet adverse sur une autre métrique : ne pas
  conserver l'ajustement ;
- amélioration à une seule position et dégradation ailleurs : résultat
  inconclusif ;
- égalité entre deux ajustements : aucun choix arbitraire ;
- résultat inchangé : rollback et absence de recommandation.

## 17. Risques et limites

- **Pseudo-précision** : une formule physique ne suffit pas à fournir une
  amplitude optimale.
- **Causalité insuffisante** : une corrélation géométrique peut seulement
  justifier un test.
- **Phénomènes couplés** : un déplacement modifie plusieurs trajets, modes et
  métriques.
- **Recommandations contradictoires** : deux causes peuvent demander des
  mouvements opposés.
- **Géométrie erronée** : coordonnées ou orientations imprécises invalident le
  plan.
- **Faisabilité physique** : meubles, câbles, portes et limites d'usage peuvent
  rendre une plage impossible.
- **Bénéfice local** : une amélioration au micro peut nuire à d'autres
  positions.
- **Métrique unique** : maximiser un indicateur peut dégrader la scène,
  l'équilibre ou le temporel.
- **Campagne insuffisante** : sans multi-position, la portée de la conclusion
  doit rester locale.
- **Confusion test/correction** : le vocabulaire et le statut doivent rester
  explicites dans le modèle et le rendu.
- **Double autorité** : le moteur PR-044 et un nouveau planner ne doivent jamais
  sélectionner indépendamment deux déplacements.

## 18. Découpage d'implémentation recommandé

### Phase A — Modèle minimal et blocages

**Objectif :** représenter un plan ou un refus sans produire de plan positif.

**Livrables :** enums, `GeometryAdjustmentPlan`, amplitude, validation,
blocages, invariants.

**Dépendances :** `RoomGeometry` et références d'objets existants.

**Acceptation :** modèle immutable, absence de valeur inventée, tests de tous
les blocages.

**Exclusions :** stage, CLI, règle acoustique, recommandation positive.

### Phase B — Projection des expériences existantes

**Objectif :** exposer sans duplication une proposition PR-044 éligible comme
`EXPERIMENTAL_TEST`.

**Livrables :** planner pur, référence obligatoire au `proposal_id`, plan de
validation dérivé des contrôles et observables existants, presenter.

**Dépendances :** Phase A et `LoudspeakerPositioningExperimentAnalysis`.

**Acceptation :** aucune nouvelle sélection, direction ou amplitude ; identité
et provenance conservées ; cas bloqués préservés.

**Exclusions :** correction permanente, écouteur, toe-in, nouvelle CLI.

### Phase C — Première correction déterministe limitée

**Objectif :** permettre `VALIDATED_CORRECTIVE_ADJUSTMENT` pour un phénomène et
un protocole explicitement approuvés.

**Livrables :** spécification scientifique versionnée, règle unique, lien à une
comparaison avant/après, critères adverses.

**Dépendances :** validation scientifique humaine et données de comparaison.

**Acceptation :** la règle échoue fermée ; aucun effet favorable non mesuré ;
portée locale explicite.

**Exclusions :** arbitrage multi-phénomènes et optimum global.

### Phase D — Validation longitudinale

**Objectif :** suivre état initial, ajustement, résultat, rollback ou maintien.

**Livrables :** association stable aux expériences et intégration au suivi
longitudinal.

**Dépendances :** déclaration d'expérience et comparaison reproductible.

**Acceptation :** historique immuable, résultat favorable/défavorable/inchangé/
inconclusif, aucune réécriture amont.

**Exclusions :** recherche automatique.

### Phase E — Recherche multi-objectif

**Objectif :** seulement si justifié, comparer plusieurs ajustements sous des
objectifs et contraintes explicites.

**Dépendances :** corpus de validation, objectifs non contradictoires, règles
scientifiques approuvées.

**Acceptation :** arbitrage explicable, contraintes dures, résultats
reproductibles.

**Exclusions :** optimisation numérique implicite ou pilotée par LLM.

Cette phase n'est pas engagée par le présent document.

## 19. Questions ouvertes

Décisions nécessitant une autorité humaine :

1. Quelles relations causales sont assez solides pour autoriser autre chose
   qu'un test expérimental ?
2. Une correction doit-elle exiger une amélioration sur plusieurs positions ?
3. Quels observables sont impératifs et lesquels sont seulement informatifs ?
4. Quels critères adverses annulent une amélioration locale ?
5. Une plage peut-elle être recommandée, ou seulement provenir d'un protocole ?
6. Le pas de 5 cm existant reste-t-il limité à PR-044 ?
7. Quels plafonds physiques s'appliquent à chaque cible et pièce ?
8. Comment représenter les zones praticables et les contraintes de mobilier ?
9. Quelle tolérance de coordonnées et d'orientation est acceptable ?
10. Faut-il autoriser un déplacement indépendant sans preuve d'asymétrie
    localisée ?
11. Quand le toe-in peut-il devenir une variable unique réellement contrôlée ?
12. Quelle campagne valide un déplacement de position d'écoute ?
13. Comment arbitrer deux corrections compatibles mais opposées ?
14. Quel objet de comparaison fait autorité pour la validation avant/après ?
15. Comment rattacher ce futur contrat aux documents scientifiques normatifs
    sans reconstruire de Scientific Question depuis le code ?

## 20. Recommandation finale

```text
REQUIRES_SCIENTIFIC_SPECIFICATION
```

Les prérequis architecturaux essentiels existent déjà : géométrie structurée,
provenance, actions, poids multidimensionnels, blocages, acquisitions,
proposition expérimentale de déplacement et reporting. Une Phase A purement
structurelle puis une Phase B de projection sans nouvelle sélection sont
architecturalement possibles.

En revanche, AcousticBrain ne possède pas encore de contrat scientifique
général autorisant le passage d'un test géométrique à une recommandation
corrective à conserver. Les seuils de preuve, critères multi-objectifs,
plafonds de déplacement, exigences multi-positions et règles de validation
doivent être décidés par l'autorité scientifique. Les déduire du code existant
inverserait la gouvernance.

La prochaine décision recommandée n'est donc pas d'implémenter un moteur
d'optimisation. Elle consiste à faire relire cette architecture, puis à
autoriser séparément soit la Phase A, soit la rédaction d'une spécification
scientifique pour un seul phénomène borné.
