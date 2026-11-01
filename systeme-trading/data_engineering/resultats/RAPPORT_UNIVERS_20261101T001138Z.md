# Rapport d'univers des perpétuels USDT, collecte du 01/11/2026

Document de recherche. Aucune recommandation d'investissement et aucune promesse de gain. Aucune stratégie ne change de statut. dry_run reste true.

Ce rapport remplace RAPPORT_UNIVERS_20261031T224232Z.md, qui reste en place et marqué remplacé. Le panier est figé par son horodatage 20261101T001138Z. Une relance crée d'autres fichiers et ne le remplace pas.

## 1. Biais à lire d'abord

Le classement d'aujourd'hui appliqué à 2021-2024 est un biais d'anticipation et du survivant. Seuls les gagnants actuels y figurent et les jetons morts manquent. Ce panier ne remplace donc PAS l'univers figé de STRAT-20261031-01. Il sert aux recherches futures. Toute stratégie testée dessus doit porter ce biais ou utiliser un univers reconstruit à la date.

La règle des 180 jours de cotation avant le 30/06/2024 aggrave ce biais. Elle choisit des paires pour leur présence dans une fenêtre passée, à partir d'un classement connu seulement en 2026.

Instantanés pris un week-end. Les six instantanés retenus tombent un dimanche UTC, de 00:17:45 à 00:31:49. Ceux de l'ancien panier tombaient un samedi soir et ceux du contrôle un dimanche matin. Aucune mesure n'a donc été prise en semaine ni sur plusieurs jours, et le glissement comme l'écart peuvent différer en heures ouvrées. Le volume confirme cette période creuse, car BTC a traité 4,0 G USDT le 31/10 contre une médiane de 10,5 G.

Alerte en cours. Piratage Binance fin octobre 2026 et retraits suspendus, reprise annoncée le 01/11, selon NOTE_STRATEGIE_ET_REGIME.md (information non revérifiée ici). Les données publiques restent lisibles mais ne préjugent pas d'une exécution sur cette plateforme.

## 2. Ce qui a été exécuté

Toutes les heures sont en UTC, le 01/11/2026.

| Étape | Heure UTC | Résultat |
|---|---|---|
| Collecte complète retenue, règle U03, 1 503 appels HTTP | 00:11:38 à 00:32:07 | Terminée. 2 incidents réseau repris (Binance 00:12:57, Bybit 00:15:35). Aucune erreur de collecte |
| Téléchargement freqtrade des 4 paires nouvelles | 00:33 à 00:34 | AVAX, BCH, FIL et QNT, 12 fichiers. Le journal montre 4 sur 4 sans erreur. Le code de sortie n'y est pas consigné |
| Contrôle et coupe par verifier_donnees_panier.py | 00:34 | 12 fichiers coupés au 30/06/2024, aucun trou détecté |
| Rejeu des deux collectes avec le script final, hors dépôt | 07:53 | Collecte retenue, 6 fichiers de sortie identiques octet par octet. Ancienne collecte, panier de 13 paires identique |
| Contrôle indépendant des fichiers feather | Vers 07:55 | 51 fichiers et 17 paires. Aucun dépassement du 30/06/2024 et aucun trou |
| Collecte de contrôle complète, hors dépôt, 1 548 appels HTTP | 07:53:55 à 08:13:12 | Aucun incident HTTP. Elle ne remplace pas le panier (voir § 5) |
| Stabilité du top 30 sur 14 jours, stabilite_top30.py, 513 appels HTTP | 08:13:52 à 08:16:12 | Aucune erreur (voir § 5) |

La collecte retenue et le téléchargement viennent d'une passe précédente de ce même travail, arrêtée avant le rapport. Ils n'ont pas été refaits, car une nouvelle collecte aurait créé un autre panier. Ils ont été contrôlés par le rejeu et par la lecture directe des fichiers.

