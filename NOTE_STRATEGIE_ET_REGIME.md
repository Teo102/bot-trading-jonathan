# NOTE_STRATEGIE_ET_REGIME — version du 31/10/2026 (v3)

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

**Alertes ouvertes :** piratage Binance ≈ 6,3 Md$ (retraits suspendus, reprise annoncée le 01/11) ; mi-mandat US le 03/11 (résolutions Polymarket en masse) ; résidence de Jonathan : **Émirats** (confirmée le 31/10) ; Polymarket accessible, statut légal en zone grise [risque faible, non nul].

## 2. Règles de régime (appliquées par le cerveau tant que le régime ne change pas)

- Thèse haussière : ratio rendement/risque minimal relevé à 3 et taille à la moitié du risque par position de `commun-trading` § 3.
- Thèse baissière ou absence de trade : règles normales.
- Aucune exposition dépendant d'une plateforme dont les retraits sont suspendus.
- Marché Polymarket : grille de risque de résolution obligatoire ; ordres maker par défaut.

Ces ajustements sont des propositions du conseil ; ils deviennent des règles après accord de Jonathan (`cerveau-trading` § 6).

## 3. Moteurs (révisés le 31/10, v3)

| Moteur | Statut | Condition |
|---|---|---|
| A. Swing filtré, 15–25 trades/mois (BTC, ETH, alts liquides, perps) | backtest dans freqtrade puis dry-run | ≥ 100 trades simulés, espérance > 0,2 R nette, drawdown < 20 %, `lookahead-analysis` propre |
| B. Polymarket, prévisions calibrées en **maker** (Kelly/4 tant que la calibration n'est pas mesurée) | actif en petite taille | journal de calibration ; Kelly/2 seulement si l'intervalle de confiance de l'edge est > 0 |
| C. Portage de financement delta neutre | réserve | capital et plateformes renseignés |
| Rejetées | intraday taker, arbitrage taker « somme ≠ 1 » (frais 2026), marchés 5–15 min, sniping, MEV, suivi d'« initiés », TradingAgents ou ai-hedge-fund comme moteurs | coûts, latence, aucun edge démontré |

**Frais Polymarket 2026 :** taker = parts × taux × p × (1 − p), soit jusqu'à 1–1,75 ¢ par part à 50 ¢ ; maker = 0 avec rebates de 15 à 25 % ; géopolitique sans frais.

**Edge visé :** discipline écrite, tests avant capital, lecture des clauses, patience. Aucun edge de vitesse. Les règles de régime du § 2 sont des hypothèses à backtester, pas des règles validées.

**Taux de base :** environ 70 % des comptes particuliers perdent, sur Polymarket (Galaxy, oct. 2026) comme sur les CFD (ESMA). Sans edge prouvé, l'espérance du système est négative.

## 4. Ce qui change le régime

Passage en « neutre » si deux conditions sur trois : BTC au-dessus de 87 k$ en clôture hebdomadaire ; trois semaines d'entrées nettes ETF ; 10 ans sous 4,5 %.
Passage en « crise » si : cassure de 76 k$ avec hausse du financement, ou retraits Binance non rétablis au 03/11.

## 5. Dates

01/11 retraits Binance · 02/11 flux ETF finaux d'octobre · 03/11 mi-mandat · ≈ 09–12/11 inflation d'octobre [date à vérifier] · 09/12 décision Fed.

## 6. Données manquantes (à combler)

Résidence fiscale aux Émirats à inscrire dans `commun-trading` ; support Hyperliquid dans freqtrade [à confirmer] ; données Hyperliquid via SQD (connecteur par URL https://portal.sqd.dev/mcp) ; financement Bybit et Hyperliquid ; carte des liquidations (connecteur CoinGlass) ; BCE et BoJ ; flux on-chain memecoins, IA et L2 ; paramètres de `commun-trading` § 3.
