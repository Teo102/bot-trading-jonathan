# Simulateur maker avec file d'attente et antisélection, 2026-11-01T09:11:23Z

Résultat de recherche sans ordre ni clé. Aucun appel réseau : le script `simulateur_file_attente.py` relit les fichiers des collectes `20261101T001303Z` (ligne principale) et `20261031T224031Z` (contrôle de stabilité). Heures en UTC. Les hypothèses H1 à H7 sont listées au § 5.

## Verdict en une phrase

**Dès qu'on modélise la file d'attente, le gain maker hypothétique disparaît.** Hors mi-mandat, à 1 h, un maker qui cote au meilleur prix perd 0,272 ¢ par part [IC 95 % : -0,631 ; -0,176] et 15,42 $ pour 1 000 $ exécutés [-35,89 ; -8,43]. Le simulateur naïf donnait -0,084 ¢ [-0,536 ; 0,021], et le +4,83 $ du classement venait des marchés du mi-mandat. Ces marchés tombent eux aussi à -7,38 $ [-18,87 ; 0,52] avec la file.

## 1. Pourquoi le simulateur naïf trompe

Le simulateur de `clob_collector.py` suppose un remplissage sur chaque trade public, au prix du trade. Il oublie deux faits.

1. **La file.** Au meilleur prix, des milliers de parts attendent devant un nouvel ordre. Sur le marché Fed de décembre, l'instantané montre 38 832 parts au bid. Un ordre de 357 parts ne passe qu'après elles.
2. **La sélection.** Un ordre en bout de file est servi surtout quand un taker vide tout le niveau. Ces moments sont ceux où le prix part contre le maker. Quand le prix s'éloigne, l'ordre n'est pas servi et doit être reposé.

## 2. Couche (b), rejeu approché sur l'historique REST

Données : 82 395 trades publics sur 40 marchés, fenêtre de 14 jours se terminant le 01/11/2026 à 00:13 UTC. Ordre fictif de 100 $ environ par côté (taille minimale respectée). Bootstrap par événement, 2 000 tirages, graine 20261031.

### 2.1 Ligne principale, hors mi-mandat (23 marchés, 16 événements)

| Variante | Remplissages | ¢/part à 1 min | ¢/part à 1 h | IC 95 % (1 h) | Net $/1 000 à 1 h | IC 95 % |
|---|---:|---:|---:|---|---:|---|
| Naïf (chaque trade) | 13 867 | -0,040 | -0,084 | [-0,536 ; 0,021] | -2,54 | [-26,95 ; 0,60] |
| File nulle, meilleur prix | 12 462 | +0,012 | -0,038 | [-0,247 ; 0,048] | -1,59 | [-16,63 ; 1,51] |
| **File ×1, meilleur prix (base)** | **2 443** | **-0,264** | **-0,272** | **[-0,631 ; -0,176]** | **-15,42** | **[-35,89 ; -8,43]** |
| File ×0,5, meilleur prix | 2 913 | -0,230 | -0,239 | [-0,569 ; -0,155] | -13,22 | [-34,35 ; -6,82] |
| File ×1, milieu ±1 cent | 407 | -1,615 | -1,488 | [-2,046 ; -0,878] | -38,82 | [-67,96 ; -23,32] |
| File ×0,5, milieu ±1 cent | 413 | -1,556 | -1,462 | [-2,050 ; -0,860] | -38,20 | [-64,23 ; -23,95] |

Décomposition de la base, hors mi-mandat, à 1 h.

| Type de remplissage | Remplissages | Événements | ¢/part | IC 95 % |
|---|---:|---:|---:|---|
| Servi à notre prix, après la file | 312 | 7 | +0,094 | [-0,010 ; 0,387] |
| Servi par un trade à un prix moins bon (niveau vide devant nous) | 2 131 | 16 | -0,334 | [-0,802 ; -0,211] |

L'ordre est servi par un trade traversant dans 87 % des cas. C'est le mécanisme de l'antisélection. **Contre-épreuve, ordres annulés sans remplissage :** si on les avait servis au moment de l'annulation, ils auraient gagné +0,76 ¢ par part à 1 h (4 884 ordres). On manque les bons remplissages et on reçoit les mauvais.

Taux de remplissage de la base, hors mi-mandat : 2 332 ordres sur 7 305 reçoivent au moins une part (31,9 %). Les parts remplies font 7,65 % du volume que le naïf s'attribue. La médiane est de 913 parts par jour et par marché.

Le placement à ±1 cent du milieu fait pire. Avec un pas d'un cent et un écart d'un cent, il pose l'ordre un cran derrière le meilleur prix. Il n'est alors servi que quand le prix traverse un niveau entier.

### 2.2 Mi-mandat, montré à part (17 marchés, 10 événements)

| Variante | ¢/part à 1 h | IC 95 % | Net $/1 000 à 1 h | IC 95 % |
|---|---:|---|---:|---|
| Naïf | +0,255 | [0,121 ; 0,315] | +6,02 | [2,53 ; 9,30] |
| File nulle, meilleur prix | +0,250 | [0,091 ; 0,326] | +7,52 | [1,96 ; 13,94] |
| File ×1, meilleur prix | -0,245 | [-0,789 ; 0,015] | -7,38 | [-18,87 ; 0,52] |

Le gain du mi-mandat suppose d'être en tête de file. Sur ces marchés la file au meilleur prix va jusqu'à 2,49 millions de parts, et un nouvel ordre ne reçoit que 0,64 % du volume naïf. Le positif du classement ne se transpose pas à un nouvel entrant.

