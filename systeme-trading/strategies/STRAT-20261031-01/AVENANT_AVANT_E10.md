# Avenant avant E10 de STRAT-20261031-01

Statut : proposé, à valider par Jonathan avant E10.

Rédigé le 01/11/2026. Résultats de recherche, aucune promesse de gain, aucune recommandation. Rien dans cet avenant n'est appliqué à la stratégie. `TrendDonchianV1.py`, `config_strat01.json` et la fiche restent intacts, le statut reste `backtest` et `dry_run` reste à true. E10 et E11 n'ont pas été lancés.

## 1. Objet

Les relectures contradictoires du 01/11/2026 ont montré que la lecture de E10 dépendait de choix qui n'étaient écrits nulle part. La fiche parle d'une borne de l'intervalle à 90 % sans dire laquelle. Elle annonce 5 paramètres libres alors que l'ordre de la whitelist en constitue un sixième. Cet avenant fixe ces choix tant que le hors échantillon reste fermé. Il ne change aucune règle d'entrée ou de sortie, aucun paramètre et aucune période. Les chiffres cités portent sur le développement et la validation, ils sont indicatifs et n'annoncent rien sur E10.

Le détail et les sources sont dans `resultats/RAPPORT_E01_E09.md`. Le registre ne reçoit aucune nouvelle ligne d'essai au titre de cet avenant.

## 2. Ordre de la whitelist déclaré comme règle de priorité

Quand les signaux du jour dépassent les places libres, freqtrade sert d'abord les paires déjà en position puis les autres dans l'ordre de `pair_whitelist`. Nous proposons de déclarer cet ordre comme une règle de priorité et comme un sixième paramètre libre. L'ordre figé est celui de la configuration actuelle, soit dans cet ordre BTC ETH XRP LTC BCH LINK ADA BNB DOGE TRX. Aucun ordre n'a été cherché ni retenu pour sa performance, et aucun ne le sera.

Cet ordre pèse beaucoup. En rejeu simulé sur 200 ordres tirés avec la graine 0, l'espérance de E01 va de +0,011 à +0,468 R avec 53,5 % des ordres à 0,2 R ou moins. Celle de E00-ref va de +0,175 à +0,528 R. Avec le vrai freqtrade, E00-ref donne +2 461 USDT dans l'ordre de la configuration, +3 662 USDT dans l'ordre inverse et +4 698 USDT dans l'ordre alphabétique. La base se situe plutôt sous la médiane, donc le problème est l'instabilité et non un biais flatteur.

## 3. Méthode de l'intervalle à 90 % et graine

Nous proposons de lire le critère de la fiche sur l'intervalle par blocs. La méthode est un bootstrap par blocs circulaires de 10 trades consécutifs dans l'ordre d'ouverture, sur le R nominal, avec 50 000 tirages et la graine 20261101. Les bornes sont les centiles 5 et 95. La borne basse de cette méthode décide du critère « borne basse de l'intervalle à 90 % ≤ 0 ». La graine ne se change pas après coup et le tirage ne se relance pas.

L'intervalle iid (5000 tirages et graine 0, puis 50 000 tirages) et les intervalles par épisodes et par mois restent affichés à titre de comparaison et ne décident de rien. Si les méthodes divergent sur le signe, le rapport le dira et la méthode par blocs tranchera.

Ce choix vient de trois constats. La borne iid a un bruit de graine du même ordre que sa distance à zéro sur E00-ref, où 70 % des graines de 5000 tirages donnent une borne positive. Presque tous les trades en chevauchent un autre, ce que l'iid ignore. La forme circulaire donne le même poids aux premiers et aux derniers trades, contrairement aux blocs mobiles sans repli. Sur 20 graines à 50 000 tirages, la borne basse de E00-ref a un écart-type de 0,0016. Le signe de la borne ne change pas avec des blocs de 5 ou 20 trades sur les sept essais contrôlés.

