#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A2 : date de la bascule d'horodatage des metrics sur des alts.

Mesure de synchronisation pure, méthode de STRAT-04 (`mesure_bascule_horodatage.py`) étendue à 8 alts.
Lit la valeur absolue des rendements à 5 minutes (aucun sens, aucune position, aucun rendement de stratégie),
sur 2023-06 (développement) et 2024-02 à 2024-04 et 2025-03 (validation). Rien du hors échantillon.
Si l'heure est juste, |variation d'intérêt ouvert| en s couvre [s-5, s) et le pic de corrélation tombe sur la bougie
ouverte à s-5 (pas -1). Si le pic tombe sur la bougie ouverte en s (pas 0), l'archive est datée 5 minutes trop tôt.

Usage : python3 -B a2_bascule_alts.py"""
import io, json, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
SYMS = ["SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT", "ARBUSDT", "SUIUSDT", "1000PEPEUSDT"]
MOIS = ["2023-06", "2024-02", "2024-03", "2024-04", "2025-03"]


def get(url):
    for essai in range(6):
        try:
            return requests.get(url, timeout=60)
        except requests.exceptions.ConnectionError:
            time.sleep(2 + essai)
    raise RuntimeError(url)


def metrics_jour(sj):
    sym, j = sj
    r = get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{j}.zip")
    if r.status_code != 200:
        return None
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf, zf.open(zf.namelist()[0]) as f:
        return pd.read_csv(f, usecols=["create_time", "sum_open_interest"])


R, jours_tous = {}, {}
for sym in SYMS:
    for m in MOIS:
        r = get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/5m/{sym}-5m-{m}.zip")
        if r.status_code != 200:
            print(sym, m, "klines absentes"); continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf, zf.open(zf.namelist()[0]) as f:
            k = pd.read_csv(f, header=None, usecols=[0, 1, 4])
        if str(k.iloc[0, 0]) == "open_time":
            k = k.iloc[1:]
        k.columns = ["t", "o", "c"]; k = k.astype(float)
        k.index = pd.to_datetime(k.t.astype("int64"), unit="ms")
        ret = (k.c / k.o - 1).abs()
        jours = [d.date().isoformat() for d in pd.date_range(f"{m}-01", pd.Period(m).end_time.normalize(), freq="D")]
        with ThreadPoolExecutor(4) as ex:
            parts = [x for x in ex.map(metrics_jour, [(sym, j) for j in jours]) if x is not None]
        mm = pd.concat(parts); mm.index = pd.to_datetime(mm.create_time).dt.round("min").values
        oi = mm[~mm.index.duplicated()].sort_index().sum_open_interest.astype(float)
        d = oi.pct_change().abs()
        par_jour = []
        for dd, g in d.groupby(d.index.floor("D")):
            cs = {}
            for p in (-1, 0):
                r2 = ret.copy(); r2.index = r2.index - pd.Timedelta(minutes=5 * p)
                x = pd.concat([g.rename("d"), r2.rename("r")], axis=1, join="inner").dropna()
                cs[p] = x.d.corr(x.r, method="spearman") if len(x) > 50 else float("nan")
            par_jour.append((dd.date().isoformat(), cs[-1], cs[0]))
        D = pd.DataFrame(par_jour, columns=["j", "pas_moins_1", "pas_0"]).set_index("j")
        part0 = float((D.pas_0 > D.pas_moins_1).mean())
        R[f"{sym} {m}"] = {"corr_moy_pas_moins_1": round(float(D.pas_moins_1.mean()), 3), "corr_moy_pas_0": round(float(D.pas_0.mean()), 3),
                           "part_des_jours_au_pas_0": round(part0, 3)}
        if m == "2024-03":
            jours_tous[sym] = D
        print(sym, m, R[f"{sym} {m}"], flush=True)
print("== Mars 2024, jour par jour : pas gagnant par symbole (-1 = heure juste, 0 = datée 5 min trop tôt)")
T = pd.DataFrame({s: (D.pas_0 > D.pas_moins_1).map({True: 0, False: -1}) for s, D in jours_tous.items()})
print(T.head(12).to_string())
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"a2_bascule_alts_{h}.json").write_text(json.dumps({"genere_utc": h, "par_mois": R, "mars_2024_pas_gagnant": T.to_dict()}, indent=1))
