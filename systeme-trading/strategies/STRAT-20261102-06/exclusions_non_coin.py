#!/usr/bin/env python3
"""Liste des perpétuels USDT de Binance dont le sous-jacent n'est pas une crypto (actions, ETF, métaux, pétrole,
indices) : `underlyingType` différent de COIN, ou `contractType` TRADIFI_PERPETUAL, dans `fapi/v1/exchangeInfo`.

Attribut statique du contrat : le lire aujourd'hui n'apporte aucune information de prix. Point public, sans clé.
Les contrats déjà retirés d'`exchangeInfo` ne figurent pas : ils sont listés à part s'ils sont connus.

Usage : python -B exclusions_non_coin.py      -> exclusions_non_coin.json
"""
import datetime as dt
import json
import sys
from pathlib import Path

import requests

URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"


def main() -> int:
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    s = r.json()["symbols"]
    non_coin = sorted(x["symbol"] for x in s if x.get("quoteAsset") == "USDT" and
                      (x.get("underlyingType", "COIN") != "COIN" or "TRADIFI" in str(x.get("contractType", ""))))
    types = {}
    for x in s:
        if x["symbol"] in non_coin:
            types.setdefault(f"{x.get('underlyingType')}/{x.get('contractType')}", []).append(x["symbol"])
    out = {"source": URL, "lu_le_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "symboles": non_coin, "par_type": types, "contrats_examines": len(s)}
    Path(__file__).resolve().parent.joinpath("exclusions_non_coin.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(non_coin)} contrats non crypto sur {len(s)} : " + ", ".join(f"{k} {len(v)}" for k, v in types.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
