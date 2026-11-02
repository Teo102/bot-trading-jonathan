# Verdict des portes de STRAT-20261031-03 (E01 et E02)

Écrit le 02/11/2026 par le cerveau d'après les exports du 02/11/2026 (E01 00:53 UTC, E02 01:15 UTC, commit `e321e00`). Règles figées le 01/11/2026 (commit `37b947f`). Résultat de recherche, aucune recommandation.

**Verdict : `rejetée`.** La porte « sous-périodes » échoue. Une seule porte échouée suffit (fiche § 1.8). E03 à E27 ne se lancent pas. **E25 et E26 restent fermés** : le hors échantillon d'août 2025 à octobre 2026 n'est pas lu.

## Portes

| Porte (fiche § 1.8) | Seuil | Mesure | Résultat |
|---|---|---|---|
| Rendement net, développement (E01) | > 0 | +25,39 % cumulé à brut 100 % | Passe |
| Rendement net, validation (E02) | > 0 | +39,89 % | Passe |
| Sous-périodes | ≥ 3 années positives sur 2021 à 2024 | 2021 +55,3 %, 2022 −19,4 %, 2023 +44,2 %, 2024 −8,6 % (−54,7 % au 1er semestre, +46,1 % au 2nd) : **2 sur 4** | **Échec** |
| Voisins, coûts doublés, délistages | — | Non lancés après l'échec | — |

Qualité des données vérifiée avant lecture : 318 jours 1 d et 256 jours 1 h comblés par les journalières, 5 jours introuvables dans chaque cas, aucune exclusion H1, aucun repli du prix de marque.

## Ce que montrent les chiffres, sans valeur de décision

- **Le signal de prix ne paie pas ses coûts.** Sur E01 : prix +15,9 %, coûts −23,1 %, financement +32,6 %. Le gain net vient du financement encaissé, pas du momentum.
- **La jambe courte perd.** Prix : longs +89,2 %, shorts −73,3 %. Les pires résidus rebondissent souvent (squeezes).
- **Concentration extrême.** TRBUSDT porte 155 % du gain net et un seul mois 199 %. Le critère C8 (25 % et 40 %) aurait échoué.
- **Drawdown −68,4 %** à brut 100 %, creux le 03/06/2024. Le critère C5 (< 50 %) aurait échoué.
- Sharpe net 0,15 sur E01 et 1,07 sur E02, bêta proche de 0 (+0,03 et −0,03). Le Sharpe de E02 repose sur 56 semaines, un IC à 90 % qui contient zéro ([−0,29 % ; +1,81 %]) et un nom (REEFUSDT) à 60 % du gain.

## Conséquences

- Statut `rejetée`. Aucun papier, aucun réel.
- Le moteur, le chargeur et les tests restent valides et servent à STRAT-05.
- **Contamination déclarée pour STRAT-05.** L'observation « le financement porte le gain » vient des blocs 2021 à juillet 2025. Une stratégie fondée sur le financement testée sur ces mêmes blocs n'aurait plus de développement aveugle. Son verdict devra reposer sur le hors échantillon non lu (août 2025 à octobre 2026) et sur le papier en avant.
