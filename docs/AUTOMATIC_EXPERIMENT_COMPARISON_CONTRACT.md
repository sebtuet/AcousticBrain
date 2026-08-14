# Automatic Experiment Comparison Contract

PR-028 relie la chronologie physique découverte par PR-027 aux snapshots et à
l’évolution d’hypothèse introduits par PR-025. Elle ne modifie aucun moteur
acoustique et ne crée ni `OptimizationSession`, ni `OptimizationIteration`, ni
expérience métier terminée.

## Activation

La comparaison est strictement explicite :

```python
AcousticBrain().analyze(
    measurement_root="measurements",
    compare_experiments=True,
)
```

Sans `compare_experiments=True`, le pipeline et les rapports historiques restent
inchangés. Une session PR-025 explicitement fournie peut seulement fournir un
protocole déjà déclaré ; elle n’est ni complétée ni mutée.

## Chronologie physique

La baseline est l’état initial. Les autres dossiers suivent l’ordre déterministe
de PR-027 (timestamp puis identifiant). Deux chemins sont conservés :

- local : `baseline → exp-001`, puis `exp-001 → exp-002` ;
- cumulatif : `baseline → exp-001`, puis `baseline → exp-002`.

Chaque bloc cumulatif rappelle explicitement son référentiel dans son titre
(`Comparaison cumulative depuis baseline`). Un résultat local et un résultat
cumulatif peuvent donc avoir des directions différentes sans être présentés
comme deux verdicts portant sur le même couple de mesures.

Un parent déclaré dans `manifest.json` est prioritaire pour le chemin local :

```json
{
  "comparison": {
    "parent_experiment_ids": ["baseline"],
    "source_protocol_id": "protocol.repeat-pair",
    "source_hypothesis_code": "ASYMMETRIC_SPEAKER_ROOM_INTERACTION",
    "declared_change_codes": ["LEFT_RIGHT_REMEASUREMENT"],
    "required_fact_codes": ["spatial.left_right.level_difference_abs_db"]
  }
}
```

Plusieurs parents, un parent inconnu ou postérieur produisent une comparaison
structurée non comparable. Le nom du dossier et les noms de fichiers n’ont
aucune signification causale.

## Comparabilité

Seuls des faits structurés possédant le même code, la même unité, la même
famille et la même sémantique sont comparés. Leur provenance, leur readiness et
leur seuil explicite sont conservés. Une analyse `BLOCKED`, une valeur absente,
une unité incompatible ou un fait requis manquant ne sont jamais compensés par
du texte ou une supposition. Une variation sous seuil est `UNCHANGED`.

Trois axes sont restitués séparément :

- évolution acoustique des faits ciblés par le protocole : `IMPROVED`,
  `DEGRADED`, `MIXED`, `UNCHANGED` ou `INCONCLUSIVE` ;
- évolution du soutien de l'hypothèse : `STRONGER`, `WEAKER`, `UNCHANGED`,
  `INCONCLUSIVE` ou `CONTRADICTED` ;
- résultat expérimental discriminant, lorsqu'une règle déclarée l'établit,
  par exemple `LOCAL_POSITION_EFFECT_SUPPORTED`.

PR-028 ne possède volontairement aucun outcome `CONFIRMED`.
Sans hypothèse ou protocole déclaré, la comparaison factuelle reste disponible,
mais l’évolution causale est `INCONCLUSIVE`.

## Limites causales

Une inférence ne dépasse jamais les changements contrôlés déclarés. Répéter les
mesures LEFT/RIGHT peut établir la reproductibilité d’un motif, mais laisse
notamment `LOUDSPEAKER_VS_ROOM_SIDE` et `LOUDSPEAKER_VS_SIGNAL_CHAIN` ouverts.
Seul un code de changement contrôlé correspondant, par exemple
`CONTROLLED_LOUDSPEAKER_SWAP`, retire la discrimination qu’il traite.

Les discriminations non résolues sont des données métier immuables. Le
presenter traduit leurs codes grâce à une table fixe ; il ne calcule ni delta,
ni outcome, ni causalité.

