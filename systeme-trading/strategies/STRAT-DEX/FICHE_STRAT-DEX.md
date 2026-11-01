# STRAT-DEX — Rétro-ingénierie de wallets Solana (pump.fun, Raydium)

Statut : **recherche**. Mandat : `MISSION_REVERSE_ENGINEERING_WALLETS.md` (Téo et Jonathan, 01/11/2026). Aucun capital, aucune clé, aucun wallet de trading, `dry_run: true`.

Protocole écrit et poussé le 01/11/2026 avant toute lecture de la cohorte. Une donnée non vérifiée est entre crochets. Ces résultats ne sont pas une recommandation d'investissement.

## 1. Avertissements à lire d'abord

**Décision antérieure.** Le journal du 01/11/2026 indique que Jonathan et Téo ont abandonné l'approche par les wallets car elle est circulaire. Cette mission, plus récente, la rouvre. La circularité reste le risque central : choisir les gagnants puis étudier ce qu'ils ont fait explique le passé sans rien prédire. Le test de persistance du § 6 sert à la mesurer.

**Tri T1 à T10 de `validation-edge` § 0 bis.**

| N° | Lecture | Résultat |
|---|---|---|
| T1 | Contrepartie : acheteurs tardifs de memecoins. Nommée, mais la contrainte qui les force reste à démontrer | Passe, faiblement |
| T2 | Mouvements souvent supérieurs à 3 fois un coût de 2 % l'aller-retour [coût réel à mesurer] | Passe |
| T3 | Beaucoup de décisions possibles, à condition d'avoir la durée | Passe |
| T4 | Les wallets morts et les jetons disparus manquent au tirage. Biais non corrigible avec ces sources | **Non** |
| T5 | Les filtres retirent les stratégies de vitesse. Reste à vérifier sur les survivants | À vérifier |
| T6 | Long seul, RPC et DEX accessibles [statut légal par pays non vérifié] | Passe |
| T7 | Perte bornée à la mise, jusqu'à -100 % en cas de rug, sans stop fiable | Passe par la taille seule |
| T8 | Paramètres fixés sur les survivants, risque élevé | **Présomption** |
| T9 | Proche de la « copie de baleines » et du « suivi d'initiés » rejetés dans la note de régime | **Non probable** |
| T10 | Dépendance probable au régime des memecoins | À vérifier |

Le tri écarterait l'idée sur T4 et sans doute sur T9. Le travail se poursuit uniquement parce que la mission le demande explicitement, avec le statut `recherche`.

**Réserve de l'étude par les tokens.** `recherche/dex_faisabilite/` gardait septembre 2025 à octobre 2026 comme réserve non lue. Ce pilote lit octobre 2026 sur un échantillon de jetons. Ce mois n'est donc plus aveugle pour cette étude.

**Sources.** Aucune clé Dune, Helius ou Solscan n'est disponible. pump.fun et Solscan refusent l'accès public (403 et 401, 01/11/2026 12:58 UTC, depuis le serveur). Les sources réelles sont le RPC public Solana et GeckoTerminal. Le RPC met environ 3,6 s par `getTransaction` (60 appels en 217,8 s). Un classement des meilleurs wallets sur 90 jours n'est donc pas atteignable. Le pilote porte sur 30 jours et sur un tirage aléatoire.

## 2. Cohorte

1. Graines : pools dont le jeton de base est un mint suffixé `pump`, pris sur `pumpswap`, `pump-fun` et `raydium`, triés par volume 24 h (GeckoTerminal). Les trades publics de ces pools de 50 $ ou plus donnent les wallets. Le tirage ne regarde aucun gain.
2. Tirage aléatoire de 400 wallets, graine 20261101.
3. Période : les 30 jours avant le tirage.
4. Budget : 8 000 transactions. Un wallet à plus de 400 signatures réussies sur 30 jours est classé `hors_budget`. Ce n'est pas une preuve de MEV, et le compte est publié.
5. Une position est un couple wallet et jeton, datée de son premier achat. Tout achat en SOL, wSOL, USDC ou USDT compte. Un jeton vendu sans achat vu est exclu pour coût inconnu.
6. Le reliquat non vendu est valorisé au prix actuel GeckoTerminal, et à zéro sans prix. Sans cela, les jetons morts cacheraient les pertes.

