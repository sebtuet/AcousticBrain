# ETC Contract

PR-014A définit uniquement la connaissance structurée des événements temporels
mesurés dans une réponse impulsionnelle. Elle n'ajoute ni moteur ETC, ni
agrégateur, ni stage, ni corrélation physique, ni diagnostic ou présentation.

## ReflectionEvent

Un événement conserve exclusivement des faits mesurés ou directement dérivés :

- son délai après le son direct ;
- son niveau relatif ;
- son temps absolu et son indice d'échantillon ;
- la différence de trajet acoustique correspondante ;
- la confiance technique associée.

Il ne référence aucune paroi, surface, cause SBIR ou action corrective.

## ETCChannelAnalysis

L'analyse d'un canal identifie éventuellement le temps et l'indice du son
direct, puis regroupe les événements temporels détectés dans une fenêtre
explicite. Elle conserve également le bruit de fond et la confiance globale du
canal. Une donnée indisponible reste `None`.

## ETCAnalysis

L'agrégation multi-canal conserve les analyses indexées par `ImpulseChannel`,
les canaux disponibles et les nombres d'événements communs ou propres à gauche
et à droite. Elle ne contient aucune interprétation physique des événements.

Les calculs d'ETC, de maxima, de délais, de distances et de confiance
appartiendront au moteur PR-014B. L'appariement entre canaux appartiendra à
l'agrégateur PR-014C et toute hypothèse de surface à un moteur de corrélation
séparé.

## Analyse mono-canal

PR-014B ajoute `ETCAnalyzer`, qui reçoit uniquement une `ImpulseResponse`. Le
pic REW est vérifié dans une fenêtre locale de ±1 ms et le maximum global sert
de repli lorsque ce pic n'est pas crédible.

L'ETC est exprimée en dB relativement au son direct. Les événements sont
recherchés pendant 50 ms par défaut, au moins 0,5 ms après le direct et avec
0,5 ms de séparation. Leur niveau doit dépasser à la fois -40 dB et le bruit de
fond de 10 dB, avec une proéminence minimale de 3 dB.

Le moteur calcule uniquement les faits du contrat et une confiance technique
fondée sur le rapport au bruit, la proéminence et la cohérence du pic direct. Il
ne connaît aucune surface, analyse SBIR ou action corrective.

## Agrégation et intégration

PR-014C ajoute `ETCAggregator`. Il reçoit uniquement les analyses de canaux et
apparie gauche et droite par proximité de délai, avec une tolérance explicite
de 0,5 ms par défaut. Chaque événement ne peut appartenir qu'à une paire. Les
paires et les événements spécifiques restent conservés avec leurs faits
d'origine.

La confiance d'agrégation combine les confiances de canaux et la proximité
temporelle des paires. Elle ne suppose jamais que deux événements proches
proviennent d'une même surface.

`TemporalAnalysisStage` exécute séparément les chaînes RT60 et ETC à partir des
mêmes `ImpulseResponse`, puis stocke `context.rt60_analysis` et
`context.etc_analysis`. Aucun calcul ETC n'est ajouté au stage.

## Corrélations ETC-SBIR

PR-014D ajoute une connaissance distincte,
`ETCReflectionCorrelationAnalysis`, produite par
`ETCReflectionCorrelationEngine`. Le moteur reçoit explicitement `ETCAnalysis`,
`SBIRAnalysis` et, si nécessaire, une liste de surfaces autorisées.

Une corrélation exige par défaut un candidat SBIR d'au moins 60/100, une erreur
temporelle maximale de 1 ms et un score combiné d'au moins 60/100. Elle conserve
les deux délais, leur erreur, le trajet acoustique mesuré, la surface candidate,
le score, la confiance et les provenances. Les événements sans correspondance
restent explicitement regroupés par canal.

Ce rapprochement ne recalcule ni ETC ni SBIR et ne constitue pas encore une
interprétation utilisateur ou une recommandation.

## Diagnostic

PR-014E raccorde le moteur de corrélation dans un `ETCCorrelationStage` exécuté
après `TemporalAnalysisStage`. Le stage transmet uniquement `ETCAnalysis` et
`SBIRAnalysis`, puis stocke `context.etc_reflection_correlation_analysis`.

`ETCDiagnostic` lit exclusivement les deux connaissances ETC. Il présente les
comptes communs et spécifiques, les événements dominants déjà détectés, les
corrélations de confiance au moins égale à 70 % et les événements importants
non expliqués. Un événement est seulement interprété comme dominant s'il est
déjà présent dans l'analyse, avant 20 ms et à au moins -20 dB du direct.

Le diagnostic ne redétecte aucun maximum, ne recalcule aucun délai ou trajet et
ne réassocie aucune surface.
