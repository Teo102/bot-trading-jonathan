# STRAT-20261031-02 — Portage de financement delta neutre (spot long + perpétuel court)

Statut : **recherche** (31/10/2026). Aucun capital, aucun ordre. Moteur C de `NOTE_STRATEGIE_ET_REGIME.md` § 3, « réserve ».

**Dépassements signalés (`commun-trading` § 3).** Le panier de 6 paires dépasse la valeur prudente de 3 positions simultanées (§ 8.2). Il sert à la recherche seulement. Le stop posé sur la plateforme (§ 8.2) ne s'applique pas tel quel à une jambe de couverture (§ 5 ci-dessous). Ces deux points attendent une décision de Jonathan. Le levier de base respecte la valeur prudente « aucun ».

**L'APR historique n'est pas un rendement attendu.** C'est la mesure d'un passé sans sinistre de plateforme subi. Il ne compte ni perte de fonds, ni ADL, ni dépeg, ni interruption de service.

## 1. Fiche (écrite avant tout test)

**Hypothèse économique.** Sur les perpétuels crypto, les acheteurs à levier sont plus nombreux que les vendeurs. Ils paient donc un financement aux positions courtes pour garder une exposition sans échéance. Une position courte couverte par du spot encaisse ce paiement sans risque de prix direct.

**Qui paie en face.** Les acheteurs à levier paient, souvent des particuliers. Ils acceptent ce coût contre l'accès au levier et l'absence d'échéance. Ce n'est pas un repas gratuit : le porteur est rémunéré pour immobiliser du capital, pour le risque de plateforme et pour le risque de queue (§ 6). L'edge attendu est donc une prime de risque, pas une inefficience.

**Connaissance préalable déclarée.** Le seuil d'entrée a été choisi en connaissant le plancher habituel de 0,01 % par 8 h (≈ 10,95 %/an), et après lecture de deux taux BTC récents (Binance et Bybit, API publiques, 31/10/2026 22:17 UTC). Aucune série historique n'avait été téléchargée. Le choix n'est donc pas totalement à l'aveugle.

**Marchés.** Perpétuels linéaires USDT et spot USDT, jambes sur la même plateforme, deux comptes internes (spot et dérivés). Binance et Bybit sont testés séparément. Univers figé : BTC, ETH, XRP, BNB, ADA, LINK, déjà parmi les actifs liquides début 2021 et présents dans l'univers de STRAT-20261031-01. SOL est écarté du test pour ne pas choisir une paire parce qu'elle a bien monté depuis.

**Signal.** À chaque règlement t, chaque taux réglé est annualisé par son intervalle réel. Le signal est la moyenne des taux annualisés réglés dans les 24 heures finissant en t, t compris. Seuls des taux déjà publiés entrent dans le signal.

**Entrée.** Si le signal atteint 10 %/an et que la paire est hors position : achat du spot et vente du perpétuel, en quantités égales, juste après le règlement t, aux prix de t. Le taux de t n'est pas encaissé. Le premier encaissement est le règlement suivant.

**Sortie.** Si le signal passe sous 3 %/an : fermeture des deux jambes juste après le règlement t, aux prix de t. Le taux de t est encaissé, pas le suivant. L'écart entre les seuils évite les allers-retours coûteux.

**Rééquilibrage.** Contrôle à chaque règlement. Si le prix du perpétuel s'écarte de 25 % ou plus du prix du dernier rééquilibrage, la quantité est recalée pour retrouver la répartition cible entre spot et marge, sur les deux jambes. Les frais et le glissement s'appliquent sur la quantité échangée. Le transfert interne entre comptes est supposé gratuit.

**Taille et marge.** Levier 1 sur la jambe courte, marge isolée : capital C = notionnel N + marge N/L, soit N = C/2 pour L = 1. La moitié du capital reste donc en marge et ne rapporte rien par elle-même. Chaque paire reçoit 1/6 du capital du panier, sous le plafond prudent de 20 % par actif. Le gain n'est pas retiré : il est réinvesti au rééquilibrage et à l'entrée suivante. Capital réel alloué : 0 (`commun-trading` § 8.2).

