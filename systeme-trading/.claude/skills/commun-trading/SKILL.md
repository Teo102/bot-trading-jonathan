---
name: commun-trading
description: Données partagées du système de trading de Jonathan (plateformes, univers d'actifs, règles de risque, format des fiches et du journal, classement). Ouvert par cerveau-trading au début de chaque traitement et par tout skill du système qui en a besoin.
---

# Commun trading : données partagées (version 1.3)

Les valeurs entre crochets sont à compléter par Jonathan. Tant qu'une valeur manque, le skill qui en dépend la marque au compte rendu et applique la valeur prudente indiquée.

## 1. Plateformes

| Plateforme | Usage | Accès des outils |
|---|---|---|
| [Crypto.com Exchange] | spot [et dérivés ?] | lecture des prix par le connecteur Crypto.com |
| [Polymarket] | marchés de prédiction | lecture par la recherche web ; Jonathan réside aux Émirats (confirmé le 31/10/2026) : accès ouvert, statut légal en zone grise [risque faible, non nul] |
| [autres] | [ ] | [ ] |

Aucune plateforme n'est connectée en écriture à Claude. L'exécution passe soit par Jonathan (mode discrétionnaire), soit par le moteur autonome déterministe (§ 8).

## 2. Univers

- Actifs suivis : [BTC, ETH, SOL, …]
- Actifs exclus : [memecoins, jetons de moins de X M$ de capitalisation, …]
- Horizon dominant : [swing, quelques jours à quelques semaines]

## 3. Règles de risque

| Règle | Valeur | Valeur prudente par défaut |
|---|---|---|
| Capital alloué au système | [ ] | — |
| Risque maximal par position (perte à l'invalidation) | [ ] % du capital | 1 % |
| Exposition maximale totale | [ ] % | 50 % |
| Exposition maximale par actif | [ ] % | 20 % |
| Mise maximale par marché Polymarket | [ ] % | 2 % |
| Levier maximal | [ ] | aucun |
| Ratio rendement/risque minimal | [ ] | 2 |
| Perte mensuelle déclenchant une pause | [ ] % | 10 % |
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
| Plateforme(s) | [Hyperliquid ? autre] — support freqtrade [à confirmer] | une seule au départ |
| Compte | dédié au moteur | — |
| Clé | trading seulement, sans retrait, liste blanche d'IP si disponible | — |
| Accès de supervision | API du moteur en lecture, clé plateforme en lecture seule | — |
| Interrupteur d'urgence | [Telegram du moteur] | testé avant le premier trade réel |
| Délai de battement de cœur | [ ] minutes | 15 |

### 8.2 Limites du moteur (codées dans sa configuration)

| Règle | Valeur | Valeur prudente |
|---|---|---|
| Capital alloué au moteur | [ ] | 0 tant qu'aucune stratégie n'est promue |
| Risque par trade (réel) | [ ] % | 0,5 % ; quart de cette valeur en « réel réduit » |
| Positions ouvertes simultanées | [ ] | 3 |
| Exposition totale du moteur | [ ] % de son capital | 100 %, sans levier implicite au-delà de 2 |
| Stop | posé sur la plateforme à l'entrée, jamais géré seulement par le moteur | — |
| Coupe-circuits | § 3 bis, codés dans le moteur (protections natives si disponibles) | — |

Ces limites sont des plafonds : le moteur peut les resserrer seul, jamais les relâcher.

### 8.3 Incidents de plateforme

Retraits suspendus, piratage annoncé, maintenance non prévue ou données incohérentes : aucune nouvelle entrée sur la plateforme concernée. Les positions ouvertes se gèrent selon [ ] (valeur prudente : conservation avec stops sur la plateforme, sauf si la plateforme elle-même paraît menacée, auquel cas sortie au plus tôt).

### 8.4 Registre des stratégies

| Identifiant | Description courte | Statut | Drawdown 95e centile (backtest) | Seuil coupe-circuit moteur | Dernière décision |
|---|---|---|---|---|---|
| — | aucune stratégie enregistrée | — | — | — | — |

Le registre est tenu par `validation-edge` ; un changement de statut vers le réel suit la porte humaine de `cerveau-trading` § 3.