## Campagne modale multi-position

Une campagne confirmée par l'utilisateur utilise le protocole existant
`protocol.verify_modal_bass_persistence.v1`. AcousticBrain écrit ensuite les
déclarations structurées ; aucune édition manuelle du JSON n'est requise.

```python
ExperimentProtocolDeclarationService().confirm_modal_multi_position(
    "measurements",
    reference_experiment_id="exp-003",
    reference_parent_experiment_id="exp-002",
    listening_position_offsets_m={
        "exp-003": 0.0,
        "exp-004": -0.30,
        "exp-005": 0.30,
    },
)
```

Le service ne déduit jamais un déplacement depuis un nom de fichier. Il ne
fait que traduire les offsets explicitement confirmés, vérifie que les dossiers
existent et conserve les données techniques déjà présentes. La référence est
rattachée à son parent antérieur ; toutes les positions testées sont rattachées
directement à cette référence.

Une variation supérieure au seuil de comparaison Bass Decay existant produit
`BASS_DECAY_VARIES_BY_LISTENING_POSITION` et
`LOCAL_POSITION_EFFECT_SUPPORTED`. Elle ne réfute pas une composante modale
globale : `LOCAL_POSITION_EFFECT_VS_GLOBAL_MODE` reste ouverte. Une fois la
campagne déclarée, `MEASURE_MULTIPLE_POSITIONS` est affichée `COMPLETED` et le
candidat de planification porte `ALREADY_COMPLETED`.

### Synthèse de campagne

Les comparaisons locales restent disponibles, mais une campagne déclarée
produit également une synthèse indépendante : mesures et rôles, résultats
observés par branche, évolution acoustique de chaque position, meilleure valeur
existante, discriminations restantes et état de résolution. Les constats
`stable` et `réduit` ne sont donc jamais fusionnés sans indiquer la position qui
les produit.

La synthèse porte également un objectif stable, distingue visuellement les
conclusions établies des discriminations encore ouvertes et expose la prochaine
discrimination nécessaire. Celle-ci est dérivée des ambiguïtés restantes ; elle
ne déclenche aucune action physique et ne constitue pas à elle seule un candidat
éligible du planificateur.

Pour la campagne modale, l'état est :

- `INCOMPLETE` si la référence, une branche comparable ou le fait Bass Decay
  requis manque ;
- `INCONCLUSIVE` si la campagne est complète sans variation locale observée ;
- `PARTIALLY_RESOLVED` si un effet local est soutenu tandis que la composante
  modale globale reste non discriminée ;
- `RESOLVED` uniquement si les discriminations déclarées sont réellement
  levées.

La synthèse agrège exclusivement les `ExperimentFactDelta`, observations et
discriminations déjà produits. Elle ne relit aucun fichier de mesure et
n'ajoute aucune analyse acoustique. Le presenter traduit seulement les codes
calculés et ne produit ni métrique ni conclusion métier.

Si tous les candidats du planificateur sont inéligibles, le rapport expose les
raisons structurées de chaque exclusion (`ALREADY_COMPLETED`, `USER_DEFERRED`,
prérequis ou géométrie manquante) et distingue les recommandations actives pour
lesquelles aucun protocole planifiable n'existe encore.

## Traçabilité

Chaque comparaison conserve séparément son type local ou cumulatif et relie :

`dossier → hashes des fichiers → snapshot analysé → fait avant → fait après → delta → fait expérimental → hypothèse → évolution → discrimination`.

Les détails sont affichés uniquement avec
`detailed_comparison_traceability=True` ou avec un reporter configuré en mode
détaillé.

## Articulation des PR

- PR-025 fournit le snapshot structuré et l’évolution déterministe d’hypothèse ;
- PR-027 fournit les dossiers, imports, hashes, timestamps et manifests ;
- PR-028 orchestre les analyses indépendantes et projette les séquences locale
  et cumulative sans créer d’historique métier implicite.
