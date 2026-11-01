# Verdict hors échantillon de STRAT-20261031-01

**Verdict : `rejetée`.** Trois critères figés sur sept échouent. La stratégie ne passe pas au papier.

Écrit le 01/11/2026 d'après l'unique run de E10 et de E11 (freqtrade 2026.10, exports du 01/11/2026 08:50 UTC, données publiques des perpétuels Binance, 01/08/2025 au 31/10/2026). Résultat de recherche, aucune recommandation.

**Hors échantillon non aveugle.** La fiche citait déjà une baisse avec rebonds sur cette période. Les données de backtest du bloc n'avaient pas été lues. Le 31/10, elles sont restées 3 min 12 s sur le disque sans affichage. Le résultat n'est pas flatteur, donc ce point ne l'explique pas.

## 1. Critères figés avant l'ouverture (`AVENANT_AVANT_E10.md` § 9)

| Critère | Échec si | Mesure | Résultat |
|---|---|---:|---|
| Espérance nette, E10 | ≤ 0,2 R | +0,147 R | **Échec** |
| Borne basse de l'intervalle à 90 % par blocs, E10 | ≤ 0 | -0,376 R (haut +0,744 R) | **Échec** |
| Sharpe réévalué, E10 | < 1,58 | 0,354 | **Échec** |
| Drawdown réévalué, E10 | > 20 % | 6,2 % | Passe |
| Espérance à frais doublés, E11 | ≤ 0 R | +0,135 R | Passe |
| Trades hors échantillon, E10 | < 30 | 46 | Passe |
| Trades au total, E00-ref + E10 | < 100 | 224 | Passe |

Lecture, non éliminatoire : DSR réévalué 0,313 pour N = 15, contre un seuil de lecture de 0,95. DSR réalisé 0,402. Le recalcul séparé depuis l'export redonne 46 trades, +0,147 R et un capital final de 10 309,30 USDT. Empreinte de l'export de E10 : `d214eebb…2912`.

## 2. Résultats

| | E10 (frais 0,05 %) | E11 (frais 0,10 %) |
|---|---:|---:|
| Trades, longs et shorts | 46, 21 et 25 | 46, 21 et 25 |
| Espérance | +0,147 R | +0,135 R |
| Espérance hors sorties forcées | +0,161 R | +0,149 R |
| Intervalle à 90 % par blocs | -0,376 à +0,744 R | -0,388 à +0,732 R |
| Intervalle à 90 % iid, comparaison | -0,232 à +0,576 R | -0,244 à +0,564 R |
| Taux de réussite | 32,6 % | 32,6 % |
| Rendement sur 457 jours | +3,09 % | +2,81 % |
| Sharpe réévalué | 0,354 | 0,325 |
| Drawdown réévalué | 6,2 % | 6,3 % |
| DSR réévalué, N = 15 | 0,313 | 0,301 |

## 3. Avocat du diable

Thèse attaquée : les tendances de plusieurs semaines donnent à cette stratégie un edge qui survit aux frais et au hasard.

**Verdict de l'avocat : rejetée.**

**Argument 1, le résultat ne se distingue pas du hasard.** L'intervalle par blocs va de -0,376 à +0,744 R. La p-value de freqtrade sur le profit moyen vaut 0,585. Le DSR vaut 0,313.

**Argument 2, un seul trade porte tout le gain.** Le short BCH du 14/05/2026 au 02/07/2026 rapporte +7,35 R et 361,58 USDT, soit 117 % du P&L de 309,30 USDT. Sans lui, l'espérance tombe à -0,013 R et le P&L à -52 USDT. Sans les trois meilleurs, elle tombe à -0,173 R.

**Argument 3, le comportement s'inverse d'un bloc à l'autre.** Sur 2021 à juillet 2025, les longs font +0,606 R et les shorts -0,119 R. Sur E10, les longs font -0,239 R et les shorts +0,471 R. Cette inversion suit le régime et ne montre pas un edge stable.

**Contre-arguments pris en compte, et insuffisants.**
- Le marché moyen des 10 paires a fait -39,51 % selon freqtrade, et la stratégie +3,09 %. Mais son exposition est faible (mise moyenne de 632 USDT sur 10 000) et elle peut shorter, donc la comparaison n'est pas directe.
- Le rendement annualisé de 2,46 % reste sous le taux court de 3,875 % utilisé pour STRAT-02.
- Le drawdown faible tient en partie à la petite taille des positions. Le creux réévalué tombe le dernier jour du bloc, et 2026-T4 affiche -0,70 R sur 7 trades.

**Scénario d'échec en réel.** Une longue suite de petites pertes (10 pertes consécutives ici, 2025-S2 à -0,388 R) attend un rare grand mouvement qui peut ne pas venir. Ce chemin paraît assez probable pour dominer [environ 50 à 70 %, jugement non calculé]. S'y ajoutent des coûts non mesurés : glissement au stop et entrée réelle après l'ouverture.

**Biais retenus.**
- Univers choisi avec le recul : DOGE et TRX n'étaient pas parmi les plus liquides fin 2020 [rangs 42 et 19], et le biais du survivant demeure.
- Récit : le short BCH et la baisse de 2026 invitent à une histoire de « tendance captée » que 46 trades ne soutiennent pas.
- Ordre de la whitelist : sur 2021 à juillet 2025, il faisait varier l'espérance de +0,175 à +0,528 R. E10 n'est qu'un chemin parmi d'autres. Ce biais ne sauve pas le résultat, car le verdict porte sur l'ordre figé.

**Ce que ce verdict ne dit pas.** Il ne prouve pas l'absence de tout edge de tendance. Avec 46 trades, l'intervalle est large et un edge modeste aurait pu échouer aussi. Mais la fiche annonçait qu'un échec dû au régime reste un échec.

## 4. Conséquences

- Statut `rejetée`. Aucun papier, aucun réel, aucun capital.
- Le bloc d'août 2025 à octobre 2026 est consommé. Aucune variante de cette stratégie ne s'y teste pour en tirer une validation.
- Toute reprise est une nouvelle stratégie, avec une nouvelle fiche et des essais comptés, jugée sur des données postérieures au 31/10/2026.
- Non lancés : les 200 permutations d'ordre et la sensibilité d'attribution des places (points non cités par Jonathan et Téo, qui relisent ce bloc). Le correctif de stop devient sans objet pour cette version.

Sources : `resultats/E10_metriques.json`, `resultats/E11_metriques.json`, `resultats/brut/E10_backtesting.txt`, `resultats/brut/E11_backtesting.txt`, `resultats/brut/E10_download-data.txt`, `AVENANT_AVANT_E10.md`.
