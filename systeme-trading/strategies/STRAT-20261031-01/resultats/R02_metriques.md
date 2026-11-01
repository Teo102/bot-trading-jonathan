# Métriques de l'essai R02 (TrendDonchianV1_R02)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/R02/backtest-result-2026-10-31_22-43-49.zip --essai R02 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:18+00:00 |
| Export analysé | `user_data/backtest_results/R02/backtest-result-2026-10-31_22-43-49.zip` |
| Membre lu | `backtest-result-2026-10-31_22-43-49.json` |
| sha256 de l'export | `33d65eb42ccf8ae85972bfaae9d0acfc659030e5f713c523715ab5640967c7e1` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:43:42+00:00 |
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
| Trades (longs, shorts) | 171 (91, 80) |
| Sorties force_exit | 3 |
| Taux de réussite | 28,7 % |
| Gain moyen, perte moyenne | 2,56 R, -0,74 R |
| Espérance | +0,207 R |
| Espérance hors force_exit | +0,167 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,086 à +0,514 R |
| Intervalle à 90 % iid (50000 tirages) | -0,082 à +0,522 R |
| Intervalle à 90 % par blocs de 10 trades | -0,119 à +0,573 R |
| Intervalle à 90 % par épisodes (23) | -0,138 à +0,633 R |
| Intervalle à 90 % par mois d'ouverture (49) | -0,131 à +0,606 R |
| Espérance, frais doublés (approximation) | +0,197 R |
| Espérance, frais et financement payé doublés (approximation) | +0,092 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 13,1 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 29,0 % |
| Part du gain du meilleur trade (en R) | 38 % |
| Part du gain du meilleur trade (en P&L) | 40 % |
| Capital final | 11 703,31 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 3,5 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,412 |
| Sharpe quotidien non annualisé | 0,02158 |
| Sortino annualisé | 0,599 |
| Calmar | 0,207 |
| Drawdown maximal | 16,9 % |
| Creux du drawdown | 2023-05-15 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1526 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 17,0 % |
| Rendement annualisé | 3,5 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,498 |
| Sharpe quotidien non annualisé | 0,02607 |
| Sortino annualisé | 1,522 |
| Calmar | 0,260 |
| Drawdown maximal | 13,4 % |
| Taux de réussite | 28,7 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 12 | +0,640 | 1,26 | 1,5 % | +381,23 | +334,47 |
| 2021-S2 | 184 | 19 | +0,132 | 0,52 | 2,4 % | +123,24 | +207,48 |
| 2022-S1 | 181 | 12 | +0,316 | 1,12 | 1,7 % | +193,92 | +276,30 |
| 2022-S2 | 184 | 24 | -0,686 | -3,72 | 8,5 % | -852,29 | -955,98 |
| 2023-S1 | 181 | 23 | -0,400 | -3,19 | 5,4 % | -445,52 | +138,25 |
| 2023-S2 | 184 | 16 | +0,194 | 0,49 | 2,2 % | +141,10 | +363,84 |
| 2024-S1 | 182 | 18 | +1,227 | 1,83 | 1,6 % | +1 081,50 | +265,42 |
| 2024-S2 | 184 | 23 | +0,694 | 1,17 | 5,0 % | +790,34 | +1 075,28 |
| 2025-S1 | 181 | 19 | -0,014 | -0,18 | 2,5 % | -54,87 | -356,93 |
| 2025-S2 (partiel) | 31 | 5 | +1,222 | non significatif | 0,6 % | +344,67 | +355,17 |

Semestres positifs 7 sur 10 (70 %). Hors semestre partiel 6 sur 9. Réévalué 8 sur 10, hors semestre partiel 7 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 91 | 33,0 % | +0,667 | +3 026,08 | 52,62 | 846,49 | 120,12 | 726,38 |
| shorts | 80 | 23,8 % | -0,317 | -1 322,77 | 32,67 | 51,79 | 48,40 | 3,39 |
| total | 171 | 28,7 % | +0,207 | +1 703,31 | 85,29 | 898,28 | 168,51 | 729,77 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,013, 12,566 |
| PSR(0) | 0,811 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,510 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 11,304, 169,694 |
| PSR(0) | 0,893 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,648 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,160 |
| Sharpe (solde quotidien) | 0,403 |
| Sortino (trades) | 1,112 |
| Sortino (solde quotidien) | 0,514 |
| Calmar (trades) | 1,448 |
| Calmar (solde quotidien) | 1,101 |
| Drawdown du compte | 13,4 % |
| Capital final | 11 703,31 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-43-49.zip`, analyse du 2026-11-01T00:29:18+00:00.
