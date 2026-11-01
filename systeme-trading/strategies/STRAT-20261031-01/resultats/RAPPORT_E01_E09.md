# Rapport des essais E01 à E09 de STRAT-20261031-01

Résultats de recherche du 31/10/2026, repris le 01/11/2026 après deux relectures contradictoires. Aucune promesse de gain, aucune recommandation. Rapport généré le 2026-11-01T00:29:46Z.

Le statut reste `backtest`. Le hors échantillon n'est pas ouvert. E10 et E11 n'ont pas été lancés. Ce rapport ne contient aucun verdict de rentabilité, car le critère porte sur le hors échantillon.

## 1. État de la procédure

La porte technique de E01 est franchie. L'exécution est correcte, le financement est appliqué et les deux contrôles de biais sont propres. La performance n'a joué aucun rôle dans cette porte. Ces contrôles couvrent les signaux et les indicateurs, pas l'attribution des places entre paires (§ 4).

Tous les essais prévus ont tourné, soit E01 à E09, R01 à R03 et l'essai de référence E00-ref. Aucun hyperopt n'a été lancé. Les paramètres de base n'ont pas changé. La configuration a été acceptée telle quelle, donc `config_strat01_backtest.json` n'existe pas.

Une anomalie majeure s'est produite au téléchargement. Elle a été corrigée avant tout backtest de ce `user_data` et le § 3 la détaille.

Cette reprise n'a lancé aucun backtest ni téléchargement. Les chiffres viennent d'un rejeu de `analyse_strat.py` sur les exports .zip existants (`brut/rejeu_analyse.sh`, `brut/<id>_analyse_reevalue.txt`) et d'un rejeu des scripts locaux des contradicteurs (`controles/`). Les valeurs déjà publiées sur la base réalisée restent identiques. L'équité réévaluée chaque jour devient la référence de lecture pour le Sharpe et le Sortino, ainsi que pour le Calmar, le drawdown et le DSR. La base réalisée reste affichée et libellée en second. L'avenant à valider avant E10 est dans `AVENANT_AVANT_E10.md`. Il n'est pas appliqué.

## 2. Tous les essais

Source pour le tableau, exports freqtrade 2026.10 du 2026-10-31 (22:33:52Z à 22:44:55Z), analysés de nouveau le 01/11/2026 par `analyse_strat.py`, données publiques Binance. La base réalisée compte le P&L le jour de la clôture du trade. La base réévaluée ajoute chaque jour le latent au prix de clôture 1d, hors frais et financement latents. L'IC iid garde 5000 tirages et la graine 0 pour rester comparable. L'IC par blocs utilise des blocs circulaires de 10 trades, 50 000 tirages et la graine 20261101. Le DD95 par permutation mélange les trades et le DD95 par blocs tire des blocs de 30 jours de rendements réévalués.

| Essai | Variante | Période | Frais | Trades | Espérance R | Hors force_exit | IC 90 % iid | IC 90 % blocs | DD réalisé | DD réévalué | DD95 permutation | DD95 blocs | Sharpe réalisé | Sharpe réévalué | Semestres + réalisés | DSR réévalué | DSR réalisé |
|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E01 | base (20/10/2.0/200) | 20210101-20240630 | 0,0005 | 135 | +0,134 | +0,124 | -0,115 à +0,408 | -0,132 à +0,403 | 10,9 % | 12,8 % | 10,9 % | 24,9 % | 0,43 | 0,31 | 4/7 | 0,433 | 0,573 |
| E02 | base | 20240701-20250731 | 0,0005 | 46 | +0,573 | +0,431 | -0,094 à +1,400 | -0,167 à +1,552 | 3,8 % | 8,3 % | 5,5 % | 13,9 % | 1,15 | 1,15 | 2/3 | 0,786 | 0,879 |
| E03 | entry 16 | 20210101-20250731 | 0,0005 | 178 | +0,485 | +0,452 | +0,074 à +1,002 | +0,071 à +1,008 | 8,8 % | 9,9 % | 9,5 % | 22,2 % | 0,71 | 0,87 | 7/10 | 0,845 | 0,931 |
| E04 | entry 24 | 20210101-20250731 | 0,0005 | 177 | +0,190 | +0,147 | -0,064 à +0,465 | -0,101 à +0,531 | 11,6 % | 14,4 % | 11,7 % | 28,0 % | 0,53 | 0,41 | 6/10 | 0,504 | 0,675 |
| E05 | exit 8 | 20210101-20250731 | 0,0005 | 188 | +0,254 | +0,216 | +0,010 à +0,520 | -0,030 à +0,573 | 10,4 % | 12,7 % | 10,2 % | 25,2 % | 0,71 | 0,57 | 6/10 | 0,642 | 0,835 |
| E06 | exit 12 | 20210101-20250731 | 0,0005 | 171 | +0,058 | +0,012 | -0,149 à +0,282 | -0,191 à +0,340 | 13,4 % | 16,5 % | 13,2 % | 33,4 % | 0,18 | 0,14 | 5/10 | 0,289 | 0,358 |
| E07 | atr_mult 1.6 | 20210101-20250731 | 0,0005 | 186 | +0,646 | +0,603 | +0,209 à +1,162 | +0,070 à +1,353 | 12,0 % | 17,7 % | 10,5 % | 30,1 % | 1,01 | 0,87 | 8/10 | 0,848 | 0,987 |
| E08 | atr_mult 2.4 | 20210101-20250731 | 0,0005 | 165 | +0,241 | +0,205 | -0,004 à +0,502 | -0,023 à +0,540 | 6,5 % | 9,1 % | 9,3 % | 22,0 % | 0,72 | 0,56 | 5/10 | 0,632 | 0,836 |
| E09 | base | 20210101-20250731 | 0,0010 | 178 | +0,259 | +0,219 | -0,012 à +0,553 | -0,044 à +0,605 | 11,1 % | 13,0 % | 11,1 % | 26,1 % | 0,69 | 0,54 | 6/10 | 0,620 | 0,814 |
| R01 | entry 15 | 20210101-20250731 | 0,0005 | 176 | +0,524 | +0,483 | +0,107 à +1,054 | +0,105 à +1,049 | 6,9 % | 9,6 % | 8,8 % | 21,3 % | 0,75 | 0,93 | 7/10 | 0,874 | 0,958 |
| R02 | entry 30 | 20210101-20250731 | 0,0005 | 171 | +0,207 | +0,167 | -0,086 à +0,514 | -0,119 à +0,573 | 13,4 % | 16,9 % | 13,1 % | 29,0 % | 0,50 | 0,41 | 7/10 | 0,510 | 0,648 |
| R03 | base | 20210101-20250731 | 0,0015 | 178 | +0,250 | +0,210 | -0,021 à +0,544 | -0,053 à +0,596 | 11,3 % | 13,2 % | 11,3 % | 26,5 % | 0,66 | 0,52 | 6/10 | 0,604 | 0,794 |
| E00-ref | base | 20210101-20250731 | 0,0005 | 178 | +0,268 | +0,228 | -0,003 à +0,562 | -0,035 à +0,614 | 10,9 % | 12,8 % | 10,9 % | 25,7 % | 0,71 | 0,56 | 6/10 | 0,635 | 0,832 |
| E10 | base | 20250801-20261031 | 0,0005 | verrouillé | | | | | | | | | | | | | |
| E11 | base | 20250801-20261031 | 0,0010 | verrouillé | | | | | | | | | | | | | |

E00-ref n'était pas préenregistré. Il est consigné comme essai de calcul et le § 13 explique pourquoi. Il donne 178 trades contre 181 pour E01 et E02 pris ensemble, car E01 ferme de force ses positions le 30/06/2024 et E02 repart sans position.

Le DSR réalisé n'est pas comparable d'un essai à l'autre. E07 et R01 ne passent 0,95 que sur la série réalisée et ce dépassement est un effet d'asymétrie, pas un résultat. Un seul jour de clôture y gonfle g3 et g4 puis écrase le dénominateur du PSR (§ 13). Aucune ligne n'atteint 0,95 en DSR réévalué.

Les sorties forcées de fin de fenêtre ferment une position à la borne de période et non par la règle de sortie. Sans elles, l'espérance baisse de 0,142 R sur E02 et de 0,040 R sur E00-ref. Elles portent 33 % du P&L de E02 et 19 % de celui de E00-ref. Le même chiffre sera donné pour E10 dans le rapport de verdict.

## 3. Données et verrou

Source, `freqtrade download-data` et `list-data`, 2026-10-31 entre 22:30:15Z et 22:33:28Z. Sorties brutes dans `brut/01_download-data.txt`, `brut/02_list-data.txt`, `brut/03_troncature_verrou.csv` et `brut/04_list-data_apres_troncature.txt`.

