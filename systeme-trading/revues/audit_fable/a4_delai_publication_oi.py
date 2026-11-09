#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A4 : à quel instant réel correspond un point d'intérêt ouvert publié, et quand apparaît-il ?

Intérêt ouvert seulement : aucun prix, aucun rendement. API publique Binance, sans clé.
- relève l'intérêt ouvert en direct (/fapi/v1/openInterest) toutes les ~6 s pour quelques symboles ;
- relève en parallèle le dernier point de /futures/data/openInterestHist (5 min) et l'heure où il apparaît ;
- à la fin, cherche pour chaque point publié l'instant du relevé direct dont la valeur est égale (ou la plus proche).

Usage : python3 -B a4_delai_publication_oi.py --minutes 26
"""
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
import requests

FAPI = "https://fapi.binance.com"
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "SUIUSDT", "WIFUSDT", "ENAUSDT", "1000PEPEUSDT"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--minutes", type=float, default=26); a = ap.parse_args()
    s = requests.Session()
    direct = {x: [] for x in SYMS}      # (heure locale s, heure serveur ms, valeur)
    publies = {x: {} for x in SYMS}     # horodatage ms -> (valeur, première heure locale où il est vu)
    fin = time.time() + a.minutes * 60
    while time.time() < fin:
        for x in SYMS:
            try:
                r = s.get(f"{FAPI}/fapi/v1/openInterest", params={"symbol": x}, timeout=5).json()
                direct[x].append((time.time(), int(r["time"]), r["openInterest"]))
                h = s.get(f"{FAPI}/futures/data/openInterestHist", params={"symbol": x, "period": "5m", "limit": 2}, timeout=5).json()
                for p in h:
                    publies[x].setdefault(int(p["timestamp"]), (p["sumOpenInterest"], time.time()))
            except Exception as e:  # réseau : on continue
                print("erreur", x, e, flush=True)
        time.sleep(3)
    R = {"debut_utc": None, "symboles": {}}
    for x in SYMS:
        lignes = []
        vus = sorted(publies[x])
        for ts in vus[1:]:  # le premier point était déjà publié au démarrage : délai inconnu
            val, vu = publies[x][ts]
            egal = [d for d in direct[x] if float(d[2]) == float(val)]
            proche = min(direct[x], key=lambda d: abs(float(d[2]) - float(val)))
            lignes.append({"horodatage_utc": datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%H:%M:%S"),
                           "delai_apparition_s": round(vu - ts / 1000, 1),
                           "egalites_exactes": len(egal),
                           "egal_de_s": round(egal[0][1] / 1000 - ts / 1000, 1) if egal else None,
                           "egal_a_s": round(egal[-1][1] / 1000 - ts / 1000, 1) if egal else None,
                           "plus_proche_decalage_s": round(proche[1] / 1000 - ts / 1000, 1),
                           "plus_proche_ecart_relatif": abs(float(proche[2]) / float(val) - 1)})
        R["symboles"][x] = {"releves_directs": len(direct[x]), "valeurs_distinctes": len({d[2] for d in direct[x]}), "points": lignes}
    h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(__file__).resolve().parent / "resultats" / f"a4_delai_publication_oi_{h}.json"
    out.write_text(json.dumps(R, indent=1))
    print(out)


if __name__ == "__main__":
    main()
