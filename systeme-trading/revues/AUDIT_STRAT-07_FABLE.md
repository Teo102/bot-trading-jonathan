# Audit adverse avant gel — STRAT-20261109-07 (portage de financement conditionnel aux pointes)

Rédigé le 09/11/2026 par Claude Fable 5.2, dans le rôle d'auditeur adverse de la mission du même jour. Heures en UTC. Résultat de recherche. Aucun ordre, aucune clé, `dry_run` permanent. **Aucune règle ni aucun paramètre n'a été modifié. Le statut de la stratégie ne change pas.**

Pièces auditées (commit `57dcd3c`) : `strategies/STRAT-20261109-07/FICHE_STRAT-20261109-07.md`, `recherche/TRI_STRAT-07_STRAT-08.md`, `recherche/criblage_strat07/` (règle, script, tests, résultats du 09/11/2026 11:11 UTC) et les trois fichiers d'épisodes restés sur le serveur (`episodes_entree_*.csv`, sommes SHA-256 au § Sources). Le moteur `moteur_portage.py` n'existe pas encore.

**Données lues par l'audit : seulement les épisodes déjà lus par le criblage** (financement moins coûts, 2021 au 28/07/2025), et des listes d'archives. Aucune donnée nouvelle de rendement, aucun prix, rien du hors échantillon. Les recalculs ci-dessous ne choisissent aucune règle. Ils qualifient un chiffre déjà publié et sont rendus quels qu'ils soient. Je les place hors N ; si Jonathan et Téo préfèrent les compter, N passe de 19 à 21.

## 0. Synthèse

| Classe | Nombre | Constats |
|---|---:|---|
| Bloquant, à trancher avant le gel | 1 | B1 le criblage ne passe sa règle que grâce à 2021 ; sur le bloc de validation il est sous le seuil que la fiche impose |
| Majeur | 6 | M1 portes écrites après lecture ; M2 ordre des emplacements ; M3 taux court constant ; M4 le Sharpe ne teste pas un portage ; M5 nombre réel d'essais ; M6 épisodes sans paire au comptant (46 % du gain de la validation) |
| Mineur | 5 | m1 à m5 |
| Conforme | 4 | règle écrite avant calcul, reproduction exacte, épisodes sans anticipation, contamination déclarée |

**Verdict de la lecture adverse : affaiblie, proche du rejet.** Sur 2022 à juillet 2025, le portage par pointes rapporte 2,90 % par an sur le capital. H10 a été écartée le 02/11/2026 à environ 2,5 %. La différence avec H10 tient presque entièrement à l'année 2021.

## 1. Constat bloquant

### B1. Hors 2021, le criblage redonne le chiffre de H10, et le bloc de validation est sous le seuil de la fiche

**Reproduction d'abord** (`python3 -B b2_blocs_strat07.py <épisodes>`, 09/11/2026 20:46 UTC). Le portefeuille du criblage est refait avec la même logique et le même tri.

```
entree_50_sortie_10 épisodes pris 233 rendement reproduit 6.8898%
   developpement (2021-2023)          épisodes pris  149   +25.85% du capital   +8.62%/an
   validation (2024 au 27/07/2025)    épisodes pris   84   +5.64% du capital   +3.59%/an
   2021                               épisodes pris   83   +21.11% du capital   +21.13%/an
   2022                               épisodes pris   10   -0.20% du capital   -0.20%/an
   2023                               épisodes pris   56   +4.94% du capital   +4.94%/an
   2024                               épisodes pris   58   +5.05% du capital   +5.04%/an
   2025 (au 27/07)                    épisodes pris   26   +0.59% du capital   +1.04%/an
   2022 au 27/07/2025                 épisodes pris  150   +10.37% du capital   +2.90%/an
```

Le chiffre publié (233 épisodes, +6,89 %/an) est retrouvé à l'identique. Les épisodes sont rattachés au bloc de leur début.

**Lecture.**
1. La règle du criblage (rendement indicatif > 3,875 %/an) est remplie sur l'ensemble 2021 à 07/2025. Elle ne l'est sur aucune période qui exclut 2021 : 2,90 %/an de 2022 à 07/2025.
2. La fiche (§ 7) exige un rendement supérieur à 3,875 % **sur E01 et sur E02**. Avec les chiffres du criblage, E02 (validation) donne 3,59 %. La porte serait échouée de 0,29 point, sauf si la base comptant / perpétuel, non mesurée, apporte la différence. Et ce chiffre est lui-même gonflé : 46 % du gain de ce bloc vient d'épisodes sans paire au comptant (M6).
3. Avec l'entrée à 30 %, la validation donne 2,90 %/an et 2022 à 07/2025 donne 2,40 %/an.
4. 2021 porte 67 % du gain des épisodes pris (21,11 points de capital sur 31,49). Les 8 plus gros épisodes commencent tous en janvier 2021 et durent 81 à 137 jours.

