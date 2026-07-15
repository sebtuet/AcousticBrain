# Statut factuel de `SPLAnalyzer`

Statut : **`UNUSED_BUT_INTENT_UNKNOWN`**.

Cette note accompagne une micro-PR de robustesse indépendante de l'audit REW. Elle ne modifie ni l'import REW, ni les exigences de calibration, ni le guide de mesure.

## Capacité actuelle

`SPLAnalyzer.analyze` reçoit un `Measurement`, refuse une liste de fréquences vide, puis retourne :

- le nombre de points ;
- les fréquences minimale et maximale ;
- les niveaux SPL minimal, maximal et moyen.

La classe est exportée par `acousticbrain.analyzers`, mais aucun appel depuis le code de production sous `acousticbrain/` n'a été trouvé. `BrainPipeline` et `AnalysisStage` utilisent `PeakDetector` et `DipDetector`, pas `SPLAnalyzer`. Le commentaire « Analyse SPL principale » dans `AnalysisStage` désigne cette détection de pics et de creux; il n'est pas accompagné d'un appel à `SPLAnalyzer`.

## Appels et tests

- Appels directs de production trouvés : aucun.
- Appels indirects trouvés : aucun.
- Appel de test trouvé : `tests/test_spl_analyzer.py::test_spl_analyzer`.
- Le test importe une mesure REW de référence, appelle directement la classe et vérifie seulement que le nombre de points est positif et que les plages de fréquence et de SPL ne sont pas constantes.
- Aucun test d'étape, de pipeline, de rapport ou de diagnostic n'attend un résultat de `SPLAnalyzer`.

## Documentation et intention

Aucun contrat, document d'architecture, README ou élément de roadmap ne décrit `SPLAnalyzer` comme une capacité active ou planifiée. Aucun marqueur `TODO`, « future », « planned » ou équivalent lié à cette classe n'a été trouvé.

Le code et son test prouvent que l'utilitaire existe et fonctionne isolément. Ils ne permettent pas d'établir pourquoi il n'est pas orchestré, ni s'il doit être supprimé ou intégré ultérieurement. Cela exclut `ACTIVE_CAPABILITY` et `DOCUMENTED_PLANNED_CAPABILITY`, sans fournir une preuve suffisante pour `LEGACY_OR_DEAD_CODE`.

## Dépendance aux niveaux SPL absolus

Les valeurs `min_spl`, `max_spl` et `average_spl` sont calculées directement à partir de `Measurement.spl`, sans centrage, différence relative ou normalisation. Elles dépendent donc numériquement des niveaux SPL fournis par l'export. Le nombre de points et les bornes fréquentielles n'en dépendent pas.

`SPLAnalyzer` ne reçoit et ne conserve aucune provenance de calibration du microphone. En l'absence de cette provenance, le code peut calculer les trois statistiques SPL, mais ne peut pas établir leur exactitude absolue ni distinguer une mesure calibrée d'une mesure non calibrée.

Conséquence actuelle démontrée : aucune sortie de la pipeline, du rapport ou des diagnostics ne dépend de ces statistiques, puisque l'utilitaire n'y est pas appelé. Cette conclusion est limitée à `SPLAnalyzer`; elle ne qualifie pas les autres usages actifs de `Measurement.spl` par les détecteurs et analyses stéréo.

## Termes et symboles recherchés

`SPLAnalyzer`, `SPL Analyzer`, `analyse SPL`, `SPL analysis`, `average_spl`, `min_spl`, `max_spl`, `niveau SPL`, `absolute SPL`, `sound pressure level`, imports de `acousticbrain.analyzers`, appels `.analyze`, contrats, README, architecture, roadmap, `TODO`, `future`, `futur`, `planned`, `prévu` et `à venir`.
