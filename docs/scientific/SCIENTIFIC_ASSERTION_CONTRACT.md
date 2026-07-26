# Contrat transversal des affirmations scientifiques

## Autorité et subordination

Le présent document est un document scientifique **normatif**. Il est
subordonné à `SCIENTIFIC_CONTRACT.md`, qui prévaut en cas de conflit ou
d’ambiguïté.

Il précise les clauses `SC-TRU-001`, `SC-TRU-002`, `SC-TRU-003`,
`SC-AST-001`, `SC-AST-002`, `SC-EVD-001`, `SC-EVD-002`, `SC-EVD-003`,
`SC-SCP-001`, `SC-SCP-002`, `SC-REF-001`, `SC-REV-001`, `SC-REV-002` et
`SC-TRC-001`.

Il normalise l’expression de toute affirmation scientifique produite,
maintenue, révisée, réfutée ou retirée par une transformation de connaissance.
Ses exigences s’appliquent indépendamment de la capacité productrice et de
toute représentation technique.

## Exclusions

Le présent document :

- ne crée, ne décrit et n’autorise aucune capacité scientifique ;
- ne crée, ne reconstruit et ne valide aucune Scientific Question ;
- ne modifie aucun type ni aucune relation du modèle normatif des
  connaissances ;
- ne définit aucune méthode scientifique, aucun algorithme, aucun calcul ni
  aucun protocole de validation ;
- n’impose aucune classe, interface, API, sérialisation, persistance,
  architecture ou stratégie de migration ;
- ne dépend normativement d’aucun registre descriptif ni d’aucun rapport
  d’audit ;
- ne définit pas les graphes normatif et documentaire.

Une citation descriptive d’un registre ou d’un audit NE PEUT ni modifier une
exigence du présent contrat ni lui transférer une autorité normative.

## Nature de l’affirmation scientifique

Une affirmation scientifique est l’expression transversale d’un contenu
épistémique produit ou maintenu par une transformation de connaissance. Elle
rend auditables la nature, la provenance, la portée, les limites et le statut
de ce contenu.

L’affirmation scientifique n’est pas un nouveau type de connaissance. Elle
exprime exactement un type épistémique défini par `KNOWLEDGE_MODEL.md`.

Elle ne rend pas un contenu vrai par sa seule présence ni conforme par la seule
complétude de ses attributs. Sa validité scientifique reste bornée par ses
preuves, son domaine de validité, ses hypothèses et les validations
applicables.

## Attributs conceptuels obligatoires

Toute affirmation scientifique DOIT exprimer les attributs conceptuels
suivants :

1. **type épistémique** : nature de la connaissance exprimée ;
2. **contenu** : proposition exacte portée par l’affirmation ;
3. **provenance** : sources et transformations qui autorisent le contenu ;
4. **portée** : objets, conditions, phénomènes et usages auxquels le contenu
   s’applique ;
5. **domaine de validité** : conditions dans lesquelles les règles ayant
   produit ou interprété le contenu sont valides ;
6. **force probante** : niveau ordinal autorisé par les preuves applicables ;
7. **hypothèses sous-jacentes** : suppositions et hypothèses nécessaires à la
   validité du contenu ;
8. **limitations** : restrictions connues de l’interprétation ou de l’usage ;
9. **contradictions** : connaissances incompatibles pertinentes selon un
   critère explicite ;
10. **conditions de révision** : observations ou changements exigeant une
    réévaluation ;
11. **conditions de réfutation** : conditions dans lesquelles une hypothèse
    exprimée peut être réfutée, ou justification explicite de leur
    inapplicabilité au type exprimé ;
12. **conditions de retrait** : conditions mettant fin à l’usage actif de
    l’affirmation sans réécriture de son historique ;
13. **portée maximale autorisée** : limite supérieure que le contenu NE DOIT
    PAS dépasser ;
14. **statut** : état actuel appartenant à un vocabulaire normatif déclaré.

Un attribut obligatoire NE DOIT PAS être omis parce qu’aucune valeur positive
n’est disponible. Une absence, une inapplicabilité ou un état indéterminé
DOIT être déclaré et justifié selon les règles applicables.

## Clauses normatives

### SA-AUT-001 — Autorité et indépendance du contrat

**Exigence**

Le présent contrat DOIT rester subordonné à `SCIENTIFIC_CONTRACT.md` et
indépendant de toute capacité, Scientific Question, méthode, protocole,
représentation technique, registre descriptif ou rapport d’audit.

