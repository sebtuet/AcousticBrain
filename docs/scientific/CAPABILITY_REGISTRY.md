# Registre descriptif des capacités scientifiques d’AcousticBrain

## Autorité et statut

**Autorité documentaire : DESCRIPTIVE.**

Ce registre est un instantané auditable des transformations de connaissance
observées dans AcousticBrain à la révision
`5752ed72c1d75edd9098265ba8e90a49143a3ea5`.

Il est subordonné à `SCIENTIFIC_CONTRACT.md`. Il ne crée aucune connaissance,
ne définit aucune Scientific Question, ne confère aucune autorité scientifique
à une transformation et ne démontre pas sa conformité. Il référence uniquement
des faits établis par l’audit du dépôt.

Ce document ne précise aucune clause normative. Il fournit des éléments
descriptifs d’audit relatifs à `SC-CAP-001`, `SC-SQ-001`, `SC-AST-001`,
`SC-VAL-001`, `SC-VAL-002` et `SC-CON-001`, sans en modifier les exigences.

Une entrée décrit l’existence d’une transformation ; elle ne signifie ni que
la transformation est gouvernée, ni que ses affirmations satisfont le contrat,
ni qu’elle est scientifiquement validée.

## Séparation des autorités

```text
Autorité scientifique
        ↓
SCIENTIFIC_QUESTIONS.md — NORMATIF, absent à la révision auditée
        ↓ gouverne explicitement
CAPABILITY_REGISTRY.md — DESCRIPTIF
        ↓ décrit les transformations observées
Contrat transversal des affirmations — NORMATIF, non établi à la révision auditée
```

Les invariants suivants s’appliquent :

- le registre NE DOIT PAS créer ou reconstruire une Scientific Question ;
- une Scientific Question NE DOIT PAS être déduite du code, des tests, de
  l’orchestration ou d’un contrat historique ;
- les axes d’état sont indépendants et aucun NE DOIT être dérivé
  automatiquement d’un autre ;
- le registre NE DOIT PAS transformer une absence de preuve en absence de
  capacité ;
- chaque information factuelle DOIT citer sa source et la nature de celle-ci ;
- toute modification du moteur exige un nouvel audit avant modification du
  présent instantané.

## Vocabulaires descriptifs

| Dimension | Valeurs autorisées |
|---|---|
| Existence | `OBSERVÉE`, `NON OBSERVÉE` |
| Gouvernance | `RELIÉE`, `NON RELIÉE` |
| Contrat d’affirmation | `SATISFAIT`, `PARTIEL`, `NON SATISFAIT` |
| Validation logicielle | `DÉMONTRÉE`, `PARTIELLE`, `NON DÉMONTRÉE` |
| Validation scientifique | `DÉMONTRÉE`, `PARTIELLE`, `NON DÉMONTRÉE`, `NON APPLICABLE` |

`NON APPLICABLE` exige une justification explicite. Il ne peut pas remplacer
une validation scientifique simplement absente.

Les natures de source sont :

- **Code** : transformation effectivement exécutée ;
- **Modèle** : entrées, sorties et invariants structurés ;
- **Orchestration** : insertion et dépendances dans un flux exécuté ;
- **Test** : comportement logiciel exercé ;
- **Contrat historique** : intention antérieure au contrat scientifique ;
- **Documentation** : description non normative de l’architecture.

Un contrat historique constitue une source descriptive. Il n’est pas une
autorité normative au sens du contrat scientifique tant qu’il ne déclare pas
sa subordination et les clauses qu’il précise.

## Méthode d’inventaire

Une transformation est inscrite lorsqu’au moins un moteur ou service
exécutable est observé et qu’une sortie de connaissance identifiable est
produite. Les stages d’orchestration génériques, présentateurs, consoles,
adaptateurs, importateurs, commandes, persistence et Advisor ne sont pas
inscrits comme capacités autonomes.

Les identifiants `CAP-*` sont des identifiants de registre. Ils n’indiquent ni
un rang, ni une maturité, ni une priorité.

