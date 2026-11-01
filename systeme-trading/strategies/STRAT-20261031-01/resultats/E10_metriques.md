# Métriques de l'essai E10 (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E10/backtest-result-2026-11-01_08-50-27.zip --essai E10 --start 2025-08-01 --end 2026-10-31 --n-trials 15 --sr-var 0.0004147722100656455 --sr-var-reevalue 0.0005560603764310167` |
| Horodatage de l'analyse (UTC) | 2026-11-01T08:50:29+00:00 |
| Export analysé | `user_data/backtest_results/E10/backtest-result-2026-11-01_08-50-27.zip` |
| Membre lu | `backtest-result-2026-11-01_08-50-27.json` |
| sha256 de l'export | `d214eebb4d2c3448872ee0ec7a6085ec40debb41515cf0e83f99527bb8ca2912` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-11-01T08:50:26+00:00 |
| Plage analysée | 2025-08-01 à 2026-10-31 |
| Timerange de l'export | 20250801-20261031 |
| Backtest réel | 2025-08-01 00:00:00 à 2026-10-31 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,0005 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 46 (21, 25) |
| Sorties force_exit | 2 |
| Taux de réussite | 32,6 % |
| Gain moyen, perte moyenne | 2,00 R, -0,75 R |
| Espérance | +0,147 R |
| Espérance hors force_exit | +0,161 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,232 à +0,576 R |
| Intervalle à 90 % iid (50000 tirages) | -0,228 à +0,571 R |
| Intervalle à 90 % par blocs de 10 trades | -0,376 à +0,744 R |
| Intervalle à 90 % par épisodes (10) | -0,518 à +0,615 R |
| Intervalle à 90 % par mois d'ouverture (14) | -0,313 à +0,703 R |
| Espérance, frais doublés (approximation) | +0,135 R |
| Espérance, frais et financement payé doublés (approximation) | +0,112 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 5,8 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 14,8 % |
| Part du gain du meilleur trade (en R) | 109 % |
| Part du gain du meilleur trade (en P&L) | 117 % |
| Capital final | 10 309,30 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 457 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 2,5 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,354 |
| Sharpe quotidien non annualisé | 0,01850 |
| Sortino annualisé | 0,473 |
| Calmar | 0,399 |
| Drawdown maximal | 6,2 % |
| Creux du drawdown | 2026-10-31 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 457 jours civils, dont 422 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 3,1 % |
| Rendement annualisé | 2,5 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,485 |
| Sharpe quotidien non annualisé | 0,02539 |
| Sortino annualisé | 1,119 |
| Calmar | 0,670 |
| Drawdown maximal | 3,7 % |
| Taux de réussite | 32,6 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025-S2 (partiel) | 153 | 13 | -0,388 | -1,98 | 3,0 % | -250,50 | -132,11 |
| 2026-S1 | 181 | 16 | +0,611 | 1,97 | 1,2 % | +477,98 | +780,59 |
| 2026-S2 (partiel) | 123 | 17 | +0,119 | 0,35 | 3,4 % | +81,81 | -339,18 |

Semestres positifs 2 sur 3 (67 %). Hors semestre partiel 1 sur 1. Réévalué 1 sur 3, hors semestre partiel 1 sur 1. Semestres avec au moins un trade 3.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 21 | 23,8 % | -0,239 | -248,30 | 16,63 | 33,65 | 6,75 | 26,90 |
| shorts | 25 | 40,0 % | +0,471 | +557,59 | 12,05 | 18,64 | 12,67 | 5,97 |
| total | 46 | 32,6 % | +0,147 | +309,30 | 28,68 | 52,29 | 19,41 | 32,87 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | options --n-trials et --sr-var, V de la série réévaluée |
| N | 15 |
| V[SR] quotidien | 0,000556 |
| Asymétrie g3, kurtosis g4 | -1,732, 27,016 |
| PSR(0) | 0,651 |
| SR0 quotidien, annualisé | 0,0418, 0,798 |
| DSR | 0,313 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | options --n-trials et --sr-var |
| N | 15 |
| V[SR] quotidien | 0,000415 |
| Asymétrie g3, kurtosis g4 | 6,810, 79,563 |
| PSR(0) | 0,723 |
| SR0 quotidien, annualisé | 0,0361, 0,689 |
| DSR | 0,402 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,158 |
| Sharpe (solde quotidien) | 0,513 |
| Sortino (trades) | 0,844 |
| Sortino (solde quotidien) | 0,517 |
| Calmar (trades) | 3,527 |
| Calmar (solde quotidien) | 3,738 |
| Drawdown du compte | 3,7 % |
| Capital final | 10 309,30 |

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-11-01_08-50-27.zip`, analyse du 2026-11-01T08:50:29+00:00.
