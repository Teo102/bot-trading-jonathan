"""Construit resultats/registre_dsr.json : N = essais réellement lancés, V = Sharpe quotidiens de la seule période commune."""
import json, sys, datetime as D
from pathlib import Path
res = Path(sys.argv[1])
meme_periode = ["E00-ref","E03","E04","E05","E06","E07","E08","E09","R01","R02","R03"]
autres = ["E01","E02"]
essais = []
for e in meme_periode + autres:
    m = json.loads((res/f"{e}_metriques.json").read_text(encoding="utf-8"))
    q = m["metriques_quotidiennes"]
    row = {"id": e, "statut": "exporte", "timerange": m["plage"]["timerange_analyse"], "frais": m["execution"]["frais_par_cote"],
           "T": q["T"], "sha256_export": m["tracabilite"]["sha256_export"]}
    q_r = m["metriques_reevaluees"]
    if e in meme_periode:
        row["sharpe_quotidien"] = q["sharpe_quotidien"]
        row["sharpe_quotidien_reevalue"] = q_r["sharpe_quotidien"]
    else:
        row["sharpe_quotidien"] = None
        row["sharpe_quotidien_hors_V"] = q["sharpe_quotidien"]
        row["sharpe_quotidien_reevalue"] = None
        row["sharpe_quotidien_reevalue_hors_V"] = q_r["sharpe_quotidien"]
        row["note"] = "Compté dans N. Exclu de V car période différente."
    essais.append(row)
out = {"essais": essais, "n_essais_declares": len(essais),
       "note": "N = 13 lancés (E01 à E09, R01 à R03, E00-ref). V sur les 11 essais de la période 20210101-20250731, calculée à part pour la série réalisée et pour la série réévaluée. Les 6 contrôles de format de 3 paires ne sont pas comptés (voir REGISTRE_ESSAIS.csv, N = 19 en sensibilité). E10 et E11 non lancés, non comptés.",
       "agrege_le_utc": D.datetime.now(D.timezone.utc).isoformat(timespec="seconds")}
(res/"registre_dsr.json").write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