**Pourquoi c'est bloquant.** Le tri (T9, T10) demandait que STRAT-07 « diffère réellement » de H10 et ne dépende pas d'un seul régime. Le criblage a répondu sur une moyenne. Par bloc, la réponse est non. Geler puis lancer E01 et E02 en l'état, c'est très probablement consommer deux essais pour retrouver ce résultat. La décision de continuer appartient à Jonathan et Téo ; elle devrait se prendre avec ce tableau.

**Ce qui lèverait le constat** : une décision écrite, avant le gel, sur l'une de ces voies. (a) Écarter comme H10. (b) Continuer en sachant que tout repose sur la base, et écrire avant E01 le gain de base minimal attendu (environ 0,3 point par an sur E02). (c) Reformuler, ce qui est une nouvelle hypothèse et une nouvelle ligne au registre.

## 2. Constats majeurs

### M1. Deux portes de la fiche ont été écrites après lecture des résultats

- **Porte des années** (« au moins 3 années civiles sur 4 positives, 2021 à 2024 »). Le fichier de résultats du criblage donne déjà, pour 50 / 10, le net par année : 2021 +28,7, 2022 −0,04, 2023 +7,4, 2024 +9,1 (`criblage_20261109T111132Z.json`, champ `par_annee`). Trois années sur quatre étaient donc connues positives avant d'écrire le seuil. Sur le financement, cette porte ne teste rien.
- **Porte des voisins.** Les voisins de sortie sont 5 % et 15 % (E05, E06). La sortie à 20 %, lue négative au criblage (−2,66 %/an), n'est pas dans la grille des voisins. Elle est comptée dans N, pas dans la porte « 6 sur 8 rentables ».

La fiche déclare la contamination du financement (§ 0). Elle ne dit pas que ces deux portes en héritent.

### M2. Le « premier arrivé, premier servi » dépend de l'ordre des symboles

**Fait** (`python3 -B b1_ordre_emplacements_strat07.py <épisodes>`, 20:46 UTC).

```
"episodes": 1371, "part_debuts_simultanes": 0.726,
"ordre_alphabetique": 0.0668, "ordre_alphabetique_inverse": 0.0678,
"aleatoire_2000_tirages": {"min": 0.0658, "q05": 0.0666, "mediane": 0.0679, "q95": 0.069, "max": 0.07, "part_sous_le_taux_court": 0.0}
```

- 73 % des épisodes commencent au même instant qu'un autre, parce que les versements tombent aux mêmes heures.
- 1 138 épisodes sur 1 371 sont refusés faute d'emplacement (83 %). Le choix des 233 retenus dépend donc du départage.
- Le criblage départage par le tri par défaut de pandas, qui n'est pas stable. Son chiffre (6,89 %) n'est ni l'ordre alphabétique (6,68 %) ni l'ordre inverse (6,78 %). Il se situe vers le 94e centile de 2 000 ordres tirés au hasard.
- L'effet est petit : de 6,58 à 7,00 %, jamais sous le taux court. Le constat ne change pas la conclusion du criblage. Il montre un paramètre caché, du type de l'ordre de la whitelist de STRAT-01, que la fiche (§ 3) reprend sans règle de départage.

**Ce qui lèverait le constat** : une règle écrite (par exemple le financement le plus élevé d'abord, connu à l'instant de la décision), un tri stable, et un test de permutation.

### M3. Le taux court de référence est constant et daté

La porte d'excès compare tous les blocs à 3,875 %, taux de fin 2026. Le rendement des bons du Trésor à 3 mois était proche de 0 % en 2021 et d'environ 5 % en 2023 et 2024 [de mémoire, non vérifié ici]. Avec les taux de l'époque, 2023 (+4,94 %) et 2024 (+5,04 %) ne battent pas la trésorerie, et seule 2021 la bat. La porte est trop sévère sur 2021 et trop douce sur 2023 à 2025. Un taux daté par période serait à écrire avant le gel.

### M4. Le seuil de Sharpe ne teste pas un portage

