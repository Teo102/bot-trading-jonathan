---
name: fiche-trade
description: "Rédaction de la fiche de trade du système de Jonathan au format de commun-trading § 5, classement selon § 4, ligne ajoutée au journal, décision marquée en attente. Dernière étape des chaînes T1 et P1 de cerveau-trading ; s'ouvre aussi pour toute demande de fiche, de mise à jour d'une fiche existante ou de consignation d'une absence de trade."
---

# Fiche de trade (version 1.1)

Le skill assemble ce que la chaîne a produit. Il n'ajoute pas d'analyse nouvelle ; une donnée manquante reste entre crochets et se signale.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Fiche existante

Une fiche ouverte sur le même actif ou le même marché se reprend et se met à jour (section « Mise à jour du AAAA-MM-JJ » ajoutée en fin) ; elle ne se double pas.

## 2. Contenu (`commun-trading` § 5, dans l'ordre)

En tête, s'il y a lieu : **Alerte** (dépassement de règle, pause mensuelle, accès plateforme non vérifié, actif hors univers).

1. **Thèse en une phrase.** Ou « Absence de trade » avec sa raison.
2. **Données** : tableau donnée / valeur / source / heure.
3. **Contre-arguments** : verdict de `avocat-du-diable`, ses arguments, et la réponse de la thèse à chacun.
4. **Plan** : invalidation d'abord, puis entrée, objectif(s), horizon.
5. **Taille et perte maximale** : reprises de `risque-position`, avec ratio et corrélation.
6. **Sortie anticipée** : faits qui ferment la position avant l'invalidation (catalyseur manqué, horizon dépassé, donnée invalidante observée).
7. **Ticket** : identifiant `TK-AAAAMMJJ-NN`, ordre exact proposé (marché, sens, taille, prix limite, stop envoyé avec l'entrée), perte stressée et ligne d'approbation à recopier : « approuvé TK-AAAAMMJJ-NN ».
8. **Décision de Jonathan : [en attente].** Seule une approbation citant l'identifiant du ticket compte ; une approbation vague ne vaut pas décision. Le système n'envoie aucun ordre, même approuvé : l'envoi relève de l'outil d'exécution de Jonathan.

Pied de fiche : date de rédaction, chaîne suivie, skills ouverts.

## 3. Classement (`commun-trading` § 4)

- Chemin : `<racine>\fiches\AAAA-MM\AAAA-MM-JJ_ACTIF_sens.md` ; sens = `long`, `short`, `oui`, `non`, ou `aucun`.
- Pour un marché Polymarket, ACTIF = identifiant court du marché.
- Sans accès au dossier racine, la fiche se livre comme fichier, avec le chemin prévu indiqué.

## 4. Journal

Une ligne ajoutée à `JOURNAL-TRADING.md` (format de `journal-trading`) : date, actif ou marché, type `analyse`, décision `en attente`, lien vers la fiche. La décision ne change que sur parole de Jonathan.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
