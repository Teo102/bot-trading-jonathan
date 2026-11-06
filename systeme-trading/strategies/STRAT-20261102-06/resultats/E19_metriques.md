# E19 de STRAT-20261102-06 — métriques

Passage du 2026-11-06T07:59:59Z. Bloc hors_echantillon, lundis 2025-08-04 à 2026-10-19. Données data.binance.vision lues jusqu'à 2026-10-26T02:00:00Z (verrou de bloc). Empreinte des données : `c65685de2dc9116b…`. Résultat de recherche, sans verdict : le verdict ne porte que sur E19/E20 (fiche § 1.8).

| Mesure | Valeur |
|---|---:|
| Semaines, dont vides | 64, 0 |
| Lignes, stops, délistages | 388, 67, 0 |
| Rendement net cumulé, brut 100 % | +64.06 % |
| Moyenne hebdomadaire nette | +1.00 % |
| IC 90 % par blocs de 4 semaines | [-0.04 % ; +2.13 %] |
| Sharpe net annualisé | 1.398 |
| Bêta hebdomadaire sur BTC | -0.014 |
| Rendement résiduel (alpha) annualisé | +51.75 % |
| Sharpe résiduel annualisé | 1.390 |
| Drawdown maximal, brut 100 % | -22.93 % |
| Espérance par ligne (publiée, non éliminatoire) | +0.032 R |
| Jambe longue, jambe courte | -21.96 %, +89.03 % |
| Prix, financement, coûts | +88.07 %, -21.01 %, -3.00 % |
| Années positives | 2 sur 2 |
| Part maximale d'un mois, d'un nom dans le gain | 38.1%, 18.6% (AVNTUSDT) |

Par année : 2025 +30.38 %, 2026 +33.68 %.

Repli du prix de marque sur le contrat : 0 symboles. Sans financement : 0. Sans archive 1 h (lignes « absent ») : 0. Incidents réseau : 0.

Trous des archives mensuelles comblés par les journalières : 1d 318 jours comblés, 13 introuvables (53 symboles), 1h 1 jours comblés, 0 introuvables (1 symboles), marque 86 jours comblés, 0 introuvables (86 symboles).
Semaines où la règle H1 a retiré au moins un nom du classement : 0, noms retirés en moyenne : 0.00.

Variante : base. Surcharges : {"cotation": {}, "moteur": {}, "special": {}}. Notionnel par ligne : 0.0833. Commentaire du registre : verdict avant papier - regime connu.

| Sous-bloc | Semaines | Net brut 100 % | Sharpe | Alpha annualisé | DD | Nom max | Mois max | Portes net, alpha, nom, mois, DD |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| total | 64 | +64.06% | 1.398 | +51.75% | -22.93% | 18.6% (AVNTUSDT) | 38.1% | True, True, True, True, True |

Spécification hors échantillon : décision « Décision conjointe Jonathan et Téo du 06/11/2026 : les 4 propositions du Cerveau sont adoptées et tranchées avant tout calcul hors échantillon. 1. Critère 0,2 R non applicable (décision D3 reconduite, le seuil de Sharpe 1,72 en tient lieu). 2. Glissement au stop de E20 fixé à 0,60 % (identique à E17). 3. Exposition brute prévue de 9,7 % (risque 0,25 % par ligne, porte de drawdown). 4. Lectures descriptives du § 19, décompositions par jambe et année, part du financement > 10 %/an et stress mode 1 des stops de E19 adoptées pour publication non éliminatoire. ».

## Portes du hors échantillon (fiche § 7), E19

| Porte | Résultat |
|---|---|
| sharpe_sup_seuil | ÉCHEC |
| ic90_bas_positif | ÉCHEC |
| alpha_btc_positif | franchie |
| drawdown_au_risque_prevu | franchie |
| semaines_avec_position | franchie |
| lignes | franchie |
| concentration_nom | franchie |
| concentration_mois | franchie |

Drawdown à brut 100 % : 22.93% ; au risque prévu (9.7% d'exposition brute) : 2.22%.
Sharpe 1.398 contre seuil 1.72. Reste la porte E20 > 0.

Lecture descriptive (non éliminatoire) : part des shorts payant plus de 10 %/an de financement 37.7% (2021-2025 : 15,5 % ; 2025 : 35,6 %).
