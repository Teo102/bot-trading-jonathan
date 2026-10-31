---
name: analyse-polymarket
description: "Analyse d'un marché de prédiction (Polymarket ou autre) pour le système de trading de Jonathan : règles exactes de résolution, date, liquidité, probabilité implicite, estimation propre argumentée et sourcée, écart, risques propres (résolution ambiguë, liquidité, oracle), accès depuis le pays de résidence. S'ouvre sur tout lien ou question Polymarket, Kalshi, cote, « quelle chance que… », et en première étape de la chaîne P1 de cerveau-trading."
---

# Analyse d'un marché de prédiction (version 1.1)

Premier maillon de la chaîne P1. Le skill compare le prix du marché à une estimation propre et documentée. Un écart faible ou une règle ambiguë conduit à l'absence de trade.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Accès

Le statut d'accès se lit dans `commun-trading` § 1, sans être recopié ici. Une alerte en tête n'apparaît que si ce statut est absent, marqué [à vérifier], ou s'il a changé (pays de résidence, liste des pays restreints de Polymarket, décision d'un régulateur). Un statut « zone grise » se rappelle en une ligne dans la section des risques (§ 5), pas en alerte.

## 2. Le marché

Lu par la recherche web (page du marché), heure notée :

- Question exacte et **règles de résolution mot pour mot** (paraphrase interdite pour la clause décisive), source de résolution, oracle (par exemple UMA), cas limites prévus.
- Date de clôture et date de résolution.
- Prix « oui » et « non », écart acheteur-vendeur, volume, liquidité visible.
- Probabilité implicite = prix du « oui » (corrigée de l'écart si celui-ci est large).

## 3. Estimation propre

1. **Taux de base** : fréquence historique d'événements comparables, avec sa source.
2. **Ajustements** : faits récents, sondages, données, déclarations, chacun daté et sourcé, avec son sens et son poids.
3. **Estimation finale** en pourcentage, avec une fourchette et sa base.
4. **Autres sources** : cotes d'autres plateformes ou modèles publics, s'ils existent.

## 4. Écart

Écart = estimation − probabilité implicite, en points.

Frais en vigueur (à vérifier sur la page des frais de Polymarket, date notée) :
- ordre **taker** : frais = parts × taux de la catégorie × p × (1 − p), maximaux autour de p = 0,5 ; certaines catégories sont sans frais ;
- ordre **maker** (limite au carnet) : sans frais, avec rebates éventuels ; le remplissage n'est pas garanti et expose à l'antisélection.

L'écart se compare à l'écart **net** : en taker, après frais et glissement ; en maker, après une marge d'antisélection [estimation]. Le mode maker est le mode par défaut. Un écart net inférieur à l'incertitude de l'estimation conduit à l'absence de trade.

## 5. Risques propres

- **Résolution ambiguë** : formulations ouvertes, précédents de litiges.
- **Oracle** : mécanisme de contestation, risque de résolution erronée.
- **Liquidité** : profondeur du carnet face à la mise envisagée, possibilité de sortir avant résolution.
- **Temps** : capital immobilisé jusqu'à la date ; rendement annualisé indicatif.
- **Accès et cadre légal** : statut de `commun-trading` § 1, rappelé en une ligne.

## 6. Conclusion et sortie

Position envisagée (« oui » ou « non ») ou absence de trade ; invalidation (fait ou cote qui ferait sortir) ; horizon = date de résolution. Bloc transmis à `avocat-du-diable`.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
