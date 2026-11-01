# STRAT-DEX — Avenant 2, règle de décision écrite avant les résultats

Écrit le 01/11/2026 par le cerveau, en session avec Jonathan et Téo, **avant** la sortie de `resultats/cohorte_pilote.json` (calcul en cours sur le serveur, aucun résultat de persistance lu). Il précise le § 6 de la fiche sans changer le tirage, les filtres ni les seuils. Résultat de recherche, aucune recommandation.

## 1. Ce que le pilote peut et ne peut pas prouver

- **Aucun wallet n'est déclaré compétent à titre individuel.** Sur 70 wallets, quelques-uns seront positifs sur les deux périodes par simple hasard. Le contrôle compare donc le nombre observé de « survivants » au nombre attendu sous l'indépendance (`survivants_attendus_hasard`).
- **Puissance** (calcul du 01/11/2026, 2 000 tirages, Fisher unilatéral à 5 %, 40 % de wallets positifs en A) :

| Wallets dans le test | Persistance faible (B+ : 50 % si A+, 30 % si A−) | Moyenne (60 % / 25 %) | Forte (75 % / 20 %) |
|---:|---:|---:|---:|
| 30 | 18 % | 45 % | 85 % |
| 50 | 31 % | 72 % | 98 % |
| 80 | 46 % | 91 % | 100 % |

Un échec sur ce pilote ne prouve donc pas l'absence de compétence. Il prouve que ces données ne la montrent pas.

## 2. Règle de décision (codée dans `controles_robustesse.py`, tests 5 sur 5)

Période A : J−90 à J−46. Période B : J−45 à J. Wallets qui passent F1 à F3, avec au moins 3 positions dans chaque période.

| Verdict | Condition |
|---|---|
| `non_concluant_echantillon_insuffisant` | Moins de 30 wallets dans le test |
| `aucune_persistance_detectee` | Fisher unilatéral ≥ 0,05, ou Spearman ≤ 0, ou p de permutation du Spearman ≥ 0,05 |
| `persistance_fragile` | La base passe, mais au moins une variante de robustesse échoue |
| `persistance_soutenue` | La base et les trois variantes passent |

Variantes de robustesse, chacune déjà justifiée par un biais connu :
1. **Sans le jeton graine.** Un wallet entre au tirage parce qu'il a traité un pool chaud au moment du tirage. Cette position tombe en période B et la contamine.
2. **Positions soldées seules.** Le reliquat non vendu est valorisé au prix GeckoTerminal du jour. Il pèse surtout en B, d'où une asymétrie de mesure entre A et B.
3. **Sans la meilleure position de chaque wallet dans chaque période.** Les rendements memecoin sont dominés par quelques gains extrêmes.

Le test bilatéral déjà codé dans `analyse_cohorte.py` reste publié, sans valeur de décision.

## 3. Points à lire avant tout chiffre de gain

- Les 193 wallets écartés à plus de 1 000 signatures sont `hors_budget` et non des bots prouvés (fiche § 2). L'échantillon est donc biaisé vers les wallets peu actifs.
- Un wallet plafonné à 1 000 signatures peut n'avoir que sa période récente lue : sa période A est vide et il sort du test sans bruit.
- Le champ `sources` du rapport cite le RPC public alors que Helius a servi depuis l'avenant 1 [à corriger dans le rapport].
- Le tri T1 à T10 écartait l'idée sur T4 et T9 (fiche § 1). Le pilote ne continue que par exception écrite de Jonathan (journal du 01/11/2026).

## 4. Suite selon le verdict

| Verdict | Suite |
|---|---|
| `persistance_soutenue` | Phase 3 descriptive autorisée. Phase 4 seulement par une **nouvelle fiche** `validation-edge`, testée sur une nouvelle cohorte tirée après le 01/11/2026 et suivie en avant : aucun paramètre fixé et testé sur les mêmes wallets |
| `persistance_fragile` | Rapport descriptif seul. Aucune phase 4. Un second pilote n'est possible qu'avec un nouveau tirage plus grand, décidé par Jonathan |
| `aucune_persistance_detectee` ou `non_concluant_echantillon_insuffisant` | Approche par les wallets close (statut `rejetée` pour cette approche). Données conservées pour le taux de base : distribution des rendements de toutes les positions, coûts et part de jetons morts. Retour à l'étude par les tokens (`recherche/dex_faisabilite/`), lancée par Téo dans l'interface Dune. Priorité inchangée à STRAT-03 et STRAT-05 |

Dans tous les cas, `bot_simulation.py` ne tourne pas tant qu'aucune fiche de stratégie n'existe.
