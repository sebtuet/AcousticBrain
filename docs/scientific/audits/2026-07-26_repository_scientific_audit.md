# Repository Scientific Audit

## Nature

**AUDIT — NON NORMATIF**

Ce document décrit un état observé du dépôt. Il ne prescrit aucune exigence et
n’a aucune autorité normative. Il conserve le premier audit complet du moteur
réalisé contre la fondation scientifique.

Cet audit ne crée aucune règle, aucune capacité et aucune Scientific Question.

## Métadonnées

- Date : `2026-07-26`
- Commit du dépôt audité :
  `0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8`
- Branche auditée : `agent/scientific-normative-foundations`
- Nature de l’audit : audit scientifique et de conformité du dépôt complet
- Résultat historique global : `NON CONFORME`

## Base normative

Base normative effectivement utilisée lors de l’audit :

- `docs/scientific/SCIENTIFIC_CONTRACT.md`
- `docs/scientific/KNOWLEDGE_MODEL.md`
- `docs/scientific/EVIDENCE_MODEL.md`

`SCIENTIFIC_ASSERTION_CONTRACT.md` et `CAPABILITY_REGISTRY.md` sont présents
dans le commit de référence final, mais ont été produits après ce premier
audit. Ils ne sont donc pas présentés rétroactivement comme sa base.

## Périmètre

L’audit a porté sur :

- le corpus documentaire du dépôt ;
- les modèles métier ;
- les moteurs d’analyse ;
- les services applicatifs ;
- l’orchestration du pipeline ;
- les diagnostics et décisions ;
- les objets de preuve, reasoning, action et acquisition ;
- les tests automatisés ;
- les 28 clauses de `SCIENTIFIC_CONTRACT.md`.

État observé :

- 415 fichiers Python ;
- 162 fichiers de tests ;
- 40 stages ;
- 44 documents historiques nommés `*CONTRACT*.md`.

## Exclusions

L’audit :

- n’a pas modifié le moteur, les tests ou les documents ;
- n’a pas évalué une nouvelle capacité ;
- n’a pas reconstruit de Scientific Question depuis le code ;
- n’a pas transformé la réussite des tests en validation scientifique externe ;
- n’a pas proposé de migration ou de changement algorithmique ;
- n’a pas réalisé de validation physique externe indépendante.

## Méthode

Méthodes utilisées :

- inspection manuelle du contrat et des documents historiques ;
- inventaire des sources avec `rg`, `find` et lecture ciblée ;
- inspection des stages, moteurs, modèles et services ;
- recherche exhaustive des Scientific Questions déclarées ;
- comparaison des objets de preuve avec `SC-EVD-001` et `SC-EVD-002` ;
- exécution de la suite complète ;
- compilation Python ;
- vérification Git.

Commandes représentatives :

```text
git branch --show-current
git rev-parse HEAD
git status --short
rg --files
find acousticbrain -type f -name '*.py'
find tests -maxdepth 1 -type f -name 'test_*.py'
rg -n 'Scientific Question|Question scientifique' .
rg -n '^class .*Stage' acousticbrain/brain/stages
rg -n 'class .*Analysis|class .*Engine|class .*Service' acousticbrain
python -m pytest -q
python -m compileall -q acousticbrain main.py
git diff --check
```

## Reproductibilité

Pour reproduire l’état historique, se placer sur :

```text
0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8
```

Puis répéter l’inventaire documentaire et structurel, la recherche des
Scientific Questions et les validations indiquées ci-dessus. Les résultats
scientifiques doivent être évalués contre les versions des quatre documents
normatifs présentes à ce commit.

## Observations et preuves

### Aucune Scientific Question déclarée

Aucune Scientific Question n’a été trouvée hors des documents normatifs qui en
définissent le rôle.

Conséquence observée : aucune capacité candidate ne pouvait démontrer la chaîne
descendante exigée par `SC-SQ-001`.

### Modèle de preuve incompatible avec le contrat normatif

`EvidenceReference` ne déclarait pas systématiquement :

- une hypothèse cible ;
- une direction ;
- une règle d’interprétation ;
- un domaine de validité.

Plusieurs vocabulaires de force coexistaient :

- `OBSERVED / CALCULATED / HYPOTHESIS / CONFIRMED` ;
- scores numériques `0..100` ;
- `UNAVAILABLE / LOW / MEDIUM / HIGH`.

Aucun ne correspondait à l’ordre normatif complet :

```text
NON DÉMONTRÉ < INSUFFISANT < FAIBLE < MODÉRÉ < FORT
```

### Contrat transversal absent dans les objets du moteur

De nombreuses informations existaient : provenance partielle, limitations,
contradictions, confiance et blocages. Aucun objet commun ne garantissait
toutefois les attributs imposés par `SC-AST-001`.

### Documents historiques non subordonnés

À la révision auditée, aucun des 44 anciens fichiers `*CONTRACT*.md` ne
déclarait sa subordination à `SCIENTIFIC_CONTRACT.md` ni les clauses `SC-*`
qu’il précisait.

### Validation externe non démontrée