La commande demandait `--timerange 20200501-20250801`. Freqtrade a pourtant écrit des pages complètes au-delà de cette fin. Les bougies 1d allaient jusqu'au 16/10/2025 (25/12/2025 pour DOGE). Le mark 1h allait jusqu'au 16/08/2025 (03/08/2025 pour DOGE). Le financement allait jusqu'au 28/06/2026. La borne de fin de `--timerange` ne suffit donc pas comme verrou physique avec cette version.

Toutes les lignes datées à partir du 01/08/2025 00:00 UTC ont été supprimées à 22:33:27Z, soit avant le premier backtest de ce `user_data` (22:33:52Z). Six backtests de contrôle de format avaient déjà tourné entre 22:18:20Z et 22:29:11Z dans un dossier séparé, sur 3 paires et avec des données finissant au plus le 22/11/2023 (§ 16). Ces données sont restées sur le disque 3 min 12 s. Seules des dates et des nombres de lignes ont été affichés. Aucun prix ni taux de cette période n'a été affiché ou utilisé. Le script de troncature les a chargés en mémoire sans les afficher. La dernière clôture de tous les exports est au plus le 31/07/2025.

| Paires | Début 1d | Début mark | Début financement | Fin 1d | Fin mark | Fin financement | Lignes 1d / mark / financement |
|---|---|---|---|---|---|---|---|
| BTC, ETH, XRP, LTC, BCH, LINK, ADA, BNB, TRX (chacune) | 01/05/2020 | 01/05/2020 | 01/05/2020 | 31/07/2025 | 31/07/2025 23h | 31/07/2025 16h | 1918 / 46032 / 5754 |
| DOGE | 10/07/2020 | 10/07/2020 03h | 10/07/2020 08h | 31/07/2025 | 31/07/2025 23h | 31/07/2025 16h | 1848 / 44349 / 5543 |

Les séries sont complètes pour les neuf premières paires (24 lignes de mark et 3 de financement par jour). Le financement et le mark sont présents pour les 10 paires.

Effet sur la chauffe de 220 jours. Pour E01, freqtrade charge à partir du 26/05/2020 et la chauffe est donc complète pour neuf paires au 01/01/2021. DOGE commence plus tard. Sa moyenne 200 jours existe à partir du 25/01/2021. D'après le code de `trim_dataframe`, freqtrade retire 220 bougies depuis le début de la paire et DOGE ne devient donc négociable que vers le 15/02/2021 [déduit du code, non observé directement]. Sa première entrée, tous essais confondus, date du 04/05/2021. E01 démarre donc à neuf paires pendant environ 45 jours.

## 4. Contrôles de biais

Source, `brut/E01_lookahead-analysis.txt`, `brut/E01_lookahead-analysis_elargi.txt` et `brut/E01_recursive-analysis.txt`, 2026-10-31 entre 22:34:30Z et 22:40:56Z, période 20210101-20240630.

| Contrôle | Options | Résultat |
|---|---|---|
| lookahead-analysis | défaut (20 signaux visés) | has_bias No, 20 signaux, 0 entrée biaisée, 0 sortie biaisée |
| lookahead-analysis élargi | `--minimum-trade-amount 50 --targeted-trade-amount 300` | has_bias No, 271 signaux, 0 entrée biaisée, 0 sortie biaisée, 6 sorties forcées écartées par l'outil |
| recursive-analysis | sans `--fee`, refusé par la commande | atr 0,000 % pour 199 et 220 bougies, -0,000 % pour 399, aucun écart à 499 et au-delà, « No lookahead bias on indicators found » |

Ces deux outils ne testent pas les rappels `custom_stake_amount` et `custom_stoploss`, et recursive-analysis ne regarde que BTC. Un contrôle indépendant a donc été ajouté (`brut/controles_complementaires.txt`, 22:49 UTC environ). Sur E00-ref, la mise rapportée à la cible calculée avec l'ATR de la veille est stable sur les paires à petit prix, médiane 0,990, p5 0,988 et p95 0,990. Le 0,99 est `tradable_balance_ratio`. Avec l'ATR du jour, le même rapport va de 0,957 à 1,157. La mise n'utilise donc pas la bougie en cours. La distance de stop vaut entre 0,998 et 1,000 fois 2 ATR de la veille sur les 178 trades.

Le contrôle a été étendu aux 10 paires le 01/11/2026 (`controles/sorties/t6_signaux_troncature.txt`). Le code de la stratégie et un recalcul indépendant donnent 0 écart de signal. Une troncature à 250 dates aléatoires par paire donne 0 écart sur 1500 comparaisons par paire. Les indicateurs restent donc propres hors BTC.

Ces outils ont trois limites. Le décompte du lancement élargi n'est pas fermé, car 271 signaux testés et 6 sorties forcées écartées laissent 1 cas sur 278 [non élucidé]. L'outil force `max_open_trades` à -1 et valide donc les signaux et les indicateurs, pas l'attribution des places. `recursive-analysis` ne contrôle l'absence de biais d'indicateur qu'à une date (2021-01-11).

L'attribution des places contient une anticipation que `lookahead-analysis` ne teste pas. Freqtrade traite d'abord les paires déjà en position dans la bougie. Un stop touché dans la journée libère donc sa place avant les entrées, et une position s'ouvre à l'ouverture du jour avec une place qui n'était pas libre à cette heure. L'équité servant à la mise inclut aussi cette perte future, avec une mise jusqu'à 1,054 fois la cible calculée sur l'équité de la veille (`t2_mises_financement_E01.txt`). Le rejeu indépendant retrouve 178 trades sur 178 et compte 6 entrées de ce type sur E01, 1 sur E02 et 6 sur E00-ref. En réel, le signal reste valide toute la bougie et l'entrée se ferait plus tard au prix du moment [déduit du code, non observé].

Le tableau ci-dessous donne une sensibilité seulement, par simulation et non par freqtrade. Il ne remplace jamais la base. La règle stricte interdit de réutiliser le jour même une place libérée par un stop. Son gain tient à un effet de chaîne sur très peu de trades, car 3 trades propres à cette règle portent +1 126 USDT sur E01. Le chiffre publié dépend donc d'une règle impossible à reproduire en réel, sans que le sens observé soit flatteur pour la base.

| Essai | Rejeu base (trades, R, USDT) | Règle stricte (trades, R, USDT) |
|---|---|---|
| E01 | 135, +0,137, +896 | 129, +0,333, +2 196 |
| E02 | 46, +0,579, +1 282 | 46, +0,567, +1 250 |
| E00-ref | 178, +0,272, +2 499 | 172, +0,423, +3 979 |

Le risque réel est un peu sous les 0,5 % annoncés. S'y ajoute le facteur 0,99 de `tradable_balance_ratio`. Le pas de quantité sur BTC retire jusqu'à 10 % de plus, avec une mise rapportée à la cible médiane de 0,960 et minimale de 0,907, les autres paires restant au moins à 0,99 (E01). La perte stressée prévue va donc de 0,449 % à 0,495 % du capital. Ce pas vient des marchés actuels appliqués à des prix de 2021 [non vérifié pour les anciens pas]. L'effet est sans conséquence sur le signal et légèrement conservateur.

## 5. Financement payé

Source, champ `funding_fees` des exports, déjà inclus dans le P&L. Le financement est appliqué. Il est non nul sur 134 trades sur 135 pour E01 et 177 sur 178 pour E00-ref. Un recalcul indépendant depuis les fichiers (taux x mark x quantité) redonne -665,282 USDT pour E01 et -768,379 USDT pour E00-ref, avec un écart moyen nul à cinq décimales.

| Essai | Longs (trades, espérance R, P&L) | Shorts (trades, espérance R, P&L) | Payé | Reçu | Net payé | dont longs | dont shorts | Frais |
|---|---|---|---:|---:|---:|---:|---:|---:|
| E01 | 70, +0,331, +1 157 | 65, -0,078, -280 | 792 | 127 | 665 | 689 | -24 | 65 |
| E02 | 26, +1,226, +1 558 | 20, -0,274, -288 | 121 | 26 | 95 | 103 | -8 | 26 |
| E03 | 96, +0,950, +5 120 | 82, -0,059, -339 | 1 005 | 172 | 834 | 865 | -31 | 103 |
| E04 | 93, +0,545, +2 533 | 84, -0,202, -890 | 920 | 144 | 776 | 788 | -11 | 88 |
| E05 | 100, +0,574, +2 994 | 88, -0,109, -541 | 924 | 140 | 784 | 812 | -28 | 96 |
| E06 | 89, +0,277, +1 142 | 82, -0,181, -742 | 851 | 137 | 714 | 751 | -36 | 80 |
| E07 | 94, +1,440, +8 026 | 92, -0,166, -1 111 | 1 841 | 215 | 1 626 | 1 652 | -27 | 157 |
| E08 | 88, +0,522, +2 399 | 77, -0,080, -357 | 775 | 128 | 647 | 678 | -31 | 70 |
| E09 | 95, +0,596, +2 951 | 83, -0,126, -587 | 924 | 156 | 768 | 800 | -32 | 183 |
| R01 | 96, +0,986, +5 408 | 80, -0,030, -197 | 1 021 | 176 | 845 | 875 | -31 | 102 |
| R02 | 91, +0,667, +3 026 | 80, -0,317, -1 323 | 898 | 169 | 730 | 726 | 3 | 85 |
| R03 | 95, +0,586, +2 885 | 83, -0,134, -620 | 923 | 156 | 767 | 799 | -32 | 273 |
| E00-ref | 95, +0,606, +3 020 | 83, -0,119, -559 | 925 | 157 | 768 | 801 | -33 | 92 |

