# Plan du module papier à 7 cohortes de STRAT-06-bis, et ligne de gel proposée

Écrit le 13/11/2026 par Claude, à la demande de Jonathan et Téo. Résultat de recherche : aucun ordre, aucune clé, `dry_run` permanent, capital nul. Rien n'est codé ni gelé par ce document. Il répond à la question « que faut-il coder, et que faut-il figer avant le premier jour compté » (`FICHE_STRAT-06-BIS.md` § 4).

## 0. Ce que le papier peut prouver, rappelé avant de coder

La v1 a été **rejetée au hors échantillon** le 09/11/2026 par ses propres portes : Sharpe 1,398 pour un seuil de 1,72, borne basse de l'IC à 90 % à −0,04 %. Le +64 % net de E19 est réel mais n'a pas passé le seuil statistique fixé d'avance. STRAT-06-bis n'est donc pas un edge prouvé : c'est un test en avant. Sa puissance est publiée au § 2 de la fiche : un verdict favorable dans 69 % des cas si le vrai Sharpe vaut 1,3, et un faux verdict favorable dans 21 % des cas s'il vaut 0. Le papier ne passe aucun ordre : Jonathan verra des signaux et un suivi quotidien, pas des trades. Tout pilote réel demande une nouvelle décision écrite, au plus tôt après le point d'étape de 26 semaines (fiche § 3).

## 1. Pourquoi ne pas adapter `paper_trading_strat06.py`

Le module actuel ne fait pas la même chose que le moteur qui a produit les résultats de la v1. Lu le 13/11/2026 :

| Point | Moteur de backtest (`univers_cotations.py`, `moteur_xsmom.py`) | Module papier actuel |
|---|---|---|
| Date de cotation | Premier jour de volume non nul | `onboardDate` de l'API, qui diffère après un renommage ou une recotation |
| Exclusions | Stablecoins et indices (`est_exclu`), contrats « 1000X » dont l'actif était déjà coté | Absentes |
| Contrats | Perpétuels des archives | Accepte aussi `PREMARKET` |
| Classement | Médiane de volume décroissante, puis symbole | Médiane seule, égalités non tranchées |
| Taille | 1/12 de notionnel par ligne à brut 100 % (1/84 par cohorte) | Taille par le risque (capital × risque / stop) |
| Calendrier | Signal à 00:00, exécution à l'ouverture de 01:00 | Scan le lundi à 00:05, aucune exécution suivie |
| Suivi | Stop sur le plus haut horaire du prix de marque, financement H2, rotation, H4 | Aucun : pas de position, pas de stop, pas de P&L |
| Série stressée | Mode 1 de `stress_stops.py` | Absente |

Le corriger point par point referait un deuxième moteur, avec le risque d'un écart silencieux, le défaut de l'ordre de la whitelist de STRAT-01. **La voie proposée est de faire tourner le moteur de backtest lui-même sur les données publiques du jour.** `moteur_xsmom.backtest` accepte déjà une liste de dates de rééquilibrage quelconque : une cohorte n'est que ce moteur appelé avec des dates espacées de 7 jours, à partir de son jour de la semaine.

## 2. Ce qu'il faut coder

**`collecte_papier06.py`, collecte quotidienne en ajout seul.** Chaque jour vers 00:10 UTC, puis chaque heure à :05 :
- volumes journaliers de tous les perpétuels USDT (`/fapi/v1/klines` 1d, depuis la première bougie pour les noms récents, afin de dater la cotation comme le moteur) ;
- bougies horaires du contrat et du prix de marque (`/fapi/v1/klines` et `/fapi/v1/markPriceKlines` 1h) pour les noms tenus et BTC ;
- événements de financement (`/fapi/v1/fundingRate`) ;
- `exchangeInfo` pour les contrats non crypto (leçon L10) et la liste close des faux nouveaux noms.

Stockage au format de `donnees_binance` (mêmes colonnes que le backtest), un fichier par jour, empreinte SHA-256 inscrite dans un manifeste. Un fichier écrit n'est jamais réécrit : une donnée corrigée s'ajoute à côté et se signale.

