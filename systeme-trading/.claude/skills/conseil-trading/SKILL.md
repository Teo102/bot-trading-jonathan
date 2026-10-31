---
name: conseil-trading
description: "Conseil contradictoire pour une question stratégique de trading de Jonathan : plusieurs points de vue opposés (macro, technique, risque, contrarien) débattent, puis synthèse et position argumentée. Déclenché par le mot CONSEIL TRADING (ligne C1 de cerveau-trading), et aussi par toute question d'allocation, de stratégie, de changement de règle ou de choix difficile entre plusieurs options de marché."
---

# Conseil trading (version 1.0)

Ligne C1 de `cerveau-trading`. Une question stratégique (allocation, changement de règle, sortie d'un marché, choix entre deux approches) passe devant quatre voix contradictoires avant une position argumentée. La décision reste à Jonathan.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Cadrage

La question se reformule en une phrase, avec les options en présence et l'horizon. Les données utiles (veille récente, journal, positions) sont lues et datées ; une donnée absente reste entre crochets.

## 2. Les voix

Chaque voix rend un avis de cinq à dix phrases, appuyé sur des données sourcées, et une position (pour, contre, conditionnel) :

1. **Macro** : taux, liquidité, dollar, flux, régime.
2. **Technique** : tendance, structure, niveaux, positionnement.
3. **Risque** : règles de `commun-trading` § 3, perte maximale, corrélation, scénario de pire cas.
4. **Contrarien** : ce que le consensus ignore, où la foule se trompe peut-être.

Les voix ne se ménagent pas : chacune relève au moins une faille chez une autre.

## 3. Synthèse

- Points d'accord et points de désaccord.
- Ce qui départagerait les voix (donnée, date, seuil).
- **Position argumentée** : option retenue, ou attente, avec son niveau de confiance chiffré et sa base, et la condition qui la ferait changer.
- Le risque passe avant le potentiel ; une option qui viole une règle de `commun-trading` le dit en tête.

## 4. Trace

Ligne `analyse` au journal si la question touche une position ou une règle ; une règle nouvelle proposée suit `cerveau-trading` § 6.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