## Matrice d’état

À la révision auditée, les 48 capacités ci-dessous partagent les constats
suivants :

- **Existence : `OBSERVÉE`**, démontrée par les sources de code et tests ;
- **Gouvernance : `NON RELIÉE`**, car aucune Scientific Question normative
  n’est présente dans le dépôt ;
- **Contrat d’affirmation : `NON SATISFAIT`**, car aucun contrat transversal
  commun ne porte tous les attributs de `SC-AST-001` ;
- **Validation scientifique : `NON DÉMONTRÉE`**, faute de validation externe
  indépendante déclarée selon `SC-VAL-002`.

La validation logicielle est indiquée individuellement. Ces dimensions ne
constituent pas un statut global.

| Identifiant | Capacité observée | Existence | Gouvernance | Contrat d’affirmation | Validation logicielle | Validation scientifique |
|---|---|---|---|---|---|---|
| CAP-001 | Qualité des mesures | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-002 | Exploitabilité des mesures | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-003 | Description guidée de la salle | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-004 | Construction de la géométrie de salle | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-005 | Projection des caractéristiques de salle | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-006 | Qualification des matériaux surfaciques | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-007 | Géométrie de propagation planaire | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-008 | Analyse des modes propres | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-009 | Analyse de densité modale | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-010 | Analyse stéréo | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-011 | Analyse SBIR spectrale | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-012 | Analyse RT60 | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-013 | Analyse ETC | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-014 | Analyse de clarté | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-015 | Analyse d’énergie directe et réverbérée | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-016 | Analyse de décroissance grave | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-017 | Analyse spatiale | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-018-A | Corrélation directe/réverbérée | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-018-B | Corrélation décroissance grave–modes | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-018-C | Corrélation de clarté | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-018-D | Corrélation ETC–réflexions | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-018-E | Interprétation et corrélation spatiales | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-019 | Prédiction géométrique des premières réflexions | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-020 | Prédiction géométrique SBIR | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-021 | Corrélation SBIR–géométrie | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-022 | Qualification de confiance historique | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-023 | Classement de candidats de réflexion tenant compte des matériaux | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-024 | Planification de vérification de réflexion contrôlée | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-025 | Comparaison d’expériences de réflexion contrôlée | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-026 | Mise à jour du statut d’une hypothèse de réflexion | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-027 | Synthèse d’observations acoustiques déterministes | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-028 | Raisonnement acoustique historique | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-029 | Raisonnement acoustique déterministe | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-030 | Actions correctives déterministes | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-031 | Pondération déterministe multidimensionnelle des preuves | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-032 | Planification déterministe d’acquisition de preuves | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-033 | Génération d’hypothèses et d’expériences acoustiques | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-035 | Comparaison automatique d’expériences | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-036 | Synthèse de campagne expérimentale | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-037 | Discrimination causale expérimentale | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-038 | État d’apprentissage expérimental longitudinal | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-039 | Planification expérimentale | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-040 | Proposition déterministe d’expérience de positionnement | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-041 | Plan de campagne de positions d’écoute | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-042 | Qualification d’une référence de campagne | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-043 | Synthèse globale de connaissances | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-044 | Recommandations structurées | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |
| CAP-045 | Traçabilité structurée | OBSERVÉE | NON RELIÉE | NON SATISFAIT | DÉMONTRÉE | NON DÉMONTRÉE |

## Fiches factuelles

Les mentions « aucune hypothèse explicite observée » et « aucune condition de
révision explicite observée » sont des résultats d’audit. Elles ne déclarent
pas qu’aucune hypothèse ou révision ne devrait exister.

### CAP-001 à CAP-017 — Analyses descriptives et physiques

