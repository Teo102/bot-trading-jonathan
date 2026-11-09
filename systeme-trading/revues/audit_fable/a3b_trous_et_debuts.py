#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A3 bis (intérêt ouvert seulement, aucun prix).
1. Heures exactes des points manquants des fichiers metrics les jours de krach de 2021.
2. Première date d'archive metrics par symbole (liste du dépôt public), pour un échantillon de 40 symboles.
Usage : python3 -B a3b_trous_et_debuts.py"""
import io, json, re, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
s = requests.Session()


def get(url, **kw):
    for essai in range(5):
        try:
            return s.get(url, timeout=60, **kw)
        except requests.exceptions.ConnectionError:
            time.sleep(2 + essai)
    raise RuntimeError(url)


R = {"trous": {}, "debuts": {}}
print("== 1. Points manquants (heure UTC de la ligne absente)")
for sym, j in [("BTCUSDT", "2021-05-19"), ("BTCUSDT", "2021-09-07"), ("BTCUSDT", "2021-12-04"), ("ETHUSDT", "2021-12-04"),
               ("SOLUSDT", "2021-12-04"), ("BTCUSDT", "2021-12-10"), ("SOLUSDT", "2021-12-10"), ("BTCUSDT", "2022-06-13"), ("SOLUSDT", "2022-06-13")]:
    r = get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{j}.zip")
    if r.status_code != 200:
        print(sym, j, "archive absente"); continue
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f)
    tm = pd.to_datetime(df["create_time"]).dt.round("min")
    grille = pd.date_range(j, periods=288, freq="5min")
    manq = [t.strftime("%H:%M") for t in grille[~grille.isin(tm)]]
    R["trous"][f"{sym} {j}"] = manq
    print(sym, j, "lignes", len(df), "manquants", manq)

print("== 2. Première archive metrics par symbole")
SYMS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT",
        "MATICUSDT", "ATOMUSDT", "NEARUSDT", "FTMUSDT", "SANDUSDT", "AXSUSDT", "GALAUSDT", "LUNAUSDT", "FILUSDT", "EOSUSDT", "TRXUSDT",
        "ETCUSDT", "UNIUSDT", "AAVEUSDT", "SUSHIUSDT", "CRVUSDT", "DYDXUSDT", "MANAUSDT", "1000SHIBUSDT", "ICPUSDT", "THETAUSDT",
        "VETUSDT", "ALGOUSDT", "XLMUSDT", "XTZUSDT", "KSMUSDT", "ZECUSDT", "CHZUSDT"]
base = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
for sym in SYMS:
    r = get(base, params={"delimiter": "/", "prefix": f"data/futures/um/daily/metrics/{sym}/", "max-keys": 5})
    dates = re.findall(rf"{sym}-metrics-(\d{{4}}-\d{{2}}-\d{{2}})\.zip<", r.text)
    R["debuts"][sym] = min(dates) if dates else None
    print(sym, R["debuts"][sym])
d = pd.Series(R["debuts"]).dropna()
print("Symboles dont la première archive est postérieure au 01/01/2021 :", int((d > "2021-01-01").sum()), "sur", len(d))
print("Répartition des débuts :", d.str.slice(0, 7).value_counts().sort_index().to_dict())
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"a3b_trous_et_debuts_{h}.json").write_text(json.dumps({"genere_utc": h, **R}, indent=1))
