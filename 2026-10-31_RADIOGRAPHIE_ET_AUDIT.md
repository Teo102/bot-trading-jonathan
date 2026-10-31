# Radiographie du marché et audit des stratégies — 31/10/2026

Chaîne suivie : M1 (`veille-macro-crypto` → `synthese-marche`) puis C1 (`conseil-trading`), sous `cerveau-trading`.
Classement prévu : `<racine>\veille\2026-10-31_veille.md` (racine encore [à confirmer] dans `commun-trading` § 4).
Heures en UTC. Une donnée non vérifiée ou non trouvée figure entre crochets.

---

## ALERTES (en tête, selon `cerveau-trading` § 2)

1. **Piratage de Binance, environ 6,3 Md$ (29-30/10).** Retraits et dépôts suspendus ; environ 3 Md$ gelés, dont plus de 2,3 Md$ par Tether et Circle ; Binance annonce couvrir les pertes ; reprise des retraits attendue dimanche 01/11 selon un cofondateur. Attribution probable à un groupe lié à la Corée du Nord (TRM Labs). Sources : CNBC 30/10, Bloomberg 29/10, Al Jazeera 30/10. Conséquence pour le système : risque de contrepartie centralisée relevé ; toute stratégie dépendant de Binance est suspendue jusqu'à reprise vérifiée des retraits.
2. **Élections de mi-mandat américaines le 03/11.** Résolution imminente de centaines de marchés Polymarket (315 marchés actifs au 31/10 00:50 UTC, source polymarkettrader.com). Risque de litige de résolution élevé sur les marchés à formulation ouverte.
3. **Accès à Polymarket depuis les Émirats : [à vérifier]** (`commun-trading` § 1). Aucune position Polymarket n'est envisageable avant cette vérification.

---

## VOLET 1 — ÉTAT DES LIEUX

### 1. Macro et liquidité

| Donnée | Valeur | Source | Heure |
|---|---|---|---|
| Taux directeur Fed | 3,75 %–4,00 %, maintenu le 28/10 par 10 voix contre 2 (Cook et Hammack pour une hausse) | CNBC, Fox Business | 28/10/2026 |
| Cycle | hausse de 25 pb en septembre, première depuis juillet 2023 ; inflation jugée « élevée » | Fox Business | 28/10/2026 |
| Probabilité d'une hausse en décembre | 82,6 % (FedWatch) | Fox Business | 28/10/2026 |
| Prochaine réunion Fed | 08–09/12/2026, décision le 09/12 à 14 h ET | fedratecalc.com | 29/10/2026 |
| Président de la Fed | Kevin Warsh | CNBC | 28/10/2026 |
| Indice dollar (DXY) | 101,96, stable sur la semaine ; plus haut de 18 mois vers 102,50 début octobre | Stocktwits, FXStreet | semaine close le 30/10 |
| Taux US 2 ans / 10 ans / 30 ans | 4,59 % / 4,93 % / 5,32 % ; le 10 ans a touché 5,35 % début octobre, plus haut depuis 2002 | Stocktwits, FXStreet | 30/10/2026 |
| Contexte actions | vente marquée sur les valeurs IA : SOX −7,2 % le 30/10, pire mois du Nasdaq 100 depuis 2025 | Stocktwits | 30/10/2026 |
| Géopolitique | risque de conflit au Moyen-Orient intégré par les marchés ; choc d'offre énergétique cité | Kiplinger, CNN | 28/10/2026 |
| BCE, BoJ | [non vérifié dans cette veille] | — | — |

Lecture : politique monétaire en resserrement, taux longs proches de leurs plus hauts depuis vingt ans, dollar ferme. Ce contexte pèse historiquement sur les actifs risqués et sur la crypto [corrélation non chiffrée ici].

### 2. Flux ETF et marché crypto

