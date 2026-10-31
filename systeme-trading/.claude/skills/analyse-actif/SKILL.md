---
name: analyse-actif
description: "Analyse d'un actif du système de trading de Jonathan (crypto ou autre marché) : tendance et structure sur plusieurs unités de temps, niveaux clés, volumes, financement et intérêt ouvert, catalyseurs, fondamentaux, conclusion haussière, baissière ou absence de trade. S'ouvre sur toute idée de trade, toute question « BTC / ETH / SOL… monte ou baisse ? », tout suivi de position ouverte, et en première étape des chaînes T1 et S1 de cerveau-trading."
---

# Analyse d'un actif (version 1.0)

Premier maillon de la chaîne T1 (idée de trade) et second maillon de S1 (suivi). Le skill produit une thèse datée, ou constate l'absence de trade. Il ne calcule pas de taille : c'est le rôle de `risque-position`.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Préalables

1. Fiches existantes : le journal a été relu par le cerveau ; une fiche ouverte sur l'actif sert de point de départ (S1 : la question devient « la thèse tient-elle encore ? »).
2. Univers : l'actif figure dans les actifs suivis de `commun-trading` § 2. Un actif exclu ou absent est signalé en tête ; l'analyse continue seulement si Jonathan l'a demandée explicitement.

## 2. Données

| Donnée | Source | Remarque |
|---|---|---|
| Prix, bougies, carnet, volumes | connecteur Crypto.com | heure de lecture notée |
| Financement, intérêt ouvert | connecteur Crypto.com si disponible, sinon recherche web (Coinglass, etc.) | sinon : « non disponible » |
| Catalyseurs, actualité | recherche web | date de chaque source |
| Fondamentaux (offre, déblocages, revenus, activité on-chain) | recherche web | date de chaque source |

Un chiffre lu de mémoire ou sans heure n'entre pas dans l'analyse, ou entre entre crochets.

## 3. Lecture technique

- **Unités de temps** : hebdomadaire, journalier, 4 h (et 1 h si l'horizon est court). Pour chacune : tendance (hausse, baisse, range), structure (sommets et creux), position par rapport aux moyennes mobiles usuelles.
- **Concordance** : les unités alignées ou en conflit sont nommées ; un conflit pèse vers l'absence de trade.
- **Niveaux clés** : supports, résistances, zones de volume, plus haut et plus bas récents, chacun chiffré.
- **Volumes** : confirmation ou divergence avec le mouvement.
- **Dérivés** : financement (positif extrême = positionnement acheteur chargé), intérêt ouvert (hausse avec le prix ou contre lui), liquidations notables.

## 4. Catalyseurs et fondamentaux

Événements datés à venir (macro, déblocages de jetons, mises à jour, décisions réglementaires, résultats). Fondamentaux en quelques lignes. Ce qui relève de la macro générale renvoie à `veille-macro-crypto` si une veille récente existe.

## 5. Conclusion

Une des trois issues, sans autre :

- **Thèse haussière** ou **thèse baissière** : une phrase ; zone d'entrée envisagée ; **invalidation d'abord** (niveau précis et raison) ; objectif(s) ensuite ; horizon ; probabilité estimée avec sa base.
- **Absence de trade** : raison (signaux en conflit, rapport rendement/risque insuffisant, données manquantes) et condition qui changerait l'avis.

En S1 : thèse intacte, affaiblie ou invalidée, avec le niveau ou le fait qui le montre.

## 6. Sortie pour la chaîne

Bloc transmis à `avocat-du-diable` : thèse, données (source, heure), niveaux, invalidation, objectif, horizon, catalyseurs, points faibles déjà vus.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
