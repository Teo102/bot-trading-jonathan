---
name: revue-performance
description: "Revue périodique (hebdomadaire ou mensuelle) des trades de Jonathan à partir du journal : taux de réussite, gain moyen contre perte moyenne, espérance, respect des règles, erreurs récurrentes, chaque erreur transformée en règle proposée pour le skill concerné. Seconde étape de la chaîne R1 de cerveau-trading ; s'ouvre sur bilan, revue, statistiques, « qu'est-ce qui ne marche pas »."
---

# Revue de performance (version 1.2)

Second maillon de la chaîne R1. Le skill mesure, puis apprend. Il juge le processus autant que le résultat : un trade gagnant hors règles reste une erreur.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Entrée

Extrait du journal sur la période, fourni par `journal-trading`, et les fiches liées. Un échantillon de moins de vingt trades clos est signalé : les statistiques restent indicatives.

## 2. Mesures

| Mesure | Calcul |
|---|---|
| Trades clos | nombre |
| Taux de réussite | gagnants / clos |
| Gain moyen, perte moyenne | en % du capital et en R |
| Ratio gain moyen / perte moyenne | |
| Espérance par trade | taux × gain moyen − (1 − taux) × perte moyenne, en R |
| Résultat de la période | % du capital, comparé au seuil de pause (`commun-trading` § 3) |
| Plus forte baisse | |
| Polymarket | calibration : probabilités estimées contre issues |

## 3. Respect des règles

Pour chaque trade : risque par position, exposition, levier, ratio minimal, invalidation respectée, passage par `avocat-du-diable`, fiche complète. Les écarts sont comptés.

## 3 bis. Processus et résultat, notés séparément

Chaque trade reçoit deux notes indépendantes : **processus** (règles suivies, ticket complet, réconciliation faite) et **résultat** (P&L en R). Un trade gagnant au processus fautif compte comme erreur ; un trade perdant au processus propre n'en est pas une. La matrice des quatre cas (bon/mauvais processus × gain/perte) figure dans chaque revue.

## 3 ter. Moteur autonome

Par stratégie : espérance réalisée et son intervalle de confiance, comparés à l'intervalle du backtest ; drawdown contre le seuil du coupe-circuit moteur ; glissement et frais réels contre hypothèses. Une borne supérieure d'espérance sous 0 après 30 trades réels conduit à proposer la suspension. Les rapports de `supervision-moteur` de la période sont relus : toute alerte rouge reçoit une cause et une règle.

## 4. Erreurs récurrentes

Regroupement par cause (entrée tardive, invalidation déplacée, taille excessive, catalyseur ignoré, biais nommé par l'avocat du diable puis négligé). Une erreur vue deux fois ou plus devient récurrente.

## 5. Règles proposées

Chaque erreur retenue donne une règle générique, rédigée sans impératif, avec le skill où elle s'inscrirait (ou `commun-trading` si elle touche une règle partagée), conformément à `cerveau-trading` § 6. L'inscription attend l'accord de Jonathan.

## 6. Classement

`<racine>\revues\AAAA-MM-JJ_revue.md`, ligne `revue` au journal.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
