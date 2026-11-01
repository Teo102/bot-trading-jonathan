# Métriques de l'essai E04 (TrendDonchianV1_E04)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E04/backtest-result-2026-10-31_22-42-21.zip --essai E04 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:02+00:00 |
| Export analysé | `user_data/backtest_results/E04/backtest-result-2026-10-31_22-42-21.zip` |
| Membre lu | `backtest-result-2026-10-31_22-42-21.json` |
| sha256 de l'export | `1f94800394e89cef1a3c4a1431a2174bdfccf0fe9b6105fae79d8ca4f565b246` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:42:17+00:00 |
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
| Trades (longs, shorts) | 177 (93, 84) |
| Sorties force_exit | 3 |
| Taux de réussite | 31,6 % |
| Gain moyen, perte moyenne | 2,14 R, -0,71 R |
| Espérance | +0,190 R |
| Espérance hors force_exit | +0,147 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,064 à +0,465 R |
| Intervalle à 90 % iid (50000 tirages) | -0,058 à +0,467 R |
| Intervalle à 90 % par blocs de 10 trades | -0,101 à +0,531 R |
| Intervalle à 90 % par épisodes (26) | -0,089 à +0,529 R |
| Intervalle à 90 % par mois d'ouverture (51) | -0,094 à +0,522 R |
| Espérance, frais doublés (approximation) | +0,181 R |
| Espérance, frais et financement payé doublés (approximation) | +0,078 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 11,7 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 28,0 % |
| Part du gain du meilleur trade (en R) | 40 % |
| Part du gain du meilleur trade (en P&L) | 42 % |
| Capital final | 11 642,75 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 3,4 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,406 |
| Sharpe quotidien non annualisé | 0,02123 |
| Sortino annualisé | 0,587 |
| Calmar | 0,234 |
| Drawdown maximal | 14,4 % |
| Creux du drawdown | 2023-05-15 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1527 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 16,4 % |
| Rendement annualisé | 3,4 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,526 |
| Sharpe quotidien non annualisé | 0,02753 |
| Sortino annualisé | 1,573 |
| Calmar | 0,292 |
| Drawdown maximal | 11,6 % |
| Taux de réussite | 31,6 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,788 | 1,43 | 1,5 % | +432,93 | +361,64 |
| 2021-S2 | 184 | 22 | +0,063 | 0,25 | 3,3 % | +62,12 | +133,41 |
| 2022-S1 | 181 | 14 | +0,246 | 0,90 | 1,5 % | +179,71 | +411,21 |
| 2022-S2 | 184 | 21 | -0,453 | -2,89 | 5,5 % | -498,85 | -673,90 |
| 2023-S1 | 181 | 23 | -0,331 | -2,78 | 4,7 % | -381,66 | -169,15 |
| 2023-S2 | 184 | 19 | -0,230 | -1,16 | 3,1 % | -212,20 | +324,16 |
| 2024-S1 | 182 | 19 | +0,832 | 1,73 | 1,0 % | +772,04 | -0,50 |
| 2024-S2 | 184 | 23 | +0,882 | 1,50 | 2,9 % | +1 012,13 | +1 244,42 |
| 2025-S1 | 181 | 20 | -0,070 | -0,44 | 2,7 % | -115,80 | -391,23 |
| 2025-S2 (partiel) | 31 | 5 | +1,404 | non significatif | 0,6 % | +392,33 | +402,71 |

Semestres positifs 6 sur 10 (60 %). Hors semestre partiel 5 sur 9. Réévalué 6 sur 10, hors semestre partiel 5 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 93 | 33,3 % | +0,545 | +2 533,24 | 52,76 | 876,52 | 88,84 | 787,67 |
| shorts | 84 | 29,8 % | -0,202 | -890,48 | 35,36 | 43,47 | 54,93 | -11,46 |
| total | 177 | 31,6 % | +0,190 | +1 642,75 | 88,12 | 919,99 | 143,78 | 776,21 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | -0,022, 12,034 |
| PSR(0) | 0,807 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,504 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 11,519, 182,404 |
| PSR(0) | 0,908 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,675 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,174 |
| Sharpe (solde quotidien) | 0,411 |
| Sortino (trades) | 1,039 |
| Sortino (solde quotidien) | 0,570 |
| Calmar (trades) | 1,622 |
| Calmar (solde quotidien) | 1,173 |
| Drawdown du compte | 11,6 % |
| Capital final | 11 642,75 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-42-21.zip`, analyse du 2026-11-01T00:29:02+00:00.
