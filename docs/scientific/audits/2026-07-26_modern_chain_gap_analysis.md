# Modern Scientific Assertion Chain Gap Analysis

## Nature

**AUDIT — NON NORMATIF**

Ce document compare les cinq objets de la chaîne déterministe moderne avec les
quatorze attributs de `SCIENTIFIC_ASSERTION_CONTRACT.md`.

Il ne crée aucune règle, aucune capacité et aucune Scientific Question. Il ne
propose aucune implémentation, modification de code ou migration.

## Métadonnées

- Date : `2026-07-26`
- Commit du dépôt audité :
  `0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8`
- Branche auditée : `agent/scientific-normative-foundations`
- Nature : analyse d’écart sémantique de la chaîne moderne

## Base normative

- `docs/scientific/SCIENTIFIC_CONTRACT.md`
- `docs/scientific/KNOWLEDGE_MODEL.md`
- `docs/scientific/EVIDENCE_MODEL.md`
- `docs/scientific/SCIENTIFIC_ASSERTION_CONTRACT.md`

## Périmètre

- `AcousticObservation`
- `DeterministicAcousticReasoning`
- `DeterministicCorrectiveAction`
- `DeterministicEvidenceWeight`
- `EvidenceAcquisitionPlan`

Comparaison avec :

1. type épistémique ;
2. contenu ;
3. provenance ;
4. portée ;
5. domaine de validité ;
6. force probante ;
7. hypothèses sous-jacentes ;
8. limitations ;
9. contradictions ;
10. conditions de révision ;
11. conditions de réfutation ;
12. conditions de retrait ;
13. portée maximale autorisée ;
14. statut.

## Exclusions

- aucune proposition de représentation commune ;
- aucun renommage ou changement de code ;
- aucune stratégie de migration ;
- aucun changement de comportement ;
- aucune évaluation des algorithmes acoustiques ;
- aucune dérivation de Scientific Question.

## Méthode

Classification utilisée :

- **R — Réutilisable tel quel** : sémantique déjà exprimée ;
- **N — Renommage sémantique uniquement** : information complète et
  équivalente, nom exprimant une autre sémantique ;
- **A — Véritablement absent** : information absente ou exigeant une nouvelle
  déduction, règle ou information.

Un attribut partiel a été classé `A`. Une confiance n’a pas été assimilée à une
force ; une liste de sources n’a pas été assimilée à une provenance complète.

Commandes et inspections représentatives :

```text
sed -n '<plage>' acousticbrain/models/acoustic_observation.py
sed -n '<plage>' acousticbrain/models/deterministic_acoustic_reasoning.py
sed -n '<plage>' acousticbrain/models/deterministic_corrective_action.py
sed -n '<plage>' acousticbrain/models/evidence_weighting.py
sed -n '<plage>' acousticbrain/models/evidence_acquisition.py
rg -n 'source|upstream|rule|limitation|contradict|status|confidence|strength' \
  acousticbrain/models
git status --short
git diff --check
```

## Reproductibilité

Inspecter les cinq modèles au commit :

```text
0958ef2a098d44ea06f4d8d3ce6c0996430e5eb8
```

Appliquer la classification ci-dessus à chacun des quatorze attributs, sans
déduire un attribut depuis une relation seulement indirecte.

## Observations et preuves

### Matrice d’écart

| Attribut normatif | Observation | Reasoning | Action | Weight | Acquisition Plan |
|---|:---:|:---:|:---:|:---:|:---:|
| Type épistémique | A | A | A | A | A |
| Contenu | R | R | R | R | R |
| Provenance | A | R | R | R | A |
| Portée | A | A | A | A | A |
| Domaine de validité | A | A | A | A | A |
| Force probante | A | A | A | A | A |
| Hypothèses sous-jacentes | A | R | A | A | A |
| Limitations | R | R | R | R | R |
| Contradictions | A | A | R | A | A |
| Conditions de révision | A | A | A | A | A |
| Conditions de réfutation | A | A | A | A | A |
| Conditions de retrait | A | A | A | A | A |
| Portée maximale | A | A | A | A | A |
| Statut transversal | A | A | A | A | R |

Aucun attribut n’a été classé `N`. Le contrat étant indépendant des noms de
champs, une sémantique équivalente est réutilisable ; les autres écarts
observés ne sont pas purement lexicaux.

