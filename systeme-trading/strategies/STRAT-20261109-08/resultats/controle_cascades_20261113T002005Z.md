# Contrôle sans rendement de STRAT-20261109-08

Cascades détectées seulement : aucune issue de position lue. Base : X = 4 %, Y = 3 % (intérêt ouvert en contrats, daté à `create_time` + 5 minutes, valeurs nulles rejetées), entrée à t + 5 minutes, K = 5, départage par le volume sur 15 minutes.

Deux comptes : pause de 4 h après l'événement (borne haute) et de 8 h (tenue de 4 h puis pause de 4 h, borne basse). La règle des 2 stops par jour n'est pas comptée : elle demande une issue.

| Bloc | Cascades (pause 4 h) | Symboles | Par semaine | Part simultanées | Heures avec plus de 5 symboles | Jouables, borne haute | Jouables, borne basse | Exigence |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| developpement | 2277 | 209 | 20.9 | 72% | 58 | 952 | 923 | ≥ 300 : borne haute oui, borne basse oui |
| validation | 2434 | 352 | 29.7 | 54% | 37 | 1334 | 1277 | — |
| hors_echantillon | 1509 | 283 | 22.9 | 24% | 13 | 1249 | 1161 | ≥ 100 : borne haute oui, borne basse oui |

Par année (pause 4 h) : 2021 158, 2022 894, 2023 1225, 2024 1623, 2025 1571, 2026 749.
Candidats au seuil le plus lâche (X 3 %, Y 2 %, avant pause) : 29733.

Le 10 et le 11/10/2025 : 99 cascades de base.

Lignes d'intérêt ouvert : 68933535 présentes sur 69134688 attendues, soit 0.29% manquantes ou nulles. Le détecteur est aveugle à ces instants et 15 minutes après.

Symboles traités : 607 ; mois éligibles : 7905. Compact : `/root/strat08_compact`.
