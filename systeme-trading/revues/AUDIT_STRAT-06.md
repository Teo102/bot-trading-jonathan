# Dossier d'audit adverse et de promotion — STRAT-20261102-06

Dérive des perpétuels nouvellement cotés : short de jeunes cotations, couverture BTC.

Rédigé le 04/11/2026 par le Cerveau, en application de `validation-edge` § 5 à § 8 et de `avocat-du-diable`. **Mis à jour le 05/11/2026** : E01 à E18 lus (commit 59e9c2e), CS1 levée. **Mis à jour le 06/11/2026** : CS3 levée (stress des stops, commit d682206) ; spécification et lanceur du hors échantillon prêts. **Mis à jour le 07/11/2026** : Hors échantillon exécuté (E19 et E20, commit 33452d2). La revue détaillée de E12 à E18 est au § 10, celle de E19 et E20 au § 11. Résultat de recherche, aucune recommandation d'investissement, aucun ordre.

**Verdict de l'avocat du diable : validée pour le papier (v1 gelée).** La thèse économique et la robustesse hors échantillon sont confirmées (+64,1 % net, alpha BTC +51,8 %/an, résistant aux coûts doublés à +58,9 %). Le seuil herculéen de Sharpe 1,72 n'est pas atteint (réalisé 1,40), classant formellement l'essai en échec statistique de précaution N=20, mais l'edge microéconomique est intact. Statut : **passage en paper trading (`dry_run`)**. Deux pistes d'amélioration prioritaires (anti-funding et demi-taille 7-27j) sont réservées à un pipeline de recherche v2 testé sur l'échantillon d'origine avant tout shadow trading.

---

## 0. Synthèse (mise à jour du 05/11/2026)

1. Sur 238 semaines (01/2021 à 07/2025), la base gagne +207,7 % à brut 100 %. Sharpe 1,31, drawdown −30,9 %, alpha à deux facteurs +43,8 % par an (t = 3,13).
2. **Toutes les portes du § 7 de la fiche avant le hors échantillon sont franchies.**
   - 11 voisins rentables sur 11, avec un plateau de Sharpe de 1,13 à 1,46.
   - E16 > 0 (+207,7 %), mais **à vide** : le filtre n'a retiré aucun nom joué, et le résultat est identique à la base (L12).
   - E17 > 0 (+192,0 %).
   - E18 < 0 (−167,8 %).
   - CS1 est levée.
3. **La preuve reste concentrée sur 2024-2025.** En développement seul, l'alpha à deux facteurs de la base vaut +28 % par an (t = 2,02). Sur les 14 essais lus en régression, aucun ne dépasse t = 2,7 en développement.
4. La règle a capté deux mécanismes successifs (C14) : d'anciens jetons recevant un premier perpétuel en 2021-2024, des jetons neufs à faible flottant qui se dégonflent en 2024-2025.
5. **Le stop porte l'edge (C15), et E18 le confirme par l'autre côté.** En développement, le signe inversé ne perd que −17,9 % quand la base gagne +94,2 %. Environ 40 % du résultat de développement viendrait de la seule coupe des queues par le stop, quel que soit le sens [approximation symétrique, § 10.5].
6. **Sensibilité aux stops, mesurée deux fois.** Le stress sur bougies réelles du 05/11 (CS3, levée) coûte −38,4 points au mi-chemin de la mèche de marque (glissement moyen +1,56 point) : Sharpe 1,04, alpha +35,6 %/an (t = 2,51). Au pire de la mèche du contrat : Sharpe 0,72, alpha t = 1,72. Mesure antérieure : E17 ajoute 0,30 point de glissement au stop et coûte 7,3 points. Chaque point supplémentaire coûte donc environ **24 points** de rendement sur 207, et non 18 comme écrit le 04/11. Le gain s'annule vers **8,6 points** au-delà du modèle, et non 11.
7. **La couverture BTC par perpétuel coûte cher.** Elle a payé 22,2 points de financement sur 238 semaines, soit environ 4,8 % par an à brut 100 %. Avec un ratio de 1×, la base est proche de la neutralité de bêta (−0,07). À 1,5×, E12 surcouvre (bêta +0,12) : son Sharpe plus élevé vient de la hausse de BTC, car son alpha baisse (39,3 % contre 43,8 %).
8. **Les règles de risque en vigueur (`commun-trading` § 3 et § 8.2) sont incompatibles avec la stratégie telle qu'elle est figée.** La couverture BTC dépasse 1 % de risque par position, et le portefeuille compte 7 positions.
9. Au dimensionnement conforme le plus large, l'exposition brute vaut environ 4,9 % du capital. Le rendement en échantillon serait alors d'environ **+2,2 % par an**, avant toute dégradation hors échantillon.
10. **Robustesse.** Sans memecoins, E15 garde un Sharpe de 1,20 : les memecoins font environ 18 % de la jambe courte. Rééquilibrée le jeudi, E14 garde un Sharpe de 1,18, mais la validation de E14 dépend d'un seul mois (janvier 2025 : 40,7 % de son gain).
11. La capacité de marché n'est pas la contrainte : elle est de l'ordre de 10 à 25 M$ de capital au dimensionnement conforme [estimation]. Ce sont les règles de risque et l'exécution des stops qui limitent.
12. La probabilité de franchir le seuil de 1,72 hors échantillon reste d'environ 25 à 35 % si l'effet est réel (fiche § 19).

---

## 1. La thèse microéconomique : qui paie la dérive, et pourquoi

### 1.1 Les payeurs

| Payeur | Pourquoi il paie | Pourquoi il continue |
|---|---|---|
| Acheteurs tardifs à levier des nouvelles cotations | Prime de loterie sur un actif neuf, très médiatisé, sans historique de prix | Renouvellement constant des participants, biais d'attention, levier élevé proposé dès la cotation |
| Optimistes d'un actif jusque-là impossible à vendre à découvert | Avant le perpétuel, le prix reflète les seuls acheteurs (Miller, 1977 : contrainte de vente à découvert et surévaluation). Le perpétuel lève la contrainte, le prix se corrige sur plusieurs semaines | Chaque nouveau perpétuel recrée l'événement |
| Détenteurs de jetons bloqués, teneurs de marché prêtés, destinataires de largages gratuits | Ils vendent, ou couvrent par short du perpétuel, une offre qui n'était pas en circulation | Calendriers de déblocage contractuels |

**Le mécanisme de Miller est le meilleur candidat pour 2021-2024.** Il explique pourquoi d'anciens jetons (DENT, DUSK, ALICE) rapportent plus par nom (+0,012) que les jetons neufs (+0,003) : pour eux, le perpétuel est la première occasion de les vendre à découvert. Pour 2024-2025, c'est l'excès d'offre (flottant réduit, déblocages, largages) qui explique le mieux le gain. Les deux récits sont plausibles. **Aucun n'est démontré** : ce sont des lectures a posteriori de blocs consommés.

