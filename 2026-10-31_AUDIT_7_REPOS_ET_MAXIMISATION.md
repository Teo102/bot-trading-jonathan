# Audit des 7 dépôts et maximisation du cash — 31/10/2026

Chaîne : C1 (`conseil-trading`) sous `cerveau-trading`. Heures en UTC. Donnée non vérifiée = entre crochets. Les chiffres de simulation dépendent d'hypothèses écrites ; aucun n'est une promesse de gain.

---

## 0. Corrections et cadrage

**Le tweet.** J'avais supposé qu'il parlait du protocole SQD (Subsquid), parce qu'il venait de ce compte. C'était une erreur. Le tweet liste 7 dépôts GitHub de trading assisté par IA. Mon analyse SQD reste juste pour SQD, mais elle ne répondait pas au tweet.

**Émirats.** La résidence aux Émirats est désormais une donnée, à inscrire dans `commun-trading` § 1.
- Polymarket n'y est pas géobloqué et ne figure pas sur sa liste de pays restreints (nextpredict.io, 07/08/2026 ; polymarket.review, 17/08/2026).
- « 100 % légal » est en revanche trop fort. Le droit fédéral interdit les jeux d'argent hors licence GCGRA, et aucun texte ne qualifie les marchés de prédiction. Les sources parlent de **zone grise**, sans poursuite connue contre un particulier (tradetheoutcome.com, neoslegal.co).
- L'accès est donc ouvert et le risque légal paraît faible, sans être nul. La décision appartient à Jonathan.
- Fiscalité : pas d'impôt personnel sur le revenu aux Émirats selon plusieurs sources [statut de résident fiscal à confirmer].

**Le compounding.** Ma simulation précédente réinvestissait déjà les gains : chaque mise valait un pourcentage du capital courant. Les ≈ 90 € par mois ne venaient pas d'une absence de réinvestissement. Ils venaient de **6 trades par mois sur 5 000 €**. Les trois vrais leviers sont l'edge par trade, le nombre de trades et la taille par trade. Ils sont chiffrés aux § 2 et 3.

**Règle « aucun ordre ».** `cerveau-trading` interdit tout ordre. Brancher freqtrade ou hummingbot en réel change ce mandat. La proposition du § 4 garde les skills sans exécution : un bot séparé, piloté et détenu par Jonathan, exécute, et aucune clé n'entre jamais dans Claude. Cette modification de règle appartient à Jonathan (`cerveau-trading` § 6).

---

## A. Audit des 7 dépôts

Les étoiles du tweet ne sont pas vérifiées à la date du jour. Les sources consultées en donnent d'autres pour TradingAgents (de 75 557 à 103 000 selon la date). **Les étoiles mesurent la popularité, pas la rentabilité.**

| Dépôt | Nature réelle | Exécution réelle | Preuve de rentabilité publiée | Verdict pour nous |
|---|---|---|---|---|
| TradingAgents | Cadre de recherche : agents LLM (analystes, débat haussier/baissier, trader, gestion du risque), article arXiv 2412.20138, Apache-2.0 | **Aucune** connexion courtier, aucun routage d'ordres (MoClaw) | Aucun historique réel. Un backtest AAPL de 6 mois annonce un Sharpe de 8,21 et un drawdown de 0,91 % (PickMyTrade) | **Hype pour le cash.** Un Sharpe de 8 sur 6 mois signale un biais, pas un edge : le LLM a souvent « vu » la période testée pendant son entraînement |
| ai-hedge-fund | Preuve de concept : agents qui imitent des investisseurs célèbres, actions US | **Aucune** : le dépôt précise que le système ne passe pas d'ordre | Aucune ; usage éducatif seulement | **Coquille pédagogique.** Seule l'idée d'une validation (CPCV, PBO) avant promotion d'une stratégie est à retenir |
| freqtrade | Bot crypto mature (version 2026.8 sur PyPI) : backtest, hyperopt, papier (dry-run), réel, Telegram, FreqAI | **Oui**, spot et contrats à terme (« expérimental » pour les futures) | Outil, pas stratégie : la rentabilité dépend de la stratégie écrite | **Moteur de production réel.** Son point fort : `lookahead-analysis` et `recursive-analysis` détectent les backtests qui trichent. Hyperliquid [support à confirmer dans la doc « exchanges »] |
| qlib (Microsoft) | Plateforme de recherche quantitative ML, surtout actions | Non (recherche) | Résultats académiques sur actions | **Robuste mais hors sujet** pour la crypto et Polymarket à court terme |
| Kronos | Modèle de fondation pour bougies, pré-entraîné sur plus de 12 Md de bougies de 45 places (NeurIPS 2025, atelier) | Non | Gain de RankIC annoncé (+93 % contre le meilleur modèle généraliste), **pas un P&L net de frais** | **Recherche sérieuse, pas un edge prêt.** À tester comme variable dans FreqAI, après le reste |
| AI-Trader (HKUDS) | Cadre et banc d'essai d'agents de trading autonomes | [non vérifié en détail] | [aucune trouvée] | **Non prioritaire** |
| hummingbot | Cadre mature de market making : plus de 300 connecteurs, connecteurs Hyperliquid spot et perps maintenus | **Oui** | Stratégie gagnante d'un concours : plus de 120 000 $ de volume sur Hyperliquid avec quelques milliers de dollars, **P&L à peu près nul** (podcast Hummingbot) | **Robuste, mais le market making de détail rapporte peu.** Utile plus tard ; aucun connecteur Polymarket confirmé |

