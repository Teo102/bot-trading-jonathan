#!/usr/bin/env python3
"""Audit Fable, STRAT-07, contrôle B3 (aucune donnée de rendement nouvelle : listes d'archives et dates des épisodes déjà lus).
1. Le criblage a-t-il lu des versements du bloc hors échantillon (à partir du 28/07/2025 00:00 UTC) ?
2. La paire au comptant de même nom avait-elle des archives pendant tout l'épisode (début et fin) ?
   Le criblage ne contrôle que le mois de première cotation.
Usage : python3 -B b3_comptant_et_verrou_strat07.py <dossier des episodes_*.csv>"""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
BASE = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"


def mois_comptant(sym):
    for essai in range(6):
        try:
            r = requests.get(BASE, params={"delimiter": "/", "prefix": f"data/spot/monthly/klines/{sym}/1d/"}, timeout=60)
            m = sorted(set(re.findall(rf"{re.escape(sym)}-1d-(\d{{4}}-\d{{2}})\.zip<", r.text)))
            return sym, m
        except requests.exceptions.RequestException:
            time.sleep(2 + essai)
    return sym, None


e = pd.read_csv(Path(sys.argv[1]) / "episodes_entree_50_sortie_10.csv", parse_dates=["debut", "fin"])
R = {"verrou": {"fin_max": str(e["fin"].max()), "episodes_finissant_le_28_07_2025_ou_apres": int((e["fin"] >= "2025-07-28").sum()),
                "ouverts_au_verrou": int(e["ouvert_au_verrou"].fillna(False).astype(bool).sum())}}
print("1.", R["verrou"])
syms = sorted(e["symbole"].unique())
with ThreadPoolExecutor(4) as ex:
    mois = dict(ex.map(mois_comptant, syms))
pb = []
for r in e.itertuples():
    m = mois.get(r.symbole)
    if not m:
        pb.append((r.symbole, str(r.debut), str(r.fin), "aucune archive au comptant listée")); continue
    # mois entiers strictement compris dans l'épisode : chacun doit avoir une archive mensuelle
    dedans = [str(p) for p in pd.period_range(r.debut, r.fin, freq="M")][1:-1]
    manq = [x for x in dedans if x not in m]
    if r.debut.strftime("%Y-%m") < m[0] or manq:
        pb.append((r.symbole, str(r.debut), str(r.fin), f"comptant listé de {m[0]} à {m[-1]}, mois sans archive : {manq[:4]}"))
R["comptant"] = {"symboles": len(syms), "episodes": int(len(e)), "episodes_sans_comptant_complet": len(pb), "exemples": pb[:15],
                 "net_des_episodes_en_cause": round(float(e[e.apply(lambda r: any(p[0] == r.symbole and p[1] == str(r.debut) for p in pb), axis=1)]["net"].sum()), 4),
                 "net_total": round(float(e["net"].sum()), 4)}
print("2.", json.dumps(R["comptant"], indent=1, ensure_ascii=False))
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"b3_comptant_et_verrou_strat07_{h}.json").write_text(json.dumps({"genere_utc": h, **R}, indent=1, ensure_ascii=False))
