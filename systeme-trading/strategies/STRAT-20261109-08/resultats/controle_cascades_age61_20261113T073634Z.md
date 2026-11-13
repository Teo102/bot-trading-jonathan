# Contrôle sans rendement de STRAT-20261109-08, refiltré à l'âge minimal de 61 jours

Cascades détectées seulement : aucune issue de position lue. Base : X = 4 %, Y = 3 % (intérêt ouvert en contrats, daté à `create_time` + 5 minutes, valeurs nulles rejetées), entrée à t + 5 minutes, K = 5, départage par le volume sur 15 minutes.

Deux comptes : pause de 4 h après l'événement (borne haute) et de 8 h (tenue de 4 h puis pause de 4 h, borne basse). La règle des 2 stops par jour n'est pas comptée : elle demande une issue.

| Bloc | Cascades (pause 4 h) | Symboles | Par semaine | Part simultanées | Heures avec plus de 5 symboles | Jouables, pause 4 h (nominale) | Jouables, borne basse (8 h) | Exigence |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| developpement | 2126 | 189 | 19.6 | 73% | 56 | 881 | 857 | ≥ 300 sur la pause de 4 h : oui (borne basse : oui) |
| validation | 2034 | 314 | 24.8 | 59% | 37 | 1028 | 989 | — |
| hors_echantillon | 1229 | 249 | 18.7 | 26% | 13 | 997 | 930 | ≥ 100 sur la pause de 4 h : oui (borne basse : oui) |

Par année (pause 4 h) : 2021 153, 2022 853, 2023 1120, 2024 1465, 2025 1108, 2026 690.
Candidats au seuil le plus lâche (X 3 %, Y 2 %, avant pause) : 25512.

Le 10 et le 11/10/2025 : 89 cascades de base.

Refiltrage sans téléchargement de `candidats_20261113T002005Z.csv` : 29733 candidats au seuil lâche avant, 25512 après. Symboles sans volume : 0. Candidats écrits dans `candidats_age61_20261113T073634Z.csv`.