Sur E00-ref, le financement net payé (768 USDT) représente 31 % du P&L final de 2 461 USDT et environ huit fois les frais. Le coût qui pèse est donc le financement et non les frais de transaction.

## 6. Longs contre shorts

Le tableau du § 5 donne le détail. Les shorts ont une espérance négative dans la base, sur E01, E02 et E00-ref. Sur E00-ref, les longs donnent +0,606 R sur 95 trades et les shorts -0,119 R sur 83 trades. Tout le gain vient donc des longs sur une période où le panier de la fiche a fortement monté (Market change freqtrade de 895,85 % sur 20210101-20250731). Ce constat est décrit ici sans aucun changement de règle, car retirer les shorts serait une nouvelle stratégie.

## 7. Résultat par paire

Source, exports E01, E02 et E00-ref, calcul de `brut/controles.py`. Le R est nominal.

E01.

| Paire | Trades | Réussite | Espérance R | Somme R | P&L USDT | Financement net payé | Première entrée |
|---|---:|---:|---:|---:|---:|---:|---|
| LINK | 11 | 55 % | +1,059 | +11,65 | +598 | 92 | 2021-01-16 |
| ADA | 10 | 70 % | +0,817 | +8,17 | +425 | 30 | 2021-05-14 |
| BTC | 15 | 47 % | +0,455 | +6,82 | +355 | 95 | 2021-01-03 |
| ETH | 16 | 31 % | +0,360 | +5,75 | +282 | 264 | 2021-01-03 |
| BCH | 17 | 18 % | +0,167 | +2,84 | +133 | -8 | 2021-01-04 |
| XRP | 17 | 35 % | +0,008 | +0,13 | -6 | 140 | 2021-01-31 |
| BNB | 8 | 38 % | -0,044 | -0,35 | -16 | -13 | 2021-05-04 |
| TRX | 14 | 29 % | -0,058 | -0,81 | -52 | 42 | 2021-04-01 |
| DOGE | 9 | 22 % | -0,500 | -4,50 | -238 | 6 | 2021-10-29 |
| LTC | 18 | 11 % | -0,645 | -11,61 | -605 | 16 | 2021-01-04 |

E02.

| Paire | Trades | Réussite | Espérance R | Somme R | P&L USDT | Financement net payé | Première entrée |
|---|---:|---:|---:|---:|---:|---:|---|
| DOGE | 2 | 50 % | +6,597 | +13,19 | +634 | 34 | 2024-10-19 |
| ADA | 4 | 25 % | +2,873 | +11,49 | +544 | 20 | 2024-09-04 |
| ETH | 5 | 60 % | +1,086 | +5,43 | +291 | 1 | 2024-07-05 |
| BTC | 7 | 43 % | +0,649 | +4,54 | +225 | 45 | 2024-07-05 |
| BCH | 6 | 33 % | +0,029 | +0,17 | +16 | -1 | 2024-07-29 |
| TRX | 6 | 50 % | +0,017 | +0,10 | +9 | -4 | 2024-07-02 |
| LTC | 3 | 0 % | -0,353 | -1,06 | -57 | -1 | 2024-08-03 |
| LINK | 4 | 25 % | -0,405 | -1,62 | -88 | 0 | 2024-08-03 |
| BNB | 3 | 0 % | -0,795 | -2,39 | -122 | -1 | 2024-08-23 |
| XRP | 6 | 0 % | -0,583 | -3,50 | -183 | 2 | 2024-07-05 |

E00-ref.

| Paire | Trades | Réussite | Espérance R | Somme R | P&L USDT | Financement net payé | Première entrée |
|---|---:|---:|---:|---:|---:|---:|---|
| ADA | 14 | 57 % | +1,349 | +18,88 | +985 | 51 | 2021-05-14 |
| ETH | 20 | 40 % | +0,607 | +12,14 | +657 | 267 | 2021-01-03 |
| BTC | 22 | 45 % | +0,515 | +11,34 | +604 | 145 | 2021-01-03 |
| LINK | 15 | 47 % | +0,642 | +9,62 | +478 | 91 | 2021-01-16 |
| DOGE | 11 | 27 % | +0,790 | +8,69 | +464 | 44 | 2021-10-29 |
| BCH | 23 | 22 % | +0,131 | +3,01 | +151 | -9 | 2021-01-04 |
| TRX | 19 | 42 % | +0,097 | +1,84 | +96 | 35 | 2021-04-01 |
| BNB | 11 | 27 % | -0,248 | -2,73 | -150 | -14 | 2021-05-04 |
| XRP | 22 | 27 % | -0,109 | -2,40 | -156 | 143 | 2021-01-31 |
| LTC | 21 | 10 % | -0,603 | -12,66 | -668 | 15 | 2021-01-04 |

LTC perd sur les trois lignes et concentre la plus forte perte de E00-ref (-668 USDT, 21 trades, 10 % de réussite). Le classement des paires change beaucoup entre E01 et E02. DOGE et ADA portent E02 avec peu de trades (2 et 4).

## 8. Semestres

Source, `resultats/<essai>_metriques.json`, essai E00-ref. La colonne réalisée affecte chaque trade à sa date de clôture. La colonne réévaluée donne la variation de l'équité réévaluée sur le semestre. Le second semestre 2025 est partiel (31 jours) et son Sharpe annualisé n'a pas de sens.

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé USDT | P&L réévalué USDT |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,788 | 1,43 | 1,5 % | +433 | +362 |
| 2021-S2 | 184 | 24 | -0,080 | -0,36 | 4,4 % | -111 | +17 |
| 2022-S1 | 181 | 9 | +0,855 | 2,14 | 0,5 % | +399 | +741 |
| 2022-S2 | 184 | 23 | -0,302 | -1,54 | 5,9 % | -381 | -732 |
| 2023-S1 | 181 | 26 | -0,311 | -2,62 | 5,5 % | -409 | +175 |
| 2023-S2 | 184 | 18 | +0,191 | 0,50 | 2,4 % | +163 | +379 |
| 2024-S1 | 182 | 22 | +0,619 | 1,48 | 1,7 % | +693 | -107 |
| 2024-S2 | 184 | 22 | +1,060 | 1,74 | 1,8 % | +1 238 | +1 483 |
| 2025-S1 | 181 | 19 | +0,015 | -0,07 | 2,1 % | -25 | -219 |
| 2025-S2 (partiel) | 31 | 4 | +1,920 | non significatif | 0,1 % | +461 | +363 |

| Essai | Positifs réalisés | Hors semestre partiel | Positifs réévalués | Réévalués hors semestre partiel |
|---|---:|---:|---:|---:|
| E01 | 4/7 | 4/7 | 5/7 | 5/7 |
| E02 | 2/3 | 1/2 | 2/3 | 1/2 |
| E03 | 7/10 | 6/9 | 8/10 | 7/9 |
| E04 | 6/10 | 5/9 | 6/10 | 5/9 |
| E05 | 6/10 | 5/9 | 6/10 | 5/9 |
| E06 | 5/10 | 4/9 | 4/10 | 3/9 |
| E07 | 8/10 | 7/9 | 8/10 | 7/9 |
| E08 | 5/10 | 4/9 | 7/10 | 6/9 |
| E09 | 6/10 | 5/9 | 7/10 | 6/9 |
| R01 | 7/10 | 6/9 | 8/10 | 7/9 |
| R02 | 7/10 | 6/9 | 8/10 | 7/9 |
| R03 | 6/10 | 5/9 | 7/10 | 6/9 |
| E00-ref | 6/10 | 5/9 | 7/10 | 6/9 |

L'affectation à la clôture déforme la datation. Sur E00-ref, 20 trades à cheval sur deux semestres portent 75 % du P&L, soit +1 854 USDT sur +2 461 (`controles/sorties/verif2.txt` section 7). Trois semestres changent de signe une fois réévalués, soit 2021-S2, 2023-S1 et 2024-S1. Le nombre de semestres positifs n'est donc pas flatté, mais la datation des pertes et des gains l'est.

