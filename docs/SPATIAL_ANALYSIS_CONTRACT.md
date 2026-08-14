# Spatial Analysis Contract

PR-016A définit uniquement les connaissances structurées nécessaires à
l'analyse future d'une paire de signaux. Le protocole d'acquisition reste
explicite afin de distinguer une comparaison d'enceintes d'une mesure
binaurale.

## Nature de la mesure

`SpatialMeasurementType` possède deux valeurs :

- `SPEAKER_CHANNEL_PAIR` pour deux enceintes mesurées au même point ;
- `BINAURAL_PAIR` pour deux signaux captés selon un protocole binaural.

Une paire d'enceintes permet de décrire une différence de niveau, un retard
relatif et une cohérence de paire. Elle ne mesure pas un ILD, un ITD ou un IACC
interaural. Le contrat interdit donc de renseigner ces champs avec ce type de
mesure.

## SpatialBandAnalysis

Chaque bande conserve uniquement :

- sa fréquence centrale ;
- la différence de niveau et la différence temporelle de la paire ;
- la corrélation croisée et le délai de son maximum ;
- les métriques interaurales, éventuellement disponibles pour une paire
  binaurale uniquement ;
- le type de mesure, la confiance technique et le code de méthode.

Une métrique non exploitable reste explicitement `None`.

## SpatialChannelPairAnalysis

L'analyse de paire agrège les bandes, les valeurs large bande déjà calculées,
la confiance et la méthode. Toutes ses bandes doivent provenir du même type de
mesure.

## SpatialAnalysis

L'analyse spatiale transporte une analyse de paire éventuelle, son type de
mesure source et sa confiance. Une absence de paire reste explicite. Lorsque la
paire existe, son type doit correspondre au type source déclaré.

Ce contrat ne contient aucun calcul, score acoustique, centre fantôme, largeur
apparente, localisation, diagnostic, recommandation ou texte destiné à
l'utilisateur. Les moteurs, stages et consommateurs appartiennent aux étapes
suivantes.

## Interprétation selon le protocole

`SpatialInterpretationEngine` consomme exclusivement `SpatialAnalysis`. Il ne
relit aucune impulsion et ne recalcule ni niveau, ni délai, ni corrélation.

Pour `SPEAKER_CHANNEL_PAIR`, il produit une
`SpeakerPairSpatialInterpretation` décrivant l'équilibre de niveau,
l'alignement relatif, la cohérence de paire, la stabilité technique et les
bandes les plus asymétriques. Ces statuts restent techniques et ne constituent
pas une affirmation de localisation perceptive.

Pour `BINAURAL_PAIR`, il produit une `BinauralSpatialInterpretation` qui expose
les ILD, ITD et IACC déjà calculés par bande et leurs statuts structurés. Une
paire d'enceintes ne peut jamais produire cet objet.
