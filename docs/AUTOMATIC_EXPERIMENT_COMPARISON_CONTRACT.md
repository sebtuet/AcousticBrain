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

Les résultats sont `STRONGER`, `WEAKER`, `UNCHANGED`, `INCONCLUSIVE` ou
`CONTRADICTED`. PR-028 ne possède volontairement aucun outcome `CONFIRMED`.
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
