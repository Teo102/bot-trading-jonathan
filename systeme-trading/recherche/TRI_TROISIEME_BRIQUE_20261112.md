# Tri en 10 minutes : pistes pour la troisième brique du portefeuille

Écrit le 12/11/2026 par Claude Fable 5.2, selon la grille de `validation-edge` § 0 bis. Aucun rendement lu, aucune donnée téléchargée, aucun essai consommé. Résultat de recherche : aucun ordre, aucune recommandation d'investissement. Les données non vérifiées sont entre crochets.

## 1. Ce que « sans corrélation » veut dire ici

STRAT-07 a été écartée le 12/11/2026. Il reste deux briques.

| Brique | Ce qu'elle porte | Quand elle perd |
|---|---|---|
| STRAT-06-bis (papier aveugle) | Short de jeunes perpétuels, long BTC en couverture. Exposition au facteur « alts anciennes moins BTC » vers −0,30 (constat C16) | Hausses brutales des alts (stops, queue droite, constat C15) |
| STRAT-08 (gel en attente) | Long de quelques heures sur des alts, après une cascade de liquidations | Baisse durable où les cascades s'enchaînent |

Les deux vivent sur les perpétuels d'alts de Binance. Elles se compensent en partie sur le sens des alts. Elles partagent trois risques : la plateforme, la liquidité des alts, et les journées de stress.

Une troisième brique « sans corrélation » devrait donc éviter trois choses : le sens des alts, les journées de stress crypto comme moment de perte, et si possible la même plateforme.

**Limite.** La corrélation entre les deux briques actuelles est elle-même inconnue : STRAT-08 n'a aucun rendement. Une corrélation moyenne faible ne dit rien des semaines de stress. Elle se mesurera sur les semaines extrêmes, quand les deux séries existeront.

## 2. Résultat du tri

