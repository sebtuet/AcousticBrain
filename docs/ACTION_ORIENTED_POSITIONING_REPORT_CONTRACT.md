# Action-oriented positioning report contract

## Statut et utilisateur cible

PR-040 ajoute une synthèse de présentation destinée à un amateur de Hi-Fi qui
sait réaliser des mesures REW mais ne maîtrise pas nécessairement le vocabulaire
acoustique interne. Cette synthèse guide la lecture d'une expérience contrôlée;
elle ne choisit pas une position optimale et ne promet aucune amélioration.

Le rapport complet conserve deux niveaux :

1. `PROCHAINE ÉTAPE DE POSITIONNEMENT`, immédiatement après le nom du projet;
2. toutes les sections scientifiques et techniques existantes, inchangées et
   présentées ensuite.

## Audit préalable du rapport de référence

L'instruction PR-040 anticipait un rapport de 978 lignes. Sur `develop` au
commit `7c5fe222473987a6406f303bd221f73a2e7503b6`, l'exécution réelle de
`python main.py` produit **823 lignes**.

Structure observée avant PR-040 :

| Lignes | Section | Utilité principale |
|---|---|---|
| 1–22 | en-tête, salle et géométrie | contexte utile, détails géométriques techniques |
| 23–43 | expériences découvertes | utile pour savoir quelles mesures existent |
| 44–141 | évolutions locales et cumulatives | utile mais longue; une partie des faits de `exp-001` est répétée dans la vue cumulative |
| 142–177 | discrimination causale | scientifiquement importante, vocabulaire expert |
| 178–286 | recommandations structurées | contient des actions, mais la prochaine action concrète est difficile à isoler |
| 287–359 | synthèse acoustique globale | utile pour la priorité; répète des actions et scores détaillés ailleurs |
| 360–365 | traçabilité résumée | principalement technique |
| 366–380 environ | prochaine expérience recommandée | sélection utile, mais sans consigne concrète de déplacement dans le contexte courant |
| reste du rapport | diagnostics priorisés | faits utiles, puis causes, identifiants, readiness, confiance et recommandations détaillées |

Les principales duplications sont :

- comparaisons locales puis cumulatives sur les mêmes expériences;
- recommandations structurées, références d'action par domaine et
  recommandations des diagnostics;
- niveaux de confiance/readiness dans plusieurs sections;
- mêmes phénomènes dans la synthèse globale puis dans les diagnostics.

Avant PR-040, le rapport permettait de retrouver une prochaine expérience en
cherchant la section technique dédiée, mais ne disait pas en tête de document
quoi déplacer, quoi conserver, quelles mesures refaire et quels observables
seraient comparés.

### Présence PR-035 à PR-039 dans le contexte de référence

L'inspection structurée du `Report` produit par `main.py` établit :

- PR-035 `MaterialAwareReflectionCandidateAnalysis` : aucune présentation,
  zéro candidat;
- PR-036 `ControlledReflectionVerificationPlanningAnalysis` : aucune
  présentation, zéro proposition;
- PR-037 déclarations d'expérience : zéro;
- PR-038 comparaisons contrôlées : zéro;
- PR-039 mises à jour de soutien observationnel : zéro.

La traçabilité cite les types d'analyse PR-035 et PR-036 parce que les stages
existent, mais aucune instance exploitable n'est présente dans le rapport de
référence. La planification générale recommande
`experiment_candidate.modal_bass_persistence`, sans cible, direction, distance
ni `changed_variable_codes`. PR-040 doit donc répondre honnêtement qu'aucune
expérience de positionnement fiable ne peut être proposée dans ce contexte.

## Sources scientifiques autorisées

La synthèse est une projection déterministe des objets déjà présentés :

- premier diagnostic de `DiagnosticPriorityAnalysis`;
- candidat déjà désigné par `ExperimentPlanningAnalysis.recommended_candidate`;
- proposition PR-036 déjà ordonnée et, lorsqu'elle existe, déclaration PR-037
  au statut `PLANNED`;
- résultat PR-038 déjà calculé;
- statut PR-039 déjà calculé.

Le presenter ne recalcule aucun score, ne modifie aucun rang et ne crée aucune
hypothèse. Une égalité au rang prioritaire ou plusieurs propositions sans
décision unique produisent un état explicite de pistes multiples, jamais une
sélection locale nouvelle.

## Distinction obligatoire des informations

### Faits

La situation, la certitude et au plus trois faits viennent du diagnostic déjà
priorisé. Les causes existantes sont étiquetées `Explications possibles — à
vérifier`; elles ne deviennent pas des causalités.

### Hypothèses

