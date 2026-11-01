# Tests synthétiques préalables de STRAT-20261031-03 (fiche § 1.7)

Écrit le 01/11/2026. Passage du 01/11/2026 à 09:18:12 UTC, Python 3.13, pandas 3.0.5, numpy 2.5.3. Journal brut : `tests_synthetiques_20261101T091812Z.log`.

**Résultat : 16 tests sur 16 passent.** Aucun prix de marché n'a été lu. Aucun essai du registre n'est consommé. Le statut reste `recherche`.

Code testé : `moteur_xsmom.py` (empreinte SHA-256 `a64fd77ed82ee643…`), tests : `test_moteur_synthetique.py` (`5c1da63d07ff9379…`). Commande : `python -B test_moteur_synthetique.py`.

## 1. Données

Marches aléatoires 1 h log-normales, graines fixes. Un facteur BTC, 36 à 40 symboles de bêta tiré entre 0,6 et 1,4, bruit propre de même volatilité (0,6 % par heure), volumes log-normaux. Bougies journalières agrégées depuis le 1 h. Prix de marque approché par les mèches 1 h. Aucune de ces séries ne ressemble au marché réel, et ce n'est pas leur rôle.

## 2. Tests exigés par la fiche

| Exigence du § 1.7 | Test | Résultat |
|---|---|---|
| Troncature : le signal à `t` reste identique après suppression des données postérieures | 42 lundis, coupe des zombies comprise, un symbole qui meurt en cours de période | 0 écart sur 42 |
| Contrôle du contrôle | Un score qui lit la dernière ligne disponible | Détecté : la comparaison échoue, comme attendu |
| Retrait des bougies plates | Prix figé, volume nul et financement qui survit après la mort | Séries coupées au dernier jour actif, financement compris. Jamais sélectionné ensuite |
| Délistage simulé | Short arrêté un mercredi | Sortie à la dernière clôture 1 h (23:00 UTC), frais et glissement normaux, ligne non remplacée, absent de l'univers suivant |
| Signe du financement | Événements à 0,5 %, 0,1 % et 0,2 % | Long paie 0,3 % du notionnel, short encaisse 0,3 %. L'événement du lundi 00:00 d'entrée appartient au portefeuille sortant, celui du lundi suivant à la ligne |
| Stop avec saut | Long sans saut, long ouvrant à −50 %, short ouvrant à +100 % | Sortie au niveau, puis au pire du niveau et de l'ouverture, glissement de stop compris. Le short perd 100,6 % du notionnel |
| Passage long → short | Tenue de 1,1 en long, cible de 1,0 en short | 2,1 échangés, donc deux côtés. Ligne conservée : seul l'écart paie |

## 3. Tests ajoutés

| Test | Résultat |
|---|---|
| Rotation de bout en bout, recalcul indépendant | Coût identique au moteur |
| Résidu sur BTC, marché à +3,6 % par jour | Classement brut corrélé au bêta à plus de 0,8. Score résiduel : corrélation moyenne sous 0,15 |
| Égalités | Départagées par ordre alphabétique |
| Ancienneté de 90 jours | Un symbole de 80 jours est exclu |
| **Aucun edge fantôme** : 24 chemins sans dérive, sans coût | Moyenne hebdomadaire de +0,039 % à brut 100 %, z = 0,34. Aucun rendement fabriqué par le moteur |
| Sensibilité : dérive résiduelle persistante plantée | Net positif, Sharpe de 16,3 sur 31 semaines. Le moteur voit un momentum qui existe. Dérive volontairement grossière, ce chiffre ne dit rien du marché |

## 4. Hypothèses du moteur à relire

Écrites en tête de `moteur_xsmom.py`. Elles ne figuraient pas mot pour mot dans la fiche.

- H1. Un rendement manquant dans les 60 jours de bêta exclut le symbole de la semaine.
- H2. Le financement porte sur le notionnel d'entrée, pas sur la valeur courante.
- H3. « Vivant » veut dire un volume non nul le dimanche `t − 1`, lu sans regarder après `t`.
- H4. Une ligne stoppée ou délistée reste vide jusqu'au lundi suivant (déjà dans la fiche).

## 5. Ce que ces tests ne couvrent pas

- Le chargement des archives data.binance.vision (klines 1 d et 1 h, marque, financement). Ce module reste à écrire, avec somme de contrôle (fiche § 2.4).
- Le prix de marque réel. Ici il est approché par les mèches du contrat.
- Le règlement de délistage à la moyenne de l'indice sur 30 minutes (fiche § 2.4).
- La liquidation d'un short à levier 1 vers +100 %. Le moteur laisse la perte dépasser 100 %, ce qui est prudent.
- Le bêta ex ante journalisé, le déséquilibre après un stop, la sortie par jambe et par poste au format du registre, le filtre E16 et les variantes E03 à E24.
- Le contrôle d'équivalence avec freqtrade en papier (fiche § 4).

## 6. Suite

E01 reste fermé jusqu'au module de données et à un second passage de ces tests sur des données réelles tronquées (troncature seulement, aucun rendement lu). La liste des actifs exclus de `commun-trading` § 2 reste ouverte.
