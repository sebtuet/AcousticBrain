# PR-022A — Contrat RoomGeometry

## Finalité

`RoomGeometry` est la représentation géométrique validable et calculable qui
servira progressivement d'entrée aux moteurs. Elle reste indépendante de la
technologie d'interface, des mesures REW et des résultats acoustiques.

Les trois responsabilités restent séparées :

- `RoomDescription` contient la saisie déclarative de l'utilisateur ;
- `RoomGeometry` contient une représentation géométrique explicite ;
- `Room` reste le modèle historique de compatibilité.

PR-022A ne construit pas une géométrie à partir de ces sources. Cette
responsabilité appartient au futur `RoomGeometryBuilder` de PR-022B.

## Repère et unités

Le repère reprend sans conversion implicite celui de `RoomDescription` :

- origine au coin avant-gauche du sol ;
- `x` du mur avant vers le mur arrière ;
- `y` du mur gauche vers le mur droit ;
- `z` du sol vers le plafond ;
- toutes les coordonnées et dimensions sont exprimées en mètres.

`GeometryPoint` conserve un identifiant stable et trois coordonnées finies et
non négatives. Le contrat local ne vérifie pas encore son inclusion dans le
volume de salle.

## Surfaces et ouvertures

`RoomSurface` représente une surface rectangulaire par un identifiant, un type
stable, une origine et deux dimensions locales strictement positives. Les types
initiaux sont les quatre murs, le sol et le plafond.

`GeometryOpening` est distinct de `RoomOpening`. Il conserve son identifiant,
l'identifiant de sa surface porteuse, ses décalages locaux et ses dimensions.
Cette séparation interdit à la géométrie calculable de dépendre
rétrospectivement du modèle de saisie utilisateur.

Le rattachement à une surface existante, l'inclusion dans ses limites et les
chevauchements sont des invariants relationnels différés à PR-022B.

## Provenance et modèle

`GeometrySource` rend la source exclusive et explicite :

- `LEGACY_ROOM` ;
- `ROOM_DESCRIPTION`.

Deux sources ne sont jamais fusionnées dans le contrat. `RoomGeometryModel`
contient initialement uniquement `RECTANGULAR`. `model_version` est un entier
strictement positif destiné à versionner la représentation, indépendamment du
schéma JSON de `RoomDescription`.

`completeness` est bornée entre 0 et 100. Elle décrit la complétude des faits
géométriques disponibles ; ce n'est ni une confiance acoustique ni un score de
salle.

## RoomGeometry

Le modèle conserve :

- les dimensions effectives ;
- les surfaces nommées ;
- les points des enceintes ;
- les positions d'écoute ;
- les ouvertures ;
- une provenance exclusive ;
- le type et la version du modèle ;
- la complétude géométrique.

Toutes les collections sont des tuples immuables et leurs identifiants sont
uniques au sein de leur catégorie.

## Invariants et exclusions de PR-022A

- aucune valeur non finie ;
- aucune dimension nulle ou négative ;
- aucune coordonnée ou aucun décalage négatif ;
- aucun identifiant vide ou dupliqué dans sa catégorie ;
- aucune dépendance à l'UI, au pipeline ou aux mesures ;
- aucun volume, surface totale, mode, Schroeder ou trajet de réflexion ;
- aucun builder, adaptateur, stage, diagnostic, recommandation ou rapport ;
- aucune modification de `Project`, `AnalysisContext` ou des moteurs existants.

## PR-022B — Construction et adaptation

`RoomGeometryBuilder` expose deux entrées volontairement distinctes :

- `from_description(RoomDescription)` ;
- `from_legacy_room(Room)`.

Il n'existe aucune méthode générique qui choisirait ou fusionnerait les sources.
Une description est validée par `RoomDescriptionValidator` avant toute
construction. Un échec lève `RoomGeometryBuildException`, qui conserve les
erreurs structurées et n'expose aucun objet géométrique partiel. Les dimensions
legacy sont contrôlées explicitement, car le modèle historique ne protège pas
ses propres invariants.

Le builder produit toujours les surfaces dans cet ordre : mur avant, mur
arrière, mur gauche, mur droit, sol, plafond. Les origines suivent le repère du
contrat et les dimensions locales sont : largeur × hauteur pour les murs,
longueur × largeur pour le sol et le plafond.

Les ouvertures conservent leurs décalages locaux. Leur surface déclarative est
convertie vers l'identifiant stable correspondant (`front_wall`, `rear_wall`,
`left_wall`, `right_wall`). Les enceintes, positions d'écoute et ouvertures sont
triées par identifiant afin de garantir une construction déterministe.

La complétude suit une règle factuelle explicite :

- dimensions valides et six surfaces : 60 points ;
- au moins une enceinte : 20 points ;
- au moins une position d'écoute : 20 points.

