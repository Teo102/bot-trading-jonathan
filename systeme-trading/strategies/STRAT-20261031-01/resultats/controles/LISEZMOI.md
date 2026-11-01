# Contrôles des contradicteurs de STRAT-20261031-01

Ces scripts viennent du scratchpad de la session du 31/10 au 01/11/2026 et auraient disparu avec elle. Ils lisent les exports et les données tronquées sans rien modifier dans le dossier de la stratégie. Aucun n'est un candidat et aucun ne change de paramètre.

Trois retouches seulement ont été faites à la copie. Les chemins absolus sont remplacés par des chemins relatifs au fichier. Les pickles deviennent des CSV dans `sorties/`. `t5` et `t12` écrivent en plus un résumé JSON et `verif1` lit la colonne `sharpe_realise`. Les scripts `t1` à `t12` portent un nom lisible et gardent leur numéro d'origine.

Commande de rejeu, depuis ce dossier, `./rejouer_controles.sh verif1.py t3_rejeu_portefeuille.py`. Chaque sortie va dans `sorties/` avec ses horodatages UTC.

| Script | Objet | Rejeu du 01/11/2026 |
|---|---|---|
| `verif1.py` | Recalcul indépendant des métriques et du DSR depuis les .zip | oui, relancé après mise à jour du registre |
| `verif2.py` | Base réévaluée, DSR sous variantes, V tranchée, IC corrélés, semestres | oui |
| `verif3.py` | Bruit de graine de l'IC iid, force_exit | oui |
| `common.py`, `sim.py` | Données, indicateurs par boucles, rejeu de portefeuille | importés par les autres |
| `t1_trades_E01.py` | Signal, entrée, stop et sortie des 135 trades de E01 | oui |
| `t2_mises_financement_E01.py` | Mises, levier, financement et P&L recalculés | oui |
| `t3_rejeu_portefeuille.py` | Le rejeu retrouve les trades et les rejets des exports | oui |
| `t4_places_et_ordres.py` | Première version de t5, avec ordres inverse et alphabétique simulés | non, doublon lent de t5 |
| `t5_permutations_ordre_places_strictes.py` | 200 ordres de whitelist, graine 0, et règle stricte des places | oui, identique |
| `t6_signaux_troncature.py` | Signaux et indicateurs sur les 10 paires, troncature | oui |
| `t7_glissement_financement_mark1h.py` | Borne sur le mark 1h, écarts de financement | oui |
| `t8_gaps_verrou_qualite.py` | Gaps, sha des données, qualité 1d, volumes locaux de décembre 2020 | oui |
| `t9_stop_papier_estimation.py` | Effet estimé du stop en papier | oui |
| `t10_stop_papier_methode.py` | Appel de la vraie méthode `_atr_at_entry` avec un faux dataprovider | oui |
| `t11_rangs_volume_dec2020.py` | Rangs de volume de décembre 2020, API publique Binance | non, appel réseau exclu de cette reprise |
| `t12_retrait_doge_trx.py` | Retrait de DOGE et de TRX en simulation | oui |
| `ic_sensibilite.py` | Ajout de la reprise. Longueur des blocs, repli circulaire, bruit de graine | oui |
| `avenant_reperes.py` | Ajout de la reprise. Repères de l'avenant, sans donnée du hors échantillon | oui |
| `Inst_strategie_instrumentee.py` | Stratégie journalisée du contradicteur (appels de mise et de stop) | non, backtest |

Le dossier `sorties_contradicteur/` garde les 7 journaux freqtrade du contradicteur et leurs configurations, soit les ordres inverse et alphabétique sur 3 périodes et le run instrumenté, du 2026-10-31 entre 23:49Z et 23:52Z. Les journaux sont en heure locale et leurs chemins locaux sont remplacés par des repères entre chevrons. Ces backtests n'ont pas été relancés. `verif.py` du scratchpad concerne STRAT-20261031-02 et reste hors de ce dossier.
