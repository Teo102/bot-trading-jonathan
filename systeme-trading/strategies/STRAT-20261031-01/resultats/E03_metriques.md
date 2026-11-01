# Métriques de l'essai E03 (TrendDonchianV1_E03)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E03/backtest-result-2026-10-31_22-42-10.zip --essai E03 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:28:59+00:00 |
| Export analysé | `user_data/backtest_results/E03/backtest-result-2026-10-31_22-42-10.zip` |
| Membre lu | `backtest-result-2026-10-31_22-42-10.json` |
| sha256 de l'export | `2711cb18e1c245acc37133c5c83813fa521816565b8100e68936089f2addd741` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:42:04+00:00 |
| Plage analysée | 2021-01-01 à 2025-07-31 |
| Timerange de l'export | 20210101-20250731 |
| Backtest réel | 2021-01-01 00:00:00 à 2025-07-31 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,0005 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 178 (96, 82) |
| Sorties force_exit | 3 |
| Taux de réussite | 37,6 % |
| Gain moyen, perte moyenne | 2,55 R, -0,76 R |
| Espérance | +0,485 R |
| Espérance hors force_exit | +0,452 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | +0,074 à +1,002 R |
| Intervalle à 90 % iid (50000 tirages) | +0,082 à +1,007 R |
| Intervalle à 90 % par blocs de 10 trades | +0,071 à +1,008 R |
| Intervalle à 90 % par épisodes (20) | +0,055 à +1,044 R |
| Intervalle à 90 % par mois d'ouverture (53) | +0,052 à +1,060 R |
| Espérance, frais doublés (approximation) | +0,475 R |
| Espérance, frais et financement payé doublés (approximation) | +0,371 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 9,5 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 22,2 % |
| Part du gain du meilleur trade (en R) | 52 % |
| Part du gain du meilleur trade (en P&L) | 54 % |
| Capital final | 14 780,79 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 8,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,874 |
| Sharpe quotidien non annualisé | 0,04574 |
| Sortino annualisé | 1,320 |
| Calmar | 0,899 |
| Drawdown maximal | 9,9 % |
| Creux du drawdown | 2024-11-05 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1528 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 47,8 % |
| Rendement annualisé | 8,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,708 |
| Sharpe quotidien non annualisé | 0,03705 |
| Sortino annualisé | 4,150 |
| Calmar | 1,016 |
| Drawdown maximal | 8,8 % |
| Taux de réussite | 37,6 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +1,608 | 2,01 | 1,5 % | +876,45 | +802,16 |
| 2021-S2 | 184 | 22 | +0,194 | 0,67 | 2,3 % | +220,99 | +355,65 |
| 2022-S1 | 181 | 12 | +0,511 | 1,74 | 0,9 % | +341,42 | +690,76 |
| 2022-S2 | 184 | 19 | -0,116 | -0,57 | 3,9 % | -138,26 | -479,65 |
| 2023-S1 | 181 | 26 | -0,276 | -2,22 | 5,0 % | -398,30 | +229,03 |
| 2023-S2 | 184 | 16 | +0,375 | 0,89 | 1,3 % | +324,16 | +560,76 |
| 2024-S1 | 182 | 22 | +0,618 | 1,47 | 1,7 % | +760,68 | -210,27 |
| 2024-S2 | 184 | 24 | -0,099 | -0,49 | 3,6 % | -148,25 | +2 225,67 |
| 2025-S1 | 181 | 22 | +1,966 | 1,21 | 2,5 % | +2 430,15 | +240,29 |
| 2025-S2 (partiel) | 31 | 4 | +1,789 | non significatif | 0,1 % | +511,76 | +366,38 |

Semestres positifs 7 sur 10 (70 %). Hors semestre partiel 6 sur 9. Réévalué 8 sur 10, hors semestre partiel 7 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 96 | 36,5 % | +0,950 | +5 119,77 | 63,10 | 966,22 | 101,58 | 864,64 |
| shorts | 82 | 39,0 % | -0,059 | -338,98 | 39,49 | 39,05 | 70,13 | -31,08 |
| total | 178 | 37,6 % | +0,485 | +4 780,79 | 102,59 | 1 005,27 | 171,71 | 833,56 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,310, 14,948 |
| PSR(0) | 0,970 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,845 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 29,198, 1028,520 |
| PSR(0) | 0,998 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,931 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,248 |
| Sharpe (solde quotidien) | 0,653 |
| Sortino (trades) | 2,754 |
| Sortino (solde quotidien) | 1,864 |
| Calmar (trades) | 6,240 |
| Calmar (solde quotidien) | 5,561 |
| Drawdown du compte | 8,8 % |
| Capital final | 14 780,79 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-42-10.zip`, analyse du 2026-11-01T00:28:59+00:00.
