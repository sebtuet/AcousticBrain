# Direct-to-Reverberant Energy Contract

PR-018A définit uniquement les connaissances structurées nécessaires aux
futurs calculs d'énergie directe et réverbérée. Aucune fenêtre temporelle ne
reste implicite dans un moteur.

## EnergyWindowAnalysis

Une fenêtre conserve son nom stable, ses bornes en millisecondes, son énergie
éventuelle, son énergie relative éventuelle, sa confiance et sa méthode. Une
borne de fin `None` représente une intégration jusqu'à la fin des données
disponibles. Une énergie indisponible reste `None`.

## DirectReverberantBandAnalysis

Chaque bande conserve quatre fenêtres explicites :

- `direct_window` ;
- `early_window` ;
- `late_window` ;
- `total_window`.

Les trois fenêtres composantes ne peuvent pas se chevaucher. La fenêtre totale
les enveloppe nécessairement et peut donc les recouvrir sans ambiguïté. Le
rapport D/R ne peut exister que si l'énergie directe est strictement positive
et si les énergies précoce et tardive permettent de former une énergie
réverbérée strictement positive.

## DirectReverberantChannelAnalysis

L'analyse de canal conserve ses bandes, les quatre agrégats large bande, le
rapport D/R large bande, toutes les bornes configurées, sa confiance et sa
méthode. Le rapport large bande respecte le même invariant énergétique que les
rapports par bande.

## DirectReverberantAnalysis

L'analyse multi-canal conserve les analyses indexées par canal, les canaux
disponibles, les bandes communes agrégées, les écarts D/R gauche moins droite
en dB et la confiance globale.

Ce contrat ne contient aucun calcul, score acoustique, seuil qualitatif,
diagnostic, recommandation ou interprétation perceptive.

## Corrélations structurées

`DirectReverberantCorrelationEngine` consomme exclusivement les analyses D/R,
RT60, ETC, Clarity et Spatial déjà produites. Il ne relit aucune impulsion et
ne recalcule aucune énergie.

Les codes initiaux sont `LOW_DRR_HIGH_RT60`,
`LOW_DRR_DOMINANT_EARLY_REFLECTIONS`, `DRR_SPATIAL_CHANNEL_ASYMMETRY` et
`FAVORABLE_DRR_HIGH_CLARITY`. Chaque corrélation conserve ses bandes, métriques
sources, analyses sources, score de correspondance, confiance et fondements
techniques. Elle ne contient aucun texte utilisateur ni recommandation.

`FAVORABLE_DRR_HIGH_CLARITY` est une observation favorable de traçabilité :
elle est exclue des causes négatives et des pénalités. Le score de domaine part
de la qualité D/R large bande, puis applique une pénalité plafonnée fondée sur
la sévérité moyenne des seules corrélations défavorables ; leur accumulation ne
peut donc pas écraser mécaniquement le résultat large bande.