Toute modification de règle est déclarée dans REGISTRE_ESSAIS_UNIVERS.csv. Le changement de cette version est l'essai U03. L'entrée au top 30 se fait sur le volume médian à 30 jours de bougies 1 j closes, au lieu du volume 24 h. Le volume 24 h reste affiché et sert encore à la règle de pointe. Les pondérations, les seuils et le plafond de 15 paires ne changent pas.

## 3. Panier retenu, 15 paires

Sources : Binance /fapi/v1/klines, /fapi/v1/depth, /fapi/v1/fundingRate, Bybit /v5/market/orderbook, collecte du 01/11/2026 de 00:11 à 00:32 UTC.

| Paire | Rang score | Score | Rang vol. médian | Vol. médian 30 j (M USDT) | Rang vol. 24 h | Vol. 24 h (M USDT) | Gliss. 50k Binance (bps) | Gliss. 50k Bybit (bps) | Financement annualisé 1 an (%) | Part négative (%) | Corr. BTC 180 j | Bêta BTC 180 j |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTC | 1 | 83,6 | 1 | 10 536 | 1 | 3 913 | 0,01 | 0,01 | 3,47 | 22,7 | 1,00 | 1,00 |
| ETH | 2 | 83,3 | 2 | 7 152 | 2 | 2 155 | 0,02 | 0,02 | 2,50 | 26,5 | 0,89 | 1,23 |
| SOL | 4 | 73,3 | 4 | 1 468 | 5 | 614 | 0,52 | 0,60 | -0,30 | 44,7 | 0,84 | 1,27 |
| ZEC | 5 | 70,4 | 3 | 1 668 | 3 | 953 | 1,46 | 2,58 | -7,17 | 38,0 | 0,51 | 1,83 |
| BNB | 6 | 69,6 | 9 | 281 | 10 | 257 | 0,43 | 1,25 | 2,53 | 1,2 | 0,72 | 0,80 |
| DOGE | 7 | 64,0 | 8 | 315 | 17 | 131 | 1,12 | 1,40 | 3,09 | 31,3 | 0,81 | 1,26 |
| NEAR | 8 | 63,1 | 5 | 667 | 9 | 328 | 2,36 | 2,75 | 3,71 | 26,6 | 0,39 | 1,25 |
| AVAX | 10 | 55,8 | 19 | 129 | 40 | 51 | 3,57 | 3,53 | -0,19 | 39,7 | 0,59 | 1,15 |
| SUI | 12 | 53,6 | 13 | 224 | 26 | 76 | 2,43 | 2,27 | 3,14 | 29,9 | 0,68 | 1,53 |
| LINK | 13 | 53,2 | 22 | 109 | 20 | 119 | 2,16 | 2,32 | 4,63 | 20,8 | 0,73 | 1,27 |
| BCH | 15 | 47,7 | 30 | 75 | 42 | 49 | 3,96 | 6,41 | -3,76 | 52,3 | 0,65 | 1,50 |
| UNI | 17 | 46,7 | 15 | 199 | 18 | 125 | 4,45 | 6,03 | 4,45 | 22,6 | 0,53 | 1,33 |
| FIL | 18 | 46,6 | 18 | 129 | 49 | 39 | 4,73 | 17,65 | -1,68 | 38,4 | 0,49 | 1,24 |
| WLD | 19 | 45,7 | 11 | 268 | 24 | 82 | 4,49 | 4,94 | -5,92 | 47,3 | 0,32 | 1,20 |
| QNT | 21 | 42,9 | 23 | 105 | 29 | 68 | 8,51 | 37,27 | -1,28 | 40,6 | 0,20 | 0,75 |

Le glissement est la médiane des six instantanés, moyenne de l'achat et de la vente, contre le prix médian du carnet et hors frais. Le pire instantané du panier reste à 13,14 bps (achat QNT, CSV). Le score est un rang relatif parmi les 30 paires classées, donc il ne se compare pas d'une règle à l'autre.

