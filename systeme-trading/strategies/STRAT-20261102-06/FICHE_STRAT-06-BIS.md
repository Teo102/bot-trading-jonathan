# Fiche STRAT-06-bis — Dérive des jeunes perpétuels, cohortes quotidiennes, verdict par le papier

Rédigée le 09/11/2026 par le Cerveau, sur décision de Jonathan et Téo du même jour (réouverture après rejet de la v1). Résultat de recherche, aucun ordre, `dry_run` permanent, capital nul.

**Statut des critères : PROPOSÉS.** Ils deviennent figés par une ligne de journal de Jonathan et Téo, **avant le premier jour compté**. Aucune semaine de papier antérieure à ce gel ne compte dans le verdict.

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
