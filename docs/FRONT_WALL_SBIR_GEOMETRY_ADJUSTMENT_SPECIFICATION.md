# Spécification scientifique — ajustement longitudinal symétrique pour SBIR au mur avant

> Statut : spécification normative proposée, soumise à revue scientifique.
>
> Périmètre : déplacement longitudinal, identique et réversible des deux
> enceintes pour éprouver une interaction probable avec le mur avant.
>
> Cette spécification ne crée aucune capacité logicielle et ne modifie aucun
> comportement existant.

## 1. Objet de la spécification

Cette spécification définit les règles permettant d'évaluer si un déplacement
longitudinal symétrique et limité des deux enceintes constitue :

- une expérience justifiée face à une annulation fréquentielle compatible avec
  une interaction au mur avant ;
- ou, après validation expérimentale, une correction recommandable.

Les décisions publiques sont exclusivement :

```text
NO_ACTION
REQUEST_MORE_EVIDENCE
PROPOSE_GEOMETRY_EXPERIMENT
RECOMMEND_GEOMETRY_ADJUSTMENT
```

Le périmètre exclut le déplacement d'une seule enceinte, tout déplacement
latéral ou vertical, l'écartement, le toe-in, la position d'écoute, les
traitements, l'EQ, l'optimisation globale, l'arbitrage multi-objectifs et toute
décision produite par l'Advisor.

La présente version spécifie complètement les conditions d'une expérience.
Elle décrit les conditions nécessaires d'une recommandation corrective, mais
ne fixe pas les seuils de succès requis pour l'autoriser.

## 2. Terminologie normative

Les mots **DOIT**, **NE DOIT PAS**, **DEVRAIT** et **PEUT** ont une portée
normative.

- **Mur avant** : surface `FRONT_WALL`, située à `x = 0` dans le repère de
  `RoomGeometry`.
- **Distance enceinte–mur avant** : coordonnée `x_m` du
  `GeometryPoint` représentant l'enceinte, ou
  `GeometrySBIRCandidate.speaker_boundary_distance_m` lorsque le candidat
  référence `FRONT_WALL`.
- **Déplacement vers l'avant** : translation selon `-x`, vers le mur avant,
  sans franchissement de `x = 0`.
- **Déplacement vers l'arrière** : translation selon `+x`, vers le mur arrière.
- **Déplacement symétrique** : application du même delta signé sur `x` aux deux
  enceintes, sans modification de `y`, `z`, de leur orientation ni de leur
  écartement.
- **Position initiale** : paire de coordonnées d'enceintes enregistrée avant
  toute intervention et associée à l'expérience baseline.
- **Position candidate** : paire obtenue uniquement par application du delta
  déclaré à la position initiale.
- **Bande cible** : intervalle fréquentiel explicitement associé au creux
  observé et au candidat SBIR. Ses bornes NE DOIVENT PAS être inventées par le
  planner.
- **Fréquence d'annulation** : première fréquence attendue d'un candidat
  géométrique, ou fréquence du creux observé qui lui est corrélé.
- **Preuve causale** : résultat reproductible d'une intervention contrôlée qui
  discrimine l'hypothèse SBIR d'au moins une hypothèse concurrente.
- **Expérience géométrique** : test temporaire et borné destiné à produire une
  preuve ; il n'affirme aucune amélioration.
- **Recommandation corrective** : décision de conserver une position candidate
  après comparaison avant/après conforme à un protocole et à des seuils
  scientifiques approuvés.
- **Validation** : nouvelle mesure contrôlée et comparaison explicite avec la
  position initiale.
- **Rollback** : retour vérifié aux coordonnées initiales.

Le référentiel unique est celui de `RoomGeometry` : origine au coin
avant-gauche du sol, `x` vers l'arrière, `y` vers la droite, `z` vers le haut,
distances en mètres.

## 3. Hypothèse physique couverte

### 3.1 Modèle retenu

La spécification couvre uniquement une interférence entre le trajet direct et
un trajet réfléchi du premier ordre sur le mur avant.

`GeometrySBIRPredictionEngine` calcule :

```text
f_cancel = c / (2 × ΔL)
```

avec :

- `f_cancel` en hertz ;
- `c = 343 m/s`, constante utilisée par le moteur existant ;
- `ΔL` en mètres, différence positive entre trajet réfléchi et trajet direct.

Dans le cas simplifié historique d'une source à distance `d` d'une paroi,
`ΔL ≈ 2d`, ce qui donne :