Les pistes restent possibles, inconclusives ou non évaluables selon les objets
amont. Aucun texte utilisateur ne peut transformer une hypothèse en cause
confirmée.

### Actions

Une action est affichée uniquement si une source existante fournit :

- une variable à modifier;
- une cible identifiable;
- les variables à contrôler;
- des observables existants.

Pour un déplacement d'enceinte, `speaker_id` est obligatoire. La direction
n'est affichée que si un paramètre de direction existe. L'amplitude n'est
affichée que si `proposed_displacement_m` existe et est positif; sa conversion
mètre-centimètre est uniquement une conversion d'unité de présentation.

Une proposition PR-036 conserve sa méthode, sa cible, ses variables contrôlées,
ses observables et son ordre PR-035. Une proposition seule ne devient pas une
action recommandée : elle doit être reliée à une déclaration PR-037 `PLANNED`
pour apparaître comme expérience déjà planifiée. PR-040 ne lui ajoute aucun
impact sur les recommandations ou l'éligibilité.

### Résultats

Les états PR-038 sont traduits sans changer leur signification :

- `NOT_COMPARABLE` : les mesures ne permettent pas la comparaison;
- `INCONCLUSIVE` : aucune conclusion favorable ou défavorable;
- `NO_OBSERVABLE_CHANGE` : aucun changement mesurable dans le périmètre;
- `CHANGE_OBSERVED` : changement mesuré, sans causalité.

PR-039 `SUPPORTED_BY_OBSERVATION` et `NOT_SUPPORTED_BY_OBSERVATION` décrivent
uniquement le soutien observationnel de la piste. Ils ne confirment pas une
cause.

## Champs de la synthèse utilisateur

La projection contient toujours :

- statut de disponibilité;
- situation actuelle;
- niveau de certitude;
- faits mesurés;
- explications possibles;
- action ou absence explicite d'action;
- cible, direction et amplitude lorsqu'elles existent;
- éléments à conserver;
- mesures REW nécessaires;
- critères de comparaison existants;
- résultat précédent lorsqu'il existe;
- informations manquantes;
- limites;
- `causality_status` et identifiants sources conservés dans la projection.

Lorsqu'une action est disponible, le protocole utilisateur demande une nouvelle
expérience REW distincte avec L, R et L+R, la position du microphone et le
volume inchangés, et une note explicite de l'unique élément modifié. Les détails
d'acquisition restent dans le guide REW.

## Cas sans action

### Données insuffisantes

Le rapport affiche :

```text
Aucune expérience de positionnement fiable ne peut être proposée avec les données actuelles.
```

Il nomme ensuite la cible ou la variable manquante connue.

### Plusieurs pistes non départageables

Une égalité explicite au premier rang ou plusieurs propositions sans décision
unique produit :

```text
Plusieurs explications restent également plausibles.
Une mesure supplémentaire est nécessaire avant de proposer un déplacement.
```

### Expérience déjà planifiée

Une déclaration PR-037 `PLANNED` est reliée à sa proposition PR-036 et présentée
sans créer une nouvelle action.

### Résultat précédent

Les cas non comparable, inconclusif, sans changement et avec changement sont
affichés même lorsqu'aucune nouvelle action n'est disponible.

## Vocabulaire

La synthèse privilégie `problème observé`, `piste à vérifier`, `test de
positionnement`, `changement mesuré`, `résultat inconclusif` et `prochaine
étape`. Les identifiants, provenances, règles, impacts et statuts complets
restent dans les sections techniques existantes.

## Limites causales et interdictions

Chaque synthèse conserve :

```text
causality_status = NOT_ESTABLISHED
```

Elle rappelle qu'une seule variable doit changer, qu'une nouvelle mesure est
nécessaire et que le résultat peut être favorable, défavorable ou inconclusif.

Le presenter ne peut pas :

- inventer une cible, une direction ou une distance;
- calculer une nouvelle priorité ou départager un ex æquo;
- attribuer une surface comme cause;
- annoncer une position optimale;
- garantir une amélioration;
- modifier scores, recommandations, rangs ou éligibilité;
- masquer les détails techniques PR-035 à PR-039.

## Relation avec PR-035 à PR-039

```text
PR-035 candidat et rang informatif
  → PR-036 proposition descriptive et variables contrôlées
    → PR-037 expérience déclarée
      → PR-038 comparaison des observables déclarés
        → PR-039 soutien observationnel, causalité toujours non établie
          → PR-040 traduction utilisateur sans décision scientifique nouvelle
```

PR-040 est donc une feuille de présentation. Aucun moteur scientifique ou
contrat amont ne dépend de sa sortie.
