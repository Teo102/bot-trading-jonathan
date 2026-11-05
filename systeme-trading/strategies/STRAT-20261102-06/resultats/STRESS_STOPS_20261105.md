# Rapport de Stress-Test d'Exécution des Stops (Condition CS3)

Date : 05/11/2026. Évaluation du glissement intra-horaire sur les 220 stops de la base continue (CDV).
Règle de gouvernance : CS3 exige que le rendement net et l'alpha à deux facteurs restent strictement positifs en Mode Midpoint.

## 1. Tableau Récapitulatif

| Mode | Net Total | Sharpe | Alpha 2-facteurs (t) | Max Drawdown | Glissement Moyen | Perte vs Base | Statut CS3 |
|:---|---:|---:|---:|---:|---:|---:|:---:|
| **Base (Modèle actuel)** | **+207.7 %** | **1.307** | +43.8 %/an (t=3.13) | -27.8 % | +0.00 % | -0.0 pts | FRANCHIE |
| **Stress 1 (Midpoint Mèche Mark)** | **+169.3 %** | **1.039** | +35.6 %/an (t=2.51) | -30.4 % | +1.56 % | -38.4 pts | FRANCHIE |
| **Stress 2 (Pire Mèche Mark)** | **+131.0 %** | **0.781** | +27.3 %/an (t=1.90) | -33.0 % | +3.13 % | -76.7 pts | FRANCHIE |
| **Stress 3 (Pire Mèche Contrat)** | **+120.6 %** | **0.715** | +25.1 %/an (t=1.72) | -33.7 % | +3.53 % | -87.1 pts | FRANCHIE |

## 2. Décomposition par Sous-bloc et par Année

| Mode | Dév Net (Sharpe) | Val Net (Sharpe) | 2021 | 2022 | 2023 | 2024 | 2025 |
|:---|:---:|:---:|---:|---:|---:|---:|---:|
| Base (Modèle actuel) | +94.2% (0.84) | +113.5% (2.55) | -2.2% | +9.0% | +53.9% | +84.9% | +62.0% |
| Stress 1 (Midpoint Mèche Mark) | +69.2% (0.60) | +100.2% (2.20) | -14.2% | +6.1% | +46.5% | +76.3% | +54.8% |
| Stress 2 (Pire Mèche Mark) | +44.1% (0.37) | +86.9% (1.86) | -26.3% | +3.1% | +39.1% | +67.6% | +47.5% |
| Stress 3 (Pire Mèche Contrat) | +37.0% (0.31) | +83.6% (1.77) | -28.7% | +2.0% | +36.1% | +66.0% | +45.3% |

## 3. Conclusion et Verdict de Gouvernance

- Le Mode 1 (Midpoint Mèche Mark) réalise **+169.3 %** net avec un Sharpe de **1.039** et un alpha de **+35.6 %/an** (t = 2.51).
- **La condition suspensive CS3 est donc FORMELLEMENT ET MATHÉMATIQUEMENT FRANCHIE.**
- Même dans le pire des cas théorique (Pire Mèche Contrat), le système reste net positif à **+120.6 %** et conserve un alpha de **+25.1 %/an** (t = 1.72).

Résultat de recherche, aucun ordre.
