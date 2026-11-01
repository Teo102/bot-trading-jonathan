# Rapport d'univers des perpétuels USDT, collecte du 31/10/2026

> REMPLACÉ le 01/11/2026 par RAPPORT_UNIVERS_20261101T001138Z.md. Ce panier de 13 paires, figé par son horodatage 20261031T224232Z, ne doit plus servir. Son entrée au top 30 reposait sur le volume 24 h, instable d'un moment à l'autre (essai U02, voir REGISTRE_ESSAIS_UNIVERS.csv). Le texte ci-dessous reste tel quel, à une correction près. Le bêta à BTC dépasse 1 pour 11 paires sur 12 hors BTC, et non 12 sur 13.

Document de recherche. Aucune recommandation d'investissement et aucune promesse de gain. Aucune stratégie ne change de statut. dry_run reste true.

## 1. Biais à lire d'abord

Le classement d'aujourd'hui appliqué à 2021-2024 est un biais d'anticipation et du survivant. Seuls les gagnants actuels y figurent et les jetons morts manquent. Ce panier ne remplace donc PAS l'univers figé de STRAT-20261031-01. Il sert aux recherches futures. Toute stratégie testée dessus doit porter ce biais ou utiliser un univers reconstruit à la date.

La règle des 180 jours de cotation avant le 30/06/2024 aggrave ce biais. Elle choisit des paires pour leur présence dans une fenêtre passée, à partir d'un classement connu seulement en 2026.

Alerte en cours. Piratage Binance fin octobre 2026 et retraits suspendus, reprise annoncée le 01/11, selon NOTE_STRATEGIE_ET_REGIME.md (information non revérifiée ici). Les données publiques restent lisibles mais ne préjugent pas d'une exécution sur cette plateforme.

## 2. Ce qui a été exécuté

| Étape | Heure UTC | Résultat |
|---|---|---|
| Essai sur 4 paires, dossier temporaire | 22:23 à 22:24 | Sans erreur |
| Première collecte complète | 22:24 à 22:40 | Écartée. PUMPUSDT passait à tort pour absent de Bybit, qui le nomme PUMPFUNUSDT |
| Test de faisabilité de l'univers à la date | 22:29 à 22:32 | Terminé. Une première version a échoué à 22:25 sur le listing de l'archive (délai dépassé), puis le listing a répondu |
| Collecte complète retenue, 729 appels HTTP, aucun incident HTTP | 22:42 à 22:58 | Terminée avec le même panier de 13 paires que la première |
| Téléchargement freqtrade du panier | BTC à 22:42, le reste de 23:03 à 23:05 | 13 paires et 39 fichiers, code de sortie 0 |
| Contrôle et coupe des fichiers à la fin de fenêtre | Après le téléchargement | 39 fichiers coupés, aucun trou détecté |
| Test freqtrade sur des paires mortes, dossier temporaire | 23:07 | FTM téléchargé, LUNA refusé (voir § 7) |

Six instantanés de carnets ont été pris sur les 30 paires, de 22:44:28 à 22:58:12, espacés d'environ 2 min 45. Ils tombent tous un samedi soir. Ils ne mesurent donc pas la liquidité en heures ouvrées ni sur plusieurs jours.

## 3. Panier retenu, 13 paires

Sources : Binance /fapi/v1/klines, /fapi/v1/depth, /fapi/v1/fundingRate, collecte du 31/10/2026 de 22:42 à 22:58 UTC.

| Paire | Rang score | Score | Vol. médian 30 j (M USDT) | Gliss. 50k Binance (bps) | Gliss. 50k Bybit (bps) | Financement annualisé 1 an (%) | Part négative (%) | Corr. BTC 180 j | Bêta BTC 180 j |
|---|---|---|---|---|---|---|---|---|---|
| BTC | 1 | 86,7 | 10 969 | 0,01 | 0,01 | 3,47 | 22,7 | 1,00 | 1,00 |
| ETH | 2 | 86,4 | 7 596 | 0,02 | 0,12 | 2,51 | 26,4 | 0,89 | 1,23 |
| SOL | 4 | 75,9 | 1 502 | 0,52 | 0,52 | -0,31 | 44,7 | 0,84 | 1,26 |
| ZEC | 5 | 74,6 | 1 699 | 1,34 | 2,51 | -7,31 | 38,0 | 0,52 | 1,83 |
| BNB | 6 | 73,5 | 281 | 0,36 | 1,32 | 2,52 | 1,3 | 0,72 | 0,80 |
| DOGE | 7 | 68,6 | 325 | 1,10 | 1,56 | 3,09 | 31,3 | 0,81 | 1,26 |
| NEAR | 8 | 67,0 | 682 | 2,45 | 2,77 | 3,70 | 26,6 | 0,39 | 1,24 |
| SUI | 12 | 60,8 | 229 | 2,13 | 2,26 | 3,15 | 29,9 | 0,68 | 1,52 |
| LINK | 13 | 59,0 | 109 | 2,71 | 2,74 | 4,64 | 20,8 | 0,74 | 1,27 |
| 1000PEPE | 14 | 56,6 | 234 | 5,38 | 4,36 | -0,85 | 38,1 | 0,74 | 1,76 |
| AAVE | 15 | 53,9 | 99 | 6,18 | 5,30 | 2,75 | 28,1 | 0,63 | 1,41 |
| UNI | 16 | 53,3 | 203 | 4,33 | 6,00 | 4,45 | 22,7 | 0,53 | 1,33 |
| WLD | 17 | 52,4 | 271 | 4,60 | 5,41 | -5,94 | 47,4 | 0,32 | 1,20 |

