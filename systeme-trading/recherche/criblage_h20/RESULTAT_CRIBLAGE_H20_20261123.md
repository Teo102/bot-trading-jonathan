# Résultat du criblage de H20 (écart de financement Binance–Bybit), 23/11/2026

Règle figée le 23/11/2026 avant tout téléchargement (`REGLE_CRIBLAGE_H20.md`, commit 413e9ba), code et tests poussés avant le premier calcul (commit 0ddfff1). Exécution sur le serveur du 23/11/2026 à 09:02:50 UTC, durée 11 297 s (3 h 08). Sorties : `criblage_h20_20261123T090250Z.json`, `positions_h20_20261123T090250Z.csv`, `run_20261123T090250Z.log`. Résultat de recherche : aucun ordre, aucune recommandation d'investissement.

## Verdict des critères du § 5 : **H20 ÉCARTÉE**

| Critère | Seuil | Résultat | Rempli |
|---|---|---|---|
| 1. Blocs à au moins 5 % net par an | 4 sur 6 | **0 sur 6** | non |
| 2. Net positif sur chaque bloc hors la meilleure année (2021) | tous | **les 5 négatifs** | non |
| 3. Net annualisé hors la meilleure année | ≥ 3 % | **−5,7 %** | non |
| 4. Concentration (paire ≤ 30 %, mois ≤ 25 % du gain net) | — | sans objet, le gain net total est négatif | non |
| 5. Positions | ≥ 100 | 2 788 | oui |

## Par année (capital à levier 1, coûts preneur du verdict)

| Bloc | Financement brut | Coûts | Net annualisé | Version teneur de marché (information) | Positions ouvertes |
|---|---:|---:|---:|---:|---:|
| 2021 | +6,5 % | 7,2 % | **−0,8 %** | +4,6 % | 472 |
| 2022 | +3,7 % | 14,4 % | **−10,7 %** | +0,7 % | 766 |
| 2023 | +2,5 % | 5,7 % | **−3,2 %** | +1,2 % | 308 |
| 2024 | +2,8 % | 5,8 % | **−3,0 %** | +1,5 % | 311 |
| 2025 | +2,6 % | 7,5 % | **−4,9 %** | +1,1 % | 377 |
| 2026 (au 31/10) | +5,0 % | 10,8 % | **−6,9 %** | +3,3 % | 554 |
| Ensemble | | | **−4,9 % par an** (−28,4 % cumulés) | | 2 788 |

## Ce qui l'explique

- **L'écart se referme trop vite pour payer les frais.** Une position dure 5 fenêtres de 8 heures en médiane (environ 40 heures). Elle encaisse un financement brut médian de 0,035 % du notionnel, pour 0,41 % de coûts : le brut vaut moins d'un dixième des coûts. Seules 12 % des positions finissent nettes positives.
- **Même sans frais preneur, c'est trop peu.** La version teneur de marché (0,02 % par ordre, sans glissement, donc optimiste sur le remplissage) gagne entre +0,7 % et +4,6 % par an sur le capital. C'est moins qu'un placement sans risque, avec deux plateformes et un risque de liquidation par jambe en plus.
- **Le brut lui-même est faible**, de 2,5 à 6,5 % par an sur le capital, avant les coûts et avant l'écart de prix entre les deux perpétuels, que ce criblage ne compte pas. Comme le résultat est déjà une borne haute, la seconde étape (prix des deux plateformes) n'a pas d'objet.
- Les gains bruts les plus forts viennent d'alts ponctuellement en manie (PIPPIN, TRB, XTZ), comme pour H10 et H31.

## Limites déclarées

- L'univers est petit en 2021 (5 à 20 contrats communs aux deux plateformes depuis 60 jours au premier semestre), faute d'historique chez Bybit.
- Appariement exact des noms : les contrats nommés différemment sur les deux plateformes (par exemple les versions « 1000 ») sont perdus.
- Les données de 2026 incluent des perpétuels sur actions cotés sur les deux plateformes, conformément à la règle.
- Correction après le calcul, sans effet sur les résultats : l'affichage final du script plantait sur un booléen numpy (les fichiers étaient déjà écrits). La conversion en booléen Python a été ajoutée ; dans le JSON de cette exécution, certains critères s'écrivent « False » entre guillemets.

## Conclusion

H20 est écartée au criblage, comme H10 et H31. C'est le quatrième essai de la famille du portage de financement, et le quatrième échec. **Leçon proposée pour le registre** : sur les grandes paires, les écarts de financement entre plateformes ou entre comptant et perpétuel se referment en moins de deux jours et ne paient pas un aller-retour à quatre ordres. Une nouvelle idée de cette famille ne devrait passer le tri que si elle évite les frais d'entrée répétés (position longue tenue sans rotation, par exemple).