```text
f_cancel ≈ c / (4 × d)
```

Cette simplification n'est recevable que pour le premier ordre, une géométrie
rectangulaire compatible et un trajet effectivement associé au mur avant. Le
planner DOIT préférer le candidat dérivé par
`GeometryEarlyReflectionEngine` au modèle de distance simplifié.

### 3.2 Compatibilité, pas causalité

Une fréquence mesurée proche de la fréquence théorique indique seulement une
compatibilité. `SBIRGeometryCorrelationEngine` conserve explicitement la règle
`SBIR_COMPATIBILITY_IS_NOT_CAUSAL_PROOF`.

Une fréquence seule NE SUFFIT PAS parce que :

- un mode de pièce peut produire un défaut voisin ;
- une autre surface peut produire une annulation compatible ;
- plusieurs trajets peuvent se superposer ;
- la réponse gauche et la réponse droite peuvent différer ;
- une erreur géométrique déplace la prédiction ;
- la proéminence du creux ne démontre pas son origine.

La tolérance expérimentale existante est :

- erreur fréquentielle maximale : 15 % ;
- incertitude de prédiction maximale : 10 % ;
- confiance géométrique minimale : 70/100.

Ces valeurs proviennent du contrat
`GEOMETRY_DRIVEN_SBIR_CONTRACT.md` et de
`ExperimentPlanningEngine`. Elles autorisent au plus une expérience
discriminante. Elles NE DOIVENT PAS être interprétées comme seuils
d'amélioration corrective.

## 4. Données obligatoires

| Donnée | Classement | Source actuelle | Règle |
| --- | --- | --- | --- |
| Dimensions rectangulaires | `REQUIRED` | `RoomGeometry.dimensions` | DOIVENT être finies et positives |
| Repère et mètres | `REQUIRED` | contrat `RoomGeometry` | aucune conversion implicite |
| Deux enceintes identifiées | `REQUIRED` | `RoomGeometry.speakers` | exactement deux cibles distinctes pour ce plan |
| Coordonnées initiales | `REQUIRED` | `GeometryPoint` | `x_m`, `y_m`, `z_m` DOIVENT être disponibles |
| Référence au mur avant | `REQUIRED` | surface et `base_surface_id` | DOIT être `front_wall`/`FRONT_WALL` |
| Distance de chaque enceinte au mur avant | `DERIVED` | `x_m` ou candidat SBIR | les deux représentations DOIVENT être cohérentes |
| Orientation des enceintes | `REQUIRED` comme contrôle | `speaker_orientations` | ne change pas pendant le test |
| Position d'écoute | `REQUIRED` | `listening_positions` | identifiant et coordonnées fixes |
| Creux gauche et droit localisés | `REQUIRED` | pics/creux observés | chaque enceinte DOIT avoir une observation traçable |
| Candidats géométriques gauche et droit | `REQUIRED` | `GeometrySBIRCandidate` | chacun DOIT viser le mur avant |
| Corrélations fréquence-géométrie | `REQUIRED` | `SBIRGeometryCorrelation` | chacune respecte les seuils expérimentaux existants |
| Répétabilité baseline | `REQUIRED_FOR_RECOMMENDATION` | répétitions déclarées | seuil humain non encore approuvé |
| Comparaison multi-position | `REQUIRED_FOR_RECOMMENDATION` | campagne déclarée | obligatoire pour une correction |
| Dégagement avant/arrière | `REQUIRED` | contrainte utilisateur/géométrique | DOIT couvrir chaque position testée |
| Position initiale persistable | `REQUIRED` | référence d'expérience | nécessaire au rollback |
| Orientations exactes | `OPTIONAL` pour la causalité | qualité géométrique | obligatoires uniquement comme valeur contrôlée |

Une valeur dérivable NE DOIT être calculée que depuis une géométrie validée.
Une confiance acoustique élevée NE DOIT jamais compenser une coordonnée, une
unité ou une marge physique absente.

## 5. Conditions d'éligibilité

Le cas est évaluable seulement si toutes les conditions suivantes sont vraies :

1. `RoomGeometry` existe et utilise le modèle rectangulaire supporté.
2. Deux enceintes et une position d'écoute sont identifiées.
3. Les coordonnées initiales et unités sont valides.
4. Les deux enceintes disposent d'un candidat SBIR associé au mur avant.
5. Chaque candidat est relié à un creux observé de son canal.
6. Chaque corrélation respecte 15 % d'erreur maximale, 10 % d'incertitude
   maximale et 70/100 de confiance géométrique minimale.
