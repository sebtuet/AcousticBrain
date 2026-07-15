# Longitudinal experimental learning state contract

## Sens du terme apprentissage

L'apprentissage expérimental désigne ici une mémoire déterministe et traçable
des expériences déclarées, de leurs comparaisons et des ambiguïtés explicitement
résolues ou restantes. Il ne s'agit ni de machine learning, ni d'un modèle
entraîné, ni d'un ajustement automatique de seuils.

L'état est recalculé depuis les manifests, déclarations PR-043, comparaisons,
campagnes et décisions utilisateur. Il ne possède donc aucune persistance
autonome.

## Audit de l'existant

Avant PR-045, trois mémoires partielles existaient :

- `ExperimentComparisonAnalysis` conservait la chronologie, les comparaisons
  locales et cumulatives, les observations, contre-faits, exclusions et traces;
- `ExperimentCampaignAnalysis` synthétisait uniquement la campagne modale
  déclarée, avec ses branches, métriques et discriminations restantes;
- `CausalDiscriminationAnalysis` réduisait les ambiguïtés du protocole
  d'asymétrie à partir d'étapes, observations et décisions `DEFERRED` explicites.

Les mises à jour PR-039 mémorisent par ailleurs le soutien observationnel des
propositions de réflexion contrôlée, sans modifier recommandations, classement
ou éligibilité. Les hypothèses acoustiques courantes sont recalculées par
expérience et ne constituent pas une synthèse longitudinale.

Ces objets se recouvrent sur les identifiants d'expérience, les observations et
les ambiguïtés, mais aucun ne fournit un état unique par hypothèse. PR-045 ne les
remplace pas : il les référence et conserve leur provenance.

Une synthèse complète exigerait d'inventer des informations lorsque le protocole
ou l'hypothèse n'est pas déclaré, lorsque plusieurs variables changent sans
périmètre explicite, ou lorsqu'une observation acoustique n'est pas reliée par
une règle existante au soutien d'une hypothèse. Ces cas sont enregistrés ou
exclus, jamais complétés implicitement.

## Unité d'agrégation

Un état correspond exactement à un `hypothesis_code`. Deux hypothèses ne sont
jamais réunies. Les comparaisons locales sont utilisées une seule fois; les
comparaisons cumulatives restent consultables mais ne sont pas ajoutées une
seconde fois à la mémoire.

Une expérience contribue à l'historique si son identité est stable. Elle ne
contribue aux observations longitudinales que si sa comparaison et sa
comparabilité sont explicites et si sa déclaration est exploitable. Chaque
observation conserve l'identifiant de sa comparaison source.

Le modèle distingue sans recouvrement sémantique implicite :

- `historical_context_experiment_codes`, qui inventorie les expériences citées
  par une comparaison, une campagne ou une discrimination;
- `evidence_contributing_experiment_codes`, limité aux comparaisons admissibles
  de déclarations `CONTROLLED_INTERVENTION` ou `MEASUREMENT_REPEAT`;
- `campaign_source_experiment_codes`, transporté depuis
  `ExperimentCampaignTrace.experiment_ids`;
- `discrimination_source_experiment_codes`, transporté depuis
  `CausalDiscriminationTrace.experiment_ids`;
- `historical_experiment_declaration_statuses`, qui conserve le statut PR-043
  disponible, `UNKNOWN_DECLARATION` ou `DECLARATION_UNAVAILABLE`.

Les champs génériques `experiment_codes` et `used_experiment_codes` ne sont pas
employés dans ce contrat, car ils confondraient historique et preuve admissible.
Le rapport reprend cette séparation avec les intitulés « Preuves longitudinales
admissibles », « Historique expérimental conservé » et « Historique non
admissible comme nouvelle preuve ».

## Inclusion et exclusion

- `CONTROLLED_INTERVENTION` peut alimenter soutien ou contradiction uniquement
  dans l'hypothèse et le protocole déclarés.
- `MEASUREMENT_REPEAT` alimente uniquement les observations inchangées ou
  inconclusives de répétabilité. Elle n'est jamais une intervention de placement.
- `UNKNOWN` reste dans l'historique et dans les exclusions. Elle ne produit ni
  soutien ni contradiction.
- `NOT_COMPARABLE` reste dans l'historique avec son motif et ne produit aucune
  preuve longitudinale.
- une comparaison sans hypothèse déclarée n'est attribuée à aucune hypothèse.

Les scores de soutien et confiances ne sont jamais additionnés ou moyennés.
`evidence_summary` contient seulement des nombres d'identifiants d'observation
distincts.

## Statuts longitudinaux