| Essai | Borne basse iid à 50 000 tirages | Blocs de 5 trades | Blocs de 10 trades | Blocs de 20 trades |
|---|---:|---:|---:|---:|
| E00-ref | +0,002 | -0,030 | -0,035 | -0,024 |
| E01 | -0,116 | -0,136 | -0,132 | -0,125 |
| E02 | -0,104 | -0,190 | -0,167 | -0,097 |
| E05 | +0,012 | -0,024 | -0,030 | -0,026 |
| E07 | +0,198 | +0,127 | +0,070 | +0,041 |
| E08 | -0,000 | -0,028 | -0,023 | -0,006 |
| E09 | -0,007 | -0,039 | -0,044 | -0,033 |

Il faut en connaître le prix. La méthode est le plus souvent plus sévère que l'iid et elle a été choisie en connaissant ces chiffres de développement et de validation, sans connaître E10. Avec 30 à 50 trades hors échantillon, elle ne tirera que 3 à 5 blocs par séquence et l'intervalle sera large (-0,167 à +1,552 R sur les 46 trades de E02). Le critère de la borne basse sera donc difficile à franchir, et un échec de ce seul critère pourra venir du faible nombre de trades. Il reste un échec selon la fiche.

## 4. Base de lecture du drawdown et série principale du DSR

Le critère de drawdown de la fiche se lit sur l'équité réévaluée chaque jour au prix de clôture 1d, avec le seuil de 20 % inchangé. Le drawdown réalisé reste affiché en second. Les DD95 par permutation et par blocs servent seulement de lecture de la dispersion.

La série principale du DSR est la série réévaluée, avec une V[SR] réévaluée. Le DSR sur série réalisée reste affiché en second, car il n'est pas comparable d'un essai à l'autre. N vaut 15 pour E10 et E11, soit les 13 essais déjà lancés plus ces deux lignes. N = 21 ajoute les 6 contrôles de format et N = 28 ajoute aussi les 7 backtests du contradicteur, à titre de sensibilité. V ne peut pas être tranchée sur la fenêtre de E10 sans lancer des variantes dans le hors échantillon, ce que nous excluons. La V principale est donc la V réévaluée de 1,519e-04 mise à l'échelle par 1673 / 457, soit 5,561e-04. La V commune et V = 1/T restent en sensibilité.

Le seuil proposé est 0,95, le seuil conventionnel, en seuil de lecture et non en critère éliminatoire. Le critère du § 5 de `validation-edge` reste le Sharpe hors échantillon comparé au repère du nombre d'essais. Le Sharpe retenu pour ce critère est le Sharpe réévalué. Le tableau suivant, calculé sans aucune donnée du hors échantillon sur T = 457 jours, montre pourquoi. Atteindre 0,95 demanderait un Sharpe annualisé d'environ 2,3 sous hypothèse normale, ce qui en ferait un filtre presque impossible sur 457 jours. Si Jonathan veut en faire un critère éliminatoire, il doit le décider maintenant.

| N | Repère de Sharpe annuel du § 4.3 | SR0 annualisé, V mise à l'échelle | Sharpe requis pour DSR 0,95, V mise à l'échelle | Sharpe requis pour DSR 0,95, V commune | Sharpe requis pour DSR 0,95, V = 1/T |
|---:|---:|---:|---:|---:|---:|
| 15 | 1,58 | 0,80 | 2,27 | 1,89 | 3,06 |
| 21 | 1,72 | 0,87 | 2,34 | 1,93 | 3,20 |
| 28 | 1,83 | 0,92 | 2,40 | 1,96 | 3,31 |

## 5. Présentation de E10

Le verdict porte sur l'ordre figé et sur lui seul. Il s'écrit et se date d'abord, à partir de l'unique run de E10 puis de E11. Il donne les chiffres réévalués et l'intervalle par blocs, ainsi que l'espérance hors force_exit.

Une fois ce verdict figé, E10 sera présenté avec la distribution des 200 ordres à titre de lecture, en indiquant où se situe l'ordre figé dans cette distribution. Ces rejeux simulés relisent les données du hors échantillon alors que la règle veut une seule ouverture. Ils sont donc annoncés ici, hors N, et ils ne peuvent ni modifier le verdict ni faire retenir un autre ordre. Jonathan peut aussi décider de ne pas les lancer. Le script est `resultats/controles/t5_permutations_ordre_places_strictes.py`, avec la même graine 0.

