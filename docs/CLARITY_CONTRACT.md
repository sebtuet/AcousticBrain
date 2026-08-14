# Clarity and Definition Contract

PR-015A définit uniquement la connaissance structurée nécessaire aux futurs
calculs de clarté et de définition. Elle n'ajoute ni moteur, ni agrégateur, ni
stage, ni diagnostic ou présentation.

## ClarityBandAnalysis

Une analyse de bande conserve exclusivement :

- la fréquence centrale ;
- la clarté de la parole C50 en dB ;
- la clarté musicale C80 en dB ;
- la définition D50 en pourcentage ;
- le temps central Ts en secondes ;
- la confiance technique et le code stable de la méthode.

Chaque métrique peut rester `None` lorsque les données ne permettent pas son
calcul. Aucun seuil d'interprétation ou score acoustique n'appartient au modèle.

## ClarityChannelAnalysis

L'analyse d'un canal regroupe ses bandes et les agrégats large bande déjà
calculés pour C50, C80, D50 et Ts. Elle référence explicitement son
`ImpulseChannel` et conserve une confiance globale.

## ClarityAnalysis

L'analyse multi-canal conserve :

- les analyses indexées par canal ;
- les canaux disponibles ;
- les bandes agrégées communes ;
- leurs fréquences centrales ;
- les écarts gauche moins droite pour C50, C80, D50 et Ts ;
- la confiance globale.

Les fenêtres énergétiques, filtres fréquentiels, formules, règles de confiance
et stratégies d'agrégation appartiendront aux moteurs des étapes suivantes.

## Corrélations structurées

`ClarityCorrelationAnalysis` conserve séparément les croisements factuels avec
RT60 et ETC. Chaque `ClarityCorrelation` porte un code stable, les bandes
concernées, des métriques numériques nommées, les analyses sources, un score de
correspondance, une confiance et des codes de fondement technique.

Ces codes ne constituent pas une explication destinée à l'utilisateur. Le
contrat ne contient ni diagnostic, ni recommandation, ni gravité. Le moteur de
corrélation ne modifie et ne recalcule aucune des analyses sources.
