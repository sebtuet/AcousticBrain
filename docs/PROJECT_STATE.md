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

La branche `develop` expose également le rapport complet dans un fichier texte
par l'option `--full-assessment-output PATH`. Le rendu est encodé une seule
fois en UTF-8, puis les mêmes octets sont écrits sur stdout et dans le fichier.
Un chemin existant n'est jamais écrasé et le fichier final est publié
atomiquement. Cette exposition n'ajoute aucune capacité scientifique, aucun
Advisor et aucun accès réseau.

La branche `develop` expose désormais aussi la readiness technique existante
par l'option `--analysis-readiness`. Ce mode affiche les expériences
découvertes avec leur état `READY` ou `INCOMPLETE`, puis les sept familles
d'analyse dans leur ordre existant, avec leurs statuts et les codes existants
des blocages et réserves. Il indique explicitement que ces statuts
n'établissent pas la validité scientifique et que `BLOCKED` ne signifie pas
que le pipeline a sauté le calcul.

La branche `develop` expose également une synthèse déterministe par l'option
`--assessment-summary`. Cette présentation utilise exclusivement les données
déjà projetées dans `Report` et distingue l'absence de données structurées
d'action d'une collection structurée présente sans action bloquée. Elle
n'ajoute aucune analyse, classification scientifique ou interprétation.

Le code de ces workflows produit est présent dans `develop`, mais pas dans
`main` à la date de cette mise à jour.

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
n'est pas encore définie. L'export texte déterministe de ce rapport complet
est également terminé. L'exposition de la readiness technique des analyses
est terminée. La synthèse déterministe destinée à l'utilisateur est également
terminée.