Le glissement est la médiane des six instantanés, moyenne de l'achat et de la vente, contre le prix médian du carnet et hors frais. Le pire instantané du panier reste à 8,10 bps (vente AAVE, CSV).

Corrélation entre paires du panier sur 180 jours, médiane 0,58, minimum 0,31, maximum 0,89 (BTC et ETH, exemptées du plafond). Le plafond de 0,85 a suffi et n'a pas été assoupli. Ce niveau n'empêche pas un risque commun, car le bêta à BTC dépasse 1 pour 12 paires sur 13.

Recouvrement avec l'univers figé de STRAT-01. BTC, ETH, BNB, DOGE et LINK figurent dans les deux. Cet univers n'est pas modifié.

Décisions fragiles à connaître. La corrélation DOGE et 1000PEPE vaut 0,8499 pour un plafond de 0,85. XRP (rang 3) est écarté à 0,868 avec BTC. TRX (rang 11) est écarté pour un volume 24 h de 5,3 fois sa médiane, juste au-dessus du seuil de 5. Un autre jour de mesure pourrait changer ces trois décisions.

Écartées par la règle de cotation avant le 30/06/2024 alors qu'elles sont liquides aujourd'hui, HYPE (rang 9) et ENA (rang 10).

## 4. Volume et classement

Le classement des 30 premiers par volume 24 h est très instable. 11 paires sur 30 ont un volume 24 h supérieur à 5 fois leur médiane sur 30 jours, jusqu'à 207 fois pour IDOL. Ces pointes faussent le classement brut, c'est pourquoi le score repose sur la médiane.

Le volume quotidien de BTC chez Binance était de 20,3 G USDT le 29/10 et 18,7 G le 30/10, contre une médiane de 11,0 G. TRX est passé de 33 M de médiane à 306 M le 29/10. La simultanéité avec l'incident Binance est visible, le lien de cause n'est pas établi.

Contrôle croisé Bybit. 24 bases sont communes aux deux classements de 30 paires. Seulement chez Bybit, ONDO, XMR, OP, STX, LIT et ADA. Seulement chez Binance, AIN, IDOL, COW, ESPORTS, AIOT et RSR. L'écart de prix médian Bybit contre Binance est de -0,04 % sur les paires communes et de 0,39 % au plus dans le panier (1000PEPE). Aucune dislocation forte n'apparaît. Cela ne dit rien de la solvabilité ni des retraits.

## 5. Financement et coût d'emprunt

Un perpétuel n'a pas d'emprunt. Le coût de portage est le financement. Le signe se lit pour une position acheteuse, qui paie quand le taux est positif.

Les 13 paires du panier couvrent 365 jours et 1 095 périodes chez Binance. Le 95e centile vaut environ 0,01 % par 8 h pour chacune, soit le taux de base habituel. Le détail figure dans le CSV et aux § 6 et 7 du rapport du screener. Sur 90 jours, la moyenne annualisée est positive pour les 13 paires, de 1,07 % (WLD) à 6,53 % (UNI). Le signe d'un an ne se prolonge donc pas forcément. Pour BNB, 56,8 % des périodes ont un taux exactement nul.

Coût d'emprunt spot sur marge. Chez Binance, le point d'accès officiel exige une clé (/sapi/v1/margin/allAssets répond -2014). Deux sources publiques répondent sans clé, relevées à 22:44 UTC.

