# RT60 Contract

PR-013A définit uniquement la connaissance structurée nécessaire à une future
analyse du temps de réverbération. Elle n'ajoute ni importeur, ni moteur RT60,
ni stage, ni diagnostic, ni présentation.

## Donnée brute

`ImpulseResponse` contient les échantillons bruts d'un `ImpulseChannel`, leur
fréquence d'échantillonnage, un décalage temporel éventuel et un identifiant de
source. Les métadonnées REW `peak_value`, `peak_index`, `response_length`,
`sample_interval_s` et `start_time_s` sont conservées sans transformation. Elle
ne contient aucun résultat RT60 dérivé.

## Analyse par bande

`RT60BandAnalysis` décrit une bande par ses bornes et sa fréquence centrale. Le
résultat conserve le RT60 éventuel, la plage de décroissance utilisée, la
corrélation de l'ajustement et la confiance. Une valeur indisponible reste
`None`.

## Agrégation par canal

`RT60ChannelAnalysis` regroupe les analyses fréquentielles d'un canal et leurs
statistiques RT60 agrégées. Elle référence le même `ImpulseChannel` que la
réponse impulsionnelle source.

## Agrégation multi-canal

`RT60Analysis` regroupe les analyses par canal ainsi que les bandes agrégées
entre canaux. Elle porte uniquement des valeurs calculées et leur confiance,
sans score de qualité acoustique ni texte utilisateur.

Les formules, fenêtres de décroissance, filtres fréquentiels, règles de
confiance et agrégations appartiendront aux moteurs des étapes ultérieures.

## Analyse mono-canal

`RT60Analyzer` reçoit une seule `ImpulseResponse`, applique des filtres de tiers
d'octave et calcule la décroissance énergétique par intégration inverse de
Schroeder. Il tente les régressions EDT (0 à -10 dB), T20 (-5 à -25 dB) et T30
(-5 à -35 dB), puis sélectionne explicitement T30, T20 ou EDT dans cet ordre.

Une estimation exige toute sa plage de décroissance, au moins 5 dB de marge
sur le bruit de fond, un nombre minimal de points et une pente négative. Une
plage inexploitable reste `None`. La confiance combine la longueur de plage,
la corrélation de la régression et la marge sur le bruit, sans produire de
score de qualité acoustique.

## Import REW

`REWImpulseImporter` lit une réponse impulsionnelle exportée par REW et exige
un canal explicite. Il vérifie la présence des cinq métadonnées, le marqueur de
données, le nombre exact d'échantillons, la plage de l'indice de pic et la
positivité de l'intervalle d'échantillonnage.

L'importeur retourne uniquement `ImpulseResponse`. Il ne normalise pas les
échantillons et ne calcule ni décroissance, ni bande fréquentielle, ni RT60.

## Agrégation et intégration

`RT60Aggregator` reçoit explicitement un dictionnaire d'analyses par canal. Il
conserve les canaux disponibles, agrège uniquement les bandes valides communes,
calcule les écarts gauche moins droite, la confiance de couverture et une
homogénéité intercanal. Il ne reçoit jamais les réponses impulsionnelles brutes.

`Project` stocke les réponses par `ImpulseChannel`. `ImportEngine` reconnaît les
exports `Impulse_Left.txt`, `Impulse_Right.txt` et `Impulse_L+R.txt` sans les
analyser. `TemporalAnalysisStage`, distinct de `PhysicsStage`, orchestre ensuite
les analyses mono-canal et l'agrégation, puis stocke `context.rt60_analysis`.

## Interprétation

`RT60Diagnostic` lit exclusivement `context.rt60_analysis`. Il présente la
valeur large bande déjà agrégée, l'étendue entre canaux, l'homogénéité et les
écarts gauche-droite par bande. Aucun EDT, T20, T30, filtre ou agrégat n'est
recalculé.

La plage indicative de 0,2 à 0,4 seconde suit les conditions d'écoute de
référence EBU Tech 3276. Le score combine cette durée déjà calculée et
l'homogénéité intercanal. La confiance est recopiée depuis `RT60Analysis`.
