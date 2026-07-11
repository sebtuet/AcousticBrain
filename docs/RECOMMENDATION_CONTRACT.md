# Recommendation Contract

PR-009A définit uniquement les objets de connaissance échangés avec le futur
moteur de recommandation. Elle n'ajoute ni moteur, ni étape de pipeline, ni
diagnostic, ni rendu.

## Entrées du futur moteur

Le moteur consommera directement les objets `Analysis` physiques. Il ne devra
ni lire, ni parser, ni fusionner les champs textuels des diagnostics.

## Sortie

Une `RecommendationAnalysis` contient des `Recommendation` structurées. Chaque
recommandation porte :

- un `code` stable ;
- une `action` et une `target` exploitables par la machine ;
- des `parameters` scalaires ;
- une `RecommendationPriority` ordonnable ;
- une `confidence` ;
- les types d'analyses physiques qui l'ont produite dans `source_analyses`.

Les titres, descriptions, justifications et autres textes destinés à
l'utilisateur appartiendront à une couche d'interprétation ou de rendu
ultérieure.
