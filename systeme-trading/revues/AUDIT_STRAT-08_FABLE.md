# Audit adverse avant gel — STRAT-20261109-08 (contre-tendance après cascade de liquidations)

Rédigé le 09/11/2026 par Claude Fable 5.2, dans le rôle d'auditeur adverse de la mission du même jour. Heures en UTC. Résultat de recherche. Aucun ordre, aucune clé, `dry_run` permanent. **Aucune règle ni aucun paramètre n'a été modifié. Aucun rendement de stratégie n'a été lu. Le statut de la stratégie ne change pas.**

Objet : faire échouer la stratégie sur le papier avant le gel et avant tout rendement. Priorité donnée par la mission : la non-anticipation des klines 1 minute et des metrics.

Pièces auditées (commit `57dcd3c`) : `strategies/STRAT-20261109-08/FICHE_STRAT-20261109-08.md`, `donnees_1m.py`, `detection_cascades.py`, `controle_cascades.py`, `test_strat08.py`, et `donnees_binance.py` de STRAT-03 (lecteur de klines réutilisé). Le moteur `moteur_intraday.py` et le lanceur `run_essai08.py` n'existent pas encore : ils ne sont pas audités.

Scripts de preuve et sorties brutes : `revues/audit_fable/` et `revues/audit_fable/resultats/`. Chaque constat cite sa commande.

## 0. Synthèse

| Classe | Nombre | Constats |
|---|---:|---|
| Bloquant pour le gel | 3 | B1 horodatage des metrics non corrigé ; B2 l'archive d'intérêt ouvert commence le 01/12/2021 ; B3 départage des cascades simultanées non écrit |
| Majeur | 6 | M1 délai de publication de l'intérêt ouvert ; M2 valeurs nulles ; M3 lignes manquantes pendant les krachs de 2021 ; M4 contrôle du § 5 non conforme à la fiche ; M5 glissements optimistes ; M6 fréquence des événements |
| Mineur | 6 | m1 à m6 |
| Conforme | 5 | klines 1 minute, convention de prix, éligibilité sur la veille, blocs, mesure de Y en contrats |

**Verdict de la lecture adverse : affaiblie, gel non défendable en l'état.** Le défaut B1 est celui que STRAT-04 avait déjà trouvé le 31/10/2026. Il n'est pas corrigé dans le code de STRAT-08, et son effet est le pire possible pour une validation : il est absent du bloc de développement et présent dans tout le hors échantillon.

## 1. Constats bloquants

### B1. Le code lit l'intérêt ouvert 5 minutes dans l'avenir depuis mars 2024

**Fait.** `donnees_1m.py`, ligne 52, indexe l'intérêt ouvert sur `create_time` tel quel. `detection_cascades.py`, lignes 36 à 39, lit ensuite cette valeur à l'instant t. Aucune correction n'est appliquée. Les mots « bascule », « décalage » et « + 5 min » sont absents du dossier de STRAT-08.

**Preuve 1, sans aucun prix** (`python3 -B a1_archive_contre_rest.py`, 09/11/2026 20:35 UTC). L'archive est lue par le lecteur même de la stratégie, puis comparée à l'API publique `openInterestHist`, sur 16 symboles (BTC, ETH et 14 alts) et 3 jours (03, 05 et 07/11/2026, hors de tout bloc).

```
TOTAL lignes 13824 égalités par décalage k (archive(t) = REST(t + 5k min)) : {-2: 0, -1: 0, 0: 0, 1: 13824, 2: 0}
```

Les 13 824 lignes portent la valeur que l'API date 5 minutes plus tard. Aucune ne correspond à sa propre heure.

**Preuve 2, date de la bascule sur des alts** (`python3 -B a2_bascule_alts.py`, 20:40 UTC). Méthode de STRAT-04 étendue à 8 alts : corrélation entre la valeur absolue de la variation d'intérêt ouvert et la valeur absolue du rendement à 5 minutes, jour par jour. Mesure de synchronisation, sans sens ni position, sur le développement et la validation seulement.

| Mois | Part des jours où l'archive est datée 5 minutes trop tôt (8 alts) |
|---|---|
| 2023-06 | 0 à 7 % |
| 2024-02 | 0 à 14 % |
| 2024-03 | 55 à 84 % |
| 2024-04 | 73 à 97 % |
| 2025-03 | 74 à 87 % |

