---
name: avocat-du-diable
description: "Lecture adverse de toute thèse de trading de Jonathan (actif, marché Polymarket, stratégie) : meilleurs arguments contraires, scénario d'échec, biais probables, données qui invalideraient la thèse, verdict maintenue, affaiblie ou rejetée. Étape obligatoire des chaînes T1 et P1 de cerveau-trading ; s'ouvre aussi dès qu'une idée de trade paraît évidente, qu'un « tout le monde achète » apparaît ou qu'une contradiction est demandée."
---

# Avocat du diable (version 1.0)

Aucune idée ne sort sans passer ici (`cerveau-trading` § 1.4). Le skill attaque la thèse reçue comme le ferait un trader adverse compétent. Il ne cherche pas l'équilibre : il cherche ce qui peut faire perdre.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Entrée

Le bloc de sortie de `analyse-actif` ou de `analyse-polymarket`, ou une thèse donnée par Jonathan. Les données reprises gardent leur source et leur heure ; une vérification nouvelle se date.

## 2. Lecture adverse

1. **Trois meilleurs arguments contraires**, classés par poids, chacun appuyé sur une donnée sourcée ou marqué entre crochets.
2. **Scénario d'échec** : le chemin le plus plausible vers l'invalidation, avec son déclencheur et un ordre de grandeur de probabilité.
3. **Biais probables** : confirmation (données choisies dans un seul sens), récence (dernière bougie surpondérée), FOMO (entrée après une forte hausse), ancrage (prix d'achat passé), excès de confiance, narratif. Chaque biais retenu cite l'indice qui le suggère.
4. **Données invalidantes** : liste des faits observables qui rendraient la thèse fausse, avec seuils chiffrés (prix, financement, flux, probabilité Polymarket, date).
5. **Positionnement** : la thèse est-elle déjà le consensus ? Financement, sentiment, intérêt ouvert, cotes Polymarket.
6. **Invalidation** : le niveau proposé est-il logique ou trop proche du bruit ? Un niveau trop serré ou trop lâche est signalé.

## 3. Verdict

- **Maintenue** : aucun argument contraire ne dépasse la thèse ; les risques sont connus et chiffrés.
- **Affaiblie** : la thèse reste défendable mais demande un ajustement (taille réduite, entrée différente, invalidation déplacée, attente d'une confirmation). L'ajustement est nommé.
- **Rejetée** : un argument contraire domine ou une donnée invalidante est déjà présente. La chaîne s'arrête avant `risque-position` ; la fiche, si elle est rédigée, consigne l'absence de trade.

## 4. Sortie

Verdict, trois arguments, scénario d'échec, biais, données invalidantes. La fiche (`commun-trading` § 5, point 3) reprend ces contre-arguments et la réponse qui leur est faite.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
