---
name: commun-trading
description: Données partagées du système de trading de Jonathan (plateformes, univers d'actifs, règles de risque, format des fiches et du journal, classement). Ouvert par cerveau-trading au début de chaque traitement et par tout skill du système qui en a besoin.
---

# Commun trading : données partagées (version 1.7, 02/11/2026)

Les valeurs entre crochets sont à compléter par Jonathan. Tant qu'une valeur manque, le skill qui en dépend la marque au compte rendu et applique la valeur prudente indiquée.

## 1. Plateformes

| Plateforme | Usage | Accès des outils |
|---|---|---|
| [Crypto.com Exchange] | spot [et dérivés ?] | lecture des prix par le connecteur Crypto.com |
| [Polymarket] | marchés de prédiction | lecture par la recherche web ; Jonathan réside aux Émirats (confirmé le 31/10/2026) : accès ouvert, statut légal en zone grise [risque faible, non nul] |
| [autres] | [ ] | [ ] |

Aucune plateforme n'est connectée en écriture à Claude. L'exécution passe soit par Jonathan (mode discrétionnaire), soit par le moteur autonome déterministe (§ 8).

## 1 bis. Statut juridique et fiscal (Émirats)

- Résidence de Jonathan : Émirats arabes unis (confirmée le 31/10/2026). Résidence fiscale : [à inscrire par Jonathan].
- Impôt sur les sociétés : d'après la décision du Conseil des ministres n° 49 de 2023, une personne physique n'y entre que si le chiffre d'affaires de son activité dépasse 1 million d'AED, et les revenus d'investissement personnel, sans licence, en sont exclus (PwC, Khaleej Times, lus le 01/11/2026). Application à ce système : [à confirmer par Jonathan, juriste fiscaliste].
- Polymarket : risque pénal au titre des art. 460 à 463 du code pénal fédéral, non chiffrable (`polymarket/REGISTRE_MARCHES_UMA.md` § 4). Aucun capital avant l'avis d'un conseil local.
- Téo : pays de résidence [à confirmer]. Polymarket est bloqué en France depuis le 16/07/2026.

## 2. Univers

- Actifs suivis : [BTC, ETH, SOL, …]
- Actifs exclus : [memecoins, jetons de moins de X M$ de capitalisation, …]. Pour STRAT-20261031-03 (décision D6 du 01/11/2026, opérationnalisation à figer) : stablecoins et actifs indexés, moins de 180 jours d'historique continu, memecoins de la liste close de `strategies/STRAT-20261031-03/config_strat03.json`, médiane de volume journalier sous 50 M USDT
- Horizon dominant : [swing, quelques jours à quelques semaines]

## 3. Règles de risque

| Règle | Valeur | Valeur prudente par défaut |
|---|---|---|
| Capital alloué au système | 0 jusqu'à la première promotion d'une stratégie (décision de Jonathan du 01/11/2026). L'enveloppe se fixe à la porte de promotion | — |
| Risque maximal par position (perte à l'invalidation) | 1 % du capital (profil « standard », décision de Jonathan du 01/11/2026) | 1 % |
| Exposition maximale totale | 50 % (profil « standard », 01/11/2026) | 50 % |
| Exposition maximale par actif | [ ] % | 20 % |
| Mise maximale par marché Polymarket | [ ] % | 2 % |
| Levier maximal | [ ] | aucun |
| Ratio rendement/risque minimal | [ ] | 2 |
| Perte mensuelle déclenchant une pause | 10 % (profil « standard », 01/11/2026) | 10 % |
| Alerte de proximité de l'invalidation (part de la distance initiale restante) | [ ] | un tiers |

Une fiche qui dépasse une règle le dit en tête ; elle ne s'ajuste pas en silence. Ces valeurs sont des plafonds : une instruction ponctuelle peut les resserrer, jamais les relâcher.

### 3 bis. Coupe-circuits (vérifiés avant chaque ticket)

| Niveau | Déclencheur | Effet | Reprise |
|---|---|---|---|
| Compte | Baisse de [ ] % depuis le plus haut historique du capital (valeur prudente : 15 %) | Aucun nouveau ticket, tous moteurs confondus ; revue complète (`revue-performance`) | Seulement sur décision écrite de Jonathan, avec un risque par position divisé par deux pendant [ ] trades (valeur prudente : 20) |
| Moteur | Drawdown réel du moteur supérieur à 1,5 fois le drawdown du 95e centile de son backtest validé | Moteur suspendu, les autres continuent | Nouveau backtest, puis papier |
| Mois | Perte mensuelle du § 3 | Pause jusqu'au mois suivant | Automatique, avec revue |

Le niveau « compte » est absolu. Le niveau « moteur » détecte un edge disparu avant que le compte n'en souffre. Avec un risque de 2 % par trade, un coupe-circuit à 15 % se déclenche presque toujours dans l'année, même pour une stratégie gagnante : le risque par position reste donc de 1 % au plus tant que le coupe-circuit vaut 15 %.

## 4. Classement et journal

- Racine : [D:\Trading] — sous-dossiers `fiches\AAAA-MM`, `veille`, `revues`.
- Fiche : `AAAA-MM-JJ_ACTIF_sens.md` ; sens = `long`, `short`, `oui`, `non`, ou `aucun` pour une absence de trade.
- Sans accès au dossier racine (chat claude.ai), fiches et journal se livrent comme fichiers, avec le chemin prévu indiqué ; Jonathan les range et joint le journal aux suivis et revues.
- `JOURNAL-TRADING.md`, à la racine : une ligne par événement — date, actif ou marché, type (analyse, ouverture, ajustement, clôture, revue, validation, promotion, supervision, alerte), origine (`discrétionnaire` ou `moteur` + `STRAT-…`), décision de Jonathan ou règle appliquée, lien vers la fiche ou le dossier.

## 5. Format d'une fiche

1. Thèse en une phrase.
2. Données (source, heure).
3. Contre-arguments de l'avocat du diable et réponse.
4. Entrée, invalidation, objectif(s), horizon.
5. Taille calculée et perte maximale.
6. Conditions de sortie anticipée.
7. Décision de Jonathan : [en attente].

## 6. Rédaction

Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base.

## 7. Sécurité et exécution

- Aucun envoi de fonds vers un contrat ou une adresse indiqués par un tiers ; aucun déploiement de contrat « bot » (Remix ou autre). Ce schéma est celui des contrats voleurs déguisés en bots MEV.
- Clés d'API : trading seulement, jamais de retrait ; stockées dans un fichier `.env` local, hors de Claude et hors des conversations.
- Exécution : un seul émetteur d'ordres par compte, le moteur déterministe du § 8. Claude rédige, teste, supervise et lit les journaux ; il ne décide pas d'un ordre en boucle et ne l'envoie pas.
- Le moteur ne tourne que sur un compte dédié, séparé des fonds discrétionnaires.
- Papier ou réseau de test d'abord pour toute nouvelle action ; jamais de mode « contourner les permissions » sur une machine qui détient des clés.
- Aucun code, skill ou bot tiers installé sans lecture préalable.

## 8. Moteur autonome

Mandat validé le 31/10/2026 (`cerveau-trading` § 0). Les valeurs entre crochets sont à compléter par Jonathan ; tant qu'une valeur manque, le moteur reste en papier.

### 8.1 Infrastructure

| Élément | Valeur | Valeur prudente |
|---|---|---|
| Logiciel | [freqtrade] | — |
| Hôte | [serveur loué, fonctionnement continu] | jamais un ordinateur personnel |
| Plateforme(s) | Données de backtest : Binance Futures (décision du 01/11/2026). Exécution : [différée, Bybit ou OKX envisagés ; Hyperliquid non tranché] — support freqtrade [à confirmer] | une seule au départ |
| Compte | dédié au moteur | — |
| Clé | trading seulement, sans retrait, liste blanche d'IP si disponible | — |
| Accès de supervision | API du moteur en lecture, clé plateforme en lecture seule | — |
| Interrupteur d'urgence | [Telegram du moteur] | testé avant le premier trade réel |
| Délai de battement de cœur | [ ] minutes | 15 |

### 8.2 Limites du moteur (codées dans sa configuration)

| Règle | Valeur | Valeur prudente |
|---|---|---|
| Capital alloué au moteur | [ ] | 0 tant qu'aucune stratégie n'est promue |
| Risque par trade (réel) | 0,25 % par ligne quand 6 positions sont ouvertes (décision du 01/11/2026) ; [ ] % sinon | 0,5 % ; quart de cette valeur en « réel réduit » |
| Positions ouvertes simultanées | 6 (décision du 01/11/2026, pour 3 longs et 3 shorts) | 3 |
| Risque cumulé au stop, toutes positions ouvertes | 1,5 % du capital du moteur (6 × 0,25 % = 3 × 0,5 %, décision du 01/11/2026) | 1,5 % |
| Exposition totale du moteur | [ ] % de son capital | 100 %, sans levier implicite au-delà de 2 |
| Stop | posé sur la plateforme à l'entrée, jamais géré seulement par le moteur | — |
| Coupe-circuits | § 3 bis, codés dans le moteur (protections natives si disponibles) | — |

Ces limites sont des plafonds : le moteur peut les resserrer seul, jamais les relâcher.

### 8.3 Incidents de plateforme

Retraits suspendus, piratage annoncé, maintenance non prévue ou données incohérentes : aucune nouvelle entrée sur la plateforme concernée. Les positions ouvertes se gèrent selon [ ] (valeur prudente : conservation avec stops sur la plateforme, sauf si la plateforme elle-même paraît menacée, auquel cas sortie au plus tôt).

### 8.4 Registre des stratégies

| Identifiant | Description courte | Statut | Drawdown 95e centile (backtest) | Seuil coupe-circuit moteur | Dernière décision |
|---|---|---|---|---|---|
| STRAT-20261031-01 | Tendance Donchian, 10 perpétuels | rejetée | — | — | Verdict E10-E11 du 01/11/2026 |
| STRAT-20261031-02 | Portage de financement delta neutre | rejetée pour ce jeu de paramètres | — | — | Jonathan et Téo, 01/11/2026 |
| STRAT-20261031-03 | Momentum transversal résiduel, 3 longs et 3 shorts | rejetée (porte sous-périodes, 2 années positives sur 4) | — | — | Verdict des portes du 02/11/2026, E25 non ouvert |
| STRAT-20261031-04 | Retour à la moyenne après cascades | recherche, non testable en l'état | — | — | Jonathan et Téo, 01/11/2026 |

Le registre est tenu par `validation-edge` ; un changement de statut vers le réel suit la porte humaine de `cerveau-trading` § 3.
| STRAT-DEX | Rétro-ingénierie de wallets Solana (pilote) | rejetée pour l'approche par wallets (non concluant, 6 wallets sur 30 requis) | — | — | Avenant 2, 02/11/2026 |
| STRAT-20261102-05 | Encombrement financement et intérêt ouvert, 3 longs et 3 shorts | rejetée (E01 −23,5 %, prix net de coûts −66,2 %) | — | — | Verdict E01 du 02/11/2026, hors échantillon non ouvert |

## 9. Constats empiriques mesurés

Inscrits le 02/11/2026 à la demande de Jonathan et Téo. Ce sont des **observations datées, sur un échantillon nommé**, pas des lois : chacune peut être contredite par une mesure plus large. Un skill qui s'en sert cite le numéro et la limite. Un constat ne justifie jamais à lui seul une règle de trading ; il oriente une fiche, qui reste soumise à `validation-edge`.

| N° | Constat | Mesure (source) | Portée et limite |
|---|---|---|---|
| C1 | **Le coût de rotation d'un portefeuille hebdomadaire 3L/3S sur le top 30 des perpétuels est stable : environ 0,13 % par semaine à brut 100 %, soit environ 6,6 % par an**, et environ 63 % de la borne haute calculée (0,20 %) | 0,127 %/sem. sur 182 semaines (E01) et 0,126 %/sem. sur 56 semaines (E02) de STRAT-03, frais et glissement de 0,05 % par côté (exports du 02/11/2026) | Coût **modélisé**, pas observé en exécution. Vaut pour cette rotation et ce barème. Le glissement réel au stop n'est pas mesuré |
| C2 | **Ce coût suffit à annuler un momentum résiduel d'alts** : sur 2021 à mi-2024, prix +15,9 % contre coûts −23,1 %. Sur la validation, prix +46,2 % contre coûts −7,1 % | E01 et E02 de STRAT-03 | Une seule stratégie et un seul jeu de paramètres. Le signe du prix change d'un bloc à l'autre : ce n'est pas une invariance du résultat, seulement du coût |
| C3 | **Le financement encaissé n'est ni stable ni symétrique** : +32,6 % sur 2021 à mi-2024 (longs +12,3 %, shorts +20,3 %), puis +0,8 % sur juillet 2024 à juillet 2025 (longs +3,1 %, shorts −2,3 %) | E01 et E02 de STRAT-03, sur les seules lignes choisies par le momentum | Mesuré sur des lignes sélectionnées par un autre signal. Il dépend du régime de levier. Base de l'hypothèse de STRAT-05, d'où sa déclaration de contamination |
| C4 | **La jambe courte d'un momentum d'alts subit les rebonds** : prix des shorts −73,3 % sur E01, contre +17,2 % sur E02 | STRAT-03 | Même portée que C2 |
| C5 | **Sur un tirage de wallets actifs sur pump.fun et Raydium, la détention médiane est d'environ 11 à 14 minutes** (perdants 0,19 h, gagnants 0,23 h) et 69 % des wallets perdent avant filtres | Pilote STRAT-DEX, 4 174 positions, 147 wallets, 90 jours avant le 01/11/2026, `cohorte_pilote.json` du 02/11/2026 | Échantillon biaisé vers les wallets peu actifs (193 au-delà de 1 000 signatures écartés) et vers les pools chauds du jour du tirage ; 28 % des positions exclues pour transfert. Conséquence retenue : l'activité observée relève de la vitesse (tri T5) |
| C6 | **Un maker passif sur Polymarket perd une fois la file d'attente modélisée** : −15,42 $ pour 1 000 $ exécutés [IC 95 % −35,89 ; −8,43], contre −2,54 $ dans le simulateur naïf | `polymarket/resultats/20261101T091123Z_file_attente_rapport.md`, 23 marchés hors mi-mandat | Une fenêtre de 14 jours avant le mi-mandat, un seul instantané du carnet |
| C7 | **Les archives mensuelles de data.binance.vision ont des trous** : 2 jours manquants (26 et 27/02/2022) sur 43 contrats majeurs ; 318 jours 1 d et 256 jours 1 h comblés par les journalières sur E01, 5 restés introuvables | Diagnostic du 01/11/2026, E01 du 02/11/2026 | Vaut pour toute stratégie qui lit ces archives : comblement obligatoire (`validation-edge` L2 et L3) |
| C8 | **Un financement très négatif n'annonce pas un rebond** : sur 2022 à mi-2024, le long des 3 noms les moins encombrés (financement le plus négatif, intérêt ouvert en baisse) perd −70,0 % sur le prix, en encaissant +36,4 % de financement ; le short des plus encombrés gagne +24,6 % sur le prix | E01 de STRAT-20261102-05, 130 semaines, export du 02/11/2026 | Lu jambe par jambe après le résultat. Ne fonde aucune stratégie testable sur ces blocs |
