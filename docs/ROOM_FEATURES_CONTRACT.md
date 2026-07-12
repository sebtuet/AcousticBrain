# PR-023A — Contrats déclaratifs des caractéristiques de salle

## Finalité et frontières

PR-023A étend uniquement `RoomDescription`, source de saisie utilisateur. Les
nouveaux faits sont tous optionnels et n'affectent ni `RoomGeometry`, ni le
pipeline, ni les analyses existantes.

Une description contenant seulement un nom et des dimensions reste valide.
Les anciennes constructions de `SpeakerPosition` restent valides et leur
orientation vaut `None`.

Cette sous-PR ne modifie pas le schéma JSON version 1. Une description enrichie
ne doit donc pas encore être confiée au codec existant pour être persistée ; la
persistance versionnée appartient à PR-023C.

## Orientation des enceintes

`SpeakerOrientation.yaw_degrees` décrit une rotation autour de l'axe vertical
`+z`. L'orientation `0°` suit `+x`. Vue depuis le plafond, une rotation positive
va de `+x` vers `+y`.

Dans ce repère, les toe-in de référence sont :

- enceinte gauche : `+15°` ;
- enceinte droite : `-15°`.

L'angle doit être fini et compris entre `-180°` et `+180°`. L'absence
d'orientation est représentée par `SpeakerPosition.orientation = None`. Pitch,
roll, directivité et point visé sont différés.

## Surfaces et matériaux

`RoomDescriptionSurface` nomme les quatre murs, le sol et le plafond. Cet enum
appartient à la couche déclarative et n'est pas confondu avec
`RoomSurfaceKind`, qui appartient à la géométrie calculable.

`SurfaceMaterialDescription` associe un `SurfaceMaterialType` à une surface et
peut conserver un détail textuel. Un type de matériau ne possède aucun
coefficient implicite d'absorption, de diffusion ou de transmission.

Une surface ne peut recevoir qu'un matériau principal dans une même
`RoomDescription`. Une information absente reste absente ; aucun matériau par
défaut n'est créé.

## Zones de revêtement

`SurfaceCoveringZone` décrit une zone rectangulaire dans le repère local de sa
surface. Les deux offsets sont les coordonnées locales de son coin minimal.
Les dimensions et offsets forment un groupe atomique : ils sont tous `None`,
ou tous renseignés.

Cette règle permet de déclarer l'existence du tapis de référence sur le sol,
avec un placement encore inconnu, sans inventer ses dimensions.

L'inclusion dans la surface, les chevauchements et la conversion vers
`RoomGeometry` sont différés.

## Mobilier simple

`RoomFurnitureDescription` conserve un identifiant, un `FurnitureType`, un
détail optionnel et une boîte englobante optionnelle. Lorsque la boîte est
renseignée, `(x_m, y_m, z_m)` représente son coin minimal dans le repère de la
salle. Les trois coordonnées et les trois dimensions sont toutes absentes ou
toutes présentes.

Les coordonnées doivent être finies et non négatives ; les dimensions doivent
être finies et strictement positives. Aucune influence sur le volume ou les
réflexions n'est calculée.

## Traitements acoustiques

`AcousticTreatmentDescription` conserve un identifiant, un type, un détail et
un placement rectangulaire optionnel sur une surface. La surface, les offsets
et les dimensions sont tous `None`, ou tous renseignés.

Les coefficients, traitements en angle, volumes autoportants, performances et
courbes fréquentielles sont différés. Le mot `ABSORBER` ne produit notamment
aucun coefficient d'absorption.

## Agrégation et immutabilité

`RoomDescription` ajoute quatre tuples vides par défaut :

- `surface_materials` ;
- `covering_zones` ;
- `furniture` ;
- `acoustic_treatments`.

Les collections et modèles sont immuables. Les surfaces de matériaux sont
uniques et les identifiants des zones, meubles et traitements sont uniques dans
leur catégorie.

## Invariants et exclusions

- valeurs numériques présentes finies ;
- offsets et coordonnées non négatifs ;
- dimensions présentes strictement positives ;
- groupes de placement entièrement absents ou entièrement renseignés ;
- champs optionnels conservés à `None` ;
- aucune validation relationnelle ;
- aucune persistance ou migration de schéma ;
- aucune interface utilisateur ;
- aucun builder, stage ou changement de pipeline ;
- aucune modification de `RoomGeometry` ;
- aucun calcul acoustique, coefficient, diagnostic ou recommandation.

## PR-023B — Validation relationnelle

`RoomDescriptionValidator` valide désormais les features placées sans modifier
leurs contrats. Une feature dont le placement complet est absent reste valide
et n'est ni positionnée implicitement, ni soumise à un contrôle de limites.

