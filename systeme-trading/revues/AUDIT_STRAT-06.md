# Dossier d'audit adverse et de promotion — STRAT-20261102-06

Dérive des perpétuels nouvellement cotés : short de jeunes cotations, couverture BTC.

Rédigé le 04/11/2026 par le Cerveau, en application de `validation-edge` § 5 à § 8 et de `avocat-du-diable`. État des essais au 04/11/2026 : E01 à E11 lus, E12 en cours, E13 à E20 non lus. Résultat de recherche, aucune recommandation d'investissement, aucun ordre.

**Verdict de l'avocat du diable : affaiblie.** La thèse reste défendable. Le dossier n'est **pas promouvable** aujourd'hui. Statut : `backtest`. Sept conditions suspensives précèdent le papier (§ 7) et six autres le pilote réel (§ 8).

---

## 0. Synthèse en dix lignes

1. Sur 238 semaines (01/2021 à 07/2025), la base gagne +207,7 % à brut 100 %. Sharpe 1,31, drawdown −30,9 %, alpha à deux facteurs +43,8 % par an (t = 3,13).
2. Neuf voisins sur neuf sont rentables, avec un plateau de Sharpe de 1,13 à 1,46. Le signal ne tient pas à un réglage fin.
3. La preuve repose surtout sur 2024-2025. En développement seul, l'alpha à deux facteurs vaut +28 % par an, t = 2,02. C'est sous un seuil corrigé des tests multiples.
4. La règle a capté **deux mécanismes successifs** (C14). En 2021-2024, d'anciens jetons reçoivent un premier perpétuel. En 2024-2025, des jetons neufs à faible flottant se dégonflent.
5. **Le stop porte l'edge** (C15). Sans stop, le Sharpe tombe à 0,49, le développement devient négatif et le drawdown atteint −82 %.
6. Chaque point de glissement supplémentaire aux stops coûte environ 18 points de rendement sur 207. Un écart de l'ordre de 11 points au-delà du modèle annule le gain.
7. **Les règles de risque en vigueur (`commun-trading` § 3 et § 8.2) sont incompatibles avec la stratégie telle qu'elle est figée.** La couverture BTC dépasse 1 % de risque par position, et le portefeuille compte 7 positions.
8. Au dimensionnement conforme le plus large, l'exposition brute vaut environ 4,9 % du capital. Le rendement en échantillon serait alors d'environ **+2,2 % par an**, avant toute dégradation hors échantillon.
9. La capacité de marché n'est pas la contrainte : elle est de l'ordre de 10 à 25 M$ de capital au dimensionnement conforme [estimation]. Ce sont les règles de risque et l'exécution des stops qui limitent.
10. La probabilité de franchir le seuil de 1,72 hors échantillon est d'environ 25 à 35 % si l'effet est réel (fiche § 19).

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

### 3.2 Sensibilité chiffrée

- La base compte 220 stops sur 1 330 lignes, à 1/12 de notionnel : environ 18,3 unités de notionnel stoppées sur 238 semaines.
- **Chaque point de glissement supplémentaire au stop coûte environ 18 points de rendement** à brut 100 %, sur 207,7.
- Le seuil d'annulation du gain se situe vers **11 points** de glissement moyen au-delà du modèle.
- E09 (361 stops) y est plus sensible : environ 30 points par point de glissement.

Le modèle actuel remplit au pire du niveau et de l'ouverture de l'heure, plus 0,30 %. Il couvre les sauts à l'ouverture, pas ceux qui se produisent dans l'heure. E17 double le glissement au stop (0,60 %), sans modéliser de saut.

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

---

## 5. Tests multiples, puissance et transparence

### 5.1 État des portes du § 7 (au 04/11/2026)

| Porte | État |
|---|---|
| Net > 0 sur E01 et E02 | franchie (+94,1 %, +113,4 %) |
| Alpha > 0 sur E01 et E02 | franchie |
| 3 années sur 4 positives (2021-2024) | franchie (2021 négative) |
| 9 voisins sur 11 rentables | franchie (9 sur 9, E12 et E14 en attente) |
| E16 et E17 > 0, E18 < 0 | **non lues** |
| Concentration, drawdown (base) | franchies |
| Hors échantillon (E19, E20) | **non lancé** ; seuil de Sharpe 1,72 (20 essais) |

### 5.2 Puissance (L8)

Si le vrai Sharpe est entre 1,1 et 1,3, la probabilité de franchir 1,72 sur 64 semaines est d'environ 25 à 35 %. Un échec ne prouvera pas l'absence d'effet, mais il restera un échec. Au niveau du système, 7 hypothèses ont été testées sur des rendements (H01 à H03, H05 à H07, H12). Un promu sur sept ne se lit pas comme un promu sur un.

### 5.3 Points de transparence à publier tels quels