| Base | Binance VIP 0 (% par an) | Bybit sans VIP (% par an) |
|---|---|---|
| BTC | 0,49 | 0,49 |
| ETH | 2,78 | 2,78 |
| SOL | 5,49 | 4,37 |
| ZEC | 14,55 | [non disponible] |
| BNB | 2,96 | 4,45 |
| DOGE | 3,45 | 5,17 |
| NEAR | 7,01 | 2,32 |
| SUI | 1,57 | 1,59 |
| LINK | 0,61 | 0,91 |
| PEPE | 1,57 | 2,38 |
| AAVE | 2,50 | 3,75 |
| UNI | 0,50 | 0,75 |
| WLD | 11,92 | 7,74 |

Limites de ce tableau. Ce sont des instantanés, sans historique. Le point d'accès Binance (www.binance.com/bapi/margin/v1/public/margin/vip/spec/list-all) sert le site web et n'est pas documenté. Il peut changer sans préavis. Bybit (/v5/spot-margin-trade/data) est documenté, et seuls les actifs marqués empruntables sont retenus. Binance affiche 499,99 % pour HYPE, hors panier [plafond ou quasi-indisponibilité, interprétation non vérifiée]. Le taux n'indique pas la quantité réellement empruntable. L'historique de ces taux reste [non disponible] sans authentification.

## 6. Données téléchargées

Fichiers dans user_data/data/binance/futures (feather), mode futures. Le financement et le prix de marque arrivent automatiquement au pas de 1 h. La fin effective est le 30/06/2024 pour toutes les paires, à 00:00 pour les bougies 1 j, 23:00 pour le prix de marque et 16:00 pour le financement.

| Paire | Listing Binance | Début réel 1 j | Début réel marque | Début réel financement | Bougies 1 j |
|---|---|---|---|---|---|
| BTC/USDT:USDT | 2019-09-08 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| ETH/USDT:USDT | 2019-11-27 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| SOL/USDT:USDT | 2020-09-14 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| ZEC/USDT:USDT | 2020-02-05 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| BNB/USDT:USDT | 2020-02-10 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| DOGE/USDT:USDT | 2020-07-10 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| NEAR/USDT:USDT | 2020-10-15 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| SUI/USDT:USDT | 2023-05-03 | 2023-05-03 | 2023-05-03 12:00 | 2023-05-03 16:00 | 425 |
| LINK/USDT:USDT | 2020-01-17 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| 1000PEPE/USDT:USDT | 2023-05-05 | 2023-05-05 | 2023-05-05 11:00 | 2023-05-05 16:00 | 423 |
| AAVE/USDT:USDT | 2020-10-16 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| UNI/USDT:USDT | 2020-09-18 | 2021-01-01 | 2021-01-01 00:00 | 2021-01-01 00:00 | 1 277 |
| WLD/USDT:USDT | 2023-07-24 | 2023-07-24 | 2023-07-24 09:00 | 2023-07-24 16:00 | 343 |

SUI, 1000PEPE et WLD ne couvrent que la fin de la fenêtre. Un test sur ce panier compte donc moins de paires avant mai 2023. SOL compte 3 906 périodes de financement contre 3 831 pour les autres paires de même début, car certaines périodes ont été plus courtes [cause précise non vérifiée].

Dépassement constaté. freqtrade 2026.10 garde les lots entiers de l'API et dépasse la fin demandée, jusqu'au 03/05/2025 pour le financement. Le script verifier_donnees_panier.py a consigné la fin brute puis a coupé les 39 fichiers. Un nouveau téléchargement ferait réapparaître ce dépassement, et il faudrait relancer ce script.

## 7. Univers à la date, faisabilité

Verdict. La reconstruction est faisable pour les listes et les volumes depuis 2021, avec un travail de données supplémentaire. Elle ne l'est pas avec exchangeInfo seul.

Tests réels du 31/10/2026, de 22:29 à 22:32 UTC, sauf les deux derniers à 23:07.