**TradingAgents et ai-hedge-fund face aux skills de Jonathan.** L'architecture est la même : analystes (`analyse-actif`, `veille`), débat (`avocat-du-diable`, `conseil-trading`), gestionnaire de risque (`risque-position`), trader (`fiche-trade`).

Le système de Jonathan est **plus strict** sur trois points : données datées et sourcées, contradiction obligatoire, journal. Les deux dépôts ne l'enrichissent pas sur le fond. Ils partagent aussi la même faiblesse : **aucun ne prouve un edge**. Ajouter des agents LLM qui débattent ne crée pas d'avantage statistique.

**Ce que freqtrade apporte sans réinventer la roue.**
1. Données historiques et backtest avec frais réels.
2. Contrôle des biais d'anticipation.
3. Hyperopt, à manier avec prudence : optimiser beaucoup de paramètres sur peu de données fabrique un edge fictif.
4. Dry-run sur flux réel, qui sert de papier.
5. Réel avec stops et levier configurés.

---

## B. Polymarket : maximiser le cash

### B.1 Comment gagnent réellement les gros portefeuilles

- **Concentration extrême.** Sur les marchés politiques de décembre 2025 à février 2026, 0,55 % des portefeuilles makers gagnants ont capté 50 % des gains, soit ≈ 8 M$ sur ≈ 16 M$. Côté takers, 0,26 % des gagnants en ont capté presque autant (Solidus Labs, via CoinDesk, 29/04/2026). Environ 15 % du volume de certains marchés ressemble à du wash trading.
- **Trois profils** ressortent d'un audit de 40 portefeuilles (leolabs, janvier à mars 2026) :
  - **Volume énorme à marge minuscule** : « swisstony », 494 M$ échangés, ≈ 1 % de rendement, 4,96 M$ de profit, entièrement automatisé.
  - **Market maker sur les options binaires BTC à 5 ou 15 minutes**, actif jour et nuit.
  - **Paris dirigés et concentrés** fondés sur une connaissance de niche, par exemple 1,58 M$ sur un match de League of Legends.
  - Plus de 70 % des profits d'arbitrage crypto iraient à des bots de latence inférieure à 100 ms.
- **Persistance.** Parmi les portefeuilles ayant au moins 10 trades en juin et en juillet 2026, 124 des 137 gagnants de juin ont de nouveau gagné en juillet (Vultax, 9 902 portefeuilles). C'est un indice qu'une compétence existe et persiste chez les actifs [fenêtre courte, biais de sélection possible].
- **Taux de base** : 84,1 % des 2,5 millions de portefeuilles perdent ; 2 % ont gagné plus de 1 000 $ (Sergeenkov, avril 2026).

**Calcul clé.** Faire 10 000 $ par mois avec une marge de 1 % demande **1 M$ de volume mensuel**. Sur 5 000 $, cela fait **200 rotations du capital par mois**. Ce rythme n'existe que sur des marchés ultra-courts (5 à 15 minutes), tenus par des bots à latence très faible. Les portefeuilles à 10 000–50 000 $ par mois combinent donc gros capital, infrastructure et volume, ou bien de rares paris d'information concentrés.

### B.2 Les frais de 2026 changent les calculs

- Les takers paient `parts × taux × p × (1 − p)`, soit un maximum de 1 à 1,75 cent par part à 50 cents selon la catégorie. Le sport est passé de 0,03 à 0,05 en juillet 2026. La géopolitique reste sans frais (startpolymarket.com, octobre 2026).
- Les makers ne paient rien et reçoivent une part des frais takers : 25 % dans la plupart des catégories, 20 % en crypto, 15 % en sport. Ils reçoivent en plus des récompenses de liquidité quotidiennes pour des ordres placés près du milieu de carnet.
- **Conséquence.** Avec un taux de 0,04, un taker à 50 cents paie 1 cent par part, soit 2 % de la mise. L'arbitrage « somme des prix ≠ 1 » en taker, qui rapportait 1 à 5 %, est **en grande partie effacé**. L'edge passe par les ordres à cours limité (maker), avec leur antisélection.