Une source descriptive ou d’audit NE DOIT PAS modifier ses exigences ni être
utilisée comme fondement de son autorité normative.

**Critères de conformité**

- la subordination au contrat scientifique est explicite ;
- les clauses précisées sont identifiées ;
- aucune exigence ne dépend de l’état contingent du moteur ;
- aucune représentation particulière n’est nécessaire à la conformité.

**Critères de non-conformité**

- une capacité ou une Scientific Question est créée par le présent document ;
- une exigence algorithmique ou une représentation particulière est imposée ;
- un registre ou un audit modifie la définition d’une affirmation conforme ;
- un conflit est résolu contre le contrat scientifique.

**Preuves d’audit attendues**

- correspondance entre les exigences du présent document et les clauses
  précisées ;
- revue des dépendances normatives ;
- vérification sur plusieurs représentations conceptuellement équivalentes.

### SA-ATR-001 — Complétude des attributs conceptuels

**Exigence**

Toute affirmation scientifique DOIT exprimer les quatorze attributs
conceptuels obligatoires définis par le présent contrat. Aucun attribut NE DOIT
être reconstruit implicitement depuis un autre.

Une absence, une inapplicabilité ou un état indéterminé DOIT être déclaré et
justifié selon les règles applicables.

**Critères de conformité**

- chacun des quatorze attributs est explicitement évaluable ;
- les attributs conservent des significations distinctes ;
- toute absence ou inapplicabilité est déclarée et justifiée ;
- aucune information de présentation n’est nécessaire pour compléter le
  contrat.

**Critères de non-conformité**

- un attribut obligatoire est absent ou implicite ;
- portée, domaine, force, confiance ou statut sont confondus ;
- une valeur manquante est inventée ;
- une inapplicabilité est déclarée sans justification.

**Preuves d’audit attendues**

- matrice des quatorze attributs pour chaque affirmation auditée ;
- justification des absences, inapplicabilités et états indéterminés ;
- cas démontrant l’indépendance sémantique des attributs.

### SA-NAT-001 — Unicité du contenu et du type épistémique

**Exigence**

Toute affirmation scientifique DOIT exprimer un contenu déterminé et
exactement un type épistémique parmi mesure, fait, hypothèse, preuve,
diagnostic, conclusion scientifique, décision et acquisition de preuve.

Une affirmation NE DOIT PAS changer implicitement de type. Toute
transformation produisant un type différent DOIT produire un nouvel état
traçable et justifier le changement.

**Critères de conformité**

- le contenu peut être évalué sans reconstruire une proposition implicite ;
- un unique type est déclaré ;
- le contenu respecte la définition et les limites de ce type ;
- tout changement de type est relié à sa transformation autorisante.

**Critères de non-conformité**

- plusieurs types sont simultanément attribués au même contenu ;
- une hypothèse est exprimée comme fait ;
- un diagnostic devient implicitement conclusion scientifique ou décision ;
- le type doit être inféré depuis le texte de présentation.

**Preuves d’audit attendues**

- représentation auditable du contenu et du type ;
- trace des transformations ayant produit ou changé le type ;
- cas limites entre fait, hypothèse, diagnostic, conclusion scientifique et
  décision.

### SA-PRV-001 — Provenance complète et bornée

**Exigence**

Toute affirmation scientifique DOIT déclarer ses sources directes, les
transformations appliquées, les règles autorisantes et les états antérieurs
dont elle dépend.

La provenance DOIT rester parcourable jusqu’aux mesures sources pour toute
affirmation qui en dérive. Une supposition, une déclaration ou une source
externe DOIT rester identifiable comme telle et NE DOIT PAS être transformée
silencieusement en mesure.

**Critères de conformité**

- chaque dépendance directe et chaque règle appliquée est identifiable ;
- les mesures, suppositions, déclarations et sources externes restent
  distinguées ;
- une révision ou un retrait conserve la provenance antérieure ;
- aucune présentation ne constitue l’unique provenance.

**Critères de non-conformité**

- une source ou une transformation nécessaire est introuvable ;
- une supposition est présentée comme mesure ;
- une révision efface une source antérieure ;
- le contenu ne peut être relié qu’à un texte de restitution.

**Preuves d’audit attendues**