**Liquidation (modélisée).** Testée sur le plus haut du perpétuel entre deux règlements, marge de maintenance 0,5 % [hypothèse]. La marge restante est perdue. Le spot, découvert, est vendu au règlement suivant.

**Coûts (preneur sur les deux jambes, grille de base).**

| Plateforme | Spot | Perpétuel | Source |
|---|---|---|---|
| Binance | 0,10 % | 0,05 % | FAQ Binance et grilles publiques, recherche web du 31/10/2026 [à revérifier avant tout papier] |
| Bybit | 0,10 % | 0,055 % | Centre d'aide Bybit, recherche web du 31/10/2026 [à revérifier avant tout papier] |

Glissement par jambe et par côté : 0,02 % pour BTC et ETH, 0,05 % pour les autres [hypothèse, comparée à un relevé de carnet réel à l'exécution, mais un relevé du jour ne dit rien du carnet passé]. La base réelle (écart spot/perpétuel) entre dans le résultat aux prix réels d'entrée et de sortie.

**Coût d'opportunité.** Taux court US de la note de régime : Fed 3,75–4 %, soit 3,875 % au milieu, appliqué à tout le capital et à toute la période, position ouverte ou non. Ce taux fixe est trop sévère pour 2021 et trop indulgent pour 2023. Un contrôle secondaire utilise le taux effectif quotidien publié par la FRED (série DFF). Le capital hors position est supposé ne rien rapporter.

**Paramètres libres : 5** (entrée 10 %, sortie 3 %, fenêtre 24 h, levier 1, rééquilibrage 25 %). Valeurs choisies avant test, non optimisées.

**Critère d'échec annoncé.** Évalué sur chaque panier. La stratégie échoue si l'un de ces points est vrai :

1. hors échantillon, APR net ≤ 3,875 % ;
2. hors échantillon, APR net avec frais et glissement doublés ≤ 3,875 % ;
3. drawdown maximal sur toute la période > 10 % du capital (un portage qui perd plus n'est plus un portage) ;
4. au moins une liquidation sur une paire, levier 1, sur toute la période ;
5. développement + validation, un voisin à ±20 % (E03 à E06) dont l'APR net passe sous 3,875 % ;
6. plus de 50 % du gain net total porté par un seul mois ;
7. moins de 100 trades au total ou moins de 30 hors échantillon (`validation-edge` § 5, repris sans le relâcher) ;
8. Sharpe hors échantillon sous le repère de tests multiples pour le nombre d'essais déclaré.

**Écart de méthode.** L'espérance en R de `validation-edge` § 5 n'a pas de sens ici, faute de stop. Elle n'est pas remplacée en silence : le critère reste marqué « non applicable, à trancher ». Le gain moyen par trade est donné pour information.

## 2. Données

- Financement : `fapi/v1/fundingRate` (Binance), `v5/market/funding/history` (Bybit). Aucun compte requis.
- Prix : bougies 4 h spot et perpétuel des deux plateformes, prix d'ouverture à l'heure du règlement.
- Période : 01/01/2021 – 31/10/2026, ou la date de début des données si elle est plus tardive (notée).
- **Biais du survivant partiel** : l'univers est figé, mais aucun actif délisté n'y figure. Ce biais flatte le résultat.
- **Biais de plateforme** : la série Binance n'intègre pas le coût du piratage d'octobre 2026, ni FTX et d'autres plateformes disparues ne figurent au test. Ce biais flatte fortement le résultat.

## 3. Découpage

| Bloc | Période | Part |
|---|---|---|
| Développement | 01/01/2021 – 30/06/2024 | ≈ 60 % |
| Validation | 01/07/2024 – 31/07/2025 | ≈ 19 % |
| Hors échantillon | 01/08/2025 – 31/10/2026 | ≈ 21 %, ouvert une seule fois |

Les résultats demandés par année et sur 12 mois recouvrent le hors échantillon. Ils proviennent du seul essai E01 et de son stress E02. Les variantes de sensibilité (E03 à E12) s'arrêtent au 31/07/2025 et ne sont jamais substituées à la base.

## 4. Sensibilité déclarée (liste complète, `REGISTRE_ESSAIS.csv`)

| Essai | Variante | Bloc |
|---|---|---|
| E01 | base | toute la période |
| E02 | base, frais et glissement × 2 | toute la période |
| E03 / E04 | entrée 8 % / 12 % | dév. + valid. |
| E05 / E06 | sortie 2,4 % / 3,6 % | dév. + valid. |
| E07 / E08 | fenêtre 16 h / 32 h | dév. + valid. |
| E09 / E10 | rééquilibrage 20 % / 30 % | dév. + valid. |
| E11 | levier 2 (N = 2C/3, liquidation vers +48 %) | dév. + valid. |
| E12 | témoin : toujours en position | dév. + valid. |

Soit 12 essais × 2 paniers = 24 séries comptées pour les tests multiples. E04 à 12 % passe au-dessus du plancher de 10,95 %/an : c'est un test volontaire de fragilité du seuil. E07 et E08 valent ±33 %, car à 8 h par règlement ±20 % ne changerait rien.

## 5. Exécution : freqtrade ne convient pas tel quel

**Constat vérifié dans le code installé (freqtrade 2026.10).** `trading_mode` vaut `spot` ou `futures` pour toute l'instance (`enums/tradingmode.py`). Binance et Bybit y sont déclarés par couple mode/marge (`_supported_trading_mode_margin_pairs`). Une stratégie freqtrade pilote donc des transactions indépendantes sur un seul marché. Elle ne connaît pas une position à deux jambes, ni un delta net, ni un rééquilibrage conjoint. Son backtest ne peut donc pas produire ce calcul, d'où `apr_net.py`.

**Architecture proposée (non codée, non testée).**

| Couche | Rôle |
|---|---|
| `tracker_funding.py` | lecture seule, signal et alertes, déjà livré |
| Moteur `portage` déterministe, processus unique | machine à états : hors position, entrée en cours, en position, rééquilibrage, sortie, incident |
| Émission | un seul émetteur par compte (`commun-trading` § 7). Deux instances freqtrade sur le même compte enfreindraient cette règle, et rien ne les coordonnerait |
| Entrée à deux jambes | jambe la moins liquide d'abord, seconde immédiate, delta résiduel borné, annulation et retour à plat si la seconde jambe échoue |
| Réconciliation | à chaque cycle : quantité spot contre quantité courte, alerte si l'écart dépasse 1 % ; détecte aussi un ADL |
| `dry_run` | permanent. Le dry-run freqtrade ne simule pas le financement à deux jambes : le papier exigerait un journal dédié |

**Conflit à trancher.** `commun-trading` § 8.2 impose un stop posé sur la plateforme. Sur la jambe courte, un stop déclenché laisse le spot découvert au pire moment. Proposition : un stop de réduction près du prix de liquidation, couplé à la vente immédiate du spot par le moteur. Décision de Jonathan : [en attente].

**Conditions de sortie anticipée (non simulées).** Retraits suspendus ou piratage annoncé : aucune entrée, sortie au plus tôt si la plateforme paraît menacée (`commun-trading` § 8.3). USDT sous 0,98 $ sur une source externe : sortie [seuil hypothétique]. Écart de quantités non expliqué : sortie et alerte. Écart de marge sous 25 % du prix de liquidation : rééquilibrage immédiat.

## 6. Risques de plateforme et de queue

**Piratage Binance.** La note de régime cite ≈ 6,3 Md$, retraits suspendus, reprise annoncée le 01/11. Confirmation partielle le 31/10/2026 : presse spécialisée (Crypto Briefing, Bitcoinist), couverture annoncée de 90 %, reprise visée au 01/11 sous réserve de contrôles. Aucune source primaire Binance lue. Bitcoinist indique un financement par le SAFU, le fonds d'assurance des contrats à terme et la trésorerie [une seule source lue sur ce point]. Si c'est exact, le fonds qui protège contre l'ADL a été ponctionné, ce qui touche directement une jambe courte. La règle de régime (note § 2) exclut toute exposition à une plateforme aux retraits suspendus. **Binance reste donc une source de données, pas une plateforme d'exécution envisageable à ce jour.**

| Risque | Mécanisme | Dans le calcul ? |
|---|---|---|
| Perte des fonds sur la plateforme | FTX 2022, Bybit 2025, Binance 2026 [les deux premiers de mémoire, à sourcer]. Le spot et la marge sont tous deux exposés | non. Seuil de sinistre calculé à part |
| Liquidation de la jambe courte | hausse rapide, marge isolée, deux comptes séparés : le gain du spot ne couvre pas la marge sans transfert | oui, sur les plus hauts |
| ADL | en chute, le moteur de la plateforme ferme d'office les courts gagnants. Le spot reste découvert pendant la chute | non. Perte de 4 h mesurée à part sur les pires bougies réelles |
| Dépeg USDT | la position courte BTC/USDT est longue USDT. L'exposition vaut tout le capital, quel que soit le levier : un USDT à −10 % coûte ≈ 10 % du capital en dollars | non. Arithmétique à part |
| Fonds sur deux comptes | spot et marge ne se compensent pas sans transfert. Un transfert bloqué en incident peut provoquer une liquidation alors que la position est couverte | en partie (liquidation) |
| Répartition sur deux plateformes | réduit la concentration, mais ajoute frais de retrait, délai réseau et risque de couverture | non, jambes sur la même plateforme au test |
| Financement négatif | le court paie. Le signal réagit après coup | oui, au taux réel |
| Base | l'écart peut s'élargir à la sortie et effacer des mois de financement | oui, aux prix réels |

Les bougies de `last` servent de proxy au prix de marque, qui peut en différer lors d'une mèche.

## 7. Avocat du diable (avant test)

**Verdict préliminaire : affaiblie.** La thèse reste défendable comme prime de risque, pas comme rendement sans risque. Ajustement nommé : aucun passage en papier sans décision sur les plateformes, le stop et le critère en R.

**Trois meilleurs arguments contraires.**

1. **Le rendement rémunère un risque que le test ne voit pas.** Une perte de plateforme efface plusieurs années de portage. Un excédent de 3 %/an ne compense qu'environ 3 % de probabilité annuelle de perte totale. La dernière alerte date de cette semaine (note de régime, § 1).
2. **Le marché a compressé cette prime.** Le portage est connu et industrialisé, notamment par des produits comme USDe [de mémoire, à sourcer]. Avec un taux court à 3,875 %, levier 1 et la moitié du capital en marge, un financement au plancher de 10,95 %/an ne laisse qu'environ 5,5 %/an brut sur capital. L'excédent attendu est donc mince avant tout sinistre.
3. **Le régime joue contre la thèse.** Tendance baissière sur 12 mois (note § 1). Le levier acheteur peut se vider et le financement tomber sous le seuil, laissant le capital à plat sous le taux court.

**Scénario d'échec.** Chute violente de 20 à 40 % sur les alts, ADL sur la jambe courte, USDT sous pression, retraits ralentis, le tout le même jour. Ordre de grandeur : [hypothèse de 2 à 5 % par an et par plateforme pour un incident avec perte ou gel durable, base : trois cas majeurs cités depuis 2022, sans estimation statistique].

**Biais probables.** Survivant et plateforme (§ 2). Récence : la période 2021 flatte le financement, qui peut ne pas revenir. Narratif « rendement sans risque ». Connaissance préalable du plancher (§ 1). Un Sharpe élevé serait trompeur : le risque de queue n'apparaît pas dans une série qui ne l'a pas subi.

**Données invalidantes.** Financement moyen sur 90 jours sous 7,75 %/an sur le notionnel, soit sous le taux court sur le capital à levier 1. Taux négatifs sur plus de 25 % des règlements d'un trimestre. Retraits non rétablis au 03/11 (note § 4). USDT sous 0,98 $.

**Positionnement.** Financement BTC encore positif malgré la baisse (CoinDesk via la note, 30/10). Relevé réel dans `resultats/` (tracker).

## 8. Décision

Décision de Jonathan : [en attente]. Aucune recommandation d'investissement. Aucun changement de statut vers le papier ou le réel.
