# NOTE_STRATEGIE_ET_REGIME — version du 01/11/2026 (v5, indicateurs du 01/11 en soirée)

Document de référence pour `cerveau-trading` et `synthese-marche`. Relu avant chaque chaîne T1, P1 ou M1. Remplacé à chaque nouvelle synthèse ; une note de plus de 7 jours est signalée comme ancienne. Détail et sources : `2026-10-31_RADIOGRAPHIE_ET_AUDIT.md`, `2026-10-31_SQD_RENTABILITE_INTEGRATION.md` et `2026-10-31_AUDIT_7_REPOS_ET_MAXIMISATION.md`.

## 1. Régime en vigueur

**Aversion au risque — tendance baissière sur 12 mois — liquidité en resserrement.**

| Indicateur | Valeur (source, heure UTC) | Feu |
|---|---|---|
| BTC | 78,1 k$, +0,7 % sur 24 h ; capitalisation totale 2,61 T$, −3,1 % sur 24 h (CoinGecko, 01/11 ≈ 17:17) | rouge |
| Fed | 3,75–4 %, maintien le 28/10 par 10 voix contre 2 (Cook et Hammack pour une hausse) ; hausse de décembre ≈ 85 % (Bloomberg via Admiral Markets, 28/10) | rouge |
| Taux 10 ans US / DXY | 4,93 % / 101,96 (Stocktwits, 30/10) [non relu le 01/11] | orange |
| Flux ETF BTC octobre | −515,0 M$ sur 22 séances au 30/10, dont −643,3 M$ le 30/10 (TFTC, relu le 01/11) | rouge |
| Dominance BTC | 60,0 % (CoinGecko, 01/11 ≈ 17:17) | orange |
| Financement BTC | positif malgré la baisse (CoinDesk, 30/10) [non relu le 01/11] | orange : levier acheteur encore chargé |

**Alertes ouvertes :** piratage Binance ≈ 6,3 Md$ : retraits rouverts par phases le 01/11 (BTC, ETH, USDT, USDC, BNB, XRP et 15 chaînes), 95 % des actifs remplacés selon Binance, ≈ 3 Md$ gelés, preuve de réserves promise et non publiée (CoinDesk, Forbes, 01/11) ; mi-mandat US le 03/11 (résolutions Polymarket en masse) ; résidence de Jonathan : **Émirats** (confirmée le 31/10) ; Polymarket accessible, statut légal en zone grise (le registre UMA § 4 note un risque pénal non chiffrable).

## 2. Règles de régime (appliquées par le cerveau tant que le régime ne change pas)

- Thèse haussière : ratio rendement/risque minimal relevé à 3 et taille à la moitié du risque par position de `commun-trading` § 3.
- Thèse baissière ou absence de trade : règles normales.
- Aucune exposition dépendant d'une plateforme dont les retraits sont suspendus.
- Marché Polymarket : grille de risque de résolution obligatoire ; ordres maker par défaut.

Ces ajustements sont des propositions du conseil ; ils deviennent des règles après accord de Jonathan (`cerveau-trading` § 6).

## 3. Matrice des 5 stratégies (révisée le 01/11, v4)

Aucun edge n'est validé à ce jour et le moteur autonome n'a aucune stratégie candidate au papier. Les chiffres ci-dessous sont des résultats de recherche.