**`paper_cohortes06.py`, calcul des deux séries.** Après chaque collecte :
- pour chaque cohorte d (0 à 6), dates de rééquilibrage = jour 0 + d, puis tous les 7 jours ;
- appel de `moteur_xsmom.backtest` avec `fonction_cible = univers_cotations.fabrique_cible(...)`, la configuration figée de la v1 et `notionnel = 1/84`, sur les données collectées depuis le jour 0 ;
- série de base = somme des 7 cohortes ; série stressée = même calcul avec la sortie de stop du mode 1 (mi-chemin entre le niveau et le plus haut de marque de l'heure), réutilisée depuis `stress_stops.py` ;
- sorties en ajout seul : `JOURNAL_COHORTES.md` (signal, entrées, stops, sorties, net du jour de chaque série), `serie_base.csv`, `serie_stressee.csv`, `incidents.csv`.

**`rejeu_cohortes06.py`, contrôle hebdomadaire (préalable 2 de la fiche).** Dès que data.binance.vision publie les archives de la semaine, relance du même calcul sur les archives au lieu des données collectées. Toute différence de sélection, de stop ou de prix d'entrée au-delà d'une tolérance écrite d'avance est un incident consigné, jamais une correction rétroactive.

**`verdict_bis06.py`, critères de la fiche § 2.** Drawdown de la série stressée à brut 100 % (arrêt au-delà de 40 %), net cumulé au point d'étape de 26 semaines, puis à 52 semaines : Sharpe annualisé des rendements hebdomadaires, alpha à deux facteurs (méthode du diagnostic B, facteurs recalculés sur la période du papier), concentration par nom et par mois, nombre de lignes de shorts. Il refuse de rendre un verdict avant la date.

**Tests synthétiques (à écrire avant tout déploiement) :**
- une cohorte rend exactement le backtest v1 quand les dates sont des lundis et le notionnel 1/12 ;
- les 7 cohortes sont décalées d'un jour et pèsent 1/7 chacune ; la première semaine monte de 1/7 à 7/7 ;
- sélection identique entre données collectées et archives sur un même jour fabriqué ;
- stop sur le plus haut horaire du prix de marque, rempli au pire du niveau et de l'ouverture plus 0,30 %, et version stressée au mi-chemin ;
- financement payé ou reçu selon le sens, sur ]entrée ; sortie] ;
- un jour manquant n'est ni rejoué ni remplacé, et il est compté comme incident ;
- relance après une panne sans double comptage ; refus de réécrire un fichier du journal.

**Exploitation sur le serveur :** une tâche `cron` horaire plutôt qu'une boucle dans tmux, pour survivre à un redémarrage ; un fichier de battement de cœur ; une alerte si aucun signal n'est écrit pendant plus de 2 jours (règle d'incident de la fiche). Volume estimé : quelques mégaoctets par jour.

**Ordre de grandeur :** 600 à 900 lignes de code et de tests, une session de travail. Puis 3 jours de fonctionnement à blanc sur le serveur, non comptés, pour vérifier la collecte et un premier rejeu partiel.

## 3. Ligne de gel proposée (à écrire par Jonathan et Téo, pas avant la fin des jours à blanc)

> | [date] | STRAT-06-bis | validation | décision Jonathan et Téo | **Gel des critères de STRAT-06-bis.** Règles du § 1 de `FICHE_STRAT-06-BIS.md` et configuration v1 figée (`config_strat06.json`, empreinte [SHA-256]) : âge de 7 à 60 jours daté par le premier jour de volume, médiane ≥ 20 M USDT, 6 noms au plus, short de chaque nom, long BTC à 1× la somme des shorts, stop à 30 % sur le prix de marque, frais 0,05 % et glissement 0,05 % par côté, glissement au stop 0,30 %, financement réel. 7 cohortes, signal à 00:00 UTC, exécution à l'ouverture de 01:00 UTC, tenue de 7 jours, 1/84 de notionnel par ligne. Moteur : `moteur_xsmom.backtest` appelé par `paper_cohortes06.py` (commit [hash]). Verdict sur la série stressée (mode 1). Critères du § 2 : 52 semaines, point d'étape à 26 semaines (net cumulé ≤ 0 → rejet), arrêt anticipé si drawdown > 40 %, verdict favorable si Sharpe > 0,8, alpha à deux facteurs > 0, aucun nom > 25 % et aucun mois > 40 % du gain net, au moins 300 lignes de shorts ; incidents selon le § 2. **Premier jour compté : [date], 00:00 UTC**, premier jour suivant cette ligne. Aucun jour antérieur ne compte. Puissance publiée : 69 % si Sharpe 1,3, 21 % de faux positif si Sharpe 0 | `strategies/STRAT-20261102-06/FICHE_STRAT-06-BIS.md` |

**Points à trancher par Jonathan et Téo avant d'écrire cette ligne :**
1. **La semaine de montée en charge** (exposition de 1/7 à 7/7) compte-t-elle dans les 52 semaines ? Proposition : oui, les 52 semaines partent du jour 0, et la montée en charge se publie.
2. **Tolérance du rejeu** : proposition, sélection identique exigée ; écart de prix d'entrée toléré de 0,01 % (arrondis de l'API).
3. **Facteurs de l'alpha** : recalculés sur la période du papier avec la méthode du diagnostic B, sur le panier de 30 grandes alts de la v1. À confirmer.
4. **Signal montré à Jonathan** : le journal quotidien donne, à titre indicatif, le notionnel par ligne pour un capital donné. Ce montant ne sert pas au verdict et ne vaut pas ordre.
5. **Les filtres « v2 » du module actuel** (anti-financement, demi-tailles) restent hors du verdict. Proposition : les retirer du module papier, ou les publier dans une série fantôme à part.

## 4. Ce qui reste du module actuel

`paper_trading_strat06.py` reste dans le dépôt comme outil de lecture rapide, sans valeur pour le verdict. Les deux signaux déjà produits sur le serveur (07 et 09/11/2026, non suivis par Git) ne comptent pas : ils sont antérieurs au gel et viennent d'une autre règle.