1. La concentration est calculée hors couverture BTC. C'est une lecture du texte du § 3, par décision du 02/11/2026, et elle était favorable à la poursuite.
2. La porte du drawdown est limitée à la base et au hors échantillon. Décision du 04/11/2026, favorable à la poursuite. E07 (−57,7 %) et E11 (−82,0 %) l'auraient échouée.
3. E11 est rentable sur l'ensemble, mais **négatif sur le développement** (−27,5 %).
4. Le critère de 0,2 R de `validation-edge` § 5 n'est pas repris par la fiche (décisions D3 du 01/11 et du 02/11, reconduites). L'espérance publiée est de l'ordre de 0,03 R, ou environ 0,06 R avec le notionnel corrigé. **Avec le critère de 0,2 R, la stratégie échouerait au § 5.** Le conflit entre le skill et la fiche doit être tranché par écrit (CS5).
5. La fiche a été relue après résultats (§ 19, mécanismes de C14), sans aucun changement de règle.
6. Une erreur de libellé du § 17 (E16 présenté comme un essai de coûts) a été corrigée avant tout essai.
7. Lectures a posteriori sur blocs consommés : diagnostics A, B, C et constats C12 à C15. Elles sont hors N et ne servent pas de preuve.

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

| N° | Condition | Critère |
|---|---|---|
| CS1 | Fin du train E12 à E18, lu sur la grille du § 17 | E16 > 0, E17 > 0, E18 < 0 |
| CS2 | Chargeur des archives journalières pour le dernier mois, testé, puis E19 et E20 **une seule fois** | Verdict du § 7 de la fiche : Sharpe > 1,72, borne basse de l'IC > 0, alpha > 0, drawdown < 20 % au risque prévu, E20 > 0, au moins 30 semaines et 100 lignes, concentration. Lectures descriptives du § 19 publiées |
| CS3 | Stress d'exécution des stops, hors N, décidé par écrit avant lancement | Base : net > 0 et alpha > 0 avec remplissage à mi-chemin du plus haut de l'heure. Remplissage au plus haut de l'heure publié. Résultat publié quel qu'il soit |
| CS4 | Compatibilité avec `commun-trading` § 3 et § 8.2, exigée par `validation-edge` § 5 | Décision écrite de Jonathan : soit dimensionnement conforme strict (≈ 4,9 % brut), soit règle de compensation de la couverture, avec le rendement attendu chiffré et accepté par écrit. Statut de la couverture : 7e position ou « jambe de couverture » |
| CS5 | Conflit sur le critère de 0,2 R | Décision écrite : le critère ne s'applique pas à STRAT-06 (Sharpe hors échantillon à la place, D3), ou s'applique et rejette |
| CS6 | Drawdown du 95e centile (tirage par blocs de 4 semaines sur E19) | Valeur inscrite. Elle fixe le coupe-circuit « moteur » (1,5 fois ce centile) |
| CS7 | Moteur de papier | Calcul en direct du lundi, à partir de l'`exchangeInfo` du jour (exclusion des contrats non crypto par `underlyingType` et `contractType`, L10) et des volumes journaliers. `dry_run: true`. Journal des signaux. Rejeu hebdomadaire dans le moteur de backtest sur les mêmes données : sélection identique exigée chaque semaine |

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

- **La thèse tient.** Un effet de dérive après cotation, de même signe dans deux régimes, survit au facteur « alts moins BTC ». Il est stable sur neuf voisins.
- **Trois faiblesses empêchent toute promotion :**
  1. la preuve est concentrée sur 2024-2025 ;
  2. le résultat dépend de l'exécution des stops, non mesurée ;
  3. sous les règles de risque actuelles, le gain attendu sur le capital (≈ 2 à 4 % par an en échantillon) est probablement trop faible pour justifier l'infrastructure et le risque de plateforme.
- **Ajustements nommés :**
  - lever les conditions CS1 à CS7 dans l'ordre ;
  - trancher CS4 avant de construire le moteur de papier, car c'est elle qui dit si l'effort vaut la peine.

Le capital reste à 0 et `dry_run` reste permanent jusqu'à la levée des conditions.

---

## Sources

- Registre : `strategies/STRAT-20261102-06/REGISTRE_ESSAIS.csv`, essais E01 à E11.
- Fiche : `strategies/STRAT-20261102-06/FICHE_STRAT-20261102-06.md`, § 0, § 3, § 6, § 7, § 13 à § 19.
- Rapports : `strategies/STRAT-20261102-06/resultats/` (E01 à E11, CDV, diagnostics A, B, C).
- Constats C11 à C15 : `commun-trading` § 9.
- Règles : `commun-trading` § 1 bis, § 3, § 3 bis, § 7, § 8.1, § 8.2 ; `validation-edge` § 5 à § 8.
- Journal : `journal/JOURNAL-TRADING.md`, lignes du 02/11 au 04/11/2026.
- Référence théorique : E. Miller, « Risk, Uncertainty, and Divergence of Opinion », *Journal of Finance*, 1977 (contrainte de vente à découvert).
- Les chiffres de capacité et les seuils des plateformes sont des estimations marquées entre crochets, non mesurées.
