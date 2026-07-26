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
d'acquisition existent. Le pipeline peut produire toute cette chaîne lorsque
`synthesize_evidence_acquisition=True`.

Le CLI expose désormais ces cinq rapports par l'option `--full-assessment`,
dans l'ordre suivant :

1. observations ;
2. reasoning ;
3. actions correctives ;
4. evidence weighting ;
5. plans d'acquisition.

Cette option utilise la cascade déterministe existante et n'active pas
l'Advisor.

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

Le parcours minimal recherché reste :

1. validation des mesures ;
2. synthèse des problèmes observés ;
3. explication déterministe ;
4. actions applicables ou raisons précises de blocage ;
5. expériences recommandées pour lever les blocages ;
6. rapport lisible et exportable.

La première étape produit, qui consistait à exposer les cinq rapports
existants par une seule option CLI, est terminée. La prochaine étape produit
n'est pas encore définie.

## 8. Dernier mandat produit terminé

### Unified Deterministic Assessment Workflow

Branche de départ :

- `agent/scientific-audit-records`
- commit : `cb74b2a354b40c2f363e49566b2babba2f0267af`

Branche d'implémentation :
`agent/unified-deterministic-assessment`

Commit d'implémentation :
`c4e698108070ea8c0552fc46cbec7b76edeb75b9`

Message :
`feat(cli): add unified deterministic assessment workflow`

État :

- implémenté ;
- testé ;
- publié dans la Draft PR
  [#39](https://github.com/sebtuet/AcousticBrain/pull/39) ;
- non fusionné à la date de cette mise à jour.

La PR #39 utilise une branche de publication propre issue de `develop`. Elle
contient un seul commit fonctionnel et les cinq fichiers autorisés.

Comportement établi :

- `--full-assessment` active uniquement
  `synthesize_evidence_acquisition=True` ;
- la cascade existante produit les cinq couches déterministes ;
- les cinq reporters historiques reçoivent le même objet `Report` ;
- leur ordre est observations, reasoning, actions correctives, evidence
  weighting, puis plans d'acquisition ;
- l'Advisor n'est pas activé ;
- aucun calcul, tri, filtrage, résumé, interprétation ou appel réseau
  supplémentaire n'est introduit.

Validations établies :

- tests CLI et reporter réussis ;
- tests ciblés de la chaîne moderne réussis ;
- suite complète : `1509 passed` ;
- `compileall` réussi ;
- `git diff --check` réussi ;
- sorties historiques inchangées byte-for-byte ;
- deux sorties `--full-assessment` identiques byte-for-byte.

## 9. Démarrage d'une nouvelle conversation

> Voici l'état officiel actuel d'AcousticBrain.
> Utilise `docs/PROJECT_STATE.md` comme référence descriptive de cette
> conversation. Ne modifie pas les jalons figés. Le dernier mandat produit est
> terminé et présent dans la Draft PR #39. Aucune prochaine étape produit
> n'est encore définie. N'invente aucun nouveau mandat scientifique ni aucune
> Scientific Question.
