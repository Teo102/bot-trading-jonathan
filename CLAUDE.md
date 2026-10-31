# Système de trading de Jonathan & Téo — Projet Claude Code

Ce dépôt est l'environnement d'exécution et de recherche principal du système (`cerveau-trading` § 0 bis).

- **Skills disponibles** : Les 14 skills sont situés dans `.claude/skills/` (et `systeme-trading/.claude/skills/`).
- **Orchestration** : Toute demande d'analyse de marché, de trade, d'audit de ressource, de stratégie, de backtest ou de revue commence par l'ouverture du skill `cerveau-trading`, qui sélectionne la chaîne d'outils appropriée.
- **Mots déclencheurs** : `TRADE`, `VALIDER`, `MOTEUR`, `CONSEIL TRADING`, `AUDIT`.
- **Règles de sécurité** :
  - Claude ne passe aucun ordre direct et ne manipule aucune clé privée.
  - Les fichiers `.env` et le dossier `secrets/` ne sont jamais lus ni versionnés.
  - Mode simulation / `dry_run: true` permanent tant qu'une stratégie n'a pas validé les 11 phases statistiques (E01 à E11).
- **Persistance** : Toute action importante est consignée dans `systeme-trading/journal/JOURNAL-TRADING.md` et les fiches associées.
- **Style de rédaction** : Français soigné, phrases courtes, chiffres sourcés et datés, esprit critique acéré (avocat du diable).

Première action opérationnelle : « VALIDER STRAT-20261031-01 » d'après `systeme-trading/strategies/STRAT-20261031-01/`.
