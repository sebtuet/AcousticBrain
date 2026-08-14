# AcousticBrain — Project State

Ce document décrit l’état d’AcousticBrain V1.0.0. Il est non normatif, non
scientifique et ne constitue pas un audit. Il ne crée aucune capacité, aucune
Scientific Question et aucune règle.

## 1. État de release

Version applicative :

`1.0.0`

Commit de préparation de release :

`6f9f662256dcb36330d28d2e49a1aadec24eadc9`

Commit d’intégration validé dans `develop` :

`c3de99f`

La CLI publique V1 est centralisée dans `main.py`. Les adaptateurs de contrats
experts ou internes ne font pas partie de cette interface publique.

La validation de release sur `develop` établit :

- `2465 passed` ;
- `main.py --help` réussi ;
- `compileall` réussi ;
- `git diff --check` réussi ;
- worktree suivi propre avant publication.

L’historique fonctionnel de la release est résumé dans
[`CHANGELOG.md`](../CHANGELOG.md). La roadmap canonique se trouve dans
[`ROADMAP.md`](ROADMAP.md).

## 2. Mission et autorité

AcousticBrain est un moteur déterministe d’analyse acoustique fondé sur des
campagnes de mesures. Le moteur déterministe est l’autorité scientifique.

L’Advisor LLM est optionnel, en lecture seule, et séparé du moteur
déterministe. Il peut expliquer des résultats structurés existants, mais ne
crée aucune connaissance scientifique et ne remplace aucune analyse.

## 3. Catégories documentaires

- **Normatif** : prescrit une règle ou une frontière.
- **Descriptif** : décrit un état observé.
- **Audit** : démontre un état sur un commit donné.

Les documents normatifs ne dépendent ni des documents descriptifs ni des
audits. Les audits sont non normatifs, historiques et attachés à la révision
qu’ils ont examinée.

## 4. Gouvernance scientifique historique

Le jalon historique de gouvernance scientifique est :

`0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8`

Message :

`docs(scientific): establish normative scientific governance`

Il comprend historiquement :

- `docs/scientific/SCIENTIFIC_CONTRACT.md`
- `docs/scientific/KNOWLEDGE_MODEL.md`
- `docs/scientific/EVIDENCE_MODEL.md`
- `docs/scientific/SCIENTIFIC_ASSERTION_CONTRACT.md`
- `docs/scientific/CAPABILITY_REGISTRY.md`

Ces fichiers ne sont pas présents dans l’arbre V1 courant. Ils restent
conservés dans le commit historique et sur la branche
`agent/scientific-normative-foundations`. Leur absence de l’arbre courant ne
constitue pas une révocation du jalon.

Les Scientific Questions relèvent exclusivement de l’autorité scientifique.
Elles ne doivent jamais être reconstruites depuis le code, un registre, une
présentation ou un audit.

## 5. Audits scientifiques historiques

Le jalon historique d’audit est :

`cb74b2a354b40c2f363e49566b2babba2f0267af`

Message :

`docs(audit): record scientific governance assessments`

Branche historique :

`agent/scientific-audit-records`

Il contient historiquement :

- `docs/scientific/audits/2026-07-26_repository_scientific_audit.md`
- `docs/scientific/audits/2026-07-26_assertion_model_inventory.md`
- `docs/scientific/audits/2026-07-26_modern_chain_gap_analysis.md`

Ces audits ne sont pas présents dans l’arbre V1 courant. Ils restent
conservés dans leur commit et leur branche historiques.

Les anciens audits sont immuables. Une erreur factuelle doit être rectifiée
de façon traçable, jamais par réécriture silencieuse.

## 6. Capacités V1 établies

La chaîne déterministe principale est :

```text
Mesures
→ Observations
→ Reasoning
→ Actions
→ Evidence Weighting
→ Evidence Acquisition
→ Présentations publiques
→ Advisor optionnel
```

La V1 comprend notamment :

- import et analyse déterministe de campagnes REW ;
- analyse des réponses fréquentielles et impulsionnelles ;
- diagnostics, observations, reasoning, actions et pondération des preuves ;
- analyses de modes, SBIR, temporelles, spatiales et de qualité des mesures ;
- readiness technique ;
- rapport déterministe complet et export texte ;
- synthèse utilisateur déterministe ;
- vues en lecture seule des expériences et evidence plans ;
- parcours guidés de statut, préparation et déclaration ;
- complétion structurée d’evidence plans bloqués ;
- préparation, preview, confirmation et relecture explicites ;
- génération, révision et revue des documents `CHANNEL_ISOLATION` ;
- qualification de readiness et déclaration explicite ;
- propositions déterministes de positionnement et acceptation explicite d’une
  proposition encore éligible ;
- preview, enregistrement et relecture exacte de snapshots SBIR ;
- qualification explicite des références de campagnes ;
- mode déterministe `EXPLORATORY` avec décision de faisabilité explicite ;
- Advisor LLM optionnel et sans autorité scientifique.

Les opérations en lecture seule restent séparées des mutations explicites.
Aucune sélection, référence, donnée manquante ou qualification scientifique
n’est inventée.

