#!/usr/bin/env python3
"""STRAT-20261031-04 : mesure réelle de la profondeur des données publiques.

Uniquement des points d'accès publics en lecture, sans clé. Aucun calcul de rendement.
Mesure :
  1. Binance openInterestHist : ancienneté maximale acceptée (par période).
  2. Bybit /v5/market/open-interest : première date disponible (recherche dichotomique).
  3. OKX rubik open-interest-history : première date disponible.
  4. data.binance.vision : metrics (OI 5 min), bookDepth, liquidationSnapshot.
  5. Liquidations : REST publics, flux websocket (écoute courte), échantillon gratuit Tardis.
  6. Financement et bougies : première date disponible.
  7. Délai de publication de l'OI Binance.

Sortie : resultats/verif_donnees_oi_<horodatage UTC>.json et .txt
Usage : python verif_donnees_oi.py [--ws-secondes 60]
"""
import argparse
import asyncio
import gzip
import io
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent
RES = ICI / "resultats"
UNIVERS = json.loads((ICI / "parametres_geles.json").read_text())["univers"]
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
VISION = "https://data.binance.vision"
FAPI = "https://fapi.binance.com"
BYBIT = "https://api.bybit.com"
OKX = "https://www.okx.com"
UA = {"User-Agent": "recherche-donnees-publiques/1.0"}
JOUR_MS = 86_400_000


def now_ms():
    return int(time.time() * 1000)


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")


def get(url, params=None, tries=4, timeout=30):
    """GET avec reprises. Retourne (code, texte) ou (None, message d'erreur)."""
    err = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code in (429, 418, 500, 502, 503, 504):
                err = f"HTTP {r.status_code}"
                time.sleep(2 * (i + 1))
                continue
            return r.status_code, r.text
        except requests.RequestException as e:
            err = type(e).__name__
            time.sleep(2 * (i + 1))
    return None, err


# --- 1. Binance openInterestHist ---------------------------------------------
def binance_oi_accepte(symbol, period, age_h):
    start = now_ms() - int(age_h * 3_600_000)
    code, txt = get(f"{FAPI}/futures/data/openInterestHist",
                    {"symbol": symbol, "period": period, "limit": 1, "startTime": start})
    if code != 200:
        return False, code, txt[:120] if txt else txt
    data = json.loads(txt)
    return bool(data), code, data[0]["timestamp"] if data else None


def binance_oi_profondeur():
    out = {"source": f"{FAPI}/futures/data/openInterestHist", "resultats": []}
    for symbol in ["BTCUSDT", "DOGEUSDT"]:
        for period in ["5m", "1h", "1d"]:
            bas, haut = 24.0, 24.0 * 400  # heures
            ok_h, _, _ = binance_oi_accepte(symbol, period, haut)
            if ok_h:
                bas = haut
            else:
                while haut - bas > 2:
                    mid = (bas + haut) / 2
                    ok, _, _ = binance_oi_accepte(symbol, period, mid)
                    if ok:
                        bas = mid
                    else:
                        haut = mid
                    time.sleep(0.15)
            _, code, msg = binance_oi_accepte(symbol, period, haut + 24)
            out["resultats"].append({
                "symbole": symbol, "periode": period,
                "anciennete_max_acceptee_jours": round(bas / 24, 2),
                "reponse_au_dela": f"code={code} {msg}"})
    return out


def binance_oi_delai():
    code, txt = get(f"{FAPI}/futures/data/openInterestHist",
                    {"symbol": "BTCUSDT", "period": "5m", "limit": 1})
    if code != 200:
        return {"erreur": f"{code} {txt}"}
    ts = json.loads(txt)[-1]["timestamp"]
    return {"dernier_horodatage": iso(ts), "age_secondes_a_la_requete": round((now_ms() - ts) / 1000, 1),
            "note": "Un seul relevé. Il borne le délai de publication sans le mesurer sur un événement."}


# --- 2. Bybit ----------------------------------------------------------------
def bybit_a_des_donnees(symbol, debut_ms, interval="5min"):
    fin = debut_ms + 30 * JOUR_MS
    code, txt = get(f"{BYBIT}/v5/market/open-interest",
                    {"category": "linear", "symbol": symbol, "intervalTime": interval,
                     "limit": 1, "startTime": debut_ms, "endTime": fin})
    if code != 200:
        return None
    d = json.loads(txt)
    if d.get("retCode") != 0:
        return None
    lst = d["result"]["list"]
    return bool(lst)