### Repères locaux des surfaces

Pour les zones de revêtement et les traitements surfaciques :

- murs avant et arrière : axe horizontal local `y`, axe vertical local `z` ;
- murs gauche et droit : axe horizontal local `x`, axe vertical local `z` ;
- sol et plafond : premier axe local `x`, second axe local `y`.

Les limites correspondantes sont respectivement largeur × hauteur, longueur ×
hauteur et longueur × largeur. Une zone ou un traitement peut toucher la
frontière de sa surface.

### Mobilier

La boîte englobante d'un meuble doit être entièrement incluse dans le volume
fermé de la salle. Les maxima sont calculés depuis le coin minimal déclaré et
les trois dimensions. Un contact avec une paroi, le sol ou le plafond est
valide.

### Politique de chevauchement

Une intersection est interdite seulement lorsqu'elle possède une mesure
strictement positive au sein d'une même catégorie :

- aire positive entre deux zones de revêtement portées par la même surface ;
- volume positif entre deux boîtes de mobilier ;
- aire positive entre deux traitements portés par la même surface.

Les contacts par face, arête ou coin sont valides. Les surfaces distinctes ne
sont jamais comparées. Les catégories ne sont pas comparées entre elles : un
tapis peut donc se trouver sous un canapé, et un revêtement mural peut partager
une zone avec un traitement déclaré.

### Erreurs structurées

Les codes ajoutés sont :

- `COVERING_ZONE_OUTSIDE_SURFACE` ;
- `COVERING_ZONE_OVERLAP` ;
- `FURNITURE_OUTSIDE_ROOM` ;
- `FURNITURE_OVERLAP` ;
- `TREATMENT_OUTSIDE_SURFACE` ;
- `TREATMENT_OVERLAP` ;
- `INVALID_FEATURE_PLACEMENT`.

`INVALID_FEATURE_PLACEMENT` constitue un contrôle défensif pour un modèle
corrompu ou reconstruit en contournant les invariants locaux. Il n'invente
aucune valeur manquante. Les features et les paires sont triées par identifiant,
et les catégories sont produites dans l'ordre zones, mobilier, traitements,
après les erreurs géométriques historiques.

PR-023B ne modifie ni le codec JSON, ni le schéma, ni l'UI, ni
`RoomGeometryBuilder`, ni la complétude, le pipeline ou les analyses
acoustiques.

## PR-023C — Persistance JSON version 2

`RoomDescriptionJsonCodec` écrit systématiquement `schema_version: 2`. Le
schéma conserve les quatre collections déclaratives, l'orientation optionnelle
de chaque enceinte et tous les champs de placement optionnels.

Les valeurs absentes sont sérialisées explicitement à `null`; les collections
absentes du domaine sont écrites comme des listes vides. Aucun coefficient
acoustique n'est ajouté au payload.

Les collections sont sérialisées dans un ordre canonique : identifiant pour
les enceintes, écoutes, ouvertures, zones, meubles et traitements ; valeur de
surface pour les matériaux principaux. Les clés JSON restent triées. Deux
descriptions contenant les mêmes faits dans un ordre différent produisent donc
le même document.

### Compatibilité v1

Le lecteur accepte les versions 1 et 2. Un fichier v1 reconstruit les nouveaux
champs avec leurs absences contractuelles : orientation à `None` et collections
vides. Le résultat de chargement expose :

- `source_schema_version` ;
- `requires_migration`.

Pour une source v1, `requires_migration` vaut `True`. Aucune réécriture n'est
effectuée pendant la lecture. Une écriture ultérieure produit explicitement un
document v2 complet. Le chargeur applicatif propage ces deux faits et la
commande affiche séparément versions source et cible.

Le lecteur v2 tolère l'absence des nouveaux champs pour préserver le
fonctionnement de l'adaptateur UI existant, qui n'est pas encore enrichi. Le
writer v2 les matérialise toujours sous leur forme canonique.

### Erreurs

Les JSON invalides, versions inconnues, enums inconnus, valeurs non finies,
dimensions invalides et structures incorrectes restent des erreurs
structurées. Leurs chemins incluent la collection, l'index et le champ lorsque
celui-ci est identifiable. Une erreur relationnelle PR-023B produit
`INVALID_GEOMETRY`, conserve son code de validation et n'expose aucune
description partielle.

PR-023C ne modifie pas les formulaires, `RoomGeometry`, le builder, la
complétude, le pipeline ou les calculs acoustiques.

## PR-023D — Conversion vers RoomGeometry

`RoomGeometry` reçoit des contrats calculables distincts des modèles de saisie :

