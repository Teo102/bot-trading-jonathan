# Verdict de STRAT-20261102-05 après E01

Écrit le 02/11/2026 par le cerveau, d'après l'export de E01 (02/11/2026 08:58 UTC, commit `a092fc8`). Règles figées avant l'essai (commit `fb38f9f`, 08:14 UTC). Résultat de recherche, aucune recommandation.

**Verdict : `rejetée`.** Deux portes de la fiche § 6 échouent dès E01. E02 à E21 ne se lancent pas. Le hors échantillon reste fermé.

| Porte | Seuil | Mesure | Résultat |
|---|---|---|---|
| Rendement net, développement | > 0 | −23,50 % à brut 100 % sur 130 semaines | **Échec** |
| Prix seul, net de coûts | ≥ 0 | −66,18 % (prix −45,44 %, coûts −20,74 %) | **Échec** |
| Drawdown | < 50 % à brut 100 % | −75,48 %, du 27/06/2022 au 28/08/2023 | Échec |
| Années positives | ≥ 2 sur 3 | 2022 −44,8 %, 2023 −11,9 %, 2024 +33,2 % : 1 sur 3 | Échec |

Qualité des données vérifiée avant lecture : intérêt ouvert, 12 jours introuvables sur 4 177 ; 318 jours 1 d et 241 jours 1 h comblés, 5 introuvables chacun ; 14 semaines avec au moins un nom retiré par H1 (0,11 nom en moyenne). Les données n'expliquent pas l'échec.

## Lecture, sans valeur de décision

- **Le financement encaissé est réel, le prix l'efface.** Financement +42,7 %, prix −45,4 %, coûts −20,7 %.
- **Les deux jambes divergent.** Short des plus encombrés : prix +24,6 %, financement +6,3 %. Long des moins encombrés, à financement très négatif : prix −70,0 %, financement +36,4 %. Les actifs que les vendeurs à découvert paient cher pour shorter ont continué de baisser : ces vendeurs étaient plutôt informés que piégés.
- Bêta faible (+0,05), 49 % de semaines positives, 65 stops dont 42 sur la jambe courte.

## Ce que cette lecture n'autorise pas

La jambe courte seule paraît positive. C'est une observation faite **après** le résultat, sur le bloc de développement. Une stratégie « short des encombrés seul » serait une nouvelle stratégie, dont le développement et la validation seraient déjà vus. Elle serait aussi nette vendeuse du marché, ce qui change son risque. Elle ne se teste pas sur ces blocs.
