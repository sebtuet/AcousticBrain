# Contrat scientifique d’AcousticBrain

## Statut et autorité

Le présent document est le contrat scientifique normatif de niveau 0
d’AcousticBrain. Il prévaut, en matière scientifique et épistémique, sur tout
autre document scientifique du projet. Un document subordonné NE DOIT PAS
réduire, contourner ou contredire une exigence du présent contrat.

Ce contrat définit les règles auxquelles toute capacité, affirmation,
validation et documentation scientifique d’AcousticBrain DOIT se conformer. Il
ne décrit ni une implémentation, ni une architecture, ni un inventaire de
capacités.

## Mission

AcousticBrain est un moteur déterministe de diagnostic acoustique basé sur des
mesures.

## Vocabulaire normatif

- **DOIT** indique une obligation.
- **NE DOIT PAS** indique une interdiction.
- **DEVRAIT** indique une exigence recommandée dont toute dérogation doit être
  justifiée et auditée.
- **PEUT** indique un comportement autorisé.
- **NON DÉMONTRÉ** indique que les preuves d’audit accessibles sont
  insuffisantes pour établir la conformité ou la non-conformité.
- **INDÉTERMINÉ** indique un état scientifique valide dans lequel les preuves
  disponibles ne permettent pas de conclure dans la portée demandée.

## Définitions normatives

- **Mesure** : observation quantitative ou qualitative obtenue par un
  instrument ou un protocole déclaré, accompagnée de sa provenance, de ses
  conditions d’acquisition et de son domaine de validité.
- **Fait** : affirmation descriptive déterminée à partir d’une ou plusieurs
  mesures par une règle déclarée, sans attribution causale non démontrée.
- **Hypothèse** : proposition réfutable susceptible d’expliquer ou d’anticiper
  des faits, distincte de ces faits et de toute conclusion scientifique.
- **Preuve** : relation orientée entre un fait source et une hypothèse cible,
  interprétée par une règle déclarée dans un domaine de validité donné.
- **Diagnostic** : caractérisation structurée d’un état ou d’un problème à
  partir des connaissances disponibles. Un diagnostic n’implique pas
  nécessairement une cause établie ni une décision autorisée.
- **Conclusion scientifique** : affirmation qui statue sur une hypothèse ou
  une question scientifique dans une portée explicitement bornée par les
  preuves.
- **Décision** : choix orienté vers l’utilisateur, autorisé par un état de
  connaissance déclaré et distinct du diagnostic comme de la conclusion
  scientifique.
- **Acquisition de preuve** : action de connaissance destinée à produire les
  faits nécessaires pour réduire une incertitude ou départager des hypothèses
  concurrentes.
- **Affirmation scientifique** : objet transversal exprimant un contenu doté
  d’un type épistémique, d’une provenance, d’une portée et d’un statut
  révisable.
- **Vérité interne** : conformité déterministe d’un résultat aux entrées,
  règles et calculs déclarés dans leurs conditions de validité.
- **Vérité externe** : adéquation démontrée entre une affirmation et le
  phénomène physique auquel elle se rapporte.
- **Portée** : ensemble explicite des objets, conditions, phénomènes et usages
  auxquels une affirmation s’applique.
- **Portée maximale autorisée** : affirmation la plus forte qu’une
  transformation est autorisée à produire compte tenu de sa nature et de ses
  preuves admissibles.
- **Force probante** : niveau ordinal d’une preuve ou d’une conclusion
  scientifique. Les niveaux forment l’ordre total suivant :
  `NON DÉMONTRÉ < INSUFFISANT < FAIBLE < MODÉRÉ < FORT`. Cet ordre permet la
  comparaison ; il ne confère à lui seul aucun sens physique aux niveaux.

Le niveau de force probante `NON DÉMONTRÉ` et le statut d’audit
`NON DÉMONTRÉ` appartiennent à deux vocabulaires distincts. Leur contexte
DOIT permettre de les distinguer sans ambiguïté.

## Clauses normatives

### SC-AUT-001 — Autorité du contrat

**Exigence**

Toute règle scientifique ou épistémique subordonnée DOIT être compatible avec
le présent contrat. En cas de conflit, le contrat DOIT prévaloir.

**Critères de conformité**

