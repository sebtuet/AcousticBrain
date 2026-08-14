# Complete Room Modes Contract

PR-012A définit uniquement la connaissance structurée des modes propres de la
salle. Elle n'ajoute ni formule de calcul, ni moteur, ni stage, ni diagnostic,
ni présentation.

## RoomModeType

- `AXIAL` : un indice modal non nul ;
- `TANGENTIAL` : deux indices modaux non nuls ;
- `OBLIQUE` : trois indices modaux non nuls.

## RoomMode

Un mode conserve son type, les indices entiers `order_x`, `order_y` et
`order_z`, sa fréquence et les axes géométriques concernés.

Les propriétés historiques `axis` et `order`, ainsi que leur constructeur,
restent temporairement disponibles pour les consommateurs axiaux v0.11.0. Ils
ne font pas partie des champs sérialisés du nouveau contrat.

## RoomModesAnalysis

L'analyse regroupe tous les modes et les vues axiale, tangentielle et oblique,
leurs bornes fréquentielles, leurs nombres et la confiance du calcul. Elle ne
porte aucun score de qualité acoustique et aucun texte utilisateur.

PR-012A ne modifie ni `AnalysisContext`, ni `context.room_modes`, ni les
calculateurs et consommateurs existants.

## RoomModesAnalyzer

PR-012B ajoute un moteur pur recevant explicitement une salle, une fenêtre
fréquentielle inclusive et un ordre maximal par axe. La fréquence est calculée
par :

```text
f = c / 2 × √((nx/L)² + (ny/W)² + (nz/H)²)
```

La fréquence maximale constitue la borne métier principale ; l'ordre maximal
évite une exploration non bornée. Le moteur déduplique les triplets, trie les
modes par fréquence et retourne uniquement `RoomModesAnalysis`. Il ne modifie
pas le calculateur axial historique.

## Intégration compatible

PR-012C stocke le résultat dans `AnalysisContext.room_modes_analysis` après le
calcul des propriétés de salle. La configuration d'intégration couvre de 0 à
300 Hz, avec un ordre maximal de 4 par axe.

Pendant la migration, `context.room_modes` référence uniquement
`context.room_modes_analysis.axial_modes`. `ModalDensityAnalyzer`,
`ModeMatcher`, `StereoAnalyzer` et les autres consommateurs historiques ne sont
pas modifiés dans cette étape.

## Migration des consommateurs physiques

PR-012D fait de `RoomModesAnalysis` l'unique entrée modale de
`ModalDensityAnalyzer` et `ModeMatcher`. La densité porte désormais sur toutes
les familles et conserve leurs nombres séparés. Les correspondances de pics
parcourent tous les modes ; leur `ModeMatch.mode` conserve naturellement le
`RoomModeType` et les indices complets.

`context.room_modes` reste temporairement disponible pour `StereoAnalyzer` et
les autres consommateurs non migrés. `PeakClassifier` n'est pas présent dans
la baseline intégrée et devra être migré lors de sa réintroduction, sans
adaptateur vers le format historique.
