# Deterministic loudspeaker positioning experiment proposal contract

## Statut et utilisateur cible

Ce contrat décrit une proposition destinée à un utilisateur capable de déplacer
une enceinte et de refaire des mesures REW L, R et L+R. La proposition est une
expérience contrôlée, informative, bornée et réversible. Elle ne constitue ni
une position optimale, ni une correction définitive, ni une amélioration
garantie.

## Audit préalable de `develop`

L'audit a été réalisé sur `develop` synchronisé au merge commit PR-043
`6a50013b926478d400aff00e2c57d841ebd85879`. Le worktree était propre et
`python main.py` produisait un rapport complet sans déplacement précis.

Les sources existantes ont les propriétés suivantes :

| Source | Cible exploitable | Direction | Distance | Blocage observé |
|---|---|---|---|---|
| `CHECK_STEREO_PLACEMENT` | paire d'enceintes | aucune | aucune | le score stéréo ne démontre aucun sens de déplacement |
| `TEST_SPEAKER_DISTANCE` | surface seulement | aucune | distance actuelle seulement | l'enceinte à déplacer n'est pas identifiée |
| `VERIFY_SPEAKER_ROOM_ASYMMETRY` | interaction G/D et pièce | aucune | aucune | décision utilisateur `DEFERRED` dans le cas réel |
| candidat planifié `VERIFY_SBIR_PLACEMENT` | enceinte identifiée si la géométrie précise existe | aucune | `proposed_displacement_m = 0.10` | la géométrie et une direction explicite sont nécessaires |
| propositions contrôlées PR-036 | surface ou région à masquer | sans objet | sans objet | elles ne sont pas des déplacements d'enceinte |
| déclaration PR-043 | variables modifiées et contrôlées d'une expérience | aucune direction implicite | aucune amplitude implicite | elle décrit une expérience; elle ne doit pas inventer la suivante |

La géométrie du cas réel `exp-006` est `LEGACY_ROOM`, avec zéro enceinte
positionnée, zéro orientation et aucune scène de propagation. La planification
réelle marque l'asymétrie `USER_DEFERRED`, le protocole modal
`ALREADY_COMPLETED`, et les pistes SBIR/réflexion
`GEOMETRY_PARAMETER_MISSING`. Aucune proposition PR-036 n'existe. Le rendu
existant conclut donc honnêtement qu'aucune expérience de positionnement fiable
ne peut être proposée.

Une proposition immédiate sur ce cas obligerait à inventer au minimum la cible
individuelle, la direction, la relation géométrique avec une paroi et, hors du
cas SBIR géométrique, la distance. PR-044 interdit ces inventions.

La recherche contradictoire a trouvé une amplitude existante de 10 cm dans le
protocole SBIR géométrique. Cette amplitude est conservée lorsqu'elle est
présente dans la source. La politique opérationnelle de 5 cm ne s'applique
qu'à une source par ailleurs éligible et déjà orientée qui ne fournit aucune
amplitude.

## Principe de sélection

La projection examine, dans l'ordre :

1. le candidat de positionnement déjà sélectionné par la planification;
2. une proposition contrôlée de positionnement déjà structurée;
3. une recommandation active, unique à sa priorité, dont la cible et la
   direction sont explicitement structurées;
4. l'absence de proposition.

Elle ne réordonne pas les recommandations sources et ne sélectionne jamais le
premier élément d'une égalité. Une décision utilisateur différée bloque la
source correspondante.

## Éligibilité

Une proposition positive exige simultanément une source active de placement,
une cible non ambiguë, une direction explicite, une seule variable modifiée,
les contrôles protocolaires complets, les mesures L/R/L+R, au moins un
observable existant, une géométrie suffisante lorsque la source en dépend, une
priorité non ex æquo et une expérience réversible. Tout manque produit un statut
négatif explicite sans cible, direction ni distance proposées.

## Cibles et directions

Les seules cibles sont `LEFT_SPEAKER`, `RIGHT_SPEAKER` et `BOTH_SPEAKERS`.
Les seules directions sont `FORWARD`, `BACKWARD`, `INWARD` et `OUTWARD`.
`FORWARD` et `BACKWARD` utilisent l'axe longitudinal; `INWARD` et `OUTWARD`
utilisent l'axe latéral. Aucun score acoustique n'est converti en direction.

## Politique de distance

Une amplitude positive déjà structurée est conservée. À défaut, le pas initial
est exactement `0.05 m`. Ces 5 cm sont une granularité de protocole
exploratoire, pas une déduction acoustique. Le pas est petit, mesurable et
réversible; aucun second pas n'est généré avant comparaison de la nouvelle
mesure.

## Limites causales

Toute proposition conserve `causality_status = NOT_ESTABLISHED`. Les
observables indiquent uniquement ce qu'AcousticBrain comparera. Le résultat
peut être favorable, défavorable, inchangé ou inconclusif. Aucun score,
classement, statut d'hypothèse ou recommandation source n'est modifié.