- `GeometrySpeakerOrientation` ;
- `GeometrySurfaceMaterial` et `GeometryMaterialType` ;
- `GeometryCoveringZone` ;
- `GeometrySurfaceRectangle` ;
- `GeometryFurniture`, `GeometryFurnitureType` et `GeometryBox` ;
- `GeometryAcousticTreatment` et son enum calculable ;
- `GeometryCoordinate` pour les coins globaux sans identité métier.

Aucun objet déclaratif PR-023A n'est stocké dans `RoomGeometry`. Les enums sont
convertis explicitement par leur code stable et la provenance globale reste
`ROOM_DESCRIPTION`.

### Orientations

Le noyau historique `speakers: tuple[GeometryPoint, ...]` reste inchangé.
`speaker_orientations` constitue une collection séparée, ordonnée par
`speaker_id`, avec une entrée par enceinte déclarée. Un angle absent reste
explicitement `None`.

### Matériaux et placements surfaciques

Les matériaux principaux référencent les identifiants stables des six surfaces
calculables. Ils ne contiennent aucun coefficient acoustique.

Une zone ou un traitement placé produit un `GeometrySurfaceRectangle` qui
conserve :

- les offsets et dimensions dans le repère local déclaré ;
- le coin global minimal ;
- le coin global maximal.

La conversion des axes est explicite : `y/z` pour les murs avant et arrière,
`x/z` pour les murs latéraux, `x/y` pour le sol et le plafond. La coordonnée
normale est fixée à la position de la surface correspondante. Une feature non
placée reste présente avec `placement=None`.

### Mobilier

Une boîte de mobilier placée devient un `GeometryBox`. Son coin minimal est la
position déclarée ; son coin maximal est obtenu par addition des trois
dimensions. Un meuble non placé reste présent avec `bounding_box=None`.

### Complétude séparée

La propriété historique `RoomGeometry.completeness` reste strictement
inchangée : 60 points pour le noyau, 20 pour les enceintes et 20 pour les
positions d'écoute.

`feature_completeness` est une connaissance géométrique séparée et vaut `None`
lorsqu'aucune feature PR-023 n'est renseignée. Lorsqu'elle existe, elle conserve
cinq couvertures de 0 à 100 :

- enceintes possédant une orientation ;
- surfaces possédant un matériau principal, sur six surfaces ;
- zones de revêtement placées ;
- meubles possédant une boîte ;
- traitements surfaciques placés.

Son score est la moyenne arithmétique non pondérée de ces cinq couvertures.
Une catégorie optionnelle absente vaut 0 dans ce score d'enrichissement, mais
ne diminue jamais la complétude ou la validité géométrique de base.

`RoomGeometry` vérifie également que les orientations référencent une enceinte
existante et que les features surfaciques référencent une surface calculable.

PR-023D ne modifie aucun consommateur acoustique, stage, diagnostic,
recommandation ou rapport. Le noyau géométrique legacy et les résultats
existants restent identiques.

## PR-023E — UI progressive et restitution

L'interface définit trois niveaux purement présentatifs :

- `MINIMAL` : nom et dimensions ;
- `GUIDED` : enceintes, orientations, écoute et matériaux principaux ;
- `EXPERT` : ouvertures, zones de revêtement, mobilier et traitements en plus
  des sections guidées.

`RoomDescriptionEditorLevel` n'appartient ni à `RoomDescriptionFormState`, ni à
`RoomDescription`, ni au JSON. `section_visibility` produit seulement les
booléens de visibilité. Les sections masquées restent dans l'état complet et
sont validées, chargées et sauvegardées sans suppression. Changer de niveau ne
modifie donc jamais le contenu sémantique du domaine.

L'adaptateur UI prend en charge toutes les features v2. Une chaîne vide devient
`None` uniquement pour un champ contractuellement optionnel ; aucune valeur
numérique ou type par défaut n'est inventé. Le chargement v1 continue de
produire des lignes nouvelles absentes et le prochain enregistrement utilise le
codec v2 canonique.

La restitution géométrique affiche désormais :

- la provenance et la complétude géométrique de base ;
- la complétude séparée des features, ou `indisponible` ;
- le nombre d'orientations disponibles ;
- le nombre de matériaux ;
- les nombres de revêtements, meubles et traitements déclarés et placés.

La traçabilité conserve la complétude détaillée, chaque orientation, chaque
type de matériau principal et l'état placé/non placé des zones, meubles et
traitements. Ces faits restent attachés à `RoomGeometry` et ne deviennent ni
scores acoustiques, ni causes diagnostiques.

PR-023E ne modifie aucun moteur acoustique, coefficient, corrélation,
diagnostic ou recommandation.