- trace de provenance parcourable dans les deux sens ;
- historique versionné des états dépendants ;
- cas contenant des mesures, suppositions et déclarations explicitement
  distinguées.

### SA-SCP-001 — Portée, domaine de validité et portée maximale

**Exigence**

Toute affirmation scientifique DOIT distinguer sa portée, son domaine de
validité et sa portée maximale autorisée.

Le contenu DOIT rester inclus dans la portée maximale autorisée et NE DOIT PAS
être appliqué hors de son domaine de validité. Une composition
d’affirmations NE DOIT PAS dépasser la limite la plus restrictive de ses
maillons nécessaires.

**Critères de conformité**

- les objets, conditions, phénomènes et usages couverts sont explicites ;
- les conditions de validité des règles appliquées sont identifiables ;
- la portée maximale est déclarée indépendamment du contenu produit ;
- la composition conserve la limite la plus restrictive.

**Critères de non-conformité**

- portée et domaine de validité sont confondus ou implicites ;
- le contenu est universalisé au-delà des conditions déclarées ;
- la portée maximale est reconstruite après production du contenu ;
- une composition augmente la portée sans connaissance nouvelle autorisée.

**Preuves d’audit attendues**

- correspondance entre contenu, portée, domaine et portée maximale ;
- cas dans le domaine, hors domaine et aux limites ;
- traces de propagation des limites dans les compositions.

### SA-EVD-001 — Force probante de l’affirmation

**Exigence**

Toute affirmation scientifique DOIT déclarer une force probante appartenant à
l’ordre total :

`NON DÉMONTRÉ < INSUFFISANT < FAIBLE < MODÉRÉ < FORT`.

La force d’une conclusion scientifique DOIT être inférieure ou égale à la
force minimale des preuves nécessaires qui la soutiennent. Les preuves
nécessaires et le critère qui les détermine DOIVENT être déclarés.

Un score, une confiance, une répétition, un volume de données ou une qualité
de présentation NE DOIT PAS augmenter la force probante sans règle probante
déclarée.

**Critères de conformité**

- la force appartient au vocabulaire normatif ;
- son critère d’attribution est identifiable ;
- les preuves nécessaires d’une conclusion scientifique sont déclarées ;
- la borne minimale est respectée ;
- confiance, score et force restent distincts lorsqu’ils coexistent.

**Critères de non-conformité**

- la force est absente, implicite ou exprimée par un vocabulaire concurrent ;
- une conclusion scientifique dépasse sa preuve nécessaire la plus faible ;
- le volume ou la répétition remplace l’évaluation probante ;
- une confiance numérique est assimilée à une force probante.

**Preuves d’audit attendues**

- preuves nécessaires, forces individuelles et minimum ordinal ;
- règle d’attribution de chaque niveau ;
- cas où une confiance élevée ne relève pas une force limitée ;
- cas contradictoires et insuffisants.

### SA-HYP-001 — Hypothèses sous-jacentes

**Exigence**

Toute affirmation scientifique DOIT déclarer les hypothèses et suppositions
nécessaires à son contenu. Lorsqu’aucune hypothèse sous-jacente n’est requise,
cette absence DOIT être explicite.

Une hypothèse concurrente pertinente au regard d’un critère explicite et non
examinée DOIT être signalée. Son absence d’examen NE DOIT PAS être assimilée à
une réfutation.

**Critères de conformité**

- les dépendances à des hypothèses ou suppositions sont visibles ;
- les hypothèses concurrentes applicables sont identifiées ou leur
  non-examen est déclaré ;
- la suppression d’une hypothèse déclenche la réévaluation des affirmations
  dépendantes.

**Critères de non-conformité**

- une hypothèse nécessaire reste implicite ;
- une supposition est masquée comme fait ;
- une hypothèse concurrente non examinée est déclarée réfutée ;
- une dépendance supprimée ne provoque aucune réévaluation.

**Preuves d’audit attendues**

- trace des hypothèses et suppositions sous-jacentes ;
- critères identifiant les hypothèses concurrentes ;
- cas de suppression ou de modification d’une hypothèse.

### SA-LIM-001 — Limitations et contradictions

**Exigence**

Toute affirmation scientifique DOIT déclarer ses limitations connues et les
contradictions pertinentes au regard d’un critère explicite. L’absence
constatée de limitation ou de contradiction DOIT résulter d’un périmètre et
d’un critère déclarés.

