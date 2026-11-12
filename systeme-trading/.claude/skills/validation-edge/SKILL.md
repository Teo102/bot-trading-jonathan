---
name: validation-edge
description: "Porte d'entrée du moteur autonome de Jonathan : toute stratégie candidate (crypto, perps, alts, règles de bot freqtrade ou autre) y passe par backtest honnête, contrôle des biais, correction des tests multiples, hors échantillon, papier, puis dossier de promotion. Chaîne V1 de cerveau-trading ; s'ouvre sur le mot VALIDER, sur toute idée de stratégie automatisable, de bot, de backtest, d'optimisation, de « stratégie qui marche » vue en ligne, et sur toute modification d'une stratégie existante."
---

# Validation d'un edge (version 1.3, 01/11/2026)

Le skill répond à une seule question : cette stratégie a-t-elle un edge qui survit aux frais, au hasard et au temps ? Il ne cherche pas à rendre une stratégie bonne ; il cherche à la faire échouer avant le capital. Une stratégie qui échoue ici coûte du temps, pas d'argent.

## Ouverture

Ouvert directement, ce skill ouvre d'abord `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`. Ouvert dans une chaîne en cours, il ne rouvre pas le cerveau. Les valeurs propres à Jonathan (risque, coupe-circuits, plateformes, moteur) se lisent dans `commun-trading` ; aucune n'est recopiée ici.

## 0 bis. Tri en 10 minutes (avant toute fiche)

Ajouté le 01/11/2026 sur décision de Jonathan et Téo. Toute idée passe ce tri **avant** qu'une fiche soit ouverte ou qu'une ligne de code soit écrite. Un seul « non » écarte l'idée ; le compte rendu nomme le critère en cause en une phrase. Une idée écartée ici ne consomme aucun essai et ne s'inscrit au journal que si Jonathan le demande.

| N° | Question | Écarte si |
|---|---|---|
| T1 | Qui perd en face, et pourquoi continue-t-il ? | Aucune contrepartie nommée et contrainte (liquidée, forcée, mal informée, payée pour porter un risque) |
| T2 | Le mouvement espéré dépasse-t-il trois fois le coût d'un aller-retour (frais, écart, glissement, financement) ? | Non, ou ordre de grandeur inconnu |
| T3 | Peut-on obtenir au moins 100 décisions en développement et 30 hors échantillon ? | Non : intestable (cas de STRAT-20261031-04) |
| T4 | Les données existent-elles telles qu'elles étaient connues à la date (univers, calendriers, intérêt ouvert) ? | Non : biais non corrigible |
| T5 | L'edge demande-t-il de la vitesse (moins d'une seconde, colocalisation, course aux ordres) ? | Oui |
| T6 | L'exécution est-elle possible : vente à découvert, accès depuis le pays de résidence (`commun-trading` § 1), règles de risque du § 3 ? | Non |
| T7 | La perte maximale est-elle bornée sans couverture qui mange l'edge ? | Non (vente de volatilité nue, martingale, moyenne à la baisse) |
| T8 | Plus de 5 paramètres réglés, ou idée arrivée avec un backtest flatteur vu en ligne ? | Oui : présomption de surapprentissage, passage par `avocat-du-diable` avant toute fiche |
| T9 | Est-ce une stratégie déjà rejetée sous un autre nom, ou du bêta marché déguisé ? | Oui (voir `commun-trading` § 8.4) |
| T10 | L'idée ne marche-t-elle que dans un régime précis (hausse de 2021 par exemple) ? | Oui |

Une idée qui passe les dix questions ouvre la fiche du § 1. Le tri ne dit rien de l'edge : il élimine seulement les impasses à coût nul.

## 0 ter. Leçons inscrites (cerveau-trading § 7)

Règles génériques tirées des erreurs relevées, chacune datée et sourcée au journal.

