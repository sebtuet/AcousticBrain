# Contrat de raisonnement acoustique déterministe

PR-024 introduit une couche de raisonnement structurée entre les analyses et
leur restitution. Elle consomme exclusivement des résultats d'analyse et la
`RoomGeometry`. Elle ne lit ni échantillons, ni `ImpulseResponse`, ni texte de
diagnostic ou utilisateur. Elle ne dépend d'aucun LLM.

## Sortie

`AcousticReasoningAnalysis` contient une séquence immuable et déterministe de
quatre `AcousticHypothesis` :

1. `ASYMMETRIC_SPEAKER_ROOM_INTERACTION`
2. `MODAL_BASS_PERSISTENCE`
3. `DOMINANT_EARLY_REFLECTION_INTERACTION`
4. `SBIR_PLACEMENT_INTERACTION`

Chaque hypothèse sépare strictement les preuves favorables, contre-preuves,
faits de contexte et faits manquants. Chaque élément conserve son fait source,
son analyse source, les règles ou seuils appliqués et les corrélations déjà
calculées utilisées. Une absence est un fait manquant, jamais une
contre-preuve.

## Scores et statuts

Le score de support et la confiance ont des sémantiques distinctes :

```text
support = borne_0_100(
    moyenne(force des preuves favorables)
    - 0,5 × moyenne(force des contre-preuves)
)

confiance = moyenne(confiance technique de toutes les preuves)
             × couverture des faits requis
```

Les seuils de statut sont explicites : `SUPPORTED` à partir de 70 sans fait
requis manquant, `PLAUSIBLE` à partir de 40, `CONTRADICTED` lorsqu'une
contre-preuve atteint 70 et que le support reste inférieur à 40, sinon
`INCONCLUSIVE`.

## Règles initiales

- Asymétrie : symétrie stéréo inférieure à 85, différence d'événements ETC
  d'au moins 3, écarts D/R d'au moins 3 dB et écarts Bass Decay d'au moins
  0,25 s.
- Persistance modale : décroissance maximale d'au moins 2 s et corrélation
  structurée `SLOW_DECAY_MODAL_INTERACTION`. Une décroissance d'au plus 1 s
  constitue une contre-preuve.
- Réflexions précoces : événements non expliqués avant 20 ms et au-dessus de
  -20 dB, avec concordance D/R lorsqu'elle existe.
- SBIR : meilleur candidat SBIR structuré, concordance ETC de surface si elle
  existe, et provenance géométrique conservée comme contexte.

Ces règles ne recalculent aucune analyse source.

## Actions et traçabilité

Les actions initiales sont exclusivement des vérifications : comparaison,
mesure, déplacement temporaire ou masquage temporaire. Elles référencent les
faits qui les fondent ainsi que les faits attendus pour confirmer ou réfuter
l'hypothèse. Une hypothèse `INCONCLUSIVE` ne peut contenir aucune correction
définitive.

Le graphe de traçabilité conserve la chaîne complète :

```text
fait source → preuve typée → hypothèse → action de vérification
```

`RecommendationEngine` peut exposer ces actions, marquées explicitement comme
vérifications. Il ne transforme pas une hypothèse en cause ou correction sans
la chaîne complète.
