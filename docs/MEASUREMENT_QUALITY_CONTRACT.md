# PR-021A — Contrat Measurement Quality

## Finalité

La qualité de mesure décrit exclusivement la fiabilité technique des données
acquises. Elle reste indépendante de la qualité acoustique de la salle : une
issue de mesure n'est ni un défaut acoustique, ni un diagnostic utilisateur,
ni une recommandation.

PR-021A introduit seulement des modèles factuels et des codes stables. Aucun
échantillon n'est analysé et aucune politique d'exploitabilité n'est décidée.

## Codes d'issues

`MeasurementQualityIssueCode` contient :

- `CLIPPING_DETECTED` ;
- `LOW_SIGNAL_LEVEL` ;
- `HIGH_NOISE_FLOOR` ;
- `INSUFFICIENT_DYNAMIC_RANGE` ;
- `INVALID_DIRECT_PEAK` ;
- `INSUFFICIENT_IR_DURATION` ;
- `CHANNEL_SAMPLE_RATE_MISMATCH` ;
- `CHANNEL_LENGTH_MISMATCH` ;
- `CHANNEL_TIMING_MISMATCH` ;
- `MISSING_REQUIRED_CHANNEL` ;
- `INCONSISTENT_MEASUREMENT_METADATA`.

## MeasurementQualityIssue

Une issue atomique conserve :

- son code stable ;
- sa portée `CHANNEL` ou `MEASUREMENT_SET` ;
- le canal concerné lorsque la portée est `CHANNEL` ;
- les métriques observées ;
- les seuils techniques appliqués ;
- une confiance technique entre 0 et 100 ;
- une sévérité technique optionnelle ;
- un ou plusieurs identifiants de provenance.

Une issue de canal exige un `ImpulseChannel`. Une issue de jeu de mesures ne
peut pas cibler artificiellement un canal unique. Les métriques et seuils sont
copiés dans des mappings immuables. Les seuils sont numériques et finis ; les
métriques sont des scalaires structurés et finis.

`MeasurementQualityTechnicalSeverity` contient `INFO`, `WARNING` et `ERROR`.
Cette sévérité décrit l'impact technique sur la donnée et ne doit jamais être
interprétée comme une gravité acoustique.

## MeasurementChannelQuality

Les faits d'un canal regroupent le canal, ses issues, la fréquence
d'échantillonnage, le nombre d'échantillons, la durée, l'indice du pic direct,
la confiance technique et l'identifiant source. Toute valeur indisponible
reste à `None`.

Toutes les issues contenues doivent cibler exactement le canal propriétaire.
Le modèle ne porte ni score acoustique ni statut d'exploitabilité.

## MeasurementSetQuality

Les faits multi-canaux conservent les canaux disponibles, les canaux requis,
les issues de portée `MEASUREMENT_SET`, la confiance technique et les sources.
Les listes de canaux et de sources sont uniques et déterministes.

Ce modèle accueillera les constats PR-021C de fréquence d'échantillonnage,
longueur, synchronisation, présence et métadonnées. Il ne décide pas quelles
analyses peuvent être exécutées.

## MeasurementQualityAnalysis

L'analyse globale regroupe les `MeasurementChannelQuality` uniques et un
`MeasurementSetQuality` optionnel. Elle conserve une confiance et les analyses
sources, mais aucun score acoustique, aucune readiness et aucune action.

## Invariants bloquants

- une mauvaise mesure ne devient jamais une mauvaise acoustique ;
- chaque issue possède une portée et une provenance cohérentes ;
- aucune métrique ou aucun seuil non fini ;
- aucune issue de canal attachée au mauvais canal ;
- aucun canal dupliqué dans une analyse ;
- aucune correction ou valeur de remplacement ;
- aucun diagnostic, recommandation ou score acoustique ;
- aucune politique d'exécution avant PR-021D ;
- aucun moteur, stage, pipeline ou rapport dans PR-021A.

## PR-021B — Analyse mono-canal

`MeasurementQualityAnalyzer` reçoit une unique `ImpulseResponse` et retourne
une unique `MeasurementChannelQuality`. Il ne reçoit aucune autre analyse et
ne modifie jamais la réponse source.

Les contrôles techniques initiaux sont :

- clipping lorsqu'au moins deux échantillons atteignent un niveau absolu de
  `0.999` ;
- niveau direct faible lorsque le maximum absolu est inférieur à `0.01` ;
- pic direct invalide lorsqu'il est absent, hors limites ou inférieur à 90 %
  du maximum global ;
- bruit de fond estimé par RMS sur les 10 % finaux, avec au moins 20
  échantillons ;
- bruit élevé au-dessus de `-40 dBFS` ;
- dynamique insuffisante sous `35 dB` ;
- durée utile après le direct inférieure à `0.2 s` ;
- incohérences de longueur déclarée, intervalle d'échantillonnage, origine
  temporelle, valeur de pic ou valeurs non finies.