7. L'hypothèse `SBIR_PLACEMENT_INTERACTION` existe et n'est pas contredite.
8. Aucune hypothèse concurrente de même autorité ne reste non discriminée.
9. Le déplacement conserve `y`, `z`, orientation, écartement, position
   d'écoute, niveau, chaîne de mesure et configuration de la pièce.
10. Une direction et une amplitude proviennent d'un protocole compatible, ou un
    test bidirectionnel borné a été explicitement approuvé.
11. Le dégagement physique couvre chaque position candidate.
12. Le protocole L/R/L+R et le rollback sont disponibles.

Une condition manquante produit un motif de blocage de la section 16. Aucun
résultat positif partiel ne doit exposer une direction ou une amplitude
applicable.

Le mouvement est symétrique par construction lorsque le même delta `x` est
appliqué aux deux enceintes. La spécification n'exige pas que leurs coordonnées
initiales soient identiques ; elle exige que leurs écarts initiaux en `x`, `y`
et `z` ne soient pas modifiés par l'expérience.

## 6. Niveaux de preuve

Cette échelle qualifie uniquement le cas SBIR/mur avant. Elle ne remplace pas
`DeterministicEvidenceWeight`.

| Niveau | Données requises | Signification | Décision maximale |
| --- | --- | --- | --- |
| `LEVEL_0` | aucune corrélation exploitable, ou hypothèse contredite | aucune base SBIR utilisable | `REQUEST_MORE_EVIDENCE` si un plan déterministe existe, sinon `NO_ACTION` |
| `LEVEL_1` | creux observé et fréquence théorique historique proche | compatibilité fréquentielle non géométrique | `REQUEST_MORE_EVIDENCE` |
| `LEVEL_2` | candidats géométriques et corrélations gauche/droite conformes aux seuils existants | compatibilité géométrique et fréquentielle bilatérale | `PROPOSE_GEOMETRY_EXPERIMENT` si toutes les préconditions sont complètes |
| `LEVEL_3` | `LEVEL_2` plus répétitions ou positions cohérentes | phénomène stable, causalité non établie | `PROPOSE_GEOMETRY_EXPERIMENT` |
| `LEVEL_4` | effet reproductible d'un déplacement contrôlé, retour baseline vérifié, hypothèses concurrentes discriminées | preuve expérimentale compatible avec la causalité SBIR | recommandation seulement si tous les seuils correctifs humains sont approuvés |

Règles :

- un niveau ne peut être attribué si une donnée requise manque ;
- un conflit causal plafonne la décision à `REQUEST_MORE_EVIDENCE` ;
- `LEVEL_2` ou `LEVEL_3` n'affirme aucune amélioration ;
- `LEVEL_4` est nécessaire mais non suffisant pour
  `RECOMMEND_GEOMETRY_ADJUSTMENT` dans la présente version ;
- aucun niveau n'est calculé par moyenne ou score global.

## 7. Matrice de décision

Les variables sont :

- `G` : géométrie et état initial complets ;
- `E` : niveau de preuve ;
- `C` : conflit causal présent ;
- `F` : déplacement physiquement faisable ;
- `V` : protocole de validation disponible ;
- `M` : validation multi-position conforme ;
- `H` : seuils correctifs humains approuvés.
- `A` : plan déterministe d'acquisition de preuve disponible.

Les règles sont évaluées dans cet ordre :

| Priorité | Condition | Décision | Motif principal |
| ---: | --- | --- | --- |
| 1 | hypothèse SBIR contredite | `NO_ACTION` | `INSUFFICIENT_CAUSAL_EVIDENCE` |
| 2 | `G = false` | `REQUEST_MORE_EVIDENCE` | motif géométrique précis |
| 3 | `C = true` | `REQUEST_MORE_EVIDENCE` | `CONFLICTING_CAUSAL_HYPOTHESES` |
| 4 | `E ∈ {LEVEL_0, LEVEL_1}` et `A = true` | `REQUEST_MORE_EVIDENCE` | `INSUFFICIENT_CAUSAL_EVIDENCE` |
| 5 | `E ∈ {LEVEL_0, LEVEL_1}` et `A = false` | `NO_ACTION` | `INSUFFICIENT_CAUSAL_EVIDENCE` |
| 6 | `F = false` | `REQUEST_MORE_EVIDENCE` | `INSUFFICIENT_PHYSICAL_CLEARANCE` |
| 7 | `V = false` | `REQUEST_MORE_EVIDENCE` | `MISSING_VALIDATION_PROTOCOL` |
| 8 | `E ∈ {LEVEL_2, LEVEL_3}` et préconditions complètes | `PROPOSE_GEOMETRY_EXPERIMENT` | aucun |
| 9 | `E = LEVEL_4` et `M = false` | `REQUEST_MORE_EVIDENCE` | `MULTI_POSITION_EVIDENCE_REQUIRED` |
| 10 | `E = LEVEL_4`, `M = true`, `H = false` | `NO_ACTION` | `CORRECTIVE_THRESHOLDS_NOT_APPROVED` |
| 11 | `E = LEVEL_4`, `M = true`, `H = true`, critères favorables et aucun critère adverse | `RECOMMEND_GEOMETRY_ADJUSTMENT` | aucun |

