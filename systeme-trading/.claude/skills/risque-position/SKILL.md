---
name: risque-position
description: "Calcul de la taille d'une position du système de trading de Jonathan à partir de l'invalidation et des règles de risque de commun-trading § 3 : perte maximale, ratio rendement/risque, corrélation avec les positions ouvertes du journal, signalement de tout dépassement. Étape des chaînes T1 et P1 de cerveau-trading ; s'ouvre aussi pour toute question « combien mettre », taille, levier, stop ou exposition."
---

# Risque et taille de position (version 1.3)

Le skill traduit une thèse validée par `avocat-du-diable` en taille, perte maximale et ratio. Il ne modifie pas les règles : il les applique et nomme chaque écart.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Entrées

- Entrée, invalidation, objectif(s) (issus de l'analyse et du verdict).
- Règles de `commun-trading` § 3, coupe-circuits du § 3 bis et, pour le moteur autonome, limites du § 8.2.
- Positions ouvertes et résultat du mois, lus dans `JOURNAL-TRADING.md` par `journal-trading` ou par le cerveau.

Une valeur manquante dans `commun-trading` prend la valeur prudente du tableau, et le compte rendu le signale. Sans capital renseigné, la taille s'exprime en pourcentage du capital et le montant reste entre crochets.

## 2. Calcul — actif

1. Distance à l'invalidation : |entrée − invalidation| / entrée, en %.
2. Risque autorisé = capital × risque maximal par position.
3. Taille (valeur notionnelle) = risque autorisé / distance à l'invalidation.
4. Plafonds : la taille est ramenée au plus petit de : exposition maximale par actif, place restante sous l'exposition totale. Un plafond qui s'applique réduit la perte maximale réelle ; les deux chiffres sont donnés.
5. Levier implicite = taille / capital alloué à la position. Au-delà du levier maximal (par défaut : aucun), dépassement signalé.
6. Perte maximale sur **stop stressé** : un stop déclenché est un ordre au marché, il glisse et paie le taker sur les deux jambes. La perte par unité vaut |entrée − stop| + glissement estimé au stop + frais taker d'entrée et de sortie. La taille se calcule sur cette perte stressée, pas sur la seule distance au stop ; la taille de l'étape 3 est donc recalculée avec ce dénominateur. Le glissement retenu s'appuie sur la profondeur du carnet lue (source, heure) ou, à défaut, sur une valeur prudente [estimation].
7. Ratio rendement/risque = (objectif − entrée) / (entrée − invalidation), en valeur absolue, par objectif. Sous le ratio minimal : dépassement signalé.

## 3. Calcul — marché de prédiction

Une part achetée au prix p (0 à 1) perd p si le marché se résout contre elle. La perte maximale est donc la mise entière, sauf sortie anticipée prévue.

- Mise = min(mise maximale Polymarket, risque maximal par position) × capital.
- Gain si résolution favorable = mise × (1 − p) / p, avant frais.
- Ratio = (1 − p) / p ; espérance = estimation propre × (1 − p) − (1 − estimation) × p, par unité misée.
- Liquidité : une mise supérieure à une fraction notable de la profondeur du carnet est signalée (glissement).

## 4. Corrélation

Les positions ouvertes sont regroupées par facteur commun (bêta BTC, même secteur, même événement macro, marché Polymarket lié à l'actif). Des positions fortement corrélées s'additionnent comme une seule exposition ; le risque cumulé en cas de choc commun est chiffré.

## 5. Contrôles

- Coupe-circuits de `commun-trading` § 3 bis vérifiés **avant chaque ticket** : niveau du compte par rapport à son plus haut, drawdown du moteur, perte du mois. Un coupe-circuit actif bloque le ticket ; la sortie le dit en tête.
- **Reprise après le coupe-circuit « compte »** : pendant le nombre de trades fixé au § 3 bis, le risque par position utilisé au § 2 (étape 2) et au § 3 vaut la moitié de la valeur du § 3. La sortie indique « reprise : n trades restants à risque réduit ».
- Pour une stratégie du moteur autonome, les plafonds de `commun-trading` § 8.2 s'appliquent en plus de ceux du § 3, le plus strict l'emportant ; au statut « réel réduit », le risque vaut le quart de la valeur prévue (`validation-edge` § 8).

- Les limites de `commun-trading` § 3 sont des plafonds : une instruction ponctuelle peut les resserrer, jamais les relâcher.

- Perte mensuelle déjà atteinte au-delà du seuil de pause : la fiche le dit en tête et la position n'est pas proposée sans décision explicite de Jonathan.
- Tout dépassement de règle figure en tête de la sortie, jamais ajusté en silence (`commun-trading` § 3).

## 6. Sortie

Tableau : entrée, invalidation, distance, taille (% et montant), perte maximale, objectif(s), ratio(s), levier, exposition après ouverture (actif, total), corrélation, dépassements.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
