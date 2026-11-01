#!/usr/bin/env python3
"""Suivi en temps réel des taux de financement (STRAT-20261031-02).

Lecture seule : aucun ordre, aucune clé, points d'accès publics uniquement.
L'envoi POST vers Hyperliquid est une simple requête de lecture de son API /info.

Le taux affiché est le prochain taux estimé par la plateforme, pas un taux réglé,
sauf mention contraire dans la colonne `nature`. Une plateforme en échec est signalée
et marquée en lacune : aucune valeur n'est remplacée ni estimée.

Le repère `seuil` compare seulement le taux instantané aux seuils de la fiche. La règle
de la fiche porte sur une moyenne de 24 h de taux réglés. Ce n'est ni un signal ni un conseil.

Usage :
  tracker_funding.py --once
  tracker_funding.py --intervalle 60
  tracker_funding.py --paires BTC ETH SOL --plateformes binance bybit --iterations 10
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent
HEURES_AN = 365.0 * 24.0
DELAI = 15
COLONNES = ["horodatage_utc", "plateforme", "paire", "nature", "taux_periode_pct", "intervalle_h", "annualise_pct",
            "prix_marque", "prix_indice", "base_pb", "prochain_reglement_utc", "repere_seuil", "source"]


def utc_ms(ms) -> str:
    if not ms:
        return ""
    return datetime.fromtimestamp(int(ms) / 1000.0, timezone.utc).strftime("%Y-%m-%d %H:%M")


def get(url, **params):
    r = requests.get(url, params=params, timeout=DELAI, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def ligne(pf, base, nature, taux, intervalle, marque, indice, prochain, source):
    return {"plateforme": pf, "paire": base, "nature": nature, "taux": taux, "intervalle": intervalle,
            "marque": marque, "indice": indice, "prochain": prochain, "source": source}


def binance(paires):
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    tout = {x["symbol"]: x for x in get(url)}
    # fundingInfo ne liste que les paires dont l'intervalle ou les bornes ont été ajustés ; sinon 8 h.
    infos = {x["symbol"]: x for x in get("https://fapi.binance.com/fapi/v1/fundingInfo")}
    res = []
    for b in paires:
        s = tout.get(f"{b}USDT")
        if s is None:
            continue
        iv = float(infos.get(f"{b}USDT", {}).get("fundingIntervalHours", 8))
        res.append(ligne("binance", b, "estime", float(s["lastFundingRate"]), iv, float(s["markPrice"]),
                         float(s["indexPrice"]), s["nextFundingTime"], url))
    return res


def bybit(paires):
    url = "https://api.bybit.com/v5/market/tickers"
    d = get(url, category="linear")
    if d.get("retCode") != 0:
        raise RuntimeError(d.get("retMsg"))
    tout = {x["symbol"]: x for x in d["result"]["list"]}
    res = []
    for b in paires:
        s = tout.get(f"{b}USDT")
        if s is None or not s.get("fundingRate"):
            continue
        iv = float(s.get("fundingIntervalHour") or 8)
        res.append(ligne("bybit", b, "estime", float(s["fundingRate"]), iv, float(s["markPrice"]),
                         float(s["indexPrice"]), s.get("nextFundingTime"), url))
    return res


def okx(paires):
    url = "https://www.okx.com/api/v5/public/funding-rate"
    res = []
    for b in paires:
        d = get(url, instId=f"{b}-USDT-SWAP")
        if d.get("code") != "0" or not d.get("data"):
            continue
        s = d["data"][0]
        t0, t1 = int(s["fundingTime"]), int(s["nextFundingTime"])
        iv = (t1 - t0) / 3600000.0 if t1 > t0 else 8.0
        m = get("https://www.okx.com/api/v5/public/mark-price", instType="SWAP", instId=f"{b}-USDT-SWAP")
        i = get("https://www.okx.com/api/v5/market/index-tickers", instId=f"{b}-USDT")
        marque = float(m["data"][0]["markPx"]) if m.get("data") else None
        indice = float(i["data"][0]["idxPx"]) if i.get("data") else None
        res.append(ligne("okx", b, "estime", float(s["fundingRate"]), iv, marque, indice, t0, url))
        time.sleep(0.1)
    return res


def hyperliquid(paires):
    url = "https://api.hyperliquid.xyz/info"
    r = requests.post(url, json={"type": "metaAndAssetCtxs"}, timeout=DELAI)
    r.raise_for_status()
    meta, ctx = r.json()
    noms = {a["name"]: i for i, a in enumerate(meta["universe"])}
    prochain = (int(time.time() // 3600) + 1) * 3600 * 1000
    res = []
    for b in paires:
        if b not in noms:
            continue
        c = ctx[noms[b]]
        res.append(ligne("hyperliquid", b, "estime", float(c["funding"]), 1.0, float(c["markPx"]),
                         float(c["oraclePx"]), prochain, url))
    return res


def cryptocom(paires):
    # Valeur horaire publiée ; contrat à marge USD, pas USDT.
    url = "https://api.crypto.com/exchange/v1/public/get-valuations"
    res = []
    for b in paires:
        inst = f"{b}USD-PERP"
        try:
            d = get(url, instrument_name=inst, valuation_type="funding_hist", count=1)
        except requests.HTTPError:
            continue  # instrument absent
        rows = d.get("result", {}).get("data") or []
        if d.get("code") != 0 or not rows:
            continue
        marque = indice = None
        try:
            m = get(url, instrument_name=inst, valuation_type="mark_price", count=1)["result"]["data"]
            i = get(url, instrument_name=inst, valuation_type="index_price", count=1)["result"]["data"]
            marque = float(m[0]["v"]) if m else None
            indice = float(i[0]["v"]) if i else None
        except (requests.RequestException, KeyError, ValueError):
            pass  # le taux reste exploitable, la base reste vide
        res.append(ligne("cryptocom", b, "dernier_regle", float(rows[0]["v"]), 1.0, marque, indice, None, url))
        time.sleep(0.1)
    return res


PLATEFORMES = {"binance": binance, "bybit": bybit, "okx": okx, "hyperliquid": hyperliquid, "cryptocom": cryptocom}


def statut_binance():
    """Statut public général. Il ne dit pas si les retraits sont réellement ouverts."""
    try:
        d = get("https://api.binance.com/sapi/v1/system/status")
        return f"code {d.get('status')}, {d.get('msg')}"
    except (requests.RequestException, ValueError) as e:
        return f"lacune ({e})"


def relever(paires, plateformes, entree, sortie):
    horo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lignes, lacunes = [], []
    for pf in plateformes:
        try:
            res = PLATEFORMES[pf](paires)
        except Exception as e:  # une plateforme en échec ne bloque pas les autres
            lacunes.append(f"{pf} : {type(e).__name__} {str(e)[:160]}")
            continue
        vues = {x["paire"] for x in res}
        for b in paires:
            if b not in vues:
                lacunes.append(f"{pf} {b} : absent de la réponse")
        for x in res:
            ann = x["taux"] * 100.0 * HEURES_AN / x["intervalle"]
            base = (x["marque"] / x["indice"] - 1.0) * 1e4 if x["marque"] and x["indice"] else None
            repere = "au-dessus entree" if ann >= entree else ("sous sortie" if ann < sortie else "entre seuils")
            lignes.append({
                "horodatage_utc": horo, "plateforme": x["plateforme"], "paire": x["paire"], "nature": x["nature"],
                "taux_periode_pct": round(x["taux"] * 100.0, 6), "intervalle_h": x["intervalle"],
                "annualise_pct": round(ann, 3), "prix_marque": x["marque"], "prix_indice": x["indice"],
                "base_pb": round(base, 2) if base is not None else "", "prochain_reglement_utc": utc_ms(x["prochain"]),
                "repere_seuil": repere, "source": x["source"]})
    return horo, lignes, lacunes


def afficher(horo, lignes, lacunes, statut):
    print(f"\n{horo} UTC, lecture seule, statut système Binance : {statut}")
    print(f"{'plateforme':<12}{'paire':<6}{'nature':<14}{'taux %':>10}{'h':>4}{'%/an':>9}{'marque':>12}"
          f"{'base pb':>9}  {'prochain':<17}repère")
    for x in sorted(lignes, key=lambda v: (v["paire"], v["plateforme"])):
        marque = f"{x['prix_marque']:.4f}" if x["prix_marque"] else "[lacune]"
        base = f"{x['base_pb']:.2f}" if x["base_pb"] != "" else "[lacune]"
        print(f"{x['plateforme']:<12}{x['paire']:<6}{x['nature']:<14}{x['taux_periode_pct']:>10.5f}"
              f"{x['intervalle_h']:>4.0f}{x['annualise_pct']:>9.2f}{marque:>12}{base:>9}  "
              f"{x['prochain_reglement_utc']:<17}{x['repere_seuil']}")
    for l in lacunes:
        print(f"  LACUNE {l}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paires", nargs="+", default=["BTC", "ETH", "XRP", "BNB", "ADA", "LINK", "SOL"])
    ap.add_argument("--plateformes", nargs="+", default=list(PLATEFORMES), choices=list(PLATEFORMES))
    ap.add_argument("--once", action="store_true", help="un seul relevé")
    ap.add_argument("--intervalle", type=float, default=60.0, help="secondes entre deux relevés")
    ap.add_argument("--iterations", type=int, default=0, help="nombre de relevés, 0 = sans limite")
    ap.add_argument("--seuil-entree", type=float, default=10.0, help="repère de la fiche, %%/an")
    ap.add_argument("--seuil-sortie", type=float, default=3.0, help="repère de la fiche, %%/an")
    ap.add_argument("--csv", type=Path, default=None, help="défaut : resultats/<horodatage>_tracker_funding.csv")
    a = ap.parse_args()

    debut = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    chemin = a.csv or ICI / "resultats" / f"{debut}_tracker_funding.csv"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    nouveau = not chemin.exists()
    n, total = 0, 0
    with chemin.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        if nouveau:
            w.writeheader()
        try:
            while True:
                horo, lignes, lacunes = relever(a.paires, a.plateformes, a.seuil_entree, a.seuil_sortie)
                afficher(horo, lignes, lacunes, statut_binance() if "binance" in a.plateformes else "non demandé")
                w.writerows(lignes)
                f.flush()
                total += len(lignes)
                n += 1
                if a.once or (a.iterations and n >= a.iterations):
                    break
                time.sleep(a.intervalle)
        except KeyboardInterrupt:
            print("\nArrêt demandé.")
    print(f"\n{n} relevé(s), {total} ligne(s) dans {chemin}")
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
