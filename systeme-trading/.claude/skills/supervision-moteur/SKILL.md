---
name: supervision-moteur
description: "Supervision du moteur de trading autonome de Jonathan (freqtrade ou équivalent) : battement de cœur, réconciliation des positions avec la plateforme, coupe-circuits, écart au backtest, incidents de plateforme, rapport d'état. Chaîne A1 de cerveau-trading et étape des revues R1 ; s'ouvre sur le mot MOTEUR, sur toute alerte ou notification du bot, toute question « le bot tourne ? », « où en est le moteur ? », toute anomalie de position ou d'exécution."
---

# Supervision du moteur autonome (version 1.1)

Le moteur décide et exécute seul. Ce skill vérifie qu'il fait ce qui a été validé, ni plus ni moins, et déclenche l'arrêt quand ce n'est plus le cas. Il lit ; il n'envoie aucun ordre. Les arrêts automatiques sont codés dans le moteur ; le skill les constate, les complète par ses contrôles et en rend compte.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les seuils viennent de `commun-trading` § 3 bis et § 8 ; aucun n'est recopié ici.

## 1. Sources

- État du moteur : API en lecture du moteur ou base des trades (freqtrade), lue directement depuis Claude Code (`cerveau-trading` § 0 bis). Dans claude.ai, le skill travaille sur les exports fournis et le dit en tête.
- Positions et soldes réels : plateforme, par une clé en lecture seule ou un export.
- Prix : connecteur Crypto.com, CoinGecko ; incidents de plateforme : recherche web.
- Chaque lecture porte sa source et son heure. Une source muette se marque [non lue], jamais comme « rien à signaler ».

## 2. Contrôles, dans l'ordre

| # | Contrôle | Anomalie | Action |
|---|---|---|---|
| 1 | Battement de cœur : dernière activité du moteur | Silence au-delà du délai de § 8 | Alerte rouge ; consigne d'arrêt ou de vérification à Jonathan |
| 2 | Réconciliation : positions, tailles, stops du moteur contre ceux de la plateforme | Position inconnue du moteur, stop absent, taille différente | Alerte rouge ; arrêt des nouvelles entrées |
| 3 | Stops posés sur la plateforme pour chaque position | Position sans stop côté plateforme | Alerte rouge |
| 4 | Coupe-circuit « compte » : capital contre son plus haut | Seuil atteint | Moteur arrêté ; porte humaine de reprise |
| 5 | Coupe-circuit « moteur » : drawdown de chaque stratégie contre 1,5 × son drawdown du 95e centile | Seuil atteint | Stratégie suspendue (`validation-edge` § 8) |
| 6 | Perte du mois | Seuil atteint | Pause jusqu'au mois suivant |
| 7 | Limites : risque par trade, exposition, levier, positions ouvertes | Dépassement | Alerte rouge ; recherche de la cause (bug, paramètre) |
| 8 | Écart au backtest : fréquence des trades, glissement, espérance glissante | Hors de l'intervalle à 90 % | Alerte orange ; revue de la stratégie |
| 9 | Plateforme : retraits, incidents, piratage, maintenance | Incident ouvert | Arrêt des entrées sur cette plateforme ; plan de sortie de `commun-trading` § 8 |
| 10 | Version : configuration et code en service identiques à ceux du dossier `STRAT-…` | Différence | Alerte rouge : changement non validé |

Une alerte rouge passe en tête du compte rendu et au journal. L'arrêt d'une stratégie ou du moteur ne demande aucun accord ; la reprise suit les portes de `cerveau-trading` § 3.

## 3. Rapport d'état

Une page :

- état global : actif, en pause, arrêté ; cause ;
- capital, plus haut, drawdown courant ; P&L du jour, de la semaine, du mois (en % et en R) ;
- par stratégie : statut, trades, espérance réalisée contre intervalle du backtest, drawdown contre seuil ;
- positions ouvertes réconciliées, ou écarts ;
- alertes et actions ; prochaine vérification.

## 4. Journal

Chaque contrôle donne une ligne `supervision` à `JOURNAL-TRADING.md` (format de `journal-trading`) ; chaque trade du moteur s'y inscrit d'après son exécution réelle, marqué `moteur` et rattaché à son `STRAT-…`.

## Règles communes

- Aucun ordre, aucune clé de trading manipulée, aucune promesse de gain.
- Chaque chiffre porte sa source et son heure ; une donnée non vérifiée se marque entre crochets.
- Le risque passe avant le rendement : dans le doute, la sortie conseille l'arrêt.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir.
