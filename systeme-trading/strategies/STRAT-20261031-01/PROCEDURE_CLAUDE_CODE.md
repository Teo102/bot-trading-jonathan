# Procédure STRAT-20261031-01 dans Claude Code

Texte à coller dans une session Claude Code ouverte dans un dossier contenant les cinq fichiers du dossier (`TrendDonchianV1.py`, `config_strat01.json`, `analyse_strat.py`, `REGISTRE_ESSAIS.csv`, `FICHE_STRAT-20261031-01.md`).

---

Mission : exécution de la procédure de validation de STRAT-20261031-01 décrite dans FICHE_STRAT-20261031-01.md.

Règles strictes :
- Les paramètres de TrendDonchianV1 (20, 10, 14, 2.0, 200) ne changent jamais. Les variantes de robustesse sont des sous-classes séparées.
- Aucune clé d'API, aucun mode réel, aucun hyperopt. dry_run reste à true.
- Chaque exécution remplit une ligne de REGISTRE_ESSAIS.csv (date, trades, espérance, intervalle, drawdowns) d'après la sortie de analyse_strat.py.
- Le bloc hors échantillon (E10, E11) ne s'exécute qu'après E01 à E09, une seule fois, sans relance.

Étapes attendues :
1. Installation de freqtrade (pip install freqtrade, ou image Docker freqtradeorg/freqtrade:stable), puis `freqtrade create-userdir --userdir user_data` ; copie de TrendDonchianV1.py dans user_data/strategies/.
2. Données : `freqtrade download-data -c config_strat01.json --trading-mode futures --timeframes 1d --timerange 20200501-`. Contrôle avec `freqtrade list-data -c config_strat01.json --trading-mode futures` : présence des 10 paires, date de début de chacune, présence des taux de financement.
3. E01, développement : `freqtrade backtesting -c config_strat01.json -s TrendDonchianV1 --timerange 20210101-20240630 --fee 0.0005 --export trades --export-filename user_data/backtest_results/E01.json`, puis `python analyse_strat.py <export E01>`.
4. Contrôle des biais sur le développement : `freqtrade lookahead-analysis` et `freqtrade recursive-analysis` avec la même configuration et la même période. Un biais signalé arrête la procédure.
5. E02, validation : même commande sur 20240701-20250731.
6. E03 à E08 : six sous-classes (entry_period 16 et 24 ; exit_period 8 et 12 ; atr_mult 1.6 et 2.4), chacune sur 20210101-20250731.
7. E09 : la base sur 20210101-20250731 avec --fee 0.0010.
8. E10 puis E11 : la base sur 20250801-20261031, avec --fee 0.0005 puis 0.0010. Une seule fois.
9. Rapport final : registre complet ; sortie brute de analyse_strat.py pour E01, E02, E09, E10, E11 ; tableau freqtrade de E10 (par paire, longs et shorts séparés, financement payé) ; anomalies rencontrées. Aucune conclusion sur la rentabilité : le verdict revient à validation-edge.

---

Le rapport final se recolle ensuite dans le chat claude.ai, avec le mot VALIDER, pour le verdict.
