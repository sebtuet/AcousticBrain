# Modèle normatif des connaissances

> Ce document est subordonné à `SCIENTIFIC_CONTRACT.md`. En cas de conflit
> scientifique ou épistémique, le contrat scientifique prévaut.

## Clauses du contrat précisées

Ce document précise les clauses `SC-TRU-003`, `SC-AST-001`, `SC-AST-002`,
`SC-EVD-001`, `SC-EVD-002`, `SC-REF-001`, `SC-REV-001`, `SC-REV-002`,
`SC-DEC-001`, `SC-DEC-002` et `SC-TRC-001`.

## Objet

Le présent document précise les types de connaissances et leurs relations
autorisées. Il ne décrit aucune architecture ni aucun moyen d’implémentation.

## Types de connaissances

### Mesure

Une mesure est une observation obtenue par un instrument ou un protocole
déclaré. Elle DOIT conserver ses conditions d’acquisition, sa provenance, son
unité lorsqu’elle s’applique, son domaine de validité et ses limitations. Une
mesure NE DOIT PAS contenir implicitement une interprétation causale.

### Fait

Un fait est une affirmation descriptive dérivée de mesures par une règle
déclarée. Il DOIT citer ses mesures sources et la règle de dérivation. Il NE
DOIT PAS dépasser ce que ces sources permettent d’observer.

### Hypothèse

Une hypothèse est une proposition réfutable visant à expliquer ou anticiper des
faits. Elle DOIT rester distincte des faits qui la motivent. Elle DOIT déclarer
ses conditions de support, d’affaiblissement, de contradiction et de
réfutation.

### Preuve

Une preuve est une relation orientée entre un fait source et une hypothèse
cible. Elle DOIT respecter `EVIDENCE_MODEL.md` et les clauses `SC-EVD-*`.

### Diagnostic

Un diagnostic caractérise un état ou un problème à partir des connaissances
disponibles. Il DOIT déclarer les faits, hypothèses et preuves qui le fondent,
ainsi que ses incertitudes. Il NE DOIT PAS être assimilé à une conclusion
scientifique causale ou à une décision.

### Conclusion scientifique

Une conclusion scientifique statue sur une hypothèse ou une Scientific
Question. Elle DOIT être bornée par la portée et la force de ses preuves,
indiquer les hypothèses concurrentes non éliminées et exposer ses conditions de
révision et de réfutation.

### Décision

Une décision est un choix orienté vers l’utilisateur. Elle DOIT citer l’état de
connaissance qui l’autorise, ses conditions d’applicabilité et ses blocages.
Elle NE DOIT PAS renforcer la conclusion scientifique dont elle dépend.

### Acquisition de preuve

Une acquisition de preuve est une action de connaissance destinée à réduire
une incertitude explicite ou à départager des hypothèses concurrentes. Elle
DOIT déclarer l’incertitude visée, les faits recherchés et les effets attendus
de chaque résultat possible sur les hypothèses.

### Affirmation scientifique

Une affirmation scientifique est la forme transversale dans laquelle un
contenu épistémique est exprimé. Elle DOIT satisfaire `SC-AST-001`, conserver
son type et sa provenance et rester révisable.

## Relations autorisées

Les relations suivantes ont un sens normatif exclusif.

- **dérivé de** : relie une connaissance à ses sources et à sa règle de
  dérivation ;
- **soutient** : indique qu’un fait augmente le support d’une hypothèse dans un
  domaine déclaré ;
- **affaiblit** : indique qu’un fait réduit le support d’une hypothèse sans
  suffire à la réfuter ;
- **contredit** : indique que des connaissances ne peuvent être simultanément
  tenues pour cohérentes dans le même domaine et sous les mêmes hypothèses ;
- **réfute** : indique qu’une preuve défavorable suffisante satisfait une règle
  explicite de réfutation ;
- **dépend de** : déclare qu’une connaissance perd ou révise sa validité lorsque
  la connaissance cible change ;
- **révise** : produit un nouvel état de connaissance à partir d’une preuve ou
  condition de révision ;
- **retire** : met fin à l’usage actif d’une affirmation tout en conservant son
  historique et la cause du retrait ;
- **autorise** : relie un état de connaissance à une décision dont toutes les
  conditions sont satisfaites ;
- **demande** : relie une incertitude à une acquisition de preuve.

Une relation non définie dans ce document NE DOIT PAS être utilisée pour
augmenter la force, la portée ou le statut d’une affirmation.

## Provenance

Toute connaissance DOIT posséder une provenance permettant d’identifier :

- ses sources directes ;
- la transformation qui l’a produite ;
- les règles appliquées ;
- les hypothèses et domaines de validité ;
- les états antérieurs en cas de révision ;
- les retraits ou réfutations qui l’affectent.

La provenance DOIT rester parcourable jusqu’aux mesures sources. Un texte de
présentation NE DOIT PAS constituer l’unique provenance d’une connaissance.

## Contradiction

Une contradiction est un état explicite entre au moins deux connaissances
incompatibles dans un même domaine et sous des conditions comparables.

- une contradiction DOIT préserver les connaissances concernées et leurs
  provenances ;
- elle NE DOIT PAS être résolue par préférence implicite, ordre d’arrivée ou
  suppression d’une source ;
- elle DOIT provoquer une réévaluation des conclusions scientifiques
  dépendantes ;
- elle PEUT conduire à `INDÉTERMINÉ` ou à une acquisition de preuve.

Une différence entre domaines de validité ou conditions d’observation NE DOIT
PAS être qualifiée de contradiction sans règle le démontrant.

## Révision

Une révision produit un nouvel état d’une connaissance à la suite d’une
condition déclarée. Elle DOIT :

- identifier l’état révisé ;
- citer la preuve ou condition déclenchante ;
- appliquer une règle de révision explicite ;
- conserver l’état antérieur ;
- propager la révision aux connaissances dépendantes.

Une révision NE DOIT PAS être utilisée pour effacer une contradiction ou
réécrire rétroactivement la provenance.

## Réfutation

Une réfutation s’applique à une hypothèse lorsque des preuves défavorables
satisfont une règle de réfutation dans leur domaine de validité. L’absence de
preuve favorable, l’absence de détection ou l’existence d’une hypothèse
concurrente NE SUFFISENT PAS à réfuter une hypothèse.

Toute réfutation DOIT conserver :

- l’hypothèse réfutée ;
- les preuves défavorables ;
- la règle et le domaine de réfutation ;
- la date ou version de l’état ;
- les connaissances dépendantes à réviser.

## Retrait

Le retrait cesse l’usage actif d’une affirmation sans prétendre nécessairement
qu’elle est fausse. Il DOIT déclarer sa cause, sa règle et ses conséquences.
Une affirmation retirée DOIT rester accessible à l’audit et NE DOIT PLUS
autoriser de nouvelle conclusion scientifique ou décision.

Révision, réfutation et retrait NE DOIVENT PAS être employés comme synonymes.