- le document subordonné déclare sa subordination ;
- aucune de ses règles ne contredit une clause du contrat.

**Critères de non-conformité**

- une règle subordonnée autorise un comportement interdit par le contrat ;
- un conflit est résolu en faveur du document subordonné.

**Preuves d’audit attendues**

- corpus documentaire versionné ;
- matrice de correspondance entre exigences subordonnées et clauses du contrat.

### SC-AUT-002 — Indépendance de l’implémentation

**Exigence**

La conformité scientifique DOIT être évaluée sur les connaissances,
transformations et preuves produites. Elle NE DOIT PAS être présumée à partir
de la seule structure ou réussite d’une implémentation.

**Critères de conformité**

- l’audit examine les sorties scientifiques et leur provenance ;
- les preuves logicielles et scientifiques sont identifiées séparément.

**Critères de non-conformité**

- une réussite logicielle est présentée comme validation scientifique ;
- une structure technique est utilisée comme preuve d’exactitude physique.

**Preuves d’audit attendues**

- résultats séparés des validations logicielle et scientifique ;
- échantillons d’affirmations avec leurs preuves scientifiques.

### SC-AUT-003 — Statut exclusif d’audit

**Exigence**

Toute clause auditée DOIT recevoir exactement un et un seul des statuts
`CONFORME`, `PARTIELLEMENT CONFORME`, `NON CONFORME` ou `NON DÉMONTRÉ`.
Ces statuts sont mutuellement exclusifs. Le périmètre et l’applicabilité des
critères DOIVENT être déclarés et justifiés avant leur évaluation.

**Critères de conformité**

- chaque clause auditée possède un unique statut autorisé ;
- le statut résulte des critères applicables et des preuves d’audit déclarées ;
- tout critère déclaré non applicable possède une justification.

**Critères de non-conformité**

- plusieurs statuts sont attribués à une même clause ;
- aucun statut n’est attribué ;
- un critère est exclu sans justification.

**Preuves d’audit attendues**

- matrice versionnée clause–critères–applicabilité–preuves–statut ;
- justification des critères déclarés non applicables.

### SC-AUT-004 — Qualificatifs évaluatifs

**Exigence**

Tout qualificatif évaluatif, notamment « pertinent », « suffisant » ou
« représentatif », NE PEUT produire d’effet normatif que s’il renvoie à un
critère explicite défini par une Scientific Question, une règle
d’interprétation, une clause du contrat ou un protocole de validation.

**Critères de conformité**

- chaque qualificatif ayant un effet sur un verdict cite son critère ;
- le critère permet à deux auditeurs d’évaluer le qualificatif de la même
  manière sur les mêmes preuves.

**Critères de non-conformité**

- un qualificatif modifie un verdict sans critère identifiable ;
- son appréciation dépend uniquement du jugement implicite de l’auditeur.

**Preuves d’audit attendues**

- correspondance entre qualificatifs évaluatifs et critères déclarés ;
- cas limites évalués selon les mêmes critères.

### SC-AUT-005 — Séparation de la définition, de l’interprétation et de la validation

**Exigence**

Une clause normative DOIT définir une exigence et sa frontière de conformité.
Elle NE DOIT PAS définir la méthode scientifique permettant de satisfaire
l’exigence ni le protocole permettant d’en démontrer la conformité. Les règles
d’interprétation et protocoles de validation DOIVENT rester identifiables,
versionnés et subordonnés au contrat.

**Critères de conformité**

- l’exigence reste indépendante d’une méthode ou d’un protocole particulier ;
- les méthodes d’interprétation et protocoles de validation sont distingués de
  la clause qu’ils servent ;
- une évolution de protocole compatible ne requiert pas de redéfinir
  l’exigence.

**Critères de non-conformité**

- une clause impose une méthode opérationnelle comme unique moyen de
  conformité sans que cette méthode constitue elle-même l’exigence ;
- un protocole de validation est présenté comme définition de l’exigence ;
- une règle subordonnée modifie la frontière de conformité du contrat.

**Preuves d’audit attendues**

- correspondance entre clauses, règles d’interprétation et protocoles ;
- historique versionné démontrant leur évolution séparée.

### SC-TRU-001 — Modèle de vérité bornée

**Exigence**

