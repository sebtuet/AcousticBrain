# Contrat de planification expérimentale

`ExperimentPlanner` classe des expériences à partir des hypothèses et actions
structurées déjà produites. Il ne lit aucune mesure, ne relance aucune analyse,
ne modifie aucune géométrie et n’exécute aucune expérience.

## Activation explicite

La planification est désactivée par défaut :

```python
report = AcousticBrain().analyze(project)
```

Elle doit être demandée explicitement :

```python
report = AcousticBrain().analyze(project, plan_experiments=True)
```

Une session existante peut être fournie pour exclure ses expériences terminées
et tracer une éventuelle itération en attente :

```python
report = AcousticBrain().analyze(
    project,
    plan_experiments=True,
    session_context=session,
)
```

Le planificateur ne crée jamais de session et ne démarre jamais l’itération
recommandée.

## Sources et protocoles

Les quatre protocoles initiaux sont des définitions immuables associées aux
quatre `HypothesisCode`. Une `VerificationAction` correspondante est conservée
comme source lorsqu’elle existe. Une hypothèse `INCONCLUSIVE` peut utiliser la
définition de protocole comme source d’investigation sans produire de
correction définitive.

`SUPPORTED` signifie que les faits actuels soutiennent l’hypothèse ; il ne
signifie pas `CONFIRMED`. Le candidat reste donc possible, mais sa faible
incertitude réduit naturellement sa valeur informative. `CONTRADICTED` est
traité comme une hypothèse réfutée et rend le candidat inéligible.

Les protocoles de masquage d’une réflexion et de déplacement SBIR exigent leurs
paramètres géométriques explicites. Aucune surface, fréquence ou distance n’est
déduite ou inventée. Les protocoles de comparaison gauche/droite et de mesure à
plusieurs positions peuvent rester génériques.

## Valeur informative V1

Toutes les composantes sont bornées entre 0 et 100. Le résultat final est
également borné entre 0 et 100 et arrondi à deux décimales.

```text
incertitude = 100 - 2 × |support_score - 50|

valeur =
    0,25 × incertitude
  + 0,10 × support_score
  + 0,10 × confidence
  + 0,20 × part des faits manquants résolus
  + 0,10 × capacité à départager les contre-preuves
  + 0,10 × capacité à discriminer plusieurs hypothèses
  + 0,10 × réversibilité
  - pénalité de difficulté
  - pénalité de durée, seulement si la durée est connue
  - pénalité de coût
  - pénalité de répétition
```

Pénalités déterministes :

- difficulté : `EASY=0`, `MEDIUM=5`, `HARD=10` ;
- durée : `≤15=0`, `16–30=2`, `31–60=5`, `>60=8`, inconnue `=0` ;
- coût : `FREE=0`, `LOW=2`, `MEDIUM=5`, `HIGH=10` ;
- répétition : 20 points par occurrence, bornée à 30 points.

Une expérience déjà terminée dans la session est en outre inéligible. La
formule est indépendante de la gravité acoustique, de
`RecommendationPriority`, du score global et de toute phrase de diagnostic.

## Éligibilité et ordre

Les règles structurées vérifient la présence de l’hypothèse, du protocole, de
la provenance, des faits observables, des prérequis, des paramètres
géométriques, la réversibilité, le statut de l’hypothèse et l’historique de
session.

L’ordre total est : valeur informative décroissante, éligibilité,
réversibilité décroissante, difficulté croissante, durée croissante lorsqu’elle
est connue, coût croissant, confiance décroissante, identifiant stable.

## Traçabilité et restitution

`ExperimentPlanningTraceLink` puis `ExplanationLink` conservent :

fait → preuve → hypothèse → protocole → candidat → rang → recommandation →
itération éventuelle.

Le rapport standard affiche le candidat recommandé et au plus trois
alternatives éligibles. Tous les candidats, y compris les inéligibles et leurs
raisons structurées, restent disponibles dans la projection et dans la
traçabilité détaillée. Le presenter ne recalcule ni score, ni rang, ni raison.