Un unique échantillon normalisé au plein niveau n'est pas assimilé à du
clipping. Le moteur conserve l'indice de pic déclaré, même lorsqu'il est
invalide ; il ne le remplace pas par le maximum détecté. Une fréquence
d'échantillonnage invalide produit une valeur `None` pour les durées dérivées,
jamais une valeur de substitution.

Chaque issue conserve les métriques réellement observées, les seuils appliqués
et l'identifiant source de l'impulsion. L'ordre des issues suit l'ordre stable
de `MeasurementQualityIssueCode`.

La confiance de `MeasurementChannelQuality` mesure seulement la disponibilité
des cinq familles de faits nécessaires au contrôle : échantillons, fréquence
d'échantillonnage, finitude du signal, crédibilité du pic et disponibilité du
bruit de fond. Une issue certaine peut donc coexister avec une confiance
technique élevée. Cette confiance n'est ni un score acoustique ni une décision
de readiness.

PR-021B n'effectue aucune correction, normalisation, mutation, recommandation,
interprétation utilisateur ou lecture d'une autre analyse.

## PR-021C — Cohérence multi-canal et intégration

`MeasurementSetQualityAnalyzer` reçoit exclusivement un dictionnaire de
`MeasurementChannelQuality`. Il ne relit aucune `ImpulseResponse` et ne déplace
aucune issue hors de son canal d'origine.

Les canaux requis par défaut sont `LEFT`, `RIGHT` et `STEREO`, ce dernier
représentant la mesure L+R. La liste peut être configurée explicitement par
l'appelant. Une issue `MISSING_REQUIRED_CHANNEL` distincte est produite pour
chaque canal absent.

Les règles de cohérence initiales sont :

- fréquences d'échantillonnage identiques, avec une tolérance de `0 Hz` ;
- longueurs compatibles lorsque leur écart relatif ne dépasse pas `1 %` de la
  longueur maximale ;
- temps des pics directs compatibles lorsque leur étendue ne dépasse pas
  `1 ms` ;
- propagation d'un constat global de métadonnées incohérentes lorsqu'un canal
  possède déjà `INCONSISTENT_MEASUREMENT_METADATA` ou ne fournit aucune
  fréquence d'échantillonnage.

Les comparaisons utilisent seulement les faits disponibles. Un fait absent
n'est ni remplacé ni estimé. Les incohérences de fréquence, longueur, timing et
métadonnées sont des issues `MEASUREMENT_SET`; les issues techniques qui les
fondent restent attachées aux `MeasurementChannelQuality`.

La confiance de `MeasurementSetQuality` est la moyenne des confiances de canal
pondérée par la couverture des canaux requis. Elle mesure la capacité de
validation du jeu, jamais sa qualité acoustique.

`MeasurementQualityAggregator` conserve les qualités de canal dans l'ordre
stable de `ImpulseChannel`, le `MeasurementSetQuality` et leurs provenances. Il
produit une `MeasurementQualityAnalysis` sans score, diagnostic ou readiness.

`MeasurementQualityStage` exécute l'analyse mono-canal, la cohérence
multi-canal et l'agrégation, puis stocke seulement le résultat dans
`AnalysisContext.measurement_quality_analysis`. Dans le pipeline, ce stage est
placé avant les étapes physiques et temporelles. Il ne modifie ni les mesures,
ni les impulsions, ni l'exécution des analyses existantes.

## PR-021D — Politique d'exploitabilité

La readiness est une connaissance distincte de la qualité de mesure et des
scores acoustiques. `MeasurementReadinessEngine` reçoit uniquement une
`MeasurementQualityAnalysis` et produit une `MeasurementReadinessAnalysis`.

Les familles couvertes sont :

- `FREQUENCY` ;
- `RT60` ;
- `ETC` ;
- `CLARITY` ;
- `SPATIAL` ;
- `DIRECT_REVERBERANT` ;
- `BASS_DECAY`.

Chaque `AnalysisReadiness` conserve son statut `AVAILABLE`,
`AVAILABLE_WITH_RESERVATIONS` ou `BLOCKED`, ses issues bloquantes et non
bloquantes, ses canaux requis, ses faits manquants, sa confiance technique et
les codes des règles appliquées. Le statut est cohérent par construction : un
fait manquant ou une issue bloquante implique `BLOCKED`; une réserve sans
blocage implique `AVAILABLE_WITH_RESERVATIONS`.

### Politique par famille

Les familles mono-canal exigent au moins un canal possédant une fréquence
d'échantillonnage et des échantillons exploitables. Lorsqu'un canal est affecté
mais qu'un autre reste éligible, ses issues sont conservées comme réserves et
ne bloquent pas artificiellement toute la famille.

