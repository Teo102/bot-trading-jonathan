#!/usr/bin/env python3
"""Test sur données réelles de STRAT-20261109-08 (réseau, intérêt ouvert seulement, aucun prix, aucun rendement).

Vérifie que le lecteur corrigé de la stratégie rend, pour chaque heure, la valeur que l'API publique donne à cette même
heure. Jours récents, donc hors de tout bloc. À relancer avant le gel et avant chaque essai : si Binance change un jour
la convention de l'archive, ce test échoue.

Usage : python3 -B test_reel_horodatage.py [AAAA-MM-JJ]   (un jour des 25 derniers, par défaut il y a 4 jours)"""
import datetime as dt, sys, time
from pathlib import Path
import pandas as pd, requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import donnees_1m as d1  # noqa: E402

SYMS = ["BTCUSDT", "SOLUSDT", "DOGEUSDT", "SUIUSDT", "1000PEPEUSDT", "ARBUSDT"]


def main(jour=None):
    jour = jour or (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=4)).strftime("%Y-%m-%d")
    total = ok = 0
    for sym in SYMS:
        z = requests.get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{jour}.zip", timeout=60)
        z.raise_for_status()
        lu = d1.lire_metrics_contrats(z.content)                       # heures corrigées
        a = int(pd.Timestamp(jour).timestamp() * 1000)
        api = {}
        for debut in (a - 600000, a + 300 * 300000):
            for p in requests.get("https://fapi.binance.com/futures/data/openInterestHist", timeout=20,
                                  params={"symbol": sym, "period": "5m", "limit": 500, "startTime": debut, "endTime": debut + 310 * 300000}).json():
                api[pd.Timestamp(int(p["timestamp"]), unit="ms")] = float(p["sumOpenInterest"])
            time.sleep(0.3)
        r = pd.Series(api).reindex(lu.index)
        egal = ((r - lu).abs() <= 1e-9 * lu.abs()) & r.notna()
        total += int(r.notna().sum()); ok += int(egal.sum())
        print(f"{sym} {jour} : {int(egal.sum())} égalités sur {int(r.notna().sum())} heures comparées (lecteur corrigé = API à la même heure)")
    print(f"TOTAL {ok} sur {total}")
    assert total >= 0.95 * 288 * len(SYMS), "trop peu d'heures comparées"
    assert ok == total, "le lecteur corrigé ne rend pas la valeur de l'API à la même heure : convention de l'archive à relire"
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