Une contradiction NE DOIT PAS être résolue par suppression, préférence
implicite, ordre d’arrivée ou augmentation artificielle de la force d’une
source.

**Critères de conformité**

- limitations et contradictions sont distinguées ;
- les connaissances contradictoires et leurs provenances sont conservées ;
- l’effet de chaque contradiction sur le statut, la force et la portée est
  explicite ;
- une absence déclarée est bornée par le périmètre examiné.

**Critères de non-conformité**

- une limitation ou contradiction applicable est omise ;
- une contradiction disparaît sans règle de révision, réfutation ou retrait ;
- une source est préférée sans critère ;
- l’absence de contradiction est présentée comme absolue sans périmètre.

**Preuves d’audit attendues**

- ensemble des limitations et contradictions examinées ;
- critères de pertinence et périmètre de recherche ;
- historique des effets et résolutions autorisées.

### SA-REV-001 — Révision

**Exigence**

Toute affirmation scientifique DOIT déclarer les observations, changements de
source, de règle, d’hypothèse ou de domaine susceptibles de provoquer sa
révision.

Une révision DOIT produire un nouvel état, conserver l’état antérieur,
identifier son déclencheur et propager la réévaluation aux connaissances
dépendantes. Elle NE DOIT PAS réécrire silencieusement l’historique.

**Critères de conformité**

- les conditions de révision sont testables et identifiables ;
- le déclencheur, l’état antérieur et l’état révisé sont conservés ;
- les dépendances affectées sont réévaluées ;
- une condition satisfaite ne laisse pas l’ancien état actif sans
  justification.

**Critères de non-conformité**

- l’affirmation est déclarée irrévisable sans autorité normative ;
- une condition de révision reste implicite ;
- l’ancien état ou le déclencheur disparaît ;
- les dépendances ne sont pas réévaluées.

**Preuves d’audit attendues**

- conditions de révision déclarées ;
- historique versionné des états ;
- traces de propagation vers les dépendances.

### SA-REV-002 — Réfutation

**Exigence**

Lorsqu’une affirmation exprime une hypothèse, elle DOIT déclarer ses conditions
de réfutation. Une réfutation exige une preuve défavorable suffisante, une
règle déclarée et un domaine de validité applicable.

Pour un type auquel la réfutation ne s’applique pas, l’inapplicabilité et sa
justification DOIVENT être explicites. L’absence de support, l’absence de
détection et l’existence d’une hypothèse concurrente NE SUFFISENT PAS à
réfuter.

**Critères de conformité**

- toute hypothèse possède une règle et des conditions de réfutation ;
- la preuve défavorable, sa force et son domaine sont identifiables ;
- l’inapplicabilité à un autre type est justifiée ;
- l’hypothèse réfutée et ses dépendances restent auditables.

**Critères de non-conformité**

- une hypothèse est irréfutable par construction ;
- une absence de preuve ou de détection est assimilée à une réfutation ;
- la règle ou le domaine de réfutation est absent ;
- l’hypothèse réfutée disparaît de l’historique.

**Preuves d’audit attendues**

- règles et cas de réfutation ;
- preuves défavorables et domaines applicables ;
- cas d’absence de support ou de détection ne produisant pas de réfutation.

### SA-REV-003 — Retrait

**Exigence**

Toute affirmation scientifique DOIT déclarer les conditions permettant de
mettre fin à son usage actif. Un retrait DOIT conserver le contenu, la cause,
la règle, la provenance, l’état antérieur et les conséquences sur les
connaissances dépendantes.

Le retrait NE DOIT PAS être assimilé à une réfutation ni utilisé pour effacer
une contradiction.

**Critères de conformité**

- les conditions et la règle de retrait sont explicites ;
- une affirmation retirée n’autorise plus de nouvel usage scientifique ;
- son historique et ses dépendances restent auditables ;
- retrait, révision et réfutation conservent des significations distinctes.

**Critères de non-conformité**

- une affirmation disparaît sans trace ;
- une affirmation retirée continue d’autoriser une conclusion scientifique ou
  une décision ;
- le retrait est présenté comme preuve de fausseté ;
- une contradiction est supprimée par retrait implicite.

**Preuves d’audit attendues**

- conditions et événements de retrait ;
- historique versionné de l’affirmation ;
- trace des usages interdits et des dépendances affectées.

### SA-STA-001 — Statut explicite et cohérent

**Exigence**

