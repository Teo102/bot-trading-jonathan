# Métriques de l'essai E05 (TrendDonchianV1_E05)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E05/backtest-result-2026-10-31_22-42-32.zip --essai E05 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:04+00:00 |
| Export analysé | `user_data/backtest_results/E05/backtest-result-2026-10-31_22-42-32.zip` |
| Membre lu | `backtest-result-2026-10-31_22-42-32.json` |
| sha256 de l'export | `8dbf5c78f1dba86f9e90da8f6b8c1b7b3336dc03156ef6723e2b8857f5acd1b8` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:42:28+00:00 |
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
| Trades (longs, shorts) | 188 (100, 88) |
| Sorties force_exit | 3 |
| Taux de réussite | 34,6 % |
| Gain moyen, perte moyenne | 2,09 R, -0,71 R |
| Espérance | +0,254 R |
| Espérance hors force_exit | +0,216 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | +0,010 à +0,520 R |
| Intervalle à 90 % iid (50000 tirages) | +0,012 à +0,525 R |
| Intervalle à 90 % par blocs de 10 trades | -0,030 à +0,573 R |
| Intervalle à 90 % par épisodes (30) | -0,042 à +0,578 R |
| Intervalle à 90 % par mois d'ouverture (51) | -0,031 à +0,593 R |
| Espérance, frais doublés (approximation) | +0,245 R |
| Espérance, frais et financement payé doublés (approximation) | +0,149 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 10,2 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 25,2 % |
| Part du gain du meilleur trade (en R) | 28 % |
| Part du gain du meilleur trade (en P&L) | 29 % |
| Capital final | 12 453,11 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 4,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,572 |
| Sharpe quotidien non annualisé | 0,02993 |
| Sortino annualisé | 0,835 |
| Calmar | 0,387 |
| Drawdown maximal | 12,7 % |
| Creux du drawdown | 2023-07-30 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1521 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 24,5 % |
| Rendement annualisé | 4,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,714 |
| Sharpe quotidien non annualisé | 0,03736 |
| Sortino annualisé | 2,230 |
| Calmar | 0,471 |
| Drawdown maximal | 10,4 % |
| Taux de réussite | 34,6 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,855 | 1,56 | 1,2 % | +470,85 | +399,33 |
| 2021-S2 | 184 | 26 | -0,091 | -0,44 | 5,0 % | -134,22 | -62,70 |
| 2022-S1 | 181 | 9 | +0,735 | 1,84 | 0,4 % | +342,31 | +738,26 |
| 2022-S2 | 184 | 26 | -0,318 | -1,50 | 7,3 % | -451,60 | -819,90 |
| 2023-S1 | 181 | 28 | -0,182 | -1,34 | 3,8 % | -260,03 | -14,22 |
| 2023-S2 | 184 | 18 | -0,023 | -0,09 | 1,9 % | -21,93 | +538,70 |
| 2024-S1 | 182 | 20 | +0,955 | 1,95 | 1,0 % | +966,45 | +166,61 |
| 2024-S2 | 184 | 27 | +0,701 | 1,40 | 3,6 % | +987,34 | +1 244,64 |
| 2025-S1 | 181 | 19 | +0,118 | 0,38 | 1,5 % | +93,33 | -100,54 |
| 2025-S2 (partiel) | 31 | 4 | +1,921 | non significatif | 0,1 % | +460,61 | +362,93 |

Semestres positifs 6 sur 10 (60 %). Hors semestre partiel 5 sur 9. Réévalué 6 sur 10, hors semestre partiel 5 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 100 | 38,0 % | +0,574 | +2 994,39 | 58,60 | 891,65 | 79,47 | 812,18 |
| shorts | 88 | 30,7 % | -0,109 | -541,28 | 37,48 | 32,68 | 60,46 | -27,78 |
| total | 188 | 34,6 % | +0,254 | +2 453,11 | 96,08 | 924,33 | 139,94 | 784,40 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,013, 12,439 |
| PSR(0) | 0,889 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,642 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 10,795, 158,749 |
| PSR(0) | 0,971 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,835 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,250 |
| Sharpe (solde quotidien) | 0,614 |
| Sortino (trades) | 1,537 |
| Sortino (solde quotidien) | 0,897 |
| Calmar (trades) | 2,693 |
| Calmar (solde quotidien) | 2,179 |
| Drawdown du compte | 10,4 % |
| Capital final | 12 453,11 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-42-32.zip`, analyse du 2026-11-01T00:29:04+00:00.
