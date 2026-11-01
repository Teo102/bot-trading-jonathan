# Métriques de l'essai E01 (TrendDonchianV1)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E01/backtest-result-2026-10-31_22-33-54.zip --essai E01 --start 2021-01-01 --end 2024-06-30 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:28:56+00:00 |
| Export analysé | `user_data/backtest_results/E01/backtest-result-2026-10-31_22-33-54.zip` |
| Membre lu | `backtest-result-2026-10-31_22-33-54.json` |
| sha256 de l'export | `024811d1a688a82ec99c7b7f3a069494ce5e0a9aef29aa5f98c1ccdbb1efd32c` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:33:52+00:00 |
| Plage analysée | 2021-01-01 à 2024-06-30 |
| Timerange de l'export | 20210101-20240630 |
| Backtest réel | 2021-01-01 00:00:00 à 2024-06-30 00:00:00 |
| Capital de départ, risque nominal, frais par côté | 10 000,00, 0,50 %, 0,0005 |
| Simulations, graine | 5000, 0 |
| Tirages et graine des méthodes par blocs | 50000, 20261101 |
| Longueur des blocs | 10 trades, 30 jours |

## Trades

| Mesure | Valeur |
|---|---|
| Trades (longs, shorts) | 135 (70, 65) |
| Sorties force_exit | 2 |
| Taux de réussite | 33,3 % |
| Gain moyen, perte moyenne | 1,93 R, -0,77 R |
| Espérance | +0,134 R |
| Espérance hors force_exit | +0,124 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,115 à +0,408 R |
| Intervalle à 90 % iid (50000 tirages) | -0,116 à +0,408 R |
| Intervalle à 90 % par blocs de 10 trades | -0,132 à +0,403 R |
| Intervalle à 90 % par épisodes (18) | -0,148 à +0,384 R |
| Intervalle à 90 % par mois d'ouverture (38) | -0,145 à +0,456 R |
| Espérance, frais doublés (approximation) | +0,125 R |
| Espérance, frais et financement payé doublés (approximation) | +0,009 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 10,9 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 24,9 % |
| Part du gain du meilleur trade (en R) | 59 % |
| Part du gain du meilleur trade (en P&L) | 62 % |
| Capital final | 10 876,93 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1277 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 2,4 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,310 |
| Sharpe quotidien non annualisé | 0,01622 |
| Sortino annualisé | 0,438 |
| Calmar | 0,191 |
| Drawdown maximal | 12,8 % |
| Creux du drawdown | 2023-06-09 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1277 jours civils, dont 1163 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 8,8 % |
| Rendement annualisé | 2,4 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,435 |
| Sharpe quotidien non annualisé | 0,02276 |
| Sortino annualisé | 1,090 |
| Calmar | 0,222 |
| Drawdown maximal | 10,9 % |
| Taux de réussite | 33,3 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,788 | 1,43 | 1,5 % | +432,93 | +361,64 |
| 2021-S2 | 184 | 24 | -0,080 | -0,36 | 4,4 % | -110,83 | +16,59 |
| 2022-S1 | 181 | 9 | +0,855 | 2,14 | 0,5 % | +399,02 | +740,51 |
| 2022-S2 | 184 | 23 | -0,302 | -1,54 | 5,9 % | -380,64 | -731,51 |
| 2023-S1 | 181 | 26 | -0,311 | -2,62 | 5,5 % | -409,29 | +175,01 |
| 2023-S2 | 184 | 18 | +0,191 | 0,50 | 2,4 % | +162,73 | +379,39 |
| 2024-S1 | 182 | 24 | +0,636 | 1,65 | 1,7 % | +783,02 | -64,71 |

Semestres positifs 4 sur 7 (57 %). Hors semestre partiel 4 sur 7. Réévalué 5 sur 7, hors semestre partiel 5 sur 7. Semestres avec au moins un trade 7.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 70 | 34,3 % | +0,331 | +1 156,79 | 37,22 | 765,49 | 76,45 | 689,04 |
| shorts | 65 | 32,3 % | -0,078 | -279,86 | 27,54 | 26,62 | 50,37 | -23,75 |
| total | 135 | 33,3 % | +0,134 | +876,93 | 64,77 | 792,11 | 126,82 | 665,28 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | -0,293, 9,058 |
| PSR(0) | 0,718 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,433 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 9,032, 127,947 |
| PSR(0) | 0,817 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,573 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,138 |
| Sharpe (solde quotidien) | 0,396 |
| Sortino (trades) | 0,752 |
| Sortino (solde quotidien) | 0,504 |
| Calmar (trades) | 1,201 |
| Calmar (solde quotidien) | 1,079 |
| Drawdown du compte | 10,9 % |
| Capital final | 10 876,93 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-33-54.zip`, analyse du 2026-11-01T00:28:56+00:00.
