#!/usr/bin/env python3
"""Contrôle en lecture publique de la profondeur à ±1 % du collecteur.

Le rapport du collecteur compare la bande déduite du jeton 0 au carnet lu du jeton 1, mais ce contrôle ne porte
que sur des mesures nulles. Ici nous prenons le rang 1 et les premiers marchés classés à mesure non nulle dont le
jeton le moins cher est le jeton 1. Nous lisons les deux carnets et nous comparons la lecture directe au calcul
de book_metrics. Aucun ordre et aucune clé. Usage : controle_miroir_1pct.py [--prefixe 20261101T001303Z] [--n 6]
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from clob_collector import book_metrics, rel_depth

GAMMA = "https://gamma-api.polymarket.com/markets"
BOOK = "https://clob.polymarket.com/book"


def levels(book: dict) -> tuple[list, list]:
    bids = sorted(((float(l["price"]), float(l["size"])) for l in book.get("bids") or []), key=lambda x: -x[0])
    asks = sorted(((float(l["price"]), float(l["size"])) for l in book.get("asks") or []), key=lambda x: x[0])
    return bids, asks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefixe", default="20261101T001303Z")
    parser.add_argument("--n", type=int, default=6)
    args = parser.parse_args()
    ranked = pd.read_csv(ROOT / f"resultats/{args.prefixe}_candidats_classes.csv", low_memory=False)
    positive = ranked[(ranked.jeton_ref_1pct == 1) & (ranked.score_rel_1pct_usd > 0)].head(args.n)
    chosen = pd.concat([ranked[ranked.rang == 1], positive])
    start = dt.datetime.now(dt.timezone.utc)
    rows = []
    for row in chosen.itertuples():
        market = requests.get(GAMMA, params={"condition_ids": row.condition_id}, timeout=30).json()[0]
        token0, token1 = json.loads(market["clobTokenIds"])
        book0 = requests.get(BOOK, params={"token_id": token0}, timeout=30).json()
        book1 = requests.get(BOOK, params={"token_id": token1}, timeout=30).json()
        metrics = book_metrics(book0)
        if not metrics or not book1.get("bids") or not book1.get("asks"):
            rows.append({"rang": int(row.rang), "question": row.question, "statut": "carnet vide"})
            continue
        read0, read1 = rel_depth(*levels(book0)), rel_depth(*levels(book1))
        direct = read1 if metrics["jeton_ref_1pct"] == 1 else read0
        rows.append({
            "rang": int(row.rang), "question": row.question, "milieu_jeton0": metrics["milieu"],
            "jeton_ref_1pct": metrics["jeton_ref_1pct"],
            "jeton0_bid_usd": read0["bid_usd"], "jeton0_ask_usd": read0["ask_usd"],
            "jeton1_bid_usd": read1["bid_usd"], "jeton1_ask_usd": read1["ask_usd"],
            "code_bid_usd": metrics["bid_usd_1pct"], "code_ask_usd": metrics["ask_usd_1pct"],
            "ecart_usd": abs(direct["bid_usd"] - metrics["bid_usd_1pct"]) + abs(direct["ask_usd"] - metrics["ask_usd_1pct"]),
        })
    end = dt.datetime.now(dt.timezone.utc)
    stamp = start.strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / f"resultats/{stamp}_controle_miroir_1pct.json"
    out.write_text(json.dumps({"debut_utc": start.isoformat(timespec="seconds"), "fin_utc": end.isoformat(timespec="seconds"),
                               "prefixe_classement": args.prefixe, "marches": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(r["rang"], r["question"][:44], {k: round(v, 2) for k, v in r.items() if k.endswith("_usd")})
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