- `FREQUENCY` ne dépend pas de la crédibilité du pic direct. Les problèmes de
  niveau, bruit, dynamique ou clipping sont des réserves.
- `RT60` exige un pic direct, une durée et une dynamique exploitables.
- `ETC` exige un pic direct crédible ; une durée inférieure au seuil général de
  200 ms reste une réserve, car l'analyse précoce peut disposer d'une fenêtre
  suffisante.
- `CLARITY` exige un pic direct et une durée exploitables.
- `DIRECT_REVERBERANT` exige un pic direct, une durée et une dynamique
  exploitables.
- `BASS_DECAY` exige en plus un bruit de fond acceptable.
- `SPATIAL` exige explicitement `LEFT` et `RIGHT`, des faits de base valides et
  bloque les incohérences globales de fréquence d'échantillonnage ou de timing.

Les écarts globaux de longueur et les défauts des canaux non indispensables
restent des réserves. L'absence d'un canal ou d'un fait est représentée dans
`missing_facts`; aucune issue synthétique n'est inventée lorsqu'aucune preuve
atomique ne l'accompagne.

La confiance d'une décision combine la confiance de
`MeasurementQualityAnalysis` et celles des issues réellement utilisées. Elle
exprime la certitude de la décision, pas la qualité acoustique ni la permission
d'exécuter du code.

`MeasurementReadinessStage` est placé immédiatement après
`MeasurementQualityStage` et stocke le résultat dans
`AnalysisContext.measurement_readiness_analysis`. Aucun stage existant ne lit
ce résultat et le pipeline ne contient aucun branchement conditionnel fondé sur
la readiness dans PR-021D.

## PR-021E — Couches supérieures et restitution

`ConfidenceStage` agrège désormais les confiances techniques de
`MeasurementQualityAnalysis` et `MeasurementReadinessAnalysis` comme facteurs
de fiabilité des preuves. Leur valeur ne devient jamais une qualité acoustique.

La synthèse expose un domaine `MEASUREMENT_QUALITY` explicitement typé
`MEASUREMENT_QUALITY`. Il est visible, traçable et présenté avec sa confiance
technique. Son score de disponibilité est dérivé des sept statuts de readiness
(`AVAILABLE` 100, `AVAILABLE_WITH_RESERVATIONS` 50, `BLOCKED` 0), tandis que
sa confiance exprime la certitude de ces constats. La propriété
`contributes_to_acoustic_score` vaut `False`. Ce domaine est
donc exclu du score acoustique global et des domaines acoustiques prioritaires.
Un statut de readiness `BLOCKED` ne produit aucun score acoustique nul.

Les issues structurées peuvent produire cinq actions stables de reprise :

- `RETAKE_CLIPPED_MEASUREMENT` ;
- `IMPROVE_SIGNAL_TO_NOISE` ;
- `FIX_CHANNEL_TIMING` ;
- `COMPLETE_REQUIRED_CHANNELS`.
- `CHECK_MEASUREMENT_METADATA`.

Ces actions conservent comme sources `MeasurementQualityAnalysis` et, lorsque
disponible, `MeasurementReadinessAnalysis`. Elles n'altèrent ni le signal ni
l'orchestration.

La traçabilité publie chaque issue avec son code, sa portée, son canal, ses
métriques, ses seuils et sa confiance. Chaque famille de readiness conserve son
statut, ses nombres de raisons bloquantes et non bloquantes, ses canaux requis,
faits manquants et règles appliquées.

`MeasurementQualityDiagnostic` lit exclusivement la qualité et la readiness.
Il ne possède pas de score acoustique : sa sévérité décrit seulement l'état
technique des preuves et ses recommandations portent uniquement sur la reprise
ou la complétion des mesures.

### Corrective de restitution et convention REW

La métadonnée REW `Peak value before normalisation` décrit le signal avant
normalisation, alors que les échantillons exportés appartiennent à l'IR
normalisée. `PeakValueConvention.BEFORE_NORMALIZATION` rend cette différence
explicite. Le moteur ne compare jamais directement ces deux amplitudes. Pour
`SAMPLE_VALUE`, la comparaison porte sur les grandeurs absolues et utilise la
valeur déclarée comme dénominateur protégé ; le signe du pic ne crée donc pas
une fausse incohérence.

Tant que la readiness ne contrôle pas l'orchestration, un diagnostic acoustique
associé à une famille `BLOCKED` est marqué `calculé à titre provisoire`, avec
une validité technique non garantie. Sa confiance interne ne lève pas le
blocage. `ConfidenceDiagnostic` restitue séparément confiance des calculs et
readiness des mesures.

La console affiche par défaut une synthèse de traçabilité (sources, nombres de
preuves et de liens). L'intégralité du graphe reste disponible avec
`ConsoleReporter(detailed_traceability=True)`.
