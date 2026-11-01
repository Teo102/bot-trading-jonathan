"""Génère RAPPORT_E01_E09.md. Tous les chiffres des tableaux sont lus dans resultats/, aucun n'est saisi à la main."""
import json, sys, csv, hashlib, datetime as D
from pathlib import Path
import numpy as np, pandas as pd
base = Path(sys.argv[1]); res = base/"resultats"; sys.path.insert(0, str(base))
import analyse_strat as A
ORDER = ["E01","E02","E03","E04","E05","E06","E07","E08","E09","R01","R02","R03","E00-ref"]
M = {e: json.loads((res/f"{e}_metriques.json").read_text(encoding="utf-8")) for e in ORDER}
C = json.loads((res/"controles_complementaires.json").read_text(encoding="utf-8"))
S = {r["essai"]: r for r in json.loads((res/"sensibilite_dsr.json").read_text(encoding="utf-8"))}
SM = json.loads((res/"sensibilite_dsr_meta.json").read_text(encoding="utf-8"))
T5 = json.loads((res/"controles/sorties/t5_resume.json").read_text(encoding="utf-8"))
T12 = json.loads((res/"controles/sorties/t12_resume.json").read_text(encoding="utf-8"))
ICS = json.loads((res/"controles/sorties/ic_sensibilite.json").read_text(encoding="utf-8"))["essais"]
REG = {r["id_essai"]: r for r in csv.DictReader(open(base/"REGISTRE_ESSAIS.csv", encoding="utf-8"))}
def n(v, spec=".3f"):
    if v is None: return "n/c"
    return format(v, spec).replace(",", " ").replace(".", ",")
