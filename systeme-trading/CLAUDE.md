# Système de trading de Jonathan — projet Claude Code

Ce dossier est l'environnement d'exécution principal du système (`cerveau-trading` § 0 bis).

- Toute demande de marché, de trade, de stratégie, de backtest, de moteur ou de revue commence par l'ouverture du skill `cerveau-trading`, qui choisit la chaîne et ouvre `commun-trading`.
- Mots déclencheurs : TRADE, VALIDER, MOTEUR, CONSEIL TRADING.
- Claude ne passe aucun ordre et ne manipule aucune clé. Les fichiers `.env` et le dossier `secrets/` ne se lisent pas.
- Aucun mode qui contourne les demandes de permission.
- Toute configuration du moteur garde `dry_run: true` tant qu'aucune stratégie n'est promue au statut réel.
- Dossiers : `strategies/STRAT-…/` (dossiers de validation), `journal/JOURNAL-TRADING.md`, `veille/`, `revues/`.
- Synchronisation GitHub automatique : après chaque étape clé de backtest ou mise à jour du journal, exécuter `git add . && git commit -m "update: [description]" && git push origin main`.
- Rédaction en français, phrases courtes, chiffres sourcés et datés, aucune certitude sur l'avenir.

Première tâche prévue : « VALIDER STRAT-20261031-01 », d'après `strategies/STRAT-20261031-01/`.