def bybit_profondeur():
    out = {"source": f"{BYBIT}/v5/market/open-interest", "resultats": []}
    for symbol in UNIVERS:
        bas = int(datetime(2018, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        haut = now_ms() - 31 * JOUR_MS
        etat = bybit_a_des_donnees(symbol, haut)
        if etat is None:
            out["resultats"].append({"symbole": symbol, "erreur": "API en échec ou symbole absent"})
            continue
        if not etat:
            out["resultats"].append({"symbole": symbol, "erreur": "aucune donnée à J-31"})
            continue
        while haut - bas > JOUR_MS:
            mid = (bas + haut) // 2
            if bybit_a_des_donnees(symbol, mid):
                haut = mid
            else:
                bas = mid
            time.sleep(0.1)
        # La dichotomie borne la date ; le balayage par pas d'un jour donne la première valeur réelle.
        premiere = None
        for k in range(0, 45):
            d0 = haut + k * JOUR_MS
            code, txt = get(f"{BYBIT}/v5/market/open-interest",
                            {"category": "linear", "symbol": symbol, "intervalTime": "5min", "limit": 200,
                             "startTime": d0, "endTime": d0 + JOUR_MS})
            if code == 200:
                lst = json.loads(txt).get("result", {}).get("list", [])
                if lst:
                    premiere = iso(min(int(x["timestamp"]) for x in lst))
                    break
            time.sleep(0.05)
        out["resultats"].append({"symbole": symbol, "borne_dichotomique": iso(haut),
                                 "premiere_valeur_5min": premiere})
    return out


# --- 3. OKX ------------------------------------------------------------------
def okx_profondeur():
    out = {"source": f"{OKX}/api/v5/rubik/stat/contracts/open-interest-history", "resultats": []}
    for inst in ["BTC-USDT-SWAP", "DOGE-USDT-SWAP"]:
        for period in ["5m", "1H", "1D"]:
            ages = [1, 2, 5, 10, 20, 30, 45, 60, 90, 120, 180, 365, 730, 1095, 1460]
            dernier_ok = None
            for a in ages:
                debut = now_ms() - a * JOUR_MS
                code, txt = get(f"{OKX}/api/v5/rubik/stat/contracts/open-interest-history",
                                {"instId": inst, "period": period, "limit": 1,
                                 "begin": debut, "end": debut + JOUR_MS * 2})
                ok = False
                if code == 200:
                    d = json.loads(txt)
                    ok = d.get("code") == "0" and bool(d.get("data"))
                if ok:
                    dernier_ok = a
                time.sleep(0.25)
            out["resultats"].append({"instrument": inst, "periode": period,
                                     "plus_grande_anciennete_testee_avec_donnees_jours": dernier_ok,
                                     "ages_testes": ages})
    return out


# --- 4. data.binance.vision --------------------------------------------------
def s3_lister(prefix, max_pages=12):
    """Liste les clés .zip d'un préfixe. Retourne (cles, tailles, last_modified, erreur)."""
    cles, tailles, modifs = [], [], []
    marker = None
    for _ in range(max_pages):
        params = {"prefix": prefix, "max-keys": 1000}
        if marker:
            params["marker"] = marker
        code, txt = get(S3, params, tries=5, timeout=70)
        if code != 200:
            return cles, tailles, modifs, f"{code} {txt}"
        contenus = re.findall(r"<Contents><Key>([^<]+)</Key><LastModified>([^<]+)</LastModified>.*?<Size>(\d+)</Size>", txt)
        for k, lm, sz in contenus:
            marker = k
            if k.endswith(".zip"):
                cles.append(k)
                tailles.append(int(sz))
                modifs.append(lm)
        if "<IsTruncated>true</IsTruncated>" not in txt:
            return cles, tailles, modifs, None
    return cles, tailles, modifs, "liste tronquée"


def vision_jeu(nom):
    out = {"source": f"{VISION}/data/futures/um/daily/{nom}/", "resultats": []}
    for symbol in UNIVERS:
        cles, tailles, modifs, err = s3_lister(f"data/futures/um/daily/{nom}/{symbol}/")
        ligne = {"symbole": symbol, "fichiers": len(cles), "erreur": err}
        if cles:
            dates = sorted(re.search(r"(\d{4}-\d{2}-\d{2})\.zip$", k).group(1) for k in cles)
            d0, d1 = datetime.fromisoformat(dates[0]), datetime.fromisoformat(dates[-1])
            attendus = (d1 - d0).days + 1
            ligne.update({"premier": dates[0], "dernier": dates[-1], "jours_attendus": attendus,
                          "jours_manquants": attendus - len(set(dates)),
                          "mo_total": round(sum(tailles) / 1e6, 1),
                          "derniere_mise_en_ligne_min": min(modifs)[:10],
                          "derniere_mise_en_ligne_max": max(modifs)[:10]})
        out["resultats"].append(ligne)
    return out


def vision_liquidations():
    out = {"prefixes_testes": [], "fichiers_testes": []}
    for pre in ["data/futures/um/daily/liquidationSnapshot/", "data/futures/um/monthly/liquidationSnapshot/",
                "data/futures/cm/daily/liquidationSnapshot/"]:
        code, txt = get(S3, {"prefix": pre, "max-keys": 5, "delimiter": "/"}, timeout=70)
        n = len(re.findall(r"<Key>|<CommonPrefixes>", txt or ""))
        out["prefixes_testes"].append({"prefixe": pre, "code": code, "objets_ou_sous_dossiers": n})
    for d in ["2021-06-01", "2022-06-13", "2023-01-01", "2024-08-05", "2026-10-01"]:
        u = f"{VISION}/data/futures/um/daily/liquidationSnapshot/BTCUSDT/BTCUSDT-liquidationSnapshot-{d}.zip"
        code, _ = get(u, tries=2)
        out["fichiers_testes"].append({"url": u, "code": code})
    code, txt = get(S3, {"prefix": "data/futures/um/daily/", "delimiter": "/"}, timeout=70)
    out["jeux_quotidiens_um"] = re.findall(r"daily/([A-Za-z]+)/</Prefix>", txt or "")
    code, txt = get(S3, {"prefix": "data/futures/um/monthly/", "delimiter": "/"}, timeout=70)
    out["jeux_mensuels_um"] = re.findall(r"monthly/([A-Za-z]+)/</Prefix>", txt or "")
    return out


# --- 5. Liquidations ---------------------------------------------------------
def liq_rest():
    out = []
    for nom, u, p in [
        ("Binance allForceOrders (ancien public)", f"{FAPI}/fapi/v1/allForceOrders", {"symbol": "BTCUSDT", "limit": 1}),
        ("Binance forceOrders (compte)", f"{FAPI}/fapi/v1/forceOrders", {"symbol": "BTCUSDT", "limit": 1}),
    ]:
        code, txt = get(u, p, tries=1)
        msg = (txt or "")[:90].replace("\n", " ")
        out.append({"point": nom, "code": code, "reponse": msg if code != 404 else "page d'erreur 404"})
    # OKX : profondeur réelle du REST public des liquidations.
    u = f"{OKX}/api/v5/public/liquidation-orders"
    plus_ancien = None
    apres = None
    pages = 0
    for _ in range(40):
        p = {"instType": "SWAP", "instFamily": "BTC-USDT", "state": "filled", "limit": 100}
        if apres:
            p["after"] = apres
        code, txt = get(u, p)
        if code != 200:
            break
        d = json.loads(txt)
        if d.get("code") != "0" or not d.get("data"):
            break
        ts = [int(x["ts"]) for bloc in d["data"] for x in bloc["details"]]
        if not ts:
            break
        m = min(ts)
        if plus_ancien is not None and m >= plus_ancien:
            break
        plus_ancien = m
        apres = m
        pages += 1
        time.sleep(0.25)
    out.append({"point": "OKX public liquidation-orders (BTC-USDT SWAP)", "pages_lues": pages,
                "plus_ancienne_liquidation": iso(plus_ancien) if plus_ancien else None,
                "anciennete_jours": round((now_ms() - plus_ancien) / JOUR_MS, 2) if plus_ancien else None})
    # Bybit : pas de REST public de liquidations connu ; on teste le chemin historique.
    code, txt = get(f"{BYBIT}/v5/market/liquidation", {"category": "linear", "symbol": "BTCUSDT"}, tries=1)
    out.append({"point": "Bybit /v5/market/liquidation (chemin supposé)", "code": code,
                "reponse": (txt or "")[:90].replace("\n", " ")})
    return out


async def ecoute_ws(url, abonnement, secondes):
    import websockets
    res = {"url": url, "abonnement": abonnement, "secondes": secondes, "messages": 0, "exemple": None, "erreur": None}
    try:
        async with websockets.connect(url, open_timeout=20, ping_interval=15) as ws:
            if abonnement:
                await ws.send(json.dumps(abonnement))
            fin = time.time() + secondes
            while time.time() < fin:
                try:
                    m = await asyncio.wait_for(ws.recv(), timeout=max(0.1, fin - time.time()))
                except asyncio.TimeoutError:
                    break
                d = json.loads(m)
                if "op" in d or "result" in d or d.get("success") is not None:
                    continue
                res["messages"] += 1
                if res["exemple"] is None:
                    res["exemple"] = str(d)[:260]
    except Exception as e:  # le relevé doit consigner l'échec, pas s'arrêter
        res["erreur"] = f"{type(e).__name__}: {e}"[:200]
    return res


async def liq_flux(secondes):
    return await asyncio.gather(
        ecoute_ws("wss://fstream.binance.com/ws/!forceOrder@arr", None, secondes),
        ecoute_ws("wss://fstream.binance.com/stream?streams=!forceOrder@arr", None, secondes),
        ecoute_ws("wss://fstream.binance.com/market/ws/!forceOrder@arr", None, secondes),
        # Témoins : un flux de transactions doit parler. Sinon la tuyauterie est en cause, pas le marché.
        ecoute_ws("wss://fstream.binance.com/ws/btcusdt@aggTrade", None, min(secondes, 20)),
        ecoute_ws("wss://fstream.binance.com/market/ws/btcusdt@aggTrade", None, min(secondes, 20)),
        ecoute_ws("wss://stream.bybit.com/v5/public/linear",
                  {"op": "subscribe", "args": ["publicTrade.BTCUSDT"]}, min(secondes, 20)),
        ecoute_ws("wss://stream.bybit.com/v5/public/linear",
                  {"op": "subscribe", "args": [f"allLiquidation.{s}" for s in UNIVERS]},
                  secondes),
    )


def tardis_echantillons():
    out = {"source": "https://datasets.tardis.dev (premier jour de chaque mois gratuit, sans clé)", "resultats": []}
    code, txt = get("https://api.tardis.dev/v1/exchanges/binance-futures", timeout=40)
    if code == 200:
        d = json.loads(txt)
        out["binance_futures_availableSince"] = d.get("availableSince")
        ch = [c for c in d.get("availableChannels", []) if "force" in c.lower() or "interest" in c.lower()]
        out["canaux_pertinents"] = ch
    else:
        out["erreur_api"] = f"{code} {txt}"
    for an, mo in [(2020, 2), (2021, 6), (2023, 1), (2026, 10)]:
        u = f"https://datasets.tardis.dev/v1/binance-futures/liquidations/{an}/{mo:02d}/01/BTCUSDT.csv.gz"
        try:
            r = requests.get(u, headers=UA, timeout=60)
            ligne = {"url": u, "code": r.status_code}
            if r.status_code == 200:
                lignes = gzip.GzipFile(fileobj=io.BytesIO(r.content)).read().decode().splitlines()
                ligne["lignes"] = len(lignes) - 1
                ligne["entete"] = lignes[0][:80]
            out["resultats"].append(ligne)
        except requests.RequestException as e:
            out["resultats"].append({"url": u, "erreur": type(e).__name__})
    return out


# --- 6. Financement et bougies ----------------------------------------------
def financement_bougies():
    out = []
    for symbol in UNIVERS:
        code, txt = get(f"{FAPI}/fapi/v1/fundingRate", {"symbol": symbol, "limit": 1, "startTime": 1546300800000})
        f0 = iso(json.loads(txt)[0]["fundingTime"]) if code == 200 and json.loads(txt) else f"échec {code}"
        code, txt = get(f"{FAPI}/fapi/v1/klines", {"symbol": symbol, "interval": "15m", "limit": 1, "startTime": 0})
        k0 = iso(json.loads(txt)[0][0]) if code == 200 and json.loads(txt) else f"échec {code}"
        out.append({"symbole": symbol, "premier_financement": f0, "premiere_bougie_15m": k0})
        time.sleep(0.1)
    return out


# --- Rapport ----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws-secondes", type=int, default=60)
    ap.add_argument("--etapes", default="", help="noms d'étapes séparés par des virgules ; vide = toutes")
    a = ap.parse_args()
    debut = datetime.now(timezone.utc)
    stamp = debut.strftime("%Y%m%dT%H%M%SZ")
    rap = {"debut_utc": debut.isoformat(timespec="seconds"), "script": "verif_donnees_oi.py"}
    etapes = [
        ("binance_openInterestHist", binance_oi_profondeur),
        ("binance_delai_publication", binance_oi_delai),
        ("bybit_open_interest", bybit_profondeur),
        ("okx_open_interest", okx_profondeur),
        ("vision_metrics", lambda: vision_jeu("metrics")),
        ("vision_bookDepth", lambda: vision_jeu("bookDepth")),
        ("vision_liquidations", vision_liquidations),
        ("liquidations_rest", liq_rest),
        ("liquidations_flux", lambda: asyncio.run(liq_flux(a.ws_secondes))),
        ("tardis_echantillons", tardis_echantillons),
        ("financement_bougies", financement_bougies),
    ]
    choisies = [e for e in a.etapes.split(",") if e]
    for nom, f in etapes:
        if choisies and nom not in choisies:
            continue
        t0 = time.time()
        try:
            rap[nom] = f()
        except Exception as e:  # une API en échec est une lacune à consigner
            rap[nom] = {"ECHEC": f"{type(e).__name__}: {e}"}
        print(f"[{nom}] {time.time() - t0:.0f} s", flush=True)
    rap["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    RES.mkdir(exist_ok=True)
    p = RES / f"verif_donnees_oi_{stamp}.json"
    p.write_text(json.dumps(rap, ensure_ascii=False, indent=1))
    print("écrit :", p)


if __name__ == "__main__":
    main()
