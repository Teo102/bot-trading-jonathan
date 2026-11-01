# Métriques de l'essai E08 (TrendDonchianV1_E08)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E08/backtest-result-2026-10-31_22-43-08.zip --essai E08 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:11+00:00 |
| Export analysé | `user_data/backtest_results/E08/backtest-result-2026-10-31_22-43-08.zip` |
| Membre lu | `backtest-result-2026-10-31_22-43-08.json` |
| sha256 de l'export | `ff2140f9b21302dccff0f15f8785617a372dbbcdded07f4b9f958ac4109408d3` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:43:04+00:00 |
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
| Trades (longs, shorts) | 165 (88, 77) |
| Sorties force_exit | 3 |
| Taux de réussite | 37,0 % |
| Gain moyen, perte moyenne | 1,84 R, -0,70 R |
| Espérance | +0,241 R |
| Espérance hors force_exit | +0,205 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,004 à +0,502 R |
| Intervalle à 90 % iid (50000 tirages) | -0,000 à +0,503 R |
| Intervalle à 90 % par blocs de 10 trades | -0,023 à +0,540 R |
| Intervalle à 90 % par épisodes (22) | -0,031 à +0,546 R |
| Intervalle à 90 % par mois d'ouverture (51) | -0,022 à +0,552 R |
| Espérance, frais doublés (approximation) | +0,233 R |
| Espérance, frais et financement payé doublés (approximation) | +0,141 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 9,3 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 22,0 % |
| Part du gain du meilleur trade (en R) | 28 % |
| Part du gain du meilleur trade (en P&L) | 29 % |
| Capital final | 12 042,39 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 4,1 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,558 |
| Sharpe quotidien non annualisé | 0,02923 |
| Sortino annualisé | 0,816 |
| Calmar | 0,456 |
| Drawdown maximal | 9,1 % |
| Creux du drawdown | 2023-06-22 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1540 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 20,4 % |
| Rendement annualisé | 4,1 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,716 |
| Sharpe quotidien non annualisé | 0,03748 |
| Sortino annualisé | 2,140 |
| Calmar | 0,638 |
| Drawdown maximal | 6,5 % |
| Taux de réussite | 37,0 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,600 | 1,29 | 1,4 % | +329,42 | +270,58 |
| 2021-S2 | 184 | 23 | -0,105 | -0,51 | 4,1 % | -132,14 | -27,24 |
| 2022-S1 | 181 | 9 | +0,721 | 2,15 | 0,4 % | +331,88 | +613,25 |
| 2022-S2 | 184 | 18 | -0,221 | -1,11 | 4,1 % | -217,68 | -506,13 |
| 2023-S1 | 181 | 22 | -0,187 | -2,01 | 2,5 % | -209,99 | +289,80 |
| 2023-S2 | 184 | 18 | +0,003 | 0,02 | 3,0 % | -1,82 | +173,03 |
| 2024-S1 | 182 | 18 | +0,821 | 1,92 | 1,2 % | +761,49 | +54,53 |
| 2024-S2 | 184 | 23 | +0,737 | 1,51 | 2,4 % | +893,73 | +1 125,64 |
| 2025-S1 | 181 | 19 | -0,054 | -0,44 | 2,3 % | -87,70 | -246,84 |
| 2025-S2 (partiel) | 31 | 4 | +1,608 | non significatif | 0,1 % | +375,18 | +295,78 |

Semestres positifs 5 sur 10 (50 %). Hors semestre partiel 4 sur 9. Réévalué 7 sur 10, hors semestre partiel 6 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 88 | 40,9 % | +0,522 | +2 399,04 | 42,78 | 749,69 | 71,77 | 677,92 |
| shorts | 77 | 32,5 % | -0,080 | -356,65 | 27,35 | 25,21 | 56,60 | -31,39 |
| total | 165 | 37,0 % | +0,241 | +2 042,39 | 70,14 | 774,90 | 128,36 | 646,53 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,008, 12,166 |
| PSR(0) | 0,884 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,632 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 10,732, 159,184 |
| PSR(0) | 0,971 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,836 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,226 |
| Sharpe (solde quotidien) | 0,616 |
| Sortino (trades) | 1,295 |
| Sortino (solde quotidien) | 0,754 |
| Calmar (trades) | 3,600 |
| Calmar (solde quotidien) | 2,927 |
| Drawdown du compte | 6,5 % |
| Capital final | 12 042,39 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-43-08.zip`, analyse du 2026-11-01T00:29:11+00:00.