### B.3 Les stratégies demandées, passées au crible

| Stratégie | Mécanique | Faille principale | Verdict |
|---|---|---|---|
| Rotation rapide (turnover) | Marchés courts, recyclage du capital | Les marchés de 5 à 15 minutes appartiennent aux bots à faible latence ; frais crypto pour les takers | Seulement sur des marchés de **jours ou semaines** où le jugement compte |
| Kelly fractionné | Mise f = κ·(q − p)/(1 − p) | **Une surestimation de l'edge ruine** (simulation ci-dessous) | Kelly/4 tant que la calibration n'est pas mesurée |
| Récompenses de liquidité et rebates makers | Ordres limités près du milieu de carnet | Antisélection : l'ordre est pris quand l'information arrive ; marchés à information soudaine dangereux | Complément réel sur des marchés lents (politique longue durée, macro) ; [rendement non chiffrable sans données de pool] |
| Arbitrage combinatoire | Incohérences entre marchés liés | Frais takers, jambes non remplies, **règles de résolution différentes** | Valable en maker et sur des incohérences lentes ; exige la lecture des règles |
| Arbitrage de clôture | Achat à 97–99 cents d'issues quasi certaines | Gain de 1 à 3 % ; une seule surprise ou un seul litige UMA efface des dizaines de gains | Petite taille seulement ; grille de résolution obligatoire |

### B.4 Simulation : Kelly, compounding et frais réels

Hypothèses : 40 paris par mois, prix entre 0,3 et 0,7, marchés indépendants (hypothèse **optimiste**), 12 mois, mise plafonnée à 25 %.

| Cas | Médiane 1 an | 5e centile | P(perte) | Drawdown médian | P(capital −50 % à un moment) |
|---|---|---|---|---|---|
| Maker, edge réel 3 pts, estimé 3, Kelly/2 | +100 % | −36 % | 16 % | 42 % | 8 % |
| Maker, edge réel 3 pts, **estimé 6**, Kelly/2 | +156 % | −74 % | 24 % | 70 % | 38 % |
| Maker, edge réel 3 pts, **estimé 6, Kelly plein** | +2 % | −99 % | 50 % | 95 % | **78 %** |
| Taker (frais 2026), edge 3 pts, Kelly/2 | +38 % | −35 % | 24 % | 33 % | 4 % |
| Maker, **edge réel nul**, estimé 4, Kelly/2 | −34 % | −85 % | 68 % | 70 % | 59 % |
| Maker, edge réel 5 pts, Kelly/4 | +208 % | +22 % | 2 % | 30 % | 1 % |

**Illusions détruites.**
1. Avec du compounding, **l'edge supposé décide de tout**. Un edge nul que l'on croit à 4 points, joué à Kelly/2, fait perdre 34 % en médiane avec 59 % de risque de passer sous la moitié du capital.
2. Surestimer l'edge du double en Kelly plein mène à **78 % de risque de −50 %**.
3. Les médianes à trois chiffres supposent **40 paris indépendants par mois avec un edge constant**. Les marchés sont corrélés, la liquidité limite la taille, et l'edge s'érode. Ces médianes sont un **plafond théorique**, pas une prévision.

**P&L à viser, avec 5 000 $ et 20 000 $ réinvestis.** Le point de départ honnête est simple : l'edge réel est **inconnu** tant que la calibration n'a pas été mesurée sur au moins 100 prévisions.

| Phase | 5 000 $ | 20 000 $ | Condition |
|---|---|---|---|
| Mois 1–2 : mesure (Kelly/4, maker) | De −10 à +10 % [le but est de mesurer, pas de gagner] | idem | Journal de calibration complet |
| Si edge mesuré ≈ 3 pts : Kelly/4 à Kelly/2 | Ordre de grandeur annuel +40 à +100 %, avec des drawdowns de 30 à 40 % | Rendement en % plus faible, la liquidité limite la taille | Intervalle de confiance de l'edge au-dessus de 0 |
| Si edge mesuré nul | Arrêt du moteur | Arrêt | Règle d'arrêt de `revue-performance` |

---

## C. Trading pur à plus forte fréquence

Simulation avec frais taker de 0,045 % et glissement de 0,03 % par côté [ordre de grandeur Hyperliquid, à vérifier], 1 % de risque par trade, 12 mois.

