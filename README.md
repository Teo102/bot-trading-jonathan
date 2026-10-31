# Système de Trading Quantitatif & Polymarket — Jonathan & Téo

Ce dépôt Git est la **mémoire centrale et le cerveau opérationnel** du système de trading partagé entre **Jonathan** (Dubaï) et **Téo** (France).

Il contient l'intégralité des recherches, des audits critiques de ressources externes, des transcriptions complètes, des stratégies quantitatives prêtes pour backtest, du journal de bord, ainsi que les **14 skills personnalisés** orchestrés par `cerveau-trading`.

---

## 🏛️ Architecture & Organisation du Dépôt

```
.
├── CLAUDE.md                                    # Instructions maîtresses pour Claude Code
├── README.md                                    # Documentation générale du projet
├── NOTE_STRATEGIE_ET_REGIME.md                  # Synthèse macro, régimes de marché et doctrine
├── TRANSCRIPTIONS_COMPLETES_8_RESSOURCES.md     # Transcriptions intégrales (vidéos YouTube & tweets)
├── 2026-10-31_AUDIT_5_TWEETS_IA_TRADING.md      # Audit mathématique et déconstruction des arnaques/promesses
├── 2026-10-31_AUDIT_7_REPOS_ET_MAXIMISATION.md  # Analyse des 7 dépôts quantitatifs & connecteurs
├── 2026-10-31_DECRYPTAGE_8_RESSOURCES_...md     # Analyse détaillée des vidéos drainers et bonnes pratiques
├── 2026-10-31_RADIOGRAPHIE_ET_AUDIT.md          # Audit initial de faisabilité et rentabilité
├── 2026-10-31_SQD_RENTABILITE_INTEGRATION.md    # Modélisation des flux de rentabilité et exécution
├── transcripts/                                 # Fichiers bruts de transcription (YouTube / text)
└── systeme-trading/                             # Environnement d'exécution opérationnel
    ├── CLAUDE.md                                # Directives spécifiques Claude Code
    ├── INSTALLATION.md                          # Guide de démarrage local
    ├── .claude/
    │   ├── settings.json                        # Règles de sécurité strictes (interdiction .env/secrets)
    │   └── skills/                              # Les 14 skills du système (Cerveau, Journal, etc.)
    ├── journal/
    │   └── JOURNAL-TRADING.md                   # Journal de bord persistant (mémoire de trading)
    ├── strategies/
    │   └── STRAT-20261031-01/                   # Trend Following Donchian (Binance Futures)
    │       ├── TrendDonchianV1.py               # Stratégie Freqtrade (sans lookahead bias)
    │       ├── config_strat01.json              # Configuration 10 paires crypto 1d
    │       ├── analyse_strat.py                 # Script d'analyse des backtests
    │       ├── REGISTRE_ESSAIS.csv              # Registre strict des tests (anti-overfitting)
    │       ├── FICHE_STRAT-20261031-01.md       # Fiche descriptive d'ingénierie
    │       └── PROCEDURE_CLAUDE_CODE.md         # Guide pas à pas de validation
    ├── revues/                                  # Revues périodiques de performance
    └── veille/                                  # Notes de veille macro et crypto
```

---

## 🧠 Les 14 Skills du Cerveau (`systeme-trading/.claude/skills/`)

1. **`cerveau-trading` (v2.1)** : Orchestrateur central. Oriente chaque demande vers la chaîne de skills adéquate.
2. **`commun-trading` (v1.2)** : Définitions communes, glossaire et conventions mathématiques.
3. **`journal-trading` (v1.2)** : Mise à jour automatique de `JOURNAL-TRADING.md` (mémoire persistante).
4. **`risque-position` (v1.2)** : Calcul strict des tailles de lots, levier max 1.5x, drawdown stop.
5. **`validation-edge` (v1.1)** : Protocole en 11 étapes (E01-E11) pour prouver l'edge statistique sans overfitting.
6. **`supervision-moteur` (v1.1)** : Contrôle du moteur Freqtrade (dry-run obligatoire avant validation).
7. **`analyse-polymarket`** : Analyse des spreads maker (0% fees, rebates) et résolution UMA.
8. **`avocat-du-diable`** : Contradicteur systématique pour débusquer les biais, les faux signaux et les pièges.
9. **`analyse-actif`** : Analyse technique, fondamentale et flux sur une crypto spécifique.
10. **`synthese-marche`** : Vue d'ensemble des régimes de marché (tendance, range, haute volatilité).
11. **`veille-macro-crypto`** : Suivi des taux d'intérêt, flux ETF, liquidité globale et corrélations.
12. **`fiche-trade`** : Génération de fiches d'ordre détaillées avant toute entrée.
13. **`revue-performance` (v1.1)** : Bilan hebdomadaire/mensuel (Sharpe, Sortino, Calmar, Max Drawdown).
14. **`conseil-trading`** : Recommandations stratégiques et d'allocation de capital.

---

## 🚀 Utilisation avec Claude Code

### Pour Téo et Jonathan :
1. **Cloner le projet sur votre machine locale :**
   ```bash
   git clone <URL_DU_REPO>
   cd "Bot Trading Jonathan/systeme-trading"
   ```

2. **Lancer Claude Code :**
   ```bash
   claude
   ```

3. **Exécuter une tâche :**
   Claude Code lit automatiquement le contexte, applique les skills et modifie les fichiers en temps réel.
   
4. **Partager les avancées :**
   Quand une session se termine :
   ```bash
   git add .
   git commit -m "feat: compte-rendu de session"
   git push
   ```
   L'autre partenaire fait simplement `git pull` pour récupérer l'état exact du Cerveau.

---

## 🛡️ Règles de Sécurité Inviolables

* **Aucune clé API ni mot de passe dans Git.** Les configurations sensibles restent locales.
* **Mode Dry-Run permanent** tant qu'une stratégie n'a pas validé les 11 phases du protocole statistique.
* **Zéro complaisance :** Tout rendement spectaculaire est présumé coupable d'overfitting ou d'escroquerie jusqu'à preuve chiffrée du contraire.
