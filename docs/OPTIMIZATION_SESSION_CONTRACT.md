# Contrat de session d’optimisation

La session d’optimisation raccorde plusieurs états structurés produits par
AcousticBrain. Elle ne lit aucune mesure brute et n’ajoute aucun calcul
acoustique. Elle compare uniquement les scores, faits, corrélations et
hypothèses déjà produits par le pipeline.

## Activation explicite

Une analyse historique reste inchangée :

```python
report = AcousticBrain().analyze(project)
```

Une session doit être créée ou chargée, puis passée explicitement :

```python
service = OptimizationSessionService()
session = service.create("studio-2026")
report = AcousticBrain().analyze(project, session_context=session)
```

La première analyse rattache l’état initial. Avant tout nouvel état,
l’application doit déclarer l’expérience choisie :

```python
service.start_iteration(session, ExperimentProtocol(...))
report = AcousticBrain().analyze(modified_project, session_context=session)
```

Le service ne sélectionne jamais l’expérience suivante. Il refuse un second
état si aucune itération n’a été explicitement ouverte.

## Persistance

Le pipeline ne charge et ne sauvegarde rien. Ces opérations sont explicites :

```python
service.save(session, "optimization-session.json")
session = service.load("optimization-session.json")
```

Le document JSON est versionné. Il contient les instantanés structurés, les
protocoles réellement déclarés, les comparaisons réellement terminées et leurs
références. Aucun historique absent n’est reconstruit.

## Comparaison et évolution

Une `ExperimentComparison` relie l’état avant et l’état après. Le gain global
est la différence entre les scores globaux existants. Les faits améliorés ou
dégradés sont limités aux scores de domaines dont le sens « plus haut est
meilleur » est défini. Les faits acoustiques génériques restent disponibles
pour la traçabilité mais ne sont pas interprétés sans sémantique explicite.

L’évolution de l’hypothèse testée compare son statut et son score de support :
`REINFORCED`, `REFUTED`, `WEAKENED` ou `UNCHANGED`.

## Traçabilité et rapport

Chaque itération terminée conserve la chaîne :

mesure ou état → fait → corrélation → hypothèse → protocole → nouvel état →
comparaison → évolution → progression.

Le rapport inclut une synthèse de session seulement lorsqu’une session est
active. Le presenter projette les résultats calculés par le service ; il ne
crée ni liens, ni décisions, ni phrases métier. Le détail des chaînes n’est
affiché par `ConsoleReporter` qu’avec `detailed_traceability=True`.
