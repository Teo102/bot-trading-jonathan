# Recherche fondamentale sur la dérive des perpétuels nouvellement cotés (STRAT-20261102-06)

*Note de recherche interne, 05/11/2026. Cerveau du système de trading de Jonathan et Téo.*

Résultat de recherche, aucune recommandation d'investissement, aucun ordre. Toutes les mesures empiriques portent sur des blocs déjà consommés (01/2021 à 07/2025). Elles sont **a posteriori**, hors N, et ne changent aucune règle figée de STRAT-06. Elles servent à comprendre, pas à valider.

---

## Résumé

On vend chaque semaine jusqu'à six perpétuels USDT de Binance âgés de 7 à 60 jours, couverts par BTC. Sur 1 104 lignes courtes, 218 stops et 238 semaines, l'autopsie établit six faits.

1. **Le résultat est un pari sur un facteur commun, avec une pente idiosyncratique.** La corrélation moyenne entre deux noms vendus la même semaine vaut 0,28. Six noms valent donc environ 2,5 noms indépendants. Les 10 % meilleures semaines font 119 % du gain net, et les 10 % pires en retirent 76 %. Seules 55 % des semaines sont positives.
2. **Les gros gains naissent dans les krachs d'alts.** Onze des vingt plus gros gains tombent dans quatre semaines : mai 2021, janvier 2022, mai 2022, janvier 2025. Dans les 10 % pires semaines de la stratégie, 79 % des noms vendus montent, de +24 % en moyenne.
3. **La queue droite est extrême et précoce.** Sans stop, le rendement hebdomadaire d'un nom vendu a une asymétrie de +4,9 et un aplatissement de 46. 3,9 % des lignes prennent +50 % en une semaine, 1,1 % prennent +100 %. Ces hausses frappent des cotations d'un âge médian de 23 jours.
4. **Les stops ne se concentrent pas en début de semaine, mais à certaines heures.** La médiane tombe 71 heures après l'entrée, et la répartition par jour de tenue n'est pas significativement différente de l'uniforme (p ≈ 0,31). En revanche, 35 % des stops tombent entre 00:00 et 05:59 UTC (p ≈ 0,0004), avec des pics aux heures de versement du financement (00:00 et 16:00).
5. **Le financement est un revenu en moyenne, mais il se retourne en 2025.** Le short médian reçoit +10 % par an. Mais 15,5 % des lignes paient plus de 10 % par an, et 2,6 % plus de 100 %. En 2025, cette part monte à 36 %, et le financement total devient négatif. C'est le premier indice chiffré d'encombrement du trade.
6. **Le mécanisme économique est double et seulement partiellement identifiable.** La levée de la contrainte de vente à découvert (Miller, 1977) explique la période 2021-2024. L'offre en surplomb des jetons à faible flottant (12,3 % de capitalisation sur valorisation diluée pour les lancements de 2024, Binance Research) explique la période 2024-2025. Faute de calendriers de déblocage datés, le rôle des déblocages dans la fenêtre de 7 à 60 jours ne se teste pas avec les données du dépôt.

---

## 1. Données et méthode

| Source | Contenu | Usage |
|---|---|---|
| `CDV_controle_reproduction_lignes.csv` | 1 330 lignes de la base continue (1 104 shorts, 226 couvertures BTC), 220 stops | Stops, gains, persistance, financement |
| `E11_lignes.csv` | Mêmes sélections, **sans stop** | Rendements hebdomadaires non tronqués : queue droite, corrélations |
| `CDV_controle_reproduction_semaines.csv` | 238 semaines | Concentration temporelle |
| `DIAG_E0{1,2}_classement_noms.csv` | Date de cotation du perpétuel, ancienneté au comptant | Âge à l'entrée, classe |
| `DIAG_E0{1,2}_facteurs.csv` | Rendements hebdomadaires de BTC et du panier d'alts anciennes | Bêtas, semaines de crise |

- **Code :** `recherche/analyses/autopsie_strat06.py`.
- **Sorties :** `recherche/analyses/sorties_strat06/` (JSON et CSV).
- **Unités :** à brut 100 %, avec un notionnel de 1/12 par ligne. Un gain de +0,05 vaut 5 % du capital à brut 100 %.
- **Rendement de prix d'une ligne :** sortie / entrée − 1, du lundi 01:00 UTC à la sortie.
- **Financement annualisé d'une ligne :** financement / notionnel / jours tenus × 365, compté positivement quand le short reçoit.

**Corrélation interne.** Le panel change de noms chaque semaine. La corrélation moyenne entre paires s'estime donc par le coefficient de corrélation intra-semaine :

ρ̂ = Σ_semaines [ (Σᵢ dᵢ)² − Σᵢ dᵢ² ] / ( Σ_semaines nₛ (nₛ − 1) · σ² ),

où dᵢ est l'écart du rendement du nom i à la moyenne globale. Le nombre effectif de noms indépendants vaut alors N / (1 + (N − 1) ρ̂).

