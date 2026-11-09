#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A5 : effet de l'horodatage non corrigé sur la détection (aucune issue de position lue).

Sur deux mois du bloc de validation (2024-08 et 2024-12) et 8 alts, le détecteur même de la stratégie
(`detection_cascades.candidats`, puis `filtrer` à la base X 4 %, Y 3 %) est lancé deux fois :
- « brut » : heures de l'archive telles que le code de STRAT-08 les lit aujourd'hui ;
- « corrigé » : heures de l'archive + 5 minutes (heure réelle de l'observation depuis mars 2024, contrôles A1 et A2).
Seuls la chute passée (15 minutes avant t) et l'intérêt ouvert sont lus, comme dans le contrôle du § 5 de la fiche.

Usage : python3 -B a5_effet_sur_detection.py"""
import io, json, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent.parent / "strategies" / "STRAT-20261109-08"))
sys.path.insert(0, str(ICI.parent.parent / "strategies" / "STRAT-20261031-03"))
import detection_cascades as dc  # noqa: E402
import donnees_1m as d1  # noqa: E402
import donnees_binance as db  # noqa: E402

SYMS = ["SOLUSDT", "DOGEUSDT", "AVAXUSDT", "NEARUSDT", "ARBUSDT", "SUIUSDT", "1000PEPEUSDT", "WIFUSDT"]
MOIS = ["2024-08", "2024-12"]
CINQ = pd.Timedelta(minutes=5)


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


lignes, tot = [], {"brut": 0, "corrige": 0, "communs": 0, "brut_seul": 0, "corrige_seul": 0, "brut_lache": 0, "corrige_lache": 0}
for sym in SYMS:
    for m in MOIS:
        r = get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1m/{sym}-1m-{m}.zip")
        if r.status_code != 200:
            print(sym, m, "klines absentes"); continue
        k1 = db.lire_klines(r.content)
        jours = [d.date().isoformat() for d in pd.date_range(f"{m}-01", pd.Period(m).end_time.normalize(), freq="D")]
        with ThreadPoolExecutor(4) as ex:
            oi = pd.concat([x for x in ex.map(oi_jour, [(sym, j) for j in jours]) if x is not None]).sort_index()
        oi = oi[~oi.index.duplicated(keep="last")]
        oi_c = oi.copy(); oi_c.index = oi_c.index + CINQ
        cb, cc_ = dc.candidats(k1, oi), dc.candidats(k1, oi_c)
        b, c = set(dc.filtrer(cb, 0.04, 0.03)["t"]), set(dc.filtrer(cc_, 0.04, 0.03)["t"])
        x = {"symbole": sym, "mois": m, "brut": len(b), "corrige": len(c), "communs": len(b & c), "brut_seul": len(b - c),
             "corrige_seul": len(c - b), "brut_lache": len(cb), "corrige_lache": len(cc_)}
        lignes.append(x)
        for kk in tot:
            tot[kk] += x[kk]
        print(x, flush=True)
print("TOTAL (instants de détection à la base X 4 %, Y 3 %, avant pause de 4 h) :", tot)
if tot["brut"]:
    print(f"Part des détections brutes absentes de la version corrigée : {tot['brut_seul'] / tot['brut']:.1%}")
if tot["corrige"]:
    print(f"Part des détections corrigées absentes de la version brute : {tot['corrige_seul'] / tot['corrige']:.1%}")
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"a5_effet_sur_detection_{h}.json").write_text(json.dumps({"genere_utc": h, "total": tot, "detail": lignes}, indent=1))