En base réalisée, les semestres négatifs de 2022-S2 et 2023-S1 semblent former une phase de perte de juillet 2022 à juin 2023. Cette phase tient en partie à l'artefact, car 2023-S1 passe de -409 à +175 et 2022-S2 de -381 à -732. La perte réévaluée se concentre donc sur 2022-S2. Le gain de 2024-S1 (+693) devient -107. Le semestre partiel 2025-S2 (+461 USDT réalisés) tient presque entièrement à 3 force_exit (+470 USDT).

## 9. Robustesse aux paramètres voisins

Source, E00-ref et variantes sur 20210101-20250731, frais 0,0005. Les variantes sont des sous-classes dans `user_data/strategies/`. Aucune n'est retenue à la place de la base. Les colonnes « sans le meilleur » et « sans les 3 meilleurs » retirent ces trades de la moyenne sans rejouer le backtest.

| Essai | Paramètre | Espérance R | IC 90 % iid | IC 90 % blocs | Sans le meilleur | Sans les 3 meilleurs | Meilleur trade | R max | DD réalisé | DD réévalué | Sharpe réévalué | DSR réévalué |
|---|---|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| R01 | entry 15 | +0,524 | +0,107 à +1,054 | +0,105 à +1,049 | +0,271 | +0,163 | XRP 2024-11-08 long | 44,8 | 6,9 % | 9,6 % | 0,93 | 0,874 |
| E03 | entry 16 | +0,485 | +0,074 à +1,002 | +0,071 à +1,008 | +0,235 | +0,128 | XRP 2024-11-08 long | 44,8 | 8,8 % | 9,9 % | 0,87 | 0,845 |
| E00-ref | base 20 / 10 / 2,0 | +0,268 | -0,003 à +0,562 | -0,035 à +0,614 | +0,193 | +0,058 | DOGE 2024-10-19 long | 13,5 | 10,9 % | 12,8 % | 0,56 | 0,635 |
| E04 | entry 24 | +0,190 | -0,064 à +0,465 | -0,101 à +0,531 | +0,115 | -0,023 | DOGE 2024-10-19 long | 13,5 | 11,6 % | 14,4 % | 0,41 | 0,504 |
| R02 | entry 30 | +0,207 | -0,086 à +0,514 | -0,119 à +0,573 | +0,128 | -0,026 | DOGE 2024-10-19 long | 13,5 | 13,4 % | 16,9 % | 0,41 | 0,510 |
| E05 | exit 8 | +0,254 | +0,010 à +0,520 | -0,030 à +0,573 | +0,183 | +0,055 | DOGE 2024-10-19 long | 13,5 | 10,4 % | 12,7 % | 0,57 | 0,642 |
| E06 | exit 12 | +0,058 | -0,149 à +0,282 | -0,191 à +0,340 | -0,004 | -0,075 | ADA 2024-11-08 long | 10,5 | 13,4 % | 16,5 % | 0,14 | 0,289 |
| E07 | atr 1,6 | +0,646 | +0,209 à +1,162 | +0,070 à +1,353 | +0,478 | +0,241 | ADA 2021-01-04 long | 31,7 | 12,0 % | 17,7 % | 0,87 | 0,848 |
| E08 | atr 2,4 | +0,241 | -0,004 à +0,502 | -0,023 à +0,540 | +0,174 | +0,051 | DOGE 2024-10-19 long | 11,3 | 6,5 % | 9,1 % | 0,56 | 0,632 |

Les six voisins préenregistrés à ±20 % ont tous une espérance positive, de +0,058 à +0,646 R. L'écart est large pour des variations aussi faibles. E06 (exit 12) tombe à +0,058 R et devient nul sans son meilleur trade. Les valeurs élevées de E03 et R01 tiennent pour moitié à un seul trade (XRP de novembre 2024 à +44,8 R). E07 dépend moins d'un seul trade (ADA de janvier 2021 à +31,7 R) et retombe à +0,241 R sans ses trois meilleurs. Son drawdown réévalué atteint 17,7 %, proche du seuil de 20 % de la fiche, alors que sa ligne réalisée affiche 12,0 %. La limite de 3 positions rend le résultat très dépendant du chemin, car E00-ref rejette 575 signaux d'entrée. Une petite variation change les trades qui obtiennent une place.

La base n'est pas le meilleur essai du registre. Ce constat ne change rien, car les variantes ne sont jamais substituées à la base.

### Ordre de la whitelist, sixième paramètre non déclaré

Quand plus de signaux que de places arrivent le même jour, freqtrade sert les paires dans l'ordre du dictionnaire des données (`time_pair_generator`, `list(data.keys())`). Cet ordre vient de `pair_whitelist` dans la configuration. La fiche ne donne aucune règle de priorité et annonce 5 paramètres libres, alors que cet ordre en constitue un sixième. Ni l'IC ni le DSR ne le captent. Le sens n'est pas flatteur, car la base se situe plutôt sous la médiane. L'instabilité est le problème, pas le biais.

Le premier tableau vient de backtests freqtrade réels du contradicteur, avec les mêmes règles et seul l'ordre changé. Ils datent du 2026-10-31 entre 23:50Z et 23:52Z et n'ont pas été relancés (`controles/sorties_contradicteur/run_*.txt`, journaux en heure locale). Le second vient du rejeu indépendant de 200 ordres tirés avec la graine 0, rejoué le 01/11/2026 à l'identique (`controles/sorties/t5_permutations_ordre_places_strictes.txt`, `t5_ordres_*.csv`). Ces lignes servent de lecture, aucune n'est retenue et aucun ordre n'est choisi à cause de sa performance.

| Essai | Ordre de la config (trades, USDT) | Ordre inverse (trades, USDT) | Ordre alphabétique (trades, USDT) |
|---|---|---|---|
| E01 | 135, +877 | 136, +1 968 | 126, +3 072 |
| E02 | 46, +1 270 | 46, +1 356 | 45, +1 242 |
| E00-ref | 178, +2 461 | 179, +3 662 | 169, +4 698 |

| Essai | Rejeu base R | Min | p5 | Médiane | p95 | Max | Part des ordres à 0,2 R ou moins | Part des ordres qui égalent ou dépassent la base |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E01 | +0,137 | +0,011 | +0,044 | +0,189 | +0,389 | +0,468 | 53,5 % | 67,5 % |
| E02 | +0,579 | +0,420 | +0,501 | +0,618 | +0,711 | +0,783 | 0,0 % | 68,0 % |
| E00-ref | +0,272 | +0,175 | +0,207 | +0,305 | +0,463 | +0,528 | 2,5 % | 65,5 % |

La position de E01 et de E00-ref face au seuil de 0,2 R dépend donc en partie de cet ordre. Le rejeu ne modélise pas le pas de quantité et s'écarte un peu des exports (+896 USDT contre +877 sur E01). Sa base n'est donc pas exactement celle du § 2. E10 ne donnera qu'un chemin parmi beaucoup, et l'avenant propose de le présenter avec cette distribution à titre de lecture.

## 10. Concentration du gain

Source, `resultats/controles_complementaires.json`.

| Essai | P&L USDT | Part du meilleur trade | Part des 3 meilleurs | Meilleur mois | Part du meilleur mois | Mois positifs |
|---|---:|---:|---:|---|---:|---:|
| E01 | +877 | 62 % | 146 % | 2024-01 | 52 % | 18/38 |
| E02 | +1 270 | 51 % | 124 % | 2024-12 | 99 % | 5/13 |
| E00-ref | +2 461 | 29 % | 81 % | 2024-12 | 56 % | 24/51 |
| E09 | +2 364 | 30 % | 83 % | 2024-12 | 58 % | 23/51 |

Une part supérieure à 100 % signifie que ces trades dépassent le gain total. Sur E00-ref, décembre 2024 porte 56 % du gain et trois trades en portent 81 %. Le repère de `validation-edge` § 4.4 demande qu'aucun mois ni trade unique ne porte l'essentiel du gain. Le mois de décembre 2024 dépasse la moitié du gain sur E00-ref, à titre indicatif.

## 11. Risque réalisé