| Stratégie | Statut | Mesure principale (source, heure UTC) | Principal contre-argument | Prochaine porte |
|---|---|---|---|---|
| STRAT-20261031-01, tendance Donchian, 10 perpétuels | `rejetée` le 01/11 | E10 : 46 trades, +0,147 R, IC 90 % par blocs [-0,376 ; +0,744], Sharpe réévalué 0,354, DD réévalué 6,2 %, DSR réévalué 0,313. E11 : +0,135 R (freqtrade, 01/11 08:50) | Trois critères sur sept échouent. Un seul trade porte 117 % du gain | Aucune. Toute reprise est une nouvelle stratégie, jugée sur des données postérieures au 31/10/2026 |
| STRAT-20261031-02, portage de financement delta neutre | `rejetée` pour ce jeu de paramètres, le 01/11 | APR net 12 mois : Binance -3,07 %, Bybit -5,71 %, contre 3,875 % de taux court (`apr_net.py`, 31/10 22:41) | Hors échantillon consommé, toute nouvelle règle est une nouvelle stratégie | Aucune |
| STRAT-20261031-03, momentum transversal résiduel 3L/3S | `recherche`, règles D1 à D6 prêtes à geler | Univers contrôlé sur volumes seuls : avec 50 M$ et `trou_max_jours = 7`, 9 semaines du développement sous 30 noms (`taille_univers_20261101T124557Z.md`). Trou d'archive du 26-27/02/2022 comblé par les journalières (patch 0007, tests 21, 12 et 1 verts sur la machine de Téo, 01/11) | Puissance faible : un vrai Sharpe de 1 passe C1 dans 18 % des cas | Gel des règles, puis E01 unique |
| STRAT-20261031-04, retour à la moyenne après cascades | `recherche`, non testable en l'état, maintenu le 01/11 | 65 trades pour 100 requis, 10 hors échantillon pour 30, ratio prévu médian 0,29 (comptage du 01/11 00:14) | Événement rare, objectif trop proche, carnet du choc du 10/10/2025 [non mesuré] | Aucune tant que les trades manquent |
| Polymarket, lecture des règles UMA et calibration | monitoring en lecture, aucun capital avant la fin du mi-mandat et avant l'avis juridique (décision du 01/11) | Simulateur avec file d'attente (01/11 09:11) : maker au meilleur prix, hors mi-mandat, −15,42 $ pour 1 000 $ [−35,89 ; −8,43]. Le maker passif est écarté ; reste l'information et la lecture des clauses | Journal de calibration vide, palier 1 à 100 prévisions | Premières prévisions hors mi-mandat |
| STRAT-DEX, wallets Solana (pilote) | `recherche` par exception à la grille T1 à T10 (échec sur T4 et T9) | 400 wallets tirés, 179 lus, 70 passent F3 ; persistance en calcul sur le serveur, résultat attendu dans la nuit du 01 au 02/11 | Circularité, survivants, valorisation des reliquats | Verdict de l'avenant 2 (`strategies/STRAT-DEX/AVENANT_2_AVANT_RESULTATS.md`) |
| STRAT-05, encombrement financement et intérêt ouvert | annoncée, aucune fiche | — | Information publique très surveillée | Fiche après E01 de STRAT-03 |

**Écartées :** intraday taker, arbitrage taker « somme ≠ 1 », marchés 5–15 min, sniping, MEV, suivi d'« initiés », TradingAgents ou ai-hedge-fund comme moteurs (coûts, latence, aucun edge démontré).

**Frais Polymarket :** la documentation lue le 31/10/2026 donne taker = parts × taux × p × (1 − p), maker = 0 et rebate selon la catégorie. Mais l'API `feeSchedule` donne un taux nul sur 1 973 des 2 086 marchés classés et sur 20 des 20 du classement (31/10 22:40 UTC), avec un rebate nul. Cause [non vérifiée]. Le potentiel de rebate se lit donc marché par marché.

**Correction de la radiographie :** le marché Iran vaut 177,4 M$ sur Gamma et 478,9 M$ pour l'événement, pas 120 M$ (lecture du 31/10). Le chiffre Fidonis de 7,3 % reste [source unique].

**Edge visé :** discipline écrite, tests avant capital, lecture des clauses, patience. Aucun edge de vitesse. Les règles de régime du § 2 sont des hypothèses à backtester, pas des règles validées.

**Taux de base :** environ 70 % des comptes particuliers perdent, sur Polymarket (Galaxy, oct. 2026) comme sur les CFD (ESMA). Sans edge prouvé, l'espérance du système est négative.

## 4. Ce qui change le régime

Passage en « neutre » si deux conditions sur trois : BTC au-dessus de 87 k$ en clôture hebdomadaire ; trois semaines d'entrées nettes ETF ; 10 ans sous 4,5 %.
Passage en « crise » si : cassure de 76 k$ avec hausse du financement, ou nouvelle suspension des retraits Binance, ou preuve de réserves non publiée au 15/11 [seuil proposé le 01/11, à valider].

## 5. Dates

02/11 flux ETF finaux d'octobre · 03/11 mi-mandat US · ≈ 10–13/11 inflation d'octobre [date à vérifier] · 09/12 décision Fed (hausse ≈ 85 % au 28/10) · preuve de réserves Binance [date non annoncée]

## 6. Données manquantes (à combler)

Résidence fiscale aux Émirats à inscrire dans `commun-trading` ; support Hyperliquid dans freqtrade [à confirmer] ; données Hyperliquid via SQD (connecteur par URL https://portal.sqd.dev/mcp) ; financement Bybit et Hyperliquid ; carte des liquidations (connecteur CoinGlass) ; BCE et BoJ ; flux on-chain memecoins, IA et L2 ; paramètres de `commun-trading` § 3.
