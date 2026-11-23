# Tri de nouvelles pistes (H37 à H46), 23/11/2026

Écrit le 23/11/2026 par Claude, à la demande de Jonathan et Téo, selon la grille T1 à T10 de `validation-edge` § 0 bis. **Aucune donnée lue, aucun rendement calculé.** Les références de littérature sont citées de mémoire [non relues ici]. Résultat de recherche : aucun ordre, aucune recommandation d'investissement.

## Ce que les échecs récents imposent

Onze hypothèses ont été testées sur des rendements, aucune n'est passée. Trois causes reviennent :
1. **Les frais de rotation** tuent les écarts qui se referment vite (financement : H02, H10, H20, H31 ; liquidations : H32).
2. **Les alts spéculatives** donnent des résultats concentrés sur une année et quelques noms (H12, H31, leçon L13).
3. **L'accès** bloque les pistes les plus propres (Polymarket H24 et H25, options H34).

Une nouvelle piste doit donc avoir un payeur clair, peu de rotation, un historique de plusieurs cycles et un accès simple depuis la France et les Émirats.

## Les dix pistes

| N° | Piste | Payeur (T1) | Point faible | Verdict du tri |
|---|---|---|---|---|
| **H37** | **Exposition BTC (et ETH) pilotée par la volatilité** : position longue dimensionnée par l'inverse de la volatilité réalisée récente, plafonnée, rebalancée chaque semaine | Pas d'arbitrage : la prime de risque du BTC, mieux répartie dans le temps car la volatilité se regroupe (littérature des « portefeuilles pilotés par la volatilité », Moreira et Muir, 2017) | **Directionnelle** : elle suit le BTC et peut perdre 40 à 60 % dans un marché baissier, même pilotée. Elle se juge contre la simple détention du BTC, pas contre zéro | **passe** (T3 : comptant depuis 2017, trois blocs possibles ; T2 : rotation faible ; T6 : accès simple) |
| **H38** | **Bêta faible contre bêta fort sur les perpétuels liquides** (« betting against beta ») : acheter les moins volatils, vendre les plus volatils, neutre au bêta du BTC, rebalancé chaque semaine. Absorbe H26 | Les acheteurs de loterie qui surpaient les jetons très volatils (Frazzini et Pedersen, 2014, sur les actions) | Proche des shorts de STRAT-06 (T9) ; preuves mitigées en crypto [non vérifié] ; coût de rotation hebdomadaire | **passe, affaiblie** (archives en cache, rotation hebdomadaire mesurée par le constat C1) |
| H39 | Saisonnalité intrajournalière du BTC (heures d'ouverture américaine ou asiatique) | Flux réguliers (fonds indiciels à la clôture américaine) | Effets de quelques centièmes de point contre 0,10 % d'aller-retour, comme H14 | **écartée (T2)** |
| H40 | Retour après un très grand mouvement journalier du BTC ou de l'ETH | Liquidations forcées | Même famille que STRAT-08, rejetée (T9) | **écartée (T9)** |
| H41 | Prime locale du stablecoin (pays à contrôle des changes) | Résidents bloqués | Accès et capital bloqués par construction (T6) | **écartée (T6)** |
| H42 | Arbitrage de prix au comptant entre plateformes | Lenteur des autres | Domaine des teneurs de marché rapides (T2, T6) | **écartée (T2)** |
| H43 | Flux des fonds indiciels BTC américains comme signal du lendemain | Demande institutionnelle lente | Moins de trois ans (depuis janvier 2024) ; flux publiés après la clôture, souvent déjà dans le prix | **écartée (T3)** |
| H44 | Comblement des « écarts du CME » | Aucun identifié | Folklore sans mécanisme (T1) | **écartée (T1)** |
| H45 | Dérive avant les décisions de la Fed | Prime de risque avant l'annonce (documentée sur les actions) | 8 décisions par an, environ 50 depuis 2020 (T3) | **écartée (T3)** |
| H46 | Prime de Strategy (MSTR) sur la valeur de ses BTC, retour vers la moyenne (perpétuel MSTR contre perpétuel BTC) | Acheteurs particuliers de la prime | Peu d'épisodes indépendants, changement de régime net en 2025 (T3, T10) ; historique des avoirs à reconstruire depuis les dépôts SEC (T4) | **pas maintenant** |

## Recommandation

1. **H37 d'abord.** C'est la seule piste qui peut apporter un rendement absolu important, parce qu'elle porte la prime du BTC. Il faut le dire clairement : **c'est une exposition au marché, pas un arbitrage**. Son intérêt est de rester exposé au BTC en coupant la taille quand la volatilité explose, ce qui réduit les pires baisses. Elle se teste vite : bougies journalières du comptant depuis 2017 (déjà en archive), trois blocs (2018–2020, 2021–2023, 2024–2026), deux paramètres (fenêtre de volatilité et cible). Les portes la comparent à la simple détention du BTC : meilleur Sharpe, baisse maximale plus faible, sur chaque bloc.
2. **H38 ensuite.** C'est la seule piste neutre au marché qui reste, mais elle est voisine des shorts de STRAT-06 : son résultat se lira bloc par bloc et hors de sa meilleure année (L13).
3. **Les huit autres sont écartées ou mises de côté.** Aucun test n'est lancé sur elles.

Pour l'objectif de 100 % par an : seule H37 peut s'en approcher, et seulement les années où le BTC monte fortement. Les années de baisse, elle perdra aussi, moins que le BTC si elle fonctionne.
