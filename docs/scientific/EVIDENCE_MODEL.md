# Modèle normatif de la preuve

> Ce document est subordonné à `SCIENTIFIC_CONTRACT.md`. En cas de conflit
> scientifique ou épistémique, le contrat scientifique prévaut.

## Clauses du contrat précisées

Ce document précise les clauses `SC-EVD-001`, `SC-EVD-002`, `SC-EVD-003`,
`SC-SCP-001`, `SC-SCP-002`, `SC-REF-001`, `SC-REV-002` et `SC-TRC-001`.

## Objet

Le présent document précise la preuve scientifique comme relation orientée. Il
ne définit ni algorithme de pondération, ni formule de fusion, ni mécanisme
d’implémentation.

## Définition

Une preuve est une relation orientée entre un fait source et une hypothèse
cible. Elle exprime exclusivement comment le fait modifie l’état de
connaissance relatif à cette hypothèse, selon une règle d’interprétation et dans
un domaine de validité déclarés.

Une mesure ou un fait isolé NE DOIT PAS être appelé preuve en l’absence
d’hypothèse cible. Une preuve NE DOIT PAS être interprétée comme une vérité
absolue ni comme une causalité, sauf si sa règle et ses conditions permettent
explicitement cette portée.

## Contrat obligatoire

Toute preuve DOIT déclarer :

- **fait source** : fait auquel la relation probante s’applique ;
- **hypothèse cible** : proposition dont l’état de connaissance est affecté ;
- **direction** : effet épistémique du fait sur l’hypothèse ;
- **force** : niveau ordinal déclaré de la contribution probante ;
- **règle d’interprétation** : règle qui autorise la direction et la force ;
- **domaine de validité** : conditions dans lesquelles la règle s’applique ;
- **provenance** : mesures, transformations et règles permettant l’audit.

Lorsqu’un de ces éléments est absent, la relation DOIT être considérée comme
incomplète et NE DOIT PAS autoriser une conclusion scientifique qui exige cet
élément.

## Direction

La direction DOIT appartenir à un vocabulaire déclaré qui distingue au
minimum :

- **favorable** : le fait soutient l’hypothèse cible ;
- **défavorable** : le fait affaiblit l’hypothèse cible ;
- **neutre** : le fait n’altère pas son support dans le domaine déclaré ;
- **contradictoire** : le fait est incompatible avec une connaissance retenue
  dans des conditions comparables ;
- **insuffisante** : la relation ne permet pas de déterminer un effet probant
  dans la portée demandée.

Une direction défavorable NE constitue pas automatiquement une réfutation. Une
direction contradictoire DOIT préserver les éléments en contradiction. Une
direction insuffisante DOIT rester un résultat explicite.

## Force

La force exprime la limite de ce qu’une preuve peut contribuer à une
conclusion scientifique. Elle appartient à l’ordre total :

`NON DÉMONTRÉ < INSUFFISANT < FAIBLE < MODÉRÉ < FORT`.

Cette échelle est ordinale et non numérique. Elle rend toute comparaison de
force non ambiguë mais ne donne, à elle seule, aucun sens physique aux niveaux.
Le critère attribuant un niveau DOIT être défini par la Scientific Question,
la règle d’interprétation, une clause du contrat ou un protocole de validation.

- la force NE DOIT PAS être augmentée par répétition d’une même provenance ;
- le nombre de données NE DOIT PAS remplacer l’évaluation de leur pertinence ;
- un score ou une confiance NE DOIT PAS renforcer la portée scientifique sans
  règle probante déclarée ;
- la maturité de la capacité productrice NE DÉTERMINE PAS la force de la preuve
  dans un cas particulier.

Le présent modèle ne prescrit aucune échelle numérique de force.

## Domaine de validité

Le domaine de validité DOIT préciser les conditions nécessaires à
l’interprétation de la preuve, notamment les conditions d’acquisition, les
hypothèses de mesure, les populations ou configurations concernées et les
facteurs limitants connus lorsqu’ils s’appliquent.

Une preuve hors domaine DOIT être qualifiée comme telle et NE DOIT PAS être
utilisée pour produire une conclusion scientifique dans ce domaine. Deux
preuves obtenues dans des domaines non comparables NE DOIVENT PAS être
déclarées contradictoires sans règle de comparaison explicite.

## Provenance

La provenance d’une preuve DOIT permettre de remonter :

1. au fait source ;
2. aux mesures dont le fait est dérivé ;
3. aux conditions d’acquisition ;
4. à la transformation productrice du fait ;
5. à la règle d’interprétation probante ;
6. à l’hypothèse cible ;
7. aux révisions, réfutations ou retraits ultérieurs.

Une preuve dont la provenance est incomplète DOIT signaler cette limitation et
NE DOIT PAS être présentée comme pleinement auditable.

## Règle d’interprétation

La règle d’interprétation DOIT définir de manière testable :

- les propriétés requises du fait source ;
- les conditions applicables à l’hypothèse cible ;
- la direction autorisée ;
- la force maximale autorisée ;
- le domaine de validité ;
- les conditions d’insuffisance ou de refus ;
- les observations susceptibles de réviser la relation.

Une règle NE DOIT PAS transformer une simple compatibilité en causalité,
utiliser une absence de détection comme preuve d’absence ou exclure une
hypothèse concurrente non examinée.

## Hypothèses concurrentes

Une preuve est évaluée relativement à une hypothèse cible. Lorsqu’un même fait
est pertinent pour plusieurs hypothèses concurrentes, chaque relation DOIT être
déclarée séparément avec sa propre direction, sa propre force et sa propre règle
d’interprétation.

Toute hypothèse concurrente pertinente non examinée DOIT être signalée. Le
support d’une hypothèse NE DOIT PAS être assimilé à la réfutation de ses
concurrentes.

## Contradiction, insuffisance et refus

Les preuves favorables, défavorables, contradictoires et insuffisantes DOIVENT
rester distinctes et traçables. Une contradiction non résolue ou une
insuffisance pertinente au regard d’un critère explicite PEUT imposer une
conclusion scientifique `INDÉTERMINÉ` ou une acquisition de preuve.

Le refus de conclure DOIT être produit lorsque la direction, la force, la
provenance ou le domaine de validité disponibles ne suffisent pas à la portée
de conclusion scientifique demandée.

## Composition des preuves

Le présent modèle ne définit aucune formule de fusion, moyenne, probabilité ou
score global. Une composition de preuves NE DOIT PAS :

- masquer une direction contradictoire ou insuffisante ;
- effacer les provenances individuelles ;
- produire une force supérieure sans règle de composition validée ;
- dépasser la portée du maillon probant le plus limitant ;
- convertir un volume de preuves en certitude causale.

Toute règle future de composition devra être explicitement subordonnée au
contrat scientifique et scientifiquement validée avant de pouvoir autoriser une
conclusion scientifique.
