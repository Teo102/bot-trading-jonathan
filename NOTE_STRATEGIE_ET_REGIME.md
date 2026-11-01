# NOTE_STRATEGIE_ET_REGIME — version du 01/11/2026 (v4, indicateurs de régime du 31/10)

Document de référence pour `cerveau-trading` et `synthese-marche`. Relu avant chaque chaîne T1, P1 ou M1. Remplacé à chaque nouvelle synthèse ; une note de plus de 7 jours est signalée comme ancienne. Détail et sources : `2026-10-31_RADIOGRAPHIE_ET_AUDIT.md`, `2026-10-31_SQD_RENTABILITE_INTEGRATION.md` et `2026-10-31_AUDIT_7_REPOS_ET_MAXIMISATION.md`.

## 1. Régime en vigueur

**Aversion au risque — tendance baissière sur 12 mois — liquidité en resserrement.**

| Indicateur | Valeur (source, heure UTC) | Feu |
|---|---|---|
| BTC | 77,5 k$, −29 % sur un an (CoinGecko, 31/10 ≈ 16:20) | rouge |
| Fed | 3,75–4 %, hausse de décembre à 82,6 % (FedWatch via Fox Business, 28/10) | rouge |
| Taux 10 ans US / DXY | 4,93 % / 101,96 (Stocktwits, 30/10) | orange |
| Flux ETF BTC octobre | ≈ −516 M$ (Farside via crypto.news, 31/10) | rouge |
| Dominance BTC | 59,2 % (CoinGecko, 31/10) | orange |
| Financement BTC | positif malgré la baisse (CoinDesk, 30/10) | orange : levier acheteur encore chargé |

**Alertes ouvertes :** piratage Binance ≈ 6,3 Md$ (retraits suspendus, reprise annoncée le 01/11 [non confirmée au 01/11, aucune source récente trouvée]) ; mi-mandat US le 03/11 (résolutions Polymarket en masse) ; résidence de Jonathan : **Émirats** (confirmée le 31/10) ; Polymarket accessible, statut légal en zone grise [risque faible, non nul].

## 2. Règles de régime (appliquées par le cerveau tant que le régime ne change pas)

- Thèse haussière : ratio rendement/risque minimal relevé à 3 et taille à la moitié du risque par position de `commun-trading` § 3.
- Thèse baissière ou absence de trade : règles normales.
- Aucune exposition dépendant d'une plateforme dont les retraits sont suspendus.
- Marché Polymarket : grille de risque de résolution obligatoire ; ordres maker par défaut.

Ces ajustements sont des propositions du conseil ; ils deviennent des règles après accord de Jonathan (`cerveau-trading` § 6).

## 3. Matrice des 5 stratégies (révisée le 01/11, v4)

Aucun edge n'est validé à ce jour. Les chiffres ci-dessous sont des résultats de recherche, sans verdict de rentabilité.