AcousticBrain ne produit pas des vérités absolues. Il produit des affirmations
déterministes dont la portée est limitée par les preuves disponibles, les
hypothèses considérées et le domaine de validité déclaré.

**Critères de conformité**

- chaque affirmation expose sa portée et son domaine de validité ;
- les hypothèses considérées et les preuves disponibles sont identifiables.

**Critères de non-conformité**

- une affirmation est présentée comme universelle sans justification ;
- sa portée ne peut pas être reliée aux preuves ou hypothèses examinées.

**Preuves d’audit attendues**

- représentations auditables d’affirmations ;
- traces reliant portée, hypothèses et preuves.

### SC-TRU-002 — Séparation des vérités interne et externe

**Exigence**

La certitude interne d’un calcul ne se transfère jamais automatiquement à la
certitude externe de son interprétation physique. Toute affirmation externe
DOIT disposer d’une chaîne probante explicite reliant les mesures au phénomène
désigné.

**Critères de conformité**

- les résultats de calcul et leurs interprétations physiques sont distingués ;
- l’interprétation externe cite la chaîne probante correspondante.

**Critères de non-conformité**

- un résultat déterministe est assimilé sans preuve à une cause physique ;
- la certitude externe est déduite uniquement de la reproductibilité du calcul.

**Preuves d’audit attendues**

- traces mesure–fait–preuve–hypothèse–conclusion scientifique ;
- cas d’essai où un calcul certain conduit à une conclusion scientifique
  externe
  `INDÉTERMINÉ`.

### SC-TRU-003 — Statut des données supposées

**Exigence**

Toute donnée supposée DOIT être explicitement distinguée d’une donnée mesurée.
Une supposition NE DOIT PAS être transformée silencieusement en fait.

**Critères de conformité**

- l’origine mesurée ou supposée de toute donnée est déclarée ;
- les conclusions scientifiques dépendantes d’une supposition exposent cette
  dépendance.

**Critères de non-conformité**

- une valeur supposée est étiquetée comme mesure ;
- la suppression d’une supposition ne déclenche aucune révision des résultats
  qui en dépendent.

**Preuves d’audit attendues**

- inventaire de provenance des données ;
- traces de dépendance et de révision.

### SC-AST-001 — Contrat d’une affirmation scientifique

**Exigence**

Toute affirmation scientifique DOIT déclarer au minimum : son contenu, son type
épistémique, sa provenance, sa portée, son niveau de preuve, son domaine de
validité, ses hypothèses sous-jacentes, ses conditions de révision, ses
conditions de réfutation, sa portée maximale autorisée et son statut.

**Critères de conformité**

- tous les attributs obligatoires sont présents et auditables ;
- le statut appartient à un vocabulaire déclaré ;
- le contenu respecte la portée maximale autorisée.

**Critères de non-conformité**

- un attribut obligatoire est absent ou implicite ;
- le contenu dépasse la portée maximale ;
- le statut masque une incertitude ou une contradiction.

**Preuves d’audit attendues**

- ensemble d’affirmations défini par un critère d’échantillonnage déclaré ;
- validation de complétude et de cohérence des attributs.

### SC-AST-002 — Types épistémiques disjoints

**Exigence**

Les types mesure, fait, hypothèse, preuve, diagnostic, conclusion scientifique,
décision et acquisition de preuve DOIVENT rester explicitement distingués. Une
transformation de type DOIT être déclarée et justifiée.

**Critères de conformité**

- chaque objet de connaissance porte un type explicite ;
- chaque changement de type correspond à une transformation traçable.

**Critères de non-conformité**

- une hypothèse est présentée comme un fait ;
- un diagnostic est utilisé directement comme décision ou conclusion
  scientifique ferme ;
- un changement de type est implicite.

**Preuves d’audit attendues**

- représentation auditable des connaissances et de leurs types ;
- trace versionnée des transformations de type.

### SC-EVD-001 — Preuve orientée

**Exigence**

Toute preuve DOIT posséder un fait source, une hypothèse cible, une direction,
une force, une règle d’interprétation, une provenance et un domaine de
validité. Une preuve NE DOIT PAS exister sans hypothèse cible.

**Critères de conformité**

- tous les attributs obligatoires sont présents ;
- la direction indique l’effet du fait sur l’hypothèse cible ;
- la règle d’interprétation est identifiable.