| Donnée | Valeur | Source | Heure |
|---|---|---|---|
| ETF BTC au comptant, octobre | sortie nette d'environ −516 M$ (somme Farside) | crypto.news | 31/10/2026 |
| ETF BTC, 30/10 | −643,2 M$, plus forte sortie quotidienne depuis juin | crypto.news | 31/10/2026 |
| ETF BTC, cumul depuis 2024 | environ +57,8 Md$ ; actifs nets environ 100,2 Md$ | techyorker | 26/10/2026 |
| ETF BTC, mois précédents | sept. +2,6 Md$ ; août +3,5 Md$ ; juin −4,5 Md$ | TFTC | 14/10/2026 |
| ETF ETH, octobre | environ −1,61 Md$ | crypto.news | 31/10/2026 |
| Prix BTC | 77 529 $ (−0,04 % 24 h) | CoinGecko | 31/10 ≈ 16:20 |
| BTC perpétuel Crypto.com | dernier 77 512,4 $ ; plage 24 h 76 188–77 638 $ ; OI 6 259,6 BTC | connecteur Crypto.com | 31/10 16:23:02 |
| BTC sur un an | 109 567 $ il y a un an → plus bas ≈ 58 566 $ → rebond à ≈ 86 597 $ → 77 529 $ (−29 % sur un an) | CoinGecko (série 365 j, 120 points) | 31/10 ≈ 16:20 |
| Position par rapport au coût moyen des ETF | sous l'estimation Glassnode du coût d'entrée des ETF | crypto.news | 31/10/2026 |
| ETH / SOL / BNB / XRP | 2 249,99 $ / 95,95 $ / 704,66 $ / 1,25 $ | CoinGecko | 31/10 ≈ 16:20 |
| Capitalisation totale | 2 629 Md$ (−2,5 % 24 h) ; volume 24 h 113,5 Md$ | CoinGecko | 31/10 ≈ 16:20 |
| Dominance BTC / ETH | 59,2 % / 10,4 % | CoinGecko | 31/10 ≈ 16:20 |
| Stablecoins (catégorie) | 293,3 Md$ (−0,22 % 24 h) | CoinGecko | 31/10 ≈ 16:20 |

Lecture : marché baissier sur douze mois, rebond de l'été stoppé sous 87 k$, demande ETF en reflux, dominance BTC élevée (fuite vers la qualité au sein de la crypto).

### 3. Microstructure et dérivés

| Donnée | Valeur | Source | Heure |
|---|---|---|---|
| Liquidations après le piratage | 1,57 Md$ en 24 h (×4), dont BTC 522 M$ et ETH 361 M$ | CoinDesk | 30/10/2026 |
| OI total crypto | 136,3 Md$ (−3 %) : clôture de positions | CoinDesk | 30/10/2026 |
| Financement BTC | positif et en hausse : les acheteurs restent majoritaires | CoinDesk | 30/10/2026 |
| Financement BTC (niveau) | +0,0077 %/8 h Binance ; +0,0073 % moyenne | liqwall.com | 25/10 17:02 |
| OI BTC | 53,6 Md$ (−0,84 % sur 30 j) selon CoinStats ; 29,6 Md$ selon liqwall | CoinStats, liqwall | 30/10 et 25/10 |
| Liquidations 29/10 | ≈ 628 M$ en une heure lors du passage sous 80 k$ ; 84,7 % de positions acheteuses sur 24 h | CoinStats | 30/10/2026 |
| Positionnement Binance | 68,1 % des comptes en position BTC sont acheteurs | liqwall.com | 25/10 17:02 |
| SOL | OI −13,3 % pour un prix −3,3 % : capitaux sortis des contrats SOL | CoinDesk | 30/10/2026 |
| Financement Bybit, Hyperliquid | [non trouvé dans cette veille] | — | — |
| Carte des liquidations (zones de concentration) | [non disponible : aucun connecteur CoinGlass actif] | — | — |

Écart relevé : les deux mesures d'OI BTC diffèrent du simple au double (périmètres d'agrégation différents). Aucune n'est retenue comme vérité ; la tendance (stable à baissière) concorde.