Corrélation entre paires du panier sur 180 jours, médiane 0,53, minimum 0,17, maximum 0,89 (BTC et ETH, exemptées du plafond). Le plafond de 0,85 a suffi et n'a pas été assoupli. Ce niveau n'empêche pas un risque commun, car le bêta à BTC dépasse 1 pour 12 paires sur 14 hors BTC. BTC contre lui-même vaut 1 par construction et n'est pas compté. BNB (0,80) et QNT (0,75) restent sous 1.

Recouvrement avec l'univers figé de STRAT-01. BTC, ETH, BNB, DOGE, LINK et BCH figurent dans les deux. Cet univers n'est pas modifié.

Décisions fragiles à connaître. Le plafond de 15 paires joue pour la première fois. AAVE, ARB, INJ et TIA sont éligibles mais écartées par lui seul. La dernière entrée QNT a un score de 42,9 contre 42,1 pour AAVE. La corrélation DOGE et 1000PEPE vaut 0,8501 pour un plafond de 0,85, et si 1000PEPE revenait elle prendrait une place et QNT sortirait. BCH occupe le rang 30 du volume médian avec 75,2 M USDT contre 71,7 M pour LTC au rang 31. ADA (rang score 14) est écartée pour un écart de 5,19 bps et un seuil de 5, et son retour prendrait aussi une place. SOL est à 0,840 avec BTC et XRP est écarté à 0,869 avec BTC.

QNT et FIL offrent un repli faible. Leur glissement à 50 000 USDT chez Bybit vaut 37,27 et 17,65 bps, or la règle du panier ne fixe aucun seuil sur Bybit. QNT a aussi le glissement Binance le plus élevé du panier (8,51 bps).

Écartées par la règle de cotation avant le 30/06/2024 alors qu'elles sont liquides aujourd'hui, HYPE (rang 9), ENA (rang 11) et TAO (rang 20).

## 4. Comparaison de l'ancien et du nouveau panier

L'ancien panier vient de la collecte 20261031T224232Z et de la règle sur 24 h. Le nouveau vient de la collecte 20261101T001138Z et de la règle médiane. Le témoin rejoue l'ancienne règle sur la nouvelle collecte, ce qui sépare les deux causes de changement.

| Paire | Ancien panier 22:42 | Rang score ancien | Témoin 24 h 00:11 | Nouveau panier 00:11 | Rang score nouveau | Motif |
|---|---|---|---|---|---|---|
| BTC | oui | 1 | oui | oui | 1 | Inchangée |
| ETH | oui | 2 | oui | oui | 2 | Inchangée |
| SOL | oui | 4 | oui | oui | 4 | Inchangée |
| ZEC | oui | 5 | oui | oui | 5 | Inchangée |
| BNB | oui | 6 | oui | oui | 6 | Inchangée |
| DOGE | oui | 7 | oui | oui | 7 | Inchangée |
| NEAR | oui | 8 | oui | oui | 8 | Inchangée |
| AVAX | non | hors top 30 | non | oui | 10 | Entre par la nouvelle règle. Rang 40 au volume 24 h et 19 au volume médian |
| SUI | oui | 12 | oui | oui | 12 | Inchangée |
| LINK | oui | 13 | oui | oui | 13 | Inchangée |
| BCH | non | hors top 30 | non | oui | 15 | Entre par la nouvelle règle. Rang 42 au volume 24 h et 30 au volume médian, dernière place du classement |
| UNI | oui | 16 | oui | oui | 17 | Inchangée |
| FIL | non | hors top 30 | non | oui | 18 | Entre par la nouvelle règle. Rang 49 au volume 24 h et 18 au volume médian |
| WLD | oui | 17 | oui | oui | 19 | Inchangée |
| QNT | non | hors top 30 | oui | oui | 21 | Entre par le moment de mesure. Déjà présente dans le témoin sur 24 h de cette collecte |
| 1000PEPE | oui | 14 | non | non | 16 | Sort par le moment de mesure. Corrélation avec DOGE passée de 0,8499 à 0,8501 pour un plafond de 0,85 |
| AAVE | oui | 15 | oui | non | 22 | Sort par la nouvelle règle. Éligible, rang score 22, mais le panier est complet à 15 |

