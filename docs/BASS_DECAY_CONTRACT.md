# PR-019A — Contrat Bass Decay

## Portée

PR-019A définit uniquement les faits structurés de décroissance basse
fréquence. Il n'introduit aucun moteur, contexte d'analyse, stage, diagnostic,
score global, recommandation, corrélation ou modification du rapport.

Les modèles ne fixent aucun seuil acoustique de qualité et ne font aucune
référence aux modes, aux pics, au RT60 ou au rapport direct/réverbéré.

## BassDecayBandAnalysis

Chaque bande conserve :

- sa fréquence centrale et ses bornes fréquentielles ;
- les niveaux de départ et de fin suivis ;
- la plage dynamique et la durée effectivement observées ;
- la pente de régression et le temps de décroissance estimé ;
- le plancher de bruit et la marge au bruit ;
- le coefficient de corrélation de l'ajustement ;
- la confiance technique, la méthode et le statut d'exploitabilité.

Toute valeur non disponible reste à `None`. Une bande `USABLE` doit posséder
une plage dynamique et une durée strictement positives, une pente négative,
une régression traçable, un plancher et une marge au bruit, ainsi qu'un temps de
décroissance positif. Une bande non exploitable ne reçoit aucun temps de
décroissance estimé.

`DecayUsability` contient les statuts techniques suivants :

- `USABLE` ;
- `INSUFFICIENT_DYNAMIC_RANGE` ;
- `NOISE_FLOOR_REACHED` ;
- `UNSTABLE_SLOPE` ;
- `INSUFFICIENT_DURATION`.

Ces statuts décrivent l'exploitabilité de la mesure, jamais une qualité
acoustique bonne ou mauvaise.

## BassDecayChannelAnalysis

L'analyse d'un canal conserve le canal, les bandes analysées, la plage
fréquentielle couverte, la durée maximale observée, le nombre exact de bandes
exploitables, la confiance technique agrégée et la méthode.

## BassDecayAnalysis

L'agrégation multi-canal conserve les analyses indexées par canal, les canaux
disponibles, les bandes agrégées communes, leurs fréquences centrales, les
écarts gauche moins droite typés, la couverture et la confiance globale.

`BassDecayBandDifference` rend chaque comparaison traçable avec les deux temps
comparés, leur différence signée, leurs méthodes et leur confiance. Il ne peut
être construit qu'à partir de deux temps strictement positifs et la différence
doit être égale au temps gauche moins le temps droit.

## Invariants bloquants

- aucun temps de décroissance sans bande techniquement exploitable ;
- aucune bande exploitable sans pente de décroissance et régression valides ;
- le plancher de bruit et la marge au bruit restent explicites ;
- aucune valeur zéro ou de remplacement pour un fait indisponible ;
- aucun seuil ou jugement de qualité acoustique ;
- aucune dépendance vers une autre famille d'analyse.

## PR-019B — Moteur mono-canal

`BassDecayAnalyzer` reçoit une unique `ImpulseResponse` et produit une unique
`BassDecayChannelAnalysis`. Par défaut, il analyse les tiers d'octave de 20 à
200 Hz. Chaque bande est filtrée indépendamment, puis sa courbe énergétique est
intégrée depuis la fin après correction du bruit de fond.

La plage technique suivie va de -5 à -25 dB. Une estimation exige une marge de
5 dB au-dessus du bruit, au moins 50 ms d'observation, 20 échantillons de
régression et une corrélation absolue minimale de 0,90. Ces constantes évaluent
uniquement la fiabilité de la mesure ; elles ne qualifient pas le comportement
acoustique.

Les échecs sont attribués de manière déterministe : durée brute insuffisante,
plancher de bruit atteint, plage dynamique insuffisante, durée de régression
insuffisante, puis pente instable. Seul le statut `USABLE` reçoit un temps de
décroissance estimé. La confiance combine exclusivement la corrélation de la
régression, la marge au bruit et la durée observée.

## PR-019C — Agrégation et intégration

`BassDecayAggregator` consomme exclusivement des
`BassDecayChannelAnalysis`. Il n'accède jamais aux réponses impulsionnelles.
Les canaux sont conservés dans l'ordre de `ImpulseChannel` et une bande n'est
commune que si elle est `USABLE` sur chaque canal disponible.

