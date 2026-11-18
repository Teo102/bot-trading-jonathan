# Fiche STRAT-06-bis — Dérive des jeunes perpétuels, cohortes quotidiennes, verdict par le papier

Rédigée le 09/11/2026 par le Cerveau, sur décision de Jonathan et Téo du même jour (réouverture après rejet de la v1). Résultat de recherche, aucun ordre, `dry_run` permanent, capital nul.

**Statut des critères : FIGÉS le 16/11/2026 (2026-11-16T08:52:17Z, § 7). Premier jour compté : 17/11/2026 à 00:00 UTC.** Aucune semaine de papier antérieure ne compte dans le verdict.

## 0. Origine et contamination

- **La v1 est rejetée** au hors échantillon (E19, 06/11/2026), sur deux portes du § 7 de la fiche v1 :
  - Sharpe 1,398 pour un seuil de 1,72 ;
  - borne basse de l'IC à 90 % de la moyenne hebdomadaire à −0,04 %.

  E20 (coûts doublés) : +58,88 %, porte franchie, sans effet sur le verdict.
- **La réouverture est une nouvelle hypothèse (H12-bis).** Toutes les données jusqu'au 26/10/2026 sont consommées et connues : aucun backtest ne peut plus servir de preuve. **Le seul test est le papier aveugle, en avant.**
- Ce qui est connu et déclaré : régimes 2021 à 2026, dépendance au stop (C15, C17), facteur commun (2,5 noms effectifs), encombrement croissant du financement (37,7 % des shorts payant plus de 10 %/an en E19), décote d'exécution d'environ 20 % du Sharpe (stress des stops).

## 1. Règles (identiques à la v1, sauf le calendrier)

- **Univers et sélection** : comme la v1 (`config_strat06.json` figée, exclusions des contrats non crypto et des faux nouveaux noms). Âge de 7 à 60 jours, médiane ≥ 20 M USDT, au plus 6 noms, short de chaque nom.
- **Couverture et stop** : long BTC à 1× la somme des shorts ; stop à 30 % sur le prix de marque.
- **Calendrier** :
  - 7 cohortes, une par jour de la semaine ;
  - chaque cohorte reçoit son signal à 00:00 UTC, s'exécute à 01:00 UTC, est tenue 7 jours, puis est renouvelée ;
  - chaque cohorte pèse **1/7** de la base, soit 1/84 de notionnel par ligne à brut 100 %.