| Cas | Coût par trade | Médiane | 5e centile | P(perte) | P(−50 %) |
|---|---|---|---|---|---|
| Swing, 6 par mois, stop à 4 %, 40 % gagnants à 2R | 0,04 R | +11 % | −10 % | 21 % | 0 % |
| Swing, 20 par mois, stop à 2 %, 40 %/2R | 0,07 R | +30 % | −12 % | 14 % | 0 % |
| Swing, 20 par mois, 40 %/2R, risque 2 % | 0,07 R | +59 % | −26 % | 16 % | 2 % |
| **Intraday, 100 par mois, stop à 0,6 %, 40 %/2R** | **0,25 R** | **−54 %** | −81 % | 92 % | **69 %** |
| Intraday, 100 par mois, stop à 0,6 %, 45 %/2R | 0,25 R | +178 % | +15 % | 3 % | 1 % |
| Intraday maker (frais nuls), 40 %/2R | 0,03 R | +509 % | +151 % | 0 % | 0 % |

**Lecture sans complaisance.**
1. **En intraday, les coûts mangent l'edge.** Un stop serré multiplie le levier et donc les frais par trade (0,25 R). Avec 40 % de gagnants, c'est la ruine. Avec 45 %, c'est la fortune. Cinq points de taux de réussite séparent les deux mondes, et **il faut des centaines de trades pour savoir de quel côté on se trouve**.
2. **Le cas maker « +509 % » est une illusion** : il suppose que les ordres limites sont remplis sans antisélection. En réalité, l'ordre est rempli surtout quand le prix part contre lui. La stratégie gagnante du concours Hummingbot a fini à **P&L à peu près nul**.
3. **La voie réaliste vers plus de cash** : swing de fréquence moyenne (15 à 25 trades par mois, sur plusieurs actifs), backtesté et validé, puis montée progressive du risque de 1 à 2 % **seulement si** l'edge est confirmé.

**Stratégies quantitatives candidates, à tester dans freqtrade avant tout capital :**
- tendance multi-actifs (cassure de canal plus filtre de régime) sur BTC, ETH, SOL et des alts liquides ;
- retour à la moyenne après liquidations extrêmes, filtré par le financement ;
- filtre de financement et d'OI : pas de long quand le financement est extrême ;
- portage de financement (delta neutre), comme moteur de rendement régulier.

---

## D. Stack et recommandation opérationnelle

### D.1 Stack retenue

| Couche | Outil | Rôle |
|---|---|---|
| Cerveau (analyse, contradiction, risque, journal) | **Skills de Jonathan** | Décision, documentation, revue ; aucun ordre |
| Backtest, papier, exécution du trading pur | **freqtrade** | Backtests avec frais et contrôle des biais ; dry-run ; réel plus tard, opéré par Jonathan sur sa machine |
| Données | Connecteurs Crypto.com et CoinGecko ; SQD (Hyperliquid on-chain) ; jeu de données Polymarket sur Hugging Face pour la calibration | Données sourcées et datées |
| Polymarket | **Ordres manuels en maker**, puis éventuellement un client officiel [non audité] | Prévisions calibrées et récompenses de liquidité |
| Rejetés pour l'instant | TradingAgents, ai-hedge-fund, AI-Trader, qlib | Aucun edge démontré, rien d'exécutable ou hors sujet |
| Plus tard | hummingbot, Kronos | Market making et variables ML, une fois l'edge de base prouvé |

### D.2 Plan des prochaines semaines

1. **Semaine 1**
   - Résidence (Émirats) et paramètres de risque inscrits dans `commun-trading` 1.2.
   - Installation de freqtrade (Docker), téléchargement de 2 à 3 ans de données.
   - Polymarket : premières prévisions en Kelly/4 maker sur des marchés lents, journal de calibration.
2. **Semaines 2 à 3**
   - Backtests de 3 à 4 stratégies swing, avec `lookahead-analysis` obligatoire.
   - Validation : au moins 100 trades, espérance nette supérieure à 0,2 R, drawdown inférieur à 20 %, test hors échantillon.
3. **Semaines 3 à 8**
   - Dry-run des stratégies validées.
   - Polymarket : passage à Kelly/2 seulement si l'intervalle de confiance de la calibration est au-dessus de zéro.
4. **Ensuite**
   - Réel à 0,5 % de risque par trade, puis 1 %, puis 2 % selon la revue.

**Ce qui peut produire du cash le plus tôt** : Polymarket en maker, en petite taille, sur des marchés que Jonathan connaît mieux que la moyenne. C'est aussi le moteur au risque d'erreur d'estimation le plus élevé. Le swing automatisé demande 4 à 8 semaines de validation avant le premier euro réel.

### D.3 Sécurité

- Aucun bot téléchargé sans lecture du code. Des dépôts « bots Polymarket » malveillants ont volé des clés (StepSecurity).
- Clés d'API en lecture et en trading uniquement, **jamais** en retrait. Aucune clé dans Claude.
