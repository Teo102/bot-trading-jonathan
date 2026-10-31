# Audit de 5 tweets sur le trading par IA — 31/10/2026

Chaîne : C1 (`conseil-trading`) sous `cerveau-trading`. Donnée non vérifiée = entre crochets. Aucun chiffre n'est une promesse de gain.

---

## 0. Contexte vérifié

- **Grok Bot** est un produit de xAI (devenu SpaceXAI), lancé en bêta le 11/08/2026. Ce sont des agents qui travaillent sur leur propre ordinateur dans le cloud, se coordonnent en groupes et demandent une approbation quand c'est nécessaire (BusinessToday, Pondero). Le prix serait d'environ 120 $ par utilisateur et par mois [une seule source, en hébreu].
- **Lecture d'ensemble.** Trois des cinq tweets (1, 3 et 5) mettent Grok Bot en scène avec des gains spectaculaires et sans preuve, autour d'un produit récent et payant. Ce schéma correspond à une campagne de promotion. Une rémunération n'est pas démontrée [non vérifiable].

---

## 1. Démontage tweet par tweet

### Tweet 1 — @Greshamtrade : 1 153 $ → 3 874 $ en une journée, « les 4 bots doivent être d'accord »

| Élément | Verdict |
|---|---|
| +236 % en un jour | **Invérifiable et sans valeur statistique.** Un seul jour, aucun relevé d'exécution, aucun levier indiqué. Un tel résultat est compatible avec un levier élevé et de la chance |
| « 4 bots doivent être d'accord » | **Fausse sécurité.** Quatre agents reposant sur le même modèle, alimentés par les mêmes données, sont **corrélés**. Leur accord ne vaut pas quatre validations indépendantes. Un filtre en « ET » réduit le nombre de trades, il ne crée pas d'edge |
| Le dépôt cité (HyperGrok) | **Ne correspond pas au tweet.** Il décrit 7 rôles et une **approbation humaine** par ticket, pas un vote à 4. Il ne fait aucune promesse de rendement (ticket GitHub n° 38) et n'a que 83 étoiles |
| Conseils finaux (un seul moteur d'exécution, un seul émetteur d'ordres, vérifier les exécutions réelles, chaîne d'approbation avant toute nouvelle source de signal) | **Solides.** Ce sont de vraies règles d'ingénierie de desk |
| Liste des 10 dépôts | Mélange d'outils sérieux (CCXT, freqtrade, LEAN, backtesting.py, hummingbot, OpenBB) et de projets de recherche (TradingAgents, qlib, FinRL). Aucun ne fournit d'edge |

### Tweet 2 — @carm1nee : « 10 dépôts = un hedge fund, 0 $ contre 32 000 $ pour Bloomberg »

- **Comparaison trompeuse.** Le logiciel n'a jamais été l'avantage d'un fonds. Ses avantages sont les données propriétaires, l'exécution, le capital, le risque et des chercheurs qui écartent les fausses découvertes.
- **« 575 000 étoiles »** : les étoiles mesurent la popularité, pas la rentabilité.
- **« Buffett, Munger et Druckenmiller en agents IA »** renvoie à ai-hedge-fund, dont le dépôt dit lui-même qu'il est éducatif et ne passe aucun ordre.
- **Verdict** : du marketing, sans affirmation testable.

### Tweet 3 — @RohOnChain : « un bot teste toute la nuit toutes les stratégies »

C'est le piège le plus dangereux, parce qu'il a l'air rigoureux. Tester beaucoup de stratégies sur les mêmes données **garantit** d'en trouver une excellente par hasard. Simulation : 365 jours de rendements, aucune stratégie n'ayant d'edge.

| Stratégies testées | Meilleur Sharpe annualisé trouvé (médiane) | 95e centile |
|---|---|---|
| 1 | ≈ 0 | 1,63 |
| 20 | 1,80 | 2,89 |
| 100 | 2,50 | 3,35 |
| 500 | 3,02 | 3,72 |
| 2 000 | 3,43 | 4,15 |

**Conséquence.** Un « Sharpe de 3 » sorti d'un balayage nocturne de 500 stratégies est du **bruit**. Toute recherche automatisée exige un nombre d'essais déclaré, une période hors échantillon jamais vue et une correction pour tests multiples (Sharpe déflaté, test de White). Sinon, le bot produit des stratégies qui échouent en réel.

### Tweet 4 — @RohOnChain : skill Claude à 11 agents + TradingView + Alpaca

| Élément | Verdict |
|---|---|
| Connecteur MCP officiel TradingView | **Réel.** Bêta publique depuis le 16/09/2026, URL `https://mcp.tradingview.com/mcp`, ajout comme connecteur personnalisé, **réservé aux abonnements Essential et plus** (tradingview.com/mcp/docs) |
| Fonctions | Cotations, historiques, screener, notes techniques, fondamentaux, listes de suivi et alertes. Pas de backtest documenté selon un concurrent (TradingMCP) [source intéressée, à vérifier] |
| « Backtest sur des années avec frais réels » | Possible seulement si un environnement exécute du code sur l'historique. Il faut un nombre d'essais limité et une période hors échantillon, sinon on retombe dans le piège du tweet 3 |
| Taille au Kelly | Kelly calculé sur des probabilités **estimées par un LLM** revient à surestimer l'edge, ce qui mène à la ruine (simulation précédente : 78 % de risque de −50 %) |
| « Trader 24/7 qui passe ses ordres seul » | Dans le chat, Claude agit quand il reçoit un message. Une boucle continue suppose un environnement d'exécution externe [détails produit : support.claude.com]. Le tweet montre lui-même Alpaca **en mode papier**, sur des actions US |
| « Coller le Trader Skill et taper install skill » | **Risque de sécurité** : une skill inconnue est du texte d'instructions, potentiellement une injection de prompt. Elle se lit avant d'être installée |
| Utile pour nous | Le **screener TradingView** pourrait alimenter les « opportunités à étudier » de `synthese-marche`. Le marché visé (actions US, Alpaca) n'est pas le nôtre |

### Tweet 5 — @0xTenzo : 74 $ → 8 273 $ en 12 heures sur des memecoins

**Arithmétique :**
- 74 $ multipliés par 111,8 en 12 heures.
- Les gains listés totalisent 7 481 $. Additionnés aux 74 $ de départ, on obtient 7 555 $, alors que le tweet annonce 8 273 $. **718 $ ne s'expliquent pas**, sans même compter la perte sur PODCAT.
- Le gain de FLUKE (+355 %) suppose une mise d'environ 839 $. La stratégie implicite est donc **tout le capital remis en jeu à chaque trade**.

**Probabilité.** Même avec une hypothèse très généreuse (30 % des memecoins choisis montent assez), obtenir au moins 5 gagnants sur 6 a une probabilité d'environ **1,1 %**.

**Biais du survivant.** Sur 100 comptes qui jouent ainsi, un seul publie ; les 99 autres se taisent.

**Taux de base des memecoins.**
- Taux de « graduation » pump.fun : **0,198 %** sur 832 941 lancements entre mai et juin 2026 (arXiv 2607.02823).
- Environ 68,7 % des 18,67 M de jetons lancés entre janvier 2024 et juin 2026 ont cessé de s'échanger **le jour même** [source KuCoin].
- Un graphique récent montre 73,3 % de traders gagnants en avril 2026 (CoinGecko). Mais ce chiffre ne compte que le **P&L réalisé** et exclut ceux qui gardent des jetons tombés à zéro ; 65 % des gagnants ont gagné entre 1 et 500 $.

**« Il a évité deux rug pulls »** : c'est une **narration après coup**. Aucune règle de filtrage n'est publiée, donc rien n'est testable.

**Verdict : ce tweet est de la promotion.** Le tirage est de type loterie, avec un risque de ruine quasi total à chaque trade.

---

## 2. Comparaison avec le système de Jonathan

| Fonction | Tweet 4 (11 agents) | HyperGrok (7 rôles) | Skills de Jonathan |
|---|---|---|---|
| Scanner | Screener TradingView | Market Analyst | `synthese-marche` (« opportunités à étudier ») ; **pas de screener chiffré** |
| Analyse | Analyst agent | Research Analyst | `analyse-actif`, `analyse-polymarket` |
| Contradiction | Absente | Le Risk Manager « peut dire non » | **`avocat-du-diable` obligatoire**, plus `conseil-trading` : le point le plus fort de Jonathan |
| Backtest | « Demander à Opus » | Strategist : frais, hors échantillon, distribution des trades | Absent (prévu : `validation-edge` plus freqtrade) |
| Taille | Kelly | **Stop stressé** (glissement et frais taker sur les deux jambes) | `risque-position` : **stop stressé intégré en v1.1** |
| Approbation | Implicite | **Ticket identifié, verrou d'approbation hors du chat** | `fiche-trade` v1.1 : ticket `TK-…` et approbation citant l'identifiant |
| Exécution | Agent courtier (papier) | **Un seul émetteur**, clé de trading sans droit de retrait, réseau de test d'abord | Aucune (règle « aucun ordre ») ; exécution externe par Jonathan |
| Réconciliation | Absente | Par identifiant client d'ordre | `journal-trading` v1.2 : **réconciliation sur l'exécution réelle** |
| Revue | Absente | **Processus et résultat notés séparément** | `revue-performance` v1.1 : matrice processus × résultat |

**Verdict.**
- Le tweet 4 est **inférieur** au système de Jonathan : il n'a ni contradiction, ni réconciliation, ni revue, et il fait du Kelly sur des probabilités de LLM.
- HyperGrok est **supérieur sur l'exécution** (ticket, émetteur unique, stop stressé, réconciliation, réseau de test). Le système de Jonathan est **supérieur sur l'analyse** (contradiction obligatoire, sources datées).
- Ni l'un ni l'autre n'a de preuve d'edge.

---

## 3. Outils à récupérer

**HyperGrok (galleonlabs/hypergrok-trading-desk)** : licence MIT, version 1.7.0 du 25/10/2026, 83 étoiles, 21 forks.
- Points forts : approbation par ticket appliquée hors du chat, clé de trading sans droit de retrait, taille sur stop stressé, plafonds qu'un fichier de limites peut seulement resserrer, réseau de test d'abord, un seul émetteur, revue processus/résultat. Il propose aussi un script en lecture seule, sans clé (`opening_bell.py`), qui donne prix, financement, OI et profondeur à 5, 10 et 25 points de base sur Hyperliquid. Les SDK Hyperliquid sont épinglés et relus.
- Limites : jeune, petite communauté, orienté Grok Bot. Le README affiche « Supported by the pump.fun community » [nature du lien non vérifiée].
- **Usage recommandé** : bibliothèque de référence pour le futur poste d'exécution Hyperliquid, plutôt que remplaçant du cerveau. Ses bonnes pratiques sont intégrées dans 4 skills (§ 4). Ses scripts en lecture seule peuvent tourner dans Claude Code ou Cowork. **Aucune clé** n'entre dans Claude.

**Connecteur TradingView (officiel)** : utile si Jonathan a déjà un abonnement Essential ou plus.
- Apport : screener et alertes pour le scanner, et données de cotation croisées avec Crypto.com.
- Coût : l'abonnement.
- Priorité : **moyenne**.

**OpenBB MCP** : serveur **local** (`pip install openbb-mcp-server`), pas un connecteur hébergé.
- En crypto, il fait doublon avec CoinGecko, déjà connecté.
- Seul apport réel : la macro FRED dans Claude Code ou Cowork.
- Priorité : **basse**.

**CCXT, backtesting.py, LEAN, FinRL**
- **CCXT** : interface commune vers les plateformes ; freqtrade l'utilise déjà.
- **backtesting.py** : léger, pratique pour des tests rapides.
- **LEAN** : moteur professionnel multi-actifs, plus lourd.
- **FinRL** : apprentissage par renforcement, très exposé au surajustement.
- Priorité : freqtrade suffit. backtesting.py reste en option pour des prototypes rapides.

---

## 4. Intégration de la chaîne de validation dans le cerveau

L'idée « Scanner → Analyste → Exécuteur → Risque » existe déjà dans la chaîne T1, sous une forme plus stricte. Il ne manquait que les garde-fous d'exécution.

```
synthese-marche (scanner) → analyse-actif (analyste) → avocat-du-diable (contradiction)
→ risque-position (stop stressé) → fiche-trade (ticket TK-…) → approbation de Jonathan
→ exécution externe (un seul émetteur) → journal-trading (réconciliation) → revue-performance
```

**Livré dans cette séance (zips) :**
- `risque-position` 1.1 : taille sur stop stressé ; limites qui ne peuvent que se resserrer.
- `fiche-trade` 1.1 : ticket identifié ; approbation valable seulement si elle cite l'identifiant.
- `journal-trading` 1.2 : réconciliation sur l'exécution réelle ; marque [non réconciliée].
- `revue-performance` 1.1 : processus et résultat notés séparément.

**Point de vigilance.** Un vote d'accord entre agents ne remplace pas la contradiction. La validation indépendante vient de trois sources : des **données hors échantillon** (backtest), une **règle de risque codée** (plafonds) et un **humain** qui approuve un ticket précis.

---

## 5. Feuille de route : ce qu'on garde, ce qu'on jette

| On garde | Origine | Statut |
|---|---|---|
| Ticket identifié et approbation hors du chat | HyperGrok | Intégré (`fiche-trade` 1.1) |
| Taille sur stop stressé | HyperGrok | Intégré (`risque-position` 1.1) |
| Un seul émetteur d'ordres, réconciliation sur exécution réelle | Tweet 1 et HyperGrok | Intégré (`journal-trading` 1.2) |
| Revue processus/résultat | HyperGrok | Intégré (`revue-performance` 1.1) |
| Clé de trading sans droit de retrait, réseau de test d'abord | HyperGrok | À inscrire dans `commun-trading` 1.2 |
| Screener TradingView pour le scanner | Tweet 4 | Optionnel (abonnement) |
| Correction pour tests multiples dans tout backtest | Leçon du tweet 3 | À inscrire dans `validation-edge` |

| On jette | Raison |
|---|---|
| Gains d'une journée ou de 12 heures comme preuve | n = 1, invérifiable, biais du survivant |
| Vote d'accord entre agents comme validation | Agents corrélés |
| Balayage nocturne de centaines de stratégies sans correction | Le meilleur Sharpe sur 500 stratégies sans edge vaut ≈ 3 |
| Kelly sur des probabilités de LLM | Surestimation de l'edge, ruine |
| Memecoins en mise totale | Probabilité de réussite ≈ 1 %, ruine quasi certaine |
| Installation de skills ou de bots inconnus sans lecture | Injection de prompt, vol de clés |
