# Registre des marchés UMA, grille d'audit des clauses de résolution

Version du 01/11/2026 pour Jonathan (résident à Dubaï, Émirats). Heures en UTC. Toute donnée non vérifiée figure entre crochets. Les renvois (S1 à S40) mènent au tableau des sources du § 7.

Ce document est un résultat de recherche. Il ne contient aucun ordre, aucune clé et aucune recommandation d'investissement. Il n'est pas un avis juridique. Aucune stratégie ne change de statut à sa lecture. Une note ou un marché retenu ou écarté ne vaut pas recommandation d'investissement.

Données réelles lues pour ce registre. Règles et champs UMA des 40 marchés du collecteur `20261031T224031Z` lus sur l'API Gamma et sur `/v2/resolutions` de 2026-10-31T23:01:20Z à 2026-10-31T23:01:28Z. Mesure des délais lue jusqu'à 2026-10-31T23:02:11Z. Fichiers `resultats/20261031T230120Z_clauses.json`, `_delais.csv` et `_delais.json`, produits par `extraire_clauses.py`. Le présent fichier sort de `genere_registre.py`, qui relit les précédents et l'intérêt ouvert à chaque passage.

## 0. Alerte, mi-mandat du 03/11/2026

Une vague de résolutions approche sur des marchés dont le paiement peut arriver bien après la date de fin affichée par Gamma. Sur le classement du collecteur, 14 marchés sur 20 sont liés au scrutin (rapport du collecteur, 22:46 UTC). Le passage relancé le 01/11/2026 à 00:13 UTC en compte 17 sur 20. Leur date de fin Gamma est le 04/11 à 04:59 UTC (le #9 affiche le 03/11 à 23:59 UTC), et cette date ne dit rien du jour du paiement. Le scrutin n'a pas encore eu lieu et aucun litige sur ces marchés n'est connu à cette heure. Le statut lu est `posed` sur 40 marchés sur 40. Ce qui suit décrit donc des points de friction possibles et non des litiges en cours.

| Point de friction | Fait sourcé | Marchés du registre touchés |
|---|---|---|
| Recours fédéral en Alaska | Le ministère de la Justice a déposé plainte le 22/10 pour bloquer ou retarder la certification si le sénateur sortant perd. L'État et la candidate démocrate demandent le rejet et la juge a accéléré le calendrier (S25). Issue de la requête [non vérifiée au 31/10] | #8 #2 #4 #5 et surtout #9, dont le repli passe par la certification |
| Vote préférentiel en Alaska et au Maine | L'Alaska accepte des bulletins de l'étranger 15 jours après le scrutin. Au Maine l'issue a souvent été connue la semaine suivante (S23) | #8 #2 #4 #5 #9 |
| Second tour en Géorgie | Second tour le 01/12 si aucune majorité, certification le 20/11 puis le 18/12 (S24, source opérateur concurrent). Les règles comptent ce second tour même après novembre | #8 #2 #4 #5 |
| Californie lente | Bulletins acceptés jusqu'au 10/11 si oblitérés à temps, certification de l'État le 11/12 (S24). Quelques sièges peuvent rester sans appel une à deux semaines (S23) | #1 #3 #2 #4 #5 #10 |
| Bulletins arrivés après le scrutin | La Cour suprême a jugé que les lois fédérales n'interdisent pas de compter des bulletins oblitérés à temps et reçus jusqu'à cinq jours après (S26, note du 17/07/2026). L'avance d'un candidat peut donc changer après le soir du vote (S23) | Tous les marchés de sièges |
| Louisiane | Les sources se contredisent sur le calendrier des sièges de la Chambre et sur un éventuel second tour de décembre [non vérifié] | #1 #3 #10 |
| Recomptages | Ils peuvent courir jusqu'en décembre ou au-delà (S23) | Courses serrées, dont #6 #7 #11 #14 |
| Élus indépendants | Le marché peut rester ouvert jusqu'au 04/01/2027 à 11:59 PM ET si le rattachement n'est pas connu (règles lues sur Gamma) | #1 #3 #2 #4 #5 #8 #10 |
| Caution | Elle vaut 10 000 sur les marchés de contrôle et 2 500 sur les courses du Sénat lues, contre 500 sur les précédents du § 1.5. Elle reste à 500 sur #9 #10 #14 (Gamma). Effet sur le nombre de contestations [non mesuré] | #1 #3 #2 #4 #5 #8 #6 #7 #11 #13 #16 |
| Unanimité AP, Fox et NBC | Sans appel commun le marché attend la certification officielle (règles lues sur Gamma) | #6 #7 #11 #13 #16 #9 |

Les élections récentes donnent un ordre de grandeur. Le tableau ci-dessous reprend les marchés électoraux contestés de notre échantillon. Le délai court de la date de fin Gamma à la clôture Gamma et il contient aussi l'attente des résultats. Il ne mesure donc pas le seul litige et sa cause reste [non vérifiée] pour chaque cas.

| Élection | Marchés contestés lus | Volume Gamma | Délai maximal fin à clôture | `was_disputed` vrai, lu comme passage au vote [hypothèse] |
|---|---|---|---|---|
| Présidentielle Pérou 2026 | 5 | 74,1 M$ | 29,6 j | 3 |
| Présidentielle Colombie 2026, premier tour | 7 | 6,9 M$ | 7,6 j | 2 |
| Assemblée nationale Arménie 2026 | 1 | 579,4 k$ | 8,0 j | 0 |
| Présidentielle Bulgarie 2026, premier tour | 2 | 244,7 k$ | 4,1 j | 2 |
| Land de Berlin 2026 | 5 | 4,4 M$ | 1,3 j | 0 |

Conséquence pour la recherche. Un capital posé sur ces marchés peut rester bloqué des semaines et un maker peut rester exposé pendant une proposition en cours, car les contrats restent négociables pendant un litige (S17, cas Iran). Cela concerne le moteur B de la note de régime. Nous proposons au conseil de ne pas faire entrer ces marchés dans la mesure de calibration tant qu'ils ne sont pas résolus, ce qui reste une proposition non appliquée.

## 1. Mécanique et délais

### 1.1 Fonctionnement décrit par les sources officielles

| Étape | Règle lue | Source, lue le 31/10/2026 |
|---|---|---|
| Proposition | Une issue est proposée avec une caution. La documentation Polymarket dit que tout le monde peut proposer et cite en général 750 pUSD | S1 |
| Liste blanche | Sur l'oracle géré MOOV2 seules des adresses autorisées proposent. Les autres peuvent demander à une adresse autorisée de le faire | S7, S8, S6 |
| Contestation | Elle reste ouverte à tous, avec une contre-caution de même montant | S1, S7 |
| Période de contestation | 2 heures. Le contrat prévoit ce défaut quand la durée personnalisée vaut 0 | S1, S10 |
| Première contestation | Le marché est réinitialisé et un nouveau tour de proposition s'ouvre | S1, S9, S10 |
| Seconde contestation | Le litige passe au vote DVM des détenteurs d'UMA | S1, S9 |
| Débat | 24 à 48 heures sur le Discord d'UMA | S1 |
| Vote | 48 heures, soit 24 heures de vote secret et 24 heures de révélation. Les tours changent à 24:00 UTC et un litige doit arriver au moins 4 heures avant un tour | S2, S3 |
| Seuils du vote | 5 millions d'UMA votants et 65 % d'accord. Sinon le vote est reporté, et il devient supprimable après 4 reports (valeurs au lancement de DVM 2.0) | S4 |
| Incitation des votants | Environ 0,1 % du montant déposé est retiré en cas de vote perdant ou d'absence, puis redistribué. Le retrait des jetons demande 7 jours (valeur initiale) | S3, S4, S5 |
| Répartition des cautions | Le gagnant récupère sa caution et la moitié de celle du perdant. Une proposition prématurée compte comme perdante | S1 |
| Délai annoncé | Environ 2 heures sans litige, 4 à 6 jours avec litige. Le dépôt du contrat parle de 48 à 72 heures pour le DVM | S1, S9 |
| Clarifications | Polymarket peut publier un « Additional context » en cours de vie. Il ne doit pas changer l'intention de la question et les votants doivent en tenir compte | S1 |
| Marchés Up ou Down | Ils se résolvent par TWAP Chainlink sans UMA, donc ce registre ne les couvre pas | S1, S13 |

### 1.2 Écarts entre la documentation et les données

| Point | Ce que dit la documentation | Ce que nous lisons | Lecture |
|---|---|---|---|
| Caution | Généralement 750 pUSD (S1) | Sur nos 40 marchés nous lisons 500 pour 22 marchés ; 2500 pour 5 marchés ; 10000 pour 7 marchés ; 25000 pour 3 marchés ; 50000 pour 3 marchés. Dans l'échantillon résolu la caution vaut 500 sur 6332 marchés sur 6375 | La caution se lit marché par marché. L'unité de `umaBond` reste [non vérifiée] et nous la supposons en pUSD |
| Durée de contestation | 2 heures (S1) | `customLiveness` vaut 0 sur 40 marchés sur 40. Le second échantillon montre de 600 à 1 800 secondes sur 985 marchés sur 2100. Un tirage de questions y montre surtout du sport | La fenêtre peut tomber à 10 minutes hors de notre périmètre. Elle est donc à contrôler avant tout usage |
| Qui propose | « Anyone » dans la doc Polymarket (S1) | Liste blanche MOOV2 chez UMA, avec 37 adresses au lancement (S7) puis des critères de 5 propositions sur 6 mois et plus de 95 % d'exactitude (S6) | Les deux textes ne s'accordent pas. Part réelle des marchés passés sur MOOV2 [non vérifiée] |
| Liste de 37 adresses | Le blog UMA parle de proposeurs (S7) | Crypto Briefing écrit qu'elle limite le vote (S21) | Nous retenons le blog UMA. La phrase de Crypto Briefing paraît fausse |
| Issue 50-50 | Possible si l'issue est inconnue (S1) | Le contrat neg risk n'accepte que oui ou non (S10, S11) et 34 marchés sur 40 sont `negRisk`. Aucune finale à 50-50 sur 737 états lus | Sur ces marchés le 50-50 écrit dans la doc ne semble pas disponible. Il reste possible au vote sur les 6 marchés hors `negRisk`, car la doc garde la ligne Unknown/50-50 (S1). Le chemin suivi en cas d'issue inconnue reste [non vérifié] |
| Intervention de Polymarket | Les conditions disent que Polymarket n'intervient pas dans la résolution (S36) | Le code public prévoit des fonctions d'administration de signalement et de résolution manuelle (S10, S11) | Ces droits existent dans le code de la branche principale. Titulaire et usage réel [non vérifiés] |
| Nouveaux modules | Une architecture V2 liste des modules de résolution OO, Chainlink et EOA (S12) | Les 40 marchés portent `version` v1 et `resolutionMechanism` oracle. Le champ `resolvedBy` donne 3 adresses absentes de la page des contrats | Rattachement de ces adresses [non vérifié] |
| Revue prolongée | Le schéma décrit `extended_review` pour une proposition gérée au-delà de son échéance (S13, S14) | Aucun cas sur 737 états de marchés résolus et sur nos 40 marchés | Le mécanisme est récent et il peut allonger un délai. Son usage reste [non mesuré] |

### 1.3 Délai réel et fréquence, mesurés sur Gamma et `/v2/resolutions`

Notre échantillon compte 6375 marchés clos de politique, de macro et de tech. Leur date de fin va du 04/05/2026 au 31/10/2026. Ils sont triés par volume et plafonnés par l'API à 2 100 lignes par étiquette. Un second échantillon reprend les 2100 plus gros marchés toutes catégories. Le délai va de la date de fin Gamma à la clôture Gamma et ne garde que les clôtures postérieures à cette date. Il contient donc parfois l'attente de l'événement. La colonne n donne le nombre de marchés qui portent chaque délai et la colonne suivante ceux qui en sortent. Les quantiles sont recalculés depuis `20261031T230120Z_delais.csv` par interpolation linéaire entre rangs (défaut de numpy).

| Groupe (politique, macro, tech) | Marchés | Part des marchés | Volume | Part du volume | n du délai | Clos avant la fin, exclus | Délai médian | P75 | P90 | Maximum |
|---|---|---|---|---|---|---|---|---|---|---|
| Sans statut de contestation | 6238 | 97,85 % | 3,33 Md$ | 76,2 % | 4185 | 2053 | 10,1 h | 23,1 h | 36,3 h (1,5 j) | 125,9 j |
| Au moins un statut « disputed » sur Gamma | 137 | 2,15 % | 1,04 Md$ | 23,8 % | 89 | 48 | 88,4 h | 120,6 h | 469,7 h (19,6 j) | 51,6 j |
| Dont `was_disputed` vrai, lu comme passage au vote [hypothèse] | 81 | 1,27 % | 991,2 M$ | 22,7 % | 58 | 23 | 96,6 h | 124,3 h | 432,6 h (18,0 j) | 37,6 j |
| Dont `indice_dvm` vrai, lu comme passage au vote [hypothèse] | 49 | 0,77 % | 833,7 M$ | 19,1 % | 31 | 18 | 96,5 h | 156,6 h | 336,5 h (14,0 j) | 36,0 j |

La couverture des délais reste partielle. Le délai porte sur 89 des 137 marchés contestés et sur 58 des 81 marchés à `was_disputed` vrai. Les 48 marchés contestés clos avant leur date de fin Gamma pèsent 48,1 % du volume contesté et ces lignes ne les décrivent pas. C'est le cas du marché MicroStrategy du 31/05 (375,8 M$), clos 27,1 jours avant sa date de fin Gamma.

Le P90 des marchés contestés dépend de la méthode. Il vaut 19,6 j par interpolation et 25,8 j au rang supérieur, ce que garde `_delais.json` et ce que donnait la version du 31/10. La queue tient à peu de marchés (89 ici), donc nous le lisons comme un ordre de grandeur.

Deux indices de vote existent dans le fichier et ils ne concordent pas. Le champ `was_disputed` en compte 81 et `indice_dvm` en compte 49, ce dernier demandant une clôture entre 00:00 et 01:00 UTC et un dernier statut « disputed ». Les deux sont vrais sur 48 marchés, seul `was_disputed` sur 33 et seul `indice_dvm` sur 1. La part des marchés passés au vote va donc de 0,77 % à 1,27 % selon l'indice, et aucun des deux n'est un compte officiel des votes.

Le champ `was_disputed` n'est vrai que sur des marchés à au moins deux statuts « disputed ». Sur les 56 marchés contestés où ce champ est faux, la majorité ne porte qu'une contestation. Nous le lisons donc comme un passage au vote, ce que le schéma ne dit pas exactement [hypothèse]. Parmi ces 81 marchés, 48 ferment entre 00:00 et 01:00 UTC, ce qui concorde avec un tour de vote qui finit à 24:00 UTC (S2).

Sur ces 81 marchés à `was_disputed` vrai [hypothèse de vote], la finale diffère de la première proposition 24 fois. Elle diffère de la seconde proposition 5 fois sur 78. Le vote suit donc le plus souvent le second proposeur, dans cet échantillon et sans lien de cause établi.

La médiane reste proche des 4 à 6 jours annoncés par la documentation. Le risque se trouve dans la queue, avec un P90 de 18,0 j et un maximum de 37,6 j sur 58 marchés. Nous ne pouvons pas séparer ici l'attente de l'événement et la durée du litige.

La fréquence est très concentrée. Hors Iran (46 marchés) et MicroStrategy, la part contestée du volume tombe de 23,8 % à 6,2 %. Sans le seul marché MicroStrategy du 31/05 elle vaut 16,7 %. Dans l'échantillon toutes catégories, 63 marchés sur 2100 sont contestés (3,0 %) pour 7,1 % de 17,53 Md$. Polymarket annonce 0,21 % de marchés passés au vote sur 12 mois [citation vue dans des résultats de recherche, page non relue]. Notre 1,27 % ne la contredit pas forcément, car notre échantillon surreprésente les marchés politiques à gros volume.

### 1.4 Concentration du vote

| Mesure | Valeur | Source, statut |
|---|---|---|
| Votants UMA actifs liés à un compte Polymarket | Au moins 60 % | WSJ du 18/05/2026 repris par S20 et S21. Article du WSJ non lu |
| Litiges avec au moins un votant détenteur d'une position | Environ 1 sur 5 | WSJ repris par S20. Article du WSJ non lu |
| Poids des 10 plus gros portefeuilles | Plus de 50 % dans la plupart des litiges | WSJ repris par S20 |
| Poids de 9 portefeuilles | Plus de la moitié des jetons utilisés | Bloomberg repris par S17. Article de Bloomberg non lu |
| Vote sur le marché Iran | 7 baleines à 50,3 % du vote, 565 participants | S19, source unique |
| Vote sur le marché MicroStrategy | 98,6 % pour le non (S15). Les 4 plus gros votants du non pèsent près de 7 millions (S16), soit plus que le seuil de 5 millions de S4 | Rapprochement fait par nous. Seuil actuel [à vérifier] |
| Réponse d'UMA | Pas de preuve de collusion selon ses représentants | Résultat de recherche, page non relue |
| Réformes | Les corrections proposées restent bloquées selon S21. Un jeton POLY à fonction d'oracle est à l'étude selon S21 | Source unique, aucun texte officiel trouvé pour septembre ou octobre 2026 |

### 1.5 Précédents, contrôle de `2026-10-31_RADIOGRAPHIE_ET_AUDIT.md`

| Affirmation du dépôt | Contrôle | Statut |
|---|---|---|
| Le marché Strategy du 31/05 s'est résolu non malgré un dépôt SEC indiquant des ventes du 26 au 31/05 | Confirmé sur Gamma et `/v2/resolutions`. S15 et S16 confirment 32 BTC et un 8-K du 01/06. Le marché du 30/06 s'est résolu oui | Confirmé |
| La date de publication a primé sur la date de l'événement | Exact pour le résultat. Le texte lu sur Gamma se contente d'une heure limite et ne parle pas de confirmation. Une note de contexte a été ajoutée le 01/06 selon S15, et elle n'apparaît pas dans la description Gamma lue aujourd'hui | Confirmé avec nuance. Le critère a été précisé après la vente |
| Galaxy Research et The Block comme sources | Galaxy détenait une position sur le oui d'après sa propre déclaration et conteste le résultat (S16, résultats de recherche) | Source intéressée, à lire comme telle |
| Le marché Iran pesait 120 M$ | Ce chiffre vient de S18 au 17/06. Gamma donne 177,4 M$ pour le marché du 15/06 et 478,9 M$ pour l'événement. S17 cite 345 M$ au 15/06 | À corriger, périmètres différents |
| Le marché Iran a suivi en juin | Résolu oui et clos le 18/06 à 00:32 UTC sur Gamma. Le protocole prévoyait un cadre de 60 jours selon S17 et S19, d'où le débat sur « permanent » | Confirmé |
| 3,32 Md$ contestés, soit 7,3 % du volume UMA (Fidonis) | Aucune source trouvée à ce nom ni à ces chiffres en deux recherches. Notre mesure toutes catégories donne 7,1 %, sur une autre période et avec une autre méthode. Elle ne valide pas le chiffre | [Source unique, non retrouvée]. Le rapprochement ne prouve rien |
| 60 % des votants liés à Polymarket | Repris à l'identique par S20 et S21 au nom du WSJ | Confirmé comme citation secondaire, article d'origine non lu |

Lecture directe des précédents le 01/11/2026 à 00:21 UTC. Les colonnes donnent première proposition, seconde proposition et prix final.

| Marché | Volume Gamma | Clôture Gamma (UTC) | Première / seconde / finale | `was_disputed` | Caution |
|---|---|---|---|---|---|
| MicroStrategy, 31/05/2026 | 375,8 M$ | 04/06/2026 00:34 | non / non / non | oui | 500 |
| MicroStrategy, 30/06/2026 | 8,4 M$ | 01/06/2026 14:07 | oui / vide / oui | non | 500 |
| Iran paix permanente, 15/06/2026 | 177,4 M$ | 18/06/2026 00:32 | oui / oui / oui | oui | 500 |
| Iran paix permanente, 31/12/2026 | 14,4 M$ | 18/06/2026 00:38 | oui / oui / oui | oui | 500 |
| Zelensky costume, avant juillet 2025 | 242,2 M$ | 09/07/2025 00:30 | oui / non / non | oui | 500 |
| Trump dossiers OVNI, 15/05/2026 | 3,2 M$ | 19/05/2026 00:32 | non / oui / oui | oui | 500 |

Deux enseignements se lisent ici. Le premier est que des marchés liés se résolvent ensemble, car les échéances Iran du 15/06 et du 31/12 ferment à quelques minutes d'écart. Le second est qu'une caution de 500 a été lue sur un marché de 375,8 M$ de volume cumulé, soit un rapport de 1 pour plus de 700 000. Ce rapport n'est qu'un ordre de grandeur, car le volume cumulé n'est pas l'enjeu et l'unité de `umaBond` reste [non vérifiée]. L'intérêt ouvert serait la bonne mesure, mais nous n'en lisons que la valeur courante et ce marché résolu n'en garde que 4,3 k$ (S40, lu le 01/11/2026 à 00:21 UTC). Celui du jour du litige reste [non mesuré]. La caution semble donc peser peu sur ces gros marchés, sans que nous puissions le chiffrer.

## 2. Grille notée

Chaque critère reçoit une note de 0 à 3. Le total va de 0 à 21. Ces notes restent un jugement de lecture et non une mesure, comme le dépôt l'a déjà corrigé pour ses matrices sur 20 (`2026-10-31_SQD_RENTABILITE_INTEGRATION.md`, § 0.2). Elles n'ont été ni calibrées ni testées. Elles servent à classer ce qu'il faut relire et ne donnent aucune probabilité de litige.

| Code | Critère | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| F | Formulation | Règle chiffrée, sans mot à interpréter | Détails à suivre mais écrits | Mot ou seuil qui demande une interprétation | Notion centrale non définie |
| S | Source et repli | Source officielle unique et nommée | Source hiérarchisée avec repli écrit | Sources plurielles sans ordre, ou source privée unique | Aucune source claire et aucun repli |
| A | Annulation et issue par défaut | Issue par défaut sans effet sur le fond | Issue par défaut nommée et rare | Issue par défaut qui change le sens du pari | Aucune sortie prévue pour un cas plausible |
| C | Conflit entre règle et esprit | Aucun conflit plausible | Cas limite théorique | Cas plausible où la lettre contredit le titre | Conflit déjà visible |
| L | Risque de contestation | Issue mécanique et peu d'enjeu | Issue lisible, enjeu moyen | Issue serrée ou calendrier long | Issue serrée, délais longs et contentieux ouvert |
| V | Exposition au vote | Fait public chiffré | Fait public, enjeu modéré | Interprétation et enjeu notable | Interprétation et très gros enjeu |
| M | Marchés liés | Marché isolé | Quelques marchés voisins | Plusieurs issues ou échéances liées | Résolution qui en entraîne d'autres |

Niveaux proposés. De 0 à 5 faible, de 6 à 10 modéré, de 11 à 14 élevé et à partir de 15 très élevé. Un 3 en F, S ou L impose une relecture humaine, quel que soit le total.

Mots et points à contrôler dans F, avec un cas réel.

| Point | Piège | Cas |
|---|---|---|
| « Official » ou « officially » | Le mot peut viser l'auteur ou le fait, et les canaux acceptés varient | #19 accepte toute agence fédérale. #17 exige un canal officiel ou vérifié |
| « Announce » | L'annonce vaut fait, sans contrôle de vérité et parfois sans suite | #17, #22, #20. Le #20 dispense de confirmation externe |
| Date de l'événement contre date de publication | Un fait d'avant l'échéance publié après peut ne pas compter | MicroStrategy du 31/05. Le #68 fixe un calendrier de publication écrit |
| Seuils | Valeur exacte, bornes et trous entre exemples | #48 ne couvre pas 37,5 pb. #77 attribue la borne à la tranche haute. #10 dépend de chaque siège |
| Fuseaux | Le texte parle en ET et la date Gamma en UTC, parfois sans concordance | #48 affiche 23:59 UTC pour 11:59 PM ET. #145 vise une date locale de Nouvelle-Zélande |
| Date de fin Gamma | Elle peut précéder l'issue ou s'en éloigner | MicroStrategy du 31/05 porte une date de fin au 01/07 sur Gamma |
| Clarification | Une note peut arriver après la vente et trancher le débat | MicroStrategy, note du 01/06 selon S15 |

## 3. Application aux 40 marchés du collecteur

Lecture réelle sur Gamma le 31/10/2026. L'heure figure ligne par ligne. Les extraits sont en anglais d'origine et comptent moins de 15 mots. Un texte identique à un autre marché n'est pas recité. Le texte complet de chaque règle se trouve dans `resultats/20261031T230120Z_clauses.json`. Le prix de la colonne Bid / ask est celui lu sur Gamma au même moment. Les notes suivent l'ordre F S A C L V M.

La grille donne 9 marchés faibles et 14 modérés. Elle donne 17 marchés élevés et aucun très élevé. La relecture humaine s'impose sur #9 #10 #19 #59.

### 3.1 Mi-mandat 2026

| # | Marché (question Gamma) | Bid / ask | Caution / récompense | Lu à (UTC) | Extrait des règles | F S A C L V M | Total | Niveau | Point d'attention |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Republican Party control the House after the 2026 Midterm e... | 0,050 / 0,060 | 10000 / 10 | 23:01:20 | « may remain open until the earlier of » | 1 2 1 1 1 2 3 | 11 | élevé | Majorité des sièges, puis Speaker en repli. Trois sources sans ordre de priorité. Clause des indépendants ouverte jusqu'au 04/01/2027. |
| 3 | Democratic Party control the House after the 2026 Midterm e... | 0,940 / 0,950 | 10000 / 10 | 23:01:20 | Texte identique au #1 | 1 2 1 1 1 2 3 | 11 | élevé | Miroir du #1 dans le même événement. Même lecture et mêmes délais. |
| 2 | 2026 Balance of Power: R Senate, D House | 0,230 / 0,240 | 10000 / 10 | 23:01:20 | « even if it takes place after November 2026 » | 2 2 1 1 2 2 3 | 13 | élevé | Deux chambres à la fois et trois niveaux de repli au Sénat. Le second tour de Géorgie du 01/12 peut repousser le paiement. |
| 4 | 2026 Balance of Power: D Senate, D House | 0,700 / 0,710 | 10000 / 10 | 23:01:20 | Texte identique au #2 | 2 2 1 1 2 2 3 | 13 | élevé | Issue dominante du même événement. Une seule course lente suffit à bloquer. |
| 5 | 2026 Balance of Power: R Senate, R House | 0,040 / 0,050 | 10000 / 10 | 23:01:21 | Texte identique au #2 | 2 2 1 1 2 2 3 | 13 | élevé | Issue à prix faible. Une contestation y coûte la même caution que sur le #4. |
| 8 | Republican Party control the Senate after the 2026 Midterm... | 0,280 / 0,290 | 10000 / 10 | 23:01:21 | « scheduled to take place in November 2026 as of October 31, 2026 » | 2 2 1 1 2 2 3 | 13 | élevé | La date de coupure tombe le jour de cette lecture. Alaska, Maine et Géorgie peuvent décider du contrôle après le 04/11. |
| 6 | Democrats win the Kansas Senate race in 2026 | 0,510 / 0,520 | 2500 / 20 | 23:01:21 | « once all three sources call the race for the same candidate » | 1 1 1 0 2 1 2 | 8 | modéré | Trois réseaux unanimes, puis certification officielle. Course serrée, donc attente possible jusqu'à la certification. |
| 11 | Republicans win the Kansas Senate race in 2026 | 0,480 / 0,490 | 2500 / 20 | 23:01:22 | Texte identique au #6 | 1 1 1 0 2 1 2 | 8 | modéré | Miroir du #6. Un indépendant vainqueur ne compterait pour aucune des deux issues nommées. |
| 7 | Democrats win the Iowa Senate race in 2026 | 0,440 / 0,450 | 2500 / 20 | 23:01:21 | « this market will resolve based on the official certification » | 1 1 1 0 2 1 2 | 8 | modéré | Même modèle que le Kansas. Course serrée d'après le carnet. |
| 13 | Democrats win the Texas Senate race in 2026 | 0,700 / 0,710 | 2500 / 20 | 23:01:22 | « Candidates who run as independents will not be encompassed » | 1 1 1 0 1 1 2 | 7 | modéré | Écart de prix plus net qu'au Kansas et en Iowa. Même modèle à trois réseaux. |
| 16 | Republicans win the Texas Senate race in 2026 | 0,290 / 0,300 | 2500 / 20 | 23:01:23 | Texte identique au #13 | 1 1 1 0 1 1 2 | 7 | modéré | Miroir du #13. |
| 9 | Republicans lose the Alaska, Iowa, Kansas, Maine, Michigan,... | 0,220 / 0,230 | 500 / 3.5 | 23:01:22 | « if its results cannot be determined by March 31, 2027 » | 2 1 2 1 3 2 3 | 14 | élevé | Ensemble exact de sept États. Le recours fédéral en Alaska touche directement le repli par certification. Caution de 500 seulement. |
| 10 | Republican Party hold below 190 House seats after the 2026... | 0,380 / 0,390 | 500 / 5 | 23:01:22 | « the member will not count towards the seat count of any party » | 2 2 1 1 3 2 3 | 14 | élevé | Seuil proche du prix et dépendant de chaque siège. Californie lente et clause des indépendants. |
| 14 | Democratic Party win the NJ-02 House seat | 0,310 / 0,320 | 500 / 5 | 23:01:22 | « at the time all of the 2026 House elections are conclusively called » | 2 2 1 1 2 1 2 | 11 | élevé | L'étiquette du parti se fixe sur un moment national et non sur ce siège. Le repli FEC peut arriver tard [délai non vérifié]. |

### 3.2 Autre politique

| # | Marché (question Gamma) | Bid / ask | Caution / récompense | Lu à (UTC) | Extrait des règles | F S A C L V M | Total | Niveau | Point d'attention |
|---|---|---|---|---|---|---|---|---|---|
| 12 | Alexandria Ocasio-Cortez win the 2028 US Presidential Election | 0,125 / 0,128 | 50000 / 20 | 23:01:22 | « this market will resolve based on who is inaugurated » | 1 1 0 0 1 1 2 | 6 | modéré | Règle courte et repli net. Immobilisation jusqu'en 2028 à compter dans le coût. |
| 23 | Jon Ossoff win the 2028 US Presidential Election | 0,096 / 0,097 | 50000 / 20 | 23:01:26 | Texte identique au #12 | 1 1 0 0 1 1 2 | 6 | modéré | Même lecture que le #12. |
| 26 | Marco Rubio win the 2028 US Presidential Election | 0,095 / 0,096 | 50000 / 20 | 23:01:26 | Texte identique au #12 | 1 1 0 0 1 1 2 | 6 | modéré | Même lecture que le #12. |
| 18 | Kamala Harris win the 2028 Democratic presidential nomination | 0,057 / 0,060 | 25000 / 10 | 23:01:23 | « a consensus of official Democratic Party sources » | 2 2 1 1 1 2 2 | 11 | élevé | Règle très courte. « Accepte » n'est pas daté et aucune adresse de source ne figure. |
| 29 | Jon Ossoff win the 2028 Democratic presidential nomination | 0,149 / 0,155 | 25000 / 10 | 23:01:26 | Texte identique au #18 | 2 2 1 1 1 2 2 | 11 | élevé | Même lecture que le #18. |
| 30 | Josh Shapiro win the 2028 Democratic presidential nomination | 0,049 / 0,051 | 25000 / 10 | 23:01:26 | Texte identique au #18 | 2 2 1 1 1 2 2 | 11 | élevé | Même lecture que le #18. |
| 15 | Marine Le Pen win the 2027 French presidential election | 0,406 / 0,408 | 500 / 5 | 23:01:23 | « this market will resolve to "Other" » | 1 1 1 0 1 1 1 | 6 | modéré | Consensus de presse puis ministère de l'Intérieur. Marché français, à lire avec le § 4 pour tout participant résidant en France. |
| 31 | Javier Milei win the 2027 Argentina presidential election | 0,430 / 0,440 | 500 / 5 | 23:01:26 | « If the results are not known definitively by October 31, 2028 » | 1 1 1 0 1 1 1 | 6 | modéré | Second tour inclus et sources officielles argentines nommées. |
| 61 | Republican Party control the House after the 2028 elections | 0,320 / 0,340 | 10000 / 10 | 23:01:27 | « the first elected Speaker of the House of the Congress » | 1 2 1 1 1 1 2 | 9 | modéré | Même modèle que le #1 pour 2028. Frais actifs et volume très faible. |

### 3.3 Macroéconomie

| # | Marché (question Gamma) | Bid / ask | Caution / récompense | Lu à (UTC) | Extrait des règles | F S A C L V M | Total | Niveau | Point d'attention |
|---|---|---|---|---|---|---|---|---|---|
| 48 | 1 Fed rate hike happen in 2026 | 0,270 / 0,290 | 500 / 5 | 23:01:24 | « hikes between 1–24 bps (inclusive) will also be considered 1 rate hike » | 1 0 0 0 1 0 2 | 4 | faible | Une hausse de 37,5 pb n'est pas couverte par les exemples. La date Gamma 23:59 UTC devance de 5 h le 11:59 PM ET du texte. |
| 80 | no Fed rate cuts happen in 2026 | 0,970 / 0,971 | 500 / 5 | 23:01:24 | « Emergency rate cuts outside of scheduled FOMC meetings will also count » | 0 0 0 0 0 0 2 | 2 | faible | Texte net et source officielle unique. Issue déjà très probable d'après le prix. |
| 58 | there be no change in Fed interest rates after the March 20... | 0,450 / 0,470 | 500 / 5 | 23:01:24 | « this market will resolve to the "No change" bracket » | 0 0 1 0 0 0 2 | 3 | faible | Communiqué du FOMC nommé et repli écrit. Volume très faible. |
| 89 | there be no change in Fed interest rates after the April 20... | 0,560 / 0,570 | 500 / 5 | 23:01:24 | « the change will be rounded up to the nearest 25 » | 0 0 1 0 0 0 2 | 3 | faible | Règle chiffrée et source unique. Volume faible. |
| 97 | Fed increase interest rates by 25 bps after the April 2027... | 0,260 / 0,280 | 500 / 5 | 23:01:24 | Texte identique au #89 | 0 0 1 0 0 0 2 | 3 | faible | Même lecture que le #89. |
| 98 | Bank of Japan make no change to the uncollateralized overni... | 0,480 / 0,500 | 500 / 5 | 23:01:27 | « Emergency changes to the specified rate not resulting from the specified meeting » | 0 0 1 0 0 0 2 | 3 | faible | Source officielle et arrondi écrit. Volume quasi nul, donc une erreur serait peu contestée. |
| 100 | ECB make no change to the deposit facility rate at the Marc... | 0,500 / 0,510 | 500 / 5 | 23:01:27 | « this market will resolve to the “No Change” bracket » | 0 0 1 0 0 0 2 | 3 | faible | Même modèle que le #98. Volume quasi nul. |
| 145 | Reserve Bank of New Zealand increase the official cash rate... | 0,500 / 0,510 | 500 / 5 | 23:01:27 | « scheduled for February 10, 2027 » | 0 0 1 0 0 0 2 | 3 | faible | Date locale de Nouvelle-Zélande contre date Gamma en UTC. Volume faible. |
| 155 | Reserve Bank of New Zealand make no change to the official... | 0,420 / 0,440 | 500 / 5 | 23:01:27 | Texte identique au #145 | 0 0 1 0 0 0 2 | 3 | faible | Même lecture que le #145. |

### 3.4 Technologie et entreprises

| # | Marché (question Gamma) | Bid / ask | Caution / récompense | Lu à (UTC) | Extrait des règles | F S A C L V M | Total | Niveau | Point d'attention |
|---|---|---|---|---|---|---|---|---|---|
| 17 | Anthropic announce bankruptcy by December 31, 2028 | 0,160 / 0,170 | 500 / 3.5 | 23:01:23 | « An announcement will suffice for a "Yes" resolution » | 1 1 1 1 1 1 2 | 8 | modéré | Texte long et précis, l'annonce suffit même sans dépôt. Conflit d'intérêts du rédacteur signalé au § 6. |
| 22 | JetBlue announce bankruptcy by December 31 | 0,087 / 0,091 | 500 / 5 | 23:01:24 | « Reports citing unnamed sources » | 1 1 1 1 1 1 1 | 7 | modéré | Même modèle que le #17. Le collecteur le classe en technologie à cause d'une étiquette Gamma. |
| 19 | US confirm that aliens exist before 2027 | 0,030 / 0,032 | 500 / 5 | 23:01:23 | « definitively states that extraterrestrial life or technology exists » | 3 2 1 2 2 2 2 | 14 | élevé | Toute agence fédérale suffit et « definitively » n'est pas défini. Un marché voisin sur les OVNI est passé au vote en mai 2026. |
| 20 | OpenAI announce another Millennium Prize solution by Decemb... | 0,540 / 0,550 | 500 / 5 | 23:01:23 | « No further confirmation from Clay Math Institute or any other organization is required » | 2 1 1 2 2 2 3 | 13 | élevé | Le fait qui compte est l'annonce et non la preuve. Rien n'est dit d'un retrait ultérieur. |
| 35 | Yang-Mills existence and mass gap problem be the next Mille... | 0,208 / 0,214 | 500 / 5 | 23:01:25 | « any other company with a model listed on the MMLU-pro leaderboard » | 2 2 1 2 2 2 3 | 14 | élevé | Liste de laboratoires mouvante selon un classement externe. Lié au #20 par la même annonce. |
| 59 | Perplexity launch a Muse-like personal agent before 2027 | 0,220 / 0,240 | 500 / 5 | 23:01:25 | « remains assigned to that user between tasks » | 3 2 1 2 2 2 2 | 14 | élevé | Définition par analogie et critères d'architecture difficiles à vérifier de l'extérieur. Échéance proche. |
| 68 | Anthropic's valuation hit (HIGH) $3.0T by December 31 | 0,200 / 0,210 | 500 / 5 | 23:01:25 | « as measured by the NPM Price reported by Nasdaq Private Market » | 1 2 1 1 1 1 2 | 9 | modéré | Source privée unique, page lue en statut HTTP 200 sans contrôle des chiffres. Replis écrits. Conflit d'intérêts signalé au § 6. |
| 77 | OpenAI's IPO valuation be between $1.25T and $1.5T | 0,212 / 0,216 | 500 / 5 | 23:01:25 | « this market will resolve to the lowest bracket » | 2 1 2 2 2 1 3 | 13 | élevé | Sans introduction en Bourse la tranche basse gagne, ce qui ne dit rien de la valorisation. « Fully diluted » suppose un calcul à partir du prospectus. |

### 3.5 Familles de marchés liés

| Famille | Marchés du registre | Effet d'un litige |
|---|---|---|
| Contrôle de la Chambre 2026 | #1 #3 #10 #2 #4 #5 et par le parti #14 | Un décompte de sièges commun, donc un désaccord peut s'étendre |
| Contrôle du Sénat 2026 | #8 #2 #4 #5 #9 #6 #7 #11 #13 #16 | Les courses d'État alimentent le contrôle et la combinaison du #9 |
| Présidentielle 2028 et nomination | #12 #23 #26 #18 #29 #30 | La nomination précède l'élection et les textes sont distincts |
| Annonces de résolution d'un problème du millénaire | #20 #35 | Une même annonce d'OpenAI peut toucher les deux avec des critères voisins |
| Fed et banques centrales | #48 #80 #58 #89 #97 puis #98 #100 #145 #155 chacune dans son événement | Tranches exclusives d'une même décision, mais fait public chiffré |
| Échéances d'un même événement | #17 #19 #20 sur plusieurs dates | Le précédent Iran montre une fermeture groupée |

### 3.6 Constats transverses

Aucune des 40 descriptions Gamma ne contient de clause à 50-50 (0 sur 40). Cette lecture ne porte que sur la description et elle a deux limites. La description peut manquer d'une clarification comme le montre un paragraphe plus bas. La doc garde aussi au vote une issue Unknown/50-50 (S1) que le code du contrat neg risk ne paraît pas accepter (S10, S11), et 6 marchés sur 40 restent hors `negRisk`. Ce 0 ne prouve donc pas qu'un 50-50 soit impossible. Les descriptions prévoient plutôt une issue par défaut. Il s'agit selon le cas de No ou de Other, de No change ou de la tranche basse. Ce choix réduit le risque d'annulation mais il peut changer le sens du pari, comme au #77 et au #9.

Le statut d'accès `restricted` vaut vrai sur 40 marchés sur 40. La doc le définit ainsi, « Market is geo-restricted for some jurisdictions » (S39). Il ne nomme aucune juridiction et il ne distingue aucun de nos marchés, donc l'accès depuis un pays donné se lit dans S35. Le champ `new_version_q` vaut vrai sur 40 marchés sur 40 et sur 730 états sur 737. Il ne distingue donc rien et nous ne l'utilisons pas, malgré sa définition de règles mises à jour après la pose (S14).

La description Gamma peut ne pas contenir une clarification publiée ailleurs. Le cas MicroStrategy le montre, car la note du 01/06 citée par S15 n'y figure pas. Une lecture de Gamma ne suffit donc jamais seule. Il faut aussi lire la page du marché et le contrat bulletin board avant toute décision.

Sur les petits marchés une erreur peut passer faute de contestation si la caution dépasse l'enjeu. Le volume cumulé ne mesure pas cet enjeu, donc nous comparons la caution à l'intérêt ouvert lu sur `/oi` le 01/11/2026 à 00:21 UTC (S40). Nous supposons la même unité des deux côtés [non vérifié]. La caution dépasse l'intérêt ouvert sur 4 marchés sur 40, soit #98 13 $ pour 500 ; #100 45 $ pour 500 ; #145 251 $ pour 500 ; #61 665 $ pour 10000. Cet intérêt ouvert change d'une heure à l'autre et il ne compte pas ce que des parieurs pourraient encore engager. Une caution supérieure à l'intérêt ouvert ne dit rien de la qualité du texte, qui se lit au tableau.

## 4. Cadre juridique

Cette grille n'est pas un avis juridique. Un conseil local reste à consulter avant tout usage de Polymarket depuis les Émirats. Le statut ci-dessous est celui que nous avons pu vérifier le 31/10/2026, et nous n'avons trouvé aucune décision ni aucun texte qui vise les marchés de prédiction aux Émirats.

### 4.1 Position retenue par le dépôt

La note de régime v3 indique une résidence de Jonathan aux Émirats confirmée le 31/10, un accès ouvert et une zone grise à risque faible et non nul. Nous conservons cette prudence. Nous ajoutons une réserve sur le mot « faible », car il repose sur l'absence de cas connu et non sur un texte. La sanction possible n'est pas faible si le droit pénal s'applique. Aucune de nos sources ne permet de chiffrer la probabilité d'une poursuite.

### 4.2 Faits vérifiés

| Point | Constat | Source, date | Solidité |
|---|---|---|---|
| Liste de blocage Polymarket | Les Émirats ne figurent dans aucune liste de blocage ou de restriction | S35, lu le 31/10/2026, page sans date | Officielle côté plateforme. La liste peut changer sans préavis (S36) |
| Conditions de Polymarket | L'utilisateur déclare respecter sa loi locale. Le VPN de contournement est interdit. Droit panaméen et arbitrage individuel | S36, en vigueur le 11/08/2026 | Officielle côté plateforme |
| Accès réel depuis les Émirats | Non testé depuis cette session | Aucun | [Non vérifié] |
| Infraction de jeu | Le code pénal (décret-loi fédéral 31/2021, art. 460 à 463) définit le jeu d'argent. Il prévoit pour le joueur jusqu'à 2 ans de prison ou 50 000 AED d'amende | S27 du 07/09/2023, S28 du 27/01/2025 | Résumés de cabinets. Journal officiel non lu |
| Sites en ligne | La loi cyber 34/2021, art. 38, vise ceux qui créent ou gèrent des sites de jeu non autorisé | S27. Une source citait l'art. 17 [contradiction relevée] | Résumé de cabinet |
| Autorité | La GCGRA est le régulateur fédéral. Un cabinet écrit que jouer via un opérateur non licencié est illégal | S28 | Avis de cabinet |
| Avis de décembre 2024 | La GCGRA a averti que les joueurs d'opérateurs non licenciés s'exposent à des poursuites et n'ont aucun recours en cas de non-paiement | S30 du 09/12/2024, S31 du 20/12/2024 | Presse citant l'autorité. Vise surtout loteries et jeux. Site de la GCGRA non lu (HTTP 403) |
| Droit civil | Le décret-loi 25/2025, en vigueur le 01/06/2026, ne reprend pas les articles du jeu de l'ancien code civil. Aucun changement pénal adopté n'est décrit | S29 du 20/01/2026 | Note de cabinet |
| Marchés de prédiction | Ni GCGRA ni VARA ni ADGM n'ont pris position d'après des guides. Nous n'avons trouvé aucune publication officielle qui le confirme | S33 du 07/08/2026, S34 du 16/04/2026 | Sites commerciaux, intérêt d'affiliation possible pour S34 |
| Application aux joueurs | Aucun cas nommé trouvé. S32 décrit des procédures contre les opérateurs et aucun cas visant un joueur | S32 du 21/08/2026 | L'absence de cas trouvé ne prouve pas l'absence de cas |
| Fiscalité | Des guides évoquent 0 % sur les gains | S33 | [Non vérifié, à confirmer avec un fiscaliste] |

### 4.3 Participants et pays de résidence

Seule la résidence de Jonathan est confirmée. Sa résidence fiscale reste à inscrire dans `commun-trading` (note de régime, § 6). Polymarket est bloqué en France par décision de l'ANJ du 16/07/2026, contestée en justice par la plateforme (`2026-10-31_SQD_RENTABILITE_INTEGRATION.md`, § 0.1). La documentation de la plateforme classe la France en fermeture de positions seulement (S35). Cette limite concerne tout participant selon son pays de résidence, et donc toute personne du projet qui réside en France. Le même document situe la session de travail en France. Depuis ce lieu le système lit seulement des données publiques et il ne propose aucun contournement.

### 4.4 Questions à poser au conseil local

| Question | Pourquoi |
|---|---|
| Un contrat d'événement entre-t-il dans la définition du jeu de l'art. 460 ? | La définition résumée vise un perdant qui paie un gagnant, ce qui peut couvrir ce produit |
| L'avis GCGRA de 2024 s'applique-t-il hors loteries et casinos ? | Il vise les opérateurs non licenciés sans parler de prédiction |
| Le fait de tenir un rôle de maker change-t-il la qualification ? | Le moteur B fournit de la liquidité, ce qui peut ressembler à une organisation aux yeux d'un juge |
| Les règles VARA s'appliquent-elles à un usage personnel avec pUSD ? | Polymarket n'a pas de licence VARA d'après S33 |
| Quel recours existe en cas de résolution contestée ? | Arbitrage individuel sous droit panaméen selon S36 et procédure UMA distincte |
| Quel traitement fiscal et bancaire pour les flux ? | Les guides restent sans source officielle |

## 5. Mode d'emploi

Pour un nouveau marché, nous relisons la règle sur Gamma avec `extraire_clauses.py`, puis la page du marché et ses clarifications. Nous posons ensuite les sept notes et nous inscrivons l'extrait, l'heure de lecture et la caution dans ce registre. Un marché noté 3 en F, S ou L passe par `avocat-du-diable` avant toute fiche. Nous relisons les notes de ce registre après la vague du 03/11 en comparant les notes aux litiges réels, ce qui donnera une première mesure de la grille.

Commande utilisée pour ce registre.

`extraire_clauses.py --prefixe 20261031T224031Z --delais`, puis `genere_registre.py`.

## 6. Limites

Le classement des 40 marchés vient d'un passage unique du collecteur et il change d'un passage à l'autre. Les numéros # renvoient au passage `20261031T224031Z`. Les filtres corrigés le 01/11 ne changent aucun de ces 40 marchés quand on les applique à ce passage (contrôle sur son fichier `_candidats_classes.csv`). Le collecteur relancé le 01/11/2026 à 00:13 UTC (préfixe `20261101T001303Z`) retient 33 de ces 40 marchés, dont 15 des 20 du classement. Les 7 autres de ce nouveau passage ne sont pas notés ici et cet écart ne vient pas des filtres. Les notes sont le jugement d'un seul rédacteur sans double lecture. L'échantillon de délais dépend d'un plafond d'API de 2 100 lignes par étiquette (4 réponses HTTP 422 à l'offset 2 100) et d'un tri par volume, donc il surreprésente les gros marchés. Il filtre sur la date de fin Gamma et il manque les marchés clos tôt dont la date de fin sort de la fenêtre. Le champ Gamma `umaResolutionStatuses` contient des doublons et il n'est pas documenté à notre connaissance. Nous ne l'utilisons que comme indice de contestation.