| Test | Résultat |
|---|---|
| exchangeInfo, perpétuels USDT crypto | 655 contrats, dont 519 en cotation, 135 en SETTLING et 1 à venir |
| 20 jetons témoins morts ou renommés | 12 sont absents d'exchangeInfo (dont LUNA, SRM, MATIC et EOS) |
| Bougies fapi de ces jetons | 18 sur 20 répondent dès la première requête. NU répond sans date de début. BTCST renvoie HTTP 400 |
| Archive data.binance.vision, liste S3 | 1 056 symboles sur 2 pages, avec 31 perpétuels USDT crypto absents d'exchangeInfo |
| Ces 31 contrats dans fapi | 27 ont des bougies, 4 n'en ont pas (AERGO, BDXN, BTCST, SXP) et relèvent de l'archive seule |
| Financement de contrats morts, /fapi/v1/fundingRate | Répond pour LUNA, FTM et SRM en janvier 2022 |
| freqtrade avec --include-inactive-pairs | FTM (SETTLING) téléchargé. LUNA (absent d'exchangeInfo) refusé |

Classement pilote par volume médian sur les 30 jours précédant chaque date.

| Date | Contrats candidats | Avec bougies | Hors cotation aujourd'hui dans le top 30 | Dont absents d'exchangeInfo | Paires du panier dans le top 30 |
|---|---|---|---|---|---|
| 2021-01-01 | 77 | 76 | EOS, WAVES, YFII, MKR | EOS, YFII | 6 sur 13 |
| 2022-01-01 | 132 | 129 | LUNA, MATIC, FTM, EOS, LRC, ANT | LUNA, MATIC, EOS, ANT | 7 sur 13 |
| 2023-01-01 | 156 | 144 | MATIC, FTM, OCEAN, WAVES, EOS | MATIC, EOS | 7 sur 13 |
| 2024-01-01 | 255 | 243 | MATIC, NFP, FTM | MATIC | 7 sur 13 |

Ce pilote chiffre le biais. Environ la moitié du panier n'était pas dans le top 30 de ces dates. LUNA était 3e au 01/01/2022 et n'apparaît plus dans exchangeInfo. Par ailleurs, DOGE n'est pas dans le top 30 du 01/01/2021 alors que STRAT-01 le présente parmi les actifs les plus liquides début 2021. Ce point est à transmettre à son dossier, cet univers n'est pas modifié ici.

Ce qui manque pour passer du pilote à un univers exploitable.

| Manque | Conséquence | Piste |
|---|---|---|
| Import hors freqtrade | Les contrats absents d'exchangeInfo ne se téléchargent pas par la commande standard | Écrire un import fapi et archive vers le format feather |
| Date de délistage | Un contrat SETTLING garde des bougies jusqu'à aujourd'hui, à volume nul et prix figé (FTM, FTT) | Prendre la dernière bougie à volume non nul |
| Table des renommages | MATIC et FTM sont comptés comme hors cotation, or ce sont des renommages probables [succession à vérifier] | Table manuelle ancien et nouveau symbole |
| Relistages | CVC a des bougies fapi depuis 2025-05-16 seulement, alors que l'archive répond pour janvier 2022 | Fusionner fapi et archive |
| Carnets historiques | La profondeur et l'écart à la date ne sortent pas des bougies | Volume comme approximation. Jeux bookDepth de l'archive [non testés] |
| Classification à la date | Stablecoins et actifs réels sont filtrés avec la classification d'aujourd'hui | Revue manuelle des contrats concernés |
| Autres plateformes | Le test couvre Binance seulement | Bybit [non testé] |

Le pilote lui-même est imparfait. Le sous-type et le statut sont lus aujourd'hui, et les 4 contrats sans bougies fapi en sont absents.

## 8. Anomalies

| N° | Constat | Traitement |
|---|---|---|
| 1 | Le serverTime de /fapi/v1/exchangeInfo retarde de 10,9 h sur /fapi/v1/time | Réponse probablement servie depuis un cache. Les statuts peuvent dater de quelques heures. Horodatage pris sur /fapi/v1/time et l'horloge locale |
| 2 | La règle user_data/data/ du .gitignore racine vise la racine du dépôt et ne couvrait pas systeme-trading/user_data | Fichier user_data/.gitignore ajouté dans le périmètre. Le .gitignore racine n'est pas modifié |
| 3 | git status montre aussi strategies/STRAT-20261031-01/user_data/ comme non suivi et non ignoré | Hors périmètre, non modifié. Un git add . pourrait y embarquer des données lourdes. À vérifier avant le commit |
| 4 | Les alias de tickers entre plateformes sont manuels (BEAMX et BEAM, PUMP et PUMPFUN) | Contrôle de prix à 2 % dans les règles. D'autres absents apparents restent possibles (AIN, IDOL, AIOT) [non vérifié] |
| 5 | Les seuils et pondérations sont des choix a priori, sans validation empirique | Tous écrits en tête du script. La pondération n'a jamais été testée sur un résultat de stratégie |

Sources : Binance Futures REST public (fapi.binance.com), Bybit v5 REST public (api.bybit.com), bapi web public de Binance, archive data.binance.vision. Aucune clé et aucun ordre.

Fichiers : screener_20261031T224232Z.md, .csv, .json, _panier.csv, _exclusions.csv, _corr180j.csv ; donnees_panier_dates_20261031T224232Z.csv ; faisabilite_pit_20261031T222904Z.json.