Sur les 1 371 épisodes, 270 perdent, pour −1,00 au total contre +46,35 de gains, et la pire perte est de −2,56 % (`episodes_entree_50_sortie_10.csv`). La série n'a presque pas de variance, donc son Sharpe sera très élevé par construction. Le seuil de 1,70 sera franchi sans rien prouver. Le risque réel d'un portage (défaut de plateforme, déleveraging automatique, écart de base à la sortie forcée, retrait du comptant) n'est pas dans l'échantillon. Les portes qui comptent sont l'excès sur le taux court et la borne basse de l'intervalle, pas le Sharpe.

### M5. Le nombre réel d'essais sur cette idée dépasse 19

C'est la troisième lecture du portage de financement sur les mêmes données : H02 (rejetée le 01/11/2026), H10 (écartée le 02/11/2026), puis ce criblage à trois grilles, dont la règle acceptait deux grilles sur trois (30 / 10 **ou** 50 / 10). N = 19 compte le criblage. Il ne compte ni H02 ni H10. Le dossier de promotion devrait publier le total de la famille.

### M6. Près de la moitié du gain de la validation vient d'épisodes sans paire au comptant

**Fait** (`python3 -B b3_comptant_et_verrou_strat07.py <épisodes>`, lancé depuis le serveur, 21:13 UTC). Le criblage vérifie le mois de première cotation au comptant, pas l'existence de la paire pendant l'épisode. Huit épisodes sur 1 371 courent sur des mois où la paire au comptant n'a plus d'archive.

```
BNXUSDT    2025-03-14 → 2025-06-19   net 0.0728   pris
BONDUSDT   2024-07-15 → 2024-09-21   net 0.0462   pris
DARUSDT    2024-12-25 → 2025-06-19   net 0.0477   pris
FTMUSDT    2025-01-04 → 2025-06-19   net 0.0505   pris
MATICUSDT  2024-09-03 → 2025-07-28   net 0.0994   pris   (comptant listé jusqu'en 2024-09)
REEFUSDT   2024-10-16 → 2024-12-11   net 0.1198   pris
UNFIUSDT   2024-10-30 → 2025-06-19   net 0.0655   pris
XMRUSDT    2025-05-28 → 2025-07-24   net 0.0225   pris   (comptant listé jusqu'en 2024-02)
validation : net pris 0.0564 dont épisodes sans comptant 0.0262 | rendement annualisé sans eux 0.0192
```

- Les huit sont retenus par le portefeuille du criblage. Ils pèsent 2,62 points sur les 5,64 du bloc de validation, soit 46 %.
- Sans eux, la validation tombe à 1,92 %/an (sans réattribuer les places qu'ils libèrent : c'est un ordre de grandeur, pas un recalcul).
- Ces noms correspondent à des retraits ou à des migrations de jetons (MATIC, FTM, DAR, BNX) [de mémoire]. Quatre épisodes s'arrêtent le même jour, le 19/06/2025 à 08:00, et l'épisode MATIC dure 328 jours : cela ressemble à des lignes de financement qui continuent après la fin réelle du contrat. L'état du perpétuel lui-même sur ces périodes est [non vérifié].
- Sur le reste de l'historique, le contrôle ne trouve aucun autre cas.

Deux points voisins. Le filtre de liquidité porte sur le perpétuel seul (≥ 20 M USDT), sans condition sur le volume de la paire au comptant ; le glissement de 0,05 % par jambe y est [non mesuré]. Et le net moyen par épisode baisse : 4,65 % en 2021, 2,8 % en 2023, 2,0 % en 2024, 0,4 % en 2025 (27 épisodes en 7 mois). Le hors échantillon pourrait ne pas atteindre les 30 épisodes exigés ; le contrôle du § 6 de la fiche le dira, sans rendement.

## 3. Constats mineurs

| N° | Constat | Preuve |
|---|---|---|
| m1 | Le criblage a lu le versement du 28/07/2025 à 00:00 UTC, premier instant du bloc hors échantillon (borne à 02:00). Trois épisodes s'y terminent | `criblage_strat07.py` ligne 29 ; fin maximale des épisodes : 2025-07-28 00:00 |
| m2 | Le criblage et la fiche ne décrivent pas la même règle. Le criblage refuse pour toujours un épisode sans emplacement à son début. La fiche entrerait à un versement suivant, dès qu'une place se libère | `criblage_strat07.py` lignes 64 à 70 ; fiche § 3 |
| m3 | « À l'ouverture de l'heure qui suit l'observation » ne dit pas si le versement tombant à cette heure est encaissé. Pour un financement horaire, c'est un versement par épisode | Fiche § 3 |
| m4 | Changements de nom et migrations (MATIC, RNDR, FTM, EOS, MKR) : le comptant et le perpétuel ne basculent pas le même jour. Effet [non vérifié] | Leçon L9 |
| m5 | Le seuil de 1,70 applique un facteur de 64 semaines à un bloc de 65,7 semaines | Fiche § 5 |