## 8. Mandats produit terminés

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
- publié initialement dans la PR
  [#39](https://github.com/sebtuet/AcousticBrain/pull/39) ;
- fusionné dans `develop` par le commit
  `ab0b815896798b7d9e4ed23ad0896f148da81cb2`.

La PR #39 utilisait une branche de publication propre issue de `develop`.
Elle contenait un seul commit fonctionnel et les cinq fichiers autorisés. Le
workflow n'est pas présent dans `main` à la date de cette mise à jour.

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

### Deterministic Full Assessment Text Export

Branche d'implémentation :
`agent/full-assessment-text-export`

Commit d'implémentation :
`16d9a22dfacd3fbb8842c4deb81a9a707bd7995f`

Message :
`feat(cli): export deterministic full assessment`

État :

- implémenté et testé ;
- publié dans la PR
  [#41](https://github.com/sebtuet/AcousticBrain/pull/41) ;
- fusionné dans `develop` par le commit
  `5e4bc76e9509e189a2bfbbe412f3f2aa57d68480` ;
- nouveau HEAD de `develop` :
  `5e4bc76e9509e189a2bfbbe412f3f2aa57d68480`.

Comportement établi :

- `--full-assessment-output PATH` exige `--full-assessment` ;
- le rapport complet est rendu une seule fois et encodé une seule fois en
  UTF-8 ;
- stdout et le fichier reçoivent exactement les mêmes octets ;
- un fichier existant n'est jamais écrasé ;
- le fichier final est publié atomiquement sans fichier final partiel ;
- aucune nouvelle capacité scientifique n'est créée ;
- l'Advisor n'est pas initialisé et aucun accès réseau n'est ajouté.

Validations établies :

- tests CLI et export réussis ;
- test réel en sous-processus de l'identité byte-for-byte réussi ;
- tests ciblés de la chaîne moderne réussis ;
- suite complète : `1525 passed` ;
- `compileall` réussi ;
- `git diff --check` réussi.

Cette fonctionnalité est présente dans `develop`, mais son code produit n'est
pas présent dans `main` à la date de cette mise à jour.

### Technical Analysis Readiness CLI

Branche d'implémentation :
`agent/analysis-readiness-cli`

Commit d'implémentation :
`0a64bf457172ba3cf703b5d613f8b13db5f58e5e`

Message :
`feat(cli): expose technical analysis readiness`

État :

- implémenté et testé ;
- publié dans la PR
  [#43](https://github.com/sebtuet/AcousticBrain/pull/43) ;
- fusionné dans `develop` par le commit
  `0ca2566bbdd659d2e25c93925b21edeb95668c6b` ;
- nouveau HEAD de `develop` :
  `0ca2566bbdd659d2e25c93925b21edeb95668c6b`.

Comportement établi :

- `--analysis-readiness` expose les expériences découvertes avec leur état
  exact `READY` ou `INCOMPLETE` ;
- les sept familles sont exposées dans l'ordre existant avec leur statut
  exact ;
- seuls les codes existants des blocages et réserves sont affichés lorsqu'ils
  existent ;
- la sortie précise qu'il s'agit de readiness technique et non de validité
  scientifique ;
- la sortie précise que `BLOCKED` n'implique pas que le pipeline ait sauté le
  calcul ;
- sans `MeasurementReadinessAnalysis`, aucune famille n'est inventée, un
  message structurel est affiché et le code de retour reste `0` ;
- le code de retour reste également `0` lorsqu'une famille est `BLOCKED` ;
- aucun seuil, score, verdict ou règle scientifique n'est ajouté ;
- le pipeline, les politiques de readiness, l'Advisor et le comportement
  réseau ne sont pas modifiés.

Validations établies :

- tests CLI et présentation de la readiness réussis ;
- tests du moteur de readiness réussis ;
- tests ciblés du `ReportBuilder` et des reporters réussis ;
- suite complète : `1544 passed` ;
- `compileall` réussi ;
- `git diff --check` réussi.

Cette fonctionnalité est présente dans `develop`, mais son code produit n'est
pas présent dans `main` à la date de cette mise à jour.

### Deterministic Assessment Summary CLI

Branche d'implémentation :
`agent/assessment-summary-cli`

Commit fonctionnel :
`ab88fe836e113ca245efecf36f304afd0b3512cc`

Message :
`feat(cli): add deterministic assessment summary`

Commit correctif :
`a39315df8245c0bfd76c2ef3a7b2cbc60d4ef0a1`

Message :
`fix(cli): distinguish missing blocked-action data`

État :

- implémenté, testé et revu indépendamment ;
- publié dans la PR
  [#45](https://github.com/sebtuet/AcousticBrain/pull/45) ;
- fusionné dans `develop` par le commit
  `431466515b62f6048dec4e0bf06c3979662b2699` ;
- nouveau HEAD de `develop` :
  `431466515b62f6048dec4e0bf06c3979662b2699`.

Comportement établi :

- `--assessment-summary` produit une synthèse déterministe à partir du
  `Report` existant ;
- les sections présentent le statut des mesures découvertes, la readiness
  technique, les observations acoustiques existantes, les actions applicables
  et bloquées structurées, les plans d'acquisition de preuves existants et une
  notice technique explicite ;
- les sources structurées utilisées sont `experiments_discovered`,
  `analysis_readiness`, `acoustic_observations`,
  `deterministic_corrective_actions` et `evidence_acquisition_plans` ;
- `APPLICABLE` et `CONDITIONALLY_APPLICABLE` sont projetés dans les actions
  applicables ;
- les statuts explicitement bloquants et `NOT_SUPPORTED` sont projetés dans
  les actions bloquées ;
- `ALREADY_TESTED` et `NO_ACTION_REQUIRED` ne sont reclassés dans aucune de
  ces deux sections ;
- le reporter distingue l'absence de données structurées d'action d'une
  collection structurée présente sans action bloquée ;
- aucune nouvelle science, Scientific Question, analyse, politique de
  readiness, règle, hiérarchie, interprétation, valeur ou décision n'est
  ajoutée ;
- aucun moteur scientifique, diagnostic source, action source, plan
  d'acquisition source, score ou seuil n'est modifié ;
- `BrainPipeline`, les reporters historiques, l'Advisor et le comportement
  réseau ne sont pas modifiés.

Validations établies :

- assessment summary : `9 passed` ;
- CLI : `49 passed` ;
- analysis readiness : `7 passed` ;
- full-assessment export : `11 passed` ;
- suite complète : `1565 passed` ;
- `compileall` réussi ;
- `git diff --check` réussi.

Cette fonctionnalité est présente dans `develop`, mais son code produit n'est
pas présent dans `main` à la date de cette mise à jour. `main` reçoit
uniquement cette mise à jour descriptive par la PR documentaire associée.

## 9. Démarrage d'une nouvelle conversation

> Voici l'état officiel actuel d'AcousticBrain.
> Utilise `docs/PROJECT_STATE.md` comme référence descriptive de cette
> conversation. Ne modifie pas les jalons figés. Les mandats produit
> `--full-assessment`, export texte déterministe et
> `--analysis-readiness`, ainsi que `--assessment-summary`, sont terminés dans
> `develop` par les PR #39, #41, #43 et #45. Leur code produit n'est pas encore
> présent dans `main`. Aucune prochaine étape produit n'est encore définie.
> N'invente aucun nouveau mandat scientifique ni aucune Scientific Question.
