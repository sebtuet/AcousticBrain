# Contrat — rapport acoustique orienté décision

Statut : contrat de présentation de PR-041. Il ne modifie aucun contrat
scientifique, classement, recommandation, protocole ou critère d’éligibilité.

## Utilisateur cible et rôle

La page `DÉCISION ACOUSTIQUE` s’adresse à une personne qui sait réaliser et
exporter des mesures REW, sans nécessairement maîtriser l’interprétation
acoustique. Elle doit permettre de comprendre la dernière comparaison et la
prochaine décision avant les détails scientifiques.

La page est une projection des objets déjà présents dans `Report`. Elle ne
constitue ni un moteur de raisonnement, ni un planificateur, ni un validateur de
mesures.

## Audit factuel préalable

Le rapport reproductible de `develop` après PR-040 contient 850 lignes et
commence par la section détaillée `PROCHAINE ÉTAPE DE POSITIONNEMENT`. Cette
section explique correctement qu’aucune action ne doit être inventée, mais le
verdict de la dernière expérience reste situé beaucoup plus loin dans
`ÉVOLUTION DES EXPÉRIENCES`.

Dans le contexte `exp-006` fourni pour PR-041 :

- la dernière comparaison locale est `exp-005 → exp-006`;
- son évolution acoustique est `MIXED`;
- l’évolution de l’hypothèse est `INCONCLUSIVE`;
- le protocole et l’hypothèse ne sont pas déclarés;
- aucun candidat du planificateur n’est éligible;
- plusieurs recommandations actives restent exposées;
- une discrimination est différée par décision utilisateur;
- les mesures sont techniquement exploitables.

Le verdict n’était donc pas visible dans les premières lignes. Plusieurs
recommandations concurrentes étaient visibles sans décision unique, et le
rapport ne reliait pas immédiatement l’absence d’action aux conditions de test
non déclarées, à l’inéligibilité du plan et à la décision différée.

## Hiérarchie du rapport

L’ordre de présentation est :

1. titre et projet;
2. `DÉCISION ACOUSTIQUE`;
3. section PR-040 `PROCHAINE ÉTAPE DE POSITIONNEMENT`;
4. salle et géométrie;
5. historique, comparaisons et campagnes;
6. recommandations et planification;
7. diagnostics et traçabilité.

PR-041 synthétise la décision. PR-040 conserve le détail opérationnel et les
limites propres au positionnement. Les données techniques existantes ne sont ni
supprimées ni réordonnées après ces deux pages.

## Sources autorisées

Le présentateur lit uniquement :

- la dernière comparaison locale déjà ordonnée;
- le candidat déjà recommandé par le planificateur;
- les recommandations structurées, leur priorité et leur statut;
- les propositions PR-036 reliées à une déclaration PR-037 `PLANNED`;
- les décisions de discrimination `DEFERRED`;
- les diagnostics et leur ordre de présentation déjà calculé.

Il ne lit pas les mesures brutes et ne recalcule aucun score.

## Traduction des verdicts

La dernière comparaison locale est sélectionnée selon l’ordre fourni dans
`local_comparisons`. Sa valeur `acoustic_outcome` est traduite ainsi :

- `IMPROVED` : amélioration mesurable dans le périmètre testé;
- `DEGRADED` : dégradation mesurable dans le périmètre testé;
- `MIXED` : améliorations et dégradations, sans verdict global simple;
- `UNCHANGED` : aucun changement acoustique significatif observé;
- `INCONCLUSIVE` : les mesures ne permettent pas de conclure.

Une comparaison absente ou différente de `COMPARABLE` est présentée comme non
comparable de manière fiable. L’expérience avant/après, le protocole lorsqu’il
existe et la limite au périmètre mesuré restent visibles.

`MIXED` n’est jamais traduit en amélioration. Un changement mesuré ne devient
jamais une causalité.

## Sélection d’une action existante

Le présentateur applique exclusivement la précédence explicite suivante :

1. une déclaration PR-037 `PLANNED` reliée à une proposition PR-036;
2. le candidat éligible déjà recommandé par le planificateur;
3. l’unique recommandation `ACTIVE` de priorité maximale.

Cette précédence ne modifie pas les objets sources. Une recommandation n’est
pas promue dans le moteur et une proposition PR-036 non déclarée ne devient pas
une action.

Pour les recommandations, plusieurs éléments de même priorité maximale
constituent une égalité non résolue. Aucun nom, identifiant, libellé ou ordre de
collection n’est utilisé pour les départager.

## Détail opérationnel

Une cible, une direction ou une amplitude n’est affichée que si elle existe
dans le candidat ou la proposition source :

- `speaker_id` identifie l’enceinte;
- `movement_direction`, `proposed_direction` ou `direction` fournit la direction;
- `proposed_displacement_m` fournit l’amplitude, avec une conversion d’unité en
  centimètres;
- `surface` ou la cible PR-036 identifie une surface de masquage.

Une action planifiée sans cible exploitable reste présentée comme piste dont le
déplacement exact n’est pas déterminé. Aucune valeur par défaut n’est inventée.

Les mesures L, R et L+R et les variables à maintenir fixes sont affichées
uniquement lorsqu’une expérience contrôlée ou déclarée nécessite une nouvelle
acquisition. Une recommandation abstraite n’entraîne pas automatiquement un
protocole de mesure.

## Actions différées

Une recommandation ou discrimination `DEFERRED` n’est jamais sélectionnée comme
action active. La page indique :

- qu’une investigation utile est en pause par décision utilisateur;
- que l’utilisateur peut décider de la reprendre;
- qu’AcousticBrain ne la réactive pas automatiquement.

## Expériences non déclarées

Si la dernière comparaison ne possède pas de protocole ou d’hypothèse source,
la page indique qu’AcousticBrain ne sait pas formellement quelle variable était
testée, ni si la configuration devait rester inchangée. La déclaration de ces
conditions devient alors une étape de déblocage, pas une interprétation
acoustique.

L’absence de déclaration ne prouve pas qu’un déplacement ou une modification a
eu lieu. Le présentateur ne qualifie donc pas l’expérience de « nouvelle
position » et ne crée aucun modèle de répétabilité implicite.

## Faits, limites et confiance

La page affiche au maximum trois faits, dans cet ordre stable :

1. observations de la dernière comparaison;
2. conclusion existante du diagnostic de qualité des mesures;
3. observations du diagnostic déjà placé en tête par le prioriseur.

Elle affiche au maximum deux limites contextuelles, auxquelles s’ajoute
toujours la limite causale explicite, soit trois limites au total. Elle utilise
uniquement les catégories :

- `Établi par les mesures`;
- `Explication possible`;
- `Non établi`.

Le statut technique `NOT_ESTABLISHED` reste visible avec le libellé utilisateur
de causalité.

## Longueur et stabilité

La section apparaît dans les premières lignes utiles et ne dépasse pas 45
lignes dans les scénarios complexes couverts. Les collections sont lues dans
leur ordre scientifique existant; les déduplications conservent la première
occurrence. Deux rendus du même `Report` sont identiques.

## Interdictions

Le présentateur ne peut pas :

- créer une hypothèse ou un objectif à partir d’un score;
- recalculer ou modifier une priorité;
- créer ou réactiver un protocole;
- modifier une campagne ou une décision utilisateur;
- transformer `MIXED` en amélioration;
- inventer une cible, une direction ou une distance;
- affirmer une position optimale ou une amélioration garantie;
- attribuer une cause;
- modifier l’éligibilité, le classement ou les recommandations;
- muter les modèles scientifiques;
- masquer `NOT_ESTABLISHED`.
