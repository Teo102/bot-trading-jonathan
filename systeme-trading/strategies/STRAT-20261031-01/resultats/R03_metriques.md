# Métriques de l'essai R03 (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/R03/backtest-result-2026-10-31_22-44-14.zip --essai R03 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:21+00:00 |
| Export analysé | `user_data/backtest_results/R03/backtest-result-2026-10-31_22-44-14.zip` |
| Membre lu | `backtest-result-2026-10-31_22-44-14.json` |
| sha256 de l'export | `f2e491dadbdc2fbfa2db14c001290e57fe8b10aa32fa797abe1bddccbb7b24ea` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:44:06+00:00 |
| Plage analysée | 2021-01-01 à 2025-07-31 |
| Timerange de l'export | 20210101-20250731 |
| Backtest réel | 2021-01-01 00:00:00 à 2025-07-31 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,0015 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 178 (95, 83) |
| Sorties force_exit | 3 |
| Taux de réussite | 33,7 % |
| Gain moyen, perte moyenne | 2,24 R, -0,76 R |
| Espérance | +0,250 R |
| Espérance hors force_exit | +0,210 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,021 à +0,544 R |
| Intervalle à 90 % iid (50000 tirages) | -0,016 à +0,540 R |
| Intervalle à 90 % par blocs de 10 trades | -0,053 à +0,596 R |
| Intervalle à 90 % par épisodes (22) | -0,042 à +0,589 R |
| Intervalle à 90 % par mois d'ouverture (51) | -0,044 à +0,599 R |
| Espérance, frais doublés (approximation) | +0,221 R |
| Espérance, frais et financement payé doublés (approximation) | +0,120 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 11,3 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 26,5 % |
| Part du gain du meilleur trade (en R) | 30 % |
| Part du gain du meilleur trade (en P&L) | 31 % |
| Capital final | 12 264,51 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 4,6 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,525 |
| Sharpe quotidien non annualisé | 0,02746 |
| Sortino annualisé | 0,766 |
| Calmar | 0,344 |
| Drawdown maximal | 13,2 % |
| Creux du drawdown | 2023-06-09 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1526 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 22,6 % |
| Rendement annualisé | 4,6 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,662 |
| Sharpe quotidien non annualisé | 0,03467 |
| Sortino annualisé | 1,977 |
| Calmar | 0,404 |
| Drawdown maximal | 11,3 % |
| Taux de réussite | 33,7 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,775 | 1,41 | 1,5 % | +425,38 | +354,13 |
| 2021-S2 | 184 | 24 | -0,090 | -0,40 | 4,5 % | -121,96 | +5,33 |
| 2022-S1 | 181 | 9 | +0,843 | 2,12 | 0,5 % | +392,81 | +733,16 |
| 2022-S2 | 184 | 23 | -0,318 | -1,61 | 6,0 % | -399,02 | -748,84 |
| 2023-S1 | 181 | 26 | -0,332 | -2,77 | 5,6 % | -434,30 | +145,98 |
| 2023-S2 | 184 | 18 | +0,165 | 0,44 | 2,5 % | +139,22 | +354,78 |
| 2024-S1 | 182 | 22 | +0,597 | 1,43 | 1,8 % | +662,36 | -133,55 |
| 2024-S2 | 184 | 22 | +1,034 | 1,70 | 2,0 % | +1 190,21 | +1 435,26 |
| 2025-S1 | 181 | 19 | +0,001 | -0,12 | 2,3 % | -39,18 | -234,43 |
| 2025-S2 (partiel) | 31 | 4 | +1,900 | non significatif | 0,1 % | +448,98 | +352,69 |

Semestres positifs 6 sur 10 (60 %). Hors semestre partiel 5 sur 9. Réévalué 7 sur 10, hors semestre partiel 6 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 95 | 36,8 % | +0,586 | +2 884,82 | 165,46 | 892,13 | 92,86 | 799,27 |
| shorts | 83 | 30,1 % | -0,134 | -620,32 | 107,39 | 30,54 | 62,79 | -32,25 |
| total | 178 | 33,7 % | +0,250 | +2 264,51 | 272,85 | 922,67 | 155,64 | 767,03 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,024, 11,963 |
| PSR(0) | 0,869 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,604 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 10,615, 155,644 |
| PSR(0) | 0,957 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,794 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,220 |
| Sharpe (solde quotidien) | 0,562 |
| Sortino (trades) | 1,418 |
| Sortino (solde quotidien) | 0,748 |
| Calmar (trades) | 2,293 |
| Calmar (solde quotidien) | 1,829 |
| Drawdown du compte | 11,3 % |
| Capital final | 12 264,51 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-44-14.zip`, analyse du 2026-11-01T00:29:21+00:00.
