# Registre global des hypothèses

Créé le 02/11/2026 à la demande de Jonathan et Téo (exploration continue, sans pause). Ce registre compte **toutes** les hypothèses examinées par le système, y compris celles écartées au tri. Résultat de recherche, aucune recommandation.

## Pourquoi un registre global

Explorer beaucoup d'hypothèses est légitime. Mais chaque hypothèse testée augmente la probabilité qu'une d'elles paraisse bonne par hasard. Le seuil de Sharpe d'une stratégie se calcule donc sur son propre registre d'essais **et** le système publie le nombre total d'hypothèses testées sur des rendements. Ce total sert au rapport de promotion : un promu parmi 30 hypothèses ne se lit pas comme un promu parmi 3.

## Entonnoir (une étape franchie à la fois)

| Étape | Coût | Données de rendement lues | Sortie |
|---|---|---|---|
| 0. Tri T1 à T10 (`validation-edge` § 0 bis) | 10 min | Aucune | Écartée ou fiche |
| 1. Criblage sur données déjà lues | Quelques heures | Seulement des blocs déjà consommés, déclarés | Écartée, ou fiche complète |
| 2. Fiche, gel, E01 et E02 | 1 à 2 jours | Développement et validation | Rejetée ou portes suivantes |
| 3. Hors échantillon, une seule fois | 1 jour | Le bloc réservé | Rejetée ou papier |
| 4. Papier en avant | 8 à 26 semaines | Aucune donnée passée | Dossier de promotion |

L'étape 1 est la plus rentable : elle réutilise des résultats déjà consommés pour éliminer à coût nul, sans ouvrir de nouvelle donnée.

## Tableau