Bilan. 11 paires restent, 2 sortent (1000PEPE et AAVE) et 4 entrent (AVAX, BCH, FIL et QNT). À règle égale, le seul passage du temps échange 1000PEPE contre QNT entre 22:42 et 00:11. Le changement de règle ajoute ensuite AVAX, BCH et FIL et fait sortir AAVE, ce qui porte le panier de 13 à 15 paires.

Le top 30 lui-même change de 12 noms. Sortent AIN, AIOT, AKE, BEAMX, BIRB, COW, ESPORTS, IDOL, LSK, RSR, SOPH et TRX. Entrent ADA, ARB, AVAX, BCH, BTW, FIL, INJ, ONDO, QNT, STRK, TAO et TIA. La règle médiane retire donc surtout des pointes de volume de courte durée (et TRX, passé de 33 M de médiane à 306 M le 29/10).

Les chiffres des paires communes bougent un peu, car les bougies et les carnets diffèrent. L'ancienne version de ces chiffres reste dans RAPPORT_UNIVERS_20261031T224232Z.md.

## 5. Volume, classement et stabilité

Sur 942 contrats Binance, 513 perpétuels crypto USDT restent après exclusions, et les 513 ont leurs 30 bougies closes. Aucun n'a donc été écarté pour jeunesse dans cette collecte.

Le volume 24 h ne décide plus de l'entrée au classement. Avec la règle médiane, aucune paire sur 30 ne dépasse 5 fois sa médiane, contre 11 sur 30 dans l'ancien classement. Ce résultat vient en partie de la construction, car les pointes de courte durée ne peuvent plus entrer, et la règle de pointe dépend toujours du jour de mesure. Dans le panier, le volume 24 h ne vaut qu'environ 0,42 fois la médiane, ce qui reflète le week-end.

Stabilité d'un jour à l'autre, mesurée à 08:13 UTC sur les bougies 1 j closes du 17/10 au 31/10/2026 et sur les 513 perpétuels. Le volume d'une bougie sert d'approximation du volume 24 h.

| Mesure sur 14 passages d'un jour au suivant | Règle médiane 30 j | Règle volume du jour |
|---|---|---|
| Paires changées par jour, moyenne | 0,43 | 5,50 |
| Paires changées par jour, maximum | 2 | 8 |
| Paires changées au total | 6 | 77 |
| Paires communes au top 30 du 17/10 et du 31/10 | 27 sur 30 | 15 sur 30 |
| Jours sur 15 dans le top 30, BCH | 13 | 4 |
| Jours sur 15 dans le top 30, QNT | 15 | 4 |

Limites de ce test. Deux fenêtres voisines partagent 29 jours sur 30, donc la médiane est stable en partie par construction. Elle réagit aussi plus tard à une vraie perte de liquidité. Le test porte sur l'entrée au classement et non sur le panier, faute de carnets passés, et il utilise l'univers d'aujourd'hui.

Collecte de contrôle, de 07:53:55 à 08:13:12 UTC. Avec la règle médiane, le top 30 et le panier de 15 paires sont identiques à la collecte retenue, et l'écart de glissement à 50 000 USDT reste sous 1,17 bps (QNT). Avec la règle sur 24 h, le témoin passe de 13 à 12 paires, car AVAX entre tandis que QNT et SUI sortent. Cet accord ne prouve pas la stabilité du panier d'un jour à l'autre, car les deux collectes tombent le même jour UTC et lisent donc les mêmes bougies closes. Seuls les carnets et le volume 24 h diffèrent entre elles. Un contrôle un autre jour, en semaine, reste [non exécuté].

