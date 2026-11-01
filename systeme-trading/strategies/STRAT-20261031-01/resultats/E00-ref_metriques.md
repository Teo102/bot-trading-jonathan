# Métriques de l'essai E00-ref (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E00-ref/backtest-result-2026-10-31_22-45-08.zip --essai E00-ref --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:23+00:00 |
| Export analysé | `user_data/backtest_results/E00-ref/backtest-result-2026-10-31_22-45-08.zip` |
| Membre lu | `backtest-result-2026-10-31_22-45-08.json` |
| sha256 de l'export | `bae5c5708265ab4fd0bb191e04e442ab68189feeeed3d6d9869e53b1d304571b` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:44:55+00:00 |
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
| Trades (longs, shorts) | 178 (95, 83) |
| Sorties force_exit | 3 |
| Taux de réussite | 33,7 % |
| Gain moyen, perte moyenne | 2,26 R, -0,74 R |
| Espérance | +0,268 R |
| Espérance hors force_exit | +0,228 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,003 à +0,562 R |
| Intervalle à 90 % iid (50000 tirages) | +0,002 à +0,558 R |
| Intervalle à 90 % par blocs de 10 trades | -0,035 à +0,614 R |
| Intervalle à 90 % par épisodes (22) | -0,025 à +0,607 R |
| Intervalle à 90 % par mois d'ouverture (51) | -0,026 à +0,617 R |
| Espérance, frais doublés (approximation) | +0,258 R |
| Espérance, frais et financement payé doublés (approximation) | +0,157 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 10,9 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 25,7 % |
| Part du gain du meilleur trade (en R) | 28 % |
| Part du gain du meilleur trade (en P&L) | 29 % |
| Capital final | 12 461,17 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 4,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,563 |
| Sharpe quotidien non annualisé | 0,02946 |
| Sortino annualisé | 0,823 |
| Calmar | 0,386 |
| Drawdown maximal | 12,8 % |
| Creux du drawdown | 2023-06-09 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1526 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 24,6 % |
| Rendement annualisé | 4,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,711 |
| Sharpe quotidien non annualisé | 0,03720 |
| Sortino annualisé | 2,169 |
| Calmar | 0,450 |
| Drawdown maximal | 10,9 % |
| Taux de réussite | 33,7 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,788 | 1,43 | 1,5 % | +432,93 | +361,64 |
| 2021-S2 | 184 | 24 | -0,080 | -0,36 | 4,4 % | -110,83 | +16,59 |
| 2022-S1 | 181 | 9 | +0,855 | 2,14 | 0,5 % | +399,02 | +740,51 |
| 2022-S2 | 184 | 23 | -0,302 | -1,54 | 5,9 % | -380,64 | -731,51 |
| 2023-S1 | 181 | 26 | -0,311 | -2,62 | 5,5 % | -409,29 | +175,01 |
| 2023-S2 | 184 | 18 | +0,191 | 0,50 | 2,4 % | +162,73 | +379,39 |
| 2024-S1 | 182 | 22 | +0,619 | 1,48 | 1,7 % | +693,34 | -107,34 |
| 2024-S2 | 184 | 22 | +1,060 | 1,74 | 1,8 % | +1 238,08 | +1 482,59 |
| 2025-S1 | 181 | 19 | +0,015 | -0,07 | 2,1 % | -24,77 | -218,60 |
| 2025-S2 (partiel) | 31 | 4 | +1,920 | non significatif | 0,1 % | +460,60 | +362,88 |

Semestres positifs 6 sur 10 (60 %). Hors semestre partiel 5 sur 9. Réévalué 7 sur 10, hors semestre partiel 6 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 95 | 36,8 % | +0,606 | +3 019,81 | 55,52 | 894,57 | 93,67 | 800,90 |
| shorts | 83 | 30,1 % | -0,119 | -558,65 | 36,07 | 30,70 | 63,22 | -32,52 |
| total | 178 | 33,7 % | +0,268 | +2 461,17 | 91,58 | 925,27 | 156,89 | 768,38 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,026, 11,976 |
| PSR(0) | 0,886 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,635 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 10,684, 156,507 |
| PSR(0) | 0,970 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,832 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,237 |
| Sharpe (solde quotidien) | 0,611 |
| Sortino (trades) | 1,531 |
| Sortino (solde quotidien) | 0,846 |
| Calmar (trades) | 2,572 |
| Calmar (solde quotidien) | 2,082 |
| Drawdown du compte | 10,9 % |
| Capital final | 12 461,17 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-45-08.zip`, analyse du 2026-11-01T00:29:23+00:00.
