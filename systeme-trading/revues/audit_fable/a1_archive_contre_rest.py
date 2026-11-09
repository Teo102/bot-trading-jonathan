#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A1 : l'heure d'une ligne de l'archive metrics désigne-t-elle l'intérêt ouvert à cette heure ?

Intérêt ouvert seulement : aucun prix, aucun rendement. Jours de novembre 2026, donc hors de tout bloc de la fiche.
L'archive est lue par le lecteur même de STRAT-08 (`donnees_1m.lire_metrics_contrats`), pour auditer ce que le code voit.
Pour chaque ligne d'archive d'heure t, on cherche le décalage k tel que archive(t) = REST(t + k x 5 min).
k = 0 : horodatage juste. k = +1 : l'archive est datée 5 minutes trop tôt (lire archive(t) en t lit l'avenir).

Usage : python3 -B a1_archive_contre_rest.py
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent.parent / "strategies" / "STRAT-20261109-08"))
import donnees_1m as d1  # noqa: E402

SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "SUIUSDT", "WIFUSDT", "ENAUSDT", "1000PEPEUSDT",
        "AVAXUSDT", "LINKUSDT", "ARBUSDT", "TIAUSDT", "ORDIUSDT", "NEARUSDT", "APTUSDT"]
JOURS = ["2026-11-03", "2026-11-05", "2026-11-07"]
s = requests.Session()
R, total = {}, {k: 0 for k in range(-2, 3)}
n_total = 0
for sym in SYMS:
    for j in JOURS:
        z = s.get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{j}.zip", timeout=60)
        if z.status_code != 200:
            R[f"{sym} {j}"] = "archive absente"; continue
        arch = d1.lire_metrics_contrats(z.content)
        a = int(pd.Timestamp(j).timestamp() * 1000) - 15 * 60000
        rest = {}
        for debut in (a, a + 400 * 300000):  # deux pages de 400 points de 5 minutes
            h = s.get("https://fapi.binance.com/futures/data/openInterestHist",
                      params={"symbol": sym, "period": "5m", "limit": 500, "startTime": debut, "endTime": debut + 400 * 300000}, timeout=20).json()
            for p in h:
                rest[pd.Timestamp(int(p["timestamp"]), unit="ms")] = float(p["sumOpenInterest"])
            time.sleep(0.25)
        rest = pd.Series(rest).sort_index()
        egal = {}
        for k in range(-2, 3):
            r = rest.reindex(arch.index + pd.Timedelta(minutes=5 * k))
            ok = r.notna().to_numpy()
            egal[k] = int(((abs(arch.to_numpy() - r.to_numpy()) <= 1e-9 * abs(arch.to_numpy())) & ok).sum())
            total[k] += egal[k]
        n_total += len(arch)
        R[f"{sym} {j}"] = {"lignes_archive": int(len(arch)), "points_rest": int(len(rest)), "egalites_par_decalage": egal,
                           "premiere_heure_archive": str(arch.index.min()), "derniere_heure_archive": str(arch.index.max())}
        print(sym, j, len(arch), egal, str(arch.index.min()), str(arch.index.max()), flush=True)
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
S = {"genere_utc": h, "lignes_archive": n_total, "egalites_par_decalage_k": total, "detail": R}
(ICI / "resultats" / f"a1_archive_contre_rest_{h}.json").write_text(json.dumps(S, indent=1))
print("TOTAL lignes", n_total, "égalités par décalage k (archive(t) = REST(t + 5k min)) :", total)