Concentration, pour mémoire : les 10 plus gros épisodes font 7,8 % du net total (3,54 sur 45,35) ; les 5 premiers symboles font 28 % du gain des épisodes pris. Pas de dépendance à un seul nom.

## 4. Points conformes

- **Règle écrite avant le calcul.** La règle est dans le commit `9d6ca3d` (09/11/2026 07:51:30 UTC). Les résultats portent l'heure 11:11:32 UTC. Le serveur est resté sur ce commit.
- **Reproduction exacte** du chiffre publié (233 épisodes, 6,8898 %).
- **Épisodes sans anticipation** : entrée après le versement observé, encaissement à partir du suivant, sortie après le versement observé sous le seuil (`criblage_strat07.py`, lignes 44 à 61). Liquidité lue sur la veille (ligne 97).
- **Contamination déclarée** en tête de fiche, et sélection de 50 / 10 comptée dans N.

## 5. Liste de contrôle de la mission

| Point | Résultat |
|---|---|
| Information future | Aucune dans les épisodes. m1 : un versement du hors échantillon lu |
| Paramètres cachés | **M2** (ordre des symboles, tri non stable) |
| Univers choisi avec le recul | Non pour le perpétuel. Comptant : 8 épisodes sans paire pendant l'épisode, tous retenus (**M6**) |
| Coûts, glissement, financement | Comptant non filtré (M6). Base non mesurée. Trésorerie comparée à un taux constant (M3) |
| Concentration du gain | **B1** : 2021. Par nom : non concentré |
| Nombre réel d'essais | **M5** |
| Conformité du code à la fiche | m2, m3 (moteur non écrit) |

## 6. Lecture adverse (format `avocat-du-diable`)

**Trois arguments contraires, par poids.**
1. La condition de pointe ne crée pas d'excès hors de 2021 (B1). Elle sert de détecteur de marché haussier.
2. Le gain attendu, environ 3 points par an au mieux, est du même ordre que les éléments non mesurés : base, glissement au comptant, versement de l'heure d'entrée, risque de plateforme.
3. Les portes les plus visibles (années, Sharpe) passeront sans tester l'hypothèse (M1, M4).

**Scénario d'échec le plus plausible.** E01 passe grâce à 2021, E02 échoue la porte d'excès d'un quart de point. Deux essais consommés, verdict « rejetée ». Ordre de grandeur : [deux chances sur trois, jugement, non calculé ; dépend de la base].

**Biais probables.** Moyenne sur une période dominée par une année ; récit du « rendement sans risque de prix » ; lecture du Sharpe comme preuve.

**Données invalidantes.** Rendement de E02 inférieur à 3,875 % base comprise. Moins de 30 épisodes hors échantillon. Volume médian au comptant inférieur à quelques millions sur les noms retenus.

**Verdict : affaiblie, proche du rejet.**

## 7. Ce qui attend une décision de Jonathan et Téo

1. Continuer, écarter ou reformuler STRAT-07, au vu du tableau par bloc (B1).
2. Compter ou non les recalculs de cet audit dans N (19 ou 21).
3. Si la stratégie continue : règle de départage (M2), taux court par période (M3), portes réécrites en sachant ce que le criblage a montré (M1), contrôle du comptant (M6).

## Sources

| Pièce | Heure UTC (09/11/2026) |
|---|---|
| `recherche/criblage_strat07/criblage_20261109T111132Z.json` et `.md` | 11:11 |
| Épisodes sur le serveur, `/root/bot-trading-jonathan/systeme-trading/recherche/criblage_strat07/` : `episodes_entree_50_sortie_10.csv` (SHA-256 `8f6c090f…3966ee`), `episodes_entree_30_sortie_10.csv` (`b7bc2695…e46e39`), `episodes_entree_50_sortie_20.csv` (`dd7e987f…129e40`) | 11:11 |
| `revues/audit_fable/resultats/b1_ordre_emplacements_strat07_20261109T204601Z.json` | 20:46 |
| `revues/audit_fable/resultats/b2_blocs_strat07_20261109T204637Z.json` | 20:46 |
| `revues/audit_fable/resultats/b3_comptant_et_verrou_strat07_20261109T211309Z.json` | 21:13 |
| `recherche/PISTES_20261102.md` (H10) | 02/11/2026 |

Les trois fichiers d'épisodes ne sont pas dans le dépôt. Ils ont été copiés en lecture depuis le serveur pour l'audit, sans rien y modifier.