Une bande agrégée contient les moyennes factuelles des mesures de canal et la
méthode `CHANNEL_MEAN`. Les écarts gauche moins droite sont produits sous forme
de `BassDecayBandDifference` uniquement lorsque les deux temps sont
exploitables.

La couverture est le pourcentage de centres communs exploitables par rapport à
l'union des centres analysés. La confiance globale est la moyenne des
confiances techniques de canal pondérée par cette couverture. Ces deux valeurs
décrivent la disponibilité des faits, sans jugement acoustique.

L'agrégateur refuse explicitement une clé de canal incohérente, un centre
dupliqué dans un canal, des bornes différentes pour un même centre ou des
méthodes de canal incompatibles.

`TemporalAnalysisStage` exécute la branche Bass Decay indépendamment pour
chaque réponse impulsionnelle, puis conserve son agrégation dans
`AnalysisContext.bass_decay_analysis`. PR-019C ne transmet encore ce résultat
à aucun diagnostic, score, corrélateur, moteur de recommandation ou rapport.

## PR-019D — Corrélations structurées

`BassDecayCorrelationEngine` reçoit explicitement `BassDecayAnalysis`,
`RoomModesAnalysis`, `ModalDensityAnalysis`, `RT60Analysis` et
`DirectReverberantAnalysis`. Il ne reçoit aucune mesure ni réponse
impulsionnelle et ne recalcule aucune décroissance.

Les corrélations initiales sont :

- `SLOW_DECAY_MODAL_INTERACTION` lorsqu'un temps Bass Decay supérieur à 0,8 s
  contient une fréquence modale théorique et dispose de sa bande de densité
  modale ;
- `SLOW_DECAY_RT60_INTERACTION` lorsque la même bande présente un Bass Decay
  supérieur à 0,8 s et un RT60 supérieur à 0,6 s ;
- `LOW_DRR_LONG_BASS_DECAY` lorsqu'un Bass Decay supérieur à 0,8 s coïncide
  avec un D/R inférieur à 0 dB ;
- `ASYMMETRIC_BASS_DECAY` lorsqu'un écart gauche moins droite typé atteint
  0,25 s en valeur absolue.

Le rapprochement modal utilise les bornes fréquentielles de la bande Bass
Decay. Les rapprochements RT60 et D/R utilisent des centres communs déjà
agrégés. Chaque corrélation conserve un code stable, les centres concernés,
les métriques sources, les analyses sources, un score borné entre 0 et 100, une
confiance technique et des codes de fondement.

`BassDecayCorrelationStage` stocke le résultat dans
`AnalysisContext.bass_decay_correlation_analysis`. Aucune recommandation,
aucun diagnostic et aucune intégration aux scores globaux ou au rapport ne
sont réalisés dans PR-019D.

## PR-019E — Couches supérieures et diagnostic

`ConfidenceStage` inclut la confiance technique déjà agrégée de
`BassDecayAnalysis`. Il ne relit aucun fait de bande.

`GlobalSynthesizer` crée le domaine `BASS_DECAY` lorsqu'au moins un temps
commun exploitable existe. Le score combine le temps maximal déjà estimé et la
couverture déjà calculée. Sa provenance est `GlobalAnalysis` dans la
traçabilité. Les corrélations globales `BASS_DECAY_MODAL_INTERACTION`,
`BASS_DECAY_RT60_INTERACTION` et `BASS_DECAY_DRR_INTERACTION` ne sont créées que
si la corrélation PR-019D correspondante existe réellement.

`RecommendationEngine` peut produire trois actions stables à partir des seules
corrélations Bass Decay :

- `INVESTIGATE_LONG_BASS_DECAY` ;
- `CHECK_MODAL_EXCITATION` ;
- `COMPARE_BASS_DECAY_CHANNELS`.

`TraceabilityEngine` conserve séparément le score global du domaine et les
faits physiques suivants : nombre de bandes communes exploitables, temps de
décroissance maximal, nombre d'écarts G-D significatifs et nombre de
corrélations Bass Decay.

`BassDecayDiagnostic` lit exclusivement `BassDecayAnalysis` et
`BassDecayCorrelationAnalysis`. Il restitue couverture, temps, asymétries et
corrélations existantes sans recalculer de pente, de bruit, de temps de
décroissance ou de corrélation.
