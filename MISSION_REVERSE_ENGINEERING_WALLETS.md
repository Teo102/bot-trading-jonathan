# MISSION : Reverse-Engineering Médico-Légal des Wallets DEX & Stratégies Solana

**Date :** 01 Novembre 2026  
**Auteurs :** Téo Brondel & Jonathan  
**Agent Exécutant :** Claude Code  
**Objectif :** Décortiquer de manière 100 % autonome les stratégies des meilleurs traders réels sur Solana (Pump.fun / Raydium), en éliminant tous les biais de manipulation (insiders, snipers de bloc 0, wash trading, bots MEV), et transformer ces découvertes en un modèle de trading systématique autonome.

---

## 1. INFRASTRUCTURE À TA DISPOSITION

Claude Code a accès direct à l'infrastructure suivante pour exécuter tous les calculs et téléchargements :

* **Machine de production cloud 24/7 (Scaleway Amsterdam)** :
  * **IP :** `51.158.163.228` (Zone `AMS 1`, connexion datacenter gigabit, très faible latence).
  * **Accès SSH direct sans mot de passe :**
    ```bash
    ssh trading-bot
    # ou : ssh root@51.158.163.228
    ```
  * **Dépôt cloné sur le serveur :** `/root/bot-trading-jonathan`
  * **Environnement Python sur le serveur :** `/root/bot-trading-jonathan/systeme-trading/.venv/bin/python`
  * **Usage :** Tu peux y lancer des scripts lourds, des scrapers continus, des requêtes RPC ou des listeners WebSocket dans un `tmux` sans saturer la machine locale.

* **Environnement Local Mac :**
  * Répertoire : `/Users/teobrondel/Bot Trading Jonathan`
  * Venv Python : `systeme-trading/.venv/bin/python`

* **Comptes & Données :**
  * Dépôt GitHub synchronisé : `https://github.com/Teo102/bot-trading-jonathan` (branche `main`).
  * Requête Dune de référence : `systeme-trading/strategies/STRAT-20261031-03/faisabilite_tokens_solana.sql`.

---

## 2. FEUILLE DE ROUTE OPÉRATIONNELLE POUR CLAUDE CODE

Tu dois exécuter de manière autonome les 4 phases suivantes :

### Phase 1 : Extraction d'une cohorte de wallets rentables
1. Extraire les transactions et les portefeuilles les plus performants sur Solana / Pump.fun / Raydium sur les 30 à 90 derniers jours.
2. Utiliser des scripts Python (`solana-py`, `requests`, APIs Solscan / DexScreener / Dune) ou les lancer directement sur le serveur cloud.

### Phase 2 : Filtres d'exclusion médico-légaux stricts (Anti-Tricheurs)
Éliminer systématiquement les portefeuilles dont la rentabilité repose sur un avantage non réplicable :
1. **Filtre Anti-Bloc 0 / Snipers :** Éliminer tout wallet ayant acheté dans les 2 premières secondes ou le même slot/bloc que la création de liquidité du pool.
2. **Filtre Anti-Dev / Wash-Trading :** Éliminer tout wallet ayant reçu des fonds (SOL) directement du deployer du token ou partageant un cluster de financement commun.
3. **Filtre Anti-MEV / Sandwiching :** Éliminer les bots à haute fréquence (centaines de micro-transactions par minute avec priorité maximale).

### Phase 3 : Décomposition factorielle des vrais traders (Survivants)
Sur les portefeuilles restants (vrais traders discrétionnaires ou algo réplicables) :
1. **Déclencheur d'entrée (Entry Trigger) :**
   - À quel niveau de valorisation / market cap entrent-ils (500k$, 1M$, 5M$) ?
   - Entrent-ils à la migration Pump.fun $\rightarrow$ Raydium ?
   - Sur cassure de plus haut (breakout) ou sur repli / consolidation (pullback) ?
   - Quel est le seuil de volume horaire minimum au moment de l'entrée ?
2. **Gestion du risque & Sortie (Exit & Risk) :**
   - Durée médiane de détention (en minutes / heures / jours).
   - Niveau de stop-loss moyen constaté (coupent-ils à -15 %, -30 %, ou sur perte de volume) ?
   - Stratégie de prise de profits (vente intégrale ou échelonnée : 50 % à 2x, etc.) ?
3. **Métrique de consistance :**
   - Win rate réel, profit factor, ratio gain moyen / perte moyenne.

### Phase 4 : Modélisation Algorithmique & Code
1. Coder la stratégie systématique correspondante sous forme de script autonome (dans `systeme-trading/strategies/STRAT-DEX/`).
2. Déployer et tester le bot en mode simulation (`dry_run: true`) sur le serveur Scaleway 24/7.
3. Consigner toutes les découvertes et étapes franchies dans `systeme-trading/journal/JOURNAL-TRADING.md`.
4. Effectuer les commits et pushs réguliers sur GitHub (`git push origin main`).

---

**Consigne :** Prends l'initiative complète. Conçois les scripts, lance les calculs, filtre les données, analyse les métriques et construis la stratégie étape par étape.
