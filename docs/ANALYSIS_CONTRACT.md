# Analysis Contract

Ce document définit le contrat commun de tout moteur d'analyse AcousticBrain.

## Analysis

Chaque `Analysis` :

- est une `dataclass` ;
- ne contient aucun texte destiné à l'utilisateur ;
- contient uniquement des faits, mesures et correspondances ;
- produit un `score` entre `0` et `100` ;
- produit une `confidence` entre `0` et `100` ;
- est sérialisable ;
- ne dépend pas des diagnostics ni de la présentation.

Les conventions de score, impact et confiance sont définies dans
[SCORING.md](SCORING.md).

## Analyzer

Chaque `Analyzer` :

- ne produit aucun texte destiné à l'utilisateur ;
- ne crée jamais de `Diagnostic` ;
- ne dépend jamais d'un autre `Analyzer` ;
- consomme des `Measurement`, des données de pièce, des enceintes et des
  features déjà calculées par les détecteurs lorsque cela est nécessaire ;
- retourne une `Analysis`.

Un analyzer ne redétecte jamais une feature déjà produite par un détecteur.

## Workflow d'une fonctionnalité

Chaque fonctionnalité suit les étapes suivantes :

1. Définir les modèles dans `models/` (`xxx_analysis.py` et, si nécessaire,
   `xxx_candidate.py`).
2. Implémenter le moteur dans `analysis/xxx.py`.
3. Intégrer l'analyse dans `AnalysisStage`.
4. Interpréter les faits dans `diagnostics/xxx.py`.
5. Présenter le diagnostic dans le rapport console.
6. Ajouter des tests ciblés.

## Responsabilités

```text
Measurement → Detector → Features → Analyzer → Analysis → Diagnostic → Report
```

- Les détecteurs produisent les features.
- Les analyzers transforment les features en faits structurés.
- Les diagnostics interprètent les faits et déterminent l'impact.
- Le report présente les résultats sans les recalculer.