| ID | Objectif observé | Transformation | Entrées épistémiques | Sorties épistémiques | Hypothèses manipulées | Refus observés | Domaine observé | Révision observée |
|---|---|---|---|---|---|---|---|---|
| CAP-001 | Qualifier la qualité exploitable d’un jeu de mesures | mesures → issues et qualité par canal/jeu | mesures importées | faits de qualité, limitations, confiance | aucune explicite | données absentes, invalides ou incohérentes | mesures REW/impulsion prises en charge | aucune condition explicite |
| CAP-002 | Déterminer les familles d’analyse autorisées | qualité → état d’exploitabilité | résultats CAP-001 | statuts de disponibilité et motifs | aucune explicite | famille bloquée par qualité insuffisante | familles d’analyse déclarées | recalcul depuis CAP-001 |
| CAP-003 | Construire une description déclarée de la salle | déclarations utilisateur → description validée | dimensions, positions, surfaces, ouvertures, mobilier | description et erreurs structurées | aucune explicite | ambiguïtés et incohérences géométriques | salle décrite dans le repère déclaré | nouvelle proposition explicite |
| CAP-004 | Construire une géométrie consommable | description → géométrie résolue | CAP-003 ou modèle historique | surfaces, sources, positions et qualité de provenance | aucune explicite | données géométriques manquantes ou invalides | géométrie déclarée de la salle | reconstruction depuis description |
| CAP-005 | Projeter orientations, matériaux et mobilier | caractéristiques déclarées → géométrie enrichie | description et catalogue | caractéristiques structurées et complétude | aucune explicite | cible ou relation invalide | caractéristiques déclarées | nouvelle description/version |
| CAP-006 | Qualifier les matériaux selon la fréquence | matériaux déclarés → propriétés par bande | affectations et catalogue versionné | analyse de matériaux et limitations | aucune explicite | matériau ou cible inconnu | catalogue et bandes déclarés | changement de description/catalogue |
| CAP-007 | Produire une scène de propagation | géométrie → trajets et distances | CAP-004 | faits géométriques de propagation | modèle planaire ou rectangulaire déclaré | géométrie insuffisante | géométrie déclarée, sans validation acoustique | recalcul depuis géométrie |
| CAP-008 | Calculer les modes propres | dimensions → modes axiaux/tangentiels/obliques | dimensions de salle | fréquences et types modaux | modèle de salle rectangulaire | dimensions indisponibles | salle rectangulaire déclarée | recalcul depuis dimensions |
| CAP-009 | Qualifier la distribution modale | modes → faits de densité | résultats CAP-008 | densité, espacements et confiance | aucune explicite | modes insuffisants | ensemble modal calculé | recalcul depuis modes |
| CAP-010 | Comparer les canaux stéréo | caractéristiques gauche/droite → faits stéréo | mesures et pics par canal | distribution et asymétries structurées | aucune explicite | canaux requis absents | paire de canaux disponible | recalcul depuis mesures |
| CAP-011 | Identifier des candidats SBIR spectraux | pics/creux et géométrie disponible → candidats | spectre et positions disponibles | candidats SBIR et confiance | interaction enceinte–limite | entrées nécessaires absentes | géométrie et fréquences prises en charge | recalcul depuis sources |
| CAP-012 | Estimer la décroissance RT60 | mesures de décroissance → RT60 par bande/canal | données REW ou impulsion | faits RT60, confiance et utilisabilité | modèle de décroissance déclaré historiquement | décroissance inexploitable | bandes et plages prises en charge | recalcul depuis mesures |
| CAP-013 | Extraire les événements temporels précoces | impulsion → événements ETC | réponses impulsionnelles | énergie et événements de réflexion | aucune explicite au niveau descriptif | impulsion absente ou inexploitable | fenêtre ETC déclarée historiquement | recalcul depuis impulsion |
| CAP-014 | Calculer la clarté par bande | énergie temporelle → indices de clarté | impulsion et fenêtres | faits C50/C80 par bande/canal | aucune explicite | énergie ou fenêtre inexploitable | fenêtres et bandes déclarées | recalcul depuis impulsion |
| CAP-015 | Calculer le rapport direct/réverbéré | fenêtres d’énergie → rapport par bande | impulsion et fenêtres | énergie directe, réverbérée et rapports | aucune explicite | fenêtres indisponibles | fenêtres temporelles déclarées | recalcul depuis impulsion |
| CAP-016 | Qualifier la persistance grave | décroissance par bande → faits de persistance | mesures de décroissance | durées, différences et correspondances modales | persistance modale possible dans les corrélations | décroissance inexploitable | bandes graves prises en charge | recalcul depuis mesures |
| CAP-017 | Comparer des mesures spatiales | canaux/positions → différences spatiales | mesures étiquetées spatialement | faits spatiaux et interprétation conditionnelle | dépend du protocole de mesure | protocole ou paire incompatible | protocoles spatiaux reconnus | recalcul depuis mesures/protocole |