### 2.3 Marchés à frais actifs, hors mi-mandat (5 événements, rebate API inclus)

Base à 1 h : -1,96 ¢ par part [-2,65 ; -1,48], net -41,40 $ pour 1 000 $ [-54,26 ; -27,11], dont un rebate de +6,36 $. Seulement 175 remplissages sur des marchés créés du 28 au 30/10, donc l'âge et les frais restent confondus (voir le rapport du collecteur).

### 2.4 Stabilité

La collecte du 31/10 22:40 UTC donne la même lecture : base hors mi-mandat à 1 h, -0,271 ¢ par part [-0,597 ; -0,177] et -15,46 $ pour 1 000 $ [-32,26 ; -8,20]. Les deux fenêtres partagent l'essentiel de leurs trades. Ce n'est donc pas une réplication indépendante.

### 2.5 Récompenses de liquidité, hors du net

Elles ne sont pas incluses. L'estimation du collecteur, une borne haute pour 1 000 $ posés au meilleur prix, va de 0,07 à 68,64 $ par jour selon le marché (médiane 3,55 $), avec un écart maximal admis de 3,5 à 6,5 ¢. Ce n'est pas une mesure de notre part réelle, qui dépend du temps passé dans la bande et de la concurrence [non mesurée]. À titre d'ordre de grandeur : sur 913 parts par jour à 0,5 $ (≈ 456 $), une perte de 15 $ pour 1 000 $ coûte environ 7 $ par jour. La récompense pourrait donc compenser sur certains marchés. Cette piste reste à mesurer, sans conclusion à ce stade.

## 3. Couche (a), rejeu exact sur la fenêtre WebSocket

| Collecte | Fenêtre | Événements jeton 0 | Trades vus | Ordres posés (meilleur prix) | Remplissages |
|---|---|---:|---:|---:|---:|
| 20261101T001303Z | 00:13:39 à 00:17:40, 4 min | 2 851 | 7 | 51 | 0 |
| 20261031T224031Z | 4 min | 2 857 | 8 | 36 | 0 |

**Cette couche ne permet aucune conclusion.** Il y a 7 et 8 trades en 4 minutes, et aucun ne touche un ordre fictif. De plus, les messages `book` (54 comptés) n'ont pas été écrits dans le fichier. La taille d'un niveau n'est donc connue qu'après sa première mise à jour, d'où 1 503 attentes sur un niveau inconnu. Le code est prêt et testé, mais il lui faut une capture longue qui enregistre aussi les instantanés `book`.

## 4. Ce que ce résultat dit et ne dit pas

- Il rejette, pour ce placement et ces marchés, l'idée qu'un maker passif capte l'écart. Le +4,83 $ pour 1 000 $ de la note de régime est un artefact du remplissage naïf et du mi-mandat. **Nous proposons de corriger la matrice de la note de régime en ce sens. Rien n'est appliqué.**
- Il ne teste pas un maker qui décide quand coter (par exemple retirer ses ordres avant un mouvement), ni la capture des récompenses, ni la lecture des règles de résolution. Ces pistes restent ouvertes.
- La lecture « dernière cote » (milieu de l'instantané) reste indéterminée : +0,121 ¢ [-0,222 ; 0,377] pour la base hors mi-mandat. Elle est dominée par la dérive sur 14 jours.

## 5. Hypothèses et limites

| Code | Hypothèse | Effet probable |
|---|---|---|
| H1 | File devant nous = parts à ±1 cent du milieu dans l'instantané du 01/11 00:13, supposées stables sur 14 jours. Avec un pas de 0,001, divisées par le nombre de niveaux de la bande | Inconnu. La variante ×0,5 change peu le résultat |
| H2 | Un trade à un prix moins bon que notre ordre nous sert d'abord, jusqu'à min(reste, taille du trade) | Contrefactuel : notre présence aurait changé le trade |
| H3 | Couche WS : annulations au prorata de la file | Non testée sur données, faute de remplissage |
| H4 | Milieu reconstruit depuis le dernier trade et un écart constant (écart médian observé, repli sur l'instantané) | Validé en moyenne : le naïf retrouve -0,084 ¢ à 1 h, contre -0,083 ¢ avec l'historique de prix du collecteur. Juste après un trade traversant, il peut exagérer le mouvement à 1 min |
| H5 | Couche WS : une baisse de niveau à ±2 s d'un trade au même prix est attribuée au trade | — |
| H6 | Ordre des trades d'une même seconde : celui du fichier, inversé | Faible |
| H7 | Aucune limite d'inventaire, ordres reposés sans délai ni latence | Optimiste pour le maker |

Autres limites :

- 36 % des milieux à 1 h datent de plus de 30 minutes (871 sur 2 443), faute de trade récent.
- L'échantillon compte 16 événements hors mi-mandat, une seule fenêtre de 14 jours, juste avant le scrutin.
- Notionnel compté en prix du jeton 0, alors que le collecteur prend le prix du jeton traité. Les $ pour 1 000 $ ne sont donc pas strictement comparables. La lecture en ¢ par part fait référence.
- Les témoins résolus sont exclus, faute d'instantané de carnet.

## 6. Fichiers

`20261101T091123Z_file_attente_agrege.csv` (toutes variantes, groupes et horizons), `_par_marche.csv`, `_ws.csv`, `_complet.json`. Tests : `test_simulateur_file_attente.py`, 11 tests sur cas synthétiques, tous passés le 01/11/2026.
