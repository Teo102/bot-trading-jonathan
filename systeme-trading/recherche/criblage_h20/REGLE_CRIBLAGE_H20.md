# Règle du criblage de H20 (écart de financement Binance–Bybit), écrite avant tout calcul

Écrite le 23/11/2026 par Claude, à la demande de Jonathan et Téo. **Statut : PROPOSÉE.** Aucune donnée de financement n'a été téléchargée ni lue pour ce criblage. La règle est poussée sur GitHub avant le premier calcul ; toute modification après le premier calcul est interdite (une variante serait un nouvel essai compté). Résultat de recherche : aucun ordre, aucune clé, capital nul.

## 0. Ce que le criblage peut et ne peut pas dire

- Il ne lit **que le financement**. Il ignore l'écart de prix entre les deux perpétuels à l'entrée et à la sortie, les transferts de marge entre plateformes et le risque de liquidation d'une jambe. **C'est une borne haute.** S'il échoue, H20 s'arrête à coût presque nul. S'il passe, il faut une seconde étape avec les prix des deux plateformes avant toute fiche.
- **Famille du portage de financement** : H02 rejetée, H10 et H31 écartées. C'est le quatrième essai de la famille. Le criblage compte comme un essai au registre (N + 1).
- **Contamination déclarée** : le tri du 19/11 a lu l'historique de financement d'une seule paire de Bybit (BTCUSDT, réponse de l'API), sans calcul d'écart.

## 1. Données

- Binance : financement des perpétuels USDT (data.binance.vision, archives mensuelles `fundingRate`, puis fapi pour le mois en cours).
- Bybit : `/v5/market/funding/history` (public, sans clé), complété par `public.bybit.com` si une série est incomplète.
- Période : du 01/01/2021 au 31/10/2026. Les mois incomplets d'un côté sont signalés et exclus pour la paire concernée.
- **Intervalles différents** (8 h, 4 h ou 1 h selon la paire et l'époque) : chaque série est ramenée à des fenêtres de 8 heures alignées sur 00:00, 08:00 et 16:00 UTC, en sommant les versements de la fenêtre.

## 2. Univers, sans biais du survivant

Au premier jour de chaque trimestre, les **30 perpétuels USDT présents sur les deux plateformes depuis au moins 60 jours** qui ont le plus grand volume en USDT sur Binance pendant les 30 jours précédents (bougies journalières de data.binance.vision). La liste est figée pour le trimestre. Une paire retirée en cours de trimestre est fermée à sa dernière fenêtre connue.

## 3. Règle de décision

À la fin de chaque fenêtre t, pour chaque paire de l'univers :
- D = moyenne de (financement Bybit − financement Binance) sur les 3 dernières fenêtres (24 heures), données ≤ t ;
- **entrée** si |D| ≥ **0,02 % par fenêtre de 8 heures** (environ 22 % par an) : vente du perpétuel de la plateforme qui paie le plus, achat sur l'autre, même notionnel ;
- **sortie** si |D| < **0,005 %** ou si D change de signe ;
- au plus **10 paires** ouvertes, notionnel égal de 1/10 ; au-delà, les plus grands |D| passent, égalité par ordre alphabétique ;
- le gain d'une position est la somme des écarts de financement **des fenêtres qui suivent la décision** (t + 1 et après), jamais celui de la fenêtre qui a déclenché l'entrée.

Deux seuils, un plafond : trois paramètres, fixés ici sans aucune donnée.

## 4. Coûts et capital

- **Frais preneur** des deux plateformes, quatre ordres par aller-retour : 0,05 % (Binance) et 0,055 % (Bybit) par côté, soit 0,21 % par aller-retour, plus un glissement de 0,02 % par ordre pour les 10 plus gros volumes du trimestre et 0,05 % pour les autres. C'est la version du verdict.
- Version teneur de marché (0,02 % par ordre, sans glissement) : affichée pour information, jamais utilisée pour le verdict.
- **Capital** : une marge pleine de chaque côté, soit un capital égal à deux fois le notionnel (levier 1 sur chaque jambe). Le rendement à levier 3 est affiché pour information ; il suppose qu'aucune jambe n'est liquidée, ce que le criblage ne vérifie pas.

## 5. Lecture bloc par bloc et critères, écrits avant le calcul

Blocs : les années civiles 2021, 2022, 2023, 2024, 2025 et 2026 (jusqu'au 31/10). Chaque bloc est lu séparément (leçon L13).

H20 passe le criblage seulement si **toutes** les conditions suivantes sont remplies, sur le net du verdict et le capital à levier 1 :
1. net annualisé ≥ **5 %** sur au moins 4 des 6 blocs ;
2. net positif **sur chaque bloc hors la meilleure année** ;
3. net annualisé de l'ensemble hors la meilleure année ≥ **3 %** ;
4. aucune paire ne fait plus de **30 %** du gain net, aucun mois plus de **25 %** ;
5. au moins **100 positions** sur la période.

Sinon, H20 est écartée, avec le même statut que H10 et H31.

## 6. Sorties prévues

`criblage_h20.py`, des tests synthétiques (alignement des fenêtres, absence d'anticipation, univers trimestriel, coûts), un JSON des résultats par bloc, et une note qui donne le verdict des critères du § 5 avant tout commentaire.

## 7. Décisions attendues de Jonathan et Téo avant le calcul

1. Seuils d'entrée et de sortie (0,02 % et 0,005 % par 8 heures), plafond de 10 paires.
2. Coûts preneur du verdict et capital à levier 1.
3. Critères du § 5.
4. Accès à Bybit depuis le pays de résidence de chacun [non vérifié] : même si le criblage passe, sans accès il n'y a pas de brique.