Contrôle croisé Bybit, seule mesure disponible sur 24 h. 23 bases sont communes aux deux classements de 30 paires. Seulement chez Bybit, ONDO, XMR, BIRB, STX, LIT, OP et ADA. Seulement chez Binance, AIN, IDOL, COW, AIOT, RSR, QNT et PUMP. L'écart de prix médian Bybit contre Binance est de -0,03 % sur le classement et de 0,14 % au plus dans le panier (BNB). Aucune dislocation forte n'apparaît. Cela ne dit rien de la solvabilité ni des retraits.

Bandes de profondeur. Le carnet de 500 niveaux s'arrête parfois avant la bande demandée, et la valeur n'est alors qu'une borne basse. Chez Binance, BTC est tronqué à 10 bps dans les 6 instantanés (couverture médiane de 7,5 à 7,7 bps) et BTC, ETH et ZEC le sont à 50 bps. Chez Bybit, BTC et ETH le sont à 50 bps. Le détail figure au § 5 du screener et dans les colonnes _tronquee_instantanes du CSV. Ces bandes n'entrent ni dans le score ni dans l'éligibilité, donc le panier n'en dépend pas.

## 6. Financement et coût d'emprunt

Un perpétuel n'a pas d'emprunt. Le coût de portage est le financement. Le signe se lit pour une position acheteuse, qui paie quand le taux est positif.

Les 15 paires du panier couvrent 365 jours et 1 095 périodes chez Binance. La moyenne annualisée sur un an va de -7,17 % (ZEC) à 4,63 % (LINK). Le 95e centile vaut environ 0,01 % par 8 h pour chacune, soit le taux de base habituel. Sur 90 jours, la moyenne annualisée est positive pour 14 paires, de 1,11 % (WLD) à 6,51 % (UNI). Elle est négative pour QNT à -6,06 %. Le signe d'un an ne se prolonge donc pas forcément. Pour BNB, 56,9 % des périodes ont un taux exactement nul.

Coût d'emprunt spot sur marge. Chez Binance, le point d'accès officiel exige une clé (/sapi/v1/margin/allAssets répond -2014, relevé du 31/10 non refait). Deux sources publiques répondent sans clé, relevées à 00:17 UTC.

| Base | Binance VIP 0 (% par an) | Bybit sans VIP (% par an) |
|---|---|---|
| BTC | 0,49 | 0,49 |
| ETH | 2,78 | 2,78 |
| SOL | 5,49 | 4,37 |
| ZEC | 14,55 | [non disponible] |
| BNB | 2,96 | 4,45 |
| DOGE | 3,45 | 5,17 |
| NEAR | 7,01 | 2,24 |
| AVAX | 2,33 | 3,49 |
| SUI | 1,57 | 1,59 |
| LINK | 0,61 | 0,91 |
| BCH | 7,94 | 4,01 |
| UNI | 0,50 | 0,75 |
| FIL | 2,06 | 3,09 |
| WLD | 11,92 | 7,74 |
| QNT | 12,85 | 9,69 |

Limites de ce tableau. Ce sont des instantanés, sans historique. Le point d'accès Binance (www.binance.com/bapi/margin/v1/public/margin/vip/spec/list-all) sert le site web et n'est pas documenté. Il peut changer sans préavis. Bybit (/v5/spot-margin-trade/data) est documenté, et seuls les actifs marqués empruntables sont retenus. Le taux n'indique pas la quantité réellement empruntable. L'historique de ces taux reste [non disponible] sans authentification.

## 7. Données téléchargées

Fichiers dans user_data/data/binance/futures (feather), mode futures, fenêtre du 01/01/2021 au 30/06/2024. Le financement et le prix de marque arrivent automatiquement au pas de 1 h. La fin effective est le 30/06/2024 pour toutes les paires, à 00:00 pour les bougies 1 j, 23:00 pour le prix de marque et 16:00 pour le financement. Détail dans donnees_panier_dates_20261101T001138Z.csv.