Lecture : les acheteurs à effet de levier restent nombreux malgré la baisse ; financement positif dans un marché qui baisse = positionnement encore chargé à l'achat. Ce schéma précède souvent des purges supplémentaires [observation historique, non probabilisée].

### 4. Polymarket

| Donnée | Valeur | Source | Heure |
|---|---|---|---|
| Volume hebdomadaire | 1,04 Md$ (semaine du 26/10, partielle) ; 1,22 Md$ la semaine précédente ; part de 3,7 à 5 % des plateformes de prédiction | defirate.com | 31/10/2026 |
| Intérêt ouvert | 368 M$ | defirate.com | 30/10/2026 |
| Mi-mandat, Polymarket | plus de 340 M$ de volume ; Kalshi près de 1,1 Md$ | CNN | 23/10/2026 |
| Marché « Balance of Power » | 48,1 M$ de volume ; « Democrats Sweep » 71 % | polymarket.com | 31/10/2026 |
| Volume 24 h des marchés mi-mandat | 13,41 M$ sur 315 marchés | polymarkettrader.com | 31/10 00:50 |
| Marché « décision de la Fed en octobre » | ≈ 87 M$ de volume | defirate.com | 31/10/2026 |
| Autres segments | sport (record NFL Kalshi + Polymarket 8,56 Md$ sur un week-end), culture (Ballon d'Or > 41 M$), Nobel | predictionnews, ats.io | oct. 2026 |
| Régulation | CFTC : projet de requalification en swaps ; pression politique sur les paris électoraux | predictionnews | 14/10/2026 |

Inefficiences constatées :
- **Litiges de résolution.** Le marché « Strategy vend-il du BTC avant le 31/05 » s'est résolu « non » malgré un dépôt SEC indiquant des ventes du 26 au 31/05 : la date de publication a primé sur la date de l'événement (Galaxy Research, The Block, juin 2026). Le marché « accord de paix permanent avec l'Iran » (120 M$) a suivi en juin.
- **Ampleur.** De mars 2025 à juin 2026, 3,32 Md$ de volume sont passés par une résolution UMA contestée, soit 7,3 % du volume résolu par UMA (Fidonis, édition 2026-09).
- **Gouvernance.** Au moins 60 % des votants UMA actifs seraient liés à des comptes Polymarket (WSJ cité par Finance Magnates) [conflit d'intérêts, non vérifié directement].
- **Arbitrage structurel.** Sur un an (avril 2024–avril 2025 selon la majorité des sources ; une source indique 2023–2024), environ 40 M$ ont été extraits par des stratégies de sommes de prix différentes de 1 et de dépendances logiques entre marchés ; gains unitaires de 1 à 5 % ; trois portefeuilles ≈ 4,2 M$ (étude IMDEA, arXiv 2508.03474). Les opportunités simples se referment souvent en moins de 200 ms [source secondaire].

### 5. Narratifs et flux réels

| Narratif | Signal réel mesuré | Source | Verdict |
|---|---|---|---|
| Perp DEX | Volume on-chain des perpétuels ≈ 577 Md$ en octobre (627 Md$ en sept.) ; Hyperliquid ≈ 200 Md$, ≈ 35 % de part | CryptoRank, 29/10 | **Flux réel**, en contraction hors RWA |
| RWA (actifs réels) | Perpétuels sur actifs réels 164 Md$ en octobre (+27 %), 28 % du volume perp on-chain, record | CryptoRank, 29/10 | **Flux réel et en croissance** |
| Stablecoins | 293 Md$, stable | CoinGecko | **Flux réel**, stagnant (pas d'argent frais net) |
| IA (jetons) | Rotation hors des valeurs IA en actions (SOX −7,2 %) ; données on-chain non vérifiées | Stocktwits | **[non mesuré]**, contexte défavorable |
| Memecoins | Aucune donnée de flux vérifiée dans cette veille | — | **[non mesuré]** ; narratif présumé artificiel tant qu'aucun volume n'est montré |
| Layer 2 | Aucune donnée vérifiée | — | **[non mesuré]** |

Écart de sources : une source GitHub annonce plus de 1 000 Md$ de volume perp DEX en octobre 2026, CryptoRank ≈ 577 Md$. CryptoRank (rapport daté du 29/10) est retenu ; l'autre chiffre ressemble au record d'octobre 2025 [confusion probable].

---

## SYNTHÈSE DE MARCHÉ (une page, format `synthese-marche`)

**Alerte :** piratage Binance (6,3 Md$) et mi-mandat le 03/11.

**Régime : aversion au risque, tendance baissière sur douze mois, liquidité en resserrement.** Le BTC cote 77,5 k$, −29 % sur un an, sous le coût moyen des ETF. La Fed est en cycle de hausse (3,75–4 %, hausse en décembre probable à 82,6 %). Le 10 ans est proche de 5 %. Les ETF BTC sortent en octobre (≈ −516 M$), les ETF ETH davantage (≈ −1,6 Md$). La dominance BTC monte à 59 %.

**Risques principaux :**
1. Contagion du piratage Binance : retraits non rétablis au 01/11 → déclencheur observable.
2. Purge des acheteurs à levier : financement positif dans un marché baissier → déclencheur : cassure de 76 k$ (plus bas récent du 30/10).
3. Hausse de taux en décembre et taux longs au-dessus de 5 %.

**Opportunités à étudier (pas des thèses) :** marchés Polymarket à formulation ambiguë autour du 03/11 (P1, sous réserve d'accès) ; BTC sur zone 76–78 k$ (T1, avec l'avocat du diable sur le scénario de purge) ; rendement court terme des T-bills tokenisés face à une crypto sans tendance.

**Dates à surveiller :** 01/11 reprise des retraits Binance ; 02/11 total final des flux ETF d'octobre ; 03/11 mi-mandat ; 09/11 environ [à vérifier] publication de l'inflation d'octobre ; 09/12 décision Fed.

**Ce qui changerait la lecture :** BTC durablement au-dessus de 87 k$ (plus haut du rebond) ; trois semaines consécutives d'entrées ETF ; 10 ans sous 4,5 %.

---

## VOLET 2 — AUDIT DES STRATÉGIES AUTOMATISABLES (format `conseil-trading`)

**Contrainte de cadrage.** Le système n'exécute aucun ordre (`cerveau-trading` § 1.1). « Automatisable » signifie ici : détection, analyse et documentation automatisées ; l'exécution reste à Jonathan. Toute stratégie qui exige une exécution en moins d'une seconde est donc **hors de portée par construction**, quel que soit son rendement théorique. Ce point écarte d'emblée près de la moitié des familles.

| # | Famille | Mécanique du rendement | Qui gagne aujourd'hui | Pourquoi la masse perd | Edge défendable pour nous |
|---|---|---|---|---|---|
| 1 | Sniping de lancements (memecoins) | Achat dans les premiers blocs, revente à la foule | Bots avec infrastructure privée, souvent liés aux créateurs | Pots de miel, taxes cachées, tirage du tapis, MEV ; la plupart des jetons vont à zéro | **Aucun.** Rejeté |
| 2 | Arbitrage CEX–CEX, triangulaire | Écart de prix entre plateformes | Teneurs de marché colocalisés | Écarts < frais + transferts ; risque de gel (Binance au 30/10) | **Aucun** (latence). Rejeté |
| 3 | Portage de financement / base (delta neutre) | Long spot + short perp, encaissement du financement ; ou base des contrats à terme | Fonds de base, Ethena, desks | Financement qui s'inverse, liquidation de la jambe courte, **risque de plateforme** (piratage) | **Modéré** : sélection des périodes de financement élevé, discipline de marge. Exécution manuelle possible (lent) |
| 4 | Market making (CEX ou récompenses Polymarket) | Écart acheteur-vendeur + récompenses de liquidité | Firmes spécialisées | Antisélection : on se fait remplir quand l'information arrive | **Faible** sans exécution automatique. Rejeté pour le système actuel |
| 5 | Arbitrage Polymarket intra-marché (somme ≠ 1) et combinatoire | Achat de toutes les issues sous 1 $, ou incohérences logiques entre marchés liés | Bots (14 des 20 portefeuilles les plus rentables seraient des bots, Finance Magnates) | Fenêtres de quelques centaines de ms ; frais ; jambes partiellement remplies | **Faible sur la vitesse, réel sur le combinatoire lent** : incohérences entre marchés à faible liquidité que les bots ignorent. Utile comme **filtre** dans `analyse-polymarket` |
| 6 | Arbitrage Polymarket–Kalshi | Même événement, prix différents | Bots multi-plateformes | **Règles de résolution différentes** : l'« arbitrage » devient un pari sur la divergence ; accès réglementaire | **Réel si lecture de règles** : seul le contrôle mot à mot des clauses rend l'écart sûr. Accès depuis les Émirats [à vérifier] |
| 7 | News trading | Réaction plus rapide à l'information | Fils d'information payants + exécution automatique | Latence : l'information est intégrée avant la lecture humaine | **Aucun** sur la vitesse. Rejeté |
| 8 | Momentum de liquidations | Suivre ou contrer les cascades | Desks avec carte de liquidations en temps réel | Les cascades se retournent ; glissement extrême ; faux signaux | **Faible** ; utile comme **lecture de contexte** (zones de levier) dans T1, pas comme stratégie |
| 9 | Swing directionnel filtré (tendance + positionnement + régime) | Capturer des mouvements de plusieurs jours | CTA, gérants discrétionnaires disciplinés | Sur-trading, absence d'invalidation, levier, biais de récence | **Réel** : faible fréquence, discipline écrite (`risque-position`), contradiction obligatoire (`avocat-du-diable`). C'est la force native du système |
| 10 | MEV, liquidations DeFi (keepers) | Revenus d'ordonnancement des blocs | Chercheurs spécialisés, constructeurs de blocs | Enchères concurrentielles : la rente va au constructeur | **Aucun.** Rejeté |
| 11 | Rendement DeFi (prêt de stablecoins, LP, T-bills tokenisés) | Intérêts, frais de pool | Allocataires prudents | Perte impermanente, faille de contrat, dépeg, rendements gonflés par des jetons | **Modéré** : sélection rigoureuse ; référence de rendement sans risque ≈ taux courts US [≈ 3,75–4 %] |
| 12 | Copie de baleines (Hyperliquid) | Suivre les portefeuilles gagnants | Les baleines elles-mêmes | Copie tardive ; baleines qui couvrent ailleurs ; manipulation par appât | **Faible** ; signal de contexte seulement |
| 13 | Prévision calibrée Polymarket (estimation propre contre prix, lecture des règles) | Écart entre probabilité estimée et prix | Prévisionnistes calibrés, spécialistes de niches | Excès de confiance, ignorance des clauses, illiquidité à la sortie | **Le plus défendable** : 7,3 % du volume UMA est contesté → la lecture des règles a une valeur mesurable ; les LLM aident à lire, mais la masse ne lit pas les clauses |

**Avocat du diable sur l'ensemble.** L'accès général aux LLM et aux scripts ouverts détruit tout edge de vitesse et d'accès à l'information publique. Ce qui reste : (a) la discipline (taille, invalidation, refus de trader), que la plupart des participants n'appliquent pas ; (b) la lecture minutieuse de textes (règles de résolution, dépôts SEC, conditions de contrats) ; (c) l'agilité d'un petit capital sur des marchés trop étroits pour les institutions ; (d) la patience face au régime, quand la masse sur-trade. Aucun de ces avantages n'est automatique : chacun suppose que le système refuse beaucoup plus de trades qu'il n'en propose.

---

## VOLET 3 — MATRICES ET RECOMMANDATION

Notes de 1 (faible) à 5 (fort). « Compatibilité système » = réalisable sans exécution automatique et dans les chaînes existantes.

### Matrice A — Génération de cash rapide (capital modéré)

| Stratégie | Asymétrie | Survie (risque de ruine faible = 5) | Edge défendable | Compatibilité système | Total /20 |
|---|---|---|---|---|---|
| 13 Prévision calibrée Polymarket | 4 | 4 | 4 | 5 | **17** |
| 9 Swing directionnel filtré | 4 | 4 | 3 | 5 | **16** |
| 6 Polymarket–Kalshi avec lecture de règles | 3 | 4 | 3 | 3 | 13 |
| 5 Combinatoire Polymarket lent | 3 | 4 | 2 | 4 | 13 |
| 8 Momentum de liquidations | 4 | 2 | 1 | 2 | 9 |
| 1 Sniping | 5 | 1 | 1 | 1 | 8 |
| 7 News trading | 3 | 2 | 1 | 1 | 7 |

### Matrice B — Préservation et déploiement de gros capitaux

| Stratégie | Régularité | Scalabilité | Risque de ruine faible | Compatibilité système | Total /20 |
|---|---|---|---|---|---|
| 11a T-bills tokenisés / prêt de stablecoins de premier rang | 5 | 5 | 4 | 4 | **18** |
| 3 Portage de financement delta neutre | 3 | 4 | 3 | 3 | **13** |
| 9 Swing filtré (taille réduite) | 2 | 3 | 4 | 5 | 14 |
| 11b LP / rendement DeFi exotique | 2 | 3 | 2 | 3 | 10 |
| 4 Market making | 4 | 4 | 2 | 1 | 11 |

Note : « zéro risque de ruine » n'existe pas. Le piratage de Binance rappelle que même la stratégie la plus prudente porte un risque de contrepartie ; la diversification des plateformes et la garde des fonds font partie de la stratégie.

### Recommandation (position du conseil, confiance ≈ 65 % que ce choix surpasse les alternatives sur six mois, base : jugement qualitatif sur les matrices, non backtesté)

1. **Prévision calibrée Polymarket avec lecture des règles (chaîne P1 enrichie).** Ajout à `analyse-polymarket` : grille de risque de résolution (formulation, source, précédents UMA), contrôle de somme des issues et des marchés liés, journal de calibration (estimation contre issue) exploité par `revue-performance`. Condition bloquante : accès depuis les Émirats vérifié.
2. **Swing directionnel filtré par le régime et le positionnement (chaîne T1 enrichie).** Ajout à `analyse-actif` : feu de régime issu de la synthèse (taux, flux ETF, dominance) et filtre de positionnement (financement, OI, part d'acheteurs). En régime d'aversion, seuls les trades à ratio ≥ 3 ou les thèses baissières passent. Condition : un connecteur dérivés (CoinGlass) pour sortir des chiffres contradictoires d'OI.

Écartées pour l'instant : portage de financement (pertinent pour la matrice B mais exige plusieurs plateformes, un capital renseigné et une gestion de marge active, à rouvrir quand `commun-trading` § 3 sera complet) ; toutes les stratégies à latence.

**Ce qui ferait changer cette position :** un accès Polymarket impossible depuis les Émirats (la priorité 1 passerait au portage de financement) ; une revue montrant une calibration mauvaise sur vingt prévisions ou plus.

---

## Contrôle de fin (`cerveau-trading` § 4)

1. Skills ouverts : `cerveau-trading`, `commun-trading`, `veille-macro-crypto`, `synthese-marche`, `conseil-trading` (lus le 31/10). Les versions installées de `cerveau-trading` et `commun-trading` sont encore les 1.0.
2. Chiffres sourcés et datés ; lacunes marquées entre crochets (financement Bybit et Hyperliquid, carte des liquidations, BCE, BoJ, flux memecoins, IA, L2).
3. Avocat du diable : intégré au volet 2 (pas de thèse de trade à contredire dans cette chaîne).
4. Règles de risque : aucune taille calculée ; aucune position proposée.
5. Journal : une ligne `analyse` est à ajouter (dossier racine non accessible depuis le chat).
6. Aucun ordre passé.