Toute affirmation scientifique DOIT posséder exactement un statut actuel,
appartenant à un vocabulaire normatif déclaré et compatible avec son type, sa
force, ses contradictions, ses limitations et son état de révision,
réfutation ou retrait.

Le statut NE DOIT PAS masquer une incertitude, une contradiction, une
inapplicabilité ou un refus de conclure.

**Critères de conformité**

- un unique statut actuel est déclaré ;
- sa définition et ses transitions autorisées sont identifiables ;
- il est cohérent avec les autres attributs ;
- tout changement de statut possède une cause et une trace.

**Critères de non-conformité**

- le statut est absent, multiple ou ambigu ;
- une contradiction ou un retrait est incompatible avec le statut affiché ;
- un état indéterminé est présenté comme conclusion scientifique ferme ;
- un changement de statut n’a ni règle ni provenance.

**Preuves d’audit attendues**

- vocabulaire et règles de transition applicables ;
- correspondance entre statut et attributs de l’affirmation ;
- historique versionné des changements de statut.

### SA-REF-001 — Refus d’exprimer une conclusion non autorisée

**Exigence**

Lorsqu’un attribut obligatoire est absent, non démontré, contradictoire ou hors
domaine de manière incompatible avec la portée demandée, l’affirmation NE DOIT
PAS exprimer une conclusion scientifique plus forte que l’état de connaissance
autorisé.

Le refus de conclure DOIT rester un résultat scientifique explicite,
traçable et révisable. Il DOIT indiquer ses causes et les conditions
susceptibles de permettre une réévaluation.

**Critères de conformité**

- les conditions de refus sont évaluées avant la conclusion scientifique ;
- le refus expose les attributs limitants ou manquants ;
- aucun contenu plus fort n’est produit parallèlement ;
- les conditions de réévaluation sont déclarées.

**Critères de non-conformité**

- un attribut manquant est inventé ou remplacé silencieusement ;
- une contradiction bloquante est ignorée ;
- le refus est traité comme une erreur dépourvue de valeur scientifique ;
- une conclusion scientifique est produite au-delà de la portée autorisée.

**Preuves d’audit attendues**

- cas incomplets, contradictoires, insuffisants et hors domaine ;
- résultats de refus avec causes et conditions de réévaluation ;
- preuve qu’aucune conclusion scientifique concurrente plus forte n’est
  produite.

### SA-TRC-001 — Traçabilité de l’affirmation

**Exigence**

Toute affirmation scientifique DOIT permettre de parcourir les relations entre
son contenu, son type, ses sources, ses preuves, ses hypothèses, ses
transformations, ses limitations, ses contradictions, ses révisions, ses
réfutations, ses retraits et ses usages autorisés.

Cette traçabilité NE DOIT PAS dépendre d’une représentation particulière ni
d’un texte de présentation comme source unique.

**Critères de conformité**

- chaque relation nécessaire peut être suivie dans les deux sens ;
- les éléments absents ou inapplicables sont explicitement déclarés ;
- révisions, réfutations et retraits préservent les relations antérieures ;
- une décision peut être reliée à l’état de connaissance qui l’autorise.

**Critères de non-conformité**

- une source, règle, hypothèse ou transformation nécessaire est introuvable ;
- une limitation ou contradiction disparaît de la trace ;
- une présentation remplace la provenance ;
- un état historique ne peut plus être relié à ses usages.

**Preuves d’audit attendues**

- trace complète d’un ensemble d’affirmations défini par un critère
  d’échantillonnage déclaré ;
- parcours depuis mesures vers usages et depuis usages vers mesures ;
- historique des relations affectées par révision, réfutation et retrait.

## Relations avec les types de connaissances

Le présent contrat normalise l’expression des types définis dans
`KNOWLEDGE_MODEL.md` sans en modifier le sens.

### Mesure

Une affirmation de type mesure exprime les conditions d’acquisition, la
provenance instrumentale ou protocolaire, l’unité lorsqu’elle s’applique et le
domaine de validité. Elle ne contient aucune causalité implicite.

### Fait

Une affirmation de type fait exprime une description dérivée de mesures par
une règle déclarée. Sa portée maximale reste descriptive.

### Hypothèse

Une affirmation de type hypothèse exprime une proposition réfutable, ses
conditions de support, d’affaiblissement, de contradiction et de réfutation.
Elle ne se présente ni comme fait ni comme conclusion scientifique.

### Preuve