**Critères de non-conformité**

- une donnée est qualifiée de preuve sans hypothèse cible ;
- la direction ou la règle d’interprétation est implicite ;
- le domaine de validité est absent.

**Preuves d’audit attendues**

- ensemble auditable des preuves orientées ;
- traces vers les faits, hypothèses et règles sources.

### SC-EVD-002 — Ordre et limitation de la force probante

**Exigence**

Toute preuve et toute conclusion scientifique DOIT déclarer exactement un
niveau de force probante appartenant à l’ordre total
`NON DÉMONTRÉ < INSUFFISANT < FAIBLE < MODÉRÉ < FORT`.

Toute conclusion scientifique DOIT posséder une force inférieure ou égale à
la force minimale des preuves nécessaires qui la soutiennent. L’ensemble des
preuves nécessaires DOIT être déclaré par le critère applicable. Toute preuve
contradictoire ou insuffisante pertinente au regard d’un critère explicite
DOIT rester visible dans l’état de connaissance.

**Critères de conformité**

- la justification d’une conclusion scientifique expose l’ensemble déclaré
  des preuves nécessaires ainsi que les preuves favorables et
  défavorables ;
- chaque force appartient au vocabulaire ordonné ;
- la force déclarée de la conclusion scientifique est inférieure ou égale au
  minimum des forces de ses preuves nécessaires.

**Critères de non-conformité**

- une preuve de force inférieure autorise une conclusion scientifique de
  force supérieure ;
- une contradiction pertinente est supprimée ou neutralisée sans règle ;
- le volume de données est assimilé à leur force probante.

**Preuves d’audit attendues**

- cas contradictoires et insuffisants ;
- ensemble déclaré des preuves nécessaires et calcul ordinal de leur minimum ;
- justification de la force de chaque conclusion scientifique auditée.

### SC-EVD-003 — Acquisition de preuve

**Exigence**

Toute acquisition de preuve DOIT viser une incertitude explicite ou une
compétition d’hypothèses déclarée. Elle DOIT préciser les faits recherchés, les
conditions d’acquisition et l’effet attendu de chaque résultat possible sur les
hypothèses. Elle NE DOIT PAS présupposer le résultat recherché.

**Critères de conformité**

- l’incertitude ou les hypothèses concurrentes sont identifiées ;
- chaque résultat attendu possède une interprétation probante déclarée ;
- un résultat nul, contradictoire ou inexploitable peut être conservé.

**Critères de non-conformité**

- l’acquisition ne vise aucune lacune de connaissance explicite ;
- seul le résultat favorable à une hypothèse est interprété ;
- le protocole transforme une absence de détection en preuve d’absence.

**Preuves d’audit attendues**

- contrat de l’acquisition et conditions de refus ;
- matrice résultats possibles–effets sur les hypothèses ;
- traces reliant l’acquisition à l’incertitude source.

### SC-CAP-001 — Définition d’une capacité scientifique

**Exigence**

Une capacité scientifique est une transformation déterministe, traçable et
révisable de l’état de connaissance du moteur, fondée sur des preuves
explicitement définies, soumise à des conditions de validité et de refus, et
orientée vers une décision utilisateur.

Toute capacité scientifique DOIT déclarer ses entrées épistémiques, sa
transformation autorisée, ses sorties, ses conditions de validité, ses
conditions de refus, sa portée maximale et ses règles de révision.

**Critères de conformité**

- chaque propriété obligatoire est explicite ;
- une même entrée produit le même état de connaissance ;
- toute sortie est traçable et révisable.

**Critères de non-conformité**

- une capacité est définie uniquement par un algorithme ;
- ses conditions de refus ou sa portée maximale sont absentes ;
- elle produit une connaissance sans provenance.

**Preuves d’audit attendues**

- contrat normatif de la capacité ;
- jeux de cas valides, invalides, contradictoires et insuffisants.

### SC-CAP-002 — Droits du moteur

**Exigence**

Dans le respect de sa portée, le moteur PEUT établir un fait, maintenir
plusieurs hypothèses concurrentes, produire un diagnostic, demander une preuve,
réviser ou retirer une affirmation et refuser de conclure.

Il NE DOIT exercer aucun de ces droits hors des conditions déclarées par la
transformation concernée.

