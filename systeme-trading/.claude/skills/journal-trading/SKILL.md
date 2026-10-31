---
name: journal-trading
description: "Tenue du journal JOURNAL-TRADING.md du système de trading de Jonathan : lecture des fiches et positions existantes, ajout des événements (analyse, ouverture, ajustement, clôture, revue), état des positions ouvertes. S'ouvre en tête des chaînes S1 et R1 de cerveau-trading, et sur toute mention du journal, d'une position prise ou fermée, d'un « j'ai acheté / vendu » ou d'un état des positions."
---

# Journal de trading (version 1.3)

Le journal est la mémoire du système. Le skill le lit, l'enrichit et en tire l'état des positions. Il ne réécrit jamais une ligne passée : une correction s'ajoute comme nouvelle ligne.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (capital, règles de risque, plateformes, univers, dossiers) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 1. Emplacement

`<racine>\JOURNAL-TRADING.md` (racine de `commun-trading` § 4). Sans accès au dossier, le journal est demandé à Jonathan ou reconstitué à partir des fiches fournies, et la limite est signalée.

## 2. Format (`commun-trading` § 4)

| Date | Actif ou marché | Type | Décision de Jonathan | Fiche |
|---|---|---|---|---|

Types : `analyse`, `ouverture`, `ajustement`, `clôture`, `revue`, `validation`, `promotion`, `supervision`, `alerte`. Origine : `discrétionnaire`, ou `moteur` suivi de l'identifiant `STRAT-…`. Pour une ouverture, un ajustement ou une clôture, la colonne Décision porte aussi le prix, la taille et l'heure donnés par Jonathan. Une clôture porte le résultat en % du capital et en multiple du risque (R).

## 3. Lecture

1. Fiches et lignes sur l'actif ou le marché demandé.
2. Positions ouvertes : toute ouverture sans clôture ultérieure.
3. Décisions encore `en attente`.

## 4. Réconciliation

Une ouverture, un ajustement ou une clôture s'inscrit d'après l'exécution réelle (prix moyen, taille remplie, frais, heure), relevée sur la plateforme ou transmise par Jonathan, jamais d'après l'ordre prévu. Un écart entre ticket et exécution (remplissage partiel, glissement supérieur à l'estimation) se note sur la ligne. Une position sans exécution vérifiée reste marquée [non réconciliée].

## 4 bis. Trades du moteur autonome

Les trades du moteur s'importent depuis son export ou son API en lecture (`commun-trading` § 8), puis se réconcilient avec la plateforme comme au § 4. Un trade du moteur sans `STRAT-…` connu, ou issu d'une stratégie qui n'est pas au statut réel ou réel réduit, déclenche une alerte rouge pour `supervision-moteur`.

## 5. Ajout

Une ligne par événement, à la date de l'événement. Seule une parole de Jonathan change une décision ; le système n'inscrit aucun ordre comme passé de son fait.

## 6. État des positions

Tableau : actif, sens, entrée, taille, invalidation, objectif, prix actuel (connecteur Crypto.com ou recherche web, heure), distance à l'invalidation en %, résultat latent, fiche. Une position proche de son invalidation, selon le seuil d'alerte de `commun-trading` § 3, déclenche une alerte pour le cerveau.

## 7. Sortie

S1 : fiche d'origine et état de la position, transmis à `analyse-actif` ou `analyse-polymarket`. R1 : extrait de la période, transmis à `revue-performance`.

## Règles communes

- Aucun ordre, aucune connexion en écriture à une plateforme, aucune promesse de gain.
- Chaque prix, probabilité ou chiffre porte sa source et son heure (UTC) ; une donnée non vérifiée se marque entre crochets.
- Le risque et l'invalidation passent avant l'objectif.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir ; une probabilité s'exprime en chiffre avec sa base (`commun-trading` § 6).