Aucune mesure ne porte sur l'heure de la première proposition. Le délai du litige seul n'est donc pas isolé. Le code lu pour les contrats est celui de la branche principale sur GitHub et non celui déployé à une adresse vérifiée. Les valeurs GAT, SPAT et les pénalités sont données par la documentation au lancement de DVM 2.0 et peuvent avoir changé [à vérifier]. Les articles du WSJ et de Bloomberg n'ont pas été lus directement. Le contrat bulletin board n'a pas été lu.

Conflit d'intérêts signalé. Ce registre est rédigé par Claude, un modèle d'Anthropic. Les #17 et #68 portent sur Anthropic, et les #20, #35 et #77 concernent un concurrent. Les notes de ces marchés ne portent que sur le texte des règles, et aucune ne donne d'avis sur l'issue.

## 7. Sources

Toutes les pages ci-dessous ont été lues le 31/10/2026, sauf mention. La ligne Unknown/50-50 de S1 a été relue le 01/11/2026. Les citations de presse sont reformulées.

| Réf. | Source | Date de la page | Nature |
|---|---|---|---|
| S1 | https://docs.polymarket.com/concepts/resolution | Sans date | Officielle Polymarket |
| S2 | https://docs.uma.xyz/protocol-overview/how-does-umas-oracle-work | Sans date | Officielle UMA |
| S3 | https://docs.uma.xyz/using-uma/voting-walkthrough | Sans date | Officielle UMA |
| S4 | https://docs.uma.xyz/using-uma/voting-walkthrough/dvm-2.0.md | Sans date | Officielle UMA |
| S5 | https://docs.uma.xyz/using-uma/voting-walkthrough/dvm-2.0-faq.md | Sans date | Officielle UMA |
| S6 | https://docs.uma.xyz/using-uma/default-proposer-whitelist | Sans date | Officielle UMA |
| S7 | https://blog.uma.xyz/articles/managed-proposers | 12/08/2025 | Officielle UMA |
| S8 | https://www.theblock.co/post/366507/polymarket-uma-oracle-update | 12/08/2025 | Presse |
| S9 | https://raw.githubusercontent.com/Polymarket/uma-ctf-adapter/main/README.md | Branche principale | Code public |
| S10 | https://raw.githubusercontent.com/Polymarket/uma-ctf-adapter/main/src/UmaCtfAdapter.sol | Branche principale | Code public |
| S11 | https://raw.githubusercontent.com/Polymarket/neg-risk-ctf-adapter/main/src/NegRiskOperator.sol | Branche principale | Code public |
| S12 | https://docs.polymarket.com/resources/contracts | Sans date, audits cités de juillet 2026 | Officielle Polymarket |
| S13 | https://docs.polymarket.com/changelog | Entrées de 2026 | Officielle Polymarket |
| S14 | https://data-api.polymarket.com/v2/openapi.json | Lu le 31/10/2026 | Officielle Polymarket |
| S15 | https://www.theblock.co/post/403600/polymarket-upholds-no-outcome-strategy-bitcoin-sale-market | 04/06/2026 | Presse |
| S16 | https://www.coindesk.com/markets/2026/06/04/polymarket-says-no-for-may-yes-for-june-after-strategy-s-recent-bitcoin-sale | 04/06/2026 | Presse |
| S17 | https://thenextweb.com/news/polymarket-345-million-iran-peace-deal-dispute-uma-whale-voting | 15/06/2026 | Presse citant Bloomberg |
| S18 | https://www.theblock.co/post/405117/trump-comments-fuel-dispute-over-polymarkets-120-million-permanent-iran-peace-deal-market | 17/06/2026 | Presse |
| S19 | https://www.ynetnews.com/business/article/b1ajjg97gx | [Date non relevée] | Presse, chiffres de source unique |
| S20 | https://www.financemagnates.com/fintech/polymarkets-arbitration-model-faces-conflict-of-interest-questions/ | 19/05/2026 | Presse citant le WSJ |
| S21 | https://cryptobriefing.com/polymarket-whale-voting-dispute-delays/ | 26/05/2026 | Presse citant le WSJ |
| S22 | https://gamma-api.polymarket.com/markets | Lu de 2026-10-31T23:01:20Z à 2026-10-31T23:02:11Z | API publique |
| S23 | https://www.pbs.org/newshour/politics/when-will-we-know-2026-midterm-election-results-it-may-take-some-time-but-thats-normal | [Date non relevée], avant le scrutin | Presse |
| S24 | https://news.kalshi.com/p/midterm-election-results-2026 | 23/10/2026 | Opérateur concurrent, à croiser |
| S25 | https://alaskapublic.org/news/politics/elections/2026-10-27/state-of-alaska-says-doj-lawsuit-over-senate-race-has-no-legal-basis | 27/10/2026 | Presse |
| S26 | https://www.venable.com/insights/publications/2026/07/count-the-votes-supreme-court-holds-states | 17/07/2026 | Note de cabinet |
| S27 | https://jdsupra.com/legalnews/uae-s-gambling-laws-prohibition-7827798 | 07/09/2023 | Note de cabinet |
| S28 | https://www.legal500.com/intelligence/united-arab-emirates/media-telecoms-it-entertainment/betting-on-change-the-uae-rolls-on-new-regulator-for-gaming-licences | 27/01/2025 | Note de cabinet |
| S29 | https://www.gtlaw.com/en/insights/2026/01/uae-civil-code-gambling-provisions-removed | 20/01/2026 | Note de cabinet |
| S30 | https://gulfnews.com/uae/people/uae-authorities-warn-of-risks-from-unlicensed-lottery-and-gaming-activities-1.104871831 | 09/12/2024 | Presse citant la GCGRA |
| S31 | https://thelawreporters.com/uae-residents-warned-no-legal-protection-for-unlicensed-gambling | 20/12/2024 | Presse citant la GCGRA |
| S32 | https://globallawexperts.com/gcgra-enforcement-uae/ | 21/08/2026 | Note de cabinet |
| S33 | https://nextpredict.io/legal/uae/ | 07/08/2026 | Site commercial |
| S34 | https://predictionmarkets101.com/countries/united-arab-emirates | 16/04/2026 | Site d'affiliation |
| S35 | https://docs.polymarket.com/polymarket-learn/FAQ/geoblocking | Sans date | Officielle Polymarket |
| S36 | https://polymarket.com/tos | En vigueur le 11/08/2026 | Officielle Polymarket |
| S37 | https://data-api.polymarket.com/v2/resolutions | Clauses lues de 2026-10-31T23:01:20Z à 2026-10-31T23:01:28Z, précédents relus le 01/11/2026 00:21 UTC | API publique |
| S38 | `2026-10-31_RADIOGRAPHIE_ET_AUDIT.md` ; `2026-10-31_SQD_RENTABILITE_INTEGRATION.md` ; `NOTE_STRATEGIE_ET_REGIME.md` ; `polymarket/resultats/20261031T224031Z_rapport.md` ; `polymarket/resultats/20261101T001303Z_rapport.md` | 31/10/2026 et 01/11/2026 | Dépôt |
| S39 | https://docs.polymarket.com/market-data/market-details.md | Sans date, lu le 01/11/2026 | Officielle Polymarket |
| S40 | https://data-api.polymarket.com/oi | Lu le 01/11/2026 00:21 UTC, valeur courante seulement | API publique |

Lacunes d'accès. Le site de la GCGRA, l'article d'ASGAM sur son avis et une page de Cryptoslate ont répondu HTTP 403. L'article de The Defiant sur le marché Zelensky n'a pas chargé. Une page d'Orrery et une URL de Finance Magnates ont répondu HTTP 404. Le fichier collecteur reste la source de son propre classement.
