# Métriques de l'essai E07 (TrendDonchianV1_E07)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E07/backtest-result-2026-10-31_22-42-53.zip --essai E07 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:09+00:00 |
| Export analysé | `user_data/backtest_results/E07/backtest-result-2026-10-31_22-42-53.zip` |
| Membre lu | `backtest-result-2026-10-31_22-42-53.json` |
| sha256 de l'export | `5879cd5c1b66b1dbdd4cf2b540c2d53e1a3427d1b88581a6ff858eb4d96ddc3a` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:42:48+00:00 |
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
| Trades (longs, shorts) | 186 (94, 92) |
| Sorties force_exit | 3 |
| Taux de réussite | 33,9 % |
| Gain moyen, perte moyenne | 3,45 R, -0,79 R |
| Espérance | +0,646 R |
| Espérance hors force_exit | +0,603 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | +0,209 à +1,162 R |
| Intervalle à 90 % iid (50000 tirages) | +0,198 à +1,154 R |
| Intervalle à 90 % par blocs de 10 trades | +0,070 à +1,353 R |
| Intervalle à 90 % par épisodes (22) | +0,044 à +1,417 R |
| Intervalle à 90 % par mois d'ouverture (52) | +0,170 à +1,212 R |
| Espérance, frais doublés (approximation) | +0,634 R |
| Espérance, frais et financement payé doublés (approximation) | +0,461 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 10,5 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 30,1 % |
| Part du gain du meilleur trade (en R) | 26 % |
| Part du gain du meilleur trade (en P&L) | 23 % |
| Capital final | 16 915,30 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 12,2 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,872 |
| Sharpe quotidien non annualisé | 0,04563 |
| Sortino annualisé | 1,351 |
| Calmar | 0,687 |
| Drawdown maximal | 17,7 % |
| Creux du drawdown | 2023-06-09 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1517 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 69,2 % |
| Rendement annualisé | 12,2 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 1,010 |
| Sharpe quotidien non annualisé | 0,05288 |
| Sortino annualisé | 5,213 |
| Calmar | 1,009 |
| Drawdown maximal | 12,0 % |
| Taux de réussite | 33,9 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +6,454 | 2,37 | 2,1 % | +3 570,55 | +3 454,82 |
| 2021-S2 | 184 | 25 | +0,015 | 0,05 | 3,9 % | +7,65 | +215,27 |
| 2022-S1 | 181 | 13 | +0,814 | 1,87 | 1,0 % | +720,99 | +826,90 |
| 2022-S2 | 184 | 24 | -0,595 | -4,20 | 7,1 % | -991,72 | -1 114,59 |
| 2023-S1 | 181 | 25 | -0,291 | -2,12 | 5,4 % | -473,80 | +52,49 |
| 2023-S2 | 184 | 18 | +0,109 | 0,43 | 2,2 % | +118,63 | +914,20 |
| 2024-S1 | 182 | 21 | +1,052 | 1,94 | 1,9 % | +1 457,97 | +139,55 |
| 2024-S2 | 184 | 25 | +0,990 | 1,46 | 3,9 % | +1 705,57 | +2 104,29 |
| 2025-S1 | 181 | 20 | +0,069 | 0,10 | 2,5 % | +31,03 | -282,58 |
| 2025-S2 (partiel) | 31 | 4 | +2,381 | non significatif | 0,1 % | +768,43 | +604,96 |

Semestres positifs 8 sur 10 (80 %). Hors semestre partiel 7 sur 9. Réévalué 8 sur 10, hors semestre partiel 7 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 94 | 39,4 % | +1,440 | +8 026,04 | 90,85 | 1 766,63 | 114,27 | 1 652,36 |
| shorts | 92 | 28,3 % | -0,166 | -1 110,74 | 65,74 | 74,61 | 101,23 | -26,62 |
| total | 186 | 33,9 % | +0,646 | +6 915,30 | 156,60 | 1 841,23 | 215,49 | 1 625,74 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 1,098, 26,432 |
| PSR(0) | 0,971 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,848 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 14,810, 270,362 |
| PSR(0) | 1,000 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,987 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,342 |
| Sharpe (solde quotidien) | 0,940 |
| Sortino (trades) | 3,591 |
| Sortino (solde quotidien) | 2,710 |
| Calmar (trades) | 6,561 |
| Calmar (solde quotidien) | 5,820 |
| Drawdown du compte | 12,0 % |
| Capital final | 16 915,30 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-42-53.zip`, analyse du 2026-11-01T00:29:09+00:00.
