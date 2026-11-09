#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A6 (aucun rendement de stratégie).
1. Valeurs nulles de `sum_open_interest` dans les metrics : où, et que voit le détecteur ?
2. Klines 1 minute : unité de l'heure d'ouverture, bougies incomplètes (close_time - open_time != 59 999 ms),
   minutes manquantes, doublons, dernière bougie du mois, bougies à volume nul.
Usage : python3 -B a6_zeros_et_klines.py"""
import io, json, sys, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd, requests

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent.parent / "strategies" / "STRAT-20261109-08"))
sys.path.insert(0, str(ICI.parent.parent / "strategies" / "STRAT-20261031-03"))
import detection_cascades as dc  # noqa: E402
import donnees_1m as d1  # noqa: E402
import donnees_binance as db  # noqa: E402


def get(url):
    for essai in range(6):
        try:
            return requests.get(url, timeout=120)
        except requests.exceptions.ConnectionError:
            time.sleep(2 + essai)
    raise RuntimeError(url)


def oi_jour(sj):
    sym, j = sj
    r = get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{j}.zip")
    return d1.lire_metrics_contrats(r.content) if r.status_code == 200 else None


R = {"zeros": {}, "klines": {}}
print("== 1. Valeurs nulles ou vides de l'intérêt ouvert (lecteur de STRAT-08)")
for sym, m in [("SUIUSDT", "2024-08"), ("1000PEPEUSDT", "2024-08"), ("WIFUSDT", "2024-12"), ("ARBUSDT", "2024-12")]:
    jours = [d.date().isoformat() for d in pd.date_range(f"{m}-01", pd.Period(m).end_time.normalize(), freq="D")]
    with ThreadPoolExecutor(4) as ex:
        oi = pd.concat([x for x in ex.map(oi_jour, [(sym, j) for j in jours]) if x is not None]).sort_index()
    z = oi[(oi <= 0)]
    nan = oi[oi.isna()]
    v = oi.pct_change(3, fill_method=None)
    faux = v[(v <= -0.02) & (oi <= 0)]
    R["zeros"][f"{sym} {m}"] = {"lignes": int(len(oi)), "nulles": int(len(z)), "vides": int(len(nan)), "heures_nulles": [str(t) for t in z.index[:8]],
                               "instants_ou_Y_serait_rempli_par_un_zero": int(len(faux))}
    print(sym, m, R["zeros"][f"{sym} {m}"])

print("== 2. Klines 1 minute brutes")
for sym, m in [("SOLUSDT", "2021-05"), ("SOLUSDT", "2022-11"), ("SUIUSDT", "2024-08"), ("1000PEPEUSDT", "2025-06"), ("WIFUSDT", "2024-12")]:
    r = get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1m/{sym}-1m-{m}.zip")
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f, header=None, dtype=str)
    entete = not df.iloc[0, 0].isdigit()
    if entete:
        df = df.iloc[1:]
    o, c = df[0].astype("int64"), df[6].astype("int64")
    unite = "us" if o.max() > 10**14 else "ms"
    t = pd.to_datetime(o, unit=unite)
    attendu = pd.date_range(f"{m}-01", pd.Period(m).end_time.floor("min"), freq="min")
    duree = (c - o)
    k = db.lire_klines(r.content)
    R["klines"][f"{sym} {m}"] = {"entete": bool(entete), "unite": unite, "lignes": int(len(df)), "minutes_attendues": int(len(attendu)),
                                "manquantes": int((~attendu.isin(t)).sum()), "doublons": int(t.duplicated().sum()),
                                "durees_anormales": int((duree != (59999 if unite == "ms" else 59999999)).sum()),
                                "heure_non_ronde": int((t.dt.second != 0).sum()), "volume_nul": int((df[5].astype(float) == 0).sum()),
                                "premiere": str(t.min()), "derniere": str(t.max()),
                                "lecteur_identique": bool((k.index == t.values).all()), "trie": bool(t.is_monotonic_increasing)}
    print(sym, m, R["klines"][f"{sym} {m}"])
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"a6_zeros_et_klines_{h}.json").write_text(json.dumps({"genere_utc": h, **R}, indent=1))