| Paire | Listing Binance | Début réel 1 j | Début réel marque | Début réel financement | Bougies 1 j | Statut au contrôle |
|---|---|---|---|---|---|---|
| BTC/USDT:USDT | 2019-09-08 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| ETH/USDT:USDT | 2019-11-27 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| SOL/USDT:USDT | 2020-09-14 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| ZEC/USDT:USDT | 2020-02-05 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| BNB/USDT:USDT | 2020-02-10 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| DOGE/USDT:USDT | 2020-07-10 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| NEAR/USDT:USDT | 2020-10-15 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| AVAX/USDT:USDT | 2020-09-23 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | coupé à la fin de fenêtre |
| SUI/USDT:USDT | 2023-05-03 | 2023-05-03 | 2023-05-03 12:00 | 2023-05-03 16:00 | 425 | sans dépassement |
| LINK/USDT:USDT | 2020-01-17 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| BCH/USDT:USDT | 2019-12-19 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | coupé à la fin de fenêtre |
| UNI/USDT:USDT | 2020-09-18 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | sans dépassement |
| FIL/USDT:USDT | 2020-10-16 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 | coupé à la fin de fenêtre |
| WLD/USDT:USDT | 2023-07-24 | 2023-07-24 | 2023-07-24 09:00 | 2023-07-24 16:00 | 343 | sans dépassement |
| QNT/USDT:USDT | 2022-10-18 | 2022-10-20 | 2022-10-20 01:00 | 2022-10-20 08:00 | 620 | coupé à la fin de fenêtre |

SUI, WLD et QNT ne couvrent que la fin de la fenêtre. Un test sur ce panier compte donc moins de paires avant mai 2023. SOL compte 3 906 périodes de financement contre 3 831 pour les autres paires de même début, car certaines périodes ont été plus courtes [cause précise non vérifiée].

Le dépassement connu est revenu. freqtrade 2026.10 a gardé les lots entiers de l'API pour les 4 paires nouvelles, jusqu'au 03/05/2025 pour le financement et au 12/07/2025 pour QNT en 1 j. verifier_donnees_panier.py a consigné la fin brute puis a coupé ces 12 fichiers. Un nouveau téléchargement ferait réapparaître ce dépassement, et il faudrait relancer ce script.

Les fichiers de 1000PEPE et AAVE restent sur le disque, car ils sont coupés et sans risque, mais ils ne font plus partie du panier. config_telechargement_panier.json liste les 15 paires du nouveau panier, garde key et secret vides et dry_run à true.

## 8. Univers à la date, faisabilité

Les tests de faisabilité datent du 31/10/2026 et n'ont pas été refaits, car ils ne dépendent pas du panier. Le verdict et le détail restent au § 7 de RAPPORT_UNIVERS_20261031T224232Z.md et dans faisabilite_pit_20261031T222904Z.json. La reconstruction reste faisable pour les listes et les volumes depuis 2021, avec un travail de données supplémentaire, et elle ne l'est pas avec exchangeInfo seul.

Le classement pilote a seulement été recompté avec le nouveau panier, sans nouvel appel.

| Date | Ancien panier dans le top 30 | Nouveau panier dans le top 30 | Paires du nouveau panier absentes du top 30 |
|---|---|---|---|
| 2021-01-01 | 6 sur 13 | 7 sur 15 | AVAX, DOGE, NEAR, QNT, SOL, SUI, WLD, ZEC |
| 2022-01-01 | 7 sur 13 | 9 sur 15 | BCH, QNT, SUI, UNI, WLD, ZEC |
| 2023-01-01 | 7 sur 13 | 9 sur 15 | BCH, QNT, SUI, UNI, WLD, ZEC |
| 2024-01-01 | 7 sur 13 | 9 sur 15 | BCH, QNT, SUI, UNI, WLD, ZEC |

Le biais recule un peu mais reste large. Entre 6 et 8 paires sur 15 n'étaient pas dans le top 30 de ces dates, et le pilote ne traite toujours pas les morts ni les renommages.

## 9. Constats de la revue traités

