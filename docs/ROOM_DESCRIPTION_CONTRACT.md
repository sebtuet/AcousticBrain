# PR-020A — Contrat RoomDescription

## Finalité et séparation des sources

`RoomDescription` représente exclusivement ce que l'utilisateur déclare sur
sa salle. Ce modèle ne contient aucun résultat observé dans une mesure REW,
aucune analyse acoustique et aucun calcul géométrique ou physique.

La description utilisateur et les observations du moteur restent deux sources
indépendantes. Un futur moteur `RoomGeometry` pourra les comparer sans modifier
ni attribuer rétrospectivement des faits à l'autre source.

PR-020A ne remplace pas encore les modèles historiques `Room` et `Speaker` et
ne modifie pas `Project`. La migration et la persistance appartiennent à
PR-020C.

## Repère et unités

Toutes les longueurs et coordonnées sont exprimées en mètres. Le repère est
cartésien et orthogonal :

- l'origine `(0, 0, 0)` est le coin avant-gauche du sol ;
- `x` progresse du mur avant vers le mur arrière ;
- `y` progresse du mur gauche vers le mur droit ;
- `z` progresse du sol vers le plafond.

Les identifiants sont stables et destinés à la future persistance. Ils ne sont
pas des libellés d'analyse.

## RoomDimensions

`length_m`, `width_m` et `height_m` décrivent les dimensions intérieures. Elles
doivent être finies et strictement positives. Le contrat ne calcule ni volume,
ni surface, ni fréquence acoustique.

## SpeakerPosition et ListeningPosition

Chaque position possède un identifiant et trois coordonnées finies et
positives ou nulles. PR-020A ne vérifie pas encore que le point appartient au
volume décrit : cette validation relationnelle appartient à PR-020B.

## RoomOpening

Une ouverture est un rectangle porté par une paroi verticale stable : mur
avant, arrière, gauche ou droit. Elle conserve un identifiant, un décalage
horizontal depuis l'origine locale de la paroi, un décalage vertical depuis le
sol, une largeur et une hauteur.

Sur les murs avant et arrière, l'axe horizontal local suit `y` depuis le côté
gauche. Sur les murs gauche et droit, il suit `x` depuis le mur avant. L'axe
vertical local suit toujours `z` depuis le sol.

Les décalages doivent être finis et non négatifs ; les dimensions doivent être
finies et strictement positives. L'inclusion dans la paroi et les éventuels
chevauchements seront vérifiés par PR-020B.

## RoomDescription

La description regroupe un nom, des dimensions, des enceintes, des positions
d'écoute et des ouvertures. Les collections sont des tuples immuables. Les
identifiants sont uniques au sein de leur catégorie.

`RoomObstacle` est volontairement différé jusqu'à ce que sa sémantique soit
nécessaire. Aucun obstacle générique n'est introduit prématurément.

## Invariants de PR-020A

- aucune valeur géométrique non finie ;
- aucune dimension nulle ou négative ;
- aucune coordonnée ou aucun décalage négatif ;
- aucun identifiant vide ou dupliqué dans sa catégorie ;
- aucun calcul acoustique ou géométrique dérivé ;
- aucune dépendance aux mesures, analyses ou diagnostics ;
- aucune persistance et aucune interface utilisateur.

## PR-020B — Validation géométrique relationnelle

`RoomDescriptionValidator` reçoit uniquement une `RoomDescription` et retourne
une `RoomDescriptionValidationResult`. Le résultat contient un tuple immuable
d'erreurs et expose `is_valid` ainsi que les codes rencontrés.

Une `RoomDescriptionValidationError` ne contient aucun message d'interface.
Elle conserve exclusivement un `RoomDescriptionValidationCode`, un type
d'entité, les identifiants concernés et les champs géométriques fautifs. Les
codes initiaux sont :

- `SPEAKER_OUTSIDE_ROOM` ;
- `LISTENING_POSITION_OUTSIDE_ROOM` ;
- `OPENING_OUTSIDE_SURFACE` ;
- `OPENING_ZERO_AREA` ;
- `OPENING_OVERLAP`.

Les limites du volume sont inclusives : un point situé exactement sur une
paroi reste valide. Pour une ouverture, le validateur utilise la largeur de la
salle sur les murs avant et arrière, la longueur sur les murs gauche et droit,
et la hauteur de salle sur toutes les parois.

Deux ouvertures se chevauchent uniquement si leur intersection possède une
largeur et une hauteur strictement positives. Un contact par une arête ou un
coin est donc valide. Les comparaisons sont limitées aux ouvertures portées par
la même surface et les paires d'identifiants sont produites dans un ordre
déterministe.

La surface nulle est déjà interdite par le contrat local de `RoomOpening`. Le
validateur la refuse également de manière défensive si un objet corrompu ou
désérialisé sans validation lui est transmis.

PR-020B ne calcule aucun volume, mode, trajet de réflexion, délai, distance
acoustique, diagnostic ou recommandation.

## PR-020C — Persistance JSON et Project

`RoomDescriptionJsonCodec` utilise une enveloppe explicite :

