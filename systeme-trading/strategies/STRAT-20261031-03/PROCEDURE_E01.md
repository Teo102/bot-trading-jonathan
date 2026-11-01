# Procédure de lancement de E01 (STRAT-20261031-03)

Écrite le 01/11/2026. E01 n'a **pas** été lancé. Deux raisons :

1. Les règles D6 sont au statut `proposees` dans `config_strat03.json`. `run_essai.py` refuse tout essai avant `figees`.
2. La session cloud de Claude du 01/11/2026 n'a pas accès à `data.binance.vision` (connexion refusée par le proxy, 01/11/2026 ≈ 10:30 UTC). Le lancement se fait donc sur la machine de Téo, ou dans une session où ce domaine est autorisé.

## Étapes, dans l'ordre

1. Jonathan et Téo relisent le § 0 de la fiche (tableau « Opérationnalisation de D6 ») et la liste des memecoins de `config_strat03.json`. Toute correction se fait **maintenant**, avant le moindre rendement.
2. Passer `statut_regles` à `"figees"`, puis commit et push **avant** l'étape 4. Ce commit date le gel des règles.
3. Tests, tous verts exigés :
   ```
   python -B test_moteur_synthetique.py
   python -B test_donnees_et_essai.py
   ```
4. Lancement unique :
   ```
   python -B run_essai.py --essai E01 --cache ~/cache_binance_vision
   ```
   Le script lit environ 300 symboles en 1 d de juin 2020 à juin 2024, puis le 1 h, la marque et le financement des seuls noms entrés dans l'univers. Il s'arrête au 01/07/2024 02:00 UTC (verrou de bloc). Durée [non mesurée].
5. Commit des sorties : `resultats/E01_metriques.json`, `.md`, `E01_semaines.csv`, `E01_lignes.csv`, et la ligne E01 de `REGISTRE_ESSAIS.csv`.

## Ce que E01 tranche

La porte « rendement net de la base > 0 sur le développement » (fiche § 1.8), et rien d'autre. Le Sharpe, le bêta et l'alpha résiduel de E01 sont publiés, mais le verdict C1, C2 et C7 ne porte que sur E25. Si E01 est négatif, la stratégie est rejetée et E02 ne se lance pas.

## Interdits

- Relancer E01 après lecture du résultat, même pour un bogue. Un bogue se documente, se corrige, puis l'essai corrigé prend un nouvel identifiant compté dans N.
- Modifier `config_strat03.json` après le gel.
- Lancer E25 ou E26 avec ce script (refus codé).