| N° | Règle | Origine |
|---|---|---|
| L1 | Un critère d'échec se fixe avant le test et ne se négocie pas après. Un critère inatteignable se corrige **avant** toute lecture de rendement, et la correction est consignée | STRAT-01, E10 ; STRAT-03, C3 retiré le 01/11/2026 |
| L2 | Une ligne absente d'une archive n'est pas un jour à volume nul. Toute règle de continuité distingue les deux, et un saut brutal du nombre de candidats se diagnostique sur les volumes seuls avant le gel | STRAT-03, trou du 26-27/02/2022, 43 noms perdus |
| L3 | Un trou de données se comble à la source (archives journalières) ; une heure absente suivie d'une reprise ne vaut ni délistage ni stop | STRAT-03, correctif 0007 |
| L4 | Avant tout essai, le cerveau vérifie dans `git log` et dans le code que chaque correctif annoncé est présent, et relance toutes les suites de tests. Un correctif annoncé peut manquer | 01/11/2026 : patch 0007 annoncé appliqué, absent du dépôt |
| L5 | Une idée écartée par le tri T1 à T10 ne se poursuit que par exception écrite de Jonathan, avec une règle de décision et un plan de sortie écrits avant les résultats | STRAT-DEX, avenant 2 |
| L6 | Une décision du journal ne se renverse que par une nouvelle ligne de journal qui l'acte. Un mandat plus récent ne l'efface pas en silence | Approche par wallets abandonnée puis rouverte le 01/11/2026 |
| L7 | Un simulateur qui suppose une exécution sur chaque trade public surestime le maker. Toute mesure de maker modélise la file d'attente | Polymarket, 01/11/2026 : +4,83 $ naïf contre −15,42 $ avec file |
| L8 | Avant d'interpréter un échec, publier la puissance du test. Un échec sans puissance ne prouve pas l'absence d'edge, mais reste un échec | STRAT-03 § 3, calibration Polymarket, STRAT-DEX |
| L9 | Un rapprochement de renommages par les seules dates ne vaut rien : les plateformes arrêtent et cotent par lots. La liste close se fait par les annonces, puis on vérifie que chaque nom concerné est éligible | STRAT-06, 1 075 paires candidates pour 5 vrais renommages |
| L10 | Tout univers construit par noms ou volumes vérifie le type du contrat (`underlyingType`, `contractType`) : une plateforme peut coter des actions ou des métaux sous le même format | STRAT-06, perpétuels non crypto cotés depuis décembre 2025 |
| L11 | Un code repris d'une autre stratégie se reteste contre les définitions de la nouvelle fiche, notamment quand elle ajoute une jambe de couverture | STRAT-06, porte de concentration de E02 |
| L12 | Un essai de dépendance (exclusion d'un type d'événement) vérifie d'abord que l'événement touche le portefeuille joué. Sinon la porte est franchie à vide, et elle se publie comme telle | STRAT-06, E16 : 89 retraits sur 49 dates, aucun sur un nom retenu, résultat identique à la base (05/11/2026) |
| L13 | Un criblage ou un essai publie son résultat bloc par bloc et **hors de sa meilleure année** avant toute conclusion, et vérifie que **chaque jambe existe à la date de chaque épisode**, du début à la fin de sa cotation (une paire déjà délistée ne se trade pas) | STRAT-07, 12/11/2026 : +6,89 %/an au criblage, mais +2,90 %/an hors 2021 et 46 % du gain de la validation sur des paires au comptant déjà délistées |

## 1. Fiche de stratégie

Identifiant `STRAT-AAAAMMJJ-NN`. Contenu écrit **avant** tout test :

- hypothèse économique en une phrase (pourquoi cet edge existerait, et qui perd en face) ;
- règles exactes d'entrée, de sortie, de stop, de taille ; marchés et unité de temps ;
- paramètres et leurs valeurs ; nombre de paramètres libres ;
- critère d'échec annoncé à l'avance.