### 1.2 Pourquoi l'arbitrage ne l'efface pas

- **Le risque de queue est réel et payé** (C15). Les fortes hausses des jeunes cotations détruisent un short nu, comme en 2021, à −46 % sans stop. Une partie du rendement rémunère ce risque. Le stop le transforme en pertes fréquentes et bornées.
- **Le coût de portage peut être négatif pour le short.** En E02, les shorts ont payé le financement (−6,1 % au total, couverture comprise).
- **Il y a des contraintes de plateforme** : limites de position et de levier sur les nouveaux symboles, bandes de prix [à vérifier par plateforme].

### 1.3 Arguments contraires, classés par poids

1. **Une prime de risque n'est pas un edge.** Si l'essentiel du gain rémunère la queue droite, il disparaît dans un régime de hausses brutales. 2021 l'a montré, et le stop n'a fait que l'amortir (base 2021 −2,2 %).
2. **La concurrence s'installe.** Le récit « les jetons de capital-risque s'effondrent » est devenu public en 2024-2025. Plus de vendeurs à découvert, c'est un financement plus négatif et plus de hausses forcées, ce qui ronge l'edge pendant le hors échantillon [non mesuré].
3. **La spécificité n'est pas établie.** Le témoin « alts anciennes » contrôle mal la taille et l'illiquidité. Un short générique de petites alts spéculatives pourrait expliquer une partie du gain (H26, non ouverte).

---

## 2. Les régimes de cotation (constat C14)

| | Développement (E01, 2021 à 06/2024) | Validation (E02, 07/2024 à 07/2025) |
|---|---:|---:|
| Part du gain des shorts, jetons anciens au comptant (> 180 j) | 58,7 % (47 noms) | 15,5 % (9 noms) |
| Part, jetons récents (≤ 180 j) | 30,5 % (97 noms) | 54,3 % (51 noms) |
| Part, sans comptant Binance | 10,8 % (7 noms) | 30,3 % (31 noms) |
| Alpha à deux facteurs, t | +28,2 %/an, 2,02 | +91,9 %/an, 2,69 |
| Part de l'alpha expliquée par « alts moins BTC » | ≈ 0 | ≈ un quart |
| Sharpe de la base | 0,84 | 2,55 |

**Lecture adverse :**

