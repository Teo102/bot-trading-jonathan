# Métriques de l'essai E02 (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E02/backtest-result-2026-10-31_22-41-51.zip --essai E02 --start 2024-07-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:28:57+00:00 |
| Export analysé | `user_data/backtest_results/E02/backtest-result-2026-10-31_22-41-51.zip` |
| Membre lu | `backtest-result-2026-10-31_22-41-51.json` |
| sha256 de l'export | `0bd9f1a786b8924f44d3e5c8797ac0ac8e122dbc6d323be3e00781d793c50e39` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:41:48+00:00 |
| Plage analysée | 2024-07-01 à 2025-07-31 |
| Timerange de l'export | 20240701-20250731 |
| Backtest réel | 2024-07-01 00:00:00 à 2025-07-31 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,0005 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 46 (26, 20) |
| Sorties force_exit | 3 |
| Taux de réussite | 30,4 % |
| Gain moyen, perte moyenne | 3,44 R, -0,68 R |
| Espérance | +0,573 R |
| Espérance hors force_exit | +0,431 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,094 à +1,400 R |
| Intervalle à 90 % iid (50000 tirages) | -0,104 à +1,390 R |
| Intervalle à 90 % par blocs de 10 trades | -0,167 à +1,552 R |
| Intervalle à 90 % par épisodes (6) | -0,271 à +1,494 R |
| Intervalle à 90 % par mois d'ouverture (13) | -0,184 à +1,641 R |
| Espérance, frais doublés (approximation) | +0,562 R |
| Espérance, frais et financement payé doublés (approximation) | +0,509 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 5,5 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 13,9 % |
| Part du gain du meilleur trade (en R) | 51 % |
| Part du gain du meilleur trade (en P&L) | 51 % |
| Capital final | 11 269,70 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 396 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 11,6 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 1,151 |
| Sharpe quotidien non annualisé | 0,06027 |
| Sortino annualisé | 1,863 |
| Calmar | 1,397 |
| Drawdown maximal | 8,3 % |
| Creux du drawdown | 2025-06-24 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 396 jours civils, dont 361 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 12,7 % |
| Rendement annualisé | 11,6 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 1,146 |
| Sharpe quotidien non annualisé | 0,05998 |
| Sortino annualisé | 4,897 |
| Calmar | 3,100 |
| Drawdown maximal | 3,8 % |
| Taux de réussite | 30,4 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-S2 | 184 | 23 | +0,800 | 1,35 | 3,8 % | +875,10 | +1 140,15 |
| 2025-S1 | 181 | 19 | +0,015 | -0,07 | 2,1 % | -21,93 | -198,60 |
| 2025-S2 (partiel) | 31 | 4 | +1,920 | non significatif | 0,1 % | +416,53 | +328,15 |

Semestres positifs 2 sur 3 (67 %). Hors semestre partiel 1 sur 2. Réévalué 2 sur 3, hors semestre partiel 1 sur 2. Semestres avec au moins un trade 3.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 26 | 38,5 % | +1,226 | +1 558,17 | 17,45 | 117,12 | 13,80 | 103,32 |
| shorts | 20 | 20,0 % | -0,274 | -288,47 | 8,84 | 3,70 | 11,76 | -8,06 |
| total | 46 | 30,4 % | +0,573 | +1 269,70 | 26,29 | 120,82 | 25,56 | 95,26 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,809, 17,863 |
| PSR(0) | 0,888 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,786 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 9,959, 114,854 |
| PSR(0) | 0,953 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,879 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,409 |
| Sharpe (solde quotidien) | 0,850 |
| Sortino (trades) | 3,296 |
| Sortino (solde quotidien) | 1,510 |
| Calmar (trades) | 16,346 |
| Calmar (solde quotidien) | 10,902 |
| Drawdown du compte | 3,8 % |
| Capital final | 11 269,70 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-41-51.zip`, analyse du 2026-11-01T00:28:57+00:00.