### CAP-018-A à CAP-026 — Corrélations, prédictions et hypothèses

| ID | Objectif observé | Transformation | Entrées épistémiques | Sorties épistémiques | Hypothèses manipulées | Refus observés | Domaine observé | Révision observée |
|---|---|---|---|---|---|---|---|---|
| CAP-018-A | Relier énergie directe/réverbérée et faits associés | analyses structurées → corrélation directe/réverbérée | CAP-015 et analyses compatibles | correspondances et limitations direct/réverbéré | interprétation directe/réverbérée codée | sources absentes ou non comparables | sources déclarées par le moteur | recalcul depuis analyses |
| CAP-018-B | Relier décroissance grave et modes | analyses structurées → corrélation bass decay | CAP-008 et CAP-016 | correspondances modales et limitations | persistance modale possible | sources absentes ou non comparables | bandes et modes pris en charge | recalcul depuis analyses |
| CAP-018-C | Relier les faits de clarté | analyses structurées → corrélation de clarté | CAP-014 et analyses compatibles | correspondances et limitations de clarté | interprétation de clarté codée | sources absentes ou non comparables | bandes prises en charge | recalcul depuis analyses |
| CAP-018-D | Relier événements ETC et candidats de réflexion | analyses structurées → corrélation ETC | CAP-013 et candidats compatibles | correspondances temporelles et limitations | interaction de réflexion possible | sources absentes ou non comparables | fenêtres et tolérances prises en charge | recalcul depuis analyses |
| CAP-018-E | Interpréter les différences spatiales | analyses spatiales → interprétation et corrélation | CAP-017 et protocole | statuts, correspondances et limitations spatiales | interprétation conditionnée par le protocole | protocole ou sources incompatibles | protocoles spatiaux reconnus | recalcul depuis analyses |
| CAP-019 | Prédire des trajets de premières réflexions | géométrie → chemins de réflexion | CAP-004 et CAP-007 | trajets, délais et surfaces candidates | réflexion spéculaire géométrique | géométrie incomplète | modèle géométrique déclaré | recalcul depuis géométrie |
| CAP-020 | Prédire des candidats SBIR géométriques | géométrie source–limite → fréquences candidates | CAP-004 et CAP-007 | candidats SBIR géométriques | interférence source–image | données géométriques insuffisantes | modèle géométrique déclaré | recalcul depuis géométrie |
| CAP-021 | Comparer SBIR spectral et géométrique | CAP-011 + CAP-020 → compatibilités | candidats spectraux et géométriques | correspondances, écarts et limitations | compatibilité SBIR, sans causalité automatique | candidats absents ou incompatibles | tolérances déclarées par le moteur | recalcul depuis candidats |
| CAP-022 | Synthétiser des facteurs de confiance historiques | analyses → confiance agrégée | analyses disponibles | facteurs et confiance | aucune explicite | sources insuffisantes | analyses historiques prises en charge | recalcul depuis sources |
| CAP-023 | Classer les réflexions compatibles avec les matériaux | géométrie + matériaux + ETC → candidats ordonnés | CAP-006, CAP-013, CAP-019 | candidats et provenance séparée | interaction de réflexion possible | dépendances absentes | candidats existants uniquement | recalcul depuis dépendances |
| CAP-024 | Planifier une comparaison contrôlée de réflexion | candidats → vérifications | CAP-023 | actions de vérification et blocages | hypothèse de réflexion existante | candidat ou paramètres absents | candidats pris en charge | nouveau calcul depuis candidat |
| CAP-025 | Comparer une déclaration et des mesures d’intervention | expérience contrôlée → comparaison | déclaration, référence, intervention | différences et statut de comparaison | effet de réflexion déclaré | expérience non comparable | expérience de réflexion déclarée | nouvelle comparaison versionnée |
| CAP-026 | Mettre à jour le statut observé d’une hypothèse | comparaison → transition de statut | CAP-025 et statut antérieur | nouveau statut et provenance | hypothèse de réflexion déclarée | transition interdite ou preuve absente | vocabulaire de statuts déclaré | historique de transitions conservé |

