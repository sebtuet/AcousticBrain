# AcousticBrain — Project State

Ce document est un état descriptif de reprise. Il est non normatif, non
scientifique et ne constitue pas un audit. Il ne crée aucune capacité, aucune
Scientific Question et aucune règle. Il synthétise uniquement l'état déjà
établi et les décisions déjà figées.

## 1. Mission

AcousticBrain est un moteur déterministe de diagnostic acoustique fondé sur
des mesures. Le moteur déterministe est l'autorité. L'Advisor LLM est
optionnel, en lecture seule, et ne crée aucune connaissance scientifique.

L'objectif produit immédiat est de rendre la chaîne existante utilisable par
un utilisateur.

## 2. Catégories documentaires

- **Normatif** : prescrit.
- **Descriptif** : stabilise l'état observé.
- **Audit** : démontre un état sur un commit donné.

Les documents normatifs ne dépendent ni des documents descriptifs ni des
audits. `CAPABILITY_REGISTRY.md` est descriptif et reste hors de la chaîne
normative. Les audits sont non normatifs, historiques et attachés à l'état
qu'ils ont examiné.

## 3. Gouvernance scientifique figée

Le corpus comprend :

- `docs/scientific/SCIENTIFIC_CONTRACT.md`
- `docs/scientific/KNOWLEDGE_MODEL.md`
- `docs/scientific/EVIDENCE_MODEL.md`
- `docs/scientific/SCIENTIFIC_ASSERTION_CONTRACT.md`
- `docs/scientific/CAPABILITY_REGISTRY.md`

Jalon Git :
`0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8`

Message :
`docs(scientific): establish normative scientific governance`

Ce corpus est figé. Sa modification est autorisée uniquement par un mandat
explicite ou lorsqu'une insuffisance est démontrée.

Les Scientific Questions relèvent exclusivement de l'autorité scientifique.
Aucune Scientific Question ne doit être reconstruite depuis le code, le
registre ou les audits.

## 4. Audits scientifiques versionnés

Les audits versionnés sont :

- `docs/scientific/audits/2026-07-26_repository_scientific_audit.md`
- `docs/scientific/audits/2026-07-26_assertion_model_inventory.md`
- `docs/scientific/audits/2026-07-26_modern_chain_gap_analysis.md`

Jalon Git :
`cb74b2a354b40c2f363e49566b2babba2f0267af`

Message :
`docs(audit): record scientific governance assessments`

Branche :
`agent/scientific-audit-records`

Nature :
`AUDIT — NON NORMATIF`

Les anciens audits restent immuables. Un nouvel audit est requis lorsque le
code ou la base normative change. Une erreur factuelle doit être rectifiée de
façon traçable, jamais par réécriture silencieuse.

## 5. État technique observé

Le dépôt possède une chaîne déterministe existante :

```text
Mesures
→ Observations
→ Reasoning
→ Actions
→ Evidence Weighting
→ Evidence Acquisition
→ Advisor optionnel
```

Les cinq rapports correspondant aux étapes allant des observations aux plans
d'acquisition existent déjà. Le pipeline peut déjà produire toute cette
chaîne lorsque `synthesize_evidence_acquisition=True`.

Le CLI ne peut actuellement afficher qu'un rapport à la fois. Le principal
obstacle immédiat à l'utilisabilité est donc l'accessibilité du parcours
complet, et non l'absence du cœur scientifique.

## 6. Principes de développement

- Aucune nouvelle capacité scientifique ne peut être créée sans Scientific
  Question validée.
- Les travaux produit peuvent exposer des capacités existantes sans créer de
  nouvelle science.
- Les infrastructures transversales ne doivent être généralisées qu'après
  démonstration par plusieurs cas réels.
- Les Pull Requests doivent être petites, fermées, testables et réversibles.
- Aucun push, aucune Pull Request et aucune fusion ne sont autorisés sans
  mandat explicite.
- Une autorisation de commit ne vaut pas autorisation de publication.
- Aucun agent ne doit concevoir implicitement une nouvelle règle
  scientifique.

## 7. Objectif produit immédiat

Le parcours minimal recherché est :

1. validation des mesures ;
2. synthèse des problèmes observés ;
3. explication déterministe ;
4. actions applicables ou raisons précises de blocage ;
5. expériences recommandées pour lever les blocages ;
6. rapport lisible et exportable.

La première étape retenue est volontairement plus petite : exposer les cinq
rapports existants par une seule option CLI.

## 8. Prochain mandat prêt à exécuter

### Unified Deterministic Assessment Workflow

Branche de départ :

- `agent/scientific-audit-records`
- commit : `cb74b2a354b40c2f363e49566b2babba2f0267af`

Nouvelle branche :
`agent/unified-deterministic-assessment`

Objectif :
ajouter l'option CLI `--full-assessment`.

Ordre exact des sorties :

1. observations ;
2. reasoning ;
3. actions correctives ;
4. evidence weighting ;
5. plans d'acquisition.

Comportement autorisé :

- activer uniquement `synthesize_evidence_acquisition=True` ;
- utiliser la cascade existante ;
- déléguer aux cinq reporters existants ;
- ne pas activer l'Advisor ;
- ne réaliser aucun appel réseau ;
- ne créer aucun calcul, tri, filtrage, résumé ou interprétation.

Combinaisons interdites avec `--full-assessment` :

- `--observations`
- `--reasoning`
- `--actions`
- `--weighting`
- `--evidence-acquisition`
- `--advisor`

Fichiers autorisés :

- `main.py`
- `acousticbrain/report/__init__.py`
- `acousticbrain/report/full_assessment_console.py`
- `tests/test_main_cli.py`
- `tests/test_full_assessment_console.py`

Message de commit prévu :
`feat(cli): add unified deterministic assessment workflow`

Ce mandat est prêt, mais il n'est pas exécuté par le présent travail. Aucun
fichier de code ne doit être modifié sur cette branche documentaire.

## 9. Démarrage d'une nouvelle conversation

> Voici l'état officiel actuel d'AcousticBrain.
> Utilise `docs/PROJECT_STATE.md` comme référence descriptive de cette
> conversation. Ne modifie pas les jalons figés. Le prochain travail autorisé
> est uniquement celui décrit dans la section « Prochain mandat prêt à
> exécuter », après confirmation explicite de son exécution.