| Stratégie | Statut | Mesure principale (source, heure UTC) | Principal contre-argument | Prochaine porte |
|---|---|---|---|---|
| STRAT-20261031-01, tendance Donchian, 10 perpétuels | `backtest`, E10-E11 verrouillés | E00-ref 2021-01 à 2025-07 : 178 trades, +0,268 R, IC 90 % par blocs [-0,035 ; +0,614], Sharpe réévalué 0,56, DD réévalué 12,8 %, DSR réévalué 0,635 pour N=13 (freqtrade, 31/10 22:33-22:44, analyse du 01/11) | Trois trades portent 81 % du gain, shorts à -0,119 R, l'ordre de la whitelist fait varier E01 de +0,011 à +0,468 R, DOGE et TRX choisis avec le recul | Jonathan valide `AVENANT_AVANT_E10.md`, puis avocat du diable et ouverture unique de E10-E11 |
| STRAT-20261031-02, portage de financement delta neutre | `recherche`, rejet proposé | APR net 12 mois : Binance -3,07 %, Bybit -5,71 %, contre 3,875 % de taux court (`apr_net.py`, 31/10 22:41) | Rejet valable pour ce jeu de paramètres seulement. Hors échantillon consommé, toute nouvelle règle est une nouvelle stratégie | Décision de Jonathan sur le rejet |
| STRAT-20261031-03, momentum transversal | `recherche`, aucun test | 26 essais préenregistrés. Un vrai Sharpe de 1 passerait le seuil dans 18 % des cas (calcul de puissance de la fiche) | Avocat du diable : affaiblie, proche du rejet. Survivants, squeezes de shorts, moteur séparé à écrire | Jonathan tranche la lecture « Top 3 / Flop 3 », le plafond de positions et le critère C3 |
| STRAT-20261031-04, retour à la moyenne après cascades | `recherche`, non testable en l'état | 65 trades pour 100 requis, 10 hors échantillon pour 30, ratio prévu médian 0,29 (comptage du 01/11 00:14) | Événement rare, objectif trop proche, carnet du choc du 10/10/2025 [non mesuré] | Jonathan choisit : attente, version 2 déclarée, données payantes ou lecture de contexte |
| Polymarket maker et lecture des règles UMA (ex-moteur B) | mesure, aucune position au journal | Classement du 01/11 00:13 : net hypothétique à 1 h de 4,83 $ pour 1 000 [2,47 ; 6,70], contre 4,32 [-1,07 ; 6,24] au passage de 22:40 le 31/10, donc échantillon instable. Hors mi-mandat au 31/10 22:40 : intervalle contenant zéro | Le simulateur suppose un remplissage sur chaque trade public. Calibration à mesurer sur au moins 100 prévisions, zone grise légale aux Émirats | Journal de calibration, Kelly/4 tant qu'elle n'est pas mesurée, après le mi-mandat |

**Écartées :** intraday taker, arbitrage taker « somme ≠ 1 », marchés 5–15 min, sniping, MEV, suivi d'« initiés », TradingAgents ou ai-hedge-fund comme moteurs (coûts, latence, aucun edge démontré).

**Frais Polymarket :** la documentation lue le 31/10/2026 donne taker = parts × taux × p × (1 − p), maker = 0 et rebate selon la catégorie. Mais l'API `feeSchedule` donne un taux nul sur 1 973 des 2 086 marchés classés et sur 20 des 20 du classement (31/10 22:40 UTC), avec un rebate nul. Cause [non vérifiée]. Le potentiel de rebate se lit donc marché par marché.

**Correction de la radiographie :** le marché Iran vaut 177,4 M$ sur Gamma et 478,9 M$ pour l'événement, pas 120 M$ (lecture du 31/10). Le chiffre Fidonis de 7,3 % reste [source unique].

**Edge visé :** discipline écrite, tests avant capital, lecture des clauses, patience. Aucun edge de vitesse. Les règles de régime du § 2 sont des hypothèses à backtester, pas des règles validées.

**Taux de base :** environ 70 % des comptes particuliers perdent, sur Polymarket (Galaxy, oct. 2026) comme sur les CFD (ESMA). Sans edge prouvé, l'espérance du système est négative.

## 4. Ce qui change le régime

Passage en « neutre » si deux conditions sur trois : BTC au-dessus de 87 k$ en clôture hebdomadaire ; trois semaines d'entrées nettes ETF ; 10 ans sous 4,5 %.
Passage en « crise » si : cassure de 76 k$ avec hausse du financement, ou retraits Binance non rétablis au 03/11.

## 5. Dates

01/11 retraits Binance · 02/11 flux ETF finaux d'octobre · 03/11 mi-mandat · ≈ 09–12/11 inflation d'octobre [date à vérifier] · 09/12 décision Fed.

## 6. Données manquantes (à combler)

Résidence fiscale aux Émirats à inscrire dans `commun-trading` ; support Hyperliquid dans freqtrade [à confirmer] ; données Hyperliquid via SQD (connecteur par URL https://portal.sqd.dev/mcp) ; financement Bybit et Hyperliquid ; carte des liquidations (connecteur CoinGlass) ; BCE et BoJ ; flux on-chain memecoins, IA et L2 ; paramètres de `commun-trading` § 3.