| Constat | Reproduction | Traitement |
|---|---|---|
| Entrée au top 30 fondée sur le volume 24 h, panier instable | Reproduit. Le panier de la revue (23:36 UTC le 31/10, 2 instantanés) compte 14 paires avec QNT. Le témoin de 00:11 donne 13 paires sans 1000PEPE, et le témoin de 07:53 en donne 12 | Corrigé, essai U03. Effet mesuré au § 5. Volume 24 h conservé à l'affichage |
| Bandes de profondeur tronquées sans le dire | Reproduit. Ancien CSV, BTC à 10 bps égale BTC à 50 bps égale le carnet entier (17,95 M à l'achat, 17,93 M à la vente). 1 paire à 10 bps et 3 paires à 50 bps | Signalé et non corrigé. Colonnes de couverture et de troncature ajoutées. La source bookDepth n'est pas utilisée |
| --sorties ne redirige pas le cache | Reproduit sur la copie de l'ancien script, lignes 108 et 901 | Corrigé, option --cache. Vérifié à 08:13 UTC, la collecte de contrôle n'a rien écrit dans le dépôt (empreintes SHA-1 comparées) |
| Bêta supérieur à 1 pour 12 paires sur 13, BTC compté | Reproduit. BTC vaut 1,0000000000000002 dans l'ancien CSV et passe donc le test. Le bon décompte de l'ancien panier était 11 sur 12 | Corrigé. Ici 12 sur 14 hors BTC. Le corps de l'ancien rapport garde son texte et son bandeau porte la correction |

## 10. Anomalies

| N° | Constat | Traitement |
|---|---|---|
| 1 | Le serverTime de /fapi/v1/exchangeInfo retarde de 12,4 h sur /fapi/v1/time, et de 20,1 h à 07:53 | Réponse probablement servie depuis un cache. Les statuts peuvent dater de quelques heures |
| 2 | Le § 2 de screener_20261101T001138Z.md date les tickers Binance de 00:14:28, or le journal les place avant 00:11:39 | La collecte brute n'a qu'un seul champ d'heure, et 00:14:28 est l'heure de Bybit. Le script sépare désormais les deux, et le contrôle de 07:53 les distingue. Fichier publié non modifié |
| 3 | screener_univers.py a été modifié à 00:33 UTC, juste après la fin de la collecte | Sans effet sur le panier. Le rejeu avec le script final redonne les 6 fichiers de sortie à l'identique |
| 4 | git status montre aussi strategies/STRAT-20261031-01/user_data/ comme non suivi et non ignoré | Hors périmètre, non modifié. Un git add . pourrait y embarquer des données lourdes. À vérifier avant le commit |
| 5 | Les alias de tickers entre plateformes sont manuels (BEAMX et BEAM, PUMP et PUMPFUN) | Contrôle de prix à 2 % dans les règles. D'autres absents apparents restent possibles [non vérifié] |
| 6 | Les seuils et pondérations sont des choix a priori, sans validation empirique | Tous écrits en tête du script. La pondération n'a jamais été testée sur un résultat de stratégie. Le choix de la règle médiane n'a été jugé sur aucun rendement |
| 7 | Le passage à 15 paires atteint le plafond du panier | Plafond inchangé. AAVE, ARB, INJ et TIA restent écartées, et cet effet dépend de l'ordre du score |

Sources : Binance Futures REST public (fapi.binance.com), Bybit v5 REST public (api.bybit.com), bapi web public de Binance. Aucune clé et aucun ordre.

Fichiers : screener_20261101T001138Z.md, .csv, .json, _panier.csv, _exclusions.csv, _corr180j.csv, _volumes_tous.csv ; donnees_panier_dates_20261101T001138Z.csv ; controle_stabilite_20261101T075355Z.csv, _panier.csv ; stabilite_top30_20261101T081351Z.json ; REGISTRE_ESSAIS_UNIVERS.csv ; execution_screener_U03.log, execution_telechargement_U03.log, execution_controle_stabilite_20261101T075355Z.log.