### CAP-027 à CAP-032 — Chaîne déterministe d’expertise

| ID | Objectif observé | Transformation | Entrées épistémiques | Sorties épistémiques | Hypothèses manipulées | Refus observés | Domaine observé | Révision observée |
|---|---|---|---|---|---|---|---|---|
| CAP-027 | Synthétiser des observations descriptives | analyses → observations | analyses factuelles et corrélations | observations, preuves citées, contradictions, limitations | aucune nouvelle hypothèse autorisée | règle ou preuve absente | règles d’observation codées | recalcul intégral |
| CAP-028 | Produire un raisonnement historique | faits → éléments de reasoning | analyses et corrélations historiques | raisonnements, scores et actions associées | hypothèses acoustiques historiques | faits requis absents | règles historiques | recalcul intégral |
| CAP-029 | Expliquer déterministement des hypothèses existantes | observations → premises et inférences | CAP-027 et hypothèses existantes | conclusions codées, contradictions et limitations | asymétrie, persistance modale, réflexion dominante, SBIR | aucune règle applicable ou preuve insuffisante | jeu de règles explicitement codé | recalcul intégral |
| CAP-030 | Dériver des actions correctives bornées | reasonings → actions et blocages | CAP-027 et CAP-029 | actions, applicabilité, paramètres et justifications | aucune hypothèse nouvelle | contradiction ou paramètres manquants | règles d’action codées | recalcul intégral |
| CAP-031 | Qualifier plusieurs dimensions de preuve | observations + reasonings + actions → vecteurs | CAP-027 à CAP-030 | forces, cohérence, discrimination, complétude, plafonds | hypothèses déjà référencées | références ou traçabilité invalides | règles de pondération codées | recalcul intégral |
| CAP-032 | Planifier l’acquisition manquante | blocages + pondération → plans | CAP-029 à CAP-031 | plans READY/BLOCKED, priorités et limitations | hypothèses existantes uniquement | absence de blocage ou paramètres requis | taxonomie de plans codée | recalcul intégral |

### CAP-033 à CAP-042 — Expérimentation et campagnes

