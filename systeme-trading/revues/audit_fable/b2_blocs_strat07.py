#!/usr/bin/env python3
"""Audit Fable, STRAT-07, contrôle B2 : le rendement indicatif du criblage, bloc par bloc et année par année.

Même statut que B1 : épisodes déjà lus par le criblage du 09/11/2026 (financement moins coûts, sans la base), hors N,
publié quel que soit le résultat. Reproduit d'abord le chiffre publié (tri par défaut de pandas, comme le criblage).

Usage : python3 -B b2_blocs_strat07.py <dossier des episodes_*.csv>"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ICI = Path(__file__).resolve().parent
DEBUT, FIN = pd.Timestamp("2021-01-01"), pd.Timestamp("2025-07-28 02:00:00")
BLOCS = {"developpement (2021-2023)": ("2021-01-01", "2024-01-01"), "validation (2024 au 27/07/2025)": ("2024-01-01", "2025-07-28"),
         "2021": ("2021-01-01", "2022-01-01"), "2022": ("2022-01-01", "2023-01-01"), "2023": ("2023-01-01", "2024-01-01"),
         "2024": ("2024-01-01", "2025-01-01"), "2025 (au 27/07)": ("2025-01-01", "2025-07-28"),
         "2022 au 27/07/2025": ("2022-01-01", "2025-07-28")}


def pris_comme_le_criblage(e, k=10):
    pris, libres = [], []
    for r in e.sort_values("debut").itertuples():  # tri par défaut (non stable), comme criblage_strat07.portefeuille
        libres = [f for f in libres if f > r.debut]
        if len(libres) < k:
            pris.append(r.Index); libres.append(r.fin)
    return pris


R = {}
for cle in ("entree_50_sortie_10", "entree_30_sortie_10"):
    e = pd.read_csv(Path(sys.argv[1]) / f"episodes_{cle}.csv", parse_dates=["debut", "fin"])
    p = e.loc[pris_comme_le_criblage(e)]
    total = float(p["net"].sum()) / 20 / ((FIN - DEBUT).days / 365.25)
    R[cle] = {"episodes_pris": int(len(p)), "rendement_annuel_capital_reproduit": round(total, 5), "par_periode": {}}
    print(cle, "épisodes pris", len(p), "rendement reproduit", f"{total:.4%}")
    for nom, (a, b) in BLOCS.items():
        x = p[(p["debut"] >= a) & (p["debut"] < b)]
        ans = (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25
        r = float(x["net"].sum()) / 20 / ans
        R[cle]["par_periode"][nom] = {"episodes_pris": int(len(x)), "points_de_capital": round(float(x["net"].sum()) / 20, 4), "rendement_annualise": round(r, 4)}
        print(f"   {nom:34s} épisodes pris {len(x):4d}   {float(x['net'].sum())/20:+.2%} du capital   {r:+.2%}/an")
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"b2_blocs_strat07_{h}.json").write_text(json.dumps({"genere_utc": h, "note": "épisodes rattachés au bloc de leur début", **R}, indent=1, ensure_ascii=False))