La sensibilité à la règle stricte d'attribution des places sera donnée de la même façon, comme sensibilité seulement.

## 6. Régime connu des auteurs

E10 n'est pas un hors échantillon totalement aveugle. La fiche écrite avant test (§ 4 point 2) cite déjà une baisse avec rebonds sur la période, dont un mouvement d'environ +21 % mi-2026 lu sur une série CoinGecko. Les données de backtest du bloc n'ont pas été lues et les paramètres sont classiques et figés, donc l'effet paraît limité sans pouvoir être exclu. Le rapport de verdict le dira dans ses premières lignes.

## 7. Correctif de stop à enregistrer avant le papier

Le backtest et le mode papier divergent sur le stop. Dans `_atr_at_entry`, le filtre `date < open_date` exclut la bougie d'entrée en backtest, où open_date vaut 00:00:00. En papier, open_date vaut quelques secondes après minuit, et la bougie d'entrée passe le filtre dès le lendemain. Le stop peut alors se resserrer, jamais s'élargir. Par rejeu, 53 trades sur 135 de E01 et 70 sur 178 de E00-ref seraient touchés, avec une médiane de 1,5 % de la distance et 6 et 7 sorties modifiées [estimation, mode papier non exécuté].

Nous proposons un correctif qui compare à la date de la bougie d'entrée, sans changer aucun paramètre. Il sera enregistré comme nouvel essai au registre avant le papier [identifiant à attribuer] et ne touche ni E10 ni E11, qui tournent sur le fichier figé actuel. Le traitement des entrées en cours de bougie se décide au même moment, car une entrée réelle se ferait plus tard que l'ouverture [déduit du code, non observé]. Toute modification de ce point sera aussi un nouvel essai.

## 8. Décisions demandées à Jonathan

| Point | Proposition | Décision |
|---|---|---|
| Ordre de la whitelist | Ordre actuel figé, déclaré comme règle de priorité et sixième paramètre libre | [à valider] |
| Intervalle à 90 % | Blocs circulaires de 10 trades, 50 000 tirages, graine 20261101, iid en comparaison | [à valider] |
| Drawdown du critère | Équité réévaluée, seuil de 20 % inchangé | [à valider] |
| DSR | Série réévaluée, N = 15, V réévaluée mise à l'échelle, seuil de lecture 0,95 non éliminatoire | [à valider] |
| Sharpe du § 5 | Sharpe réévalué comparé au repère pour N = 15 et T = 457 jours | [à valider] |
| Permutations d'ordre | Lancées après le verdict, à titre de lecture et hors N | [à valider] |
| Régime connu | Signalé dans le verdict, E10 non présenté comme aveugle | [à valider] |
| Correctif de stop | Nouvel essai avant le papier, aucun effet sur E10 et E11 | [à valider] |
| Biais de sélection de l'univers | DOGE et TRX n'étaient pas parmi les plus liquides fin 2020 ([rangs 42 et 19], `resultats/RAPPORT_E01_E09.md`). L'univers figé reste inchangé. Le point est porté à `avocat-du-diable` avant le verdict, avec l'ordre de la whitelist et l'attribution des places | [à valider] |
| Calcul de V pour le DSR | Seuls `resultats/brut/registre_dsr.py` et `--sr-var-reevalue` font foi. Le mode `--agreger-registre` inclut E01 et E02 dans V et compte E10 et E11 dans N, il donne donc une autre valeur | [à valider] |

Le téléchargement des données d'août 2025 à octobre 2026 n'aura lieu qu'après cette validation. Une validation partielle laisse E10 fermé sur les points restants.

Sources : `resultats/RAPPORT_E01_E09.md`, `resultats/controles/sorties/ic_sensibilite.json`, `resultats/controles/sorties/t5_resume.json`, `resultats/controles/sorties/avenant_reperes.json`, exports freqtrade 2026.10 du 31/10/2026. Toutes ces sorties ont été exécutées le 01/11/2026, sauf les backtests freqtrade réels de l'ordre (2026-10-31 entre 23:50Z et 23:52Z).
