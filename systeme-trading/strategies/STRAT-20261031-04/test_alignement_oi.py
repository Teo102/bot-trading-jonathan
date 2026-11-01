#!/usr/bin/env python3
"""STRAT-20261031-04 : à quel instant réel correspond un horodatage d'OI, et quand est-il publié ?

Contrôle du biais d'anticipation, sans aucun prix ni rendement.
- Relève l'OI en direct (/fapi/v1/openInterest) toutes les 10 s.
- Relève en parallèle le dernier point de /futures/data/openInterestHist et note son heure d'apparition.
- À la fin, cherche pour chaque point publié l'instant du relevé direct dont la valeur est la plus proche.
- L'archive metrics d'un jour se compare à part : archive(t) = REST(t + 5 min), mesuré par mesure_carnet_signaux.py.

Usage : python test_alignement_oi.py --minutes 22
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent
FAPI = "https://fapi.binance.com"
SYMS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT"]


def iso(s):
    return datetime.fromtimestamp(s, timezone.utc).strftime("%H:%M:%S")


def alignement_archive(cache_metrics, cache_5m):
    """Corrélation entre |variation d'OI| de l'archive et |rendement 5 min|, à plusieurs décalages.

    Mesure de synchronisation pure. Si create_time = instant réel, la variation à s couvre [s-5, s)
    et le pic tombe sur la bougie ouverte à s-5 (j = -1). Si le pic est à j = 0, l'archive est
    horodatée 5 minutes trop tôt et son usage direct serait un biais d'anticipation.
    """
    import io
    import zipfile

    import pandas as pd

    sortie = []
    cache_5m.mkdir(parents=True, exist_ok=True)
    for sym in ["BTCUSDT", "DOGEUSDT", "ETHUSDT"]:
        for an, mo in [(2022, 6), (2023, 4), (2024, 8), (2025, 10), (2026, 9)]:
            n = f"{sym}-5m-{an}-{mo:02d}.zip"
            c = cache_5m / n
            if not c.exists():
                r = requests.get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/5m/{n}", timeout=60)
                r.raise_for_status()
                c.write_bytes(r.content)
            with zipfile.ZipFile(c) as z, z.open(z.namelist()[0]) as f:
                k = pd.read_csv(f, header=None, usecols=[0, 1, 4])
            if str(k.iloc[0, 0]) == "open_time":
                k = k.iloc[1:]
            k.columns = ["t", "o", "c"]
            k = k.astype(float)
            k.index = pd.to_datetime(k.t.astype("int64"), unit="ms", utc=True).astype("datetime64[ns, UTC]")
            ret = (k.c / k.o - 1).abs()
            parts = []
            for j in pd.date_range(f"{an}-{mo:02d}-01", periods=31, freq="D"):
                if j.month != mo:
                    continue
                z = cache_metrics / sym / f"{sym}-metrics-{j.date()}.zip"
                if z.exists():
                    with zipfile.ZipFile(z) as zz, zz.open(zz.namelist()[0]) as f:
                        parts.append(pd.read_csv(f, usecols=["create_time", "sum_open_interest"]))
            m = pd.concat(parts)
            m.index = pd.to_datetime(m.create_time, utc=True).astype("datetime64[ns, UTC]")
            oi = m[~m.index.duplicated()].sort_index().sum_open_interest.astype(float)
            d = oi.pct_change().abs()
            corr = {}
            for pas in range(-3, 4):
                # bougie ouverte à s + pas x 5 min
                r2 = ret.copy()
                r2.index = r2.index - pd.Timedelta(minutes=5 * pas)
                x = pd.concat([d.rename("d"), r2.rename("r")], axis=1).dropna()
                corr[str(pas)] = round(float(x.d.corr(x.r, method="spearman")), 4)
            pic = max(corr, key=corr.get)
            sortie.append({"symbole": sym, "mois": f"{an}-{mo:02d}", "correlations_par_pas": corr, "pic_pas": int(pic)})
    return sortie


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=22)
    ap.add_argument("--archive-metrics", help="cache metrics : lance seulement le contrôle de l'archive")
    ap.add_argument("--archive-5m", help="cache des bougies 5 min")
    a = ap.parse_args()
    if a.archive_metrics:
        debut = datetime.now(timezone.utc)
        res = {"debut_utc": debut.isoformat(timespec="seconds"), "mesure": "pic de correlation |dOI archive| contre |rendement 5 min|",
               "resultats": alignement_archive(Path(a.archive_metrics), Path(a.archive_5m))}
        p = ICI / "resultats" / f"alignement_archive_{debut.strftime('%Y%m%dT%H%M%SZ')}.json"
        p.write_text(json.dumps(res, ensure_ascii=False, indent=1))
        for l in res["resultats"]:
            print(l["symbole"], l["mois"], "pic", l["pic_pas"], l["correlations_par_pas"])
        print("écrit :", p)
        return
    debut = datetime.now(timezone.utc)
    direct = {s: [] for s in SYMS}
    apparition = {s: {} for s in SYMS}
    fin = time.time() + a.minutes * 60
    erreurs = 0
    while time.time() < fin:
        for s in SYMS:
            try:
                r = requests.get(f"{FAPI}/fapi/v1/openInterest", params={"symbol": s}, timeout=8)
                r.raise_for_status()
                d = r.json()
                direct[s].append((d["time"] / 1000, float(d["openInterest"])))
                r = requests.get(f"{FAPI}/futures/data/openInterestHist",
                                 params={"symbol": s, "period": "5m", "limit": 3}, timeout=8)
                r.raise_for_status()
                for x in r.json():
                    apparition[s].setdefault(x["timestamp"] // 1000, (time.time(), float(x["sumOpenInterest"])))
            except (requests.RequestException, ValueError, KeyError):
                erreurs += 1
        time.sleep(10)
    # Lecture finale : une valeur publiée peut être révisée.
    res = {"debut_utc": debut.isoformat(timespec="seconds"), "fin_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "erreurs_requete": erreurs, "symboles": {}}
    for s in SYMS:
        d = direct[s]
        lignes = []
        premier = min(apparition[s])
        for ts, (vu, val) in sorted(apparition[s].items()):
            if ts == premier or not d or ts < d[0][0] - 60 or ts > d[-1][0]:
                continue  # le premier point existait déjà au lancement : son délai est inconnu
            proche = min(d, key=lambda x: abs(x[1] - val))
            exact = [x[0] for x in d if x[1] == val]
            lignes.append({
                "horodatage_hist": iso(ts), "premiere_vue": iso(vu), "delai_publication_s": round(vu - ts, 1),
                "valeur": val, "instant_direct_le_plus_proche": iso(proche[0]),
                "decalage_instant_moins_horodatage_s": round(proche[0] - ts, 1),
                "ecart_relatif": round(abs(proche[1] / val - 1), 8),
                "decalages_exacts_s": [round(e - ts, 1) for e in exact][:4]})
        res["symboles"][s] = {"releves_directs": len(d), "points": lignes}
    p = ICI / "resultats" / f"test_alignement_oi_{debut.strftime('%Y%m%dT%H%M%SZ')}.json"
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("écrit :", p)


if __name__ == "__main__":
    main()
