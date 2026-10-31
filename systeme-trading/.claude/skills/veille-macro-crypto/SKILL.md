---
name: veille-macro-crypto
description: "Point macro et crypto du système de trading de Jonathan : taux et banques centrales, dollar, liquidité, flux ETF, données on-chain, stablecoins, calendrier des événements à venir, actualité réglementaire, sources datées. Première étape de la chaîne M1 de cerveau-trading ; s'ouvre sur « où en est le marché », point du matin, veille, contexte macro, ou avant une analyse quand aucune veille récente n'existe."
---

# Veille macro et crypto (version 1.0)

Premier maillon de la chaîne M1. Le skill rassemble des faits datés ; l'interprétation d'ensemble revient à `synthese-marche`.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Rubriques

Chaque rubrique donne la valeur, sa variation récente, la source et l'heure. Une rubrique sans donnée fiable porte « non trouvée ».

1. **Taux et banques centrales** : taux directeurs (Fed, BCE, BoJ), rendements américains 2 et 10 ans, prochaines réunions, attentes du marché (FedWatch ou équivalent).
2. **Dollar** : indice DXY.
3. **Liquidité** : bilan de la Fed, conditions financières, actifs risqués (Nasdaq, S&P 500).
4. **Flux ETF** : flux nets récents des ETF BTC et ETH au comptant.
5. **On-chain** : réserves des plateformes, activité, positions des détenteurs de long terme, selon les sources disponibles.
6. **Stablecoins** : capitalisation totale et variation, tout écart de parité.
7. **Marché crypto** : prix BTC, ETH et actifs suivis (`commun-trading` § 2) par le connecteur Crypto.com ; dominance BTC ; financement agrégé.
8. **Réglementation** : décisions, textes, procédures récents ou attendus, par juridiction.
9. **Calendrier** : événements des quatorze prochains jours (CPI, emploi, réunions, déblocages de jetons, échéances d'options, résolutions Polymarket suivies), date et heure.

## 2. Urgences

Un événement majeur (décision de banque centrale imprévue, faille d'un protocole, dépeg d'un stablecoin) se place en tête et se transmet au cerveau comme alerte (`cerveau-trading` § 2).

## 3. Classement

Fichier `<racine>\veille\AAAA-MM-JJ_veille.md` (`commun-trading` § 4), ou livré comme fichier si le dossier n'est pas accessible.

## 4. Sortie

Le document de veille, transmis à `synthese-marche`.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
