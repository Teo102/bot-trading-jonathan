# CDV de STRAT-20261102-06 — métriques

Passage du 2026-11-03T10:52:50Z. Bloc dev+val, lundis 2021-01-04 à 2025-07-21. Données data.binance.vision lues jusqu'à 2025-07-28T02:00:00Z (verrou de bloc). Empreinte des données : `864f7048f588760f…`. Résultat de recherche, sans verdict : le verdict ne porte que sur E19/E20 (fiche § 1.8).

| Mesure | Valeur |
|---|---:|
| Semaines, dont vides | 238, 12 |
| Lignes, stops, délistages | 1330, 220, 0 |
| Rendement net cumulé, brut 100 % | +207.68 % |
| Moyenne hebdomadaire nette | +0.87 % |
| IC 90 % par blocs de 4 semaines | [+0.42 % ; +1.32 %] |
| Sharpe net annualisé | 1.307 |
| Bêta hebdomadaire sur BTC | -0.068 |
| Rendement résiduel (alpha) annualisé | +48.42 % |
| Sharpe résiduel annualisé | 1.403 |
| Drawdown maximal, brut 100 % | -30.87 % |
| Espérance par ligne (publiée, non éliminatoire) | +0.030 R |
| Jambe longue, jambe courte | +36.99 %, +179.14 % |
| Prix, financement, coûts | +221.53 %, -5.40 %, -8.45 % |
| Années positives | 4 sur 5 |
| Part maximale d'un mois, d'un nom dans le gain | 12.2%, 5.7% (DENTUSDT) |

Par année : 2021 -2.19 %, 2022 +9.04 %, 2023 +53.87 %, 2024 +84.93 %, 2025 +62.04 %.

Repli du prix de marque sur le contrat : 0 symboles. Sans financement : 0. Sans archive 1 h (lignes « absent ») : 0. Incidents réseau : 0.

Trous des archives mensuelles comblés par les journalières : 1d 318 jours comblés, 5 introuvables (52 symboles), marque 235 jours comblés, 0 introuvables (76 symboles), 1h 166 jours comblés, 5 introuvables (21 symboles).
Semaines où la règle H1 a retiré au moins un nom du classement : 0, noms retirés en moyenne : 0.00.

Variante : base (controle de reproduction, hors registre). Surcharges : {"cotation": {}, "moteur": {}, "special": {}}. Notionnel par ligne : 0.0833. Commentaire du registre : .

| Sous-bloc | Semaines | Net brut 100 % | Sharpe | Alpha annualisé | DD | Nom max | Mois max | Portes net, alpha, nom, mois, DD |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| total | 238 | +207.68% | 1.307 | +48.42% | -30.87% | 5.7% (DENTUSDT) | 12.2% | True, True, True, True, True |
| developpement | 182 | +94.23% | 0.839 | +28.13% | -30.87% | 12.5% (DENTUSDT) | 21.1% | True, True, True, True, True |
| validation | 56 | +113.45% | 2.547 | +123.72% | -12.86% | 8.2% (MUBARAKUSDT) | 22.3% | True, True, True, True, True |

Portes de groupe (fiche § 7) : 9 voisins sur 11 rentables (E03 à E12, E14), E16 et E17 > 0, E18 < 0. E13 et E18 ne sont jamais éligibles. Résultat de recherche, aucun ordre.

## Contrôle de reproduction

Semaines comparées : 238 (base continue 238, E01 + E02 238). Écart maximal hors semaines admises : 0.00e+00, sur 0 semaines. Écart sur les semaines admises : {Timestamp('2024-06-24 00:00:00'): 0.0009681453038381804, Timestamp('2024-07-01 00:00:00'): 0.000642022512158065, Timestamp('2025-07-21 00:00:00'): 0.0}. Verdict : **REPRODUCTION CONFORME**.