| N° | Hypothèse | Date | Étape atteinte | Statut | Pièce |
|---|---|---|---|---|---|
| H01 | Tendance Donchian, 10 perpétuels | 31/10/2026 | 3 | rejetée | `strategies/STRAT-20261031-01/resultats/VERDICT_E10_E11.md` |
| H02 | Portage delta neutre, 6 grandes paires | 31/10/2026 | 3 | rejetée pour ce jeu de paramètres | `strategies/STRAT-20261031-02/` |
| H03 | Momentum transversal résiduel 3L/3S | 31/10/2026 | 2 | rejetée | `strategies/STRAT-20261031-03/resultats/VERDICT_PORTES_E01_E02.md` |
| H04 | Rebond après cascades de liquidations | 31/10/2026 | 0 | non testable (65 trades pour 100) | `strategies/STRAT-20261031-04/` |
| H05 | Encombrement financement et intérêt ouvert 3L/3S | 02/11/2026 | 2 | rejetée | `strategies/STRAT-20261102-05/resultats/VERDICT_E01.md` |
| H06 | Wallets Solana, rétro-ingénierie | 01/11/2026 | 2 (pilote) | close, non concluant | `strategies/STRAT-DEX/` |
| H07 | Maker passif Polymarket | 01/11/2026 | 1 | écartée (−15,42 $ pour 1 000 $ avec file) | `polymarket/resultats/20261101T091123Z_file_attente_rapport.md` |
| H08 | Calibration Polymarket (lecture des clauses) | 01/11/2026 | 4 (journal) | en cours : 37 prévisions écrites sans prix le 09/11/2026 (36 avec prix relevé après), 4 résolues au 12/11/2026 dont 3 comparables au marché (Brier propre 0,2638 contre 0,0062 : pire, échantillon de 3) ; palier 1 à 100 résolues | `polymarket/calibration/` |
| H09 | Tokens pump.fun franchissant 5 M$ | 01/11/2026 | 1 | requête prête, jamais exécutée | `recherche/dex_faisabilite/` |
| H10 | Portage couvert sur financement **positif** des alts encombrés | 02/11/2026 | 1 | **écartée au criblage** (voir `PISTES_20261102.md`) | ce registre |
| H11 | Portage couvert sur financement **négatif** (long perpétuel, short spot emprunté) | 02/11/2026 | 0 | **écartée au tri (T4)** : aucun historique public des taux d'emprunt sur marge, API limitée à 90 jours avec clé (contrôle de Téo, 02/11/2026) | `PISTES_20261102.md` |
| H12 | Dérive des perpétuels nouvellement cotés | 02/11/2026 | 3 | **rejetée au hors échantillon** le 06/11 (E19 : Sharpe 1,398 < 1,72, borne basse de l'IC −0,04 %) ; rouverte en H12-bis | `strategies/STRAT-20261102-06/FICHE_STRAT-20261102-06.md` |
| H13 | Levier agrégé comme filtre de risque sur BTC | 02/11/2026 | 0 | tri du 12/11/2026 : pas une brique, filtre de risque commun aux deux briques ; puissance faible | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H09b | Cycle de vie des tokens pump.fun (taux de base à 30 jours) | 01/11/2026 | 1 | requête prête, jamais exécutée | `recherche/dex_faisabilite/taux_de_base_cycle_de_vie.sql` |
| H14 | Dérive de prix autour de l'heure de versement du financement | 02/11/2026 | 0 | **écartée au tri le 12/11/2026 (T2)** : un versement courant vaut environ 0,01 %, un aller-retour au moins 0,14 % | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H15 | Réservé (numéro non attribué, conservé pour ne pas renuméroter) | 02/11/2026 | — | — | — |
| H16 | Short après annonce de délistage | 02/11/2026 | 0 | **écartée au tri le 12/11/2026 (T3, T5)** : 89 retraits sur 49 dates depuis 2021, baisse immédiate à l'annonce | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H17 | Cotation au comptant d'un actif déjà coté en perpétuel | 02/11/2026 | 0 | tri du 12/11/2026 : affaiblie, non prioritaire (T4, T5) ; même famille d'événements que STRAT-06 | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H18 | Réservé | 02/11/2026 | — | — | — |
| H19 | Réservé | 02/11/2026 | — | — | — |
| H20 | Divergence de financement Binance–Bybit | 02/11/2026 | 0 | tri du 12/11/2026 : affaiblie (T2 inconnu, T6 deux comptes, T9 famille du portage écartée trois fois) ; criblage sur le financement seul possible, non lancé | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H21 | Après « graduation » pump.fun | 02/11/2026 | 0 | à trier, voisine de H09 (T9) | — |
| H22 | Variables « smart money » centrées sur les tokens | 02/11/2026 | 0 | à trier, voisine de H06 close (T9, L5) | — |
| H23 | Réservé | 02/11/2026 | — | — | — |
| H24 | Biais du longshot Polymarket (contrats 1 à 10 c) | 02/11/2026 | 0 | passe le tri sous conditions T2, T4, T6 ; fusion avec H25 | `recherche/TRI_H24_H25_POLYMARKET.md` |
| H25 | Portage de quasi-certitude Polymarket (95 à 99 c, derniers jours) | 02/11/2026 | 0 | passe le tri, affaiblie (prime de risque probable) ; bloquée par T6 | `recherche/TRI_H24_H25_POLYMARKET.md` |
| H12-bis | STRAT-06-bis : dérive des jeunes perpétuels, cohortes quotidiennes (1/7 par jour), verdict par le papier aveugle | 09/11/2026 | 4 (papier) | rouverte après rejet de la v1 au hors échantillon (E19 : Sharpe 1,398 < 1,72, borne basse de l'IC < 0) ; critères du papier à figer | `strategies/STRAT-20261102-06/FICHE_STRAT-06-BIS.md` |
| H26 | Témoin « short de petites alts spéculatives couvert » (contrôle de taille et d'illiquidité de STRAT-06) | 05/11/2026 | 0 | à trier | `recherche/RECHERCHE_FONDAMENTALE_STRAT-06.md` § 6.3 |
| H27 | Couverture moins chère que le perpétuel BTC | 05/11/2026 | 0 | à trier | idem |
| H28 | Dérive selon le flottant et les calendriers de déblocage | 05/11/2026 | 0 | à trier, T4 élevé | idem |
| H29 | Encombrement des shorts (financement payé) comme filtre | 05/11/2026 | 0 | à trier, voisine de STRAT-05 (T9) | idem |
| H30 | Emprunt sur marge avant le perpétuel (test direct de Miller) | 05/11/2026 | 0 | à trier, T4 élevé | idem |
| H31 | STRAT-07 : portage de financement conditionnel aux pointes (long comptant, short perpétuel) | 09/11/2026 | 2 (fiche, jamais figée) | **écartée le 12/11/2026, comme H10** : criblage favorable sur la moyenne (50/10 : +6,89 %/an) mais +3,59 %/an sur la validation (seuil 3,875 %), +2,90 %/an hors 2021, 46 % du gain de la validation sur des épisodes sans comptant ; aucun essai lancé, hors échantillon non ouvert ; 3 lectures du criblage et 2 recalculs d'audit | `strategies/STRAT-20261109-07/FICHE_STRAT-20261109-07.md` § 11, `revues/AUDIT_STRAT-07_FABLE.md` |
| H32 | STRAT-08 : contre-tendance après cascade de liquidations, données 1m | 09/11/2026 | 2 (fiche, décisions prises) | règles validées le 09/11 sauf précision sur Y (intérêt ouvert en contrats) ; détection et contrôle sans rendement codés (11 tests) ; contrôle à lancer. **Audit adverse du 09/11 : 3 constats bloquants avant gel** (horodatage des metrics non corrigé, archive débutant le 01/12/2021, départage non écrit) ; aucun rendement lu. **12/11 : les 3 constats bloquants levés par décision et correction de code** (+ 5 min sur tout l'historique, développement dès le 01/12/2021, départage par le volume, entrée à 5 min) ; Y validé en contrats et exigence 300/100 lue sur la pause de 4 h (12/11) ; contrôle sans rendement en cours sur le serveur depuis le 12/11 à 11:32 UTC | `strategies/STRAT-20261109-08/FICHE_STRAT-20261109-08.md` § 13, `revues/AUDIT_STRAT-08_FABLE.md` |
| H33 | Écart du week-end sur les perpétuels non crypto de Binance (métaux, pétrole, actions), retour à l'ouverture du lundi | 12/11/2026 | 0 | **écartée au tri pour l'instant (T3)** : cotés depuis 12/2025, moins de 2 ans d'historique ; seule voie : papier en avant | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H34 | Prime de variance sur options BTC, à risque défini (strangle court vendu, ailes achetées) | 12/11/2026 | 0 | passe le tri sous conditions : T4 (historique d'options gratuit et daté, à auditer sans prix), T6 (nouvelle plateforme), T7 (ailes obligatoires) ; rien de lancé | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |
| H35 | Portage comptant contre contrat à terme daté | 12/11/2026 | 0 | **écartée au tri (T2, T9)** : famille du portage, rendement proche du taux court | `recherche/TRI_TROISIEME_BRIQUE_20261112.md` |

Hypothèses testées sur des rendements à ce jour : H01, H02, H03, H05, H06, H07, H12, H31, soit **8** (12/11/2026 ; H12 rejetée au hors échantillon, rouverte en H12-bis dont le seul test est le papier ; H31 comptée parce que son criblage a calculé des rendements de financement sur trois grilles, à la différence de H10, écartée sur un chiffre déjà lu).