**Limites :**
- les rendements de E11 sont hebdomadaires ; aucune trajectoire intra-hebdomadaire n'est disponible hors des stops ;
- l'heure d'un stop est l'heure de la bougie qui le franchit ;
- l'âge vient du premier volume de l'archive Binance.

---

## 2. Autopsie empirique

### 2.1 Les 218 stops des shorts (et 2 stops de couverture)

| Mesure | Valeur |
|---|---:|
| Taux de stop des shorts | 19,7 % des lignes |
| Délai entre l'entrée et le stop : 10 %, 25 %, médiane, 75 %, 90 % | 17 h, 39 h, **71 h**, 119 h, 145 h |
| Stops dans les 24 premières heures, dans les 48 premières heures | 16,1 %, 32,1 % |
| Stops dans les 6 premières heures | 2 sur 218 |
| Par jour de tenue (1 à 7) | 35, 35, 41, 27, 26, 30, 24 |
| Test d'uniformité sur 7 jours | χ² = 7,2 (6 degrés de liberté), p ≈ 0,31 |
| Par tranche horaire UTC (00-05, 06-11, 12-17, 18-23) | **76**, 45, 62, 35 |
| Test d'uniformité sur 4 tranches | χ² = 18,2 (3 degrés de liberté), p ≈ 0,0004 |
| Heures des pics | 00:00 (18 stops), 16:00 (14), 17:00 (12) |
| Taux de stop par âge à l'entrée (7-13 j, 14-27 j, 28-60 j) | 24,6 %, 21,5 %, 17,1 % |
| Taux de stop par année (2021 à 2025) | 25,0 %, 15,0 %, 15,7 %, 19,5 %, 23,0 % |
| Prix perdu sur les lignes stoppées / gagné sur les autres | −552 points / +714 points |

**Lecture :**

1. **Les stops ne tombent pas dès le lundi.** Il n'y en a que 2 dans les 6 heures qui suivent l'entrée. La moitié tombe en trois jours, et la distribution par jour est compatible avec l'uniforme. Les jours 1 à 3 en portent un peu plus (51 % contre 43 % attendus), sans que l'écart soit significatif. Une hausse forcée est un processus diffus dans la semaine, pas une réaction à l'ouverture de la position.
2. **Les stops se concentrent la nuit en Europe.** Entre 00:00 et 05:59 UTC, la séance asiatique, tombent 35 % des stops contre 25 % attendus. Les heures 00:00 et 16:00 sont deux des trois heures de versement du financement sur 8 heures. Ensemble, les trois heures 00, 08 et 16 portent 40 stops contre 27 attendus. C'est un indice, sur de petits effectifs, d'une **dynamique autour du versement du financement**, qui rejoint l'hypothèse H14 (dérive à l'heure de versement).
3. **Plus la cotation est jeune, plus elle déclenche le stop** (24,6 % contre 17,1 %). Le dégonflement le plus fort coexiste avec les hausses les plus violentes. C'est la signature d'une prime de risque.
4. **Le stop est une dépense de 552 points**, financée par 714 points gagnés sur les autres lignes. Le résultat de la stratégie est la différence de deux grands nombres, ce qui explique sa sensibilité au glissement au stop : environ 24 points par point de glissement (audit, § 3.2).

### 2.2 Les 20 plus gros gains contre les 20 plus grosses pertes (lignes de shorts)

