# Criblage de STRAT-07 — portage de financement conditionnel aux pointes

Écrit le 09/11/2026, **avant tout calcul**. Étape 1 de l'entonnoir : aucune fiche, aucun prix d'entrée ni de sortie. Résultat de recherche, aucun ordre.

## 1. Question

Une pointe de financement dure-t-elle assez longtemps pour payer un aller-retour long au comptant et short au perpétuel, et le portage qui en résulte bat-il le taux court ?

H10 a été écartée le 02/11 à environ 2,5 % par an sur le capital. STRAT-07 n'existe que si la sélection par pointes change ce chiffre (tri T2 et T9, `recherche/TRI_STRAT-07_STRAT-08.md`).

## 2. Règle de décision, fixée avant le calcul

- **Données :** financement (fundingRate), volumes journaliers des perpétuels, liste et date des paires au comptant. Du 01/01/2021 au 28/07/2025 02:00 UTC. Ce sont des blocs consommés, contamination déclarée. La suite reste réservée au hors échantillon de STRAT-07.
- **Univers :** perpétuels USDT ayant une paire au comptant de même nom, cotée depuis au moins un mois entier. Médiane du volume journalier du perpétuel sur les 30 jours précédents ≥ 20 M USDT.
- **Épisode, sans anticipation :**
  - le versement i est observé ; si son taux annualisé dépasse le seuil d'entrée, on entre après lui ;
  - on encaisse les versements suivants, y compris les négatifs ;
  - on sort après le premier versement observé sous le seuil de sortie.
- **Grille déclarée :** entrée / sortie à 30 % / 10 %, 50 % / 10 % et 50 % / 20 % par an. Les trois sont publiées.
- **Coût d'un aller-retour à quatre jambes :** 0,5 % du notionnel (comptant 0,10 % × 2, perpétuel 0,05 % × 2, glissement 0,05 % × 4).
- **Portefeuille indicatif :**
  - 10 emplacements, chacun 1/10 du capital, moitié au comptant, moitié en marge du short (notionnel = capital / 20) ;
  - un épisode est pris s'il reste un emplacement libre à son début.
- **STRAT-07 obtient une fiche si, pour la grille 30 / 10 ou 50 / 10 :**
  - le financement brut médian d'un épisode est ≥ 3 × 0,5 % = **1,5 %** (critère T2) ;
  - **et** le rendement indicatif sur capital dépasse **3,875 % par an** (taux court de STRAT-02, critère de H10).
- **Sinon, STRAT-07 est écartée sans fiche, comme H10.** Aucune grille supplémentaire n'est essayée après lecture.

## 3. Ce que le criblage ne mesure pas

- **La base comptant / perpétuel.** Une pointe de financement va avec une prime du perpétuel, dont la fermeture profite au short. C'est probablement favorable, mais non compté.
- **Le risque de plateforme** et le déleveraging automatique.
- **Le coût d'opportunité** du capital immobilisé hors épisodes. Le taux court sert de référence.
- **Le risque de liquidation de la jambe courte**, borné par une marge pleine, mais qui demande un rééquilibrage.

## 4. Exécution

```
cd systeme-trading/recherche/criblage_strat07
python3 -B test_criblage_strat07.py
python3 -B criblage_strat07.py --cache ~/cache_binance_vision
```

Disque nécessaire : le financement (≈ 22 Mo) et les volumes journaliers, déjà en cache. Le criblage s'inscrit au registre des hypothèses, qu'il passe ou non.
