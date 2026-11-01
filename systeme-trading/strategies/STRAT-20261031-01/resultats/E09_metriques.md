# Métriques de l'essai E09 (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E09/backtest-result-2026-10-31_22-43-22.zip --essai E09 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:14+00:00 |
| Export analysé | `user_data/backtest_results/E09/backtest-result-2026-10-31_22-43-22.zip` |
| Membre lu | `backtest-result-2026-10-31_22-43-22.json` |
| sha256 de l'export | `512e8df35df155d779bb38c50881eb3771d9c3a43df9d5518588cf7507bb54fc` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:43:18+00:00 |
| Plage analysée | 2021-01-01 à 2025-07-31 |
| Timerange de l'export | 20210101-20250731 |
| Backtest réel | 2021-01-01 00:00:00 à 2025-07-31 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,001 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 178 (95, 83) |
| Sorties force_exit | 3 |
| Taux de réussite | 33,7 % |
| Gain moyen, perte moyenne | 2,25 R, -0,75 R |
| Espérance | +0,259 R |
| Espérance hors force_exit | +0,219 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,012 à +0,553 R |
| Intervalle à 90 % iid (50000 tirages) | -0,007 à +0,549 R |
| Intervalle à 90 % par blocs de 10 trades | -0,044 à +0,605 R |
| Intervalle à 90 % par épisodes (22) | -0,033 à +0,598 R |
| Intervalle à 90 % par mois d'ouverture (51) | -0,035 à +0,608 R |
| Espérance, frais doublés (approximation) | +0,240 R |
| Espérance, frais et financement payé doublés (approximation) | +0,139 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 11,1 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 26,1 % |
| Part du gain du meilleur trade (en R) | 29 % |
| Part du gain du meilleur trade (en P&L) | 30 % |
| Capital final | 12 364,41 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 4,7 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,544 |
| Sharpe quotidien non annualisé | 0,02848 |
| Sortino annualisé | 0,795 |
| Calmar | 0,365 |
| Drawdown maximal | 13,0 % |
| Creux du drawdown | 2023-06-09 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1526 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 23,6 % |
| Rendement annualisé | 4,7 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,687 |
| Sharpe quotidien non annualisé | 0,03597 |
| Sortino annualisé | 2,074 |
| Calmar | 0,427 |
| Drawdown maximal | 11,1 % |
| Taux de réussite | 33,7 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,781 | 1,42 | 1,5 % | +429,14 | +357,88 |
| 2021-S2 | 184 | 24 | -0,083 | -0,37 | 4,4 % | -113,89 | +13,45 |
| 2022-S1 | 181 | 9 | +0,849 | 2,13 | 0,5 % | +395,88 | +737,20 |
| 2022-S2 | 184 | 23 | -0,309 | -1,57 | 5,9 % | -389,52 | -740,26 |
| 2023-S1 | 181 | 26 | -0,321 | -2,70 | 5,6 % | -421,87 | +160,66 |
| 2023-S2 | 184 | 18 | +0,178 | 0,47 | 2,5 % | +151,01 | +367,05 |
| 2024-S1 | 182 | 22 | +0,607 | 1,46 | 1,7 % | +677,58 | -120,90 |
| 2024-S2 | 184 | 22 | +1,047 | 1,72 | 1,9 % | +1 214,00 | +1 458,78 |
| 2025-S1 | 181 | 19 | +0,008 | -0,09 | 2,2 % | -32,17 | -226,74 |
| 2025-S2 (partiel) | 31 | 4 | +1,908 | non significatif | 0,1 % | +454,28 | +357,29 |

Semestres positifs 6 sur 10 (60 %). Hors semestre partiel 5 sur 9. Réévalué 7 sur 10, hors semestre partiel 6 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 95 | 36,8 % | +0,596 | +2 951,38 | 110,70 | 893,39 | 93,29 | 800,11 |
| shorts | 83 | 30,1 % | -0,126 | -586,97 | 71,84 | 30,63 | 62,98 | -32,35 |
| total | 178 | 33,7 % | +0,259 | +2 364,41 | 182,54 | 924,02 | 156,26 | 767,76 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,025, 11,972 |
| PSR(0) | 0,878 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,620 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 10,652, 156,149 |
| PSR(0) | 0,964 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,814 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,229 |
| Sharpe (solde quotidien) | 0,587 |
| Sortino (trades) | 1,477 |
| Sortino (solde quotidien) | 0,815 |
| Calmar (trades) | 2,433 |
| Calmar (solde quotidien) | 1,956 |
| Drawdown du compte | 11,1 % |
| Capital final | 12 364,41 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-43-22.zip`, analyse du 2026-11-01T00:29:14+00:00.