La ligne 11 est spécifiée comme frontière future mais reste inatteignable dans
le MVP, car `H = false` tant que les décisions de la section 20 ne sont pas
approuvées.

## 8. Expérience et recommandation

### 8.1 Expérience géométrique

Une expérience est un test borné destiné à acquérir une preuve causale. Elle :

- DOIT conserver `causality_status = NOT_ESTABLISHED` ;
- DOIT être liée à `protocol.temporary_move_speaker.v1` ou à un protocole
  ultérieur explicitement compatible ;
- DOIT modifier uniquement `LOUDSPEAKER_POSITION` ;
- DOIT exiger L, R et L+R ;
- DOIT permettre un rollback ;
- NE DOIT PAS employer les termes « position optimale », « correction
  garantie » ou équivalent.

### 8.2 Recommandation corrective

Une recommandation est une modification soutenue par une intervention
contrôlée antérieure. Elle exige :

- `LEVEL_4` ;
- un résultat reproductible ;
- une comparaison multi-position ;
- l'absence de conflit causal ;
- l'absence de critère adverse ;
- des seuils de succès et de dégradation approuvés ;
- une validation de retour à la baseline ;
- une portée explicitement limitée à la campagne validée.

Le MVP NE DOIT PAS produire `RECOMMEND_GEOMETRY_ADJUSTMENT`. Il se limite à
`PROPOSE_GEOMETRY_EXPERIMENT`, `REQUEST_MORE_EVIDENCE` et `NO_ACTION`.

## 9. Calcul de la plage de déplacement

### 9.1 Sources admissibles

Une amplitude PEUT provenir :

1. d'un `proposed_displacement_m` positif et fini porté par un protocole ou une
   proposition source ;
2. de la politique opérationnelle de 5 cm de
   `LoudspeakerPositioningExperimentEngine`, uniquement comme premier pas
   exploratoire et avec la provenance `OPERATIONAL_FIVE_CM_POLICY` ;
3. d'une plage approuvée par une future règle scientifique.

Le moteur NE DOIT PAS déduire une amplitude corrective exacte de la seule
formule SBIR.

### 9.2 Représentation MVP

Le MVP représente un déplacement source comme :

```text
minimum_m = source_displacement_m
maximum_m = source_displacement_m
step_m = source_displacement_m
unit = m
```

La politique de 5 cm peut donc produire un unique point expérimental
réversible. Elle ne constitue ni une plage scientifique ni une recommandation.

Un balayage de plusieurs points exige :

- une borne minimale approuvée ;
- une borne maximale approuvée ;
- un pas approuvé ;
- un plafond de sécurité ;
- un dégagement validé dans chaque direction ;
- un arrondi explicite au pas.

Ces valeurs sont `HUMAN_APPROVAL_REQUIRED`. Sans elles, aucun balayage
multi-point ne doit être généré.

### 9.3 Faisabilité

Pour chaque delta :

- les nouvelles coordonnées doivent rester dans la pièce ;
- la distance minimale à toute contrainte déclarée doit être respectée ;
- les deux enceintes doivent recevoir exactement le même delta `x` ;
- aucune autre coordonnée ou orientation ne doit changer ;
- une valeur non réalisable est supprimée de l'ensemble candidat ;
- si l'ensemble devient vide, la décision est `REQUEST_MORE_EVIDENCE`.

## 10. Direction du déplacement

La seule fréquence d'annulation NE PERMET PAS de choisir avec certitude
`MOVE_FORWARD` ou `MOVE_BACKWARD`. Les deux directions déplacent la fréquence
prédite et peuvent produire des effets adverses différents.