| ID | Objectif observé | Transformation | Entrées épistémiques | Sorties épistémiques | Hypothèses manipulées | Refus observés | Domaine observé | Révision observée |
|---|---|---|---|---|---|---|---|---|
| CAP-033 | Générer des hypothèses et expériences contrôlées | analyses → hypothèses/expériences candidates | analyses et corrélations | hypothèses, variables, mesures attendues et refus | SBIR, réflexion, asymétrie, persistance modale | support, protocole ou paramètres insuffisants | quatre familles codées | régénération depuis sources |
| CAP-035 | Comparer automatiquement des expériences | baseline/interventions → différences | descripteurs découverts et analyses par expérience | comparaisons et limites de causalité | effets déclarés par expérience | non-comparabilité | campagnes déclarées | nouvelle comparaison |
| CAP-036 | Synthétiser une campagne expérimentale | comparaisons → état de campagne | CAP-035 | synthèses par cible et trajectoire | hypothèses déclarées de campagne | preuves incompatibles ou absentes | campagne comparable | recalcul depuis comparaisons |
| CAP-037 | Qualifier une discrimination causale | étapes déclarées + comparaisons → trajectoire | déclarations causales et CAP-035 | statuts, contradictions et prochaines informations | hypothèses causales explicitement déclarées | étape, comparaison ou association absente | protocoles causaux pris en charge | état versionné |
| CAP-038 | Synthétiser l’apprentissage longitudinal | historique expérimental → état longitudinal | CAP-035 à CAP-037 | répétitions, informations nouvelles, contradictions | hypothèses suivies dans le temps | comparabilité ou provenance insuffisante | historique déclaré | recalcul depuis historique |
| CAP-039 | Planifier des expériences | diagnostics et contexte → plans | connaissances disponibles | plans, scores techniques et blocages | hypothèses historiques prises en charge | protocole, session ou paramètres absents | règles de planification codées | nouvelle planification |
| CAP-040 | Proposer une expérience de positionnement | connaissances → déplacement contrôlé proposé | plans, géométrie et contexte | proposition, variables et critères | interaction enceinte–salle | distance ou géométrie non démontrée | positionnement déclaré | nouvelle proposition |
| CAP-041 | Construire un plan de campagne d’écoute | protocole + hypothèses → étapes | protocole et expériences candidates | plan, référence, étapes et statut | hypothèses prises en charge par le protocole | référence ou structure incompatible | protocole d’écoute déclaré | reconstruction depuis déclaration |
| CAP-042 | Qualifier une référence de campagne | déclaration + campagne réelle → qualification | manifeste, protocole, plan et historique | qualification, assertions rejetées et rapport | aucune hypothèse nouvelle | contradiction, absence ou incompatibilité | campagne déclarée | recalcul en lecture seule |

### CAP-043 à CAP-045 — Synthèse, décision et traçabilité

| ID | Objectif observé | Transformation | Entrées épistémiques | Sorties épistémiques | Hypothèses manipulées | Refus observés | Domaine observé | Révision observée |
|---|---|---|---|---|---|---|---|---|
| CAP-043 | Synthétiser plusieurs domaines acoustiques | analyses → domaines et corrélations globales | analyses physiques disponibles | analyse globale, priorités et corrélations | interprétations historiques | sources absentes conservées | domaines historiques pris en charge | recalcul depuis analyses |
| CAP-044 | Produire des recommandations structurées | analyses globales → recommandations | CAP-043 et analyses sources | actions, priorités, confiance et provenance | interprétations historiques | aucune recommandation si conditions absentes | règles historiques | recalcul depuis sources |
| CAP-045 | Relier recommandations et faits sources | faits + corrélations + actions → liens | CAP-043, CAP-044 et analyses | références et liens d’explication | aucune nouvelle hypothèse | chaîne incomplète non inventée | sources structurées connues | recalcul depuis sources |

## Sources d’audit typées

Les plages d’identifiants ci-dessous n’effacent pas la provenance
individuelle : elles regroupent des capacités qui partagent une même frontière
d’orchestration. Les contrats historiques associés portent le nom de la
capacité dans `docs/`.

