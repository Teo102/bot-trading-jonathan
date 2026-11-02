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
| H08 | Calibration Polymarket (lecture des clauses) | 01/11/2026 | 4 (journal) | en cours, aucune prévision | `polymarket/calibration/` |
| H09 | Tokens pump.fun franchissant 5 M$ | 01/11/2026 | 1 | requête prête, jamais exécutée | `recherche/dex_faisabilite/` |
| H10 | Portage couvert sur financement **positif** des alts encombrés | 02/11/2026 | 1 | **écartée au criblage** (voir `PISTES_20261102.md`) | ce registre |
| H11 | Portage couvert sur financement **négatif** (long perpétuel, short spot emprunté) | 02/11/2026 | 0 | en tri, données d'emprunt à vérifier | `PISTES_20261102.md` |
| H12 | Dérive des perpétuels nouvellement cotés | 02/11/2026 | 0 | tri passé, fiche à écrire | `PISTES_20261102.md` |
| H13 | Levier agrégé comme filtre de risque sur BTC | 02/11/2026 | 0 | en tri, puissance faible | `PISTES_20261102.md` |

Hypothèses testées sur des rendements à ce jour : H01, H02, H03, H05, H06, H07, soit **6**.
