# Contrôle sans rendement de STRAT-20261119-09 (fiche § 5), 19/11/2026

Lancé sur accord de Jonathan et Téo le 19/11/2026, qui ont aussi validé les valeurs de base (k = 1, H = 2 h, m = 2, K = 6). **Aucun rendement, aucune issue de position lue.** Le script lit, pour chaque week-end, le prix du perpétuel à la clôture du vendredi et à l'heure de décision, et les clôtures des jours ouvrés précédents pour σ. C'est le mouvement qui définit le signal. Les données s'arrêtent à la dernière décision (lundi 16/11/2026 13:00 UTC) et chaque calcul coupe les données à sa propre décision (test avec prix empoisonnés après la décision : vert).

Script `controle_week_end09.py` (9 tests synthétiques verts, `test_controle09.py`). Exécution du 19/11/2026 à 14:56:37 UTC depuis le poste local, 182 s, 296 appels publics à fapi.binance.com, aucune erreur. Sorties : `controle_20261119T145637Z.json`, `controle_week_ends_20261119T145637Z.csv`, `controle_evenements_20261119T145637Z.csv` (445 événements éligibles : |M|/σ et sens), `univers_20261119T145637Z.txt`. Un premier passage à 14:51 UTC, aux comptes identiques, ne gardait que les signaux ; il a été remplacé et effacé.

## Précisions de règles écrites avant le contrôle

- **Heures pleines.** Les bougies de Binance commencent à l'heure pile. Pour les actions, la décision est donc prise à 08:00 New York (1 h 30 avant l'ouverture) et la sortie à 12:00 (2 h 30 après). Pour les matières premières, rien ne change (décision dimanche 17:00, sortie 20:00).
- **σ** = écart-type des 20 derniers rendements entre deux jours ouvrés consécutifs, à l'heure de clôture du groupe. Le rendement du lundi est exclu, car il couvre le week-end et la réouverture.
- **Plafond K = 6 au total.** Les matières premières décident le dimanche, les actions prennent les places restantes le lundi.
- Week-ends exclus pour jour férié : 22/05 (Memorial Day), 19/06 (Juneteenth), 03/07 (fête nationale observée), 04/09 (Labor Day), d'après le calendrier de la bourse de New York [calendrier du CME à vérifier au gel].

## 1. Univers

17 actions et fonds dépassent 0,5 M USDT de volume horaire médian pendant la fermeture (8 week-ends du 25/09 au 13/11) : CRCL, DRAM, EWY, GOOGL, INTC, KORU, MSTR, MU, NVDA, QQQ, SKHY, SNDK, SNXX, SOXL, SOXS, SPCX, SPY. Juste sous le seuil : Tesla (0,49 M), TQQQ (0,45 M), AMD, NBIS, Coinbase.

**Trois défauts de composition :**
- **SOXS est l'inverse de SOXL** (fonds à levier 3 sur les semi-conducteurs, l'un à la hausse, l'autre à la baisse). Vendre l'un après une hausse et acheter l'autre est le même pari, compté deux fois.
- **EWY, KORU et SKHY suivent le marché coréen** [lien de SKHY à vérifier], qui rouvre le lundi à 00:00 UTC, 13 heures avant la décision. Pour eux, la fermeture est finie au moment de décider, et le mécanisme de la fiche ne s'applique pas.
- **Une grappe semi-conducteurs et mémoire** : MU, SNDK, DRAM, SOXL, SOXS, SKHY, INTC, NVDA. La moitié de l'univers réagit à la même nouvelle. SNXX et SPCX sont à identifier [nature non vérifiée].

## 2. Signaux, avec k = 1

| Mesure | Valeur |
|---|---:|
| Week-ends comptés (sur 28, 4 fériés exclus) | 24 |
| Signaux par week-end | **2,25** (matières premières 0,29 ; actions 1,96) |
| Positions par week-end après le plafond | 1,79 |
| Positions projetées sur 52 week-ends | **93** (critère du verdict : 100) |
| Week-ends sans aucun signal | 10 sur 24 |
| Week-ends au-delà de 6 signaux | 2 (11/09 : 13 signaux ; 16/10 : 10) |
| Part médiane des signaux de même sens le même week-end | **1,00** |
| Témoin BTC et ETH, signaux par week-end | 0,21 (heures du CME) ; 0,54 (heures des actions) |

**Lecture :**
- L'exigence de la fiche (au moins 2 signaux par week-end) passe de justesse, mais le critère de 100 positions ne serait probablement pas atteint en 52 semaines.
- **Les signaux d'un même week-end vont presque toujours dans le même sens.** Un week-end est donc un seul pari, et le nombre utile d'observations est le nombre de week-ends avec une position : 14 sur 24, soit environ 30 sur 52.
- **Les matières premières ne donnent presque rien** : 7 signaux en 24 week-ends, aucun depuis le week-end du 31/07. Le mouvement du week-end de l'or et du pétrole atteint rarement une journée d'écart-type.

## 3. Sensibilité au seuil et à l'univers (comptes seulement)

Univers nettoyé = sans SOXS, EWY, KORU et SKHY (13 actions). Aucune issue lue, seulement le nombre d'événements au-dessus de chaque seuil.

| Univers | k | Signaux par week-end | Positions sur 52 week-ends | Week-ends actifs sur 52 |
|---|---:|---:|---:|---:|
| Complet | 1 | 2,25 | 93 | 30 |
| Complet | 0,75 | 4,62 | 173 | 41 |
| Complet | 0,5 | 7,50 | 245 | 52 |
| Nettoyé | 1 | 1,71 | 82 | 28 |
| **Nettoyé** | **0,75** | **3,58** | **152** | **39** |
| Nettoyé | 0,5 | 6,08 | 230 | 52 |

Avec l'univers nettoyé et k = 1, l'exigence de 2 signaux par week-end échoue (1,71).

## 4. Carnet d'ordres, relevé de référence en semaine

Jeudi 19/11/2026 vers 14:56 UTC, depuis le poste local (`releve_carnet09.csv`). Écart affiché de 0,0003 % (or) à 0,033 % (SNXX). Profondeur à ±0,1 % sur le côté le plus mince : de 15 000 USDT (SOXS) et 34 000 USDT (SNXX) à 3,0 M USDT (or), et environ 0,9 à 1,1 M USDT pour SPY et QQQ. **Les relevés du samedi 21/11 et des heures de décision (dimanche 22:00 UTC, lundi 13:00 UTC) restent à faire** : leur programmation sur le serveur attend l'accord de Jonathan et Téo.

## 5. Conclusion

Le contrôle passe à la lettre (2,25 signaux par week-end), mais il change la lecture du papier.
1. **La puissance est plus faible que prévu.** Comme les paris d'un week-end vont dans le même sens, le test porte sur environ 30 week-ends actifs en un an avec k = 1, pas sur 93 positions indépendantes.
2. **L'univers doit être nettoyé avant le gel** (inverse de SOXL, contrats coréens), sinon une partie des signaux ne teste pas l'hypothèse.
3. **La stratégie serait presque entièrement une stratégie d'actions américaines de la grappe semi-conducteurs**, pas une stratégie sur l'or et le pétrole comme la fiche l'envisageait.

Décisions proposées à Jonathan et Téo, toutes fondées sur des comptes et non sur des issues : univers nettoyé, k = 0,75 (stop à m × k × σ = 1,5 σ), et un critère exprimé en week-ends (au moins 35 week-ends avec une position) à la place des 100 positions. L'alternative honnête est de mettre H33 de côté, si un papier de faible puissance ne vaut pas l'infrastructure.
