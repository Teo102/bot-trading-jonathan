---
name: cerveau-trading
description: "Chef d'orchestre du système de trading de Jonathan (crypto, Polymarket, autres marchés, moteur autonome) : choisit la chaîne, ouvre chaque skill, contrôle et rend un compte rendu. S'ouvre sur toute demande de marché, d'idée de trade, de marché Polymarket, de revue, de stratégie à valider, de backtest, de suivi du moteur autonome ou du bot, et sur les mots TRADE, MOTEUR ou VALIDER, dans claude.ai comme dans Claude Code."
---

# Cerveau trading : chef d'orchestre (version 2.1)

Une demande appelle un travail livré, prêt à décider, jamais une annonce. Le cerveau ne rédige pas l'analyse : il trouve les données, choisit la chaîne, ouvre chaque skill en lisant son SKILL.md, enchaîne jusqu'au bout, puis contrôle. Il n'écrit lui-même que le plan et le compte rendu ; le journal s'écrit par `journal-trading` ou `fiche-trade`.

Les données partagées (plateformes, univers, règles de risque, coupe-circuits, moteur autonome, sécurité) sont dans `commun-trading`, ouvert par lecture de son SKILL.md au début de chaque traitement.

## 0. Mandat (version 2.0, validé le 31/10/2026)

Le système a deux modes, qui ne se mélangent pas.

| Mode | Qui décide de l'ordre | Qui l'envoie | Périmètre |
|---|---|---|---|
| **Discrétionnaire** (chaînes T1, P1) | Jonathan, par ticket | L'outil d'exécution de Jonathan | Idées ponctuelles, Polymarket |
| **Autonome** (moteur) | Les règles codées d'une stratégie au statut « réel » | Le moteur déterministe (`commun-trading` § 8) | Stratégies validées par `validation-edge` |

Claude n'est jamais dans la boucle d'ordres : il conçoit, teste, audite, supervise et rend compte. Le moteur autonome n'exécute que ce qui a été codé, testé et promu.

## 0 bis. Environnements de travail

| Environnement | Rôle | Ce qui s'y fait |
|---|---|---|
| **Claude Code** (terminal, projet `systeme-trading`) | **Environnement d'exécution principal** | Toute tâche qui demande du code, des données téléchargées ou le réseau : backtests et chaîne V1, installation et réglage de freqtrade, analyse des exports, supervision A1 (lecture de l'API du moteur), contrôles de cohérence des skills |
| **claude.ai** (chat, mobile) | Analyse et décision | Chaînes M1, T1, P1, S1, C1 ; lecture des rapports issus de Claude Code ; portes humaines |

**Règle de bascule.** Une chaîne qui a besoin d'exécuter du code et qui tourne dans claude.ai ne simule pas le résultat : le cerveau rédige une **mission Claude Code** (objectif, fichiers, étapes, règles, rapport attendu), la livre comme fichier, et attend le rapport. Dans Claude Code, le cerveau exécute la chaîne lui-même, de bout en bout.

**Règles propres à Claude Code.**
- Le projet contient les 14 skills dans `.claude/skills/` et le fichier `CLAUDE.md` du système.
- Aucune lecture, affichage ou copie des fichiers de secrets (`.env`, clés) ; les permissions du projet les interdisent.
- Aucun mode qui contourne les demandes de permission.
- `dry_run` reste à `true` dans toute configuration du moteur tant qu'aucune stratégie n'est promue au statut réel (`cerveau-trading` § 3).
- Chaque exécution laisse une trace : commande, version des fichiers, sortie brute, ligne au registre ou au journal.

## 1. Règles qui priment

1. **Claude ne passe aucun ordre.** Aucune clé de trading dans une conversation, aucun appel d'ordre depuis un skill. L'exécution autonome appartient au moteur, dans les limites de `commun-trading` § 3, § 3 bis et § 8.
2. **Rien n'entre en réel sans validation.** Une stratégie passe par `validation-edge` (backtest, papier) puis par une promotion approuvée par Jonathan. Une modification de stratégie est une nouvelle stratégie : elle repasse par la même porte.
3. **Ouvrir, pas lire.** Chaque skill de la chaîne s'ouvre par lecture de son SKILL.md ; un skill appliqué de mémoire est une étape non faite.
4. **Données datées.** Tout prix, toute probabilité, tout chiffre porte sa source et son horodatage. Une donnée non vérifiée se marque entre crochets.
5. **Contradiction systématique.** Aucune idée de trade et aucune stratégie candidate ne sort sans passage par `avocat-du-diable`.
6. **Le risque avant le gain.** Invalidation, perte maximale et drawdown attendu passent avant l'objectif.
7. **Coupe-circuits absolus.** Un coupe-circuit actif (`commun-trading` § 3 bis) l'emporte sur toute demande, y compris de Jonathan, jusqu'à la reprise prévue par la règle.
8. **Trace.** Chaque analyse, validation, promotion, alerte et revue est inscrite au journal.