| Piste | Moteur du gain | T1 à T10 : point dur | Verdict | Orthogonalité |
|---|---|---|---|---|
| **H08 puis H24 / H25** : Polymarket (calibration, puis longshot et quasi-certitude) | Issue d'événements politiques et économiques | T6 : avis juridique local absent, accès bloqué en France. Preuve de calibration exigée avant tout capital (palier 2 à 300 prévisions résolues) | **Passe sous conditions déjà écrites** (tri du 02/11). En cours : 37 prévisions écrites le 09/11 | La plus forte, à condition d'exclure les marchés de prix crypto |
| **H34 (nouvelle)** : prime de variance sur options BTC, à risque défini (vente d'un strangle court, ailes achetées) | Écart entre volatilité implicite et volatilité réalisée | T4 : historique des cotations d'options gratuit et daté [à vérifier]. T6 : nouvelle plateforme, accès depuis les Émirats [à vérifier]. T7 : borné seulement si les ailes sont achetées | **Conditionnelle à un audit des données**, sans prix | Bonne en temps normal. Mauvaise dans les hausses violentes : les calls vendus perdent le jour où STRAT-06-bis touche ses stops |
| **H20** : écart de financement entre Binance et Bybit sur le même perpétuel | Segmentation des acheteurs à levier entre plateformes | T2 : niveau et durée de l'écart inconnus. T6 : deux comptes, pas de marge commune. T9 : famille du portage, déjà écartée trois fois (H02, H10, H31) | **Affaiblie.** Criblage sur le financement seul possible, lu bloc par bloc | Bonne sur le marché, mauvaise sur la plateforme : elle double le risque de plateforme |
| **H33 (nouvelle)** : écart du week-end sur les perpétuels non crypto (métaux, pétrole, actions, constat C9) | Flux de week-end des particuliers quand le sous-jacent est fermé, retour à l'ouverture du lundi | T3 et § 2 du skill : cotés depuis décembre 2025 seulement, soit environ 48 week-ends. Moins de 2 ans d'historique, aucun découpage en trois blocs possible. Mécanique de l'indice pendant la fermeture [non vérifiée] | **Écartée pour l'instant (T3).** Seule voie : un papier en avant, comme STRAT-06-bis | Forte : le sous-jacent n'est pas une crypto |
| **H13** : levier agrégé comme filtre | Réduit l'exposition quand le levier du marché est extrême | T3 : quelques dizaines d'épisodes par an | **Ce n'est pas une brique.** C'est un filtre posé sur les deux autres | Sans objet |
| **H16** : short après une annonce de délistage | Vente forcée avant le retrait | T3 : 89 retraits sur 49 dates depuis 2021 (mesure de STRAT-06, leçon L12), sous les 100 décisions. T5 : l'essentiel de la baisse tombe dans les secondes | **Écartée (T3, T5)** | Faible : même sens que STRAT-06-bis |
| **H17** : cotation au comptant d'un actif déjà coté en perpétuel | Attention autour de l'annonce | T4 : heure exacte des annonces. T5 : le saut est immédiat | **Affaiblie, non prioritaire** | Faible : même famille d'événements que STRAT-06 |
| **H14** : dérive autour de l'heure du financement | Longs qui ferment avant de payer | T2 : un versement courant vaut environ 0,01 % ; un aller-retour coûte au moins 0,14 % | **Écartée (T2)**, sauf aux pointes extrêmes, qui sont les événements de H31 | — |
| **H35 (nouvelle)** : portage sur contrats à terme datés (comptant contre trimestriel) | Prime du terme | T9 : famille du portage. T2 : rendement proche du taux court hors marché haussier | **Écartée (T2, T9)** | — |
| Tendance sur BTC et ETH seuls | Persistance des tendances | T9 : H01 rejetée. T3 : trop peu de décisions sur deux actifs | **Écartée** | — |
| Saisonnalité intra-journalière ou du week-end sur BTC | Aucun payeur contraint nommé | T1 | **Écartée** | — |
| H26 à H30 (dérivées de STRAT-06), H28 (déblocages de jetons) | Short d'alts | T9 pour la corrélation : même facteur que STRAT-06-bis | **Hors sujet pour une troisième brique** | Nulle |

## 3. Lecture

1. **Aucune piste ne passe le tri sans condition.** C'est le résultat honnête. Une brique vacante coûte moins qu'une brique faible : chaque hypothèse ouverte ajoute au compte global (8 testées sur des rendements au 12/11/2026).
2. **La seule piste vraiment étrangère aux cryptos est déjà en cours** : Polymarket. Elle ne demande aucune décision nouvelle, seulement de continuer la calibration et d'obtenir l'avis juridique. Elle ne donnera rien avant plusieurs mois.
3. **La seule piste nouvelle sérieuse est H34**, la prime de variance sur options. Elle change de moteur (la volatilité, pas le sens). Mais elle perd dans les deux queues, et sa queue haute coïncide avec la pire journée de STRAT-06-bis. Elle demande un autre moteur que freqtrade et une autre plateforme. Première étape possible, à coût nul : un audit des données d'options, sans prix, sur le modèle de l'audit du 09/11.
4. **H20 est la moins chère à cribler et la moins probable.** La famille a échoué trois fois. Un criblage n'aurait de valeur qu'avec la leçon de H31 : règle écrite avant calcul, lecture bloc par bloc et année par année, existence des deux jambes vérifiée. Mon jugement, non calculé : [une chance sur six de passer].
5. **H33 ne peut pas être testée sur le passé.** Si elle intéresse, elle se joue comme STRAT-06-bis : critères écrits, puis papier en avant. La collecte des prix du week-end peut commencer sans rien décider.
6. **H13 est utile ailleurs** : comme filtre de risque commun aux deux briques, pas comme source de gain.

## 4. Ce qui attend une décision de Jonathan et Téo

- Laisser la troisième brique vacante, ou ouvrir une seule des pistes : audit des données d'options (H34), criblage de l'écart de financement (H20), ou collecte en avant du week-end (H33).
- Aucune de ces étapes n'est lancée. Aucune fiche n'est ouverte.
