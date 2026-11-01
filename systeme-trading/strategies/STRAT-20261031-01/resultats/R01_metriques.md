# Métriques de l'essai R01 (TrendDonchianV1_R01)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/R01/backtest-result-2026-10-31_22-43-34.zip --essai R01 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:16+00:00 |
| Export analysé | `user_data/backtest_results/R01/backtest-result-2026-10-31_22-43-34.zip` |
| Membre lu | `backtest-result-2026-10-31_22-43-34.json` |
| sha256 de l'export | `8620cfc2ec2411c41cefb0398519919d1d0969c02f20d8e3db62524ec3a0236b` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:43:30+00:00 |
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
| Trades (longs, shorts) | 176 (96, 80) |
| Sorties force_exit | 3 |
| Taux de réussite | 38,6 % |
| Gain moyen, perte moyenne | 2,56 R, -0,75 R |
| Espérance | +0,524 R |
| Espérance hors force_exit | +0,483 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | +0,107 à +1,054 R |
| Intervalle à 90 % iid (50000 tirages) | +0,114 à +1,050 R |
| Intervalle à 90 % par blocs de 10 trades | +0,105 à +1,049 R |
| Intervalle à 90 % par épisodes (20) | +0,097 à +1,067 R |
| Intervalle à 90 % par mois d'ouverture (53) | +0,087 à +1,104 R |
| Espérance, frais doublés (approximation) | +0,515 R |
| Espérance, frais et financement payé doublés (approximation) | +0,408 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 8,8 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 21,3 % |
| Part du gain du meilleur trade (en R) | 49 % |
| Part du gain du meilleur trade (en P&L) | 51 % |
| Capital final | 15 211,30 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 9,6 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,934 |
| Sharpe quotidien non annualisé | 0,04888 |
| Sortino annualisé | 1,410 |
| Calmar | 0,997 |
| Drawdown maximal | 9,6 % |
| Creux du drawdown | 2025-06-24 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1532 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 52,1 % |
| Rendement annualisé | 9,6 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,749 |
| Sharpe quotidien non annualisé | 0,03920 |
| Sortino annualisé | 4,642 |
| Calmar | 1,382 |
| Drawdown maximal | 6,9 % |
| Taux de réussite | 38,6 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +1,637 | 2,10 | 1,5 % | +893,25 | +818,81 |
| 2021-S2 | 184 | 22 | +0,204 | 0,70 | 2,2 % | +234,22 | +369,18 |
| 2022-S1 | 181 | 12 | +0,538 | 1,83 | 0,9 % | +360,60 | +711,15 |
| 2022-S2 | 184 | 18 | -0,051 | -0,25 | 3,3 % | -65,77 | -419,51 |
| 2023-S1 | 181 | 25 | -0,264 | -2,42 | 3,3 % | -371,37 | +279,76 |
| 2023-S2 | 184 | 16 | +0,376 | 0,89 | 1,3 % | +331,15 | +565,22 |
| 2024-S1 | 182 | 22 | +0,657 | 1,56 | 1,4 % | +822,55 | -159,34 |
| 2024-S2 | 184 | 24 | -0,098 | -0,48 | 3,6 % | -149,85 | +2 300,80 |
| 2025-S1 | 181 | 22 | +2,005 | 1,23 | 2,4 % | +2 528,58 | +265,87 |
| 2025-S2 (partiel) | 31 | 4 | +2,149 | non significatif | 0,1 % | +627,94 | +479,37 |

Semestres positifs 7 sur 10 (70 %). Hors semestre partiel 6 sur 9. Réévalué 8 sur 10, hors semestre partiel 7 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 96 | 37,5 % | +0,986 | +5 408,00 | 63,10 | 979,68 | 104,23 | 875,45 |
| shorts | 80 | 40,0 % | -0,030 | -196,70 | 38,99 | 41,07 | 71,96 | -30,88 |
| total | 176 | 38,6 % | +0,524 | +5 211,30 | 102,10 | 1 020,75 | 176,18 | 844,56 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | 0,288, 14,982 |
| PSR(0) | 0,977 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,874 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 29,304, 1032,279 |
| PSR(0) | 0,999 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,958 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,264 |
| Sharpe (solde quotidien) | 0,685 |
| Sortino (trades) | 2,886 |
| Sortino (solde quotidien) | 2,051 |
| Calmar (trades) | 8,589 |
| Calmar (solde quotidien) | 7,540 |
| Drawdown du compte | 6,9 % |
| Capital final | 15 211,30 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-43-34.zip`, analyse du 2026-11-01T00:29:16+00:00.
