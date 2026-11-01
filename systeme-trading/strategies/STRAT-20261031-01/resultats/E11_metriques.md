# Métriques de l'essai E11 (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E11/backtest-result-2026-11-01_08-50-33.zip --essai E11 --start 2025-08-01 --end 2026-10-31 --n-trials 15 --sr-var 0.0004147722100656455 --sr-var-reevalue 0.0005560603764310167` |
| Horodatage de l'analyse (UTC) | 2026-11-01T08:50:35+00:00 |
| Export analysé | `user_data/backtest_results/E11/backtest-result-2026-11-01_08-50-33.zip` |
| Membre lu | `backtest-result-2026-11-01_08-50-33.json` |
| sha256 de l'export | `741e52f07a44510e918a0bdda078cc1dba34ce087462a3400748b2e4a669dd65` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-11-01T08:50:32+00:00 |
| Plage analysée | 2025-08-01 à 2026-10-31 |
| Timerange de l'export | 20250801-20261031 |
| Backtest réel | 2025-08-01 00:00:00 à 2026-10-31 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,001 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 46 (21, 25) |
| Sorties force_exit | 2 |
| Taux de réussite | 32,6 % |
| Gain moyen, perte moyenne | 1,99 R, -0,76 R |
| Espérance | +0,135 R |
| Espérance hors force_exit | +0,149 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,244 à +0,564 R |
| Intervalle à 90 % iid (50000 tirages) | -0,240 à +0,559 R |
| Intervalle à 90 % par blocs de 10 trades | -0,388 à +0,732 R |
| Intervalle à 90 % par épisodes (10) | -0,530 à +0,602 R |
| Intervalle à 90 % par mois d'ouverture (14) | -0,324 à +0,692 R |
| Espérance, frais doublés (approximation) | +0,110 R |
| Espérance, frais et financement payé doublés (approximation) | +0,088 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 5,9 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 15,0 % |
| Part du gain du meilleur trade (en R) | 118 % |
| Part du gain du meilleur trade (en P&L) | 128 % |
| Capital final | 10 281,06 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 457 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 2,2 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,325 |
| Sharpe quotidien non annualisé | 0,01699 |
| Sortino annualisé | 0,433 |
| Calmar | 0,358 |
| Drawdown maximal | 6,3 % |
| Creux du drawdown | 2026-10-31 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 457 jours civils, dont 422 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 2,8 % |
| Rendement annualisé | 2,2 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,444 |
| Sharpe quotidien non annualisé | 0,02324 |
| Sortino annualisé | 1,008 |
| Calmar | 0,595 |
| Drawdown maximal | 3,8 % |
| Taux de réussite | 32,6 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025-S2 (partiel) | 153 | 13 | -0,396 | -2,01 | 3,0 % | -256,12 | -137,79 |
| 2026-S1 | 181 | 16 | +0,599 | 1,94 | 1,2 % | +468,72 | +770,87 |
| 2026-S2 (partiel) | 123 | 17 | +0,104 | 0,30 | 3,4 % | +68,46 | -352,02 |

Semestres positifs 2 sur 3 (67 %). Hors semestre partiel 1 sur 1. Réévalué 1 sur 3, hors semestre partiel 1 sur 1. Semestres avec au moins un trade 3.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 21 | 23,8 % | -0,255 | -264,53 | 33,22 | 33,62 | 6,73 | 26,89 |
| shorts | 25 | 40,0 % | +0,462 | +545,60 | 24,06 | 18,61 | 12,66 | 5,95 |
| total | 46 | 32,6 % | +0,135 | +281,06 | 57,29 | 52,23 | 19,39 | 32,84 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | options --n-trials et --sr-var, V de la série réévaluée |
| N | 15 |
| V[SR] quotidien | 0,000556 |
| Asymétrie g3, kurtosis g4 | -1,756, 27,222 |
| PSR(0) | 0,639 |
| SR0 quotidien, annualisé | 0,0418, 0,798 |
| DSR | 0,301 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | options --n-trials et --sr-var |
| N | 15 |
| V[SR] quotidien | 0,000415 |
| Asymétrie g3, kurtosis g4 | 6,724, 79,107 |
| PSR(0) | 0,704 |
| SR0 quotidien, annualisé | 0,0361, 0,689 |
| DSR | 0,384 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,144 |
| Sharpe (solde quotidien) | 0,473 |
| Sortino (trades) | 0,758 |
| Sortino (solde quotidien) | 0,455 |
| Calmar (trades) | 3,129 |
| Calmar (solde quotidien) | 3,343 |
| Drawdown du compte | 3,8 % |
| Capital final | 10 281,06 |

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-11-01_08-50-33.zip`, analyse du 2026-11-01T08:50:35+00:00.