Une direction unique PEUT être utilisée seulement lorsqu'elle est fournie par
une source structurée compatible et que sa provenance est conservée.

Sinon :

```text
TEST_BOTH_DIRECTIONS
```

signifie deux essais séparés et ordonnés :

1. partir de la position initiale ;
2. tester un delta dans une direction ;
3. mesurer ;
4. revenir à la position initiale et vérifier le rollback ;
5. tester le delta opposé ;
6. mesurer ;
7. revenir à la position initiale.

Les deux directions ne constituent jamais deux variables simultanées. Si le
dégagement manque dans une direction, le moteur PEUT tester uniquement la
direction explicitement faisable, mais NE DOIT PAS en déduire qu'elle est
corrective. Si aucune direction n'est faisable, il refuse.

## 11. Protocole expérimental

Le protocole minimal DOIT :

1. enregistrer les identifiants et coordonnées initiales des deux enceintes ;
2. enregistrer position d'écoute, orientations et configuration contrôlée ;
3. capturer une baseline L, R et L+R ;
4. vérifier la validité et la répétabilité minimale de la baseline ;
5. appliquer le même delta `x` aux deux enceintes ;
6. mesurer physiquement et consigner les coordonnées candidates ;
7. conserver `y`, `z`, écartement, orientations, microphone, niveau, chaîne de
   mesure et pièce ;
8. répéter L, R et L+R avec les mêmes paramètres ;
9. comparer la bande cible et les observables de contrôle ;
10. appliquer les critères d'arrêt avant tout pas suivant ;
11. revenir à la position initiale ;
12. refaire une mesure de rollback ;
13. classer le résultat `FAVORABLE`, `ADVERSE`, `UNCHANGED` ou
    `INCONCLUSIVE`.

Les mesures sont reproductibles seulement si :

- chaque position et chaque variable contrôlée sont traçables ;
- le nombre de répétitions atteint la valeur approuvée ;
- les répétitions respectent la tolérance approuvée ;
- les fichiers sont associés sans ambiguïté à leur état géométrique ;
- le rollback retrouve la baseline dans la tolérance approuvée.

Le nombre de répétitions et les tolérances sont
`HUMAN_APPROVAL_REQUIRED`.

## 12. Critères de succès

Une position candidate ne peut être qualifiée de meilleure que si tous les
critères obligatoires approuvés sont satisfaits.

Les dimensions à évaluer séparément sont :

- profondeur du creux dans la bande cible ;
- largeur du défaut ;
- déplacement de sa fréquence ;
- répétabilité des mesures ;
- stabilité sur plusieurs positions ;
- cohérence entre gauche et droite ;
- absence de dégradation excessive hors bande ;
- absence de dégradation des observables de contrôle déclarés.

Aucun score composite n'est autorisé. Le résultat DOIT conserver chaque
dimension et chaque seuil appliqué.

La présente spécification ne fixe pas :

- la réduction minimale de profondeur ;
- la réduction minimale de largeur ;
- la tolérance de fréquence ;
- la dégradation maximale hors bande ;
- la cohérence minimale entre canaux ;
- le nombre de positions ou répétitions.

Ces paramètres sont `HUMAN_APPROVAL_REQUIRED`. Par conséquent, le MVP peut
constater et présenter les différences, mais pas déclarer une correction
validée.

## 13. Critères d'échec et rollback

Le rollback est obligatoire lorsque :

- aucune amélioration n'est observée ;
- l'amélioration n'est pas reproductible ;
- un bénéfice local accompagne une dégradation plus forte ;
- les canaux gauche et droit divergent au-delà du seuil approuvé ;
- une position est physiquement impossible ;
- une mesure est invalide ;
- l'hypothèse SBIR est infirmée ;
- un critère d'arrêt est déclenché ;
- le résultat est `INCONCLUSIVE`.

Le rollback DOIT :

1. restaurer les coordonnées initiales des deux enceintes ;
2. restaurer toutes les variables contrôlées ;
3. enregistrer les coordonnées restaurées ;
4. capturer une mesure de contrôle ;
5. signaler explicitement tout échec de restauration.

Un échec de rollback interdit toute recommandation et produit
`REQUEST_MORE_EVIDENCE`.

## 14. Multi-position

Une expérience mono-position est autorisée pour discriminer initialement une
hypothèse locale. Elle NE PEUT PAS produire une correction validée.