| Capacités | Transformation — Code | Sorties — Modèle | Flux — Orchestration | Validation — Test | Domaine/refus — Contrat historique |
|---|---|---|---|---|---|
| CAP-001–002 | `analysis/measurement_quality.py`, `analysis/measurement_readiness.py` | `models/measurement_quality_analysis.py`, `models/measurement_readiness_analysis.py` | `brain/stages/measurement_quality.py`, `brain/stages/measurement_readiness.py` | `test_measurement_quality_*`, `test_measurement_readiness.py` | `MEASUREMENT_QUALITY_CONTRACT.md` |
| CAP-003–006 | `application/guided_room_description.py`, `analysis/room_geometry_builder.py`, `analysis/surface_material.py` | `models/room_description.py`, `models/room_geometry.py`, `models/surface_material_analysis.py` | `brain/stages/room_geometry.py`, `brain/stages/surface_material.py` | `test_room_description_*`, `test_room_geometry_*`, `test_surface_material_*` | `ROOM_DESCRIPTION_CONTRACT.md`, `ROOM_GEOMETRY_CONTRACT.md`, `ROOM_FEATURES_CONTRACT.md`, `FREQUENCY_DEPENDENT_SURFACE_MATERIALS_CONTRACT.md` |
| CAP-007 | `analysis/propagation_geometry.py` | `models/propagation_geometry.py` | `brain/stages/propagation_geometry.py` | `test_propagation_geometry_*`, `test_planar_geometry_*` | `PLANAR_PROPAGATION_GEOMETRY_CONTRACT.md` |
| CAP-008–011 | `analysis/room_modes.py`, `analysis/modal_density.py`, `analysis/stereo.py`, `analysis/sbir.py` | modèles correspondants dans `models/` | `brain/stages/physics.py`, `brain/stages/analysis.py` | `test_room_modes_*`, `test_modal_density_*`, `test_stereo_*`, `test_geometry_sbir_*` | `ROOM_MODES_CONTRACT.md`, `GEOMETRY_DRIVEN_SBIR_CONTRACT.md` |
| CAP-012–016 | analyzers et aggregators `rt60`, `etc`, `clarity`, `direct_reverberant`, `bass_decay` | modèles correspondants dans `models/` | `brain/stages/temporal_analysis.py` | tests portant les mêmes domaines | `RT60_CONTRACT.md`, `ETC_CONTRACT.md`, `CLARITY_CONTRACT.md`, `DIRECT_REVERBERANT_CONTRACT.md`, `BASS_DECAY_CONTRACT.md` |
| CAP-017 | `analysis/spatial.py` | modèles `spatial*` | stages `spatial_*` | tests de spatial | `SPATIAL_ANALYSIS_CONTRACT.md` |
| CAP-018-A–CAP-018-E | moteurs `*_correlation.py` et `spatial_interpretation.py` | modèles `*_correlation*` et interprétations spatiales | stages de corrélation et d’interprétation | tests de corrélation par domaine | contrats historiques des domaines concernés |
| CAP-019–021 | `analysis/geometry_early_reflection.py`, `analysis/geometry_sbir.py` | `models/geometry_early_reflection_analysis.py`, `models/geometry_sbir_candidate.py` | stages géométriques correspondants | `test_geometry_early_reflection.py`, `test_geometry_sbir.py`, tests d’intégration | `GEOMETRY_DRIVEN_EARLY_REFLECTIONS_CONTRACT.md`, `GEOMETRY_DRIVEN_SBIR_CONTRACT.md` |
| CAP-022 | `analysis/confidence.py` | `models/confidence_analysis.py` | `brain/stages/confidence.py` | `test_confidence_*` | `ANALYSIS_CONTRACT.md`, `SCORING.md` |
| CAP-023–026 | moteurs `material_aware_reflection_candidate`, `reflection_verification_planning`, `reflection_experiment_comparison`, `reflection_hypothesis_status_update` | modèles correspondants | stages correspondants | tests `material_aware_*`, `reflection_*` | quatre contrats historiques `MATERIAL_AWARE_*` et `CONTROLLED_REFLECTION_*` |
| CAP-027 | `analysis/acoustic_observation.py` | `models/acoustic_observation.py` | `brain/stages/acoustic_observation.py` | `test_acoustic_observation.py` | `DETERMINISTIC_ACOUSTIC_OBSERVATIONS.md` |
| CAP-028–029 | `analysis/acoustic_reasoning.py`, `analysis/deterministic_acoustic_reasoning.py` | modèles de reasoning correspondants | stages de reasoning correspondants | `test_acoustic_reasoning_*`, `test_deterministic_acoustic_reasoning.py` | `ACOUSTIC_REASONING_CONTRACT.md`, `DETERMINISTIC_ACOUSTIC_REASONING.md` |
| CAP-030 | `analysis/deterministic_corrective_action.py` | `models/deterministic_corrective_action.py` | `brain/stages/deterministic_corrective_action.py` | `test_deterministic_corrective_action.py` | `DETERMINISTIC_CORRECTIVE_ACTIONS.md` |
| CAP-031 | `analysis/evidence_weighting.py` | `models/evidence_weighting.py` | `brain/stages/evidence_weighting.py` | `test_evidence_weighting.py` | `DETERMINISTIC_EVIDENCE_WEIGHTING.md` |
| CAP-032 | `analysis/evidence_acquisition.py` | `models/evidence_acquisition.py` | `brain/stages/evidence_acquisition.py` | `test_evidence_acquisition.py` | `DETERMINISTIC_EVIDENCE_ACQUISITION.md` |
| CAP-033 | `analysis/acoustic_hypothesis_experiment_generation.py` | modèle correspondant | stage correspondant | `test_acoustic_hypothesis_experiment_generation.py` | `DETERMINISTIC_ACOUSTIC_HYPOTHESIS_EXPERIMENT_GENERATION_CONTRACT.md` |
| CAP-035–038 | services `automatic_experiment_comparison`, `experiment_campaign_synthesis`, `causal_discrimination` et moteur longitudinal | modèles de comparaison, campagne, causalité et longitudinal | `brain/brain.py` et stage longitudinal | tests de comparaison, campagne, causalité et longitudinal | contrats historiques correspondants |
| CAP-039–040 | `analysis/experiment_planning.py`, `analysis/loudspeaker_positioning_experiment.py` | modèles correspondants | stages correspondants | `test_experiment_planning_*`, `test_loudspeaker_positioning_experiment.py` | `EXPERIMENT_PLANNING_CONTRACT.md`, `DETERMINISTIC_LOUDSPEAKER_POSITIONING_EXPERIMENT_PROPOSAL_CONTRACT.md` |
| CAP-041–042 | `analysis/listening_position_campaign_plan.py`, `analysis/campaign_reference_qualification.py` | modèles correspondants | stages correspondants et `main.py` | tests de campagne et qualification | `LISTENING_POSITION_CAMPAIGN_PLAN_CONTRACT.md`, `CAMPAIGN_REFERENCE_QUALIFICATION_CONTRACT.md` |
| CAP-043–045 | `analysis/global_synthesizer.py`, `analysis/recommendation.py`, `analysis/traceability.py` | modèles globaux, recommandation et traçabilité | stages correspondants | `test_global_*`, `test_recommendation_*`, `test_traceability_*` | `GLOBAL_KNOWLEDGE_EXPANSION_CONTRACT.md`, `RECOMMENDATION_CONTRACT.md`, `TRACEABILITY_CONTRACT.md` |