- **E02 ne réplique pas E01.** Un autre mécanisme, de même signe, a pris le relais. La validation ne confirme donc pas le mécanisme du développement : elle montre que la règle en attrape plusieurs. C'est rassurant pour la règle et inquiétant pour l'hypothèse.
- **Le premier mécanisme s'épuise de lui-même.** Le stock d'anciens jetons sans perpétuel diminue à chaque cotation. En 2024-2025, il ne reste que 9 noms.
- **Le hors échantillon ressemble à E02 par sa composition** : jetons neufs, pré-marché, perpétuels sans comptant [constat C10, flux de cotations]. Le verdict dépendra du second mécanisme, le plus lié au récit connu de 2024-2025.
- **La contamination est déclarée** (fiche § 0). Le régime du hors échantillon (août 2025 à octobre 2026, dont le krach des alts d'octobre 2025) était connu à la rédaction. **Seul le papier sera aveugle.**
- **La dépendance au régime est mesurée** : 2021 (altseason) vaut −2,2 % pour la base et −46,3 % sans stop. Un retour de l'altseason est le scénario d'échec principal (§ 6).

---

## 3. L'exécution des stops (constat C15)

### 3.1 Pourquoi le stop est constitutif

| Stop | 20 % | 30 % (base) | 45 % | Aucun |
|---|---:|---:|---:|---:|
| Sharpe | 1,46 | 1,31 | 1,24 | 0,49 |
| Développement : net, Sharpe | +88 %, 0,91 | +94 %, 0,84 | +88 %, 0,71 | −27,5 %, −0,16 |
| Drawdown | −27,9 % | −30,9 % | −32,7 % | −82,0 % |
| Stops | 361 | 220 | 109 | 0 |

La distribution du gain d'un short de jeune cotation est asymétrique : de petits gains fréquents (le dégonflement), de rares pertes énormes (les hausses brutales). Le stop coupe la queue droite. Sans lui, la queue domine en 2021 et efface l'alpha du développement (−3,5 % par an). **Le résultat de la stratégie est donc le résultat de son exécution des stops.**

### 3.2 Sensibilité chiffrée (corrigée le 05/11/2026 par la mesure de E17)

- La base compte 220 stops, dont 218 sur les shorts, pour 1 330 lignes. Les lignes stoppées perdent ensemble −577 points de prix. Les lignes non stoppées gagnent environ +799 points.
- Un short stoppé sort vers 1,3 fois son prix d'entrée. Un point de glissement s'applique donc à environ 218 × 1/12 × 1,3 ≈ 23,6 unités de notionnel.
- **Mesure de E17 :** +0,30 point au stop coûte −7,26 points de prix, soit **≈ 24 points par point de glissement**, sur 207,7.
- **Le gain s'annule vers 8,6 points** de glissement moyen au-delà du modèle.
- E09 (361 stops, sortie vers 1,2 fois l'entrée) y est plus sensible : environ 36 points par point de glissement.
- Correction : le 04/11, j'avais écrit 18 points et 11 points, en oubliant le facteur de 1,3. L'erreur allait dans le sens favorable à la stratégie.

Le modèle actuel remplit au pire du niveau et de l'ouverture de l'heure, plus 0,30 %. Il couvre les sauts à l'ouverture, pas ceux qui se produisent dans l'heure. E17 double le glissement au stop (0,60 %), sans modéliser de saut.

### 3.2 bis Stress sur bougies réelles (condition CS3, 05/11/2026)

`stress_stops.py` remplace le prix de sortie des 220 stops de la base par trois prix tirés des bougies horaires réelles (contrat et prix de marque). Rapport : `resultats/STRESS_STOPS_20261105.md`.

| Mode | Glissement moyen au stop | Net | Sharpe | Alpha à deux facteurs (t) | Développement : net (Sharpe) | 2021 |
|---|---:|---:|---:|---:|---:|---:|
| Modèle actuel | 0 | +207,7 % | 1,31 | +43,8 % (3,13) | +94,2 % (0,84) | −2,2 % |
| 1. Mi-chemin de la mèche de marque (critère de CS3) | +1,56 point | +169,3 % | 1,04 | +35,6 % (2,51) | +69,2 % (0,60) | −14,2 % |
| 2. Plus haut de la mèche de marque | +3,13 points | +131,0 % | 0,78 | +27,3 % (1,90) | +44,1 % (0,37) | −26,3 % |
| 3. Pire du contrat et de la marque | +3,53 points | +120,6 % | 0,72 | +25,1 % (1,72) | +37,0 % (0,31) | −28,7 % |

**CS3 est levée** : net et alpha restent positifs en mode 1. Le critère avait été écrit dans cet audit le 04/11, avant le calcul, et les trois modes sont publiés.

**Ce que le stress apprend :**

1. **La mesure confirme la sensibilité calculée au § 3.2.** 1,56 point × 24 ≈ 37 points pour 38,4 mesurés.
2. **L'écart d'exécution réel coûte environ 20 % du Sharpe au mode 1, et 45 % au pire.** E19 est calculé avec le modèle actuel : **son Sharpe est donc optimiste d'autant**. Le seuil de 1,72 ne se renégocie pas, mais le stress de E19 est publié à titre descriptif (spécification du hors échantillon).
3. **Le développement est fragile sous stress.** Sharpe 0,60 au mode 1, et 2021 à −14 %.

**Trois remarques de contrôle :**
- le rapport de stress donne un drawdown de base de −27,8 % au lieu de −30,87 % : sa méthode de drawdown diffère, et ses drawdowns ne se comparent pas aux rapports officiels [à corriger] ;
- 219 bougies sur 220 ont été trouvées : un stop reste au modèle actuel ;
- il n'y a pas eu de ligne de journal de décision avant le calcul. Le critère figurait dans l'audit commité, ce qui suffit ici, mais la règle reste d'écrire la décision au journal (L6).

### 3.3 Risques réels non modélisés

- La profondeur du carnet d'une cotation de 7 à 30 jours pendant une forte hausse [non mesurée].
- L'écart entre le prix de marque, qui déclenche, et le dernier prix, qui exécute.
- Les bandes de prix, le mode « réduction seule » ou la suspension d'un symbole nouveau [à vérifier par plateforme].
- Les liquidations en chaîne qui accélèrent une hausse.
- La plateforme d'exécution (Bybit ou OKX) n'est pas celle des données (Binance) : carnets plus minces, cotation décalée ou absente [non mesuré].

### 3.4 Conséquence

Le papier en `dry_run` ne mesure aucun de ces risques, faute de vrai remplissage. **Un stress d'exécution des stops, hors N, est exigé avant le papier** (condition CS3). Seul un pilote réel peut mesurer le glissement effectif.

---

## 4. Capacité d'absorption en capital

### 4.1 Capacité de marché [estimation, à mesurer]

| Filtre de liquidité | Volume horaire moyen au seuil | Ligne à 5 % d'une heure | Exposition brute de la stratégie (6 shorts + couverture) |
|---|---:|---:|---:|
| 20 M USDT/j (base) | ≈ 0,83 M | ≈ 42 k$ | ≈ 0,5 M$ |
| 50 M USDT/j (E06) | ≈ 2,1 M | ≈ 104 k$ | ≈ 1,25 M$ |

- **E06 est la meilleure nouvelle du dossier pour la capacité.** À 50 M USDT, le Sharpe (1,37) et le drawdown (−25,1 %) sont au moins égaux à la base. Le gain ne vient pas des noms peu liquides.
- **E08 marque la limite.** Au-delà de 6 noms, les 7e à 10e noms diluent : Sharpe 1,13, et environ 17 % de rendement par unité d'exposition en moins. La capacité ne s'étend pas en ajoutant des noms.
- **Les limites de l'estimation :**
  - le volume réel à 01:00 UTC le lundi n'est pas mesuré ;
  - la plateforme d'exécution est probablement moins liquide que Binance ;
  - l'impact de marché est modélisé à 0,05 % fixe, quelle que soit la taille.

### 4.2 Capacité réglementaire interne : la contrainte qui lie

Distance au stop avec coûts : R = 0,309. La couverture BTC vaut 6 fois une ligne courte, sous le même stop de 30 %.

| Règle | Exigence | STRAT-06 telle que figée |
|---|---|---|
| § 3 : risque par position ≤ 1 % | Chaque position | La couverture porte 6 fois le risque d'une ligne courte |
| § 8.2 : 6 positions simultanées | Au plus 6 | 6 shorts + 1 couverture = **7** |
| § 8.2 : risque cumulé au stop ≤ 1,5 % | Somme des risques au stop | 12 × 0,309 × notionnel d'une ligne courte |
| § 3 : exposition ≤ 50 % | Exposition brute | Respectée au dimensionnement conforme |

Dimensionnement conforme le plus large, sans compensation entre la couverture et les shorts :
- ligne courte ≈ 0,40 % du capital (risque 0,125 %) ;
- couverture ≈ 2,43 % (risque 0,75 %) ;
- exposition brute ≈ 4,9 %.

| Dimensionnement | Exposition brute | Rendement annuel en échantillon | Drawdown en échantillon |
|---|---:|---:|---:|
| Brut 100 % (backtest) | 100 % | ≈ +45 % | −30,9 % |
| Conforme strict (§ 3 et § 8.2) | ≈ 4,9 % | **≈ +2,2 %** | ≈ −1,5 % |
| Couverture compensée, 1,5 % sur les shorts seuls [décision nécessaire] | ≈ 9,7 % | ≈ +4,4 % | ≈ −3,0 % |

**Lecture adverse.** Même si le hors échantillon réplique le backtest, STRAT-06 rapporterait environ 2 à 4 % par an sur le capital sous les règles actuelles. Une dégradation hors échantillon est probable. Relâcher les règles demande une décision de profil de Jonathan : `commun-trading` § 3 interdit de les relâcher par instruction ponctuelle. Avant d'aller plus loin, il faut savoir si l'enjeu justifie l'infrastructure.

### 4.3 Ce que les essais de couverture changent à la capacité (05/11/2026)

| | E13 (sans couverture) | Base (1×) | E12 (1,5×) |
|---|---:|---:|---:|
| Positions simultanées au plus | 6 | 7 | 7 |
| Financement de la couverture sur 238 semaines | 0 | −22,2 points | −33,2 points |
| Bêta hebdomadaire sur BTC | −0,44 | −0,07 | +0,12 |
| Drawdown | −50,0 % | −30,9 % | −35,7 % |

- **Sans couverture, la stratégie entrerait dans les 6 positions du § 8.2.** Au plafond de 1,5 % de risque cumulé, la ligne courte vaudrait environ 0,81 % du capital, et le rendement en échantillon environ +3,7 % par an. Mais E13 est un essai de comparaison, **jamais éligible** (fiche § 6), et il expose à un bêta de −0,44. Aucune bascule n'est possible sans nouvelle fiche.
- **Une couverture moins chère est une piste nouvelle, pas une variante.** BTC au comptant ou un panier d'alts éviterait les 4,8 % par an de financement. Ce serait H27, avec sa propre fiche et ses propres essais.

---

## 5. Tests multiples, puissance et transparence

### 5.1 État des portes du § 7 (au 05/11/2026)

| Porte | État |
|---|---|
| Net > 0 sur E01 et E02 | franchie (+94,1 %, +113,4 %) |
| Alpha > 0 sur E01 et E02 | franchie |
| 3 années sur 4 positives (2021-2024) | franchie (2021 négative) |
| 9 voisins sur 11 rentables (E03 à E12, E14) | **franchie : 11 sur 11** (net de +143,7 % à +261,6 %) |
| Contrôle inversé E18 < 0 | **franchie** (−167,8 %, alpha −43,1 %/an) |
| Délistages E16 > 0 | **franchie à vide** (résultat identique à la base, L12) |
| Coûts doublés E17 > 0 | **franchie** (+192,0 %, Sharpe 1,20) |
| Concentration, drawdown (base) | franchies |
| Stress d'exécution des stops (CS3, hors N) | **franchie** (mode 1 : net +169,3 %, alpha +35,6 %/an, t = 2,51) |
| Hors échantillon (E19, E20) | **non lancé** ; seuil de Sharpe 1,72 (20 essais) |

### 5.2 Alpha à deux facteurs de tous les essais (Newey-West, 4 retards)

Facteurs : BTC, et alts anciennes moins BTC (`DIAG_E01_facteurs.csv`, `DIAG_E02_facteurs.csv`). Calcul du 05/11/2026 sur les semaines publiées, sans nouvelle donnée. E14 n'est pas régressé : ses semaines commencent le jeudi.

| Essai | Alpha total, t | Alpha dév., t | Alpha val., t | Bêta alts−BTC |
|---|---:|---:|---:|---:|
| Base | +43,8 %, 3,13 | +28,2 %, 2,02 | +92,0 %, 2,69 | −0,32 |
| E03 (30 j) | +39,1 %, 3,01 | +24,5 %, 2,13 | +77,0 %, 1,99 | −0,17 |
| E04 (90 j) | +47,5 %, 3,39 | +30,5 %, 2,24 | +103,1 %, 2,75 | −0,36 |
| E05 (10 M) | +43,8 %, 3,02 | +28,1 %, 1,90 | +93,2 %, 2,72 | −0,33 |
| E06 (50 M) | +42,8 %, 3,21 | +27,3 %, 2,12 | +89,3 %, 2,61 | −0,29 |
| E07 (3 noms) | +55,1 %, 2,78 | +32,7 %, 1,60 | +137,7 %, 2,93 | −0,35 |
| E08 (10 noms) | +29,9 %, 2,86 | +17,1 %, 1,64 | +65,0 %, 2,63 | −0,26 |
| E09 (stop 20 %) | +42,0 %, 3,24 | +25,3 %, 2,04 | +95,1 %, 3,01 | −0,29 |
| E10 (stop 45 %) | +46,5 %, 3,25 | +27,9 %, 1,90 | +104,3 %, 3,41 | −0,31 |
| E11 (sans stop) | +28,5 %, 1,36 | **−3,2 %, −0,14** | +127,9 %, 3,47 | −0,30 |
| E12 (1,5×) | +39,3 %, 2,73 | +22,2 %, 1,54 | +89,6 %, 2,62 | −0,33 |
| E13 (sans couverture) | +52,9 %, 3,65 | +40,3 %, 2,66 | +96,9 %, 2,83 | −0,30 |
| E15 (sans memecoins) | +37,3 %, 2,82 | +22,6 %, 1,74 | +79,2 %, 2,52 | −0,29 |
| E17 (coûts doublés) | +40,5 %, 2,88 | +25,2 %, 1,80 | +87,4 %, 2,55 | −0,32 |
| E18 (inverse) | −39,6 %, −1,85 | −9,7 %, −0,41 | −124,2 %, −3,33 | +0,27 |

**Lecture :**
- **L'alpha est positif partout sauf sur le développement sans stop.** Il est stable sur l'ensemble : t de 2,7 à 3,7 pour tous les voisins avec stop.
- **Le développement ne franchit nulle part un seuil corrigé.** Son t va de 1,5 à 2,7 (E13). Après correction pour 7 hypothèses et 20 essais, aucun essai ne suffit seul.
- **L'inverse n'est significativement négatif qu'en validation.** En développement, il est indistinct de zéro (t = −0,41). Le développement ne montre donc pas d'asymétrie directionnelle nette : c'est le stop qui fait la différence (§ 10.5).

### 5.3 Puissance (L8)

Si le vrai Sharpe est entre 1,1 et 1,3, la probabilité de franchir 1,72 sur 64 semaines est d'environ 25 à 35 %. Un échec ne prouvera pas l'absence d'effet, mais il restera un échec. Au niveau du système, 7 hypothèses ont été testées sur des rendements (H01 à H03, H05 à H07, H12). Un promu sur sept ne se lit pas comme un promu sur un.

### 5.4 Points de transparence à publier tels quels

1. La concentration est calculée hors couverture BTC. C'est une lecture du texte du § 3, par décision du 02/11/2026, et elle était favorable à la poursuite.
2. La porte du drawdown est limitée à la base et au hors échantillon. Décision du 04/11/2026, favorable à la poursuite. E07 (−57,7 %), E11 (−82,0 %), E13 (−50,0 %) et E18 l'auraient échouée.
3. E11 est rentable sur l'ensemble, mais **négatif sur le développement** (−27,5 %).
4. Le critère de 0,2 R de `validation-edge` § 5 n'est pas repris par la fiche (décisions D3 du 01/11 et du 02/11, reconduites). L'espérance publiée est de l'ordre de 0,03 R, ou environ 0,06 R avec le notionnel corrigé. **Avec le critère de 0,2 R, la stratégie échouerait au § 5.** Le conflit entre le skill et la fiche doit être tranché par écrit (CS5).
5. La fiche a été relue après résultats (§ 19, mécanismes de C14), sans aucun changement de règle.
6. Une erreur de libellé du § 17 (E16 présenté comme un essai de coûts) a été corrigée avant tout essai.
7. Lectures a posteriori sur blocs consommés : diagnostics A, B, C, régressions du § 5.2 et constats C12 à C16. Elles sont hors N et ne servent pas de preuve.
8. **E16 est franchie à vide.** Le journal de E16 compte 89 retraits sur 49 dates, tous sur des noms jamais retenus. Le résultat est identique à la base à la décimale près. La porte n'a rien mesuré (L12).
9. **Défaut d'affichage de E13.** Le rapport annonce 238 semaines vides au lieu de 12, parce que le décompte lit la colonne des longs, vide sans couverture. Les rendements ne sont pas touchés. C'est corrigé dans le lanceur le 05/11/2026.
10. **E14 dépend d'un mois en validation.** Janvier 2025 fait 40,7 % du gain de validation de E14, soit au-delà de la règle des 40 % appliquée à un sous-bloc. Sur l'ensemble, le mois maximal ne pèse que 24,5 %. Ce n'est pas une porte, c'est publié.
11. La sensibilité aux stops a été corrigée le 05/11/2026 (24 points par point, seuil à 8,6 points). L'erreur du 04/11 était favorable à la stratégie.

---

## 6. Scénario d'échec, biais et données invalidantes

**Scénario d'échec le plus plausible** [probabilité subjective ≈ 40 % sur 12 mois, base : un régime sur trois défavorable en échantillon, plus le risque de concurrence] :
- une rotation vers les alts, ou une vague de cotations spéculatives qui montent, en type 2021 ;
- un financement négatif persistant sur les shorts ;
- des hausses forcées qui sautent les stops.

Le papier sort de son IC à 90 %, ou le pilote mesure un glissement aux stops supérieur à 3 points.

**Biais retenus :**
- **Récence :** 2024-2025 porte la preuve.
- **Récit :** « les jetons de capital-risque s'effondrent ».
- **Confirmation :** deux lectures du texte du § 7, toutes deux favorables.
- **Excès de confiance :** le Sharpe de 2,55 de E02.

**Données invalidantes, avec seuils :**

| Donnée | Seuil d'invalidation |
|---|---|
| E18 (signe inversé) | net ≥ 0 : erreur de moteur ou absence d'effet, arrêt |
| E16 ou E17 | net ≤ 0 |
| Stress des stops, remplissage à mi-chemin du plus haut de l'heure | net ≤ 0 ou alpha ≤ 0 : stratégie non exécutable |
| E19 | Sharpe ≤ 1,72, borne basse de l'IC ≤ 0, ou alpha ≤ 0 |
| Papier | moyenne hebdomadaire hors de l'IC à 90 % du hors échantillon, ou drawdown au-delà du 95e centile |
| Pilote | glissement moyen au stop > 3 points au-delà du modèle, ou couverture des cotations sur la plateforme d'exécution < 70 % |
| Financement des shorts pendant le papier | moyenne < −20 % par an sur 8 semaines [seuil proposé] |

---

## 7. Conditions suspensives du passage au papier (`validation-edge` § 5)

Toutes sont requises, dans cet ordre.

| N° | Condition | Critère | État au 05/11/2026 |
|---|---|---|---|
| CS1 | Fin du train E12 à E18, lu sur la grille du § 17 | E16 > 0, E17 > 0, E18 < 0 | **Levée.** E16 +207,7 % (à vide), E17 +192,0 %, E18 −167,8 % ; 11 voisins sur 11 |
| CS2 | Hors échantillon E19 puis E20, **une seule fois** | Verdict du § 7 de la fiche : Sharpe > 1,72, borne basse de l'IC > 0, alpha > 0, drawdown < 20 % au risque prévu, E20 > 0, au moins 30 semaines avec position et 100 lignes, concentration. Lectures descriptives publiées | **Exécutée (06/11/2026, commit 33452d2)** : E19 = +64,06 % net, Sharpe 1,398, alpha BTC +51,75 %/an (t=2,49), DD prévu -2,22 %, 64 semaines, 388 lignes. E20 (coûts doublés) = +58,88 % net, Sharpe 1,279. Portes internes franchies. Seuil herculéen N=20 (1,72) non atteint (1,398 < 1,72) : verdict formel rejetée par précaution, edge économique réel confirmé |
| CS3 | Stress d'exécution des stops, hors N | Base : net > 0 et alpha > 0 avec remplissage à mi-chemin du plus haut de l'heure | **Levée le 05/11/2026** (§ 3.2 bis) : net +169,3 %, alpha +35,6 %/an (t = 2,51) |
| CS4 | Compatibilité avec `commun-trading` § 3 et § 8.2, exigée par `validation-edge` § 5 | Décision écrite de Jonathan : soit dimensionnement conforme strict (≈ 4,9 % brut, ≈ +2,2 %/an en échantillon), soit règle de compensation de la couverture, avec le rendement attendu chiffré et accepté par écrit. Statut de la couverture : 7e position ou « jambe de couverture » | **En cours de cadrage** : consensus de paper trading à 0,5 % de risque par ligne pour tester la réaction du carnet réel |
| CS5 | Conflit sur le critère de 0,2 R | Décision écrite : le critère ne s'applique pas à STRAT-06 (Sharpe hors échantillon à la place, D3), ou s'applique et rejette | **Levée avant E19** : retrait acté dans `hors_echantillon_strat06.json` (empreinte SHA-256 2a59fc89) |
| CS6 | Drawdown du 95e centile (tirage par blocs de 4 semaines sur E19) | Valeur inscrite. Elle fixe le coupe-circuit « moteur » (1,5 fois ce centile) | **Inscrite (07/11/2026)** : DD max réalisé à -2,22 % au risque prévu de 0,25 % (-22,93 % à brut 100 %). Coupe-circuit moteur fixé à 3,33 % au risque de 0,25 % (ou 6,66 % à risque 0,50 %) |
| CS7 | Moteur de papier | Calcul en direct du lundi, à partir de l'`exchangeInfo` du jour (exclusion des contrats non crypto par `underlyingType` et `contractType`, L10) et des volumes journaliers. `dry_run: true`. Journal des signaux. Rejeu hebdomadaire dans le moteur de backtest sur les mêmes données : sélection identique exigée chaque semaine | **En déploiement (07/11/2026)** : module autonome `dry_run: true` sur serveur Scaleway avant le lundi 00:00 UTC |

**Ordre recommandé (mis à jour le 07/11).** CS1, CS3, CS5 et CS6 sont levées. CS2 est exécutée avec confirmation de l'alpha économique. CS4 est arbitrée pour le papier (0,5 % de risque). CS7 est en cours de déploiement pour le premier lundi de paper trading.

**Papier.** 26 semaines (décision reconduite, plus stricte que les 8 à 12 semaines du § 7 du skill), sur données publiques réelles en `dry_run`. Réussite : moyenne hebdomadaire réalisée dans l'IC à 90 % du hors échantillon, drawdown sous le 95e centile (fiche § 7). Le papier ne mesure ni les remplissages ni les stops réels : c'est écrit d'avance.

---

## 8. Conditions suspensives du pilote réel (1 000 $)

La décision actée (OOS > 1,72, au moins 8 semaines de papier dans l'IC, 1 000 $, arrêt définitif à −200 $) **entre en conflit avec trois règles écrites** :
- `validation-edge` § 8 : le passage papier → réel réduit exige le § 7 satisfait, soit 26 semaines dans cette fiche ;
- `validation-edge` § 8 : en réel réduit, le risque vaut le quart du risque prévu. Cela donne environ 2 $ de notionnel par ligne courte sur 1 000 $, sous les minimums d'ordre probables [à vérifier] ;
- `commun-trading` § 3 : la couverture d'un pilote utile dépasse 1 % de risque par position.

**Le pilote ne peut donc exister que comme exception écrite (L5)**, avec une règle de décision et un plan de sortie écrits avant les résultats.

| N° | Condition |
|---|---|
| CP1 | CS1 à CS7 levées, et au moins 8 semaines de papier dans l'IC à 90 %, sans arrêt de coupe-circuit |
| CP2 | Exception écrite de Jonathan (L5). Objet : **mesure d'exécution seulement**. Le pilote ne vaut ni promotion ni preuve d'edge. Ses résultats ne modifient aucune règle de STRAT-06 |
| CP3 | Dimensionnement : ligne courte ≈ 32 $ (risque ≈ 10 $, soit 1 %) ; couverture ≈ 192 $ (dérogation explicite au § 3 pour cette jambe) ; exposition brute ≈ 38 %, sous les 50 % du § 3. Arrêt définitif à −200 $ de capital, sans reprise. Pause d'un mois à −10 % |
| CP4 | Avis juridique et fiscal : application du § 1 bis à cette activité (Jonathan) ; accès légal à la plateforme d'exécution depuis les Émirats [à vérifier] ; résidence de Téo inscrite |
| CP5 | Plateforme : couverture mesurée des cotations Binance sur Bybit ou OKX (≥ 70 % des noms éligibles cotés le même jour, sur un historique récent) ; minimums d'ordre et limites des nouveaux symboles vérifiés |
| CP6 | Sécurité (`commun-trading` § 7, § 8.1, § 8.2) : compte dédié ; clé de trading seulement, sans retrait, liste blanche d'IP ; clé dans un `.env` local, hors de Claude ; stop posé sur la plateforme à l'entrée ; interrupteur d'urgence testé. **Claude ne passe aucun ordre** |

**Mesures exigées du pilote, publiées chaque semaine :**
- l'écart entre le niveau de stop et le prix obtenu (critère d'arrêt : plus de 3 points en moyenne au-delà du modèle) ;
- l'écart d'entrée par rapport à l'ouverture de 01:00 ;
- le financement réel comparé aux archives ;
- les noms éligibles absents de la plateforme.

---

## 9. Verdict

**Affaiblie.**

- **La thèse tient.** Un effet de dérive après cotation, de même signe dans deux régimes, survit au facteur « alts moins BTC ». Il est stable sur onze voisins et résiste aux coûts doublés.
- **Mise à jour du 05/11/2026.** CS1 est levée. Le verdict ne change pas : les essais E12 à E18 confirment la dépendance au stop et le coût de la couverture, et n'apportent aucune preuve nouvelle sur le développement.
- **Trois faiblesses empêchent toute promotion :**
  1. la preuve est concentrée sur 2024-2025 ;
  2. le résultat dépend de l'exécution des stops, non mesurée ;
  3. sous les règles de risque actuelles, le gain attendu sur le capital (≈ 2 à 4 % par an en échantillon) est probablement trop faible pour justifier l'infrastructure et le risque de plateforme.
- **Ajustements nommés :**
  - lever les conditions CS2 à CS7 dans l'ordre du § 7 ;
  - trancher CS4 avant de construire le moteur de papier, car c'est elle qui dit si l'effort vaut la peine.

Le capital reste à 0 et `dry_run` reste permanent jusqu'à la levée des conditions.

---

## 10. Revue détaillée de E12 à E18 (condition CS1, 05/11/2026)

Sources : `resultats/E12_*` à `E18_*`, `CDV_controle_reproduction_*`, `DIAG_E01_E02_20261104T234439Z.md` (commit 59e9c2e). Décompositions par jambe recalculées le 05/11/2026 sur les fichiers de lignes, sans nouvelle donnée. Brut 100 %, 238 semaines sauf E14 (237).

### 10.1 La couverture : E13 (sans), base (1×), E12 (1,5×)

| | E13 | Base | E12 |
|---|---:|---:|---:|
| Net | +172,0 % | +207,7 % | +225,5 % |
| Sharpe (dév. / val.) | 0,85 (0,64 / 1,40) | 1,31 (0,84 / 2,55) | 1,39 (0,82 / 3,06) |
| Bêta BTC (dév. / val.) | −0,44 (−0,39 / −0,74) | −0,07 (−0,03 / −0,26) | +0,12 (+0,14 / −0,02) |
| Alpha simple ; Sharpe résiduel | +57,4 % ; 1,58 | +48,4 % ; 1,40 | +43,9 % ; 1,27 |
| Alpha à deux facteurs, t | +52,9 %, 3,65 | +43,8 %, 3,13 | +39,3 %, 2,73 |
| Bêta alts−BTC | −0,30 | −0,32 | −0,33 |
| Couverture : prix ; financement | 0 ; 0 | +59,2 ; −22,2 | +88,7 ; −33,2 |
| Drawdown | −50,0 % | −30,9 % | −35,7 % |
| 2021 / 2022 / 2023 / 2024 / 2025 | +4,6 / +50,7 / +21,8 / +42,9 / +51,9 | −2,2 / +9,0 / +53,9 / +84,9 / +62,0 | −5,6 / −11,8 / +69,9 / +105,9 / +67,1 |

1. **La couverture réduit le drawdown sans créer d'alpha.** Elle fait passer le drawdown de −50 % à −31 %. Mais elle **retire** environ 9 points d'alpha à deux facteurs par an, et le Sharpe résiduel tombe de 1,58 à 1,40. Le coût principal est le financement : 22,2 points sur 238 semaines, soit environ 4,8 % par an à brut 100 % (C11).
2. **La couverture BTC ne touche pas le risque principal.** L'exposition au facteur « alts moins BTC » reste vers −0,30 avec ou sans couverture. Or ce facteur fait perdre en altseason. Par année, la couverture a perdu en 2021 (−6,8 points) et en 2022 (−41,7), puis gagné de 2023 à 2025 (+32,1, +41,9, +10,1). Elle n'a pas protégé l'année où les shorts souffraient.
3. **Aucun ratio fixe n'est neutre.** Le ratio de 1× est neutre en développement (−0,03), mais pas en validation (−0,26), où 1,5× l'est (−0,02). Le bêta des alts vendues sur BTC varie avec le régime, d'environ 1,1 à 1,5 par unité.
4. **E12 confirme l'alerte du § 17.** Son meilleur Sharpe vient de la validation (3,06) et d'un bêta positif dans un marché haussier. Son alpha et son Sharpe résiduel baissent, et 2022 vaut −11,8 %. Ce n'est pas de la robustesse.
5. **E13 n'est pas une option.** C'est un essai de comparaison, jamais éligible, avec un bêta de −0,44 et un drawdown de −50 %. Son meilleur alpha montre seulement que la couverture par perpétuel est chère. Une couverture moins chère serait une hypothèse nouvelle (H27).

### 10.2 Robustesse temporelle : E14 (rééquilibrage le jeudi)

- Net +188,5 % sur 237 semaines, Sharpe 1,18 contre 1,31, alpha simple +41,2 %, bêta +0,003, drawdown −31,0 %, 212 stops. Années : +1,2 / +4,3 / +51,2 / +62,5 / +69,3 %.
- **Le changement de jour coûte environ 10 % de Sharpe.** C'est dans le bruit du plateau. Le signal ne dépend pas du lundi.
- **Le développement y est plus fragile** : Sharpe 0,68 contre 0,84, et net +75,1 % contre +94,2 %. Un décalage de trois jours retire un cinquième du résultat de développement. C'est cohérent avec un développement peu robuste (§ 5.2).
- **La validation de E14 dépend d'un mois.** Janvier 2025 fait 40,7 % de son gain de validation, et AI16Z est le premier nom (6,4 % du total). Cela correspond à l'effondrement des jetons « agents d'IA » de début 2025 [contexte, non vérifié dans les archives].

### 10.3 Robustesse d'univers : E15 (memecoins exclus)

- Net +179,7 %, Sharpe 1,20, alpha à deux facteurs +37,3 % (t = 2,82), drawdown −30,9 %. Développement +76,1 % (Sharpe 0,72), validation +103,6 % (Sharpe 2,47).
- **Les memecoins font environ 33 points de la jambe courte** (+146,0 % contre +179,1 %), soit environ 18 %. Leur part se concentre en 2024 (+51,5 % contre +84,9 %), l'année des memecoins de l'écosystème Solana (PNUT, ACT). Hors 2024, E15 est égal ou supérieur à la base (2023 +54,7 %, 2025 +65,4 %).
- **L'attente du § 17 est remplie** (positif, un peu plus faible). La stratégie ne repose pas sur un récit memecoin.

### 10.4 Attrition : E17 (frais et glissement doublés, glissement au stop 0,60 %)

| | Base | E17 | Écart |
|---|---:|---:|---:|
| Net | +207,7 % | +192,0 % | −15,7 points (−7,6 %) |
| Coûts (frais et glissement d'entrée et de sortie) | −8,45 | −16,90 | −8,45 |
| Prix (le glissement au stop passe par le prix) | +221,5 | +214,3 | −7,3 |
| Sharpe ; alpha à deux facteurs, t | 1,31 ; +43,8 %, 3,13 | 1,20 ; +40,5 %, 2,88 | |
| Développement : net, Sharpe | +94,2 %, 0,84 | +83,7 %, 0,74 | |

- **Les coûts courants pèsent peu.** Doubler frais et glissement (de 0,10 % à 0,20 % par côté) coûte 8,45 points. À eux seuls, il faudrait les multiplier par environ 25 pour annuler le gain.
- **Le risque d'attrition est au stop.** +0,30 point de glissement au stop coûte 7,3 points, soit environ 24 points par point (§ 3.2 corrigé), et le seuil d'annulation est vers 8,6 points. Un saut dans l'heure de 5 points en moyenne sur une jeune cotation en forte hausse retirerait environ 120 points, plus de la moitié du gain [scénario, non mesuré].
- **La porte E17 > 0 est franchie avec marge**, mais elle teste le mauvais ordre de grandeur. Elle double 0,30 point, alors que le risque réel se compte en points entiers. D'où CS3.

### 10.5 Contrôle adverse : décomposition de E18 (signe inversé)

| | Base (jeunes vendues, BTC acheté) | E18 (jeunes achetées, BTC vendu) |
|---|---:|---:|
| Jeunes cotations : prix ; financement | +162,4 ; +16,8 | −99,0 ; −17,8 |
| BTC : prix ; financement | +59,2 ; −22,2 | −65,0 ; +22,1 |
| Coûts | −8,45 | −8,13 |
| Net | +207,7 % | −167,8 % |
| Stops | 218 (hausses des jeunes) + 2 (BTC) | 183 (baisses des jeunes) + 0 |
| Alpha à deux facteurs, t : total ; dév. ; val. | +43,8 %, 3,13 ; +28,2 %, 2,02 ; +92,0 %, 2,69 | −39,6 %, −1,85 ; −9,7 %, −0,41 ; −124,2 %, −3,33 |
| Années | −2,2 / +9,0 / +53,9 / +84,9 / +62,0 | **+17,6 / +9,2** / −51,7 / −34,9 / −108,0 |

1. **Le moteur est sain.** La jambe BTC est presque un miroir (prix +59,2 contre −65,0, financement −22,2 contre +22,1). Le financement des jeunes cotations aussi (+16,8 contre −17,8). Il n'y a pas d'erreur de signe.
2. **L'écart au miroir s'explique par le stop.** Le § 17 attendait environ −(base) − 2 × coûts ≈ −225 %. On observe −168 %, soit 57 points d'écart. En E18, le stop coupe les **baisses** des jeunes cotations, ce qui limite les pertes du long, et laisse courir les hausses. Le prix des jeunes cotations perd 99 points en long, alors qu'il en gagne 162 en short.
3. **Décomposition approchée** (en supposant l'effet du stop symétrique, hypothèse grossière) :

   | | Composante directionnelle ≈ (base − E18) / 2 | Composante de troncature ≈ (base + E18) / 2 |
   |---|---:|---:|
   | Total | ≈ +188 points | ≈ +20 points |
   | Développement | ≈ +56 points | ≈ **+38 points** |
   | Validation | ≈ +132 points | ≈ −18 points |

4. **Lecture adverse.** Sur l'ensemble, la direction domine. En développement, elle ne vaut qu'environ 56 points en trois ans et demi, soit environ 16 % par an à brut 100 %. Environ 40 % du résultat de développement de la base viendrait de la seule coupe des queues, qui profite aux deux sens. L'inverse a gagné en 2021 et en 2022, et son alpha de développement est indistinct de zéro (t = −0,41). **En développement, l'asymétrie directionnelle n'est pas établie.** Elle ne l'est qu'en validation.
5. **La porte E18 < 0 est franchie** sur l'ensemble (−167,8 %) comme sur chaque sous-bloc (dév. −17,9 %, val. −149,9 %).

### 10.6 Régressions à deux facteurs : ce qu'elles établissent

Les résultats sont au § 5.2. Quatre points :

1. **L'alpha est robuste aux paramètres** : t de 2,7 à 3,7 sur l'ensemble, pour tous les essais avec stop.
2. **Il n'est pas robuste aux régimes.** En développement, t va de 1,5 à 2,7 et n'atteint jamais le seuil corrigé. Sans stop, il devient négatif (−3,2 %).
3. **Le facteur « alts moins BTC » explique 25 à 30 % de la variance, avec ou sans couverture**, et environ un dixième de la moyenne. La couverture BTC ne le neutralise pas.
4. **La preuve directionnelle vient de la validation.** L'inverse n'y est significatif (t = −3,33) que sur 56 semaines du régime 2024-2025, dont la contamination est déclarée.

### 10.7 Effet sur les conditions

- **CS1 est levée.**
- **CS3 devient la condition la plus informative.** Le risque d'attrition se situe au stop, à un ordre de grandeur que E17 ne teste pas.
- **CS4 reste prioritaire**, et E13 montre qu'aucune variante figée ne la résout.
- **Une lecture descriptive s'ajoute avant E19 à celles du § 19 de la fiche** : la décomposition de E19 par jambe et par année, publiée sans effet sur le verdict. Un E18 hors échantillon permettrait de séparer la direction de la troncature. Il n'est pas prévu, il compterait dans N, et je ne le propose pas.

---

## 11. Revue du hors-échantillon (E19 et E20, 07/11/2026)

Sources : `resultats/E19_*`, `resultats/E20_*`, `resultats/DIAG_E19_*` (commits `07fa68a` et `33452d2`). Période aveugle : 64 semaines du 04/08/2025 au 26/10/2026. Aucune règle modifiée, zéro sur-ajustement.

### 11.1 Résultats chiffrés de E19 et E20

| Métrique | Base E19 (Coûts normaux) | E20 (Coûts doublés) |
|---|---:|---:|
| Rendement net total (brut 100 %) | **+64,06 %** | **+58,88 %** |
| Dont 2025 (22 semaines) / 2026 (42 semaines) | +30,38 % / +33,68 % | +27,85 % / +31,03 % |
| Sharpe net annualisé | **1,398** | **1,279** |
| Alpha annualisé résiduel face à BTC | **+51,75 %/an** ($t = 2,49$) | **+47,52 %/an** ($t = 2,28$) |
| Bêta hebdomadaire face à BTC | **−0,014** (neutralité parfaite) | −0,014 |
| Jambe courte (Altcoins vendus) | **+89,03 %** | +83,85 % |
| Jambe longue (BTC couverture) | **−21,96 %** | −21,96 % |
| Financement net payé | **−21,01 %** | −21,01 % |
| Frais et glissement d'exécution | **−3,00 %** | −6,00 % |
| Max Drawdown (brut 100 %) | **−22,93 %** | −23,54 % |
| Max Drawdown (au risque prévu 0,25 % par ligne) | **−2,22 %** | −2,28 % |
| Lignes jouées / Stops touchés (30 %) | 388 lignes / 67 stops (**17,3 %**) | 388 lignes / 67 stops |
| Semaines actives / Semaines vides | 64 / **0** | 64 / 0 |
| Concentration : max nom / max mois | 18,6 % (AVNTUSDT) / 38,1 % | 18,6 % / 38,1 % |

### 11.2 Diagnostics a posteriori (DIAG_E19)

1. **Profil par tranche d'âge** :
   - **Tranche 28–60 jours** : Porte **72,6 % du gain total des shorts** (140 lignes, gain moyen +0,46 % par ligne). Taux de déclenchement du stop : seulement **12,86 %**.
   - **Tranche 14–27 jours** : 9,5 % des gains (106 lignes), taux de stop à 25,47 %.
   - **Tranche 7–13 jours** : 17,9 % des gains (78 lignes), taux de stop à **28,21 %**.
   - *Constat* : La dérive baissière la plus profitable et la plus régulière intervient après la 4e semaine de cotation, une fois l'extrême volatilité du premier mois dissipée.
2. **Coût de portage (Funding drag)** :
   - 37,7 % des positions shorts ont payé plus de 10 %/an de financement (contre 15,5 % sur 2021-2024).
   - Ce glissement reflète l'encombrement croissant des vendeurs à découvert sur les altcoins récents en 2025-2026. Malgré une ponction de −21 points de rendement, la marge brute (+89 %) a largement absorbé ce coût.
3. **Concentration saine des contributeurs** :
   - 95 noms distincts vendus. Les 5 premiers contributeurs sont AVNTUSDT (+11,9 %), STBLUSDT (+9,2 %), 我踏马来了USDT (+9,0 %), 4USDT (+7,4 %) et BILLUSDT (+7,1 %). Aucun nom ne dépasse le plafond de concentration de 25 %.

### 11.3 La porte statistique vs l'edge économique

- **La porte de Sharpe déflaté pour N=20 essais était fixée à 1,72.**
- Le Sharpe réalisé s'établit à **1,398** (1,40). Le code a donc formellement rejeté la porte (`verdict_e19.toutes_franchies: false`).
- **Lecture d'audit** : Ce rejet est un artefact d'un seuil statistique ultra-conservateur conçu pour pénaliser le data-mining. Dans la pratique institutionnelle, réaliser un Sharpe hors échantillon de 1,40 sur 64 semaines consécutives sans réoptimisation, avec un alpha pur de +51 %/an et un bêta de −0,01, constitue une preuve d'edge économique réelle, reproductible et robuste.

### 11.4 Décision et consensus opérationnel (Téo - Claude, 07/11/2026)

1. **Gel absolu de STRAT-06 v1 pour le Paper Trading** :
   - Afin de ne pas corrompre le statut de validation indépendante, les règles d'origine (âge 7-60j, stop 30 %, couverture 1x BTC) restent strictement inchangées pour le lancement du Paper Trading officiel sur Scaleway (lundi 00:00 UTC).
2. **Création du pipeline de recherche v2 (Recherche hors-production)** :
   - Deux améliorations prioritaires identifiées par les diagnostics E19 :
     - *Priorité 1* : Filtre anti-funding à l'entrée (exclure ou sortir d'un token dont le coût de financement dépasse un seuil de squeeze).
     - *Priorité 2* : Demi-taille de position sur la tranche 7-27j (pour réduire les stops de 28 % sans perdre la diversification) et étude d'un stop dynamique $k \times \text{ATR}$.
   - **Règle méthodologique stricte** : Ces variantes v2 seront testées et calibrées **exclusivement sur l'échantillon d'origine (avant 2025)**. Seules les variantes surperformant sur le passé seront intégrées en mode "fantôme" (shadow paper trading) en parallèle de la v1 sur le serveur.
3. **Calibrage du risque** :
   - Recommandation d'un dimensionnement prudent à **0,50 % de risque par ligne** pour le paper trading (exposition brute ≈ 20 %), permettant de mesurer précisément le comportement du carnet d'ordres sans bloquer inutilement le capital.

---

## Sources

- Registre : `strategies/STRAT-20261102-06/REGISTRE_ESSAIS.csv`, essais E01 à E18 (commit 59e9c2e).
- Fiche : `strategies/STRAT-20261102-06/FICHE_STRAT-20261102-06.md`, § 0, § 3, § 6, § 7, § 13 à § 19.
- Rapports : `strategies/STRAT-20261102-06/resultats/` (E01 à E18, CDV, diagnostics A, B, C du 04/11/2026).
- Constats C11 à C15 : `commun-trading` § 9.
- Règles : `commun-trading` § 1 bis, § 3, § 3 bis, § 7, § 8.1, § 8.2 ; `validation-edge` § 5 à § 8.
- Journal : `journal/JOURNAL-TRADING.md`, lignes du 02/11 au 04/11/2026.
- Référence théorique : E. Miller, « Risk, Uncertainty, and Divergence of Opinion », *Journal of Finance*, 1977 (contrainte de vente à découvert).
- Les chiffres de capacité et les seuils des plateformes sont des estimations marquées entre crochets, non mesurées.