**Critères de conformité**

- chaque exercice d’un droit cite sa condition d’autorisation ;
- plusieurs hypothèses compatibles peuvent rester simultanément ouvertes.

**Critères de non-conformité**

- une hypothèse est éliminée sans preuve défavorable ou règle de retrait ;
- une conclusion scientifique est forcée lorsque les conditions de refus sont
  réunies.

**Preuves d’audit attendues**

- traces d’autorisation ;
- cas conservant plusieurs hypothèses et cas de refus.

### SC-CAP-003 — Devoirs et interdictions du moteur

**Exigence**

Le moteur DOIT tracer toute affirmation, expliciter ses hypothèses, préserver
les contradictions, distinguer mesure et supposition, respecter la portée
maximale et déclarer les informations manquantes.

Le moteur NE DOIT PAS :

- transformer une compatibilité en causalité ;
- utiliser l’absence de détection comme preuve d’absence ;
- masquer une donnée supposée ;
- dépasser la portée maximale d’une capacité ;
- présenter une hypothèse non examinée comme réfutée ;
- augmenter la force d’une conclusion scientifique par un texte, un score, une
  confiance ou une étiquette.

**Critères de conformité**

- toutes les obligations sont observables dans les sorties et traces ;
- les cas interdits sont explicitement rejetés ou bornés.

**Critères de non-conformité**

- une obligation manque pour une affirmation produite ;
- l’un des comportements interdits est observé.

**Preuves d’audit attendues**

- tests de chaque interdiction ;
- traces complètes d’affirmations et de refus.

### SC-SCP-001 — Portée maximale d’une transformation

**Exigence**

Toute transformation possède une portée maximale d’affirmation qu’elle NE DOIT
PAS dépasser, indépendamment du texte, du score, du niveau de confiance ou de
l’étiquette produits par son implémentation.

**Critères de conformité**

- la portée maximale est déclarée avant l’évaluation de la transformation ;
- chaque sortie est incluse dans cette portée.

**Critères de non-conformité**

- la portée est absente, reconstruite après coup ou dépassée ;
- une présentation renforce la sortie au-delà de la portée autorisée.

**Preuves d’audit attendues**

- déclaration versionnée de portée ;
- tests aux limites et contre-exemples interdits.

### SC-SCP-002 — Composition des portées

**Exigence**

Une chaîne de transformations NE DOIT PAS produire une conclusion scientifique
plus forte que la portée permise par son maillon probant le plus limitant.

**Critères de conformité**

- la portée de chaque maillon est traçable ;
- la conclusion scientifique composée respecte la borne la plus restrictive.

**Critères de non-conformité**

- la composition augmente la portée sans preuve nouvelle ;
- une étape de présentation ou de décision contourne une limite amont.

**Preuves d’audit attendues**

- chaînes de transformations annotées par portée ;
- tests de propagation des limites.

### SC-REF-001 — Refus de conclure

**Exigence**

Le refus de conclure est un résultat scientifique valide et attendu. Le moteur
DOIT refuser de conclure lorsque les preuves, hypothèses examinées ou domaines
de validité ne permettent pas une conclusion scientifique dans la portée
demandée.

**Critères de conformité**

- le refus indique ses causes, informations manquantes et conditions de
  révision ;
- aucun résultat plus fort n’est rendu parallèlement.

**Critères de non-conformité**

- une conclusion scientifique est produite malgré une condition de refus ;
- le refus est traité comme une erreur logicielle ou remplacé par une
  supposition.

**Preuves d’audit attendues**

- cas insuffisants, hors domaine et contradictoires ;
- résultats de refus explicitement décomposés et traçables.

### SC-REV-001 — Révision

**Exigence**

Toute conclusion scientifique DOIT indiquer les observations susceptibles de
la réviser.
Lorsqu’une de ces conditions survient, les connaissances dépendantes DOIVENT
être réévaluées sans réécriture silencieuse de leur historique.

**Critères de conformité**

- les conditions de révision sont explicites ;
- l’état antérieur, la nouvelle preuve et l’état révisé restent traçables.

**Critères de non-conformité**

- une conclusion scientifique est déclarée irrévisable ;
- une mise à jour efface la provenance ou l’état antérieur.