```json
{
  "schema_version": 1,
  "room_description": {
    "name": "Studio",
    "dimensions": {},
    "speakers": [],
    "listening_positions": [],
    "openings": []
  }
}
```

Les identifiants sont conservés sans transformation et les surfaces
d'ouverture utilisent les valeurs stables de `RoomOpeningSurface`. Toutes les
collections du schéma sont obligatoires, même lorsqu'elles sont vides. La
sérialisation est déterministe grâce au tri des clés JSON et refuse les valeurs
non finies.

Le chargement reconstruit d'abord les modèles PR-020A, puis exécute
obligatoirement `RoomDescriptionValidator`. Une description géométriquement
invalide n'est jamais exposée dans `RoomDescriptionLoadResult`.

Les erreurs de persistance sont structurées avec un code et un chemin composé
de noms de champs et d'indices :

- `INVALID_JSON` ;
- `UNKNOWN_SCHEMA_VERSION` ;
- `MISSING_FIELD` ;
- `INVALID_VALUE` ;
- `INVALID_GEOMETRY`.

Une erreur `INVALID_GEOMETRY` conserve également le code de validation PR-020B
et les identifiants concernés. Une tentative de sérialisation invalide lève
`RoomDescriptionPersistenceException`, qui porte le même tuple d'erreurs
structurées.

`Project.room_description` est optionnel et coexiste avec les modèles
historiques `Room` et `Speaker`. Sa présence ne déclenche aucun stage, aucune
analyse et aucun calcul acoustique. PR-020C n'ajoute aucun rendu utilisateur.

## PR-020D — Première interface locale

`RoomDescriptionEditorAdapter` constitue la frontière entre une technologie
d'interface et les contrats du domaine. Son état de formulaire ne contient que
des chaînes et des lignes immuables pour les enceintes, positions d'écoute et
ouvertures.

L'adaptateur ne construit jamais directement un `RoomDescription`. Il convertit
les champs numériques, fabrique l'enveloppe versionnée PR-020C, puis appelle
`RoomDescriptionJsonCodec.from_dict`. Les invariants PR-020A et la validation
PR-020B restent donc les seules sources de vérité. Une saisie invalide ou une
description géométriquement incohérente ne produit ni modèle ni JSON partiel.

Les opérations exposées sont :

- validation immédiate d'un état de formulaire ;
- sérialisation d'un état valide via le codec ;
- chargement JSON via le codec ;
- conversion d'une description validée vers un état éditable.

`RoomDescriptionTkApp` est un prototype local léger. Il fournit les champs de
dimensions, l'ajout et la suppression des enceintes, positions d'écoute et
ouvertures, ainsi que les actions de chargement et de sauvegarde. Les erreurs
sont affichées par leur code stable et leur chemin ; aucun texte métier n'est
ajouté au domaine.

Le prototype peut être lancé avec :

```bash
python -m acousticbrain.ui.room_description_tk
```

Tkinter dépend uniquement de l'adaptateur. Les modèles, le validateur et le
codec n'importent aucune technologie d'interface. PR-020D ne calcule aucune
distance, réflexion, fréquence, analyse ou recommandation acoustique.

## PR-020E — Intégration contrôlée et préparation de RoomGeometry

`RoomDescriptionProjectLoader` reçoit un `Project` existant et un chemin
explicite. Il lit le fichier avec `RoomDescriptionJsonCodec` et n'affecte
`Project.room_description` qu'après un chargement entièrement réussi. Une
erreur de fichier, de schéma, de valeur ou de géométrie laisse le projet
inchangé.

Les erreurs d'accès ajoutées sont `FILE_NOT_FOUND` et `FILE_READ_ERROR`. Elles
utilisent le même contrat structuré que les erreurs PR-020C et conservent le
chemin demandé.

Une commande applicative permet de sélectionner séparément le dossier de
mesures et le fichier de description :

```bash
python -m acousticbrain.commands.load_room_description \
  --measurements measurements \
  --room-description room-description.json
```

La commande charge un `Project`, y attache la description validée et retourne
un état JSON structuré. Elle ne lance pas `AcousticBrain`, le pipeline ou un
calcul acoustique.

`LegacyRoomAdapter` prépare une migration explicite vers le modèle historique
`Room`. Il copie uniquement le nom et les trois dimensions, après validation,
et retourne un nouvel objet. Il n'est appelé par aucun stage et ne remplace
jamais automatiquement `Project.room`.

### Stratégie de migration vers RoomGeometry

1. `Room` reste la géométrie historique utilisée par les moteurs actuels.
2. `RoomDescription` reste la source déclarative utilisateur, optionnelle et
   sans effet automatique.
3. Le futur module `RoomGeometry` consommera explicitement une description
   validée et produira ses propres faits géométriques structurés.
4. Les moteurs acoustiques migreront individuellement vers ces faits, avec des
   tests de compatibilité et un choix explicite de source.
5. L'adaptateur historique pourra être retiré seulement lorsque tous les
   consommateurs de `Room` auront migré.

Cette progression interdit qu'une simple présence de `room_description`
modifie silencieusement les résultats acoustiques existants.