## 7. Analyse descriptive des caractéristiques fréquentielles

`FrequencyResponseFeatureAnalysis` réutilise les mesures TXT REW déjà chargées
et produit des caractéristiques descriptives LEFT, RIGHT et STEREO :

- pics et creux ;
- fréquence centrale, niveau relatif, proéminence ou profondeur ;
- bornes, largeur en hertz et en octaves ;
- Q estimé lorsqu’il est calculable ;
- qualité de détection, limitations et provenance ;
- comparaisons `COMMON`, `LEFT_ONLY` et `RIGHT_ONLY` ;
- relations descriptives avec STEREO.

Une relation STEREO issue d’une comparaison `COMMON` n’est résolue que si la
caractéristique STEREO est compatible avec les deux sources LEFT et RIGHT.
Pour `LEFT_ONLY` ou `RIGHT_ONLY`, la compatibilité avec l’unique source reste
suffisante. Une compatibilité multiple reste ambiguë.

Ces résultats peuvent alimenter les observations déterministes et la readiness
technique. Ils ne prouvent ni un mode de pièce, ni un SBIR, ni une autre cause
acoustique. Ils n’ajoutent aucune prémisse causale et ne produisent aucune
recommandation automatique de placement.

Le jalon principal correspondant est la PR #50, fusionnée dans `develop` par :

`6495be3af10a1c494a79be00e7dcd7f846c6c5a2`

## 8. Evidence plans et déclarations

Les `EvidenceAcquisitionPlan` utilisent les statuts `PROPOSED`, `READY` et
`BLOCKED`. Ils décrivent les preuves à acquérir, les instructions, variables,
mesures, critères et facteurs de blocage.

Une vue ou un statut de plan ne constitue ni une correction acoustique, ni
l’exécution d’une expérience.

La V1 peut :

- compléter un plan bloqué à partir d’une entrée structurée explicitement
  fournie ;
- préserver le plan dérivé et sa provenance ;
- préparer et confirmer explicitement les prérequis ;
- vérifier les documents opérationnels requis ;
- qualifier une déclaration ;
- créer une déclaration expérimentale par une action utilisateur séparée.

Elle ne complète jamais automatiquement les éléments absents, notamment :

- protocole et version ;
- référence ;
- positions du microphone ;
- répétitions et canaux ;
- réglages d’acquisition ;
- variables contrôlées ;
- critères de comparaison ;
- géométrie, cible, direction ou amplitude requise.

Déclarer une expérience ne l’exécute pas.

## 9. Frontières scientifiques V1

La V1 ne fournit pas automatiquement :

- une causalité non établie par les contrats de preuve applicables ;
- l’exécution physique d’une expérience ;
- l’acquisition de mesures ;
- le déplacement réel d’une enceinte ;
- l’optimisation bayésienne ;
- le machine learning ;
- le mode `PRESCRIPTIVE` ;
- la reconstruction 3D.

Une proposition, une compatibilité, une déclaration ou un snapshot enregistré
ne constitue pas à lui seul une preuve mesurée, une exécution ou une
causalité.

## 10. Jalons historiques de l’interface publique

Les premiers jalons publics restent traçables :

- PR #39 — `--full-assessment`
  commit fonctionnel `c4e698108070ea8c0552fc46cbec7b76edeb75b9`
- PR #41 — export texte déterministe
  commit fonctionnel `16d9a22dfacd3fbb8842c4deb81a9a707bd7995f`
- PR #43 — `--analysis-readiness`
  commit fonctionnel `0a64bf457172ba3cf703b5d613f8b13db5f58e5e`
- PR #45 — `--assessment-summary`
  commits `ab88fe836e113ca245efecf36f304afd0b3512cc` et
  `a39315df8245c0bfd76c2ef3a7b2cbc60d4ef0a1`
- PR #50 — `FrequencyResponseFeatureAnalysis`
  commits principaux `12f9bc2ae44de4fa59a4ff3a0b04aa181182f8a6`,
  `ab9b0da35cdc21e110ebc6b69099990a63c291e9`,
  `ee2ff821ee33e6b809a466875eec9ff784481897` et
  `9c44c17737e786061698134acf81b3d2894c758b`

Ces jalons sont historiques. L’état de release courant est défini par la
version `1.0.0`, son changelog, ses contrats V1 et ses validations finales.

## 11. Principes de développement

- aucune nouvelle capacité scientifique sans autorité scientifique explicite ;
- aucune donnée, référence ou causalité reconstruite implicitement ;
- séparation des lectures et mutations explicites ;
- Pull Requests petites, fermées, testables et réversibles ;
- autorisation distincte pour commit, publication et fusion ;
- maintien des limites et provenances dans les sorties utilisateur ;
- aucune généralisation d’infrastructure sans plusieurs cas démontrés.

## 12. Reprise

> AcousticBrain V1.0.0 est la base produit stable.
> Utilise ce document comme état descriptif et les contrats dédiés comme
> autorités de comportement. Ne reconstruis aucune règle scientifique depuis
> ce résumé. Les capacités post-V1 et V2 sont distinguées dans
> `docs/ROADMAP.md`.