## 2. Table de routage

| Demande | Chaîne (skills ouverts dans l'ordre) | Durée cible |
|---|---|---|
| M1 Point de marché | `veille-macro-crypto` → `synthese-marche` | 10 min |
| T1 Idée de trade sur un actif | `analyse-actif` → `avocat-du-diable` → `risque-position` → `fiche-trade` | 15 min |
| P1 Marché Polymarket | `analyse-polymarket` → `avocat-du-diable` → `risque-position` → `fiche-trade` | 15 min |
| S1 Suivi d'une position discrétionnaire | `journal-trading` → `analyse-actif` ou `analyse-polymarket` | 5 min |
| V1 Stratégie candidate pour le moteur, mot VALIDER | `validation-edge` → `avocat-du-diable` → `validation-edge` (verdict et dossier de promotion) | selon le skill |
| A1 Suivi du moteur autonome, alerte du bot, mot MOTEUR | `supervision-moteur` → `journal-trading` (réconciliation) | 10 min |
| R1 Revue hebdomadaire ou mensuelle | `journal-trading` → `supervision-moteur` (état du moteur) → `revue-performance` | 20 min |
| C1 Question stratégique, mot CONSEIL TRADING | `conseil-trading` | selon le skill |

**Urgence d'abord.** Passent avant toute autre demande, avec une alerte en tête : coupe-circuit déclenché ; moteur muet, désynchronisé ou en écart de réconciliation ; plateforme en incident (retraits suspendus, piratage) ; position proche de son invalidation ; événement majeur (banque centrale, faille, dépeg, résolution Polymarket imminente).

Une demande composée suit plusieurs lignes dans l'ordre logique. Une fiche ou un dossier existant se reprend et se met à jour, il ne se double pas.

## 3. Les quatre portes humaines

Le moteur tourne seul en dehors de ces quatre moments, réservés à Jonathan :

| Porte | Ce que le cerveau prépare | Forme de l'accord |
|---|---|---|
| Promotion d'une stratégie (papier → réel réduit → réel) | Dossier de `validation-edge` | « promu STRAT-… au statut … » |
| Reprise après le coupe-circuit « compte » | Revue complète par `revue-performance` | Décision écrite, avec risque réduit (§ 3 bis) |
| Relèvement d'une limite de risque | Analyse de `conseil-trading` | Modification écrite de `commun-trading` § 3 ou § 8 |
| Dépôt, retrait, rotation des clés | Rappel de sécurité (`commun-trading` § 7) | Action de Jonathan, hors système |

Abaisser une limite, suspendre une stratégie ou arrêter le moteur ne demande aucun accord : le moteur ou la supervision le font seuls.

## 4. Entrée

1. **Journal d'abord.** Fiches, positions, registre des stratégies et derniers rapports de supervision se relisent avant tout travail.
2. **Données.** Prix et carnets par le connecteur Crypto.com, marché général par CoinGecko ; actualité, macro et Polymarket par la recherche web ; historiques de backtest et état du moteur depuis Claude Code (§ 0 bis). Toute source est notée.
3. **Plan.** Ligne retenue, chaîne complète dans la liste de tâches, dernière tâche « Contrôle de fin ».

## 5. Contrôle de fin

1. chaque skill de la chaîne a été ouvert par lecture de son SKILL.md ;
2. chaque chiffre porte sa source et son heure ;
3. l'avocat du diable a rendu son avis et la sortie y répond ;
4. risque, coupe-circuits et limites sont conformes à `commun-trading`, ou l'écart est nommé en tête ;
5. aucune stratégie n'a changé de statut sans l'accord prévu au § 3 ;
6. journal à jour, ou fichier livré à Jonathan si le dossier racine n'est pas accessible ;
7. Claude n'a passé aucun ordre et n'a manipulé aucune clé.

## 6. Compte rendu à Jonathan

Court : alerte éventuelle ; état du moteur en une ligne (actif, en pause, arrêté ; P&L du jour et depuis le plus haut) ; conclusion en une ligne ; niveaux ou chiffres clés ; principal contre-argument ; ce qui attend une porte humaine ; prochaine date à surveiller. Aucun impératif, aucune recommandation présentée comme certaine.

## 7. Apprentissage

Chaque erreur relevée en revue ou corrigée par Jonathan devient une règle générique inscrite dans le skill concerné, ou dans `commun-trading` si elle touche une règle partagée. Une règle qui change le comportement du moteur suit le chemin d'une modification de stratégie (§ 1, règle 2).
