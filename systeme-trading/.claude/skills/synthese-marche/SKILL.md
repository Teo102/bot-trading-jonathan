---
name: synthese-marche
description: "Synthèse d'une page du marché pour Jonathan à partir de la veille macro et crypto : régime de marché, risques, opportunités à étudier, dates à surveiller. Seconde étape de la chaîne M1 de cerveau-trading ; s'ouvre sur toute demande de résumé, de point rapide ou de « en bref, où en est le marché »."
---

# Synthèse de marché (version 1.0)

Second maillon de la chaîne M1. Le skill réduit la veille à une page lisible en deux minutes. Il n'introduit aucune donnée absente de la veille, sauf vérification nouvelle datée.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Entrée

Le document de `veille-macro-crypto` du jour. Une veille de plus de 24 h est signalée comme ancienne.

## 2. Structure (une page)

1. **Alerte** éventuelle, en une ligne.
2. **Régime de marché** : appétit pour le risque, neutre, ou aversion ; tendance du BTC ; état de la liquidité. Trois à cinq phrases, chaque affirmation rattachée à un chiffre de la veille.
3. **Risques principaux** : trois au plus, chacun avec son déclencheur observable.
4. **Opportunités à étudier** : actifs ou marchés qui mériteraient une chaîne T1 ou P1, avec la raison. Une opportunité à étudier n'est pas une thèse.
5. **Dates à surveiller** : tableau date, heure, événement, effet possible.
6. **Ce qui changerait la lecture** : deux ou trois seuils chiffrés.

## 3. Ton

Pas de prévision ferme : « le régime paraît », « la probabilité semble ». Une probabilité est chiffrée avec sa base.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
