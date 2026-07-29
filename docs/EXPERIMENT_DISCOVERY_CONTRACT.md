# Contrat de découverte automatique des expériences

La campagne active du dépôt contient uniquement la baseline réelle :

```text
measurements/
    baseline/
```

Le corpus historique utilisé par les tests d'intégration est isolé de cette
campagne active :

```text
tests/fixtures/campaigns/historical_reference/
    baseline/
    exp-001/
    exp-002/
```

`AcousticBrain.analyze(measurement_root="measurements")` ouvre une
`AcousticSession`, découvre les dossiers, importe la dernière expérience
`READY`, exécute le pipeline existant et active la planification. Cette session
est un conteneur technique de fichiers et de projets. Elle ne crée aucune
`OptimizationIteration`, aucun protocole métier et aucune comparaison.

## Détection indépendante des noms

`MeasurementRepository` parcourt récursivement chaque expérience. Les chemins
servent uniquement à retrouver les fichiers ; ils ne déterminent jamais leur
canal.

- Les TXT REW sont reconnus par leurs marqueurs internes. Le canal provient de
  `* Measurement:`.
- Les WAV sont validés comme RIFF/WAVE. Un canal embarqué dans `bext` ou
  `LIST/INFO` est utilisé lorsqu’il existe.
- Lorsqu’un WAV mono ne contient aucun canal, il peut être associé à un TXT par
  corrélation de leur empreinte spectrale. L’association exige une corrélation
  minimale de 0,75 et une marge minimale de 0,03 sur la seconde possibilité.
  Une association ambiguë reste volontairement absente.
- Une affectation persistée dans `channel_assignments` du manifest est
  prioritaire.
- Un `.mdat` est seulement détecté et hashé. Son contenu n’est jamais
  désérialisé ni interprété.

L’empreinte spectrale est une opération technique d’identification de deux
exports du même enregistrement. Elle ne produit ni fait acoustique, ni score,
ni comparaison métier.

## État et ordre

Un dossier est `READY` lorsque ses TXT de mesure fournissent LEFT, RIGHT et
STEREO. Sinon il est `INCOMPLETE`. Les autres exports restent décrits même
lorsqu’ils ne peuvent pas être affectés à un canal.

`baseline` est toujours présenté en premier. Les expériences sont ensuite
ordonnées par le premier horodatage REW détecté, puis par identifiant stable.

## Manifest versionné

Le manifest contient : version, identifiant, type, état, horodatage de mesure,
date du premier import, hash agrégé, affectations de canaux et liste des
fichiers avec leurs SHA-256.

Le hash agrégé dépend des contenus, pas des noms. `manifest.json` et les
fichiers étrangers comme `.DS_Store` sont exclus. La date du premier import est
conservée. Le fichier n’est réécrit que si sa représentation complète change.

### Référence explicite au plan d’acquisition

Une expérience exécutée peut déclarer à la racine du manifest l’identifiant
exact du plan d’acquisition dont elle provient :

```json
{
  "source_evidence_acquisition_plan_id":
    "EVIDENCE_ACQUISITION_ASYMMETRIC_SPEAKER_ROOM_INTERACTION_REASONING_RESOLVE_CONTRADICTION"
}
```

Cette référence est optionnelle afin de préserver les expériences historiques.
La découverte la conserve sans normalisation et la projection compare
uniquement cet identifiant exact aux `EvidenceAcquisitionPlan` disponibles :

- `PLAN_NOT_REFERENCED` : aucune référence n’a été déclarée ;
- `PLAN_REFERENCE_RESOLVED` : l’identifiant correspond exactement à un plan
  disponible ;
- `PLAN_REFERENCE_UNKNOWN` : une référence est déclarée, mais aucun plan
  disponible ne porte cet identifiant.

Aucune référence n’est déduite d’un protocole, type de test, objectif,
reasoning, horodatage, nom de fichier ou contenu de mesure. Un lien résolu
établit uniquement la traçabilité vers le plan source ; il ne valide ni
l’exécution, ni le protocole, ni le résultat, ni une conclusion scientifique.

### Couverture déclarée d’un plan `CHANNEL_ISOLATION`