## 3. Filtres d'exclusion, figés

| Filtre | Règle | Limite connue |
|---|---|---|
| F1 snipers | Au moins un achat à 2 s ou moins de la création d'un pool du jeton | `pool_created_at` a une précision à la seconde |
| F2 dev | Le wallet a créé un jeton acheté, ou a reçu du SOL directement de son déployeur | Déployeur non trouvé au-delà de 3 pages de signatures, compte publié |
| F2 cluster | Un financeur partagé par au moins 2 wallets de l'échantillon, hors financeur très actif (1 000 signatures en moins de 24 h, lu comme une plateforme) | Heuristique. Financement avant la période invisible |
| F3 MEV | 20 transactions ou plus dans une même minute, ou frais de priorité médians supérieurs à 0,01 SOL | Seuils de jugement |

## 4. Rentabilité

Wallet **rentable** : au moins 5 positions, P&L total positif et profit factor supérieur à 1, après frais de réseau et reliquats valorisés.

## 5. Facteurs

Calculés pour les **gagnants et les perdants** qui passent les filtres. Décrire les gagnants seuls serait du biais du survivant.

FDV à l'entrée, position par rapport à la création du pool de migration, cassure (prix à 95 % ou plus du plus haut de 24 h), repli (70 % ou moins), volume horaire à l'entrée, durée de détention, perte à la sortie, ventes échelonnées, multiple à la première vente, taux de réussite, profit factor, gain moyen sur perte moyenne.

## 6. Test de persistance

Période A : J-30 à J-16. Période B : J-15 à J. Wallets avec au moins 3 positions dans chaque période. Mesures : corrélation de rang des rendements et part de wallets positifs en B selon le signe en A, avec test de Fisher. Sans différence détectable, le pilote n'apporte aucune preuve de compétence répétable. Vu la taille attendue, l'absence de signal ne prouve pas non plus l'absence de compétence.

## 7. Stratégie et simulation

Les paramètres de `parametres_geles.json` sont figés une seule fois après lecture du § 5, à partir des **médianes** des rentables, sans recherche sur grille. Chaque valeur compte comme un paramètre libre.

La simulation avance dans le temps sur le serveur, sans signature ni envoi de transaction. Elle compte 1 % de coût par côté, plus l'impact estimé. Une position sans pool lisible ou avec moins de 1 000 $ de réserve est soldée à -100 %.

**Critère d'échec.** Après 8 semaines au moins et 30 trades au moins : espérance nette inférieure ou égale à 0,2 R, ou borne basse de l'intervalle à 90 % inférieure ou égale à 0, ou drawdown supérieur à 20 %, ou espérance négative à coûts doublés. Le R vaut la distance au stop. Toute modification de règle est une nouvelle stratégie. Aucune promotion sans dossier de `validation-edge` et accord de Jonathan.

## 8. Avocat du diable avant données

Verdict préliminaire : hypothèse **affaiblie**.

1. Survivants : le tirage ne voit que des wallets actifs aujourd'hui. Les comptes vidés et abandonnés manquent.
2. Une même personne peut utiliser plusieurs wallets, et les transferts faussent les coûts.
3. Un petit nombre de gains extrêmes domine les rendements memecoin. La médiane et la moyenne divergent fortement.
4. Sur 30 jours, un rentable peut être chanceux. Le taux de base de la radiographie (84 % de perdants sur Polymarket) ne se transpose pas sans preuve, mais il rappelle l'ordre de grandeur attendu.