Une stratégie sans hypothèse économique (« l'indicateur a bien marché ») se marque [fragile] : elle reste testable, mais l'avocat du diable en tient compte.

## 2. Données

- Historique d'au moins 2 ans, si possible plus, couvrant hausse, baisse et range ; source et dates notées.
- Frais réels de la plateforme cible, glissement estimé à partir de la profondeur de carnet, financement des perpétuels inclus.
- Univers figé à la date de chaque trade : aucune paire choisie parce qu'elle a bien monté depuis (biais du survivant).

## 3. Découpage

| Bloc | Part de l'historique | Usage |
|---|---|---|
| Développement | ≈ 60 % | Réglage des paramètres |
| Validation | ≈ 20 % | Choix entre variantes |
| Hors échantillon | ≈ 20 %, la période la plus récente | Ouvert **une seule fois**, pour le verdict |

Un test glissant (walk-forward) remplace ce découpage quand l'historique le permet. Un hors échantillon regardé deux fois n'en est plus un : il redevient de la validation.

## 4. Contrôles obligatoires

1. **Biais d'anticipation** : `freqtrade lookahead-analysis` et `recursive-analysis` propres, ou contrôle équivalent hors freqtrade.
2. **Registre des essais** : chaque variante testée est comptée, y compris les abandonnées. Le nombre total d'essais figure dans le dossier.
3. **Correction des tests multiples** : Sharpe déflaté, ou comparaison avec la distribution du meilleur Sharpe obtenu par autant de stratégies aléatoires (repère : environ 3,0 pour 500 essais sans edge sur un an).
4. **Robustesse** : paramètres voisins (±20 %) encore rentables ; résultat stable sur chaque sous-période ; aucun mois ou trade unique ne porte l'essentiel du gain.
5. **Coûts stressés** : frais et glissement doublés, espérance encore positive.

## 5. Critères de passage au papier

Tous sont requis, sur le bloc hors échantillon :

| Critère | Seuil |
|---|---|
| Nombre de trades | ≥ 100 (développement + validation + hors échantillon), dont ≥ 30 hors échantillon |
| Espérance nette par trade | > 0,2 R après coûts réels ; > 0 avec coûts doublés |
| Drawdown maximal | < 20 % au risque prévu ; le drawdown du 95e centile (Monte Carlo sur l'ordre des trades) est noté, il sert au coupe-circuit « moteur » |
| Tests multiples | Sharpe hors échantillon au-dessus du repère du § 4.3 pour le nombre d'essais déclaré |
| Compatibilité | Risque par trade et exposition conformes à `commun-trading` § 3 et § 8 |

## 6. Avocat du diable

Le dossier passe par `avocat-du-diable` avant tout verdict : hypothèse économique, surajustement, dépendance à un régime, capacité (taille du marché face à la taille visée), risque de plateforme. Un verdict « rejetée » arrête la stratégie.

## 7. Papier

- Durée de 8 à 12 semaines en dry-run ou sur réseau de test, sur la plateforme cible.
- Le papier est réussi si l'espérance réalisée reste dans l'intervalle à 90 % issu du backtest et si le drawdown reste sous le drawdown du 95e centile.
- Un écart de comportement (glissement, fréquence des trades, remplissages) se documente ; un écart important renvoie au § 2.

## 8. Statuts et promotion

`recherche` → `backtest` → `papier` → `réel réduit` → `réel` ; `suspendue` ou `rejetée` à tout moment.

| Passage | Condition | Accord |
|---|---|---|
| backtest → papier | § 5 et § 6 satisfaits | Automatique, inscrit au journal |
| papier → réel réduit | § 7 satisfait | Porte humaine : « promu STRAT-… au statut réel réduit » |
| réel réduit → réel | ≥ 30 trades réels, comportement conforme au papier | Porte humaine |
| tout statut → suspendue | Coupe-circuit « moteur », anomalie de supervision, décision de Jonathan | Automatique |

En réel réduit, le risque par trade vaut le quart du risque prévu (valeur prudente).

## 9. Sortie

Dossier `STRAT-…` : fiche, données, découpage, registre des essais, résultats par bloc, contrôles, verdict de l'avocat du diable, statut proposé, drawdown du 95e centile, paramètres figés (fichier de configuration du moteur). Ligne au journal ; registre des stratégies de `commun-trading` § 8 mis à jour.

## 10. Exécution

- **Dans Claude Code** (environnement principal, `cerveau-trading` § 0 bis) : le skill exécute lui-même toute la procédure, dans l'ordre du registre : installation de freqtrade si absente, téléchargement des données, blocs de développement et de validation, `lookahead-analysis` et `recursive-analysis`, variantes de robustesse, coûts doublés, puis hors échantillon une seule fois. Après chaque essai, il remplit le registre ; à la fin, il rend le verdict du § 5 et passe le dossier à `avocat-du-diable`.
- **Dans claude.ai** : le skill prépare la fiche, le code, la configuration et une mission Claude Code ; il ne présente aucun résultat simulé comme un backtest.
- Dans les deux cas, un arrêt de la procédure (biais détecté, données manquantes, erreur) se consigne avec sa cause ; il ne se contourne pas en changeant la stratégie.

## Règles communes

- Aucun ordre, aucune clé de trading manipulée, aucune promesse de gain.
- Chaque chiffre porte sa source et sa période ; une donnée non vérifiée se marque entre crochets.
- Le risque et le drawdown passent avant le rendement.
- Français, phrases courtes, aucun impératif, aucune certitude sur l'avenir.