**Preuves d’audit attendues**

- historique versionné des révisions ;
- cas d’arrivée d’une preuve nouvelle ou contradictoire.

### SC-REV-002 — Réfutation et retrait

**Exigence**

Une hypothèse ne PEUT être réfutée que par une preuve défavorable suffisante,
appliquée selon une règle déclarée dans son domaine de validité. Une affirmation
ne PEUT être retirée que par une règle explicite conservant la cause et la
provenance du retrait.

**Critères de conformité**

- réfutation et retrait sont distingués ;
- chaque événement cite sa règle et ses preuves.

**Critères de non-conformité**

- absence de support, absence de détection ou hypothèse alternative est
  assimilée à une réfutation ;
- une affirmation disparaît sans trace de retrait.

**Preuves d’audit attendues**

- dossiers de réfutation ;
- historique versionné des retraits et trace des dépendances affectées.

### SC-DEC-001 — Séparation diagnostic, conclusion scientifique et décision

**Exigence**

Diagnostic, conclusion scientifique et décision DOIVENT rester trois objets
épistémiques distincts. Leur fusion est interdite. Un diagnostic PEUT exister
sans conclusion scientifique ferme ; une conclusion scientifique PEUT exister
sans autoriser une décision.

**Critères de conformité**

- chaque objet porte un type et une provenance distincts ;
- les transformations entre les trois sont explicites.

**Critères de non-conformité**

- un diagnostic est présenté comme causalité établie ;
- une recommandation est produite sans état de connaissance qui l’autorise.

**Preuves d’audit attendues**

- traces séparées des trois objets ;
- cas où une ou deux étapes seulement sont autorisées.

### SC-DEC-002 — Autorisation d’une décision

**Exigence**

Toute décision DOIT déclarer la conclusion scientifique ou l’état de
connaissance qui l’autorise, ses conditions d’applicabilité, ses facteurs de
blocage et ses conditions de retrait. Une décision bloquée NE DOIT PAS être
présentée comme applicable.

**Critères de conformité**

- l’autorité scientifique et les blocages sont explicites ;
- la décision est retirée ou révisée si son autorité cesse d’être valide.

**Critères de non-conformité**

- une décision ne possède pas de provenance scientifique ;
- un blocage est omis ou contourné.

**Preuves d’audit attendues**

- traces conclusion scientifique–décision ;
- cas applicables, bloqués et retirés.

### SC-SQ-001 — Gouvernance descendante

**Exigence**

Toute capacité scientifique DOIT être gouvernée par la chaîne descendante
suivante :

```text
Besoin utilisateur
↓
Question utilisateur
↓
Scientific Question
↓
Décision attendue
↓
Hypothèses concurrentes
↓
Preuves nécessaires
↓
Transformations de connaissance
↓
Capacités
↓
Implémentation
↓
Validation
```

Les Scientific Questions NE DOIVENT PAS être dérivées rétroactivement d’un
inventaire de capacités.

**Critères de conformité**

- chaque capacité remonte à une Scientific Question et une décision attendue ;
- les hypothèses et preuves nécessaires précèdent la définition de la capacité.

**Critères de non-conformité**

- une capacité sans besoin ou question gouvernante est déclarée scientifique ;
- une Scientific Question est reconstruite depuis l’implémentation.

**Preuves d’audit attendues**

- chaîne de gouvernance versionnée ;
- historique de définition des questions, preuves et capacités.

### SC-VAL-001 — Validation logicielle

**Exigence**

La validation logicielle DOIT évaluer la conformité de l’implémentation à ses
spécifications, notamment son déterminisme, ses invariants, ses refus et sa
traçabilité. Elle NE DOIT PAS être présentée comme validation d’une affirmation
physique.

**Critères de conformité**

- les propriétés logicielles évaluées sont explicites ;
- les résultats sont qualifiés exclusivement comme preuves logicielles.

**Critères de non-conformité**

- des tests logiciels sont utilisés comme preuve scientifique suffisante ;
- les conditions de refus ou invariants normatifs ne sont pas testés.

**Preuves d’audit attendues**

- protocole et résultats de tests logiciels ;
- couverture des invariants et interdictions.

### SC-VAL-002 — Validation scientifique

**Exigence**

