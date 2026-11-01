# Taille de l'univers de STRAT-20261031-03 par bloc — 20261101T122945Z

Volumes 1 d seulement (colonnes heure et volume USDT), aucun prix, aucun rendement. Aucun essai consommé. Symboles lus : 900. Exclusions et ancienneté de `config_strat03.json` (statut proposees).

| Bloc | Règle | Semaines | Médiane | Min | < 30 | < 12 | < 6 (vides) |
|---|---|---:|---:|---:|---:|---:|---:|
| developpement | sans_seuil | 182 | 30 | 30 | 0 | 0 | 0 |
| developpement | absolu_50M | 182 | 30 | 10 | 25 | 2 | 0 |
| developpement | relatif_20pct | 182 | 24 | 6 | 137 | 12 | 0 |
| developpement | indexe_marche | 182 | 30 | 17 | 20 | 0 | 0 |
| validation | sans_seuil | 56 | 30 | 30 | 0 | 0 | 0 |
| validation | absolu_50M | 56 | 30 | 30 | 0 | 0 | 0 |
| validation | relatif_20pct | 56 | 30 | 30 | 0 | 0 | 0 |
| validation | indexe_marche | 56 | 30 | 26 | 9 | 0 | 0 |
| hors_echantillon | sans_seuil | 64 | 30 | 0 | 3 | 3 | 3 |
| hors_echantillon | absolu_50M | 64 | 30 | 0 | 26 | 3 | 3 |
| hors_echantillon | relatif_20pct | 64 | 30 | 0 | 3 | 3 | 3 |
| hors_echantillon | indexe_marche | 64 | 25 | 0 | 52 | 3 | 3 |

| Bloc | Volume du 6e nom, min / médiane (M$) | 12e nom | 30e nom | Memecoins qui seraient dans le top 30, moyenne |
|---|---|---|---|---:|
| developpement | 93.4 / 409.7 | 31.7 / 215.6 | 4.7 / 79.2 | 2.04 |
| validation | 214.4 / 358.6 | 141.7 / 208.6 | 54.5 / 83.3 | 6.71 |
| hors_echantillon | 250.6 / 456.6 | 98.0 / 174.3 | 36.2 / 56.5 | 4.50 |

Lecture prévue avant le gel : si `absolu_50M` passe souvent sous 12 noms en développement, le signal 3 + 3 ne vise plus les mêmes extrêmes d'une semaine à l'autre. Le choix de la règle se fait sur ce tableau, avant E01, et le choix est consigné dans la fiche § 0.