Une affirmation de type preuve exprime une relation orientée entre un fait
source et une hypothèse cible conformément à `EVIDENCE_MODEL.md`. Sa direction,
sa force, sa règle d’interprétation et son domaine de validité sont
obligatoires.

### Diagnostic

Une affirmation de type diagnostic caractérise un état ou un problème. Elle
exprime ses faits, hypothèses, preuves et incertitudes sans devenir
implicitement conclusion scientifique causale ou décision.

### Conclusion scientifique

Une affirmation de type conclusion scientifique statue dans une portée bornée
sur une hypothèse ou une Scientific Question déjà établie par l’autorité
scientifique. Elle expose ses preuves nécessaires, ses hypothèses concurrentes,
sa force, ses limitations et ses conditions de révision.

### Décision

Une affirmation de type décision exprime un choix autorisé par un état de
connaissance déclaré. Elle conserve l’autorité, les conditions
d’applicabilité, les blocages et les conditions de retrait de ce choix.

### Acquisition de preuve

Une affirmation de type acquisition de preuve exprime l’incertitude visée, les
faits recherchés, les conditions d’acquisition et l’effet attendu de chaque
résultat possible sur les hypothèses concernées.

## Audit de conformité d’une affirmation

Chaque affirmation auditée reçoit un unique statut de conformité conformément
à `SC-AUT-003`.

L’audit DOIT :

1. identifier le contenu et le type épistémique ;
2. vérifier chacun des quatorze attributs obligatoires ;
3. vérifier les obligations propres au type ;
4. parcourir la provenance et les dépendances ;
5. vérifier la portée, le domaine et la portée maximale ;
6. vérifier la force et, pour une conclusion scientifique, le minimum de ses
   preuves nécessaires ;
7. examiner les hypothèses, limitations et contradictions applicables ;
8. vérifier les conditions et historiques de révision, réfutation et retrait ;
9. vérifier la cohérence du statut ;
10. vérifier les conditions de refus ;
11. conserver les preuves d’audit et les éléments non démontrés.

La conformité de l’expression NE DÉMONTRE PAS la vérité externe du contenu, la
validation scientifique de la capacité productrice ni la satisfaction d’une
Scientific Question.

## Matrice minimale d’audit

| Obligation | Question d’audit | Preuve attendue indépendante de la représentation |
|---|---|---|
| Type et contenu | Le contenu est-il déterminé et porte-t-il un type unique ? | contenu auditable, définition du type, transformation autorisante |
| Provenance | Toutes les sources et règles nécessaires sont-elles accessibles ? | trace de provenance et historique |
| Portée | Les objets, conditions, phénomènes et usages sont-ils bornés ? | déclaration de portée et cas limites |
| Domaine | Les conditions de validité sont-elles explicites ? | domaine déclaré et cas hors domaine |
| Force | Le niveau et son critère respectent-ils l’ordre normatif ? | règle d’attribution et preuves nécessaires |
| Hypothèses | Les hypothèses nécessaires et concurrentes sont-elles visibles ? | dépendances et critères d’examen |
| Limitations | Les restrictions connues sont-elles conservées ? | limitations et effets déclarés |
| Contradictions | Les incompatibilités pertinentes sont-elles préservées ? | connaissances concernées et critères |
| Révision | Les déclencheurs et états successifs sont-ils traçables ? | conditions et historique versionné |
| Réfutation | La règle est-elle applicable et probante ? | règle, preuve défavorable et domaine |
| Retrait | L’usage actif cesse-t-il sans effacer l’historique ? | cause, règle et dépendances affectées |
| Portée maximale | Le contenu reste-t-il sous sa limite autorisée ? | limite déclarée et cas aux frontières |
| Statut | Un état unique et cohérent est-il déclaré ? | vocabulaire, règle de transition et historique |
| Refus | Une conclusion non autorisée est-elle effectivement refusée ? | cas négatifs et résultat de refus |

## Indépendance de la représentation

Une affirmation conforme PEUT être représentée de plusieurs manières, à
condition que tous ses attributs, relations et historiques obligatoires
restent auditables.

Aucune conformité NE PEUT être déduite de la présence d’un champ, de la
réussite d’une validation technique, d’un format, d’une structure ou d’un nom
particulier. Inversement, l’absence d’une représentation technique particulière
NE CONSTITUE PAS une non-conformité lorsque les obligations conceptuelles sont
démontrées.
