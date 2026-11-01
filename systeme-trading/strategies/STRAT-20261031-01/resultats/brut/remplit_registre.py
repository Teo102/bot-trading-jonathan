"""Met à jour REGISTRE_ESSAIS.csv depuis resultats/<id>_metriques.json. Les colonnes d'origine gardent leur place.
Les valeurs déjà inscrites (date, variante, commentaire...) ne changent pas, sauf le commentaire de E10 et E11 rendu à son texte
préenregistré. Le verrouillage de ces deux lignes passe dans la colonne statut. Les lignes de synthèse sont marquées hors N."""
import csv, json, sys
from pathlib import Path
base = Path(sys.argv[1]); res = base/"resultats"; path = base/"REGISTRE_ESSAIS.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
COLS = ["id_essai","date","strategie","variante","bloc","timerange","frais","trades","esperance_R","ic90_bas","ic90_haut","dd_reel","dd_95","commentaire",
        "sharpe_realise","dsr","statut","sharpe_reevalue","dd_reevalue","dsr_reevalue","ic90_blocs_bas","ic90_blocs_haut","esperance_hors_force_exit"]
ORIGINE = {"E10": "verdict", "E11": "meme regles - stress des couts"}
out = []
for r in rows:
    if r["id_essai"].startswith("CTRL-"):
        continue
    r = dict(r)
    if "sharpe" in r: r["sharpe_realise"] = r.pop("sharpe")
    e = r["id_essai"]
    if e in ORIGINE:
        r["commentaire"] = ORIGINE[e]; r["statut"] = "verrouillé"
    else:
        m = json.loads((res/f"{e}_metriques.json").read_text(encoding="utf-8"))
        mk, iv, t = m["metriques_reevaluees"], m["intervalles_dependance"], m["trades"]
        r.update(statut="exécuté", sharpe_reevalue=f"{mk['sharpe_annualise']:.3f}", dd_reevalue=f"{mk['dd_reevalue']:.4f}",
                 dsr_reevalue=f"{m['dsr_reevalue']['dsr']:.3f}", ic90_blocs_bas=f"{iv['blocs']['bas']:.4f}", ic90_blocs_haut=f"{iv['blocs']['haut']:.4f}",
                 esperance_hors_force_exit=f"{t['esperance_hors_force_exit_R']:.4f}")
    out.append(r)
out.append({"id_essai":"CTRL-FORMAT","date":"2026-10-31","strategie":"STRAT-20261031-01","variante":"base - 3 paires BTC ETH XRP",
            "bloc":"controles de format - synthese de 6 backtests - pas un essai","timerange":"20210101-20221201 / 20210401-20220101 / 20210401-20221201","frais":"0.0005 / 0.0010",
            "statut":"hors N (contrôles de format)",
            "commentaire":"synthese hors N, marquee comme telle - aucun parametre change et aucune selection - detail dans resultats/brut/format_check/ - N = 19 en sensibilite"})
out.append({"id_essai":"CTRL-CONTRADICTEUR","date":"2026-10-31","strategie":"STRAT-20261031-01","variante":"base - ordres de whitelist inverse et alphabetique, strategie instrumentee",
            "bloc":"controles du contradicteur - synthese de 7 backtests et de 600 rejeux simules - pas un essai","timerange":"20210101-20240630 / 20240701-20250731 / 20210101-20250731","frais":"0.0005",
            "statut":"hors N (contrôles du contradicteur)",
            "commentaire":"synthese hors N, marquee comme telle - aucun ordre retenu - detail dans resultats/controles/ - N = 26 en sensibilite"})
with open(path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n"); w.writeheader()
    for r in out: w.writerow({c: r.get(c, "") for c in COLS})
