#!/usr/bin/env python3
"""Test de faisabilité d'un univers reconstruit à la date (point-in-time).

Ne construit pas l'univers définitif. Mesure ce que les données publiques
permettent. Points d'accès publics en lecture seulement.

Tests réels
1. Contrats perpétuels USDT crypto présents dans exchangeInfo, par statut.
2. Accès aux bougies de jetons morts ou renommés, listés ou non dans exchangeInfo.
3. Accès à l'archive publique data.binance.vision pour les mêmes jetons.
4. Classement par volume médian sur les 30 jours précédant chaque date test,
   calculé sur exchangeInfo seul puis sur exchangeInfo plus la liste de l'archive.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screener_univers import BINANCE, ClientPublic, iso, log, maintenant  # noqa: E402

DATES_TEST = ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01"]
TOP = 30
JETONS_TEMOINS = [
    "LUNAUSDT", "FTTUSDT", "SRMUSDT", "TOMOUSDT", "BTSUSDT", "SCUSDT", "RAYUSDT", "HNTUSDT", "ANCUSDT", "CVCUSDT",
    "BTCSTUSDT", "KEEPUSDT", "DGBUSDT", "COCOSUSDT", "NUUSDT", "MATICUSDT", "FTMUSDT", "EOSUSDT", "OCEANUSDT", "AGIXUSDT",
]
SORTIES = Path(__file__).resolve().parent / "resultats"


def main() -> int:
    c = ClientPublic()
    debut = iso(maintenant())
    ei = c.get(f"{BINANCE}/fapi/v1/exchangeInfo")
    perps = [s for s in ei["symbols"] if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT" and s.get("underlyingType") == "COIN"]
    par_statut = pd.Series([s["status"] for s in perps]).value_counts().to_dict()
    connus = {s["symbol"]: s for s in perps}

    log("Jetons témoins")
    temoins = []
    for sym in JETONS_TEMOINS:
        l = {"symbole": sym, "dans_exchangeinfo": sym in connus, "statut": connus.get(sym, {}).get("status")}
        try:
            k = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "startTime": 0, "limit": 1})
            l["premiere_bougie"] = iso(k[0][0])[:10] if k else None
            k2 = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "limit": 1})
            l["derniere_bougie"] = iso(k2[0][0])[:10] if k2 else None
            l["klines_fapi"] = bool(k)
        except Exception as e:
            l["klines_fapi"] = False
            l["erreur_klines"] = str(e)[:120]
        url = f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1d/{sym}-1d-2022-01.zip"
        try:
            r = c.s.head(url, timeout=20)
            l["archive_vision_2022_01_http"] = r.status_code
        except Exception as e:
            l["archive_vision_2022_01_http"] = f"erreur {type(e).__name__}"
        temoins.append(l)
        log(f"  {l}")

    # Listing complet de l'archive publique (S3), pagination par marqueur
    archive = {"pages": 0}
    symboles_archive: list[str] = []
    marqueur = ""
    try:
        while True:
            url = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/klines/"
            if marqueur:
                url += f"&marker={marqueur}"
            r = c.s.get(url, timeout=90)
            r.raise_for_status()
            symboles_archive += re.findall(r"<Prefix>data/futures/um/monthly/klines/([^/<]+)/</Prefix>", r.text)
            archive["pages"] += 1
            m = re.search(r"<NextMarker>([^<]+)</NextMarker>", r.text)
            if "<IsTruncated>true" not in r.text or not m:
                break
            marqueur = m.group(1)
        archive["n_symboles"] = len(symboles_archive)
    except Exception as e:
        archive["erreur"] = f"{type(e).__name__} {e}"
    log(f"Archive {archive}")
    non_crypto = {s["symbol"] for s in ei["symbols"] if s.get("underlyingType") != "COIN"}
    absents = sorted(x for x in set(symboles_archive) - set(connus) if x.endswith("USDT") and "_" not in x and x not in non_crypto)
    archive["n_perp_usdt_absents_exchangeinfo"] = len(absents)

    # Première et dernière bougie des contrats absents d'exchangeInfo
    log(f"{len(absents)} contrats de l'archive absents d'exchangeInfo")
    premieres = {}
    sans_klines = []
    for sym in absents:
        try:
            k = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "startTime": 1567296000000, "limit": 1}, delai_min=0.06)
            if k:
                premieres[sym] = k[0][0]
            else:
                sans_klines.append(sym)
        except Exception:
            sans_klines.append(sym)
    archive["n_absents_avec_klines_fapi"] = len(premieres)
    archive["n_absents_sans_klines_fapi"] = len(sans_klines)
    archive["absents_sans_klines_fapi"] = sans_klines

    # Classements à la date, avec exchangeInfo seul puis avec l'archive
    classements = {}
    for d in DATES_TEST:
        t = pd.Timestamp(d, tz="UTC")
        fin = int(t.timestamp() * 1000) - 1
        deb = int((t - pd.Timedelta(days=30)).timestamp() * 1000)
        cand = [(s["symbol"], s["status"]) for s in perps if s["onboardDate"] < fin]
        cand += [(x, "ABSENT_EXCHANGEINFO") for x, t0 in premieres.items() if t0 < fin]
        log(f"{d} : {len(cand)} contrats candidats")
        lignes = []
        for sym, statut in cand:
            try:
                k = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "startTime": deb, "endTime": fin, "limit": 31}, delai_min=0.06)
            except Exception as e:
                lignes.append({"symbole": sym, "statut_actuel": statut, "erreur": str(e)[:100]})
                continue
            if k:
                lignes.append({"symbole": sym, "statut_actuel": statut, "n_jours": len(k), "vol_median": float(np.median([float(x[7]) for x in k]))})
        df = pd.DataFrame(lignes)
        err = int(df["erreur"].notna().sum()) if "erreur" in df else 0
        df = df.dropna(subset=["vol_median"]).sort_values("vol_median", ascending=False)
        top = df.head(TOP)
        top_ei = df[df["statut_actuel"] != "ABSENT_EXCHANGEINFO"].head(TOP)
        classements[d] = {
            "n_candidats": len(cand), "n_avec_bougies": int(len(df)), "n_erreurs": err,
            "top_archive_plus_exchangeinfo": top["symbole"].tolist(),
            "top_exchangeinfo_seul": top_ei["symbole"].tolist(),
            "morts_dans_top": top[top["statut_actuel"] != "TRADING"]["symbole"].tolist(),
            "absents_exchangeinfo_dans_top": top[top["statut_actuel"] == "ABSENT_EXCHANGEINFO"]["symbole"].tolist(),
        }
        log(f"  top {TOP} : {classements[d]['top_archive_plus_exchangeinfo']}")
        log(f"  morts : {classements[d]['morts_dans_top']}")

    res = {"debut": debut, "fin": iso(maintenant()), "sources": ["Binance /fapi/v1/exchangeInfo", "Binance /fapi/v1/klines", "data.binance.vision"],
           "n_perp_usdt_crypto_exchangeinfo": len(perps), "par_statut": par_statut, "temoins": temoins, "archive_liste": archive,
           "classements_a_la_date": classements, "appels_http": c.appels, "incidents_http": c.incidents}
    SORTIES.mkdir(parents=True, exist_ok=True)
    chemin = SORTIES / f"faisabilite_pit_{debut.replace(':', '').replace('-', '')}.json"
    chemin.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Sortie {chemin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
