# Controlled reflection candidate verification planning contract

PR-036 décrit comment un candidat de réflexion PR-035 pourrait être vérifié
dans une comparaison contrôlée. Elle ne déclenche aucune mesure, ne confirme
aucune cause et ne modifie aucune décision existante.

## Pure dependency contract

`ControlledReflectionVerificationPlanningAnalysis` est exactement la fonction
déterministe :

```text
g(MaterialAwareReflectionCandidateAnalysis)
```

Elle n’accepte aucune autre entrée et n’accède à aucun service caché. Elle ne
lit ni `RoomDescription`, ni géométrie, ni événement ETC, ni catalogue, ni
mesure, ni hypothèse, ni recommandation, ni plan expérimental, ni protocole, ni
LLM. Elle ne recalcule aucun score et ne modifie pas son entrée.

La nouvelle analyse reste une feuille du graphe. Seuls la présentation du
rapport et le graphe de traçabilité consomment son résultat. Le raisonnement
acoustique, `ExperimentPlanningAnalysis`, les protocoles et les recommandations
ne dépendentent pas de PR-036.

## Existing candidates and stable ordering only

Une proposition est créée uniquement pour un candidat PR-035 dont la géométrie
est `ACCEPTED` et qui possède déjà un rang, une corrélation et un événement
observé. Un candidat `REJECTED` reste exclu avec la raison structurée
`GEOMETRICALLY_REJECTED`.

L’ordre des propositions est exactement le rang informatif PR-035. PR-036 ne
crée ni score, ni priorité, ni arbitrage supplémentaire. Les identifiants sont
reproductibles :

```text
reflection_verification_proposal.<source_candidate_id>
```

Les égalités et l’ordre sont donc déjà résolus par PR-035. L’ordre d’itération
des entrées ne change pas la sortie.

## Controlled comparison description

Chaque proposition décrit deux conditions :

- `UNMASKED_REFERENCE` ;
- `TEMPORARY_MASK_APPLIED`.

La seule variable annoncée comme modifiée est `TEMPORARY_MASK_STATE`. Les
positions du microphone et des enceintes, l’orientation des enceintes,
l’assignation de chaîne et le niveau de mesure restent explicitement contrôlés.

Les observables référencés sont limités au délai et au niveau relatif de
l’événement ETC existant ainsi qu’à l’erreur temporelle géométrique existante.
Les résultats attendus restent deux issues concurrentes :

- `REFLECTION_DECREASES_AFTER_MASKING` ;
- `REFLECTION_REMAINS_UNCHANGED_AFTER_MASKING`.

Ces codes décrivent ce qu’une future comparaison devrait observer. PR-036 ne
produit aucun de ces faits et ne prescrit ni matériau, ni dimensions, ni
placement détaillé du masque.

## Provenance separation

Une proposition conserve séparément :

- les identifiants immuables du candidat, du trajet, de la corrélation, de
  l’événement et de la cible ;
- les codes de preuves provenant de PR-035 ;
- les codes de provenance physique et descriptive provenant de PR-035 ;
- les règles de planification descriptive propres à PR-036 ;
- les variables contrôlées, la variable modifiée et les observables.

Le graphe de traçabilité relie la proposition au candidat et aux preuves déjà
existantes. Il n’ajoute aucun lien d’hypothèse, de protocole, d’action, de
recommandation ou de candidat recommandé.

## No execution, causality or decision impact

Chaque proposition impose :

```text
execution_status = NOT_EXECUTED
causality_status = NOT_ESTABLISHED
eligibility_impact = NONE
recommendation_impact = NONE
```

PR-036 ne rend aucun protocole éligible, ne modifie aucun score acoustique, ne
crée aucune recommandation de traitement, ne confirme aucune surface et ne
fait aucune inférence causale. L’exécution réelle et l’interprétation d’une
future comparaison appartiennent à une évolution ultérieure explicitement
contractualisée.
