#!/usr/bin/env python3
"""Téléchargement des données de STRAT-20261123-10 (H34), BLOC DE DÉVELOPPEMENT SEULEMENT (2021-01-01 au 2024-12-31).

Données seulement, aucun rendement calculé. Le hors échantillon (2025-2026) n'est pas téléchargé : il ne s'ouvre
qu'une fois, sur accord écrit de Jonathan et Téo.

- transactions des options BTC de Deribit le vendredi de 08:00 à 10:00 UTC (fenêtre de décision), une archive
  compressée par vendredi (horodatage, instrument, prix, prix de marque, volatilité implicite, indice, quantité, sens) ;
- prix de livraison quotidiens de l'indice btc_usd (règlement des options à 08:00 UTC).
Sources publiques : history.deribit.com et www.deribit.com.

Usage : python -I -B telecharger_deribit10.py --sorties /root/strat10_data
"""
import argparse, csv, datetime as dt, gzip, json, time
from pathlib import Path
import requests

UTC = dt.timezone.utc
DEBUT, FIN = dt.date(2021, 1, 1), dt.date(2024, 12, 31)          # verrou du bloc de développement
CHAMPS = ["timestamp", "instrument_name", "price", "mark_price", "iv", "index_price", "amount", "direction", "trade_id"]
S = requests.Session()


def appel(hote, methode, params):
    for essai in range(6):
        try:
            r = S.get(f"https://{hote}/api/v2/public/{methode}", params=params, timeout=120)
            j = r.json()
            if "result" in j:
                time.sleep(0.3)
                return j["result"]
        except (requests.RequestException, ValueError):
            pass
        time.sleep(3 + 5 * essai)
    raise RuntimeError(f"{hote} {methode} {params}")


def vendredis():
    d = DEBUT + dt.timedelta(days=(4 - DEBUT.weekday()) % 7)
    while d <= FIN:
        yield d
        d += dt.timedelta(weeks=1)


def transactions(debut_ms, fin_ms):
    vus, out, debut = set(), [], debut_ms
    while True:
        r = appel("history.deribit.com", "get_last_trades_by_currency_and_time",
                  {"currency": "BTC", "kind": "option", "start_timestamp": debut, "end_timestamp": fin_ms, "count": 1000, "sorting": "asc"})
        lot = r.get("trades", [])
        for t in lot:
            if t["trade_id"] not in vus:
                vus.add(t["trade_id"])
                out.append(t)
        if not r.get("has_more") or not lot:
            return out
        dernier = lot[-1]["timestamp"]
        debut = dernier if dernier > debut else debut + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sorties", required=True)
    a = ap.parse_args()
    out = Path(a.sorties)
    (out / "transactions").mkdir(parents=True, exist_ok=True)
    liv, offset = {}, 0
    while True:
        r = appel("www.deribit.com", "get_delivery_prices", {"index_name": "btc_usd", "offset": offset, "count": 1000})
        lot = r.get("data", [])
        for x in lot:
            if DEBUT.isoformat() <= x["date"] <= (FIN + dt.timedelta(days=10)).isoformat():   # + l'échéance du dernier vendredi
                liv[x["date"]] = x["delivery_price"]
        offset += len(lot)
        if not lot or offset >= r.get("records_total", 0):
            break
    (out / "livraisons_btc_usd.json").write_text(json.dumps(dict(sorted(liv.items()))))
    journal = []
    for v in vendredis():
        f = out / "transactions" / f"{v}.csv.gz"
        if f.exists():
            continue
        t0 = dt.datetime(v.year, v.month, v.day, 8, tzinfo=UTC)
        tr = transactions(int(t0.timestamp() * 1000), int((t0 + dt.timedelta(hours=2)).timestamp() * 1000) - 1)
        with gzip.open(f, "wt", newline="") as g:
            w = csv.DictWriter(g, fieldnames=CHAMPS, extrasaction="ignore")
            w.writeheader()
            w.writerows(tr)
        journal.append({"vendredi": str(v), "transactions": len(tr)})
        print(v, len(tr), flush=True)
    (out / f"journal_telechargement_{dt.datetime.now(UTC):%Y%m%dT%H%M%SZ}.json").write_text(json.dumps(
        {"bloc": [str(DEBUT), str(FIN)], "livraisons": len(liv), "vendredis": journal}, indent=1))


if __name__ == "__main__":
    main()