Le multi-position est obligatoire pour
`RECOMMEND_GEOMETRY_ADJUSTMENT`, parce qu'un déplacement peut améliorer un
point tout en dégradant la zone d'écoute. La campagne DOIT :

- utiliser des positions déclarées et reproductibles ;
- conserver le même protocole à chaque position ;
- inclure la position d'écoute de référence ;
- conserver séparément chaque résultat ;
- ne pas réduire les positions à une moyenne qui masque une dégradation.

Le nombre minimal et la disposition des positions sont
`HUMAN_APPROVAL_REQUIRED`.

## 15. Conflits scientifiques

| Conflit | Comportement |
| --- | --- |
| Hypothèse modale concurrente | `REQUEST_MORE_EVIDENCE` jusqu'à discrimination |
| Réflexion latérale concurrente | `REQUEST_MORE_EVIDENCE` |
| Plusieurs creux sans cible unique | `REQUEST_MORE_EVIDENCE` |
| Réponses gauche/droite incompatibles | refuser le mouvement symétrique |
| Géométrie asymétrique | autoriser seulement si le même delta est faisable et les deux corrélations sont éligibles ; sinon refuser |
| Effets contradictoires selon les positions | `REQUEST_MORE_EVIDENCE`, jamais arbitrage implicite |
| Deux directions également plausibles | `TEST_BOTH_DIRECTIONS` avec rollback intermédiaire |
| Action moderne bloquée mais recommandation historique positive | conserver le blocage moderne ; aucun fallback |

Un conflit NE DOIT PAS être résolu par priorité implicite, score global, ordre
de collection ou formulation de l'Advisor.

## 16. Motifs de blocage

| Code | Condition exacte | Décision | Action suivante |
| --- | --- | --- | --- |
| `MISSING_ROOM_GEOMETRY` | aucun `RoomGeometry` | `REQUEST_MORE_EVIDENCE` | acquérir la géométrie |
| `MISSING_FRONT_WALL_REFERENCE` | aucun candidat ne référence le mur avant | `REQUEST_MORE_EVIDENCE` | identifier la surface et les trajets |
| `MISSING_SPEAKER_COORDINATES` | moins de deux enceintes ou coordonnées absentes | `REQUEST_MORE_EVIDENCE` | mesurer les deux positions |
| `INCONSISTENT_UNITS` | unité absente ou incompatible avec les mètres | `REQUEST_MORE_EVIDENCE` | corriger la déclaration |
| `INVALID_SPEAKER_SYMMETRY` | le même delta ne peut pas être appliqué aux deux enceintes | `REQUEST_MORE_EVIDENCE` | lever la contrainte ou changer de cas d'usage |
| `INSUFFICIENT_FREQUENCY_LOCALIZATION` | creux/bande non associé sans ambiguïté | `REQUEST_MORE_EVIDENCE` | répéter ou affiner la mesure |
| `INSUFFICIENT_CAUSAL_EVIDENCE` | niveau inférieur à `LEVEL_2` | `REQUEST_MORE_EVIDENCE` si un plan déterministe existe, sinon `NO_ACTION` | suivre le plan discriminant disponible |
| `CONFLICTING_CAUSAL_HYPOTHESES` | hypothèse concurrente non discriminée | `REQUEST_MORE_EVIDENCE` | exécuter une discrimination |
| `INSUFFICIENT_PHYSICAL_CLEARANCE` | au moins une position candidate est irréalisable et aucune ne reste | `REQUEST_MORE_EVIDENCE` | déclarer les contraintes ou réduire une plage approuvée |
| `MISSING_VALIDATION_PROTOCOL` | L/R/L+R, contrôles ou rollback absents | `REQUEST_MORE_EVIDENCE` | compléter le protocole |
| `NON_REPRODUCIBLE_OBSERVATION` | répétitions hors tolérance approuvée | `REQUEST_MORE_EVIDENCE` | répéter la baseline |
| `MULTI_POSITION_EVIDENCE_REQUIRED` | tentative de recommandation avec mono-position seulement | `REQUEST_MORE_EVIDENCE` | exécuter une campagne multi-position |
| `UNSUPPORTED_GEOMETRY` | modèle non rectangulaire ou surface non supportée | `REQUEST_MORE_EVIDENCE` | aucune extrapolation ; fournir un modèle supporté |
| `MISSING_INITIAL_POSITION_REFERENCE` | état initial non enregistrable | `REQUEST_MORE_EVIDENCE` | enregistrer la baseline géométrique |
| `MISSING_SPEAKER_ORIENTATION` | orientation non contrôlable | `REQUEST_MORE_EVIDENCE` | documenter l'orientation |
| `MISSING_ADJUSTMENT_MAGNITUDE` | aucune amplitude source et politique opérationnelle non autorisée | `REQUEST_MORE_EVIDENCE` | fournir un protocole borné |
| `CORRECTIVE_THRESHOLDS_NOT_APPROVED` | critères correctifs humains absents | aucune recommandation ; expérience seulement | revue scientifique |
| `ROLLBACK_VALIDATION_FAILED` | état initial non restauré ou non vérifié | `REQUEST_MORE_EVIDENCE` | restaurer et revalider |