## AcousticObservation

Réutilisable :

- contenu : `title`, `description` ;
- limitations : `limitations`.

Absent ou incomplet :

- type : `category` décrit le domaine acoustique, pas le type épistémique ;
- provenance : sources et références présentes, transformations et règles
  incomplètes ;
- portée et domaine ;
- force : `confidence` n’est pas une force probante ;
- hypothèses ;
- contradictions : `contradicting_evidence` contient des contre-preuves, pas
  nécessairement les connaissances incompatibles ;
- révision, réfutation, retrait ;
- portée maximale ;
- statut transversal.

## DeterministicAcousticReasoning

Réutilisable :

- contenu : conclusion, premises, étapes d’inférence et statements ;
- provenance : observations, sources amont, sources typées des premises,
  règles et entrées des inférences ;
- hypothèses : premises de type hypothèse et
  `compatible_hypothesis_ids` ;
- limitations.

Absent ou incomplet :

- type épistémique ;
- portée et domaine ;
- force : `confidence` n’est pas une force ;
- contradictions : les preuves défavorables ne décrivent pas nécessairement
  l’incompatibilité entre connaissances ;
- révision, réfutation, retrait ;
- portée maximale ;
- statut transversal : `conclusion` est le résultat du reasoning, pas son état
  de cycle de vie.

## DeterministicCorrectiveAction

Réutilisable :

- contenu : titre, objectif, description et type d’action ;
- provenance : reasonings, observations, sources amont et justifications avec
  règles ;
- limitations ;
- contradictions explicites.

Absent ou incomplet :

- type épistémique ;
- portée : cible, préconditions et contraintes ne décrivent pas toute la
  portée scientifique ;
- domaine ;
- force : confiance et plafond de confiance ne sont pas une force probante ;
- hypothèses, accessibles seulement indirectement ;
- révision, réfutation, retrait ;
- portée maximale ;
- statut transversal : applicabilité, priorité et statut de traçabilité sont
  des qualifications distinctes.

## DeterministicEvidenceWeight

Réutilisable :

- contenu : vecteur des dimensions, applicabilité, plafonds et règles ;
- provenance : références typées, objets sources, règles et conditions ;
- limitations.

Absent ou incomplet :

- type épistémique ;
- portée et domaine ;
- force normative : `UNAVAILABLE / LOW / MEDIUM / HIGH` ne représente pas
  l’ordre normatif complet et ne distingue pas `INSUFFISANT` ;
- hypothèses, accessibles seulement indirectement ;
- contradictions : preuves défavorables et blocages ne décrivent pas
  nécessairement les connaissances incompatibles ;
- révision, réfutation, retrait ;
- portée maximale ;
- statut transversal : `action_applicability` qualifie l’action référencée.

## EvidenceAcquisitionPlan

Réutilisable :

- contenu : objectif, type de test, instructions, variables, mesures,
  observations, critères et cibles ;
- limitations ;
- statut : `PROPOSED / READY / BLOCKED`.

Absent ou incomplet :

- type épistémique ;
- provenance : références amont présentes, règle productrice absente ;
- portée et domaine ;
- force ;
- hypothèses, accessibles seulement indirectement ;
- contradictions, accessibles seulement par certains blocages ;
- révision, réfutation, retrait ;
- portée maximale.

## Résultat quantitatif

| Objet | Réutilisables | Renommage seul | Véritablement absents |
|---|---:|---:|---:|
| AcousticObservation | 2 | 0 | 12 |
| DeterministicAcousticReasoning | 4 | 0 | 10 |
| DeterministicCorrectiveAction | 4 | 0 | 10 |
| DeterministicEvidenceWeight | 3 | 0 | 11 |
| EvidenceAcquisitionPlan | 3 | 0 | 11 |

Attributs absents des cinq objets :

- type épistémique explicite ;
- portée ;
- domaine de validité ;
- force probante normative ;
- conditions de révision ;
- conditions de réfutation ;
- conditions de retrait ;
- portée maximale autorisée.

## Limites

- L’analyse compare les informations observées, pas une future représentation.
- Une information indirecte n’a pas été déclarée équivalente à un attribut
  explicite.
- Le classement ne démontre pas la conformité des champs réutilisables à tous
  leurs invariants futurs.
- Aucun résultat ne doit être appliqué automatiquement à une révision
  ultérieure.