- **Modèle de remplissage du papier** :
  - entrée à l'ouverture publique de 01:00 ;
  - stop déclenché sur le plus haut horaire du prix de marque, rempli au pire du niveau et de l'ouverture de l'heure, plus 0,30 % ;
  - frais de 0,05 % et glissement de 0,05 % par côté, financement réel.
  - **Une série stressée est calculée en parallèle** (stop rempli à mi-chemin du niveau et du plus haut de marque de l'heure, mode 1 de CS3). **Le verdict porte sur la série stressée.**

## 2. Critères du verdict (proposés)

| Point | Règle |
|---|---|
| Durée | **52 semaines** comptées à partir du premier jour suivant le gel et le déploiement du module à cohortes. Point d'étape à 26 semaines |
| Arrêt anticipé, à tout moment | Drawdown de la série stressée, en équivalent brut 100 %, supérieur à **40 %** (en échantillon : −30,9 % ; au pire stress : −33,7 %) → rejet |
| Point d'étape (26 semaines) | Net cumulé de la série stressée ≤ 0 → rejet. Sinon, poursuite sans changement de règle |
| Verdict favorable (52 semaines), toutes requises | Sharpe annualisé de la série stressée **> 0,8** ; alpha à deux facteurs (BTC, alts anciennes moins BTC, méthode du diagnostic B) **> 0** ; aucun nom > 25 % et aucun mois > 40 % du gain net ; au moins 300 lignes de shorts |
| Incidents | Plus de 2 jours consécutifs sans signal (panne, données) : incident consigné ; les jours manquants ne sont ni rejoués ni remplacés. Plus de 10 jours manquants au total : le verdict est reporté d'autant |

**Puissance, publiée d'avance (L8).** Sur 52 semaines, l'écart-type d'un Sharpe annualisé vaut environ 1,0.
- Si le vrai Sharpe est de 1,3 : probabilité de verdict favorable ≈ 69 %.
- Si le vrai Sharpe est de 0 : probabilité de faux verdict favorable ≈ 21 %.

Le papier ne prouve pas l'edge. Il le **réfute** s'il est absent et nettement négatif, et il le **confirme faiblement** s'il est présent. C'est la limite d'un test d'un an, écrite avant de le commencer.

## 3. Ce que le papier ne mesure pas

Les remplissages réels, la profondeur des carnets pendant une forte hausse, l'écart entre le prix de marque et le dernier prix. Seul un pilote réel le peut. La condition de pilote décidée le 05/11 (hors échantillon > 1,72) ne peut plus être remplie : **tout pilote demande une nouvelle décision écrite** (exception L5), au plus tôt après le point d'étape de 26 semaines.

## 4. Préalables au premier jour compté

1. Module papier à 7 cohortes quotidiennes, série de base et série stressée, journal quotidien en ajout seul.
2. Rejeu : chaque semaine, le moteur de backtest relancé sur les mêmes données publiques retrouve la même sélection. Un écart est un incident.
3. Gel des § 1 et § 2 par une ligne de journal de Jonathan et Téo.
4. `dry_run: true`, capital nul, aucune clé de trading sur le serveur.

## 5. Module à 7 cohortes : écrit et essayé à blanc (13/11/2026)

Préalable 1 du § 4 rempli, préalable 2 outillé. Rien n'est gelé, aucun jour n'est compté, aucune tâche planifiée n'est installée sur le serveur.

**Code** (commits `04b94c7` et `c2295f4`) :
- `collecte_papier06.py` : volumes journaliers depuis la première bougie de chaque symbole, bougies horaires du contrat et du prix de marque, financement. Fichiers en ajout seul ; une clé déjà lue n'est jamais réécrite ; chaque ajout est inscrit avec son empreinte SHA-256. Contrats non crypto écartés par `underlyingType` (L10).
- `paper_cohortes06.py` : les 7 cohortes, en base et en stressé (mode 1), avec le moteur de la v1 (`jouer_ligne`, `cout_de_rotation`, `fabrique_cible`, configuration figée de la v1, empreinte vérifiée). Sorties en ajout seul : signaux avec leur heure d'écriture, semaines de cohortes closes, lignes, série quotidienne à 01:00 UTC, incidents, journal Markdown. Un signal écrit après son heure d'exécution rend la date manquée.
- `rejeu_cohortes06.py` : sélection et prix d'entrée refaits sur les archives publiques (journalières pour le mois en cours), écarts consignés comme incidents.
- `verdict_bis06.py` : critères du § 2, refus de tout verdict avant les dates.
- `config_bis06.json` : statut `a_blanc`, paramètres du verdict et du rejeu.

**Tests** : 15 tests synthétiques, dont l'égalité exacte entre une cohorte et `moteur_xsmom.backtest` sur des semaines closes (seule différence : le solde final que le backtest impute à sa dernière semaine). Les suites de la v1 restent vertes.

**Essai à blanc sur le serveur** (13/11/2026, hors des fichiers officiels, cohortes démarrées le 06/11/2026) :
- collecte initiale : 654 perpétuels, 633 880 jours, 787 appels publics, 328 s, 38 Mo ;
- sélection identique à celle des archives sur les 7 dates du 06 au 12/11 (un seul nom éligible : CTUSDT, âge 37 à 42 jours, médiane 20,4 M USDT, tout près du seuil) ;
- 16 226 volumes journaliers et 1 344 valeurs horaires (ouverture, clôture, plus haut et plus bas de marque) identiques aux archives, écart relatif maximal nul ;
- 14 lignes jouées, aucun stop, aucun faux délistage ; mémoire de lecture ramenée de 793 à 277 Mo ; rejeu d'une semaine en 15 s.

**Ce que l'essai montre sur la stratégie elle-même :** au 13/11/2026, l'univers est presque vide. Un seul nom passe les filtres, et la médiane de volume de CTUSDT (20,4 M USDT) frôle le seuil. Le flux de jeunes cotations crypto liquides est mince depuis août 2026 (5 nouveaux symboles collectés depuis le 15/08). Un papier lancé maintenant risque de compter beaucoup de semaines vides ou à un seul nom, et d'atteindre difficilement les 300 lignes de shorts exigées en 52 semaines. À trancher avant le gel : garder le critère des 300 lignes, ou le remplacer par une durée prolongée jusqu'à 300 lignes.

**Reste avant le premier jour compté :**
1. Accord pour installer la tâche horaire sur le serveur (`cron`, à :05 chaque heure), puis 3 jours à blanc.
2. Décisions sur les points du § 3 de `PLAN_PAPIER_COHORTES.md` (montée en charge, tolérance du rejeu, facteurs de l'alpha, signal indicatif, filtres v2), sur la règle du signal manqué et sur le critère des 300 lignes.
3. Ligne de journal de gel, avec l'empreinte du commit du module et la date du jour 0.

## 6. Tâche horaire à blanc installée (13/11/2026)

Sur accord de Jonathan et Téo du 13/11/2026. **Fonctionnement à blanc : aucun jour n'est compté.**

- Code déployé : `/root/papier06`, extrait du commit `2572a4d` (fichier `COMMIT`), 15 tests verts sur le serveur.
- Données et sorties hors du code : `/root/papier06_data/donnees` (reprises de l'essai du 13/11, vérifiées égales aux archives) et `/root/papier06_data/sorties/a_blanc`.
- Tâche : `5 * * * * /root/papier06/systeme-trading/strategies/STRAT-20261102-06/run_papier06.sh`, un seul passage à la fois (`flock`), arrêt si moins de 300 Mo de disque libre, journal d'exécution `cron.log`. Copie de la crontab d'avant dans `/root/crontab_avant_papier06.txt`.
- Jour 0 à blanc : **14/11/2026**. La cohorte 0 reçoit son premier signal le 14/11 à 00:05 UTC, la cohorte 6 le 20/11.
- Exécution à la main avant l'installation : 3,7 s, 346 Mo de mémoire, collecte seule (avant le jour 0).
- Premier passage automatique vérifié : 13/11/2026 à 14:05 UTC (trace CRON du système), battement écrit, une heure de BTC ajoutée à la collecte avec son empreinte.
- La crontab contenait une ligne hebdomadaire de l'ancien module (`paper_trading_strat06.py --check-now`, lundi 00:05 UTC). **Retirée le 13/11/2026 à 16:11 UTC** sur décision de Jonathan et Téo, pour une seule source de signaux ; copie dans `/root/crontab_avant_retrait_ancien_module.txt`. Seule reste la tâche horaire du papier à 7 cohortes.

**Limite :** aucune alerte n'est envoyée si la tâche s'arrête (aucun canal de notification configuré). La surveillance se fait en lisant `battement.txt` et `cron.log`. Un battement de plus de 2 heures signale une panne.

**Après les 3 jours à blanc (à partir du 17/11/2026) :** lecture du journal et des incidents, premier rejeu sur les archives journalières, puis décisions du gel et ligne de journal fixant le jour 0 compté.

### 6.1 Premier jour à blanc (14/11/2026)

- **Signal de la cohorte 0** écrit le 14/11 à 00:05 UTC, à l'heure : **aucun nom éligible, semaine vide.** CTUSDT, seul nom retenu du 06 au 12/11, est passé sous le seuil : médiane de volume sur 30 jours à 19,62 M USDT pour 20 M (âge 44 jours). Aucune autre cotation de moins de 61 jours sur Binance au 14/11 (la plus récente avant CTUSDT date du 06/09). Lecture faite le 14/11 à 08:20 UTC sur les données collectées.
- **Deux défauts du code trouvés et corrigés** (commit `0424460`, 16 tests verts, redéployé à 08:17 UTC sous le verrou, sans croiser la tâche) :
  - le signal recalculé à chaque passage était comparé avec son heure d'écriture, ce qui produisait 16 faux incidents de 01:05 à 08:05 UTC. Ils restent dans `incidents.csv` (ajout seul), suivis d'une ligne de note qui les explique. Le signal lui-même n'a jamais changé ;
  - l'entrée quotidienne du journal s'écrivait à 00:05, avant l'exécution de 01:00. Elle s'écrit désormais au premier passage après 01:00, avec le signal du jour. L'entrée du 14/11, déjà écrite, reste telle quelle.
- **Constat pour le gel :** l'univers est vide au premier jour. Si cela dure, le papier comptera surtout des semaines vides et n'atteindra pas les 300 lignes de shorts. Le critère des 300 lignes est à trancher avant le gel (§ 5).

## 7. Rejeu des jours à blanc et gel (16/11/2026)

**Rejeu** (serveur, code `0424460`, 16/11/2026 08:51 UTC, sous le verrou de la tâche horaire) : les 3 signaux à blanc (cohortes 0, 1 et 2 des 14, 15 et 16/11, tous écrits à 00:05 UTC, à l'heure) sont refaits sur les archives journalières de data.binance.vision. **0 écart.** Les trois signaux sont vides des deux côtés : CTUSDT, seule cotation de moins de 61 jours, reste sous le seuil (médiane 30 j à 19,29 M USDT au 16/11), avec des volumes collectés identiques aux archives (écart relatif maximal nul). **Limite :** aucune ligne n'ayant été jouée, le rejeu n'a comparé aucun prix d'entrée ; l'égalité des prix horaires avec les archives avait été vérifiée lors de l'essai du 13/11 (1 344 valeurs, écart nul). Aucun incident depuis la note du 14/11 à 08:17 UTC ; 69 passages horaires au 16/11 à 08:05 UTC.

**Gel, décision de Jonathan et Téo du 16/11/2026.** Règles du § 1 et critères du § 2 figés, avec l'exigence d'**au moins 300 lignes de shorts** maintenue. Points laissés ouverts au § 5, fixés au gel selon les propositions de `PLAN_PAPIER_COHORTES.md` § 3 :
- la semaine de montée en charge compte : les 52 semaines partent du jour 0 ;
- rejeu : sélection identique, prix d'entrée à 0,01 % près ;
- alpha : méthode du diagnostic B, facteurs recalculés sur la période du papier à partir des clôtures collectées ;
- signal montré à Jonathan : notionnel indicatif pour 10 000 USDT, sans valeur de décision ;
- filtres « v2 » : hors du papier et du verdict ;
- signal manqué : semaine vide, lignes précédentes soldées à t + 1 h.

Code du papier : commit `0424460`. Configuration de la v1 : `config_strat06.json`, SHA-256 `84f43d5b…298ca0c`, vérifiée à chaque passage. `config_bis06.json` : `statut = figee`, `jour_0 = 2026-11-17`. **Premier jour compté : 17/11/2026 à 00:00 UTC** (signal de la cohorte 0 à 00:05, exécution à 01:00). Point d'étape à 26 semaines : 18/05/2027. Verdict à 52 semaines : 16/11/2027.

**Risque publié au gel :** l'univers est vide au 16/11. Si le flux de jeunes cotations liquides reste aussi mince, le papier n'atteindra pas les 300 lignes de shorts et le verdict sera un rejet, quel que soit le rendement. Le gel accepte ce risque en connaissance de cause.

## 8. Série débridée, fantôme descriptive (déclarée le 18/11/2026)

Demande de Jonathan et Téo du 18/11/2026 : suivre en parallèle une version débridée, sans toucher au gel. **La série officielle (§ 1, § 2, § 7) reste la seule référence du verdict à 52 semaines.** Déclaration écrite le 2026-11-18T18:45:38Z, configuration `config_debridee06.json`.

**Deux écarts avec la v1, et rien d'autre :**
- liquidité : noms dont la médiane de volume sur 30 jours atteint 10 M USDT. Taille pleine (1/84) à partir de 20 M USDT, demi-taille (1/168) entre 10 et 20 M USDT ;
- couverture : jambe BTC sans financement, comme un BTC détenu au comptant. Les shorts gardent leur financement réel.

Âge, nombre de noms, stop, frais, glissements, 7 cohortes et calendrier sont ceux de la v1. **Jour 0 de la série débridée : 19/11/2026**, premier jour après la déclaration ; aucun jour antérieur n'est calculé.

**Intégrité.** Fichiers séparés (`signaux_debridee.csv`, `semaines_debridee.csv`, `lignes_debridee.csv`, `serie_debridee.csv`, `etat_debridee.json`, `incidents_debridee.csv`), calcul séparé, et une erreur de la série débridée n'interrompt jamais la série officielle. Le journal quotidien affiche la série débridée sous la série officielle, avec l'écart entre les deux. Tests : 4 nouveaux (cible à demi-taille, BTC sans financement et série officielle identique, fichiers officiels intacts et rien avant le jour 0, signal marquant les demi-tailles), 20 au total.

**Limites, à publier avec tout chiffre :**
- le coût du capital immobilisé par un BTC au comptant n'est pas compté (de l'ordre du taux court sur le notionnel BTC) : la série surestime l'économie de financement ;
- entre 10 et 20 M USDT, les carnets sont plus minces : les glissements de 0,05 % et de 0,30 % au stop y sont plus optimistes ;
- le seuil de 10 M USDT est la variante E05 de la v1, déjà lue sur les blocs consommés (Sharpe 1,28 contre 1,40 pour la base E09 au stop de 20 %) : la série n'est pas aveugle ;
- une promotion éventuelle de la série débridée serait une nouvelle stratégie, avec sa propre porte (`cerveau-trading` § 1, règle 2).
