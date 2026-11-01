# Métriques de l'essai E06 (TrendDonchianV1_E06)

Résultats de recherche. Aucune promesse de gain, aucune recommandation.

## Traçabilité

| Élément | Valeur |
|---|---|
| Commande | `python analyse_strat.py user_data/backtest_results/E06/backtest-result-2026-10-31_22-42-42.zip --essai E06 --start 2021-01-01 --end 2025-07-31 --registry-json resultats/registre_dsr.json` |
| Horodatage de l'analyse (UTC) | 2026-11-01T00:29:06+00:00 |
| Export analysé | `user_data/backtest_results/E06/backtest-result-2026-10-31_22-42-42.zip` |
| Membre lu | `backtest-result-2026-10-31_22-42-42.json` |
| sha256 de l'export | `20cd993d1cce6961021c1bf618b6b31fef8fe84054271f91b056fe71256e266c` |
| Version freqtrade dans l'export | absente de l'export (vérifié pour freqtrade 2026.10) |
| Version freqtrade de l'environnement d'analyse | 2026.10 |
| Backtest exécuté le (UTC) | 2026-10-31T22:42:39+00:00 |
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
| Trades (longs, shorts) | 171 (89, 82) |
| Sorties force_exit | 3 |
| Taux de réussite | 32,2 % |
| Gain moyen, perte moyenne | 1,84 R, -0,79 R |
| Espérance | +0,058 R |
| Espérance hors force_exit | +0,012 R |
| Intervalle à 90 % iid (5000 tirages, graine 0) | -0,149 à +0,282 R |
| Intervalle à 90 % iid (50000 tirages) | -0,147 à +0,281 R |
| Intervalle à 90 % par blocs de 10 trades | -0,191 à +0,340 R |
| Intervalle à 90 % par épisodes (22) | -0,169 à +0,358 R |
| Intervalle à 90 % par mois d'ouverture (50) | -0,183 à +0,340 R |
| Espérance, frais doublés (approximation) | +0,048 R |
| Espérance, frais et financement payé doublés (approximation) | -0,054 R |
| Drawdown 95e centile (permutation des trades, comparaison) | 13,2 % |
| Drawdown 95e centile (blocs temporels de 30 jours, base reevaluee) | 33,4 % |
| Part du gain du meilleur trade (en R) | 107 % |
| Part du gain du meilleur trade (en P&L) | 123 % |
| Capital final | 10 399,71 |

## Métriques sur l'équité réévaluée chaque jour (base principale)

Série de 1673 jours civils. Latent au prix de clôture 1d, hors frais et financement latents.

| Mesure | Valeur |
|---|---|
| Rendement annualisé | 0,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,139 |
| Sharpe quotidien non annualisé | 0,00730 |
| Sortino annualisé | 0,190 |
| Calmar | 0,052 |
| Drawdown maximal | 16,5 % |
| Creux du drawdown | 2024-10-05 |

## Métriques sur l'équité réalisée (base de comparaison)

Série de 1673 jours civils, dont 1531 sans clôture comptés à 0. Équité réalisée à la clôture des trades, non réévaluée chaque jour. Cela lisse la volatilité et peut flatter le Sharpe.

| Mesure | Valeur |
|---|---|
| Rendement total | 4,0 % |
| Rendement annualisé | 0,9 % |
| Sharpe annualisé (base 365, sans risque 0 %) | 0,183 |
| Sharpe quotidien non annualisé | 0,00956 |
| Sortino annualisé | 0,420 |
| Calmar | 0,064 |
| Drawdown maximal | 13,4 % |
| Taux de réussite | 32,2 % |

## Par semestre civil (affectation à la clôture)

| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-S1 | 181 | 11 | +0,225 | 0,46 | 1,9 % | +119,35 | +50,22 |
| 2021-S2 | 184 | 21 | -0,134 | -0,62 | 3,7 % | -146,36 | -22,98 |
| 2022-S1 | 181 | 9 | +0,787 | 1,98 | 0,5 % | +354,24 | +683,30 |
| 2022-S2 | 184 | 22 | -0,308 | -1,50 | 5,8 % | -358,07 | -696,30 |
| 2023-S1 | 181 | 25 | -0,440 | -3,54 | 5,9 % | -534,48 | -272,01 |
| 2023-S2 | 184 | 18 | -0,250 | -1,20 | 2,7 % | -210,77 | -29,87 |
| 2024-S1 | 182 | 19 | +0,526 | 1,56 | 2,2 % | +465,62 | -34,11 |
| 2024-S2 | 184 | 23 | +0,337 | 0,88 | 4,2 % | +352,73 | +629,05 |
| 2025-S1 | 181 | 19 | -0,002 | -0,09 | 2,4 % | -26,58 | -210,05 |
| 2025-S2 (partiel) | 31 | 4 | +1,918 | non significatif | 0,1 % | +384,03 | +302,45 |

Semestres positifs 5 sur 10 (50 %). Hors semestre partiel 4 sur 9. Réévalué 4 sur 10, hors semestre partiel 3 sur 9. Semestres avec au moins un trade 10.

## Longs et shorts

| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| longs | 89 | 36,0 % | +0,277 | +1 141,77 | 47,39 | 822,29 | 71,65 | 750,64 |
| shorts | 82 | 28,0 % | -0,181 | -742,06 | 32,75 | 29,15 | 65,34 | -36,18 |
| total | 171 | 32,2 % | +0,058 | +399,71 | 80,15 | 851,44 | 136,99 | 714,45 |

Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.

## Sharpe déflaté (Bailey et López de Prado, 2014)

Calcul principal sur la série réévaluée, avec V réévaluée.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe réévalués connus) |
| N | 13 |
| V[SR] quotidien | 0,000152 |
| Asymétrie g3, kurtosis g4 | -1,372, 24,582 |
| PSR(0) | 0,617 |
| SR0 quotidien, annualisé | 0,0210, 0,401 |
| DSR | 0,289 |

Calcul second sur la série réalisée, non comparable d'un essai à l'autre.

| Mesure | Valeur |
|---|---|
| Source de N et V | registre resultats/registre_dsr.json (11 Sharpe connus) |
| N | 13 |
| V[SR] quotidien | 0,000113 |
| Asymétrie g3, kurtosis g4 | 8,408, 116,723 |
| PSR(0) | 0,658 |
| SR0 quotidien, annualisé | 0,0181, 0,346 |
| DSR | 0,358 |

## Contrôle face aux chiffres de freqtrade

Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.

| Mesure | Freqtrade |
|---|---:|
| Sharpe (trades) | 0,056 |
| Sharpe (solde quotidien) | 0,029 |
| Sortino (trades) | 0,277 |
| Sortino (solde quotidien) | 0,031 |
| Calmar (trades) | 0,341 |
| Calmar (solde quotidien) | 0,007 |
| Drawdown du compte | 13,4 % |
| Capital final | 10 399,71 |

## Avertissements

Registre hétérogène : 3 frais différent(e)s. V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.

Registre : 11 Sharpe connus pour 13 essais déclarés. V[SR] n'utilise que les Sharpe connus.

## Notes de méthode

Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes intrajournaliers.

Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, pas au risque effectif du trade.

L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.

Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau backtest avec --fee doublé (E09, E11) mesure réellement ce stress.

Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul principal.

Sources : export freqtrade `backtest-result-2026-10-31_22-42-42.zip`, analyse du 2026-11-01T00:29:06+00:00.