| | 20 plus gros gains | 20 plus grosses pertes |
|---|---:|---:|
| Somme | +79,8 points (**44,5 %** du gain de la jambe courte) | −51,9 points |
| Rendement de prix médian du nom | **−46,9 %** en une semaine | **+30,4 %**, soit le stop sur les 20 |
| Âge médian à l'entrée | 24,5 j | 14 j |
| Volatilité hebdomadaire médiane du nom (sans stop) | 27,6 % | 19,8 % (19,9 % pour l'ensemble) |
| Noms distincts | 20 | 16 (BERA ×3, MOVE ×2, 1000SHIB ×2) |
| Classes | 8 récents, 7 sans comptant Binance, 5 anciens | 17 récents, 3 anciens |
| Semaines | **11 sur 20 dans 4 semaines** : 17/05/2021 (×4), 27/01/2025 (×4), 17/01/2022 (×3), 09/05/2022 (×2) | Dispersées sur 2021-2025 |

Plus gros gains : ARC −64 % (03/2025), MUBARAK −60 % (03/2025, 7 jours d'âge), DENT −61 % (05/2021), DAR −55 % (05/2022), PEOPLE −53 % (01/2022), SWARMS −50 %, VINE −49 %, AI16Z −47 %, AIXBT −45 % (semaine du 27/01/2025).

Plus grosses pertes : toutes plafonnées au stop. BERA y figure trois fois (17/02, 24/02 et 24/03/2025), et MOVE deux semaines de suite en décembre 2024.

**Lecture :**

1. **L'asymétrie est construite par le stop.** Les pertes sont plafonnées à +30,4 %, les gains vont jusqu'à −64 % en une semaine. Le profil de la stratégie ressemble à une vente d'option couverte par un stop, ou à un achat de « gamma » sur la baisse.
2. **Les gros gains ne sont pas idiosyncratiques.** Ils naissent dans les krachs d'alts : le krach de mai 2021, janvier 2022, l'effondrement de Terra en mai 2022, et le krach des jetons « agents d'IA » de fin janvier 2025. La jambe courte encaisse un facteur commun que la couverture BTC n'annule pas (C16).
3. **Les pertes viennent surtout de jetons neufs** (17 sur 20). Elles sont plus jeunes (14 j contre 24,5 j) et ne sont pas plus volatiles que la moyenne. Une hausse forcée frappe un nom ordinaire, pas un nom repéré comme dangereux.
4. **La règle de réentrée.** Un nom stoppé revient le lundi suivant (règle H4 du moteur). Mesure sur 178 lignes qui suivent un stop du même nom : le taux de stop monte à 24,7 % contre 18,8 %, mais le gain moyen reste proche (+0,0014 contre +0,0017). Au total, ces lignes rapportent +25 points. **Réentrer n'est pas destructeur en moyenne**, mais cela concentre les pertes sur des noms en tendance (BERA).

### 2.3 Persistance par nom

| Mesure | Valeur |
|---|---:|
| Noms distincts vendus, séries de semaines consécutives | 236, 266 |
| Longueur des séries (1 à 8 semaines) | 62, 35, 36, 20, 17, 16, 37, 43 |
| Longueur moyenne d'une série, lignes par nom | 4,2 semaines, 4,7 lignes |
| Gain moyen par série selon la longueur (1, 2, 3, 4, 5, 6 semaines et plus) | +0,007, +0,002, +0,001, +0,016, +0,015, +0,008 |
| Noms perdants sur l'ensemble de leur passage | 81 sur 236 (34 %) |
| Gain médian par nom | +0,010 |
| Part du gain des 10 meilleurs noms, des 30 meilleurs | 43 %, **103 %** |

Dix meilleurs noms : DENT +0,118 ; MUBARAK +0,093 ; USUAL +0,077 ; MYRO +0,077 ; ARC +0,075 ; ICP +0,069 ; DUSK +0,068 ; DAR +0,066 ; ALICE +0,066 ; KAITO +0,063.

Dix pires : LUNA −0,138 ; GRT −0,129 ; 1INCH −0,097 ; BIGTIME −0,089 ; TIA −0,080 ; ORDI −0,078 ; BERA −0,071 ; JUP −0,064 ; WCT −0,063 ; ALT −0,062.

**Lecture :**

1. **La distribution des séries est bimodale.** Un nom passe soit une semaine (62 séries : il sort du classement par liquidité), soit toute la fenêtre de 7 à 8 semaines (80 séries). Les noms qui restent liquides deux mois sont ceux qui attirent durablement la spéculation.
2. **Les séries de 4 à 5 semaines sont les plus rentables** (+0,015 à +0,016 par série). Le dégonflement prend du temps, ce qui est cohérent avec l'avance encore positive entre 28 et 60 jours (diagnostic A).
3. **Le gain est très concentré par nom.** Trente noms font tout le gain net. Les 206 autres s'annulent ensemble. Un tiers des noms perd. **L'espérance par nom est faible et la dispersion énorme** : le résultat dépend de la présence de quelques effondrements massifs, ce qui rend la puissance statistique faible (audit, § 5.3).

### 2.4 Concentration temporelle

- Les 23 meilleures semaines (10 %) font **+118,6 %** du gain net total.
- Les 23 pires en retirent **−75,9 %**.
- 54,6 % des semaines sont positives.
- Le Sharpe annuel de 1,31 repose sur une poignée de semaines de krach.

---

## 3. Microstructure et mécanisme économique

### 3.1 Faible flottant et forte valorisation diluée (2024-2025)

**Ce que disent les sources.**
- Binance Research (mai 2024, « How Did We Get to Low Circulation / High FDV Tokens? ») chiffre à **12,3 %** le rapport entre capitalisation en circulation et valorisation diluée des jetons lancés en 2024. C'est le plus bas des années récentes.
- Le même rapport estime à environ **155 Md$** les jetons à débloquer entre 2024 et 2030, et à plus de 91 Md$ le capital privé investi dans les projets depuis 2017 (repris par Crypto Briefing et Cointelegraph).
- Binance Research y relie le faible flottant à l'abondance de capital privé, à une valorisation de marché privé reportée sur le marché public, et à des largages gratuits qui créent une offre vendeuse immédiate.

**Pourquoi la structure produit une dérive :**
1. **Prix fixé sur un flottant minuscule.** Avec 12 % du stock en circulation, une demande modeste fixe une valorisation diluée élevée. Le prix de lancement reflète l'offre du jour, pas l'offre à venir.
2. **Offre future connue mais non escomptée.** Si les acheteurs n'escomptent pas l'offre à venir, par attention limitée ou par horizon court, le prix dérive à la baisse à mesure qu'elle arrive. C'est le pendant crypto du sous-rendement de long terme des introductions en bourse (Ritter, 1991).
3. **Concentration des vendeurs naturels.** Destinataires de largages, teneurs de marché détenteurs de jetons prêtés, premiers investisseurs couverts par short du perpétuel : tous vendent dans les premières semaines.

**Ce que le dépôt montre.**
- En validation (2024-2025), 54 % du gain des shorts vient de jetons cotés au comptant depuis moins de 180 jours, et 30 % de jetons sans comptant Binance (C14).
- Les plus gros gains de 2025 sont des jetons de ce type (MUBARAK, ARC, VINE, SWARMS, AI16Z).
- C'est **compatible** avec le mécanisme, mais **non identifié** : faute du rapport capitalisation / valorisation diluée daté de chaque jeton à sa cotation, le dépôt ne peut pas trier les noms par flottant.

**Test à construire (hypothèse H28).** Il faut l'offre en circulation à la date de cotation. Sa source datée est [à trouver] : le critère T4 est incertain. Prédiction : l'avance des shorts croît quand le rapport capitalisation / valorisation diluée baisse.

### 3.2 Déblocages, calendriers d'acquisition et ventes de largages dans la fenêtre de 7 à 60 jours

**Ce que disent les sources.**
- **Keyrock, plus de 16 000 déblocages sur 40 jetons** (12/2024, mis à jour en 07/2025) :
  - environ 90 % des déblocages exercent une pression à la baisse ;
  - l'effet commence environ 30 jours **avant** l'événement et se stabilise environ 14 jours après ;
  - les déblocages des équipes sont les pires (jusqu'à −25 %), ceux des investisseurs sont plus maîtrisés, ceux du développement de l'écosystème sont légèrement positifs (+1,18 %).
  - Keyrock est un teneur de marché qui vend des services liés aux déblocages : la source n'est pas neutre.
- **Keyrock, 62 largages de 2024 :** 88,7 % des jetons valent moins 90 jours après leur cotation. La plupart chutent dans les 15 premiers jours (BeInCrypto).

**Correspondance avec la fenêtre de STRAT-06 :**

| Vendeur | Moment typique | Dans la fenêtre de 7 à 60 jours ? |
|---|---|---|
| Destinataires de largages | Génération du jeton et premiers jours | **Oui**, surtout de 7 à 15 jours |
| Teneurs de marché (jetons prêtés) | Continu dès la cotation | Oui |
| Couverture des détenteurs bloqués par short du perpétuel | Dès qu'un perpétuel existe | Oui (pression sur le financement et la base) |
| Premières tranches d'acquisition des équipes et des investisseurs | Souvent après un délai de 6 à 12 mois [ordre de grandeur courant, non vérifié jeton par jeton] | **Rarement** |
| Anticipation de ces tranches (−30 jours selon Keyrock) | 30 jours avant la tranche | Seulement si la première tranche tombe entre 37 et 90 jours après la cotation |

**Lecture.** Dans la fenêtre de STRAT-06, le moteur le plus plausible est **la vente des largages et des stocks des teneurs de marché**, pas les tranches d'acquisition des équipes. Le profil par âge le confirme sans le prouver : l'avance sur le témoin est maximale entre 7 et 13 jours dans les trois essais mesurés (+3,0, +5,8 et +4,9 points par semaine), puis décroît.

Les calendriers de déblocage datés ne sont pas dans le dépôt. Les relier aux lignes (hypothèse H28) demande une source historique datée, sans biais du survivant [à trouver].

### 3.3 Miller (1977) et la levée de la contrainte de vente à découvert

**Le modèle.**
- Quand les investisseurs divergent sur la valeur et que la vente à découvert est impossible ou coûteuse, le prix reflète les **plus optimistes** : les pessimistes ne peuvent que rester à l'écart. Le prix dépasse alors la valeur moyenne anticipée (Miller, 1977).
- Avec des optimistes qui changent de camp au fil des nouvelles, le prix contient même une option de revente, avec beaucoup de volume (Harrison et Kreps, 1978 ; Scheinkman et Xiong, 2003).
- **Introduire un instrument de vente** laisse les pessimistes s'exprimer : le prix baisse vers la moyenne. Fostel et Geanakoplos (2012) montrent qu'introduire un instrument de vente (les CDS sur prêts immobiliers en 2005-2007) peut faire baisser le prix de l'actif sous-jacent.

**L'application au perpétuel.**
- Avant son premier perpétuel, un jeton ne se vend à découvert que par emprunt sur marge au comptant, souvent indisponible, rare ou cher pour les petites capitalisations.
- **La cotation du perpétuel lève la contrainte d'un coup**, avec du levier et sans emprunt. La théorie prédit une baisse étalée sur quelques semaines, le temps que les pessimistes construisent leurs positions.

**Les prédictions et ce que le dépôt en dit :**

| Prédiction | Mesure | Verdict |
|---|---|---|
| Effet plus fort quand la contrainte était plus forte avant le perpétuel (jetons anciens, sans marge disponible) | 2021-2024 : jetons anciens au comptant +0,012 par nom contre +0,003 pour les récents ; 59 % du gain (C14) | **Compatible** |
| Effet concentré au début, puis décroissant | Avance maximale à 7-13 jours, décroissante en E01 et E02 (diagnostic A) | Compatible |
| Effet plus fort quand la divergence d'opinion est forte (volume élevé) | E06 (50 M USDT) ≥ base ; séries longues des noms durablement liquides plus rentables | Partiellement compatible |
| Effet qui s'épuise quand les contraintes disparaissent partout | Stock d'anciens jetons sans perpétuel épuisé en 2024-2025 (9 noms en E02) | Compatible |
| Après la levée, prix de « consensus » et dérive nulle | Avance encore positive à 28-60 j (+1,0 à +1,9 point par semaine) | Non tranché |

**Limite.** La disponibilité de l'emprunt sur marge de chaque jeton avant son perpétuel n'est pas dans le dépôt. Sans elle, la prédiction centrale ne se teste que par la proxy de l'ancienneté au comptant.

### 3.4 Synthèse du mécanisme

| Période | Payeur principal | Mécanisme | Force de la preuve |
|---|---|---|---|
| 2021-2024 | Optimistes d'anciens jetons, jusqu'alors impossibles à vendre à découvert | Miller : levée de la contrainte | Indirecte, par l'ancienneté au comptant |
| 2024-2025 | Acheteurs tardifs de jetons à faible flottant, face aux vendeurs de largages et aux teneurs de marché | Offre en surplomb, ventes de largages | Indirecte : composition des gains, littérature de Binance Research et de Keyrock |
| Toutes | Le short lui-même, payé pour porter les hausses forcées | Prime de risque de queue | **Directe** : asymétrie de +4,9, rôle constitutif du stop (C15) |

**La seule composante démontrée par les données du dépôt est la prime de risque de queue.** Les deux mécanismes informationnels restent des explications plausibles, non testées.

---

## 4. Frictions réelles et liquidité

### 4.1 Distribution du financement sur les 1 104 lignes de shorts

| Quantile du financement annualisé reçu par le short | Valeur |
|---|---:|
| 1 % | −167 %/an |
| 5 % | −66 %/an |
| 10 % | −23 %/an |
| 25 % | 0 % |
| Médiane | **+10,3 %/an** |
| 75 % | +19,7 %/an |
| 90 % | +54,7 %/an |
| 95 % | +94,7 %/an |
| 99 % | +187 %/an |

| Mesure | Valeur |
|---|---:|
| Lignes où le short paie plus de 10 %/an | **15,5 %** |
| … plus de 50 %/an | 6,1 % |
| … plus de 100 %/an | 2,6 % |
| Lignes où le short reçoit plus de 10 %/an | 52,1 % |
| Financement total des shorts, par année (2021 à 2025) | +12,2, −0,6, +3,7, +7,6, **−6,1** points |
| Part des lignes payant plus de 10 %/an, par année | 11,8 %, 20,4 %, 9,3 %, 9,4 %, **35,6 %** |
| Financement médian reçu, par âge (7-13, 14-27, 28-60 j) | +10,9 %, +10,9 %, +9,9 %/an |
| Taux de stop si le short paie plus de 50 %/an, sinon | 23,9 %, 19,5 % |
| Financement de la couverture BTC sur 238 semaines | −22,2 points |

**Les cas de financement négatif extrême** (le short paie) : MYX (semaine du 30/06/2025) −940 %/an ; KAITO (03/03/2025) −516 %/an ; 1000SHIB (17/05/2021) −427 %/an ; ROSE (10/01/2022, stoppé) −286 %/an ; AEVO trois fois en 2024 (de −200 à −237 %/an).

**Lecture :**

1. **En moyenne, le financement est un revenu du short** (+16,8 points sur la période). Les acheteurs de jeunes cotations paient pour leur levier, ce qui est cohérent avec la thèse des optimistes à levier.
2. **Mais il y a de vraies hausses forcées par le financement négatif.** Un short sur sept paie plus de 10 %/an, un sur quarante plus de 100 %/an. Dans la plupart des cas extrêmes, le prix a quand même baissé (MYX −14 %, KAITO −31 %, SHIB −50 %) : **le marché paie pour vendre ce qui baisse**. C'est le signe d'un trade encombré, où les vendeurs à découvert sont plus nombreux que les acheteurs à levier.
3. **2025 marque la bascule.** La part des lignes où le short paie plus de 10 %/an triple (35,6 % contre environ 10 %), et le financement total devient négatif. **C'est le premier indice chiffré, dans les données, que le trade s'est fait connaître.** C'est aussi l'argument contraire n° 2 de l'audit (§ 1.3), désormais mesuré.
4. **Payer beaucoup de financement s'accompagne de plus de stops** (23,9 % contre 19,5 %). L'encombrement des vendeurs à découvert précède les hausses forcées, ce qui est cohérent avec le constat C8 (STRAT-05), mais l'effectif est faible (67 lignes).

### 4.2 Limites de position et de levier sur les jeunes contrats

**Ce que disent les annonces de Binance :**
- **Contrat de pré-marché (XPLUSDT, 22/08/2025) :**
  - levier maximal 5× ;
  - position maximale **200 000 USDT**, par paliers : 5× jusqu'à 5 000 USDT, puis 4×, 3×, 2×, et 1× entre 80 000 et 200 000 USDT ;
  - financement plafonné à 0,005 % par intervalle en pré-marché, puis à ±2,00 % par intervalle de **4 heures** ;
  - prix de marque lissé et variation plafonnée à ±0,5 % par seconde ;
  - « Binance may adjust the specifications… from time to time ».
- **Révision des paliers de AERGO et ALPACA (05/03/2025, effet une heure après l'annonce, positions existantes comprises) :**
  - le levier maximal de AERGO passe de 75× à 10× ;
  - la position maximale passe de 2 M à **700 000 USDT**.

**Conséquences pour STRAT-06 :**

| Effet | Ordre de grandeur | Conséquence |
|---|---|---|
| Plafond par compte et par nom | 200 000 USDT (pré-marché) à quelques millions (contrats établis) [variable par contrat, à lire dans les paliers de levier et de marge] | Au dimensionnement conforme (≈ 0,4 % du capital par ligne), le plafond ne lie qu'au-delà de 50 M$ de capital. Non contraignant pour le système |
| Révision des paliers en cours de semaine, une heure après l'annonce | Réduction forcée possible d'une position existante | Risque de sortie forcée hors règle, non modélisé |
| Financement versé toutes les 4 heures, plafonné à ±2 % par intervalle | Jusqu'à ±12 % par jour en théorie | Explique les queues de −940 %/an observées. Le moteur utilise le financement réel des archives, mais le paramètre peut changer |
| Prix de marque lissé en pré-marché | Le stop sur le prix de marque peut se déclencher en retard sur le dernier prix | Glissement au stop plus grand que le modèle (audit, CS3) |
| Bandes de prix maximales propres à chaque contrat | Des ordres hors bande sont refusés | Un stop au marché peut être partiellement rejeté pendant une forte hausse [à vérifier] |

Les limites de Bybit et d'OKX, plateformes d'exécution envisagées, ne sont pas étudiées ici [à faire avant tout pilote, condition CP5 de l'audit].

---

## 5. Corrélation et risque de queue

### 5.1 Le portefeuille de six shorts : diversifié ou facteur unique ?

Mesures sur les 1 104 rendements hebdomadaires non tronqués de E11, avec la même sélection que la base :

| Mesure | Valeur |
|---|---:|
| Corrélation moyenne entre deux noms de la même semaine | **0,28** |
| Nombre effectif de noms indépendants pour 6 noms | **2,5** |
| Corrélation résiduelle après le facteur « panier d'alts anciennes » | 0,15 |
| Bêta d'un nom vendu sur BTC ; sur le panier d'alts | 1,46 ; 1,03 |
| Part de la variance d'un nom expliquée par le panier d'alts | 16 % |
| Écart-type hebdomadaire d'un nom | 31 % |

| Sous-ensemble de semaines | Semaines | Part des noms en hausse | Rendement moyen d'un nom |
|---|---:|---:|---:|
| Toutes | 226 | 38 % | −0,7 % |
| 10 % pires semaines de la stratégie | 23 | **79 %** | **+23,8 %** |
| 10 % meilleures semaines | 23 | 10 % | −21,4 % |
| Panier d'alts en hausse de plus de 10 % | 48 | 67 % | +11,0 % |
| Panier d'alts en baisse de plus de 10 % | 36 | 6 % | −24,2 % |

**Les stops se regroupent :**
- 27 semaines comptent au moins 3 stops, et regroupent 97 des 218 stops (44 %) ;
- 34 % des stops tombent dans les 10 % pires semaines ;
- record : 6 stops sur 6 noms la semaine du 04/11/2024 (élection américaine, envolée des memecoins, MOODENG).

**Lecture :**

1. **Le portefeuille n'est pas diversifié au sens où il paraît.** Avec ρ = 0,28, six noms valent 2,5 noms indépendants. La corrélation résiduelle (0,15) montre qu'il existe un **facteur propre aux jeunes cotations**, au-delà du facteur des grandes alts.
2. **Dans les semaines de crise, presque tous les noms montent ensemble.** C'est un risque de facteur, pas un accident sur un nom. La couverture BTC ne le neutralise pas : bêta de 1,46 sur BTC, mais exposition au facteur alts moins BTC inchangée (C16).
3. **Symétriquement, les meilleures semaines sont des krachs communs**, où 90 % des noms baissent. La stratégie est, au premier ordre, **un short du facteur « jeunes cotations » contre BTC**, avec un bonus idiosyncratique de dégonflement.
4. **Conséquence pour le risque :** le drawdown est gouverné par la fréquence des semaines de hausse commune, pas par le nombre de noms. E08, à 10 noms, n'a pas gagné en efficacité (audit, § 4.1).

### 5.2 La queue droite : les hausses de +50 % et +100 %

Sur les rendements hebdomadaires non tronqués (E11) :

| Mesure | Valeur |
|---|---:|
| Asymétrie ; aplatissement (excès) | **+4,87 ; 45,6** |
| Quantiles 1 %, 5 %, 25 %, 50 %, 75 %, 95 %, 99 % | −47 %, −35 %, −16 %, **−4,5 %**, +7 %, +40 %, **+102 %** |
| Part des lignes en baisse | 61,5 % |
| Lignes ≥ +30 % (déclencheraient le stop) | 89 (8,1 %), 68 noms |
| Lignes ≥ +50 % | 43 (3,9 %), 37 noms, âge médian 23 j |
| Lignes ≥ +100 % | 12 (1,1 %), 12 noms, âge médian 35 j |
| Perte sans stop des lignes ≥ +30 %, et gain des lignes ≤ −30 % | −509 points, +279 points |
| Années des lignes ≥ +50 % (2021 à 2025) | 9, 5, 11, 15, 3 |
| Classe des lignes ≥ +50 % | 30 récents, 8 sans comptant, 5 anciens |
| Semaine suivant une hausse de +50 % : moyenne, médiane, part en baisse | −3,7 %, −10,3 %, 68 % (37 cas) |

Les 15 plus fortes hausses hebdomadaires d'un nom vendu : CHZ +385 % (03/2021, 46 j) ; NOT +344 % (05/2024, 11 j) ; GALA +304 % (11/2021, 58 j) ; GMT +215 % (03/2022, 13 j) ; MOODENG +175 % (11/2024, 10 j) ; CFX +134 % (03/2023) ; BB +133 % (05/2024, 7 j) ; FARTCOIN +133 % (01/2025) ; GRT +129 % (02/2021) ; BIGTIME +114 % (11/2023) ; NEIRO +104 % ; TURBO +102 % ; PEOPLE +99 % ; LUNA +98 % (03/2021) ; ID +96 % (04/2023).

**Lecture :**

1. **La distribution est celle d'une loterie inversée.** Le nom typique baisse (médiane −4,5 % par semaine, 61,5 % des lignes en baisse). Mais un nom sur cent fait plus que doubler en une semaine. Sans stop, la queue droite (−509 points) efface presque deux fois la queue gauche (+279 points). C'est C15 vu par la distribution.
2. **Les hausses extrêmes touchent des cotations récentes**, d'un âge médian de 23 jours. Elles portent sur des récits du moment : jeux et métavers en 2021 (CHZ, GALA), jetons « move-to-earn » (GMT), memecoins et TON en 2024 (NOT, MOODENG, NEIRO, TURBO). 2025 en compte peu (3) : la vague des jetons neufs à faible flottant a surtout baissé.
3. **Après une hausse de +50 %, le prix revient plus souvent qu'il ne poursuit** : médiane −10,3 % la semaine suivante, 68 % de baisses. La réentrée du lundi suivant (règle H4) récupère donc une partie de la perte du stop. C'est cohérent avec le gain moyen intact des lignes qui suivent un stop (§ 2.2).
4. **La queue droite n'est pas prévisible** par l'âge (médiane proche de l'ensemble) ni par la volatilité passée du nom (les 20 pires pertes ne sont pas plus volatiles que la moyenne). Le stop reste la seule défense du jeu de règles.

---

## 6. Synthèse et programme de recherche

### 6.1 Ce qui est établi par les données du dépôt (en échantillon, contaminé)

1. Une prime de risque de queue existe sur la vente des jeunes perpétuels : asymétrie de +4,9, aplatissement de 46, rôle constitutif du stop.
2. Un facteur commun propre aux jeunes cotations gouverne le résultat (ρ = 0,28, corrélation résiduelle 0,15). La couverture BTC ne le neutralise pas.
3. Le résultat se concentre sur une trentaine de noms et une vingtaine de semaines de krach.
4. Le financement, revenu en moyenne, se retourne en 2025 : premier indice chiffré d'encombrement.
5. Les stops sont diffus dans la semaine et se regroupent sur la séance asiatique et sur les heures de versement du financement.

### 6.2 Ce qui reste plausible mais non démontré

1. La levée de la contrainte de vente à découvert (Miller) comme moteur de 2021-2024.
2. L'offre en surplomb des jetons à faible flottant et la vente des largages comme moteur de 2024-2025.
3. Le rôle des tranches d'acquisition, peu probable dans la fenêtre de 7 à 60 jours.

### 6.3 Hypothèses nouvelles, à passer au tri T1 à T10 avant toute fiche

| N° | Hypothèse | Donnée requise | Risque T4 |
|---|---|---|---|
| H14 (renforcée) | Dynamique de prix autour des heures de versement du financement (00, 08, 16 UTC), indiquée par la concentration des stops | Archives horaires déjà en cache | Faible |
| H26 | Témoin « short de petites alts spéculatives couvert » : contrôle de taille et d'illiquidité | Archives déjà en cache | Faible |
| H27 | Couverture moins chère que le perpétuel BTC (comptant, ou panier d'alts) | Archives au comptant | Moyen |
| H28 | Dérive selon le rapport capitalisation / valorisation diluée et selon les calendriers de déblocage | Offre en circulation datée, calendriers datés sans biais du survivant | **Élevé** |
| H29 | Encombrement comme filtre : le financement payé par les shorts précède les hausses forcées | Archives de financement déjà en cache | Faible. Attention : voisin de STRAT-05, rejetée (T9) |
| H30 | Disponibilité de l'emprunt sur marge avant le perpétuel : test direct de Miller | Historique de l'emprunt sur marge de Binance | **Élevé** (constat de H11 : API limitée à 90 jours) |

### 6.4 Conséquences pour STRAT-06

**Aucune modification des règles figées.** Ces lectures s'ajoutent au dossier d'audit comme éléments adverses ou explicatifs :
- facteur commun et nombre effectif de 2,5 noms (§ 5.1) ;
- retournement du financement en 2025 (§ 4.1) ;
- révisions de paliers en cours de semaine (§ 4.2).

Elles renforcent l'intérêt des lectures descriptives du hors échantillon fixées au § 19 de la fiche. **À ajouter avant E19**, par décision écrite et à titre descriptif : la part des lignes où le short paie plus de 10 %/an, comme mesure de l'encombrement.

---

## 7. Reproductibilité

```
cd systeme-trading/recherche/analyses
python3 -B autopsie_strat06.py   # écrit sorties_strat06/autopsie_strat06.json et les CSV
```

Les chiffres complémentaires de cette note ont été calculés le 05/11/2026 sur les mêmes fichiers :
- sous-ensembles de semaines du § 5.1 ;
- répartition horaire du § 2.1 ;
- réentrées du § 2.2 ;
- concentration du § 2.4.

---

## Références

**Données du dépôt :** `strategies/STRAT-20261102-06/resultats/` (CDV, E11, DIAG), commit 59e9c2e. `revues/AUDIT_STRAT-06.md`. Constats C8 et C11 à C17 (`commun-trading` § 9).

**Rapports et annonces :**
- Binance Research, « How Did We Get to Low Circulation / High FDV Tokens? », mai 2024, repris par [Crypto Briefing](https://cryptobriefing.com/binance-research-token-unlocks-2030), [Cointelegraph](https://cointelegraph.com/news/binance-urges-small-medium-projects-high-fdv-trend), [Forklog](https://forklog.com/en/binance-highlights-155-billion-token-unlock-overhang/) (lus le 05/11/2026).
- Keyrock, [« From Locked to Liquidity: What 16,000+ Token Unlocks Teach Us »](https://keyrock.com/from-locked-to-liquidity-what-16000-token-unlocks-teach-us/), 12/2024, mis à jour en 07/2025 (lu le 05/11/2026).
- Keyrock, étude de 62 largages de 2024, repris par [BeInCrypto](https://beincrypto.com/majority-airdrop-tokens-crash-within-15-days/) (lu le 05/11/2026).
- Binance, [annonce du perpétuel de pré-marché XPLUSDT](https://www.binance.com/en-AE/support/announcement/detail/6fe1579c40694f7badfd0d2e149bb43a), 22/08/2025 ; [révision des paliers de levier et de marge de AERGO et ALPACA](https://www.binance.com/en/support/announcement/cec59c7ce78340c4b00d21d1989de220), 05/03/2025 (lues le 05/11/2026).

**Articles académiques** (cités de mémoire, à vérifier avant toute publication externe) :
- Miller, E. (1977). Risk, Uncertainty, and Divergence of Opinion. *Journal of Finance*, 32(4).
- Harrison, J. M., et Kreps, D. (1978). Speculative Investor Behavior in a Stock Market with Heterogeneous Expectations. *Quarterly Journal of Economics*, 92(2).
- Ritter, J. (1991). The Long-Run Performance of Initial Public Offerings. *Journal of Finance*, 46(1).
- Scheinkman, J., et Xiong, W. (2003). Overconfidence and Speculative Bubbles. *Journal of Political Economy*, 111(6).
- Fostel, A., et Geanakoplos, J. (2012). Tranching, CDS, and Asset Prices: How Financial Innovation Can Cause Bubbles and Crashes. *American Economic Journal: Macroeconomics*, 4(1).