Les codes peuvent se cumuler dans un ordre stable. Aucun code ne doit être
remplacé par un message libre comme unique trace.

## 17. Sortie normative attendue

Structure minimale :

```text
decision
target
axis
direction
range
step
units
initial_position_reference
rationale
evidence_level
supporting_observations
supporting_hypotheses
supporting_action_ids
supporting_weight_ids
source_positioning_proposal_id
expected_effect
validation_plan
rollback_plan
blocked_reasons
scientific_status
applied_rule_ids
```

### Champs par décision

| Champ | `NO_ACTION` | `REQUEST_MORE_EVIDENCE` | `PROPOSE_GEOMETRY_EXPERIMENT` | `RECOMMEND_GEOMETRY_ADJUSTMENT` |
| --- | :---: | :---: | :---: | :---: |
| `decision`, `evidence_level`, `rationale`, `scientific_status` | requis | requis | requis | requis |
| références de preuve | si disponibles | requises si acquisition ciblée | requises | requises |
| `blocked_reasons` | selon cause | requis | vide | vide |
| cible, axe, direction, amplitude, unité | absents | absents | requis | requis |
| position initiale, validation, rollback | absents | selon plan suivant | requis | requis |
| effet attendu | absent ou limité | absent | hypothèse à tester | effet déjà validé et borné |
| règle corrective approuvée | absente | absente | absente | requise |

Pour une décision négative, cible, direction et amplitude applicables DOIVENT
être absentes.

## 18. Invariants scientifiques

1. Aucune expérience positive sans géométrie complète pour ce cas.
2. Aucune valeur sans unité et provenance.
3. Aucun déplacement sans position initiale.
4. Aucun déplacement irréversible.
5. Une seule variable modifiée : translation `x` commune aux deux enceintes.
6. Aucune modification de `y`, `z`, orientation, écartement ou position
   d'écoute.
7. Aucune affirmation d'amélioration pour une expérience.
8. Aucune recommandation issue de l'Advisor.
9. Mêmes entrées et même version de règles, même décision.
10. Tout refus est associé à un code explicite.
11. Toute recommandation est validable et reliée à une validation antérieure.
12. Aucun score global ne masque une dimension adverse.
13. Aucune contradiction n'est supprimée.
14. Aucune valeur ou direction n'est inventée.
15. Une action bloquée en amont reste bloquante.
16. Une recommandation historique ne fournit aucun fallback silencieux.
17. Toute expérience possède un rollback mesuré.
18. Une recommandation corrective exige du multi-position.

## 19. Cas de test normatifs

| Cas | Entrées essentielles | Décision | Motifs / sortie |
| ---: | --- | --- | --- |
| 1 | géométrie absente | `REQUEST_MORE_EVIDENCE` | `MISSING_ROOM_GEOMETRY` |
| 2 | une seule coordonnée d'enceinte | `REQUEST_MORE_EVIDENCE` | `MISSING_SPEAKER_COORDINATES` |
| 3 | fréquence historique compatible, aucun candidat géométrique | `REQUEST_MORE_EVIDENCE` | `LEVEL_1`, `MISSING_FRONT_WALL_REFERENCE` |
| 4 | deux corrélations conformes, géométrie et protocole complets | `PROPOSE_GEOMETRY_EXPERIMENT` | `LEVEL_2`, aucune promesse d'amélioration |
| 5 | candidat SBIR et hypothèse modale non discriminés | `REQUEST_MORE_EVIDENCE` | `CONFLICTING_CAUSAL_HYPOTHESES` |
| 6 | dégagement avant insuffisant, arrière disponible | `PROPOSE_GEOMETRY_EXPERIMENT` arrière seulement si source ou test bidirectionnel approuvé ; sinon demande de preuve | aucune direction corrective inférée |
| 7 | direction inconnue, deux dégagements valides, protocole bidirectionnel non approuvé | `REQUEST_MORE_EVIDENCE` | approbation du protocole `TEST_BOTH_DIRECTIONS` requise |
| 8 | amélioration répétée à la seule position de référence | aucune recommandation ; acquisition supplémentaire | `MULTI_POSITION_EVIDENCE_REQUIRED` |
| 9 | amélioration reproductible sur campagne multi-position, seuils correctifs absents | `NO_ACTION` | `LEVEL_4`, `CORRECTIVE_THRESHOLDS_NOT_APPROVED` |
| 10 | bande cible améliorée, autre bande dégradée au-delà du seuil approuvé | rollback | résultat `ADVERSE` |
| 11 | gauche améliorée, droite dégradée | rollback | divergence bilatérale, aucune correction symétrique |
| 12 | `LEVEL_4`, multi-position et tous seuils futurs approuvés | frontière future : `RECOMMEND_GEOMETRY_ADJUSTMENT` | règle corrective et portée obligatoires |
| 13 | Advisor favorable, action ou géométrie bloquée | décision déterministe négative inchangée | aucune valeur Advisor consommée |

