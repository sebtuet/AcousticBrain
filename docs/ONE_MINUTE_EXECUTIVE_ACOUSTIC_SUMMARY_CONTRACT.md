# Contrat de la synthèse acoustique « EN UNE MINUTE »

## Objet et utilisateur cible

`EN UNE MINUTE` est une condensation éditoriale destinée à un utilisateur qui
maîtrise REW sans nécessairement maîtriser l’interprétation acoustique. Elle répond
immédiatement à quatre questions : est-ce mieux qu’avant, puis-je conclure, que
dois-je faire maintenant et pourquoi ?

Elle est rendue après le titre et le nom du projet, avant `DÉCISION ACOUSTIQUE`.
Elle ne remplace ni cette page PR-041, ni la synthèse d’action PR-040, ni le
rapport technique qui restent présents ensuite.

## Structure obligatoire

La section contient exactement, dans cet ordre :

1. `Situation` ;
2. `Verdict` ;
3. `Puis-je conclure ?` ;
4. `Ce que je fais maintenant` ;
5. `Pourquoi` ;
6. `Confiance`.

Le cas nominal ne dépasse pas 20 lignes utiles. Aucun cas ne dépasse 24 lignes
utiles. Les actions occupent au maximum trois lignes et la justification au
maximum deux phrases.

## Sources structurées

Le présentateur consomme la projection structurée de
`DecisionFirstReportPresenter`. Cette projection expose la dernière comparaison,
son statut de comparabilité, son verdict, la présence des déclarations de protocole
et d’hypothèse, l’action déjà sélectionnée par PR-041, les conditions de déblocage
et le statut du diagnostic de qualité des mesures.

La disponibilité des mesures est traduite depuis la sévérité structurée du
diagnostic `Qualité des mesures` : `LOW` signifie exploitable, `MEDIUM`
exploitable avec réserves, `HIGH` insuffisant, et toute absence ou autre valeur
reste non établie.

## Règles de condensation

- Le verdict traduit le statut existant ; `MIXED` n’est jamais présenté comme une
  amélioration ou une dégradation globale.
- Une conclusion positive reste limitée au périmètre mesuré et exige une
  comparaison fiable ainsi que des conditions testées déclarées.
- Une comparaison absente ou non comparable, un verdict contradictoire ou
  inconclusif, ou des conditions non déclarées empêchent une conclusion globale.
- L’action est exclusivement celle déjà projetée par PR-041. La synthèse peut la
  raccourcir et y joindre sa direction, sa distance, ses contrôles ou les mesures
  requises seulement lorsque ces données existent.
- En l’absence d’action, la section l’indique explicitement. Si plusieurs actions
  sont à égalité, elle ne les départage pas. Une action différée n’est pas
  réactivée ; seule la décision déjà requise pour poursuivre peut être rappelée.
- `Pourquoi` retient une ou deux limites déjà établies au lieu de reproduire les
  observations détaillées.

## Limites et interdictions

La synthèse conserve explicitement que la cause est `NOT_ESTABLISHED`. Elle ne
calcule aucune comparaison, priorité, recommandation, action, direction,
distance, score ou confiance scientifique.

Elle ne suppose jamais qu’un déplacement, un changement de position ou une
modification volontaire a eu lieu. Elle n’invente ni protocole ni variable
testée, ne qualifie aucune position d’optimale, ne garantit aucune amélioration
et ne confirme aucune cause.
