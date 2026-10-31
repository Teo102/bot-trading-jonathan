# SQD, rentabilité chiffrée et intégration au cerveau — 31/10/2026

Chaîne : C1 (`conseil-trading`) sous `cerveau-trading`. Heures en UTC. Donnée non vérifiée = entre crochets. Aucun chiffre de ce document n'est une promesse de gain.

---

## 0. ALERTE BLOQUANTE ET AUTOCRITIQUE

### 0.1 Polymarket est interdit depuis la France

- Le 16/07/2026, l'ANJ a ordonné aux fournisseurs d'accès français de bloquer Polymarket (CoinDesk 18/07, Gambling Insider, Journal du Geek 20/07). Les transactions depuis la France étaient déjà bloquées par Polymarket depuis novembre 2024 (Medias24, 17/07).
- Polymarket conteste la décision en justice (communiqué du 21/08/2026). Aucune issue connue au 31/10 [à vérifier].
- Contourner le blocage (VPN, DNS) exposerait à des sanctions ; une source cite une amende pouvant atteindre 100 000 € (KultureGeek, 24/08) [montant non vérifié auprès de l'ANJ].
- La session de travail est localisée en France (Chartres). Le pays de résidence fiscale et légale de Jonathan n'est inscrit nulle part dans `commun-trading` : **[à confirmer, condition bloquante]**.

**Conséquence.** Si Jonathan réside en France, Polymarket ne peut pas être un moteur de cash dans ce système. Le système ne propose aucun contournement. Polymarket reste exploitable comme **source d'information** (probabilités implicites lues comme signaux pour le trading pur), pas comme lieu de mise.

### 0.2 Erreurs et faiblesses de mes rapports précédents

| # | Affirmation passée | Problème | Correction |
|---|---|---|---|
| 1 | « Accès depuis les Émirats [à vérifier] » | Hypothèse tirée d'une adresse e-mail, jamais vérifiée ; la session est en France | Pays de résidence à confirmer ; Polymarket bloqué en France |
| 2 | Priorité 1 = Polymarket | Invalide si résidence en France | Priorité déplacée (§ 4) |
| 3 | « Confiance ≈ 65 % » | Chiffre sans base mesurable : fausse précision | Retiré |
| 4 | Matrices notées sur 20 | Notes subjectives présentées comme une mesure | À lire comme un classement qualitatif, pas comme un score |
| 5 | Règle de régime « ratio ≥ 3, taille ÷ 2 » | Seuils arbitraires, non testés | Statut d'hypothèse à backtester |
| 6 | « 7,3 % du volume UMA contesté » | Source unique (Fidonis), méthode non vérifiée | Marqué [source unique] |
| 7 | « 14 des 20 portefeuilles les plus rentables sont des bots » | « Simple revue » du classement, non reproductible | Marqué [indicatif] |
| 8 | Étude des 40 M$ d'arbitrage | Période citée différemment selon les sources (2023–24 ou 2024–25) | Période à lire dans l'article arXiv 2508.03474 |
| 9 | OI BTC 53,6 Md$ contre 29,6 Md$ | Deux périmètres incompatibles, aucun retenu | Inchangé : source dérivés unique nécessaire |
| 10 | Flux ETF d'octobre « ≈ −516 M$ » | Les totaux varient selon la source et la date (−176, −314, −516, −532 M$) | Chiffre final Farside attendu le 02/11 |
| 11 | Heure CoinGecko « ≈ 16:20 » | Heure déduite, non renvoyée par l'outil | Marquée approximative |

---

## 1. DÉCRYPTAGE DE SQD

### 1.1 Le tweet

- Lien : x.com/0xsqd/status/2116310867721531848. Horodatage déduit de l'identifiant : **30/10/2026 23:26 UTC**.
- **Contenu non lu** : X bloque la lecture automatique. Aucune affirmation de ce rapport ne s'appuie sur son texte. Une copie du texte par Jonathan permettrait de l'analyser précisément.
- Contexte vérifié : le 27/01/2026, SQD annonçait son entrée dans les marchés de prédiction avec @mevtools, qui utilise le Pipes SDK pour alerter sur des portefeuilles Polymarket « sans historique » plaçant de grosses mises (X, @helloSQD).

### 1.2 Ce que SQD contient réellement

| Composant | Rôle | Licence et coût |
|---|---|---|
| SQD Network | Lac de données décentralisé, nœuds « workers » rémunérés en jeton SQD | AGPL-3.0 ; aucun jeton requis pour utiliser le Portal public |
| Portal (API HTTP) | Flux de données brutes par plage de blocs, `POST /datasets/{dataset}/stream`, réponses en JSON Lines | Public sans clé, « capacité partagée pour le développement et l'évaluation » |
| Portal MCP | 31 outils en lecture seule (v0.8.5) : EVM, Solana, Bitcoin, Substrate, Hyperliquid, Tron | Sans authentification ; **expérimental** selon la doc |
| Pipes SDK, Squid SDK | Bibliothèques TypeScript d'indexation vers Postgres, ClickHouse, BigQuery, Parquet | Apache-2.0 ; Pipes en version bêta 1.0 |
| SQD Cloud, SQD 360 | Hébergement géré, offres entreprise | [Tarifs non vérifiés] |

Nombre de réseaux : la doc indique « 120+ », d'autres pages de SQD « 200+ » ou « 225+ ». Le chiffre exact reste [incohérent selon les pages].

### 1.3 Ce qu'on peut en tirer

**Hyperliquid (le plus utile pour le trading pur).** Fills avec PnL, frais et routage ; analytics (volume, principaux actifs, classement des traders) ; bougies OHLC ; commandes brutes (ordres, annulations, transferts, changements de levier). Ce sont des données au niveau du portefeuille, introuvables sur une plateforme centralisée.

**EVM (Ethereum, Base, Arbitrum…).** Transactions, logs, traces, transferts de jetons, activité de contrats, bougies DEX (Uniswap v2/v3/v4, Aerodrome, expérimental). Utile pour les flux de stablecoins, les mouvements vers les plateformes et la concentration des détenteurs d'un jeton.

**Solana.** Transactions et instructions brutes : base de toute analyse de memecoins (créateur, premiers acheteurs, concentration).

**Polymarket : ce qui est accessible et ce qui ne l'est pas.**
- Accessible : les règlements on-chain sur Polygon (logs `OrderFilled`, création de positions, rachats). Ils passent par les outils EVM génériques. **Aucun outil ou jeu de données Polymarket dédié** n'existe dans le Portal MCP : il faut connaître les adresses de contrats et décoder les événements. La présence de Polygon dans le Portal est probable (étude de cas Olas : réindexation de Polymarket sur SQD), mais [à vérifier].
- Inaccessible : le carnet d'ordres CLOB (hors chaîne), les **règles de résolution** et les métadonnées des marchés (API Gamma de Polymarket). Or la lecture des règles était justement l'edge identifié.

**Absent de SQD.** Données des plateformes centralisées (Binance, Crypto.com), financement et OI agrégés multi-plateformes, cartes de liquidations, macro.

### 1.4 Contraintes réelles

1. **Le MCP sert aux questions bornées, pas aux backtests.** La doc le dit : une analyse large peut rendre une couverture partielle ou expirer. Les exports complets passent par l'API Stream ou un indexeur.
2. **Un backtest sérieux demande du code et une machine.** Cela suppose Claude Code ou Cowork avec accès réseau, plus du stockage (Parquet, ClickHouse). Le chat claude.ai ne suffit pas.
3. **Expérimental** : outils et comportements susceptibles de changer.
4. **Le connecteur** est annoncé dans le répertoire Claude, mais la recherche du répertoire ne l'a pas trouvé ici. L'ajout par URL (`https://portal.sqd.dev/mcp`) en connecteur personnalisé reste possible.

### 1.5 Ce que SQD ne fait pas

Il ne fournit **aucun signal ni aucun edge**. Il fournit des données brutes, déjà accessibles à tous les concurrents, y compris aux bots. L'avantage ne vient que de la question posée et de la rigueur du test.

Sur l'alerte « portefeuilles d'initiés » :
- **Antisélection et retard** : quand la mise apparaît, le prix a déjà bougé.
- **Faux positifs** : un nouveau portefeuille n'est pas un initié.
- **Concurrence** : le créneau est saturé (Nansen « polymarket insider scan », PolyGains, et d'autres).
- **Éthique et droit** : le but est de suivre une information présumée privilégiée. Plus de 150 portefeuilles soupçonnés d'avoir parié sur des secrets militaires ont été signalés (Reuters, 27/08/2026).
- **Légalité depuis la France** : sans objet, Polymarket y est bloqué.

**Sécurité.** Des dépôts GitHub de « bots Polymarket » malveillants ont volé des clés de portefeuille via une organisation GitHub piratée (StepSecurity). Toute installation de code tiers se lit avant exécution ; aucune clé privée n'entre jamais dans le système.

### 1.6 Alternatives de données Polymarket

| Source | Contenu | Coût |
|---|---|---|
| Hugging Face SII-WANGZJ/Polymarket_data | 279 Go, 6,6 Md d'enregistrements on-chain, du 21/11/2022 au 04/10/2026 | Gratuit [licence à vérifier] |
| Hugging Face TimeSeventeen/Polymarket-v1 | ≈ 1,2 Md de fills, 49 Go, jusqu'au 28/04/2026 | Gratuit, CC-BY-4.0 |
| Bitquery | 1,8 Md de lignes, depuis 09/2025, mise à jour quotidienne | 400 $ le mois, 4 000 $ l'historique |

---

## 2. CHIFFRAGE DE RENTABILITÉ

### 2.1 Taux de base (avant toute simulation)

- Polymarket : plus de 69 % des 2,9 millions de comptes « à rythme humain » finissent sous le seuil de rentabilité, pour 338,9 M$ de pertes cumulées (Galaxy Research, oct. 2026). Selon CryptoRank, le top 1 % a capté environ 95 % des profits de 2022 à 2025.
- Polymarket : sur 6 600 traders gagnant plus de 5 000 $ par mois en moyenne, seuls 2,6 % restent actifs plus d'un an (The Defiant, avril 2026). Ce point révèle un biais du survivant.
- Dérivés et CFD : de 74 à 89 % des comptes CFD particuliers perdent de l'argent (divulgations ESMA). Chez les day traders, les études donnent de 70 à 97 % de perdants.
- Futures au Brésil : 97 % des traders particuliers qui ont persisté au-delà de 300 jours ont perdu (cité par Aaron Brown, Bloomberg).

**Lecture.** Sans edge démontré, l'espérance du système est **négative** dans les deux moteurs. Les frais suffisent à l'expliquer.

### 2.2 Simulation Monte Carlo (20 000 trajectoires sur 12 mois)

**Hypothèses du trading pur (swing sur perpétuels).**
- Risque de 1 % du capital par trade, 6 trades par mois.
- Coûts de 0,06 R par trade : frais taker, glissement, financement [estimation].
- Gains variables autour de R ; pertes parfois supérieures à 1 R (glissement sur stop).

| Scénario | Espérance/trade | Médiane 1 an | 5e centile | 95e centile | P(perte annuelle) | Drawdown médian / 95e |
|---|---|---|---|---|---|---|
| Aucun edge (33 % gagnants, 2R) | −0,07 R | −5,9 % | −23,4 % | +17,2 % | 68 % | 14,9 % / 26,5 % |
| Edge modeste (38 %, 2R) | +0,08 R | +4,9 % | −15,5 % | +31,5 % | 36 % | 11,1 % / 21,2 % |
| Bon edge (42 %, 2,2R) | +0,28 R | +21,2 % | −3,9 % | +55,5 % | 9 % | 8,7 % / 16,2 % |
| Excellent, rare (46 %, 2,4R) | +0,50 R | +41,8 % | +9,6 % | +85,1 % | 1 % | 7,2 % / 12,9 % |
| Edge modeste, risque 2 % | +0,08 R | +7,9 % | −29,5 % | +69,0 % | 39 % | 21,4 % / 38,5 % |

**Hypothèses Polymarket.**
- Mise de 2 % par marché, 10 paris par mois, prix entre 0,25 et 0,75, demi-écart de 0,5 point.
- Marchés supposés **indépendants**, ce qui est optimiste.

| Scénario | Médiane 1 an | 5e centile | 95e centile | P(perte) | Drawdown médian / 95e |
|---|---|---|---|---|---|
| Aucun edge | −5,4 % | −35,7 % | +39,7 % | 59 % | 23,7 % / 41,6 % |
| Edge 2 points | +5,0 % | −28,7 % | +55,0 % | 42 % | 20,5 % / 37,2 % |
| Edge 4 points | +16,5 % | −20,6 % | +72,9 % | 26 % | 18,0 % / 32,9 % |
| Edge 7 points, rare | +36,4 % | −7,4 % | +103,2 % | 10 % | 15,0 % / 27,4 % |

**Ce que montrent ces chiffres.**
1. **La variance domine.** Même avec un bon edge, une année sur dix peut finir en perte. Une seule bonne année ne prouve rien.
2. **Les paris binaires produisent des drawdowns plus profonds** à espérance égale. Toute la mise est perdue à chaque échec.
3. **Augmenter le risque par trade n'augmente pas la fiabilité.** Avec un edge modeste, doubler le risque fait passer le 5e centile de −15 % à −30 %.

### 2.3 Cash en euros, avant impôts

Montants annuels médians. Les centiles défavorables se lisent dans le tableau 2.2.

| Capital | Swing, edge modeste | Swing, bon edge | Polymarket, edge 4 pts (hors France) |
|---|---|---|---|
| 5 000 € | ≈ 245 € | ≈ 1 060 € | ≈ 825 € |
| 20 000 € | ≈ 980 € | ≈ 4 240 € | ≈ 3 300 € (liquidité à vérifier) |
| 100 000 € | ≈ 4 900 € | ≈ 21 200 € | capacité limitée par la profondeur des carnets |

- **Impôt en France** sur les plus-values crypto : prélèvement forfaitaire d'environ 30 % [taux 2026 à vérifier]. Le régime des perpétuels pour un particulier est [à vérifier auprès d'un fiscaliste].
- **Lecture brutale.** « Cash rapide » et « fiabilité » s'opposent sur un petit capital. Un bon edge sur 5 000 € produit environ 90 € par mois en médiane. Les promesses de gros rendements mensuels supposent un levier qui détruit la fiabilité.

### 2.4 Le vrai goulot : prouver l'edge

Nombre de trades nécessaires pour distinguer une espérance E d'un hasard, avec un écart type d'environ 1,6 R par trade : n ≈ (2 × 1,6 / E)² [approximation].

| Espérance | Trades nécessaires | Durée à 6 trades par mois |
|---|---|---|
| +0,08 R | ≈ 1 600 | ≈ 22 ans |
| +0,28 R | ≈ 130 | ≈ 22 mois |
| +0,50 R | ≈ 40 | ≈ 7 mois |

**Conséquence.** Un edge modeste ne se prouve jamais par le seul track record. Il faut des **backtests sur données historiques**, puis un suivi en papier, pour écarter les idées faibles avant d'y mettre du capital. C'est là que SQD (Hyperliquid) et les jeux de données publics ont une valeur réelle.

### 2.5 Memecoins, mid-caps, alts

- **Mid-caps et alts liquides** : même moteur swing, avec un glissement plus fort et des corrélations au BTC plus élevées dans les chutes. La taille est à réduire en conséquence (`risque-position`, corrélation).
- **Memecoins** : distribution de type loterie, avec des risques de tirage du tapis, de concentration chez les initiés et de taxes cachées. Le sniping reste exclu (vitesse). Une analyse on-chain via SQD (Solana, EVM) peut écarter une partie des pièges avant un swing sur un memecoin déjà liquide. Aucun taux de base fiable n'a été trouvé : **[non chiffré]**.
- **Cadre légal en France** pour les perpétuels offshore (Hyperliquid sans KYC) et les plateformes non enregistrées : [à vérifier, AMF et MiCA].

---

## 3. EXPLOITER SQD POUR GAGNER (CONCRÈTEMENT)

Les usages sont classés par valeur attendue décroissante.

1. **Backtester avant de risquer.** Bougies et fills Hyperliquid, puis test des règles de swing (cassure, filtre de régime, filtre de financement) avec les vrais frais Hyperliquid. Critères de passage :
   - au moins 100 trades simulés ;
   - espérance supérieure à 0,2 R après coûts ;
   - drawdown maximal inférieur à 20 % ;
   - stabilité sur deux sous-périodes ;
   - aucun paramètre optimisé sur la période de test.
2. **Tester l'« argent intelligent » avant de le suivre.** Hypothèse : « les portefeuilles du top 1 % en PnL sur Hyperliquid restent gagnants le trimestre suivant ». Test sur les fills SQD. Si la persistance est faible, l'idée de copie meurt sans coût.
3. **Mesurer les flux réels.** Émissions et destructions de stablecoins (Ethereum, Tron), mouvements vers les adresses de plateformes, volumes DEX. Ces données alimentent le feu de régime de `veille-macro-crypto`.
4. **Filtrer les pièges sur les alts et memecoins.** Concentration des détenteurs, ventes du créateur, activité réelle du contrat, avant toute thèse T1.
5. **Polymarket comme capteur.** Probabilités on-chain (Fed, élections, réglementation) utilisées comme entrées macro de T1. Cet usage est légal, puisqu'il s'agit de lire des données publiques et non de parier [à confirmer].

---

## 4. PLAN D'INTÉGRATION (SANS DISPERSION)

### 4.1 Nouvelle hiérarchie des moteurs

| Moteur | Statut | Condition |
|---|---|---|
| A. Swing filtré (BTC, ETH, alts liquides, perps) | **Moteur principal** | Backtest réussi puis 8 à 12 semaines de papier |
| B. Polymarket | **Capteur d'information** ; moteur de mise seulement hors de France | Résidence confirmée et accès légal |
| C. Portage de financement delta neutre | Réserve (capital plus élevé) | Capital et plateformes renseignés |

### 4.2 Changements dans les skills (un seul nouveau skill)

| Skill | Changement |
|---|---|
| `commun-trading` 1.2 | Pays de résidence et matrice légale (Polymarket, perps offshore) ; table des sources par priorité (Crypto.com, CoinGecko, SQD, recherche web) ; fiscalité [à compléter] ; statut « papier » ou « réel » de chaque moteur |
| **`validation-edge` (nouveau)** | Aucune stratégie ne passe en capital réel sans backtest (critères du § 3.1) ni papier (au moins 30 trades). Le skill calcule l'espérance, l'intervalle de confiance et le drawdown. Il est appelé par `conseil-trading` et `revue-performance` |
| `analyse-actif` | Feu de régime ; filtre de positionnement ; données Hyperliquid on-chain (SQD) si connectées ; contrôle on-chain des alts et memecoins |
| `analyse-polymarket` | Mode « capteur » par défaut (probabilité → entrée macro) ; mode « mise » seulement si `commun-trading` l'autorise |
| `fiche-trade` et `journal-trading` | Champ « papier » ou « réel » ; P&L papier suivi comme le réel |
| `revue-performance` | Espérance en R avec intervalle de confiance ; règle d'arrêt d'un moteur si sa borne supérieure passe sous 0 après 30 trades |

### 4.3 Calendrier réaliste

1. **Semaine 1.** Pays de résidence et paramètres de `commun-trading` § 3 ; connecteur SQD ajouté par URL ; dès la première chaîne T1, fiches en mode papier.
2. **Semaines 2 à 4.** Backtests Hyperliquid dans Claude Code ou Cowork, qui exécutent du code avec accès réseau ; test de persistance des baleines.
3. **Semaines 4 à 12.** Papier sur les règles validées ; revue hebdomadaire.
4. **Après validation.** Capital réel à une fraction du risque prévu (par exemple 0,25 % par trade), puis montée progressive si la revue confirme.

**Sur le « cash immédiat ».** Le système peut produire des **opportunités documentées** dès aujourd'hui. Il ne peut pas garantir qu'elles rapportent. La voie la plus rapide vers du cash fiable passe par l'élimination rapide des mauvaises idées, pas par la mise rapide de capital.