La suite automatisée démontrait une stabilité logicielle importante. Aucune
validation physique externe indépendante conforme à `SC-VAL-002` n’était
démontrée.

## Capacités observées

Les familles suivantes ont été examinées comme transformations de connaissance
existantes :

- qualité et exploitabilité des mesures ;
- description, caractéristiques, matériaux et géométrie de salle ;
- propagation, modes propres, densité modale, stéréo et SBIR ;
- RT60, ETC, clarté, direct/réverbéré, décroissance grave et spatial ;
- corrélations acoustiques et géométriques ;
- synthèse d’observations ;
- reasonings historique et déterministe ;
- actions correctives ;
- pondération des preuves ;
- acquisition de preuves ;
- génération et comparaison d’expériences ;
- campagnes, discrimination causale et apprentissage longitudinal ;
- planification expérimentale ;
- synthèse globale, recommandations et traçabilité.

Pour toutes ces familles, l’existence logicielle était observée. Aucune ne
démontrait l’ensemble des obligations du contrat scientifique.

Les interfaces, présentateurs, Advisor, persistence, importateurs et stages
génériques n’ont pas été qualifiés comme capacités scientifiques autonomes.

## Matrice historique des 28 clauses

| Clause | Statut observé | Motif principal |
|---|---|---|
| SC-AUT-001 | NON CONFORME | Documents subordonnés non déclarés |
| SC-AUT-002 | PARTIELLEMENT CONFORME | Séparation architecturale présente, audit scientifique indépendant absent |
| SC-AUT-003 | NON DÉMONTRÉ | Aucun audit antérieur clause par clause |
| SC-AUT-004 | NON CONFORME | Qualificatifs sans rattachement systématique à un critère normatif |
| SC-AUT-005 | NON CONFORME | Contrats historiques mêlant exigences, implémentation et validation |
| SC-TRU-001 | PARTIELLEMENT CONFORME | Limitations présentes, portée non universelle |
| SC-TRU-002 | PARTIELLEMENT CONFORME | Calcul et interprétation souvent séparés, validation externe absente |
| SC-TRU-003 | PARTIELLEMENT CONFORME | Provenance mesurée ou déclarée présente dans certains domaines |
| SC-AST-001 | NON CONFORME | Contrat transversal non incarné dans les objets |
| SC-AST-002 | NON CONFORME | Transformations épistémiques non universellement déclarées |
| SC-EVD-001 | NON CONFORME | Preuves sans contrat orienté complet |
| SC-EVD-002 | NON CONFORME | Vocabulaires de force incompatibles |
| SC-EVD-003 | PARTIELLEMENT CONFORME | Planner solide, effet probant complet non universel |
| SC-CAP-001 | NON CONFORME | Déclarations obligatoires absentes |
| SC-CAP-002 | PARTIELLEMENT CONFORME | Droits et refus largement testés |
| SC-CAP-003 | PARTIELLEMENT CONFORME | Invariants récents forts, héritage non uniformisé |
| SC-SCP-001 | NON CONFORME | Portées maximales non déclarées |
| SC-SCP-002 | NON DÉMONTRÉ | Composition générale des portées non démontrée |
| SC-REF-001 | PARTIELLEMENT CONFORME | Refus nombreux, contrat transversal absent |
| SC-REV-001 | NON CONFORME | Conditions de révision absentes de nombreuses conclusions |
| SC-REV-002 | PARTIELLEMENT CONFORME | Transitions explicites localisées |
| SC-DEC-001 | PARTIELLEMENT CONFORME | Chaîne récente séparée, couches historiques moins strictes |
| SC-DEC-002 | PARTIELLEMENT CONFORME | Blocages récents préservés, retrait et révision incomplets |
| SC-SQ-001 | NON CONFORME | Aucune Scientific Question déclarée |
| SC-VAL-001 | PARTIELLEMENT CONFORME | Validation logicielle forte, statut scientifique distinct incomplet |
| SC-VAL-002 | NON DÉMONTRÉ | Aucun corpus externe indépendant |
| SC-TRC-001 | PARTIELLEMENT CONFORME | Traçabilité récente forte, héritage incomplet |
| SC-CON-001 | NON CONFORME | Anciens contrats non subordonnés |

## Preuves de validation logicielle

Résultats observés pendant l’audit :

```text
1496 passed in 61.21s
```

`compileall` et `git diff --check` ont réussi.

Ces résultats démontrent la stabilité logicielle de l’état audité. Ils ne
démontrent pas la vérité externe des affirmations ni leur validation
scientifique.

## Limites

- L’audit a évalué les artefacts disponibles dans le dépôt uniquement.
- Il n’a pas disposé de Scientific Questions émises par l’autorité scientifique.
- Il n’a pas réalisé de mesures ou de validations physiques externes.
- Les nombres de fichiers décrivent l’état du dépôt au moment de l’audit.
- Les statuts sont historiques et ne doivent pas être appliqués sans nouvel
  audit à une révision ultérieure.

## Préservation historique

Le résultat `NON CONFORME` est conservé comme observation historique. Un audit
ultérieur pourra observer un autre statut, mais ne devra pas réécrire ce
constat rétroactivement.