## Éléments explicitement exclus

Les éléments suivants ont été observés mais ne sont pas inscrits comme
capacités scientifiques autonomes :

- présentateurs, rapports console et synthèses éditoriales ;
- Optional LLM Advisor et ses fournisseurs ;
- importateurs REW, texte et WAV ;
- persistence et sérialisation ;
- commandes et interfaces utilisateur ;
- diagnostics de présentation ;
- stages génériques d’orchestration ;
- découverte de répertoires et lecture de manifestes d’expériences ;
- stockage et restitution d’une session d’optimisation ;
- déclarations ou associations manuelles qui enregistrent une information sans
  produire seules une transformation scientifique ;
- `SPLAnalyzer`, que le dépôt documente comme non intégré à une capacité.

Cette exclusion ne juge ni leur utilité ni leur conformité logicielle.

## Validation de l’instantané

À la révision auditée :

- la suite complète contient `1 496` tests réussis ;
- la compilation Python réussit ;
- aucune Scientific Question normative n’est présente ;
- aucun ancien `*CONTRACT*.md` ne déclare sa subordination au contrat
  scientifique ;
- aucune validation scientifique externe indépendante n’est démontrée ;
- aucun algorithme acoustique n’a été modifié pour produire ce registre.

Le registre devra être réaudité si sa révision source, son périmètre
d’inventaire ou l’un de ses axes descriptifs change.