- `NOT_TESTED` : aucune expérience reliée à l'hypothèse;
- `INSUFFICIENT_DECLARATION` : l'historique existe mais sa déclaration ne permet
  pas une agrégation honnête;
- `INSUFFICIENT_COMPARABILITY` : aucune contribution exploitable en raison de la
  comparabilité;
- `EVIDENCE_ACCUMULATING` : des observations exploitables existent sans stabilité
  longitudinale démontrée;
- `CONFLICTING_EVIDENCE` : soutien et contradiction explicites coexistent;
- `STABLE_SUPPORT` : plusieurs interventions contrôlées distinctes soutiennent
  les observations, sans contre-observation;
- `STABLE_NON_SUPPORT` : plusieurs interventions contrôlées distinctes produisent
  des contre-observations, sans soutien;
- `DISCRIMINATION_REQUIRED` : une ambiguïté explicite reste ouverte;
- `DEFERRED_BY_USER` : la discrimination utile est différée par décision;
- `EXPERIMENTAL_PATH_EXHAUSTED` : la campagne ne fournit plus de discrimination
  disponible dans son périmètre actuel.

`STABLE_SUPPORT` n'établit pas une causalité. `STABLE_NON_SUPPORT` ne réfute pas
l'hypothèse de manière générale.

## Ambiguïtés et information suivante

Les ambiguïtés résolues et restantes proviennent uniquement des campagnes et de
la discrimination causale. Une décision différée est conservée séparément. Le
besoin suivant reprend, par ordre déterministe, une déclaration manquante, une
comparabilité manquante, une répétition supplémentaire, une discrimination
existante ou l'absence explicite de nouvelle discrimination.

Pour une ambiguïté résolue, `resolved_ambiguity_provenance` transporte le code
du protocole, l'identifiant de la trace causale et les expériences de cette
trace. Cette provenance est directe au niveau de la discrimination. Le modèle
source ne conserve pas de relation individuelle entre chaque ambiguïté et
chaque étape : PR-045 ne déduit donc pas qu'une expérience particulière a, à
elle seule, résolu l'ambiguïté. Si la trace ne contient aucun identifiant
d'expérience, la provenance du protocole reste visible et la source
expérimentale est déclarée indisponible.

Il ne crée jamais une direction ou une amplitude de déplacement.

## Information nouvelle et répétition

Une proposition peut être classée :

- `NEW_INFORMATION` si l'hypothèse n'a pas encore de déclaration correspondante;
- `PARTIAL_REPEAT` si protocole et variable modifiée se recouvrent;
- `EXACT_REPEAT` si hypothèse, protocole, type, référence et variables sont
  identiques;
- `ALREADY_COMPLETED` si le protocole est déclaré terminé;
- `BLOCKED_BY_MISSING_DECLARATION` ou `BLOCKED_BY_NON_COMPARABILITY` si la mémoire
  ne permet pas la comparaison;
- `DEFERRED_BY_USER` si la discrimination a été différée;
- `STILL_INFORMATIVE` si la même hypothèse est testée dans un périmètre déclaré
  différent.

Cette classification est descriptive. Elle n'empêche jamais l'acquisition.

## Chemin expérimental épuisé

Un chemin est épuisé uniquement lorsqu'une campagne ou discrimination existante
n'expose plus d'ambiguïté ni de protocole suivant. Cela signifie qu'aucune
nouvelle discrimination n'est disponible dans le périmètre structuré actuel,
pas que toute recherche acoustique est terminée.

La présence technique d'un chemin épuisé ne prend pas le pas sur une déclaration
`UNKNOWN` ou une provenance expérimentale absente. Dans ces cas, l'état reste
`INSUFFICIENT_DECLARATION` et le besoin suivant demande la déclaration ou la
provenance manquante.

## Limites causales et décisionnelles

Tous les états portent `causality_status = NOT_ESTABLISHED`. PR-045 ne modifie
aucun score acoustique, statut d'hypothèse source, classement, recommandation,
éligibilité de plan ou proposition PR-044.

## Relation avec PR-036 à PR-044

PR-036 à PR-039 fournissent les propositions contrôlées de réflexion, leurs
déclarations, comparaisons et statuts observationnels. PR-040 à PR-042 organisent
la décision et le langage utilisateur. PR-043 fournit la déclaration générique
d'expérience. PR-044 construit un protocole de positionnement réversible.
PR-045 lit ces objets sans les réécrire et expose une section technique unique
après les campagnes et discriminations existantes. L'état pré-calculé est
ensuite présent dans le contexte avant la planification, afin qu'un consommateur
futur puisse le consulter explicitement. Aucun planificateur actuel ne le
consomme et son exposition ne modifie donc aucune sélection.