Source, exports, R nominal (profit / 0,5 % de l'équité de référence). La cible d'un trade arrêté au stop est de 1 R.

| Essai | Stops | Perte moyenne R | Médiane R | Rapport à 1 R | Pire stop R | Moins grave R |
|---|---:|---:|---:|---:|---:|---:|
| E01 | 56 | -0,994 | -0,983 | 0,99 | -1,257 | -0,914 |
| E02 | 16 | -0,969 | -0,977 | 0,97 | -1,002 | -0,900 |
| E00-ref | 69 | -0,990 | -0,983 | 0,99 | -1,257 | -0,914 |
| E07 | 82 | -0,979 | -0,977 | 0,98 | -1,038 | -0,896 |
| E08 | 49 | -0,990 | -0,989 | 0,99 | -1,131 | -0,852 |

Sur E00-ref, la perte moyenne au stop vaut 0,99 R (69 stops) et se décompose en 0,967 R de prix, 0,009 R de frais et 0,014 R de financement net. Le pire stop atteint -1,257 R (ETH long du 05/12/2023 au 03/01/2024, dont -0,284 R de financement). Aucun stop ne dépasse 1,5 R. Environ 16 % des stops dépassent 1 R. Hors stops, la pire sortie vaut -0,91 R et le meilleur trade +13,54 R.

Cette mesure reste favorable par construction. Le backtest ne prend l'ouverture que si le stop est hors de toute la bougie (`optimize/backtesting.py`, lignes 612 à 617). Une ouverture au-delà du stop avec une bougie qui revient au stop remplit donc au prix du stop, ce qui est favorable. L'effet observé est nul, avec 0 ouverture au-delà du stop sur E01, E02 et E00-ref (`t8_gaps_verrou_qualite.txt`). Aucun glissement séparé n'est modélisé et un stop réel peut donc coûter davantage [non mesuré sur marché réel].

Le mark 1h donne une borne absente de la version précédente (`t7_glissement_financement_mark1h.txt`). Il n'y a aucune ouverture horaire au-delà du stop. L'extension du prix au-delà du stop dans l'heure de franchissement vaut en moyenne 0,112 R sur E00-ref et au plus 0,603 R. C'est une borne haute et non un glissement mesuré. 5 stops de E00-ref ne sont pas atteints sur le mark 1h ce jour-là et sont donc touchés seulement sur le dernier prix.

La mise moyenne vaut 4,7 % de l'équité sur E00-ref et la plus forte 13,8 %. Le plafond de 20 % par actif n'a jamais été atteint. Trois positions au plus donnent donc une exposition inférieure à 42 %.

## 12. Drawdown réévalué chaque jour

`analyse_strat.py` calcule désormais les deux bases pour tous les essais et le fera pour E10 et E11. La base réévaluée ajoute le P&L latent au prix de clôture 1d, hors frais et financement latents. Source, `resultats/<id>_metriques.json`. Avec frais et financement courus, un contrôle donne pour E00-ref un Sharpe de 0,565 et un drawdown de 12,3 % (`controles/sorties/verif2.txt`, section 1). Le chiffre de 12,8 % reste donc prudent.

| Essai | DD réalisé | DD réévalué | Creux | DD95 permutation | DD médian blocs | DD95 blocs | Sharpe réalisé | Sharpe réévalué | Sortino réalisé | Sortino réévalué | Calmar réalisé | Calmar réévalué |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E01 | 10,9 % | 12,8 % | 2023-06-09 | 10,9 % | 13,7 % | 24,9 % | 0,43 | 0,31 | 1,09 | 0,44 | 0,22 | 0,19 |
| E02 | 3,8 % | 8,3 % | 2025-06-24 | 5,5 % | 7,6 % | 13,9 % | 1,15 | 1,15 | 4,90 | 1,86 | 3,10 | 1,40 |
| E03 | 8,8 % | 9,9 % | 2024-11-05 | 9,5 % | 13,1 % | 22,2 % | 0,71 | 0,87 | 4,15 | 1,32 | 1,02 | 0,90 |
| E04 | 11,6 % | 14,4 % | 2023-05-15 | 11,7 % | 15,8 % | 28,0 % | 0,53 | 0,41 | 1,57 | 0,59 | 0,29 | 0,23 |
| E05 | 10,4 % | 12,7 % | 2023-07-30 | 10,2 % | 14,2 % | 25,2 % | 0,71 | 0,57 | 2,23 | 0,84 | 0,47 | 0,39 |
| E06 | 13,4 % | 16,5 % | 2024-10-05 | 13,2 % | 18,8 % | 33,4 % | 0,18 | 0,14 | 0,42 | 0,19 | 0,06 | 0,05 |
| E07 | 12,0 % | 17,7 % | 2023-06-09 | 10,5 % | 18,0 % | 30,1 % | 1,01 | 0,87 | 5,21 | 1,35 | 1,01 | 0,69 |
| E08 | 6,5 % | 9,1 % | 2023-06-22 | 9,3 % | 12,3 % | 22,0 % | 0,72 | 0,56 | 2,14 | 0,82 | 0,64 | 0,46 |
| E09 | 11,1 % | 13,0 % | 2023-06-09 | 11,1 % | 14,8 % | 26,1 % | 0,69 | 0,54 | 2,07 | 0,80 | 0,43 | 0,37 |
| R01 | 6,9 % | 9,6 % | 2025-06-24 | 8,8 % | 12,6 % | 21,3 % | 0,75 | 0,93 | 4,64 | 1,41 | 1,38 | 1,00 |
| R02 | 13,4 % | 16,9 % | 2023-05-15 | 13,1 % | 16,3 % | 29,0 % | 0,50 | 0,41 | 1,52 | 0,60 | 0,26 | 0,21 |
| R03 | 11,3 % | 13,2 % | 2023-06-09 | 11,3 % | 15,0 % | 26,5 % | 0,66 | 0,52 | 1,98 | 0,77 | 0,40 | 0,34 |
| E00-ref | 10,9 % | 12,8 % | 2023-06-09 | 10,9 % | 14,6 % | 25,7 % | 0,71 | 0,56 | 2,17 | 0,82 | 0,45 | 0,39 |

Le Sortino est la métrique la plus flattée par la base réalisée, d'un facteur 2,5 à 2,6 sur les lignes de base E00-ref à E09. Le biais du Sharpe n'a pas de sens fixe. Il flatte la base (0,71 puis 0,56 sur E00-ref) mais sous-estime E03 et R01 (0,71 puis 0,87 et 0,75 puis 0,93). Les colonnes réalisées ne sont donc pas comparables d'un essai à l'autre.

Le DD95 par permutation ne se comporte pas comme une borne. Le drawdown réalisé le dépasse sur 6 essais sur 13 et le drawdown réévalué sur 12 sur 13. Il reste affiché à titre de comparaison et le drawdown réévalué devient le chiffre de référence au § 14. Le Monte Carlo tire maintenant des blocs de 30 jours de rendements réévalués, ce qui garde la dépendance entre jours. Il refait une trajectoire aussi longue que l'essai et décrit donc une dispersion possible du drawdown. Le DD95 par blocs de E00-ref (25,7 %) dépasse 20 % avec une médiane de 14,6 %. Ce n'est pas le critère de la fiche, qui porte sur le drawdown hors échantillon. Avec des blocs de 15 ou 60 jours, ce DD95 vaut 26,6 % et 23,7 % (`controles/sorties/ic_sensibilite.txt`).

## 13. Sharpe déflaté

Choix des entrées. Le calcul principal porte sur la série réévaluée avec une V[SR] réévaluée. Le calcul sur la série réalisée reste affiché en second. E01 et E02 couvrent des périodes différentes des autres essais. Leur Sharpe mesure aussi un effet de régime et n'entre donc pas dans V[SR]. E00-ref a été ajouté pour que la base existe sur la même période que les variantes. V[SR] est donc calculée sur les 11 essais de 20210101-20250731, soit E00-ref, E03 à E09, R01, R02 et R03. V[SR] quotidienne vaut 1,519e-04 en réévalué et 1,133e-04 en réalisé. Source, `resultats/registre_dsr.json` et `resultats/sensibilite_dsr.json`.

N vaut 13, soit les essais de ce `user_data`. La demande citait 12 essais (E01 à E09, R01 à R03). E00-ref s'y ajoute car il a été lancé, ce qui est le choix le plus prudent. Six contrôles de format antérieurs (3 paires, § 16) et sept backtests du contradicteur ont aussi tourné avec la stratégie de base. Ils ne sélectionnent rien et restent hors N, marqués comme tels au registre. Le tableau donne donc N = 19 et N = 26 en sensibilité, ainsi que N = 12 et N = 11. E10 et E11 ne sont pas comptés.

| Essai | T | Sharpe réévalué | g3 | g4 | DSR réévalué principal (N 13, V 11 essais) | N 12 | N 11 | N 19 | N 26 | V sur 9 essais à mêmes frais | V théorique 1/T |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E01 | 1277 | 0,310 | -0,29 | 9,1 | 0,433 | 0,439 | 0,447 | 0,403 | 0,380 | 0,400 | 0,131 |
| E02 | 396 | 1,151 | 0,81 | 17,9 | 0,786 | 0,789 | 0,792 | 0,774 | 0,763 | 0,772 | 0,304 |
| E03 | 1673 | 0,874 | 0,31 | 14,9 | 0,845 | 0,850 | 0,855 | 0,823 | 0,805 | 0,821 | 0,567 |
| E04 | 1673 | 0,406 | -0,02 | 12,0 | 0,504 | 0,512 | 0,520 | 0,469 | 0,442 | 0,466 | 0,202 |
| E05 | 1673 | 0,572 | 0,01 | 12,4 | 0,642 | 0,650 | 0,658 | 0,609 | 0,583 | 0,606 | 0,316 |
| E06 | 1673 | 0,139 | -1,37 | 24,6 | 0,289 | 0,295 | 0,303 | 0,260 | 0,238 | 0,257 | 0,081 |
| E07 | 1673 | 0,872 | 1,10 | 26,4 | 0,848 | 0,852 | 0,857 | 0,826 | 0,807 | 0,823 | 0,566 |
| E08 | 1673 | 0,558 | 0,01 | 12,2 | 0,632 | 0,639 | 0,647 | 0,598 | 0,571 | 0,595 | 0,306 |
| E09 | 1673 | 0,544 | 0,03 | 12,0 | 0,620 | 0,628 | 0,636 | 0,586 | 0,560 | 0,583 | 0,295 |
| R01 | 1673 | 0,934 | 0,29 | 15,0 | 0,874 | 0,878 | 0,882 | 0,854 | 0,838 | 0,852 | 0,617 |
| R02 | 1673 | 0,412 | 0,01 | 12,6 | 0,510 | 0,517 | 0,526 | 0,475 | 0,447 | 0,471 | 0,206 |
| R03 | 1673 | 0,525 | 0,02 | 12,0 | 0,604 | 0,612 | 0,620 | 0,570 | 0,543 | 0,567 | 0,281 |
| E00-ref | 1673 | 0,563 | 0,03 | 12,0 | 0,635 | 0,643 | 0,651 | 0,602 | 0,575 | 0,599 | 0,309 |

Calcul second, sur la série réalisée, non comparable d'un essai à l'autre.

| Essai | Sharpe réalisé | g3 | g4 | Dénominateur du PSR | DSR réalisé (N 13, V 11 essais) | N 12 | N 11 | N 19 | N 26 | V sur 9 essais | V 1/T | Hypothèse normale (g3 0, g4 3) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E01 | 0,435 | 9,0 | 128 | 0,811 | 0,573 | 0,579 | 0,586 | 0,544 | 0,521 | 0,540 | 0,162 | 0,566 |
| E02 | 1,146 | 10,0 | 115 | 0,505 | 0,879 | 0,881 | 0,884 | 0,868 | 0,860 | 0,867 | 0,237 | 0,797 |
| E03 | 0,708 | 29,2 | 1029 | 0,271 | 0,931 | 0,936 | 0,940 | 0,910 | 0,890 | 0,907 | 0,359 | 0,780 |
| E04 | 0,526 | 11,5 | 182 | 0,717 | 0,675 | 0,682 | 0,690 | 0,642 | 0,616 | 0,638 | 0,248 | 0,650 |
| E05 | 0,714 | 10,8 | 159 | 0,652 | 0,835 | 0,840 | 0,846 | 0,810 | 0,790 | 0,807 | 0,414 | 0,784 |
| E06 | 0,183 | 8,4 | 117 | 0,922 | 0,358 | 0,364 | 0,371 | 0,329 | 0,307 | 0,325 | 0,086 | 0,363 |
| E07 | 1,010 | 14,8 | 270 | 0,405 | 0,987 | 0,988 | 0,989 | 0,983 | 0,978 | 0,982 | 0,765 | 0,922 |
| E08 | 0,716 | 10,7 | 159 | 0,653 | 0,836 | 0,841 | 0,847 | 0,812 | 0,792 | 0,809 | 0,417 | 0,786 |
| E09 | 0,687 | 10,7 | 156 | 0,667 | 0,814 | 0,820 | 0,825 | 0,788 | 0,767 | 0,785 | 0,388 | 0,767 |
| R01 | 0,749 | 29,3 | 1032 | 0,247 | 0,958 | 0,961 | 0,964 | 0,943 | 0,928 | 0,941 | 0,420 | 0,805 |
| R02 | 0,498 | 11,3 | 170 | 0,734 | 0,648 | 0,655 | 0,663 | 0,614 | 0,588 | 0,610 | 0,229 | 0,627 |
| R03 | 0,662 | 10,6 | 156 | 0,678 | 0,794 | 0,800 | 0,806 | 0,767 | 0,745 | 0,763 | 0,365 | 0,751 |
| E00-ref | 0,711 | 10,7 | 157 | 0,656 | 0,832 | 0,837 | 0,843 | 0,808 | 0,787 | 0,804 | 0,411 | 0,782 |

V n'est pas cohérente pour E01 et E02. Ces deux essais sont écartés de V pour éviter l'effet de régime, puis jugés avec une V mesurée sur 1673 jours. Les valeurs du tableau principal pour ces deux lignes ne sont donc pas centrales sans cette réserve. La V tranchée coupe les 11 séries sur la fenêtre de l'essai, sans rejeu de backtest, et reste une approximation. La V mise à l'échelle vaut V x 1673 / T.

| Essai | Série | V commune, DSR | V tranchée | DSR | V mise à l'échelle | DSR | V = 1/T, DSR |
|---|---|---:|---:|---:|---:|---:|---:|
| E01 | réévaluée | 0,433 | 1,649e-04 | 0,420 | 1,990e-04 | 0,390 | 0,131 |
| E01 | réalisée | 0,573 | 3,035e-04 | 0,392 | 1,484e-04 | 0,532 | 0,162 |
| E02 | réévaluée | 0,786 | 1,217e-04 | 0,799 | 6,417e-04 | 0,635 | 0,304 |
| E02 | réalisée | 0,879 | 1,034e-04 | 0,884 | 4,785e-04 | 0,737 | 0,237 |

Le seuil SR0 annualisé vaut 0,401 dans le calcul principal et 0,346 sur la série réalisée. Il monte à 0,796 avec V = 1/T pour T = 1673. Source, `brut/sensibilite_dsr.txt`.

Le DSR est à lire avec trois réserves. La première est que V[SR] transversale est faible car les variantes sont très corrélées entre elles, ce qui abaisse SR0. La deuxième est que les essais ne sont pas indépendants. La troisième tient à la série réalisée, dont le défaut vient du regroupement du P&L à la clôture. Elle compte 1526 jours sans clôture sur 1673 sur E00-ref, avec g3 = 10,7 et g4 = 157. En réévalué, g3 tombe à 0,03 et g4 à 12, et le DSR de E00-ref passe de 0,832 à 0,635. L'hypothèse normale seule donne 0,782.

La correction par g3 et g4 n'est pas en défaut partout. Sur E00-ref réalisé, le bootstrap iid et le bootstrap par blocs de 30 jours donnent une probabilité plus haute que la formule (0,845 et 0,882 contre 0,832). L'écart de la formule se voit sur E02, avec un écart-type du Sharpe de 0,0358 contre 0,0458 en iid et 0,0575 en blocs, ainsi que sur E03 et R01. La série réévaluée s'aligne sur la formule sur les essais testés, sauf E02 en blocs (0,0693). Source, `controles/sorties/verif2.txt`, section 4.

Le seuil conventionnel de 0,95 n'est atteint par aucune ligne en DSR réévalué. Sur la série réalisée, seuls E07 (0,987) et R01 (0,958) le dépassent, et E03 s'en approche (0,931). Un seul trade clos en un jour crée cet effet. Sur R01, le jour du 03/02/2025 (+25,14 %, trade XRP de +44,8 R) donne un dénominateur du PSR de 0,247 contre 0,656 pour E00-ref à Sharpe voisin. La formule est juste et c'est son entrée qui est un artefact. Ces variantes ne remplacent pas la base.

## 14. Comparaison indicative aux seuils

Comparaison factuelle à `validation-edge` § 5 sur développement + validation, à titre indicatif seulement. Le critère réglementaire porte sur le hors échantillon, qui n'est pas ouvert. Aucune conclusion de rentabilité n'en découle. La colonne « Position » décrit la seule valeur chiffrée et ne vaut pas validation.

| Critère | Seuil | Valeur dev+val | Position |
|---|---|---|---|
| Nombre de trades | ≥ 100 au total, dont ≥ 30 hors échantillon | E00-ref 178, hors échantillon non lancé | total au-dessus, partie hors échantillon non mesurée |
| Espérance nette | > 0,2 R | E00-ref +0,268, E01 +0,134, E02 +0,573. Hors force_exit +0,228, +0,124 et +0,431. Ordre de la whitelist en rejeu, E00-ref p5 +0,207 et p95 +0,463, E01 p5 +0,044 et p95 +0,389 | E00-ref et E02 au-dessus, E01 en dessous. La position de E00-ref et de E01 dépend en partie de l'ordre (§ 9) |
| Espérance avec coûts doublés | > 0 R | E09 +0,259 (rejeu réel), R03 à coûts x3 +0,250 | au-dessus. Le frais seul est stressé, sans modèle de glissement |
| Drawdown maximal | < 20 % | référence réévaluée 12,8 % sur E00-ref, 12,8 % sur E01, 8,3 % sur E02. Réalisé 10,9 % sur E00-ref. Pour lecture, DD95 par blocs 25,7 % sur E00-ref | en dessous en référence. La dispersion par blocs dépasse 20 % au 95e centile (§ 12) |
| Tests multiples | Sharpe au-dessus du repère du § 4.3 pour le nombre d'essais | repère refait pour N = 13 et 4,58 ans, 0,80 (0,88 pour N = 19). E00-ref 0,56 réévalué, 0,71 réalisé. DSR réévalué 0,635 | en dessous du repère |
| Compatibilité | `commun-trading` § 3 et § 8 | risque prévu 0,5 %, perte moyenne au stop 0,99 R, levier 1, 3 positions, mise maximale 13,8 %, exposition sous 42 % | dans les valeurs prudentes. Les valeurs propres à Jonathan sont encore entre crochets dans `commun-trading` |
| Critère de la fiche § 1 | borne basse de l'IC 90 % > 0 | par blocs E00-ref -0,035, E01 -0,132, E02 -0,167. En iid à 5000 tirages -0,003, -0,115 et -0,094. En iid à 50 000 tirages +0,002 sur E00-ref | en dessous de 0 sur les trois par blocs. Le -0,003 iid de E00-ref équivaut à une borne nulle aux erreurs de simulation près |

Le repère de 0,80 reprend la formule qui donne environ 3,0 pour 500 essais sur un an, valeur retrouvée ici (3,05). Il s'applique normalement au Sharpe hors échantillon.

La borne de l'IC sert de critère binaire dans la fiche, et sa méthode décide du signe près de zéro. Sur 40 graines de 5000 tirages, la borne iid de E00-ref a un écart-type de 0,0043 et 70 % des graines donnent une borne positive, contre 55 % sur E08 (`controles/sorties/verif3.txt`). À 50 000 tirages, la borne par blocs de E00-ref a un écart-type de 0,0016 sur 20 graines. La borne iid positive de E05 devient négative par blocs (-0,030). Le contradicteur obtenait pour E07 une borne proche de zéro avec des blocs mobiles sans repli (-0,010 rejoué). Avec des blocs circulaires, qui donnent le même poids aux premiers et aux derniers trades, elle vaut +0,070. Les sensibilités à la longueur des blocs sont dans `controles/sorties/ic_sensibilite.txt`.

| Essai | iid 50 000 tirages | Blocs 5 trades | Blocs 10 trades | Blocs 20 trades | Blocs mobiles 10 trades sans repli | Épisodes | Mois d'ouverture |
|---|---|---|---|---|---|---|---|
| E00-ref | +0,002 à +0,558 | -0,030 à +0,615 | -0,035 à +0,614 | -0,024 à +0,584 | -0,073 à +0,574 | -0,025 à +0,607 (22 grappes) | -0,026 à +0,617 (51 grappes) |
| E01 | -0,116 à +0,408 | -0,136 à +0,418 | -0,132 à +0,403 | -0,125 à +0,390 | -0,155 à +0,384 | -0,148 à +0,384 (18 grappes) | -0,145 à +0,456 (38 grappes) |
| E02 | -0,104 à +1,390 | -0,190 à +1,604 | -0,167 à +1,552 | -0,097 à +1,309 | -0,185 à +1,792 | -0,271 à +1,494 (6 grappes) | -0,184 à +1,641 (13 grappes) |
| E05 | +0,012 à +0,525 | -0,024 à +0,569 | -0,030 à +0,573 | -0,026 à +0,556 | -0,067 à +0,537 | -0,042 à +0,578 (30 grappes) | -0,031 à +0,593 (51 grappes) |
| E07 | +0,198 à +1,154 | +0,127 à +1,267 | +0,070 à +1,353 | +0,041 à +1,372 | -0,010 à +1,114 | +0,044 à +1,417 (22 grappes) | +0,170 à +1,212 (52 grappes) |
| E08 | -0,000 à +0,503 | -0,028 à +0,549 | -0,023 à +0,540 | -0,006 à +0,505 | -0,056 à +0,513 | -0,031 à +0,546 (22 grappes) | -0,022 à +0,552 (51 grappes) |
| E09 | -0,007 à +0,549 | -0,039 à +0,606 | -0,044 à +0,605 | -0,033 à +0,575 | -0,082 à +0,565 | -0,033 à +0,598 (22 grappes) | -0,035 à +0,608 (51 grappes) |

## 15. Anomalies

| N° | Anomalie | Effet | Traitement |
|---:|---|---|---|
| 1 | Dépassement de `download-data` au-delà de `--timerange` (§ 3). | Des données hors échantillon sont restées 3 min 12 s sur le disque, sans être affichées ni utilisées. | Troncature à 22:33:27Z avant tout backtest. Relancer `download-data` dans ce `user_data` les ramènerait, il faudra tronquer de nouveau tant que E10 n'est pas ouvert. |
| 2 | Si `git add .` est lancé, `user_data/data/` sera inclus. Le motif `user_data/data/` du `.gitignore` racine est ancré à la racine du dépôt et ne couvre pas ce dossier. | 22 Mo de données de marché et les fichiers de `user_data` entreraient dans le dépôt. | Non corrigé ici, hors périmètre. Décision à prendre avant le commit. |
| 3 | `--export-filename` de la procédure est déprécié. | Aucun effet avec freqtrade 2026.10. | `--backtest-directory` avec un dossier créé d'avance par essai. |
| 4 | `recursive-analysis` refuse `--fee`. | Premier lancement rejeté, conservé dans `brut/E01_recursive-analysis_essai1_refus_option_fee.txt`. Il affiche `exit=0` malgré le refus, donc ce code de sortie n'est pas une preuve de succès. | Option retirée, sans effet sur les indicateurs testés. |
| 5 | `lookahead-analysis` vise 20 signaux par défaut. | Couverture faible des 135 trades de E01. | Second lancement à 271 signaux. Il remplace aussi certains réglages (mise 10000, positions illimitées, stop hors plateforme), ce qui est le fonctionnement normal de l'outil. |
| 6 | Le filet de -30 % ne borne pas le stop. Après remplissage, `custom_stoploss` peut élargir le stop. | Sur E00-ref, trois shorts du 22/06/2021 (XRP, LTC, BCH) ont un stop à 33 % à 37 %. Aucun n'a touché le stop et la taille reste calculée sur cette distance. | Consigné, stratégie non modifiée. |
| 7 | Les fins de trade sont datées à l'ouverture de la bougie 1d. | Le financement est compté bornes incluses jusqu'à cette date. Une sortie en cours de journée peut donc omettre des paiements et une entrée à 00:00 en compte un. | Chiffré le 01/11/2026 (`t7_glissement_financement_mark1h.txt`). Financement compté à l'instant d'entrée, -8,33 USDT sur E01, -0,90 sur E02 et -9,38 sur E00-ref pour -768,38 au total. Financement omis avant franchissement du stop, -2,17 sur E01 et -2,16 sur E00-ref [heure estimée sur le mark 1h]. L'écart est négligeable et le sens net légèrement défavorable au backtest. |
| 8 | Aucun glissement n'est modélisé et le stop se remplit au prix exact sur bougies 1d. | E09 et R03 stressent le seul paramètre `--fee`. La demande « slippage x2 et x3 » est donc traduite par des frais x2 et x3. | Consigné. |
| 9 | Les exports ne contiennent pas la version de freqtrade. | Le champ reste vide dans les métriques. | Version de l'environnement notée, 2026.10. |
| 10 | Biais de sélection de l'univers, au-delà du seul biais du survivant (fiche § 2). La fiche dit que les 10 actifs étaient [déjà parmi les plus liquides début 2021, affirmation contredite pour DOGE et TRX]. | Les paires délistées sont absentes. Sur le volume des perpétuels Binance de décembre 2020, DOGE est 42e et TRX 19e parmi 70 paires [rangs minimaux, exécution du contradicteur du 2026-11-01T00:03:04Z, `controles/t11_rangs_volume_dec2020.py`, non rejouée car cette reprise interdit tout téléchargement]. Les volumes locaux confirment que ces deux paires sont les plus faibles des 10 (DOGE 0,43 G$, TRX 1,32 G$, BTC 224,92 G$, `t8_gaps_verrou_qualite.txt`). En rejeu simulé, E02 passe de +0,579 R à +0,307 R sans DOGE puis +0,184 R sans DOGE ni TRX. E00-ref passe de +0,272 à +0,218 puis +0,181 R. | Univers figé inchangé. À porter à l'avocat du diable. Un univers défini par le volume à date serait une nouvelle stratégie et un nouvel essai. |
| 11 | Intervalle à 90 % calculé sur des trades traités comme indépendants. | Les actifs sont corrélés et 99 % à 100 % des trades en chevauchent un autre. La corrélation de rang entre trades chevauchants reste faible (0,003 sur E00-ref), donc l'élargissement est modéré mais il décide du signe près de zéro. | IC par blocs ajouté (§ 2 et § 14), iid conservé pour comparaison. Méthode à fixer avant E10 dans l'avenant. |
| 12 | Ordre de la whitelist, sixième paramètre libre non déclaré. Freqtrade sert les paires dans l'ordre du dictionnaire quand les signaux dépassent les places. | Sur 200 ordres en rejeu, l'espérance de E01 va de +0,011 à +0,468 R et 53,5 % des ordres sont à 0,2 R ou moins. Celle de E00-ref va de +0,175 à +0,528 R (§ 9). Bloquant pour E10 seulement, car ce run unique ne donnerait qu'un chemin. | Porté dans l'avenant, statut proposé. Ordre actuel figé sans chercher le meilleur, aucun ordre retenu pour sa performance. À porter à l'avocat du diable. |
| 13 | Attribution des places dans freqtrade. Les paires déjà en position passent d'abord dans la bougie et un stop du jour libère une place à l'ouverture de ce même jour. | 6 entrées sur E01, 1 sur E02 et 6 sur E00-ref. La règle stricte simulée donne +0,333 R contre +0,137 R sur E01 (§ 4). `lookahead-analysis` ne teste pas ce cas. | Sensibilité seulement, jamais un remplacement de la base. Le traitement des entrées en cours de bougie est à décider avant le papier, et toute modification sera un nouvel essai. |
| 14 | Stop divergent entre backtest et papier. Dans `_atr_at_entry`, `date < open_date` exclut la bougie d'entrée en backtest (00:00:00). En papier, open_date vaut quelques secondes après minuit et la bougie d'entrée passe le filtre dès le lendemain. | Le stop peut alors se resserrer, jamais s'élargir. Estimation par rejeu, 53 trades sur 135 sur E01 et 70 sur 178 sur E00-ref, médiane 1,5 % de la distance et maximum 4,9 %, avec 6 et 7 sorties modifiées (`t9`, `t10`) [mode papier non exécuté]. La comparaison papier contre backtest serait faussée. | Stratégie non modifiée. Correctif à enregistrer comme nouvel essai avant le papier, sans changer les paramètres (avenant). |
| 15 | Régime connu des auteurs. La fiche écrite avant test cite un mouvement de mi-2026, en plein hors échantillon (fiche § 4 point 2). | Le hors échantillon n'a pas été lu dans les données de backtest, mais les auteurs connaissaient qualitativement le régime. Les paramètres étant classiques et figés, l'effet paraît limité sans pouvoir être exclu. | À signaler dans le verdict. E10 ne sera pas présenté comme totalement aveugle. |
| 16 | Six contrôles de format antérieurs, absents du registre et de la version précédente de ce rapport. Sept backtests du contradicteur et 600 rejeux simulés s'y ajoutent. | Mêmes règles de base, aucun accès au hors échantillon et aucun paramètre changé. Effet limité sur le DSR, E00-ref passe de 0,635 à 0,602 avec N = 19 (réévalué). | Métadonnées dans `brut/format_check/` et scripts dans `controles/`. Deux lignes de synthèse au registre, marquées hors N. |
| 17 | Commentaires de E10 et E11 réécrits après coup dans le registre (mention verrouillé ajoutée dans la colonne commentaire). | Aucun effet sur variante, période ni frais, mais le registre préenregistré avait changé sans trace. | Texte d'origine restauré (`git show HEAD:`). Le verrouillage passe dans la colonne statut. |
| 18 | Les champs `initial_stop_loss_abs` et `initial_stop_loss_ratio` des exports ne donnent pas le stop initial réel. | Ils valent le filet de -30 % sur tous les trades de E01, avec un écart jusqu'à 27 % au stop réel. Aucun chiffre publié n'est touché, car `analyse_strat.py` et `controles.py` ne les lisent pas. | Le champ à lire est `stop_loss_abs`. Toute analyse future devra s'y tenir. |

## 16. Sorties brutes et traçabilité

Les fichiers .zip sont exclus de git. Le dossier `resultats/brut/` conserve donc le texte. Il contient pour chaque essai `<id>_backtesting.txt` (tableaux freqtrade complets), `<id>_analyse.txt` et `<id>_analyse_dsr.txt`, ainsi que `run_essais.sh`, `registre_dsr.py`, `controles.py` et `sensibilite_dsr.py`. La reprise du 01/11/2026 ajoute `<id>_analyse_reevalue.txt`, `rejeu_analyse.sh` et `remplit_registre.py`, avec les tests dans `tests_analyse_strat.txt`. La version précédente de la sensibilité reste dans `sensibilite_dsr_20261031.py` et `.txt`. Les métriques sont dans `resultats/<id>_metriques.json` et `.md`.

Le dossier `brut/format_check/` garde les métadonnées et une synthèse des 6 contrôles de format, lancés avant ce `user_data`. Le dossier `controles/` garde les scripts des contradicteurs, leurs sorties et un index (`controles/LISEZMOI.md`). Les 6 contrôles de format et les 7 backtests du contradicteur ne sont pas des candidats et n'ont pas été relancés.

| Essai | Backtest exécuté (UTC) | sha256 de l'export (16 premiers caractères) |
|---|---|---|
| E01 | 2026-10-31T22:33:52Z | `024811d1a688a82e` |
| E02 | 2026-10-31T22:41:48Z | `0bd9f1a786b8924f` |
| E03 | 2026-10-31T22:42:04Z | `2711cb18e1c245ac` |
| E04 | 2026-10-31T22:42:17Z | `1f94800394e89cef` |
| E05 | 2026-10-31T22:42:28Z | `8dbf5c78f1dba86f` |
| E06 | 2026-10-31T22:42:39Z | `20cd993d1cce6961` |
| E07 | 2026-10-31T22:42:48Z | `5879cd5c1b66b1db` |
| E08 | 2026-10-31T22:43:04Z | `ff2140f9b21302dc` |
| E09 | 2026-10-31T22:43:18Z | `512e8df35df155d7` |
| R01 | 2026-10-31T22:43:30Z | `8620cfc2ec2411c4` |
| R02 | 2026-10-31T22:43:42Z | `33d65eb42ccf8ae8` |
| R03 | 2026-10-31T22:44:06Z | `f2e491dadbdc2fbf` |
| E00-ref | 2026-10-31T22:44:55Z | `bae5c5708265ab4f` |

| Fichier resté intact | sha256 avant (22:29:58Z) | sha256 après |
|---|---|---|
| FICHE_STRAT-20261031-01.md | `2ac936ba1638e3955a0d94df99e1a7945345741fb2a0844c12351fff31a5e180` | `2ac936ba1638e3955a0d94df99e1a7945345741fb2a0844c12351fff31a5e180` |
| TrendDonchianV1.py | `072c0e3b4d6f2df9ae3fb83373aa30a7902c499ca150e003d3a457c4da2a6cee` | `072c0e3b4d6f2df9ae3fb83373aa30a7902c499ca150e003d3a457c4da2a6cee` |
| config_strat01.json | `a473eaad2bcf27c3665542c2ce0858b6409c7890f30485eb768b4e8f96dda08d` | `a473eaad2bcf27c3665542c2ce0858b6409c7890f30485eb768b4e8f96dda08d` |

## 17. Non vérifié

Le moment exact de remplissage d'un stop dans la journée n'est pas connu sur des bougies 1d. L'instant d'éligibilité de DOGE est déduit du code [non observé]. Les performances n'ont pas été comparées à une exécution réelle ou papier. L'avocat du diable après résultats n'a pas été joué ici, car il revient à l'étape de verdict. Les rangs de volume de DOGE et TRX n'ont pas été rejoués dans cette reprise, car elle interdit tout téléchargement. L'effet réel d'une entrée en cours de bougie et le stop en mode papier sont déduits du code et d'un rejeu [non observés en papier]. Le cas restant du décompte de `lookahead-analysis` est [non élucidé]. La référence du papier de Bailey et López de Prado reste citée de mémoire [papier non rouvert].

Sources : exports freqtrade 2026.10 du 31/10/2026, rejeux du 01/11/2026 sur ces exports, données publiques des perpétuels USDT de Binance (1d, mark 1h, financement) coupées au 31/07/2025.