Jour par jour, les 8 alts sont à l'heure juste du 01 au 03/03/2024. Cinq sur huit basculent le 04/03 et les huit le 05/03. C'est la date trouvée par STRAT-04 sur BTC et ETH. La mesure journalière est bruitée (environ 80 % des jours après la bascule, pas 100 %). La preuve 1 est exacte, elle.

**Preuve 3, effet sur les événements détectés** (`python3 -B a5_effet_sur_detection.py`, 20:42 UTC). Le détecteur de la stratégie est lancé deux fois sur 8 alts et deux mois de validation (2024-08 et 2024-12), à la base X = 4 %, Y = 3 %. Aucune issue de position n'est lue.

```
TOTAL : {'brut': 12, 'corrige': 7, 'communs': 4, 'brut_seul': 8, 'corrige_seul': 3, ...}
Part des détections brutes absentes de la version corrigée : 66.7%
Part des détections corrigées absentes de la version brute : 42.9%
```

**Conséquences.**
1. La condition Y vue en t couvre en réalité l'intérêt ouvert de t − 10 à t + 5 minutes. L'entrée se fait à t + 1 minute. La stratégie connaîtrait donc 4 minutes d'avance la suite de la liquidation.
2. Le biais est nul en développement (jusqu'au 31/12/2023), présent sur 17 des 19 mois de validation, et présent sur tout le hors échantillon. Un résultat qui s'améliore d'un bloc à l'autre serait attendu par construction.
3. La porte E11 (retard de 5 minutes) perd son sens après mars 2024 : le retard annule juste l'avance.
4. Les 11 tests synthétiques ne peuvent pas voir ce défaut. Ils fabriquent des metrics à l'heure juste. `test_sans_anticipation` vérifie le code, pas la donnée.

**Ce qui lèverait le constat** (proposition, non appliquée) : décaler de + 5 minutes les heures de l'archive, soit à partir de la bascule (avec exclusion des jours du 02 au 05/03/2024), soit sur tout l'historique. La seconde option ne dépend pas de la date de bascule. Elle retarde l'information de 5 minutes avant mars 2024, ce qui est prudent. Puis ajouter un test sur données réelles : archive corrigée égale à l'API sur un jour récent.

### B2. L'archive d'intérêt ouvert ne commence que le 01/12/2021

**Fait** (`python3 -B a3b_trous_et_debuts.py`, 20:37 UTC, liste du dépôt public, 40 symboles).

```
Symboles dont la première archive est postérieure au 01/01/2021 : 39 sur 40
Répartition des débuts : {'2020-09': 1, '2021-12': 39}
```

Seul BTCUSDT commence le 01/09/2020. ICPUSDT commence le 23/12/2021. Les 38 autres commencent le 01/12/2021. La fiche (§ 2) écrit « 921 symboles, 2020-09-01 à 2026-11-08 » : c'est la plus ancienne date d'un seul symbole. STRAT-04 avait d'ailleurs fixé son début au 01/12/2021.

**Conséquences.**
1. Le bloc de développement annoncé (01/01/2021 au 31/12/2023) ne contient en fait que 25 mois utilisables sur 36. Les krachs de mai et de septembre 2021 sont hors d'atteinte.
2. La porte « au moins 3 années civiles sur 4 positives (2021 à 2024) » compterait une année 2021 réduite à décembre.
3. L'exigence de 300 cascades jouables en développement doit être tenue sur 25 mois.

**Ce qui lèverait le constat** : réécrire les blocs et la porte des années avant le gel, avec les dates réelles de l'archive. C'est une correction avant toute lecture de rendement (règle L1).

### B3. Le départage des cascades simultanées n'est écrit nulle part

**Fait.** La détection se fait sur une grille commune de 5 minutes. Dans un krach, plusieurs symboles déclenchent au même instant. La fiche (§ 3) dit seulement qu'« une cascade sans emplacement libre est ignorée et comptée ». Elle ne dit pas laquelle est prise quand il y a plus de candidates que d'emplacements. `controle_cascades.py`, ligne 104, trie par l'heure avec le tri par défaut de pandas, qui n'est pas stable. L'ordre effectif serait celui du fichier, donc l'ordre alphabétique des symboles.

**Précédent.** C'est le défaut de l'ordre de la whitelist de STRAT-01 (journal du 01/11/2026). Sur STRAT-07, la même mécanique touche 73 % des épisodes (audit du même jour, contrôle B1 de STRAT-07).

**Ce qui lèverait le constat** : une règle de départage écrite avant le gel, qui n'utilise aucune information postérieure à t. Exemples à trancher par Jonathan et Téo : la plus forte chute, le plus gros volume sur 15 minutes, ou un tirage à graines publiées avec moyenne sur les graines. Puis un test : le résultat ne change pas quand on permute l'ordre des symboles. La part des instants partagés est [non mesurée]. Le contrôle du § 5 la donnera (colonne « heures avec plus de 5 symboles »).

## 2. Constats majeurs

### M1. L'intérêt ouvert de l'instant t n'est pas publié à t + 1 minute

**Fait** (`python3 -B a4_delai_publication_oi.py --minutes 26`, 20:34 à 20:59 UTC, 8 symboles, 48 points, marché calme).

```
TOUS : délai d'apparition min 17.3 médiane 117.15 max 240.2 n 48
part > 60 s 0.75   part > 120 s 0.479   part > 180 s 0.1875
```

Un point de `openInterestHist` apparaît entre 17 et 240 secondes après son heure. Trois fois sur quatre, il n'est pas encore publié à t + 60 secondes, l'heure d'entrée de la base. STRAT-04 avait mesuré 45 à 174 secondes et retenu 5 minutes de délai dans ses paramètres gelés.

Le moteur en direct pourrait lire l'intérêt ouvert instantané (`/fapi/v1/openInterest`). Mais l'égalité entre cette valeur et le point publié n'est pas établie : 0 égalité exacte sur 48 points, comme chez STRAT-04. La valeur de l'archive à l'heure t n'est donc pas prouvée être ce qu'un robot voit à t. Le délai pendant une cascade, quand la plateforme est chargée, reste [non mesuré].

**Portée.** Même après la correction de B1, l'entrée à d = 1 minute suppose une donnée que le flux publié ne fournit pas à temps. La base réaliste est plus proche de E11 (5 minutes). Décision à prendre avant le gel, pas après les résultats.

### M2. Des valeurs nulles d'intérêt ouvert remplissent la condition Y à vide

**Fait** (`python3 -B a6_zeros_et_klines.py`, 20:43 UTC).

```
SUIUSDT 2024-08 {'lignes': 8928, 'nulles': 6, 'heures_nulles': ['2024-08-12 09:25:00', '2024-08-12 09:40:00', '2024-08-12 10:30:00', ...], 'instants_ou_Y_serait_rempli_par_un_zero': 5}
1000PEPEUSDT 2024-08 {'lignes': 8928, 'nulles': 6, ... mêmes heures ..., 'instants_ou_Y_serait_rempli_par_un_zero': 5}
```

Le 12/08/2024, de 09:25 à 11:00, l'archive porte 6 lignes à zéro, aux mêmes heures pour deux symboles (incident de la source). Le lecteur ne rejette pas les valeurs nulles. Une chute de prix de 4 % à ce moment-là créerait une cascade sans aucune liquidation. Ampleur sur tout l'historique : [non mesurée].

### M3. Des lignes manquent aux heures mêmes des krachs de 2021

**Fait** (`a3_qualite_metrics.py` et `a3b_trous_et_debuts.py`, 130 fichiers, 82 propres).

```
BTCUSDT 2021-05-19 lignes 570 manquants ['11:30', '11:35', '12:45']
BTCUSDT 2021-09-07 lignes 284 manquants ['14:30', '14:50', '15:00', '15:10']
BTCUSDT 2021-12-04 lignes 285 manquants ['05:00', '05:25', '05:30']   (identique pour ETHUSDT et SOLUSDT)
```

Une ligne absente rend le détecteur aveugle à cet instant et 15 minutes plus tard. Le journal du contrôle ne compte que les jours introuvables, pas les lignes. Les jours de krach échantillonnés depuis 2022 (12/05/2022, 09/11/2022, 05/08/2024, 10 et 11/10/2025) ont leurs 288 lignes. Les doublons de 2021 sur BTC (576 lignes) ont des valeurs identiques et sont sans effet. Deux fichiers du 05/08/2024 ne sont pas triés : le code trie.

### M4. Le contrôle du § 5 ne compte pas ce que la fiche appelle « jouable »

- La fiche impose une pause de H heures **après la sortie**. `dedoublonner` (`detection_cascades.py`, lignes 49 à 57, appelé ligne 116 du contrôle) applique 4 heures **après l'événement**. Dans une série de cascades, le contrôle peut compter jusqu'à deux fois plus d'événements que la règle.
- La règle « 2 stops dans la journée » ne peut pas être comptée sans lire d'issue. Elle retire pourtant des entrées les jours de krach.

Le chiffre « jouables » du contrôle est donc une borne haute. L'exigence de 300 et de 100 devrait se lire avec cette réserve écrite dans le rapport du contrôle.

### M5. Les glissements sont plus bas que ceux déjà retenus ailleurs pour des actifs plus liquides

| Source | Entrée | Stop |
|---|---|---|
| STRAT-08, fiche § 3 (alts ≥ 20 M USDT, dans la cascade) | 0,10 % | 0,30 % |
| STRAT-04, `parametres_geles.json` du 31/10/2026 (grandes alts) | 0,30 % | 0,60 % |
| STRAT-06, stress des 219 stops du 05/11/2026 (bougies 1 h, milieu de mèche) | — | 1,56 % en moyenne |

L'essai E12 (coûts doublés) ramène seulement STRAT-08 au niveau de base de STRAT-04. Les mesures ne sont pas comparables terme à terme (autre unité de temps, autre règle de remplissage). Le glissement réel à la minute dans une cascade est [non mesuré] ; les `aggTrades` autour d'un échantillon d'événements le donneraient.

### M6. Les événements semblent rares (critère T3)

Sur l'échantillon de la preuve 3 (8 alts liquides, deux mois dont le krach du 05/08/2024), le détecteur corrigé trouve 7 instants de base avant la pause de 4 heures. Ce n'est pas une estimation de fréquence. C'est un signal : le contrôle sans rendement doit passer **après** la correction de B1 et de B2, sinon son compte est faux dans les deux sens.

## 3. Constats mineurs

| N° | Constat | Preuve |
|---|---|---|
| m1 | E13 (short après une hausse forcée) ne peut pas tourner sur le format compact : `candidats` ne garde que les baisses | `detection_cascades.py`, ligne 41 |
| m2 | Le format compact garde les minutes qui suivent chaque événement, y compris dans le hors échantillon, sans verrou. Le verrou est prévu dans `run_essai08.py`, qui n'existe pas | `controle_cascades.py`, lignes 85 à 91 |
| m3 | Le placebo E14 (+ 24 heures) reste dans le régime de krach. Ce n'est pas un témoin neutre : la volatilité y est encore anormale | Fiche § 6 |
| m4 | L'ordre stop et entrée dans la même minute n'est pas écrit. Points à écrire et à tester avant le gel : la minute d'entrée compte pour le stop ; une sortie à l'ouverture précède le plus bas de la minute | Fiche § 3, moteur absent |
| m5 | La fréquence de la régression à deux facteurs n'est pas précisée pour une stratégie investie quelques heures par semaine | Fiche § 7 |
| m6 | Le seuil de 1,63 applique un facteur de 64 semaines à un bloc de 65,7 semaines. Écart de 0,03, dans le sens strict | Fiche § 6 |

## 4. Points conformes

- **Klines 1 minute** (`a6_zeros_et_klines.py`, 5 mois-symboles de 2021 à 2025) : heure d'ouverture en millisecondes, aucune bougie incomplète, aucune minute manquante, aucun doublon, lecteur identique au fichier brut. Échantillon limité.
- **Convention de prix** : le prix à t est la clôture de la bougie ouverte à t − 1 minute (`detection_cascades.py`, lignes 22 à 24). Aucune bougie en cours n'est lue.
- **Éligibilité** : médiane de volume décalée d'un jour (`donnees_1m.py`, lignes 83 et 84).
- **Blocs** du contrôle identiques à la fiche.
- **Y mesuré en contrats** : la précision du § 12 est juste, et le code l'applique déjà.
- Les 11 tests passent (`python -B test_strat08.py`, 09/11/2026).

## 5. Liste de contrôle de la mission

| Point | Résultat |
|---|---|
| Information future (indicateur, taille, place, horodatage) | **B1** (horodatage), **M1** (publication), B3 (place) |
| Paramètres cachés | **B3** (ordre des symboles) ; fenêtre de 15 minutes, K, 2 stops, 20 M, 30 jours : fixés et déclarés |
| Univers choisi avec le recul | Non : éligibilité lue sur la veille. Liste des contrats non crypto lue le 02/11/2026, effet [faible, non mesuré] |
| Coûts, glissement au stop, financement | **M5** |
| Concentration du gain | Non auditable avant rendement. Portes du § 7 prévues (symbole, mois, jour, hors 10 et 11/10/2025) |
| Nombre réel d'essais | 16 déclarés. STRAT-04 (même hypothèse, H04) n'a lu aucun rendement : 6 comptages seulement. N tenu |
| Conformité du code à la fiche | **M4**, m1, m2 |

## 6. Lecture adverse (format `avocat-du-diable`)

**Trois arguments contraires, par poids.**
1. Le signal repose sur une donnée dont l'heure est fausse de 5 minutes sur la moitié de l'historique, et qui n'est publiée que 2 minutes après son heure en médiane (B1, M1). Une fois les deux corrigés, l'entrée se fait au mieux 3 à 5 minutes après la chute. C'est exactement le cas que le tri T5 redoutait.
2. L'historique utilisable est plus court et plus pauvre qu'annoncé (B2, M3, M6). Vingt-cinq mois de développement, dont 2022 et 2023, peu de cascades par symbole.
3. Les coûts dans une cascade sont posés plus bas que ce que le système a déjà mesuré ou retenu ailleurs (M5).

**Scénario d'échec le plus plausible.** Le contrôle sans rendement, refait après correction, compte moins de 300 cascades jouables en 25 mois. La stratégie retombe dans le cas de STRAT-04, non testable. Ordre de grandeur : [une chance sur deux, jugement, non calculé].

**Biais probables.** Récit connu (« acheter les mèches ») ; confiance dans des tests synthétiques verts ; reprise d'un chiffre d'audit (« depuis 09/2020 ») sans contrôle par symbole.

**Données invalidantes.** Moins de 300 cascades jouables en développement après correction. Net de E11 inférieur à la moitié de la base. Glissement mesuré à l'entrée supérieur à 0,3 %.

**Verdict : affaiblie.** L'hypothèse économique reste la meilleure de la grille (contrepartie forcée). Le dossier, lui, n'est pas prêt pour le gel.

## 7. Ce qui attend une décision de Jonathan et Téo

1. Correction de l'horodatage : à partir de la bascule, ou sur tout l'historique (B1).
2. Nouveaux blocs et nouvelle porte des années, vu le début réel de l'archive (B2).
3. Règle de départage des cascades simultanées (B3).
4. Retard d'entrée de base : 1 minute ou 5 minutes, vu le délai de publication (M1).
5. Traitement des valeurs nulles et des lignes manquantes (M2, M3).

Aucune de ces décisions n'a été prise ni appliquée par l'audit.

## Sources

| Pièce | Heure UTC (09/11/2026) |
|---|---|
| `revues/audit_fable/resultats/a1_archive_contre_rest_20261109T203538Z.json` | 20:35 |
| `revues/audit_fable/resultats/a2_bascule_alts_20261109T204039Z.json` | 20:40 |
| `revues/audit_fable/resultats/a3_qualite_metrics_20261109T203634Z.json` | 20:36 |
| `revues/audit_fable/resultats/a3b_trous_et_debuts_20261109T203716Z.json` | 20:37 |
| `revues/audit_fable/resultats/a4_delai_publication_oi_20261109T205958Z.json` | 20:34 à 20:59 |
| `revues/audit_fable/resultats/a5_effet_sur_detection_20261109T204223Z.json` | 20:42 |
| `revues/audit_fable/resultats/a6_zeros_et_klines_20261109T204313Z.json` | 20:43 |
| `strategies/STRAT-20261031-04/FICHE_STRAT-20261031-04.md` § 2.3 | 31/10/2026 |

Données lues : archives publiques `data.binance.vision` (metrics, klines 1 minute et 5 minutes) et API publique `fapi.binance.com` (intérêt ouvert), sans clé. Les contrôles A2 et A5 lisent des prix passés des blocs de développement et de validation pour dater ou détecter l'événement, jamais l'issue d'une position. Rien n'a été lu dans le hors échantillon, sauf le nombre de lignes de deux fichiers d'intérêt ouvert des 10 et 11/10/2025.
