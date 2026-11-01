# Journal de calibration Polymarket — mode d'emploi

Créé le 01/11/2026. Sert de porte à toute décision de capital sur Polymarket (décision de Jonathan et Téo du 01/11/2026 : monitoring en lecture, aucun capital avant la fin du mi-mandat). Résultat de recherche, aucun ordre, aucune recommandation. Ce document n'est pas un avis juridique.

Fichiers : `JOURNAL_CALIBRATION.csv` (une ligne par prévision), `score_calibration.py` (score), `test_score_calibration.py` (tests sur journaux synthétiques, 5 sur 5 au 01/11/2026).

## 1. Ce que le journal mesure

Une seule question : nos probabilités battent-elles le prix du marché, après l'écart achat-vente ? Il ne mesure ni la lecture des règles seule, ni le maker. Le simulateur du 01/11 (`resultats/20261101T091123Z_file_attente_rapport.md`) montre déjà qu'un maker passif perd une fois la file modélisée. L'edge restant à tester est donc l'information et la lecture des clauses.

## 2. Règles de saisie

1. **Une prévision s'écrit avant toute décision et ne se modifie jamais.** Une correction est une nouvelle ligne qui cite l'`id` remplacé dans `commentaire`. Chaque lot est commité le jour même : l'horodatage Git fait foi.
2. **Hors mi-mandat seulement.** `mi_mandat = oui` est exclu du score. Toute prévision sur un marché du scrutin du 03/11/2026 est inutile ici.
3. **Le prix du marché se relève à la même heure** que la prévision (`bid`, `ask`, `milieu`, `heure_lecture_prix_utc`), sur le jeton de l'issue évaluée (`issue_evaluee`, en général « Yes »).
4. **`proba_propre`** : la probabilité de l'issue évaluée, entre 0,01 et 0,99, avec sa base en une phrase (`base_de_la_proba`) et ses sources datées.
5. **Pas de tri après coup.** Toute prévision écrite compte, y compris celles qui coïncident avec le marché.
6. **Corrélation.** Une seule prévision par événement Gamma (`evenement`) et par semaine. Les tranches d'une même décision Fed comptent comme un seul événement. Le bootstrap se fait sur les événements, pas sur les lignes.
7. **Diversité d'horizon.** Viser au moins un tiers de marchés qui résolvent dans les 30 jours, sinon 100 prévisions prendront des mois à se résoudre.
8. **Grille UMA.** Reporter les notes F, S, L et le total du `REGISTRE_MARCHES_UMA.md` § 2. Un 3 en F, S ou L impose une relecture humaine avant saisie.
9. **Résolution.** `issue_resolue` vaut 1 ou 0, `annule` vaut oui pour un 50-50 ou une annulation, `litige` vaut oui si un statut « disputed » apparaît sur Gamma.

## 3. Colonnes

| Colonne | Contenu |
|---|---|
| `id` | `CAL-AAAAMMJJ-NN` |
| `auteur` | Jonathan, Téo ou Claude. Une prévision de Claude est notée comme telle et scorée à part si besoin |
| `condition_id`, `slug`, `question` | Identifiants Gamma |
| `categorie` | politique, macro, tech, sport, autre |
| `date_fin_gamma_utc`, `horizon_jours` | Fin affichée et écart avec la prévision |
| `note_F`, `note_S`, `note_L`, `note_totale_grille` | Grille du registre |
| `issue_resolue`, `horodatage_resolution_utc`, `litige`, `annule` | Remplis à la résolution |

## 4. Critères de lecture proposés — à figer par Jonathan avant la première prévision

**Constat de puissance, calculé le 01/11/2026 sur journaux synthétiques** (`test_score_calibration.py`, 100 à 200 tirages). Cas très favorable : notre erreur vaut 2 points, celle du marché 8 points, écart affiché de 1 cent.

| Prévisions résolues | Brier propre significativement meilleur | Gain par pari taker significativement positif |
|---:|---:|---:|
| 100 | 12 % des cas | 12 % des cas |
| 300 | 30 % | 57 % |
| 1 000 | 70 % | [non calculé] |

**Conséquence : 100 prévisions ne peuvent presque jamais prouver un edge**, même grand. Elles peuvent en revanche montrer qu'il n'y en a pas.

Proposition, non appliquée :

- **Porte 1, à 100 prévisions résolues sur au moins 30 événements.** Arrêt du projet si la différence de Brier est positive (nous faisons pire que le marché) ou si le gain moyen par pari taker est négatif. Sinon, poursuite jusqu'à 300.
- **Porte 2, à 300 prévisions résolues.** Borne basse de l'IC 95 % du gain par pari supérieure à 0, et différence de Brier négative. Seul ce résultat ouvre une fiche de stratégie `analyse-polymarket` avec capital papier.
- Aucune porte ne lève le verrou juridique de `REGISTRE_MARCHES_UMA.md` § 4.

## 5. Score

`python -B score_calibration.py` imprime : nombre retenu, Brier propre et marché, différence et IC 95 % par événement, perte logarithmique, paris pris, gain moyen par dollar et IC, table de calibration par tranches de 10 points.

Limites : le gain par pari suppose une exécution au meilleur prix affiché, sans profondeur ni frais (nuls sur la plupart des marchés au 31/10/2026, à relire marché par marché). Les journaux synthétiques ne disent rien de notre vraie précision.
