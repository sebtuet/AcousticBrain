# AcousticBrain Scoring

Ce document définit les conventions communes de score utilisées par tous les
moteurs d'analyse AcousticBrain.

## Score

Le score représente la qualité acoustique du domaine analysé.

- `100` : état idéal ou très satisfaisant.
- `0` : problème acoustique majeur.

Le score est calculé par un `Analysis`. Il doit être comparable, autant que
possible, aux scores produits par les autres moteurs.

## Impact

L'impact représente l'importance pratique d'un problème pour l'utilisateur.
Il est déterminé par un `Diagnostic` à partir du score et des règles propres
au domaine.

- `LOW`
- `MEDIUM`
- `HIGH`

Les seuils initiaux recommandés sont les suivants :

| Score | Impact |
| --- | --- |
| `>= 85` | `LOW` |
| `60 - 84` | `MEDIUM` |
| `< 60` | `HIGH` |

Le champ historique `severity` sera progressivement renommé en `impact`.

## Confidence

La confiance représente la fiabilité de l'analyse, indépendamment de la
qualité acoustique constatée.

- `100` : conclusion très solidement établie.
- `0` : données insuffisantes ou conclusion non fiable.

Elle sera calculée par le Confidence Engine à partir, notamment, de la qualité
des mesures, du nombre de preuves et de leur cohérence.

## Règle de responsabilité

```text
Analysis   → produit score + confidence
Diagnostic → interprète les faits et détermine l'impact
Report     → présente score, impact et confidence
```

Un diagnostic ne recalcule ni le score ni la confiance de son analyse.