La validation scientifique DOIT évaluer les affirmations externes dans un
domaine déclaré au moyen de références, données ou interprétations
indépendantes appropriées. Son statut DOIT rester indépendant de la validation
logicielle.

**Critères de conformité**

- le domaine, les références et critères d’acceptation sont déclarés ;
- les résultats négatifs, contradictoires et hors domaine sont conservés.

**Critères de non-conformité**

- la validation ne repose que sur les données ayant servi à définir la règle ;
- l’indépendance ou le domaine de validation n’est pas démontré ;
- un succès logiciel augmente le statut scientifique.

**Preuves d’audit attendues**

- protocole de validation scientifique ;
- corpus de référence et résultats reproductibles ;
- interprétation indépendante et limites constatées.

### SC-TRC-001 — Traçabilité scientifique

**Exigence**

Toute affirmation, conclusion scientifique et décision DOIT être traçable
jusqu’aux mesures sources par des transformations et preuves explicitement
identifiées. La trace DOIT préserver hypothèses, contradictions, domaines de
validité, révisions et retraits.

**Critères de conformité**

- la chaîne complète peut être parcourue dans les deux sens ;
- aucune étape ne dépend d’un texte non structuré comme unique provenance.

**Critères de non-conformité**

- une mesure, règle ou hypothèse source est introuvable ;
- une contradiction ou révision disparaît de la trace.

**Preuves d’audit attendues**

- traces de provenance complètes ;
- audits d’échantillons depuis décision vers mesures et inversement.

### SC-CON-001 — Conformité documentaire

**Exigence**

Tout document scientifique subordonné DOIT déclarer sa subordination au présent
contrat, identifier les clauses qu’il précise et NE DOIT PAS revendiquer une
conformité non auditée.

**Critères de conformité**

- la déclaration de subordination est explicite ;
- les conflits, limites et statuts `NON DÉMONTRÉ` sont visibles.

**Critères de non-conformité**

- le document se présente comme autorité scientifique concurrente ;
- il masque une information non documentée ou une conformité non démontrée.

**Preuves d’audit attendues**

- en-têtes de subordination ;
- revue de conformité documentaire versionnée.

## Invariants scientifiques consolidés

Les clauses précédentes imposent au minimum les invariants suivants.

### Nature des connaissances

- aucune hypothèse n’est un fait ;
- aucune compatibilité n’est une causalité ;
- toute donnée supposée est distinguée d’une donnée mesurée ;
- l’absence de détection ne constitue pas une preuve d’absence.

### Preuve et conclusion scientifique

- toute preuve possède une hypothèse cible et une direction ;
- la force d’une conclusion scientifique ne peut dépasser la force minimale
  de ses preuves nécessaires ;
- toute hypothèse concurrente pertinente non examinée est signalée ;
- un diagnostic peut exister sans conclusion scientifique ferme ;
- une affirmation externe ne peut être plus forte que les preuves reliant les
  mesures au phénomène ;
- la certitude interne ne devient jamais automatiquement une certitude externe.

### Traçabilité et révision

- toute conclusion scientifique est traçable jusqu’aux mesures sources ;
- toute conclusion scientifique indique les observations susceptibles de la
  réviser ;
- le refus de conclure est un résultat scientifique valide.

### Acquisition et validation

- toute acquisition vise une incertitude explicite ou une compétition
  d’hypothèses ;
- la maturité d’une capacité ne détermine pas la force d’une preuve dans un cas
  particulier ;
- validation logicielle et validation scientifique restent indépendantes.

## Statuts de conformité

- **CONFORME** : tous les critères obligatoires applicables sont démontrés
  conformes et aucun n’est non conforme.
- **PARTIELLEMENT CONFORME** : au moins un critère obligatoire applicable est
  démontré conforme, au moins un autre reste non démontré et aucun n’est non
  conforme.
- **NON CONFORME** : au moins une obligation applicable est violée ou une
  interdiction applicable est enfreinte, quels que soient les autres critères.
- **NON DÉMONTRÉ** : aucun critère obligatoire applicable ne peut être évalué
  faute de preuves d’audit suffisantes.

L’absence de preuve NE DOIT PAS être confondue avec une preuve de
non-conformité, sauf lorsqu’une clause impose explicitement que cette preuve
soit disponible.