Chaque test DOIT aussi vérifier :

- absence de mutation des objets sources ;
- ordre stable des références et motifs ;
- absence de réseau ;
- absence d'écriture implicite dans la campagne ;
- sortie identique sur deux exécutions.

## 20. Décisions humaines explicites

| Paramètre | Statut | Options à examiner |
| --- | --- | --- |
| Tolérance fréquentielle d'éligibilité | existante pour l'expérience : 15 % | conserver ou réviser par validation externe |
| Incertitude de prédiction | existante : 10 % | conserver ou réviser |
| Confiance géométrique | existante : 70/100 | conserver ou réviser |
| Profondeur minimale du défaut | `HUMAN_APPROVAL_REQUIRED` | seuil absolu, relatif ou dépendant de bande |
| Plage maximale de déplacement | `HUMAN_APPROVAL_REQUIRED` | limite globale et limite par dégagement |
| Pas minimal | 5 cm existe comme politique exploratoire | confirmer qu'il reste non scientifique |
| Nombre de répétitions | `HUMAN_APPROVAL_REQUIRED` | fixe ou dépendant de répétabilité |
| Seuil d'amélioration | `HUMAN_APPROVAL_REQUIRED` | profondeur et largeur séparées |
| Dégradation acceptable | `HUMAN_APPROVAL_REQUIRED` | par bande et observable |
| Nombre/disposition multi-position | `HUMAN_APPROVAL_REQUIRED` | protocole existant à qualifier |
| Niveau minimal de recommandation | `LEVEL_4` proposé, approbation requise | aucun niveau théorique seul |
| Domaine fréquentiel couvert | `HUMAN_APPROVAL_REQUIRED` | domaine où mesure et modèle sont fiables |
| Tolérance de rollback | `HUMAN_APPROVAL_REQUIRED` | géométrique et acoustique |
| Balayage bidirectionnel | `HUMAN_APPROVAL_REQUIRED` | ordre, plage et arrêt |

Ces valeurs NE DOIVENT PAS être déduites des fixtures, d'un résultat réel,
d'une constante opérationnelle ou du comportement d'un LLM.

## 21. Conclusion

```text
READY_FOR_EXPERIMENT_ONLY_IMPLEMENTATION
```

Le dépôt possède déjà les prérequis nécessaires pour projeter de manière
déterministe une expérience longitudinale symétrique limitée :

- repère et coordonnées structurés ;
- prédictions et corrélations SBIR au mur avant ;
- seuils existants d'éligibilité expérimentale ;
- hypothèse et protocole discriminant ;
- proposition temporaire, contrôlée et réversible ;
- provenance, blocages et validation L/R/L+R.

Le MVP peut donc produire `PROPOSE_GEOMETRY_EXPERIMENT`,
`REQUEST_MORE_EVIDENCE` ou `NO_ACTION`, en réutilisant les objets existants et
sans promettre d'amélioration.

Le MVP NE DOIT PAS produire `RECOMMEND_GEOMETRY_ADJUSTMENT`. Les seuils de
succès, critères adverses, exigences de répétabilité, plage de déplacement et
protocole multi-position restent soumis à approbation humaine. Leur absence
rend la recommandation corrective scientifiquement indéterminée, sans bloquer
l'implémentation d'une expérience conservatrice.
