# Global Knowledge Expansion Contract

PR-017A audite les contrats de synthèse, confiance, recommandation et
traçabilité avant leur extension aux connaissances temporelles et spatiales.

## Résultat de l'audit

Aucun nouveau modèle de domaine n'est requis :

- `GlobalDomainAnalysis` accepte déjà un code, un score dérivé, une confiance,
  une analyse source et des références d'action ;
- `ConfidenceFactor` représente une contribution de confiance disponible ou
  absente ;
- `Recommendation` conserve une action stable et plusieurs provenances ;
- `EvidenceReference` représente une preuve scalaire atomique ;
- `ExplanationLink` relie des preuves, corrélations et recommandations sans
  imposer que la chaîne soit complète ;
- `TraceabilityAnalysis` transporte le graphe sans en résoudre les liens.

## Domaines et sources stables

Les domaines ajoutés à la connaissance globale sont `RT60`, `ETC`, `CLARITY`
et `SPATIAL`. Leurs sources physiques restent respectivement `RT60Analysis`,
`ETCAnalysis`, `ClarityAnalysis` et `SpatialAnalysis`.

Les analyses de corrélation peuvent compléter la provenance d'un lien, mais ne
remplacent jamais les analyses physiques sources.

## Identifiants normatifs

Les identifiants de domaine, faits, corrélations globales et recommandations
sont centralisés dans `acousticbrain.knowledge_codes`. Les moteurs des étapes
suivantes doivent les réutiliser au lieu de dupliquer des chaînes littérales.

Les corrélations initiales sont :

- `ETC_SPATIAL_ASYMMETRY` ;
- `RT60_CLARITY_DECAY_INTERACTION` ;
- `ETC_CLARITY_EARLY_ENERGY_INTERACTION` ;
- `SPATIAL_STEREO_ALIGNMENT`.

Les actions initiales sont :

- `CHECK_EARLY_REFLECTION_SYMMETRY` ;
- `INVESTIGATE_RT60_CHANNEL_DIFFERENCES` ;
- `INVESTIGATE_DOMINANT_EARLY_REFLECTIONS` pour identifier les événements non appariés ;
- `APPLY_EARLY_REFLECTION_TREATMENT` lorsque la corrélation D/R–ETC établit la cause ;
- `VERIFY_TIME_ALIGNMENT`.

## Invariants

- Une confiance technique n'est jamais un score de qualité acoustique.
- Un score global dérivé n'est jamais ajouté artificiellement à une analyse
  physique.
- Une recommandation conserve toutes ses analyses sources après
  déduplication.
- Une preuve absente n'est jamais inventée pour compléter un lien.
- Une chaîne incomplète reste incomplète.
- La présentation projette les identifiants reçus sans résoudre les liens,
  rechercher une preuve manquante ou reconstruire une provenance.
- Aucun diagnostic ni texte de diagnostic n'est une entrée de ces couches.