La résolution de référence et la couverture du plan sont deux qualifications
distinctes. Une référence peut être `PLAN_REFERENCE_RESOLVED` tandis que sa
couverture reste partielle ou insuffisamment déclarée.

La validation de couverture est volontairement spécialisée au seul type
`CHANNEL_ISOLATION`. Elle compare exactement :

- les acquisitions LEFT et RIGHT structurées par la découverte ;
- les répétitions par canal, variables, entrées disponibles et mesures
  déclarées dans l’extension optionnelle suivante :

```json
{
  "channel_isolation_declaration": {
    "repeated_channels": ["LEFT", "RIGHT"],
    "available_inputs": [
      "documented_microphone_position",
      "existing_acquisition_settings"
    ],
    "controlled_variables": [
      "gain",
      "microphone_position",
      "signal_chain",
      "time_window"
    ],
    "independent_variables": ["active_channel"],
    "measurements": [
      "left_channel_response",
      "right_channel_response",
      "repeat_response"
    ]
  }
}
```

Les identifiants sont comparés sans normalisation ni correspondance
approximative. Les noms de projet, d’expérience et de fichiers ne participent
jamais à la décision. Une acquisition STEREO ne couvre pas implicitement les
acquisitions isolées LEFT et RIGHT. Les variables de
`experiment_declaration`, historiquement normalisées à l’import, ne sont pas
utilisées comme raccourci pour cette comparaison exacte.

Les états de couverture sont :

- `PLAN_COVERAGE_NOT_APPLICABLE` : aucun plan n’est résolu, ou le plan résolu
  n’est pas de type `CHANNEL_ISOLATION` ;
- `PLAN_COVERAGE_INSUFFICIENT_DECLARATION` : le plan est applicable mais les
  déclarations structurées ne permettent pas de qualifier honnêtement sa
  couverture ;
- `PLAN_COVERAGE_PARTIAL` : au moins une exigence vérifiable est couverte et
  au moins une autre est explicitement absente ;
- `PLAN_COVERAGE_COMPLETE` : toutes les exigences vérifiables sont
  explicitement couvertes.

Une exigence `missing` est comparable mais absente des déclarations
structurées. Une exigence `unverifiable` ne possède pas de représentation
comparable dans le modèle actuel. L’exécution des instructions et les
observations attendues restent ainsi non vérifiables dans cette portée.

`PLAN_COVERAGE_COMPLETE` qualifie uniquement la structure déclarée. Il ne
prouve ni que les répétitions ont été correctement réalisées, ni que les
variables sont réellement restées constantes, ni que les mesures sont
valides, ni qu’un critère de succès est satisfait, ni qu’une causalité est
établie. Cette validation n’est pas un moteur général de conformité
expérimentale.

## Extensibilité et conservation sans perte

Un manifest JSON est un document extensible. Chaque composant peut interpréter
les champs qu’il connaît, mais toute réécriture d’un document existant DOIT
partir du document complet chargé et ne modifier que les clés relevant
explicitement de sa responsabilité.

Toute clé inconnue et toute structure imbriquée inconnue DOIVENT être
conservées. Cette conservation est évaluée structurellement après parsing JSON :
l’ordre des clés, l’indentation et le formatage ne sont pas contractuels.

La création initiale d’un manifest neuf peut construire les champs techniques
requis sans document source. En revanche, lorsqu’un manifest existe déjà, une
mutation ciblée est requise :

```python
manifest = dict(existing_manifest)
manifest.update(recalculated_fields)
repository.save_manifest(path, manifest)
```

La reconstruction suivante est interdite :

```python
manifest = {
    "schema_version": existing_manifest["schema_version"],
    "experiment_id": existing_manifest["experiment_id"],
}
repository.save_manifest(path, manifest)
```

Cette reconstruction fermée supprime silencieusement toute extension inconnue
qui n’appartient pas à la liste recopiée.

## Compatibilité

Le chemin historique `AcousticBrain.analyze(project)` reste inchangé et
n’affiche aucune section de découverte. `ImportEngine.load_directory` sait
retrouver `baseline` lorsque l’ancien appel pointe désormais vers une racine
structurée. Le golden acoustique historique reste conservé ; la fixture de
travail PR-027 utilise toutefois des WAV plus courts que les anciens exports
impulsionnels texte et n’est pas utilisée pour réécrire cette référence.