def pct(v, spec=".1f"): return "n/c" if v is None else n(100*v, spec) + " %"
def ic(b): return f"{n(b['bas'],'+.3f')} à {n(b['haut'],'+.3f')}"
def bl(e): return M[e]["intervalles_dependance"]["blocs"]
def mk(e): return M[e]["metriques_reevaluees"]
def dk(e): return M[e]["dsr_reevalue"]
sh = lambda f: hashlib.sha256((base/f).read_bytes()).hexdigest()
L = []
w = L.append
w("# Rapport des essais E01 à E09 de STRAT-20261031-01\n")
w(f"Résultats de recherche du 31/10/2026, repris le 01/11/2026 après deux relectures contradictoires. Aucune promesse de gain, aucune recommandation. Rapport généré le {D.datetime.now(D.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}.\n")
w("Le statut reste `backtest`. Le hors échantillon n'est pas ouvert. E10 et E11 n'ont pas été lancés. Ce rapport ne contient aucun verdict de rentabilité, car le critère porte sur le hors échantillon.\n")
w("## 1. État de la procédure\n")
w("La porte technique de E01 est franchie. L'exécution est correcte, le financement est appliqué et les deux contrôles de biais sont propres. La performance n'a joué aucun rôle dans cette porte. Ces contrôles couvrent les signaux et les indicateurs, pas l'attribution des places entre paires (§ 4).\n")
w("Tous les essais prévus ont tourné, soit E01 à E09, R01 à R03 et l'essai de référence E00-ref. Aucun hyperopt n'a été lancé. Les paramètres de base n'ont pas changé. La configuration a été acceptée telle quelle, donc `config_strat01_backtest.json` n'existe pas.\n")
w("Une anomalie majeure s'est produite au téléchargement. Elle a été corrigée avant tout backtest de ce `user_data` et le § 3 la détaille.\n")
w("Cette reprise n'a lancé aucun backtest ni téléchargement. Les chiffres viennent d'un rejeu de `analyse_strat.py` sur les exports .zip existants (`brut/rejeu_analyse.sh`, `brut/<id>_analyse_reevalue.txt`) et d'un rejeu des scripts locaux des contradicteurs (`controles/`). Les valeurs déjà publiées sur la base réalisée restent identiques. L'équité réévaluée chaque jour devient la référence de lecture pour le Sharpe et le Sortino, ainsi que pour le Calmar, le drawdown et le DSR. La base réalisée reste affichée et libellée en second. L'avenant à valider avant E10 est dans `AVENANT_AVANT_E10.md`. Il n'est pas appliqué.\n")
w("## 2. Tous les essais\n")
w("Source pour le tableau, exports freqtrade 2026.10 du 2026-10-31 (22:33:52Z à 22:44:55Z), analysés de nouveau le 01/11/2026 par `analyse_strat.py`, données publiques Binance. La base réalisée compte le P&L le jour de la clôture du trade. La base réévaluée ajoute chaque jour le latent au prix de clôture 1d, hors frais et financement latents. L'IC iid garde 5000 tirages et la graine 0 pour rester comparable. L'IC par blocs utilise des blocs circulaires de 10 trades, 50 000 tirages et la graine 20261101. Le DD95 par permutation mélange les trades et le DD95 par blocs tire des blocs de 30 jours de rendements réévalués.\n")
w("| Essai | Variante | Période | Frais | Trades | Espérance R | Hors force_exit | IC 90 % iid | IC 90 % blocs | DD réalisé | DD réévalué | DD95 permutation | DD95 blocs | Sharpe réalisé | Sharpe réévalué | Semestres + réalisés | DSR réévalué | DSR réalisé |")
w("|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for e in ORDER:
    m=M[e];t=m["trades"];q=m["metriques_quotidiennes"];s=m["semestres"];r=REG[e]
    w(f"| {e} | {r['variante']} | {r['timerange']} | {n(m['execution']['frais_par_cote'],'.4f')} | {t['trades']} | {n(t['esperance_R'],'+.3f')} | {n(t['esperance_hors_force_exit_R'],'+.3f')} | {n(t['ic90_bas'],'+.3f')} à {n(t['ic90_haut'],'+.3f')} | {ic(bl(e))} | {pct(q['dd_reel'])} | {pct(mk(e)['dd_reevalue'])} | {pct(t['dd_95'])} | {pct(m['monte_carlo_blocs']['dd_95'])} | {n(q['sharpe_annualise'],'.2f')} | {n(mk(e)['sharpe_annualise'],'.2f')} | {s['n_positifs']}/{s['n_semestres']} | {n(dk(e)['dsr'],'.3f')} | {n(m['dsr']['dsr'],'.3f')} |")
w("| E10 | base | 20250801-20261031 | 0,0005 | verrouillé | | | | | | | | | | | | | |")
w("| E11 | base | 20250801-20261031 | 0,0010 | verrouillé | | | | | | | | | | | | | |")
w("")
w("E00-ref n'était pas préenregistré. Il est consigné comme essai de calcul et le § 13 explique pourquoi. Il donne 178 trades contre 181 pour E01 et E02 pris ensemble, car E01 ferme de force ses positions le 30/06/2024 et E02 repart sans position.\n")
w("Le DSR réalisé n'est pas comparable d'un essai à l'autre. E07 et R01 ne passent 0,95 que sur la série réalisée et ce dépassement est un effet d'asymétrie, pas un résultat. Un seul jour de clôture y gonfle g3 et g4 puis écrase le dénominateur du PSR (§ 13). Aucune ligne n'atteint 0,95 en DSR réévalué.\n")
fx=[(e,M[e]['trades']['esperance_R']-M[e]['trades']['esperance_hors_force_exit_R'],M[e]['trades']['pnl_force_exit']/M[e]['par_sens']['total']['pnl']) for e in ("E02","E00-ref")]
w(f"Les sorties forcées de fin de fenêtre ferment une position à la borne de période et non par la règle de sortie. Sans elles, l'espérance baisse de {n(fx[0][1],'.3f')} R sur E02 et de {n(fx[1][1],'.3f')} R sur E00-ref. Elles portent {pct(fx[0][2],'.0f')} du P&L de E02 et {pct(fx[1][2],'.0f')} de celui de E00-ref. Le même chiffre sera donné pour E10 dans le rapport de verdict.\n")
w("## 3. Données et verrou\n")
w("Source, `freqtrade download-data` et `list-data`, 2026-10-31 entre 22:30:15Z et 22:33:28Z. Sorties brutes dans `brut/01_download-data.txt`, `brut/02_list-data.txt`, `brut/03_troncature_verrou.csv` et `brut/04_list-data_apres_troncature.txt`.\n")
w("La commande demandait `--timerange 20200501-20250801`. Freqtrade a pourtant écrit des pages complètes au-delà de cette fin. Les bougies 1d allaient jusqu'au 16/10/2025 (25/12/2025 pour DOGE). Le mark 1h allait jusqu'au 16/08/2025 (03/08/2025 pour DOGE). Le financement allait jusqu'au 28/06/2026. La borne de fin de `--timerange` ne suffit donc pas comme verrou physique avec cette version.\n")
w("Toutes les lignes datées à partir du 01/08/2025 00:00 UTC ont été supprimées à 22:33:27Z, soit avant le premier backtest de ce `user_data` (22:33:52Z). Six backtests de contrôle de format avaient déjà tourné entre 22:18:20Z et 22:29:11Z dans un dossier séparé, sur 3 paires et avec des données finissant au plus le 22/11/2023 (§ 16). Ces données sont restées sur le disque 3 min 12 s. Seules des dates et des nombres de lignes ont été affichés. Aucun prix ni taux de cette période n'a été affiché ou utilisé. Le script de troncature les a chargés en mémoire sans les afficher. La dernière clôture de tous les exports est au plus le 31/07/2025.\n")
w("| Paires | Début 1d | Début mark | Début financement | Fin 1d | Fin mark | Fin financement | Lignes 1d / mark / financement |")
w("|---|---|---|---|---|---|---|---|")
w("| BTC, ETH, XRP, LTC, BCH, LINK, ADA, BNB, TRX (chacune) | 01/05/2020 | 01/05/2020 | 01/05/2020 | 31/07/2025 | 31/07/2025 23h | 31/07/2025 16h | 1918 / 46032 / 5754 |")
w("| DOGE | 10/07/2020 | 10/07/2020 03h | 10/07/2020 08h | 31/07/2025 | 31/07/2025 23h | 31/07/2025 16h | 1848 / 44349 / 5543 |")
w("")
w("Les séries sont complètes pour les neuf premières paires (24 lignes de mark et 3 de financement par jour). Le financement et le mark sont présents pour les 10 paires.\n")
w("Effet sur la chauffe de 220 jours. Pour E01, freqtrade charge à partir du 26/05/2020 et la chauffe est donc complète pour neuf paires au 01/01/2021. DOGE commence plus tard. Sa moyenne 200 jours existe à partir du 25/01/2021. D'après le code de `trim_dataframe`, freqtrade retire 220 bougies depuis le début de la paire et DOGE ne devient donc négociable que vers le 15/02/2021 [déduit du code, non observé directement]. Sa première entrée, tous essais confondus, date du 04/05/2021. E01 démarre donc à neuf paires pendant environ 45 jours.\n")
w("## 4. Contrôles de biais\n")
w("Source, `brut/E01_lookahead-analysis.txt`, `brut/E01_lookahead-analysis_elargi.txt` et `brut/E01_recursive-analysis.txt`, 2026-10-31 entre 22:34:30Z et 22:40:56Z, période 20210101-20240630.\n")
w("| Contrôle | Options | Résultat |")
w("|---|---|---|")
w("| lookahead-analysis | défaut (20 signaux visés) | has_bias No, 20 signaux, 0 entrée biaisée, 0 sortie biaisée |")
w("| lookahead-analysis élargi | `--minimum-trade-amount 50 --targeted-trade-amount 300` | has_bias No, 271 signaux, 0 entrée biaisée, 0 sortie biaisée, 6 sorties forcées écartées par l'outil |")
w("| recursive-analysis | sans `--fee`, refusé par la commande | atr 0,000 % pour 199 et 220 bougies, -0,000 % pour 399, aucun écart à 499 et au-delà, « No lookahead bias on indicators found » |")
w("")
w("Ces deux outils ne testent pas les rappels `custom_stake_amount` et `custom_stoploss`, et recursive-analysis ne regarde que BTC. Un contrôle indépendant a donc été ajouté (`brut/controles_complementaires.txt`, 22:49 UTC environ). Sur E00-ref, la mise rapportée à la cible calculée avec l'ATR de la veille est stable sur les paires à petit prix, médiane 0,990, p5 0,988 et p95 0,990. Le 0,99 est `tradable_balance_ratio`. Avec l'ATR du jour, le même rapport va de 0,957 à 1,157. La mise n'utilise donc pas la bougie en cours. La distance de stop vaut entre 0,998 et 1,000 fois 2 ATR de la veille sur les 178 trades.\n")
w("Le contrôle a été étendu aux 10 paires le 01/11/2026 (`controles/sorties/t6_signaux_troncature.txt`). Le code de la stratégie et un recalcul indépendant donnent 0 écart de signal. Une troncature à 250 dates aléatoires par paire donne 0 écart sur 1500 comparaisons par paire. Les indicateurs restent donc propres hors BTC.\n")
w("Ces outils ont trois limites. Le décompte du lancement élargi n'est pas fermé, car 271 signaux testés et 6 sorties forcées écartées laissent 1 cas sur 278 [non élucidé]. L'outil force `max_open_trades` à -1 et valide donc les signaux et les indicateurs, pas l'attribution des places. `recursive-analysis` ne contrôle l'absence de biais d'indicateur qu'à une date (2021-01-11).\n")
a0,a1,a2=T5["E01"],T5["E02"],T5["E00"]
w(f"L'attribution des places contient une anticipation que `lookahead-analysis` ne teste pas. Freqtrade traite d'abord les paires déjà en position dans la bougie. Un stop touché dans la journée libère donc sa place avant les entrées, et une position s'ouvre à l'ouverture du jour avec une place qui n'était pas libre à cette heure. L'équité servant à la mise inclut aussi cette perte future, avec une mise jusqu'à 1,054 fois la cible calculée sur l'équité de la veille (`t2_mises_financement_E01.txt`). Le rejeu indépendant retrouve 178 trades sur 178 et compte {a0['entrees_place_liberee']} entrées de ce type sur E01, {a1['entrees_place_liberee']} sur E02 et {a2['entrees_place_liberee']} sur E00-ref. En réel, le signal reste valide toute la bougie et l'entrée se ferait plus tard au prix du moment [déduit du code, non observé].\n")
w("Le tableau ci-dessous donne une sensibilité seulement, par simulation et non par freqtrade. Il ne remplace jamais la base. La règle stricte interdit de réutiliser le jour même une place libérée par un stop. Son gain tient à un effet de chaîne sur très peu de trades, car 3 trades propres à cette règle portent +1 126 USDT sur E01. Le chiffre publié dépend donc d'une règle impossible à reproduire en réel, sans que le sens observé soit flatteur pour la base.\n")
w("| Essai | Rejeu base (trades, R, USDT) | Règle stricte (trades, R, USDT) |")
w("|---|---|---|")
for lab,x in (("E01",a0),("E02",a1),("E00-ref",a2)):
    w(f"| {lab} | {x['base']['n']}, {n(x['base']['exp'],'+.3f')}, {n(x['base']['pnl'],'+,.0f')} | {x['stricte']['n']}, {n(x['stricte']['exp'],'+.3f')}, {n(x['stricte']['pnl'],'+,.0f')} |")
w("")
w("Le risque réel est un peu sous les 0,5 % annoncés. S'y ajoute le facteur 0,99 de `tradable_balance_ratio`. Le pas de quantité sur BTC retire jusqu'à 10 % de plus, avec une mise rapportée à la cible médiane de 0,960 et minimale de 0,907, les autres paires restant au moins à 0,99 (E01). La perte stressée prévue va donc de 0,449 % à 0,495 % du capital. Ce pas vient des marchés actuels appliqués à des prix de 2021 [non vérifié pour les anciens pas]. L'effet est sans conséquence sur le signal et légèrement conservateur.\n")
w("## 5. Financement payé\n")
w("Source, champ `funding_fees` des exports, déjà inclus dans le P&L. Le financement est appliqué. Il est non nul sur 134 trades sur 135 pour E01 et 177 sur 178 pour E00-ref. Un recalcul indépendant depuis les fichiers (taux x mark x quantité) redonne -665,282 USDT pour E01 et -768,379 USDT pour E00-ref, avec un écart moyen nul à cinq décimales.\n")
w("| Essai | Longs (trades, espérance R, P&L) | Shorts (trades, espérance R, P&L) | Payé | Reçu | Net payé | dont longs | dont shorts | Frais |")
w("|---|---|---|---:|---:|---:|---:|---:|---:|")
for e in ORDER:
    p=M[e]["par_sens"];l,s,t=p["longs"],p["shorts"],p["total"]
    w(f"| {e} | {l['trades']}, {n(l['esperance_R'],'+.3f')}, {n(l['pnl'],'+,.0f')} | {s['trades']}, {n(s['esperance_R'],'+.3f')}, {n(s['pnl'],'+,.0f')} | {n(t['financement_paye'],',.0f')} | {n(t['financement_recu'],',.0f')} | {n(t['financement_net_paye'],',.0f')} | {n(l['financement_net_paye'],',.0f')} | {n(s['financement_net_paye'],',.0f')} | {n(t['frais'],',.0f')} |")
w("")
pe=M["E00-ref"]["par_sens"]; 
w(f"Sur E00-ref, le financement net payé ({n(pe['total']['financement_net_paye'],',.0f')} USDT) représente {pct(pe['total']['financement_net_paye']/pe['total']['pnl'],'.0f')} du P&L final de {n(pe['total']['pnl'],',.0f')} USDT et environ huit fois les frais. Le coût qui pèse est donc le financement et non les frais de transaction.\n")
w("## 6. Longs contre shorts\n")
w("Le tableau du § 5 donne le détail. Les shorts ont une espérance négative dans la base, sur E01, E02 et E00-ref. "
  f"Sur E00-ref, les longs donnent {n(pe['longs']['esperance_R'],'+.3f')} R sur {pe['longs']['trades']} trades et les shorts {n(pe['shorts']['esperance_R'],'+.3f')} R sur {pe['shorts']['trades']} trades. Tout le gain vient donc des longs sur une période où le panier de la fiche a fortement monté (Market change freqtrade de 895,85 % sur 20210101-20250731). Ce constat est décrit ici sans aucun changement de règle, car retirer les shorts serait une nouvelle stratégie.\n")
w("## 7. Résultat par paire\n")
w("Source, exports E01, E02 et E00-ref, calcul de `brut/controles.py`. Le R est nominal.\n")
for e in ["E01","E02","E00-ref"]:
    w(f"{e}.\n")
    w("| Paire | Trades | Réussite | Espérance R | Somme R | P&L USDT | Financement net payé | Première entrée |")
    w("|---|---:|---:|---:|---:|---:|---:|---|")
    for r in C["par_paire"][e]:
        w(f"| {r['pair'].split('/')[0]} | {r['trades']} | {pct(r['reussite'],'.0f')} | {n(r['esp_R'],'+.3f')} | {n(r['som_R'],'+.2f')} | {n(r['pnl'],'+,.0f')} | {n(r['fin_net_paye'],',.0f')} | {r['premier']} |")
    w("")
w("LTC perd sur les trois lignes et concentre la plus forte perte de E00-ref (-668 USDT, 21 trades, 10 % de réussite). Le classement des paires change beaucoup entre E01 et E02. DOGE et ADA portent E02 avec peu de trades (2 et 4).\n")
w("## 8. Semestres\n")
w("Source, `resultats/<essai>_metriques.json`, essai E00-ref. La colonne réalisée affecte chaque trade à sa date de clôture. La colonne réévaluée donne la variation de l'équité réévaluée sur le semestre. Le second semestre 2025 est partiel (31 jours) et son Sharpe annualisé n'a pas de sens.\n")
w("| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé USDT | P&L réévalué USDT |")
w("|---|---:|---:|---:|---:|---:|---:|---:|")
for r in M["E00-ref"]["semestres"]["semestres"]:
    w(f"| {r['semestre']}{' (partiel)' if r['partiel'] else ''} | {r['jours']} | {r['trades']} | {n(r['esperance_R'],'+.3f')} | {n(r['sharpe_annualise'],'.2f') if r['sharpe_significatif'] else 'non significatif'} | {pct(r['dd'])} | {n(r['pnl'],'+,.0f')} | {n(r['pnl_reevalue'],'+,.0f')} |")
w("")
w("| Essai | Positifs réalisés | Hors semestre partiel | Positifs réévalués | Réévalués hors semestre partiel |")
w("|---|---:|---:|---:|---:|")
for e in ORDER:
    x=M[e]["semestres"]
    w(f"| {e} | {x['n_positifs']}/{x['n_semestres']} | {x['n_positifs_hors_partiel']}/{x['n_semestres_hors_partiel']} | {x['n_positifs_reevalue']}/{x['n_semestres']} | {x['n_positifs_reevalue_hors_partiel']}/{x['n_semestres_hors_partiel']} |")
w("")
w("L'affectation à la clôture déforme la datation. Sur E00-ref, 20 trades à cheval sur deux semestres portent 75 % du P&L, soit +1 854 USDT sur +2 461 (`controles/sorties/verif2.txt` section 7). Trois semestres changent de signe une fois réévalués, soit 2021-S2, 2023-S1 et 2024-S1. Le nombre de semestres positifs n'est donc pas flatté, mais la datation des pertes et des gains l'est.\n")
w("En base réalisée, les semestres négatifs de 2022-S2 et 2023-S1 semblent former une phase de perte de juillet 2022 à juin 2023. Cette phase tient en partie à l'artefact, car 2023-S1 passe de -409 à +175 et 2022-S2 de -381 à -732. La perte réévaluée se concentre donc sur 2022-S2. Le gain de 2024-S1 (+693) devient -107. Le semestre partiel 2025-S2 (+461 USDT réalisés) tient presque entièrement à 3 force_exit (+470 USDT).\n")
w("## 9. Robustesse aux paramètres voisins\n")
w("Source, E00-ref et variantes sur 20210101-20250731, frais 0,0005. Les variantes sont des sous-classes dans `user_data/strategies/`. Aucune n'est retenue à la place de la base. Les colonnes « sans le meilleur » et « sans les 3 meilleurs » retirent ces trades de la moyenne sans rejouer le backtest.\n")
w("| Essai | Paramètre | Espérance R | IC 90 % iid | IC 90 % blocs | Sans le meilleur | Sans les 3 meilleurs | Meilleur trade | R max | DD réalisé | DD réévalué | Sharpe réévalué | DSR réévalué |")
w("|---|---|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|")
for e,lab in [("R01","entry 15"),("E03","entry 16"),("E00-ref","base 20 / 10 / 2,0"),("E04","entry 24"),("R02","entry 30"),("E05","exit 8"),("E06","exit 12"),("E07","atr 1,6"),("E08","atr 2,4")]:
    t=M[e]["trades"];c=C["concentration"][e]
    w(f"| {e} | {lab} | {n(t['esperance_R'],'+.3f')} | {n(t['ic90_bas'],'+.3f')} à {n(t['ic90_haut'],'+.3f')} | {ic(bl(e))} | {n(c['esp_sans_1'],'+.3f')} | {n(c['esp_sans_3'],'+.3f')} | {c['meilleur'].replace('/USDT:USDT','')} | {n(c['rmax'],'.1f')} | {pct(M[e]['metriques_quotidiennes']['dd_reel'])} | {pct(mk(e)['dd_reevalue'])} | {n(mk(e)['sharpe_annualise'],'.2f')} | {n(dk(e)['dsr'],'.3f')} |")
w("")
w("Les six voisins préenregistrés à ±20 % ont tous une espérance positive, de +0,058 à +0,646 R. L'écart est large pour des variations aussi faibles. E06 (exit 12) tombe à +0,058 R et devient nul sans son meilleur trade. Les valeurs élevées de E03 et R01 tiennent pour moitié à un seul trade (XRP de novembre 2024 à +44,8 R). E07 dépend moins d'un seul trade (ADA de janvier 2021 à +31,7 R) et retombe à +0,241 R sans ses trois meilleurs. Son drawdown réévalué atteint 17,7 %, proche du seuil de 20 % de la fiche, alors que sa ligne réalisée affiche 12,0 %. La limite de 3 positions rend le résultat très dépendant du chemin, car E00-ref rejette 575 signaux d'entrée. Une petite variation change les trades qui obtiennent une place.\n")
w("La base n'est pas le meilleur essai du registre. Ce constat ne change rien, car les variantes ne sont jamais substituées à la base.\n")
w("### Ordre de la whitelist, sixième paramètre non déclaré\n")
w("Quand plus de signaux que de places arrivent le même jour, freqtrade sert les paires dans l'ordre du dictionnaire des données (`time_pair_generator`, `list(data.keys())`). Cet ordre vient de `pair_whitelist` dans la configuration. La fiche ne donne aucune règle de priorité et annonce 5 paramètres libres, alors que cet ordre en constitue un sixième. Ni l'IC ni le DSR ne le captent. Le sens n'est pas flatteur, car la base se situe plutôt sous la médiane. L'instabilité est le problème, pas le biais.\n")
w("Le premier tableau vient de backtests freqtrade réels du contradicteur, avec les mêmes règles et seul l'ordre changé. Ils datent du 2026-10-31 entre 23:50Z et 23:52Z et n'ont pas été relancés (`controles/sorties_contradicteur/run_*.txt`, journaux en heure locale). Le second vient du rejeu indépendant de 200 ordres tirés avec la graine 0, rejoué le 01/11/2026 à l'identique (`controles/sorties/t5_permutations_ordre_places_strictes.txt`, `t5_ordres_*.csv`). Ces lignes servent de lecture, aucune n'est retenue et aucun ordre n'est choisi à cause de sa performance.\n")
w("| Essai | Ordre de la config (trades, USDT) | Ordre inverse (trades, USDT) | Ordre alphabétique (trades, USDT) |")
w("|---|---|---|---|")
w("| E01 | 135, +877 | 136, +1 968 | 126, +3 072 |")
w("| E02 | 46, +1 270 | 46, +1 356 | 45, +1 242 |")
w("| E00-ref | 178, +2 461 | 179, +3 662 | 169, +4 698 |")
w("")
w("| Essai | Rejeu base R | Min | p5 | Médiane | p95 | Max | Part des ordres à 0,2 R ou moins | Part des ordres qui égalent ou dépassent la base |")
w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for lab,k in (("E01","E01"),("E02","E02"),("E00-ref","E00")):
    x=T5[k]
    w(f"| {lab} | {n(x['base']['exp'],'+.3f')} | {n(x['exp_min'],'+.3f')} | {n(x['exp_p5'],'+.3f')} | {n(x['exp_med'],'+.3f')} | {n(x['exp_p95'],'+.3f')} | {n(x['exp_max'],'+.3f')} | {pct(x['part_exp_inf_02'],'.1f')} | {pct(x['part_ordres_sup_base'],'.1f')} |")
w("")
w("La position de E01 et de E00-ref face au seuil de 0,2 R dépend donc en partie de cet ordre. Le rejeu ne modélise pas le pas de quantité et s'écarte un peu des exports (+896 USDT contre +877 sur E01). Sa base n'est donc pas exactement celle du § 2. E10 ne donnera qu'un chemin parmi beaucoup, et l'avenant propose de le présenter avec cette distribution à titre de lecture.\n")
w("## 10. Concentration du gain\n")
w("Source, `resultats/controles_complementaires.json`.\n")
w("| Essai | P&L USDT | Part du meilleur trade | Part des 3 meilleurs | Meilleur mois | Part du meilleur mois | Mois positifs |")
w("|---|---:|---:|---:|---|---:|---:|")
for e in ["E01","E02","E00-ref","E09"]:
    c=C["concentration"][e]
    w(f"| {e} | {n(c['pnl_total'],'+,.0f')} | {pct(c['part_top1_pnl'],'.0f')} | {pct(c['part_top3_pnl'],'.0f')} | {c['meilleur_mois']} | {pct(c['part_meilleur_mois'],'.0f')} | {c['mois_pos']}/{c['mois_avec_cloture']} |")
w("")
w("Une part supérieure à 100 % signifie que ces trades dépassent le gain total. Sur E00-ref, décembre 2024 porte 56 % du gain et trois trades en portent 81 %. Le repère de `validation-edge` § 4.4 demande qu'aucun mois ni trade unique ne porte l'essentiel du gain. Le mois de décembre 2024 dépasse la moitié du gain sur E00-ref, à titre indicatif.\n")
w("## 11. Risque réalisé\n")
w("Source, exports, R nominal (profit / 0,5 % de l'équité de référence). La cible d'un trade arrêté au stop est de 1 R.\n")
w("| Essai | Stops | Perte moyenne R | Médiane R | Rapport à 1 R | Pire stop R | Moins grave R |")
w("|---|---:|---:|---:|---:|---:|---:|")
for e in ["E01","E02","E00-ref","E07","E08"]:
    r=C["risque_stops"][e]
    w(f"| {e} | {r['n_stop']} | {n(r['moy'],'.3f')} | {n(r['med'],'.3f')} | {n(abs(r['moy']),'.2f')} | {n(r['min'],'.3f')} | {n(r['max'],'.3f')} |")
w("")
w("Sur E00-ref, la perte moyenne au stop vaut 0,99 R (69 stops) et se décompose en 0,967 R de prix, 0,009 R de frais et 0,014 R de financement net. Le pire stop atteint -1,257 R (ETH long du 05/12/2023 au 03/01/2024, dont -0,284 R de financement). Aucun stop ne dépasse 1,5 R. Environ 16 % des stops dépassent 1 R. Hors stops, la pire sortie vaut -0,91 R et le meilleur trade +13,54 R.\n")
w("Cette mesure reste favorable par construction. Le backtest ne prend l'ouverture que si le stop est hors de toute la bougie (`optimize/backtesting.py`, lignes 612 à 617). Une ouverture au-delà du stop avec une bougie qui revient au stop remplit donc au prix du stop, ce qui est favorable. L'effet observé est nul, avec 0 ouverture au-delà du stop sur E01, E02 et E00-ref (`t8_gaps_verrou_qualite.txt`). Aucun glissement séparé n'est modélisé et un stop réel peut donc coûter davantage [non mesuré sur marché réel].\n")
w("Le mark 1h donne une borne absente de la version précédente (`t7_glissement_financement_mark1h.txt`). Il n'y a aucune ouverture horaire au-delà du stop. L'extension du prix au-delà du stop dans l'heure de franchissement vaut en moyenne 0,112 R sur E00-ref et au plus 0,603 R. C'est une borne haute et non un glissement mesuré. 5 stops de E00-ref ne sont pas atteints sur le mark 1h ce jour-là et sont donc touchés seulement sur le dernier prix.\n")
expo = None
w("La mise moyenne vaut 4,7 % de l'équité sur E00-ref et la plus forte 13,8 %. Le plafond de 20 % par actif n'a jamais été atteint. Trois positions au plus donnent donc une exposition inférieure à 42 %.\n")
w("## 12. Drawdown réévalué chaque jour\n")
w("`analyse_strat.py` calcule désormais les deux bases pour tous les essais et le fera pour E10 et E11. La base réévaluée ajoute le P&L latent au prix de clôture 1d, hors frais et financement latents. Source, `resultats/<id>_metriques.json`. Avec frais et financement courus, un contrôle donne pour E00-ref un Sharpe de 0,565 et un drawdown de 12,3 % (`controles/sorties/verif2.txt`, section 1). Le chiffre de 12,8 % reste donc prudent.\n")
w("| Essai | DD réalisé | DD réévalué | Creux | DD95 permutation | DD médian blocs | DD95 blocs | Sharpe réalisé | Sharpe réévalué | Sortino réalisé | Sortino réévalué | Calmar réalisé | Calmar réévalué |")
w("|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for e in ORDER:
    q=M[e]["metriques_quotidiennes"];d=mk(e);c=M[e]["monte_carlo_blocs"]
    w(f"| {e} | {pct(q['dd_reel'])} | {pct(d['dd_reevalue'])} | {d['date_creux']} | {pct(M[e]['trades']['dd_95'])} | {pct(c['dd_50'])} | {pct(c['dd_95'])} | {n(q['sharpe_annualise'],'.2f')} | {n(d['sharpe_annualise'],'.2f')} | {n(q['sortino_annualise'],'.2f')} | {n(d['sortino_annualise'],'.2f')} | {n(q['calmar'],'.2f')} | {n(d['calmar'],'.2f')} |")
w("")
n_real=sum(M[e]['metriques_quotidiennes']['dd_reel']>M[e]['trades']['dd_95'] for e in ORDER); n_mk=sum(mk(e)['dd_reevalue']>M[e]['trades']['dd_95'] for e in ORDER)
sb=[M[e]['metriques_quotidiennes']['sortino_annualise']/mk(e)['sortino_annualise'] for e in ("E00-ref","E01","E02","E09")]
w(f"Le Sortino est la métrique la plus flattée par la base réalisée, d'un facteur {n(min(sb),'.1f')} à {n(max(sb),'.1f')} sur les lignes de base E00-ref à E09. Le biais du Sharpe n'a pas de sens fixe. Il flatte la base (0,71 puis 0,56 sur E00-ref) mais sous-estime E03 et R01 (0,71 puis 0,87 et 0,75 puis 0,93). Les colonnes réalisées ne sont donc pas comparables d'un essai à l'autre.\n")
w(f"Le DD95 par permutation ne se comporte pas comme une borne. Le drawdown réalisé le dépasse sur {n_real} essais sur 13 et le drawdown réévalué sur {n_mk} sur 13. Il reste affiché à titre de comparaison et le drawdown réévalué devient le chiffre de référence au § 14. Le Monte Carlo tire maintenant des blocs de 30 jours de rendements réévalués, ce qui garde la dépendance entre jours. Il refait une trajectoire aussi longue que l'essai et décrit donc une dispersion possible du drawdown. Le DD95 par blocs de E00-ref ({pct(M['E00-ref']['monte_carlo_blocs']['dd_95'])}) dépasse 20 % avec une médiane de {pct(M['E00-ref']['monte_carlo_blocs']['dd_50'])}. Ce n'est pas le critère de la fiche, qui porte sur le drawdown hors échantillon. Avec des blocs de 15 ou 60 jours, ce DD95 vaut {pct(ICS['E00-ref']['mc_blocs_15_jours']['dd_95'])} et {pct(ICS['E00-ref']['mc_blocs_60_jours']['dd_95'])} (`controles/sorties/ic_sensibilite.txt`).\n")
w("## 13. Sharpe déflaté\n")
w(f"Choix des entrées. Le calcul principal porte sur la série réévaluée avec une V[SR] réévaluée. Le calcul sur la série réalisée reste affiché en second. E01 et E02 couvrent des périodes différentes des autres essais. Leur Sharpe mesure aussi un effet de régime et n'entre donc pas dans V[SR]. E00-ref a été ajouté pour que la base existe sur la même période que les variantes. V[SR] est donc calculée sur les 11 essais de 20210101-20250731, soit E00-ref, E03 à E09, R01, R02 et R03. V[SR] quotidienne vaut {n(SM['V_reevalue_11'],'.3e')} en réévalué et {n(SM['V_realise_11'],'.3e')} en réalisé. Source, `resultats/registre_dsr.json` et `resultats/sensibilite_dsr.json`.\n")
w("N vaut 13, soit les essais de ce `user_data`. La demande citait 12 essais (E01 à E09, R01 à R03). E00-ref s'y ajoute car il a été lancé, ce qui est le choix le plus prudent. Six contrôles de format antérieurs (3 paires, § 16) et sept backtests du contradicteur ont aussi tourné avec la stratégie de base. Ils ne sélectionnent rien et restent hors N, marqués comme tels au registre. Le tableau donne donc N = 19 et N = 26 en sensibilité, ainsi que N = 12 et N = 11. E10 et E11 ne sont pas comptés.\n")
w("| Essai | T | Sharpe réévalué | g3 | g4 | DSR réévalué principal (N 13, V 11 essais) | N 12 | N 11 | N 19 | N 26 | V sur 9 essais à mêmes frais | V théorique 1/T |")
w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for e in ORDER:
    x=S[e]
    w(f"| {e} | {x['T']} | {n(x['SR_ann_reevalue'],'.3f')} | {n(x['g3_reev'],'.2f')} | {n(x['g4_reev'],'.1f')} | {n(x['N13_V11_reevalue'],'.3f')} | {n(x['N12_V11_reevalue'],'.3f')} | {n(x['N11_V11_reevalue'],'.3f')} | {n(x['N19_V11_reevalue'],'.3f')} | {n(x['N26_V11_reevalue'],'.3f')} | {n(x['N13_V9_reevalue'],'.3f')} | {n(x['N13_Vnul_reevalue'],'.3f')} |")
w("")
w("Calcul second, sur la série réalisée, non comparable d'un essai à l'autre.\n")
w("| Essai | Sharpe réalisé | g3 | g4 | Dénominateur du PSR | DSR réalisé (N 13, V 11 essais) | N 12 | N 11 | N 19 | N 26 | V sur 9 essais | V 1/T | Hypothèse normale (g3 0, g4 3) |")
w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for e in ORDER:
    x=S[e]
    w(f"| {e} | {n(x['SR_ann_realise'],'.3f')} | {n(x['g3'],'.1f')} | {n(x['g4'],'.0f')} | {n(x['denominateur_psr_realise'],'.3f')} | {n(x['N13_V11'],'.3f')} | {n(x['N12_V11'],'.3f')} | {n(x['N11_V11'],'.3f')} | {n(x['N19_V11'],'.3f')} | {n(x['N26_V11'],'.3f')} | {n(x['N13_V9'],'.3f')} | {n(x['N13_Vnul'],'.3f')} | {n(x['N13_V11_normal'],'.3f')} |")
w("")
w("V n'est pas cohérente pour E01 et E02. Ces deux essais sont écartés de V pour éviter l'effet de régime, puis jugés avec une V mesurée sur 1673 jours. Les valeurs du tableau principal pour ces deux lignes ne sont donc pas centrales sans cette réserve. La V tranchée coupe les 11 séries sur la fenêtre de l'essai, sans rejeu de backtest, et reste une approximation. La V mise à l'échelle vaut V x 1673 / T.\n")
w("| Essai | Série | V commune, DSR | V tranchée | DSR | V mise à l'échelle | DSR | V = 1/T, DSR |")
w("|---|---|---:|---:|---:|---:|---:|---:|")
for e in ("E01","E02"):
    x=S[e]
    w(f"| {e} | réévaluée | {n(x['N13_V11_reevalue'],'.3f')} | {n(x['V_tranche_reevalue'],'.3e')} | {n(x['N13_Vtranche_reevalue'],'.3f')} | {n(x['V_echelle_reevalue'],'.3e')} | {n(x['N13_Vechelle_reevalue'],'.3f')} | {n(x['N13_Vnul_reevalue'],'.3f')} |")
    w(f"| {e} | réalisée | {n(x['N13_V11'],'.3f')} | {n(x['V_tranche_realise'],'.3e')} | {n(x['N13_Vtranche'],'.3f')} | {n(x['V_echelle_realise'],'.3e')} | {n(x['N13_Vechelle'],'.3f')} | {n(x['N13_Vnul'],'.3f')} |")
w("")
s0=S["E00-ref"]
w(f"Le seuil SR0 annualisé vaut {n(s0['N13_V11_reevalue_SR0ann'],'.3f')} dans le calcul principal et {n(s0['N13_V11_SR0ann'],'.3f')} sur la série réalisée. Il monte à {n(s0['N13_Vnul_SR0ann'],'.3f')} avec V = 1/T pour T = 1673. Source, `brut/sensibilite_dsr.txt`.\n")
w("Le DSR est à lire avec trois réserves. La première est que V[SR] transversale est faible car les variantes sont très corrélées entre elles, ce qui abaisse SR0. La deuxième est que les essais ne sont pas indépendants. La troisième tient à la série réalisée, dont le défaut vient du regroupement du P&L à la clôture. Elle compte 1526 jours sans clôture sur 1673 sur E00-ref, avec g3 = 10,7 et g4 = 157. En réévalué, g3 tombe à 0,03 et g4 à 12, et le DSR de E00-ref passe de 0,832 à 0,635. L'hypothèse normale seule donne 0,782.\n")
w("La correction par g3 et g4 n'est pas en défaut partout. Sur E00-ref réalisé, le bootstrap iid et le bootstrap par blocs de 30 jours donnent une probabilité plus haute que la formule (0,845 et 0,882 contre 0,832). L'écart de la formule se voit sur E02, avec un écart-type du Sharpe de 0,0358 contre 0,0458 en iid et 0,0575 en blocs, ainsi que sur E03 et R01. La série réévaluée s'aligne sur la formule sur les essais testés, sauf E02 en blocs (0,0693). Source, `controles/sorties/verif2.txt`, section 4.\n")
w("Le seuil conventionnel de 0,95 n'est atteint par aucune ligne en DSR réévalué. Sur la série réalisée, seuls E07 (0,987) et R01 (0,958) le dépassent, et E03 s'en approche (0,931). Un seul trade clos en un jour crée cet effet. Sur R01, le jour du 03/02/2025 (+25,14 %, trade XRP de +44,8 R) donne un dénominateur du PSR de 0,247 contre 0,656 pour E00-ref à Sharpe voisin. La formule est juste et c'est son entrée qui est un artefact. Ces variantes ne remplacent pas la base.\n")
w("## 14. Comparaison indicative aux seuils\n")
w("Comparaison factuelle à `validation-edge` § 5 sur développement + validation, à titre indicatif seulement. Le critère réglementaire porte sur le hors échantillon, qui n'est pas ouvert. Aucune conclusion de rentabilité n'en découle. La colonne « Position » décrit la seule valeur chiffrée et ne vaut pas validation.\n")
t0=M["E00-ref"]["trades"];q0=M["E00-ref"]["metriques_quotidiennes"]
w("| Critère | Seuil | Valeur dev+val | Position |")
w("|---|---|---|---|")
w(f"| Nombre de trades | ≥ 100 au total, dont ≥ 30 hors échantillon | E00-ref {t0['trades']}, hors échantillon non lancé | total au-dessus, partie hors échantillon non mesurée |")
w(f"| Espérance nette | > 0,2 R | E00-ref {n(t0['esperance_R'],'+.3f')}, E01 {n(M['E01']['trades']['esperance_R'],'+.3f')}, E02 {n(M['E02']['trades']['esperance_R'],'+.3f')}. Hors force_exit {n(t0['esperance_hors_force_exit_R'],'+.3f')}, {n(M['E01']['trades']['esperance_hors_force_exit_R'],'+.3f')} et {n(M['E02']['trades']['esperance_hors_force_exit_R'],'+.3f')}. Ordre de la whitelist en rejeu, E00-ref p5 {n(T5['E00']['exp_p5'],'+.3f')} et p95 {n(T5['E00']['exp_p95'],'+.3f')}, E01 p5 {n(T5['E01']['exp_p5'],'+.3f')} et p95 {n(T5['E01']['exp_p95'],'+.3f')} | E00-ref et E02 au-dessus, E01 en dessous. La position de E00-ref et de E01 dépend en partie de l'ordre (§ 9) |")
w(f"| Espérance avec coûts doublés | > 0 R | E09 {n(M['E09']['trades']['esperance_R'],'+.3f')} (rejeu réel), R03 à coûts x3 {n(M['R03']['trades']['esperance_R'],'+.3f')} | au-dessus. Le frais seul est stressé, sans modèle de glissement |")
w(f"| Drawdown maximal | < 20 % | référence réévaluée {pct(mk('E00-ref')['dd_reevalue'])} sur E00-ref, {pct(mk('E01')['dd_reevalue'])} sur E01, {pct(mk('E02')['dd_reevalue'])} sur E02. Réalisé {pct(q0['dd_reel'])} sur E00-ref. Pour lecture, DD95 par blocs {pct(M['E00-ref']['monte_carlo_blocs']['dd_95'])} sur E00-ref | en dessous en référence. La dispersion par blocs dépasse 20 % au 95e centile (§ 12) |")
w(f"| Tests multiples | Sharpe au-dessus du repère du § 4.3 pour le nombre d'essais | repère refait pour N = 13 et 4,58 ans, {n(SM['repere_N13'],'.2f')} ({n(SM['repere_N19'],'.2f')} pour N = 19). E00-ref {n(mk('E00-ref')['sharpe_annualise'],'.2f')} réévalué, {n(q0['sharpe_annualise'],'.2f')} réalisé. DSR réévalué {n(dk('E00-ref')['dsr'],'.3f')} | en dessous du repère |")
w("| Compatibilité | `commun-trading` § 3 et § 8 | risque prévu 0,5 %, perte moyenne au stop 0,99 R, levier 1, 3 positions, mise maximale 13,8 %, exposition sous 42 % | dans les valeurs prudentes. Les valeurs propres à Jonathan sont encore entre crochets dans `commun-trading` |")
w(f"| Critère de la fiche § 1 | borne basse de l'IC 90 % > 0 | par blocs E00-ref {n(bl('E00-ref')['bas'],'+.3f')}, E01 {n(bl('E01')['bas'],'+.3f')}, E02 {n(bl('E02')['bas'],'+.3f')}. En iid à 5000 tirages {n(t0['ic90_bas'],'+.3f')}, {n(M['E01']['trades']['ic90_bas'],'+.3f')} et {n(M['E02']['trades']['ic90_bas'],'+.3f')}. En iid à 50 000 tirages {n(M['E00-ref']['intervalles_dependance']['iid']['bas'],'+.3f')} sur E00-ref | en dessous de 0 sur les trois par blocs. Le -0,003 iid de E00-ref équivaut à une borne nulle aux erreurs de simulation près |")
w("")
w("Le repère de 0,80 reprend la formule qui donne environ 3,0 pour 500 essais sur un an, valeur retrouvée ici (3,05). Il s'applique normalement au Sharpe hors échantillon.\n")
b00=ICS['E00-ref']['bruit_borne_basse_blocs10']
w(f"La borne de l'IC sert de critère binaire dans la fiche, et sa méthode décide du signe près de zéro. Sur 40 graines de 5000 tirages, la borne iid de E00-ref a un écart-type de 0,0043 et 70 % des graines donnent une borne positive, contre 55 % sur E08 (`controles/sorties/verif3.txt`). À 50 000 tirages, la borne par blocs de E00-ref a un écart-type de {n(b00['ecart_type'],'.4f')} sur 20 graines. La borne iid positive de E05 devient négative par blocs ({n(bl('E05')['bas'],'+.3f')}). Le contradicteur obtenait pour E07 une borne proche de zéro avec des blocs mobiles sans repli ({n(ICS['E07']['blocs_mobiles_sans_repli_10'][0],'+.3f')} rejoué). Avec des blocs circulaires, qui donnent le même poids aux premiers et aux derniers trades, elle vaut {n(bl('E07')['bas'],'+.3f')}. Les sensibilités à la longueur des blocs sont dans `controles/sorties/ic_sensibilite.txt`.\n")
w("| Essai | iid 50 000 tirages | Blocs 5 trades | Blocs 10 trades | Blocs 20 trades | Blocs mobiles 10 trades sans repli | Épisodes | Mois d'ouverture |")
w("|---|---|---|---|---|---|---|---|")
for e in ("E00-ref","E01","E02","E05","E07","E08","E09"):
    v=M[e]["intervalles_dependance"]; x=ICS[e]
    f2=lambda p:f"{n(p[0],'+.3f')} à {n(p[1],'+.3f')}"
    w(f"| {e} | {ic(v['iid'])} | {f2(x['blocs_circulaires_5'])} | {f2(x['blocs_circulaires_10'])} | {f2(x['blocs_circulaires_20'])} | {f2(x['blocs_mobiles_sans_repli_10'])} | {ic(v['episodes'])} ({v['episodes']['grappes']} grappes) | {ic(v['mois'])} ({v['mois']['grappes']} grappes) |")
w("")
w("## 15. Anomalies\n")
w("| N° | Anomalie | Effet | Traitement |")
w("|---:|---|---|---|")
rows=[
("Dépassement de `download-data` au-delà de `--timerange` (§ 3).","Des données hors échantillon sont restées 3 min 12 s sur le disque, sans être affichées ni utilisées.","Troncature à 22:33:27Z avant tout backtest. Relancer `download-data` dans ce `user_data` les ramènerait, il faudra tronquer de nouveau tant que E10 n'est pas ouvert."),
("Si `git add .` est lancé, `user_data/data/` sera inclus. Le motif `user_data/data/` du `.gitignore` racine est ancré à la racine du dépôt et ne couvre pas ce dossier.","22 Mo de données de marché et les fichiers de `user_data` entreraient dans le dépôt.","Non corrigé ici, hors périmètre. Décision à prendre avant le commit."),
("`--export-filename` de la procédure est déprécié.","Aucun effet avec freqtrade 2026.10.","`--backtest-directory` avec un dossier créé d'avance par essai."),
("`recursive-analysis` refuse `--fee`.","Premier lancement rejeté, conservé dans `brut/E01_recursive-analysis_essai1_refus_option_fee.txt`. Il affiche `exit=0` malgré le refus, donc ce code de sortie n'est pas une preuve de succès.","Option retirée, sans effet sur les indicateurs testés."),
("`lookahead-analysis` vise 20 signaux par défaut.","Couverture faible des 135 trades de E01.","Second lancement à 271 signaux. Il remplace aussi certains réglages (mise 10000, positions illimitées, stop hors plateforme), ce qui est le fonctionnement normal de l'outil."),
("Le filet de -30 % ne borne pas le stop. Après remplissage, `custom_stoploss` peut élargir le stop.","Sur E00-ref, trois shorts du 22/06/2021 (XRP, LTC, BCH) ont un stop à 33 % à 37 %. Aucun n'a touché le stop et la taille reste calculée sur cette distance.","Consigné, stratégie non modifiée."),
("Les fins de trade sont datées à l'ouverture de la bougie 1d.","Le financement est compté bornes incluses jusqu'à cette date. Une sortie en cours de journée peut donc omettre des paiements et une entrée à 00:00 en compte un.","Chiffré le 01/11/2026 (`t7_glissement_financement_mark1h.txt`). Financement compté à l'instant d'entrée, -8,33 USDT sur E01, -0,90 sur E02 et -9,38 sur E00-ref pour -768,38 au total. Financement omis avant franchissement du stop, -2,17 sur E01 et -2,16 sur E00-ref [heure estimée sur le mark 1h]. L'écart est négligeable et le sens net légèrement défavorable au backtest."),
("Aucun glissement n'est modélisé et le stop se remplit au prix exact sur bougies 1d.","E09 et R03 stressent le seul paramètre `--fee`. La demande « slippage x2 et x3 » est donc traduite par des frais x2 et x3.","Consigné."),
("Les exports ne contiennent pas la version de freqtrade.","Le champ reste vide dans les métriques.","Version de l'environnement notée, 2026.10."),
("Biais de sélection de l'univers, au-delà du seul biais du survivant (fiche § 2). La fiche dit que les 10 actifs étaient [déjà parmi les plus liquides début 2021, affirmation contredite pour DOGE et TRX].","Les paires délistées sont absentes. Sur le volume des perpétuels Binance de décembre 2020, DOGE est 42e et TRX 19e parmi 70 paires [rangs minimaux, exécution du contradicteur du 2026-11-01T00:03:04Z, `controles/t11_rangs_volume_dec2020.py`, non rejouée car cette reprise interdit tout téléchargement]. Les volumes locaux confirment que ces deux paires sont les plus faibles des 10 (DOGE 0,43 G$, TRX 1,32 G$, BTC 224,92 G$, `t8_gaps_verrou_qualite.txt`). En rejeu simulé, E02 passe de "+n(T12['E02']['base']['exp'],'+.3f')+" R à "+n(T12['E02']['sans_doge']['exp'],'+.3f')+" R sans DOGE puis "+n(T12['E02']['sans_doge_trx']['exp'],'+.3f')+" R sans DOGE ni TRX. E00-ref passe de "+n(T12['E00']['base']['exp'],'+.3f')+" à "+n(T12['E00']['sans_doge']['exp'],'+.3f')+" puis "+n(T12['E00']['sans_doge_trx']['exp'],'+.3f')+" R.","Univers figé inchangé. À porter à l'avocat du diable. Un univers défini par le volume à date serait une nouvelle stratégie et un nouvel essai."),
("Intervalle à 90 % calculé sur des trades traités comme indépendants.","Les actifs sont corrélés et 99 % à 100 % des trades en chevauchent un autre. La corrélation de rang entre trades chevauchants reste faible (0,003 sur E00-ref), donc l'élargissement est modéré mais il décide du signe près de zéro.","IC par blocs ajouté (§ 2 et § 14), iid conservé pour comparaison. Méthode à fixer avant E10 dans l'avenant."),
("Ordre de la whitelist, sixième paramètre libre non déclaré. Freqtrade sert les paires dans l'ordre du dictionnaire quand les signaux dépassent les places.","Sur 200 ordres en rejeu, l'espérance de E01 va de +0,011 à +0,468 R et 53,5 % des ordres sont à 0,2 R ou moins. Celle de E00-ref va de +0,175 à +0,528 R (§ 9). Bloquant pour E10 seulement, car ce run unique ne donnerait qu'un chemin.","Porté dans l'avenant, statut proposé. Ordre actuel figé sans chercher le meilleur, aucun ordre retenu pour sa performance. À porter à l'avocat du diable."),
("Attribution des places dans freqtrade. Les paires déjà en position passent d'abord dans la bougie et un stop du jour libère une place à l'ouverture de ce même jour.","6 entrées sur E01, 1 sur E02 et 6 sur E00-ref. La règle stricte simulée donne +0,333 R contre +0,137 R sur E01 (§ 4). `lookahead-analysis` ne teste pas ce cas.","Sensibilité seulement, jamais un remplacement de la base. Le traitement des entrées en cours de bougie est à décider avant le papier, et toute modification sera un nouvel essai."),
("Stop divergent entre backtest et papier. Dans `_atr_at_entry`, `date < open_date` exclut la bougie d'entrée en backtest (00:00:00). En papier, open_date vaut quelques secondes après minuit et la bougie d'entrée passe le filtre dès le lendemain.","Le stop peut alors se resserrer, jamais s'élargir. Estimation par rejeu, 53 trades sur 135 sur E01 et 70 sur 178 sur E00-ref, médiane 1,5 % de la distance et maximum 4,9 %, avec 6 et 7 sorties modifiées (`t9`, `t10`) [mode papier non exécuté]. La comparaison papier contre backtest serait faussée.","Stratégie non modifiée. Correctif à enregistrer comme nouvel essai avant le papier, sans changer les paramètres (avenant)."),
("Régime connu des auteurs. La fiche écrite avant test cite un mouvement de mi-2026, en plein hors échantillon (fiche § 4 point 2).","Le hors échantillon n'a pas été lu dans les données de backtest, mais les auteurs connaissaient qualitativement le régime. Les paramètres étant classiques et figés, l'effet paraît limité sans pouvoir être exclu.","À signaler dans le verdict. E10 ne sera pas présenté comme totalement aveugle."),
("Six contrôles de format antérieurs, absents du registre et de la version précédente de ce rapport. Sept backtests du contradicteur et 600 rejeux simulés s'y ajoutent.","Mêmes règles de base, aucun accès au hors échantillon et aucun paramètre changé. Effet limité sur le DSR, E00-ref passe de 0,635 à 0,602 avec N = 19 (réévalué).","Métadonnées dans `brut/format_check/` et scripts dans `controles/`. Deux lignes de synthèse au registre, marquées hors N."),
("Commentaires de E10 et E11 réécrits après coup dans le registre (mention verrouillé ajoutée dans la colonne commentaire).","Aucun effet sur variante, période ni frais, mais le registre préenregistré avait changé sans trace.","Texte d'origine restauré (`git show HEAD:`). Le verrouillage passe dans la colonne statut."),
("Les champs `initial_stop_loss_abs` et `initial_stop_loss_ratio` des exports ne donnent pas le stop initial réel.","Ils valent le filet de -30 % sur tous les trades de E01, avec un écart jusqu'à 27 % au stop réel. Aucun chiffre publié n'est touché, car `analyse_strat.py` et `controles.py` ne les lisent pas.","Le champ à lire est `stop_loss_abs`. Toute analyse future devra s'y tenir."),
]
for i,(a,b,c) in enumerate(rows,1): w(f"| {i} | {a} | {b} | {c} |")
w("")
w("## 16. Sorties brutes et traçabilité\n")
w("Les fichiers .zip sont exclus de git. Le dossier `resultats/brut/` conserve donc le texte. Il contient pour chaque essai `<id>_backtesting.txt` (tableaux freqtrade complets), `<id>_analyse.txt` et `<id>_analyse_dsr.txt`, ainsi que `run_essais.sh`, `registre_dsr.py`, `controles.py` et `sensibilite_dsr.py`. La reprise du 01/11/2026 ajoute `<id>_analyse_reevalue.txt`, `rejeu_analyse.sh` et `remplit_registre.py`, avec les tests dans `tests_analyse_strat.txt`. La version précédente de la sensibilité reste dans `sensibilite_dsr_20261031.py` et `.txt`. Les métriques sont dans `resultats/<id>_metriques.json` et `.md`.\n")
w("Le dossier `brut/format_check/` garde les métadonnées et une synthèse des 6 contrôles de format, lancés avant ce `user_data`. Le dossier `controles/` garde les scripts des contradicteurs, leurs sorties et un index (`controles/LISEZMOI.md`). Les 6 contrôles de format et les 7 backtests du contradicteur ne sont pas des candidats et n'ont pas été relancés.\n")
w("| Essai | Backtest exécuté (UTC) | sha256 de l'export (16 premiers caractères) |")
w("|---|---|---|")
for e in ORDER:
    tr=M[e]["tracabilite"]; w(f"| {e} | {tr['backtest_execute_le_utc'][:19]}Z | `{tr['sha256_export'][:16]}` |")
w("")
w("| Fichier resté intact | sha256 avant (22:29:58Z) | sha256 après |")
w("|---|---|---|")
av={"FICHE_STRAT-20261031-01.md":"2ac936ba1638e3955a0d94df99e1a7945345741fb2a0844c12351fff31a5e180","TrendDonchianV1.py":"072c0e3b4d6f2df9ae3fb83373aa30a7902c499ca150e003d3a457c4da2a6cee","config_strat01.json":"a473eaad2bcf27c3665542c2ce0858b6409c7890f30485eb768b4e8f96dda08d"}
for f,h in av.items():
    now=sh(f); assert now==h, f
    w(f"| {f} | `{h}` | `{now}` |")
w("")
w("## 17. Non vérifié\n")
w("Le moment exact de remplissage d'un stop dans la journée n'est pas connu sur des bougies 1d. L'instant d'éligibilité de DOGE est déduit du code [non observé]. Les performances n'ont pas été comparées à une exécution réelle ou papier. L'avocat du diable après résultats n'a pas été joué ici, car il revient à l'étape de verdict. Les rangs de volume de DOGE et TRX n'ont pas été rejoués dans cette reprise, car elle interdit tout téléchargement. L'effet réel d'une entrée en cours de bougie et le stop en mode papier sont déduits du code et d'un rejeu [non observés en papier]. Le cas restant du décompte de `lookahead-analysis` est [non élucidé]. La référence du papier de Bailey et López de Prado reste citée de mémoire [papier non rouvert].\n")
w(f"Sources : exports freqtrade 2026.10 du 31/10/2026, rejeux du 01/11/2026 sur ces exports, données publiques des perpétuels USDT de Binance (1d, mark 1h, financement) coupées au 31/07/2025.")
(res/"RAPPORT_E01_E09.md").write_text("\n".join(L)+"\n",encoding="utf-8")