Les ouvertures sont optionnelles et leur absence ne pénalise pas une salle
fermée. Une géométrie legacy possède donc une complétude de 60/100. Cette valeur
ne mesure toujours aucune qualité acoustique.

PR-022B n'ajoute aucun stage, aucun champ à `Project` ou `AnalysisContext`, et
ne modifie aucun moteur acoustique.

## PR-022C — Résolution et intégration au contexte

`Project.room_geometry` et `AnalysisContext.room_geometry` sont optionnels
avant l'exécution. `RoomGeometryStage` construit ensuite une seule géométrie et
affecte exactement la même instance aux deux emplacements.

La résolution est explicite et ordonnée :

1. si `Project.room_description` est présente, elle est la seule source et le
   stage appelle `RoomGeometryBuilder.from_description` ;
2. sinon, le stage appelle `from_legacy_room` avec `Project.room` ;
3. en l'absence des deux sources, le stage lève une erreur explicite.

Une erreur de construction de la description est propagée. Elle ne déclenche
jamais de fallback vers `Room` et ne remplace pas une éventuelle géométrie déjà
présente dans le projet ou le contexte. Les deux sources ne sont ni comparées,
ni fusionnées à ce stade.

Le stage est exécuté immédiatement après la construction du contexte, avant
les analyses de mesure, physiques et temporelles. Aucun consommateur acoustique
ne lit encore `room_geometry` dans PR-022C : `PhysicsStage`, `AnalysisStage`,
SBIR, les propriétés de salle et les modes continuent d'utiliser explicitement
`Project.room`.

## PR-022D — Premiers consommateurs géométriques

`RoomAcoustics`, `RoomModesAnalyzer` et le calculateur axial historique
`ModesCalculator` acceptent désormais exclusivement `RoomGeometry`. Ils lisent
les dimensions effectives dans `geometry.dimensions` et refusent directement
un objet `Room`. La compatibilité legacy est donc contrôlée en amont par
`RoomGeometryBuilder` et `RoomGeometryStage`, jamais par une adaptation cachée
dans un moteur acoustique.

`PhysicsStage` exige une géométrie déjà résolue et l'utilise comme véritable
source pour :

- le volume ;
- la surface au sol ;
- la surface intérieure rectangulaire totale ;
- la fréquence de Schroeder ;
- les modes axiaux, tangentiels et obliques.

Les formules, constantes, bornes et boucles modales restent inchangées. Deux
géométries de dimensions identiques, l'une legacy et l'autre déclarative,
produisent des propriétés strictement égales, les mêmes fréquences flottantes
et les modes dans le même ordre. Le golden report legacy reste inchangé.

`AnalysisStage` et SBIR continuent à lire `Project.room`. ETC, les positions,
les ouvertures et les futures corrélations de surfaces ne sont pas migrés dans
PR-022D.

## PR-022E — Provenance, restitution et compatibilité

`RoomGeometryComparison` conserve le statut de coexistence des sources :

- `SINGLE_SOURCE` lorsqu'une seule source est disponible ;
- `EQUIVALENT` lorsque les trois dimensions sont strictement identiques ;
- `DIVERGENT` avec les champs concernés et leurs écarts absolus en mètres.

La comparaison est effectuée par `RoomGeometryStage` après la construction
réussie. Elle ne participe pas à la sélection : `ROOM_DESCRIPTION` reste la
source prioritaire. Une divergence est un avertissement structuré, non un
blocage, et ne provoque ni fusion ni fallback.

Le rapport expose la source, le modèle, sa version, les dimensions effectives,
la complétude et le statut de compatibilité. L'avertissement n'apparaît que pour
`DIVERGENT`; deux sources équivalentes ne modifient ni les propriétés, ni les
modes, ni les scores acoustiques.

La traçabilité conserve séparément :

- `room_geometry.source` ;
- `room_geometry.model` et `model_version` ;
- les trois dimensions effectives ;
- `room_geometry.completeness` ;
- le statut de comparaison ;
- chaque écart dimensionnel en cas de divergence.

### État de migration après PR-022

Consommateurs de `RoomGeometry` :

- propriétés rectangulaires de salle ;
- volume, surface au sol et surface totale ;
- fréquence de Schroeder ;
- modes rectangulaires complets et calcul axial de compatibilité.

Consommateurs encore legacy :

- SBIR et les distances historiques d'enceintes ;
- ETC et les réflexions précoces ;
- placement et comparaison des positions ;
- surfaces acoustiques, matériaux et trajets de réflexion.

PR-022E n'ajoute aucun calcul acoustique, ne migre aucun consommateur
supplémentaire et ne transforme pas une divergence géométrique en diagnostic
acoustique.