## Contrat des variables contrôlées

La variable testée est toujours `LOUDSPEAKER_POSITION`. Les contrôles minimaux
sont `LISTENING_POSITION`, `LOUDSPEAKER_ORIENTATION`, `MEASUREMENT_LEVEL`,
`MICROPHONE_POSITION`, `REW_MEASUREMENT_PARAMETERS` et
`ROOM_CONFIGURATION`. Pour une seule enceinte, `OTHER_LOUDSPEAKER_POSITION`
est ajouté. Pour un déplacement longitudinal, `LOUDSPEAKER_SEPARATION` est
également contrôlé. Pour `BOTH_SPEAKERS`,
`LOUDSPEAKER_PAIR_SYMMETRY` impose un déplacement identique et symétrique. Une
valeur n'est jamais dite contrôlée parce qu'elle paraît
probable : elle doit appartenir au contrat de la proposition.

## Mesures et observables attendus

Chaque proposition impose une nouvelle acquisition `L`, `R` et `L+R`, dans les
mêmes conditions déclarées. Les observables standard réutilisent les faits
existants `global.domain.stereo.score`, `bass_decay.maximum_decay_time_s`,
`etc.channel_specific_event_count` et
`spatial.left_right.level_difference_abs_db`; les observables du candidat ou de
la recommandation source sont ajoutés sans remplacement. Le moteur ne crée ni
métrique acoustique, ni seuil de réussite. La comparaison ultérieure peut
constater un résultat favorable, défavorable, inchangé ou inconclusif.

## Provenance champ par champ

La cible et la direction portent la provenance `SOURCE_PARAMETER`. La distance
porte `SOURCE_PARAMETER` lorsqu'elle existe ou
`OPERATIONAL_FIVE_CM_POLICY` pour le pas exploratoire. Les contrôles portent
`PR044_PROTOCOL_CONTRACT`, les observables
`PR044_EXISTING_COMPARISON_FACTS_AND_SOURCE_CODES`, et la limite causale
`PR044_CAUSAL_LIMIT`.
L'identifiant est stable pour une même source, cible, direction et distance.

## Statuts et absence de proposition

Les statuts publics sont `ELIGIBLE`, `NOT_ELIGIBLE`, `AMBIGUOUS`,
`BLOCKED_BY_USER_DECISION`, `MISSING_GEOMETRY`, `MISSING_DIRECTION` et
`ALREADY_PLANNED`. Un statut négatif ne contient jamais de proposition
partielle. En particulier :

- une direction absente produit `MISSING_DIRECTION`;
- une géométrie exigée mais absente produit `MISSING_GEOMETRY`;
- une égalité de priorité produit `AMBIGUOUS`;
- une source uniquement différée produit `BLOCKED_BY_USER_DECISION`;
- une source sans cible, sans mesures L/R/L+R ou sans observable est
  `NOT_ELIGIBLE`.

## Relation avec PR-036 à PR-043

PR-036 demeure la source des expériences de masquage de réflexion : PR-044 ne
les convertit pas en déplacement. PR-040 demeure la source de priorisation,
sans être recalculée. PR-041 et PR-042 ne font que présenter la proposition ou
son blocage. PR-043 reste l'unique contrat de déclaration expérimentale : une
proposition PR-044 n'est pas une expérience réalisée tant que l'utilisateur ne
l'a pas explicitement acceptée.

L'acceptation convertit la proposition en `CONTROLLED_INTERVENTION`, avec
`LOUDSPEAKER_POSITION` comme seule variable modifiée, les contrôles de la
proposition, la référence choisie et une provenance contenant le
`proposal_id`. Elle ne crée ni résultat, ni score, ni causalité.

## Acceptation CLI explicite

La commande suivante est la seule écriture ajoutée par PR-044 :

```bash
python -m acousticbrain.commands.accept_positioning_proposal \
  measurements \
  --proposal-id loudspeaker_positioning_proposal.v1.example \
  --experiment exp-007 \
  --reference exp-006 \
  --note "Pas expérimental réversible accepté par l'utilisateur."
```

La commande revalide que le `proposal_id` est actuellement éligible avant de
créer le dossier cible et son `manifest.json`. Elle ne modifie aucun fichier de
mesure. Sans invocation explicite, l'analyse et le rapport restent strictement
en lecture/projection et n'acceptent aucune proposition.

## Cas réel `exp-006`

Avec la déclaration de répétition PR-043, la géométrie legacy et les données
actuelles, `exp-006` ne fournit aucune direction structurée de déplacement.
PR-044 doit donc afficher `MISSING_DIRECTION` (ou un blocage plus amont si la
source est différée), sans cible, amplitude ou déplacement inventés. Ce cas est
une validation négative attendue, pas un échec de proposition.
