# Causal Discrimination Contract

PR-029 ajoute une réduction déterministe des ambiguïtés causales au-dessus des
comparaisons PR-028. Elle ne réalise aucune analyse acoustique, ne crée aucune
session, itération, expérience ou étape et n’exécute aucune action physique.

## Activation explicite

```python
AcousticBrain().analyze(
    measurement_root="measurements",
    compare_experiments=True,
    analyze_causal_discrimination=True,
)
```

Sans `analyze_causal_discrimination=True`, aucun protocole causal n’est évalué
et la sortie historique reste inchangée. Le mode exige la comparaison PR-028.

## Étapes explicites

Une étape existe uniquement lorsqu’un manifest contient
`causal_protocol_step`. Les noms de dossiers et de fichiers ne produisent jamais
d’étape ou d’observation implicite.

```json
{
  "causal_protocol_step": {
    "protocol_code": "VERIFY_SPEAKER_ROOM_ASYMMETRY",
    "step_code": "STEP_2_SPEAKER_SWAP",
    "step_index": 2,
    "controlled_variable_codes": [
      "ROOM_SIDE",
      "SIGNAL_CHAIN_ASSIGNMENT",
      "MICROPHONE_POSITION"
    ],
    "changed_variable_codes": ["LOUDSPEAKER_ASSIGNMENT"],
    "unknown_variable_codes": [],
    "observation_codes": [
      "ANOMALY_MOVED_WITH_SWAPPED_LOUDSPEAKER"
    ]
  }
}
```

Les variables contrôlées, modifiées et inconnues sont disjointes. Une
observation de permutation n’est exploitable que lorsque la variable attendue
est modifiée et que les variables discriminantes exigées restent contrôlées.
Une déclaration incomplète ajoute `CONTROLLED_VARIABLES_INCOMPLETE` et ne réduit
aucune discrimination.

## Premier protocole

`VERIFY_SPEAKER_ROOM_ASYMMETRY` définit l’ordre de référence suivant :

1. `STEP_0_BASELINE` ;
2. `STEP_1_LEFT_RIGHT_REMEASUREMENT` ;
3. `STEP_2_SPEAKER_SWAP` ;
4. `STEP_3_SIGNAL_CHAIN_SWAP`.

Cette définition permet d’indiquer les étapes restantes. Elle ne les instancie
pas. Une recommandation désigne seulement le code de la prochaine étape
discriminante encore absente.

## Trajectoires et règles

Les trajectoires disponibles sont :

- `ANOMALY_FOLLOWS_LOUDSPEAKER` ;
- `ANOMALY_FOLLOWS_SIGNAL_CHAIN` ;
- `ANOMALY_REMAINS_WITH_ROOM_SIDE` ;
- `DISCRIMINATION_INCONCLUSIVE`.

Une trajectoire est `COMPATIBLE` ou `CONTRADICTED`. Il n’existe aucun statut
`CONFIRMED`. Son support est un score de couverture déterministe : nombre
d’observations structurées qui la soutiennent divisé par le nombre d’étapes
discriminantes contrôlées réalisées. Ce score n’est ni une probabilité ni une
estimation bayésienne.

Les seules réductions initiales sont celles encore ouvertes dans PR-028 :

- une permutation d’enceintes contrôlée peut réduire
  `LOUDSPEAKER_VS_ROOM_SIDE` ;
- une permutation de chaîne contrôlée peut réduire
  `SIGNAL_CHAIN_VS_ROOM_SIDE` ;
- `ANOMALY_MOVED_WITH_SWAPPED_SIGNAL_CHAIN` soutient la trajectoire de chaîne
  et contredit les trajectoires enceinte et côté de pièce ;
- `ANOMALY_REMAINED_WITH_LOUDSPEAKER_AFTER_SIGNAL_CHAIN_SWAP` soutient la
  trajectoire enceinte et contredit la trajectoire de chaîne ;
- deux discriminations pairwise structurées permettent de déduire la troisième
  sans confirmer aucune trajectoire.

Une observation contradictoire conserve ses preuves et place le protocole dans
l’état `CONTRADICTORY`. Une mesure non reproductible ajoute
`MEASUREMENT_VARIABILITY_VS_CAUSAL_PATTERN` au lieu de choisir une cause.

## Ambiguïtés et traçabilité

Le résultat conserve séparément :

- discriminations résolues ;
- discriminations restantes ;
- nouvelles ambiguïtés ;
- ambiguïtés perdues ;
- trajectoires compatibles et contradictoires ;
- règles appliquées et observations sources.

La chaîne de traçabilité est :

`manifest → étape → variables contrôlées/modifiées/inconnues → observation → règle → trajectoire → discrimination résolue/restante`.

Le presenter ne calcule aucune règle. Il projette ces structures dans la section
`DISCRIMINATION CAUSALE` et n’affiche la trace détaillée que sur demande.
