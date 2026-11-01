#!/usr/bin/env python3
"""Rejeu des constats d'exécution de la fiche STRAT-20261031-03 (§ 4) : ccxt et freqtrade.

Aucun backtest et aucun ordre. Configuration en dry_run, clés vides, dossier de travail temporaire.
Des fichiers téléchargés, le script ne lit que les noms, les dates et les volumes, jamais les prix.

Usage : python audit_execution.py --travail DOSSIER_VIDE
Sortie : resultats/audit_execution_<horodatage UTC>.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import ccxt
import freqtrade
import pandas as pd

SORTIES = Path(__file__).resolve().parent / "resultats"
PAIRES = ["BTC/USDT:USDT", "FTT/USDT:USDT", "SC/USDT:USDT", "LUNA/USDT:USDT", "SRM/USDT:USDT"]
FREQTRADE = Path(sys.executable).parent / "freqtrade"


def horo() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def config(allow_inactive: bool) -> dict:
    return {
        "dry_run": True, "trading_mode": "futures", "margin_mode": "isolated", "stake_currency": "USDT", "stake_amount": 100, "max_open_trades": 1,
        "exchange": {"name": "binance", "key": "", "secret": "", "pair_whitelist": PAIRES, "pair_blacklist": []},
        "pairlists": [{"method": "StaticPairList", "allow_inactive": allow_inactive}],
        "entry_pricing": {"price_side": "same"}, "exit_pricing": {"price_side": "same"},
    }


def lancer(args: list[str], travail: Path) -> dict:
    r = subprocess.run([str(FREQTRADE), *args], cwd=travail, capture_output=True, text=True, timeout=540)
    tout = r.stdout + r.stderr
    return {
        "code": r.returncode,
        "lignes_erreur": [x for x in tout.splitlines() if " - ERROR - " in x][:20],
        "lignes_luna": [x for x in tout.splitlines() if "LUNA" in x][:20],
        "fin_de_sortie": tout[-1500:],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--travail", type=Path, required=True)
    a = p.parse_args()
    a.travail.mkdir(parents=True, exist_ok=True)
    debut = horo()

    m = ccxt.binanceusdm().load_markets()
    swaps = {x["id"]: x for x in m.values() if x.get("swap") and x.get("quote") == "USDT" and x.get("settle") == "USDT"}
    res: dict = {"script": "audit_execution.py", "debut_utc": debut, "versions": {"ccxt": ccxt.__version__, "freqtrade": freqtrade.__version__}}
    res["ccxt"] = {
        "horodatage": horo(), "swaps_usdt": len(swaps), "inactifs": sum(not x["active"] for x in swaps.values()),
        "temoins": {s: ("absent" if s not in swaps else ("actif" if swaps[s]["active"] else "inactif")) for s in ["FTTUSDT", "SCUSDT", "RAYUSDT", "OMGUSDT", "LUNAUSDT", "SRMUSDT", "TOMOUSDT"]},
    }

    lancer(["create-userdir", "--userdir", str(a.travail / "ud")], a.travail)
    res["test_pairlist"] = {}
    for inactif in (False, True):
        chemin = a.travail / f"config_{inactif}.json"
        chemin.write_text(json.dumps(config(inactif)))
        res["test_pairlist"][f"allow_inactive_{str(inactif).lower()}"] = {"horodatage": horo(), **lancer(
            ["test-pairlist", "-c", str(chemin), "--userdir", str(a.travail / "ud"), "--print-json"], a.travail)}

    res["download_data"] = {"horodatage": horo(), **lancer(
        ["download-data", "-c", str(a.travail / "config_True.json"), "--userdir", str(a.travail / "ud"), "--include-inactive-pairs",
         "--timeframes", "1d", "--timerange", "20220101-20231231", "--pairs", *PAIRES[1:], "--data-format-ohlcv", "feather"], a.travail)}

    fichiers = {}
    for f in sorted((a.travail / "ud" / "data").rglob("*1d*.feather")):
        d = pd.read_feather(f, columns=["date", "volume"])
        d = d[pd.to_datetime(d["date"]).dt.tz_localize(None) <= "2026-10-31"]
        nz = d[d["volume"] > 0]
        dernier = pd.to_datetime(nz["date"]).max() if len(nz) else None
        fichiers[f.name] = {"lignes": len(d), "volume_nul_apres_dernier_volume": int((pd.to_datetime(d["date"]) > dernier).sum()) if dernier is not None else None,
                            "premiere": str(pd.to_datetime(d["date"]).min())[:10], "derniere": str(pd.to_datetime(d["date"]).max())[:10], "dernier_volume": str(dernier)[:10]}
    res["fichiers_telecharges"] = fichiers
    res["fin_utc"] = horo()

    SORTIES.mkdir(parents=True, exist_ok=True)
    sortie = SORTIES / f"audit_execution_{debut.replace('-', '').replace(':', '')}.json"
    sortie.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
