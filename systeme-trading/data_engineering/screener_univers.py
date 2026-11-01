#!/usr/bin/env python3
"""Screener d'univers des perpétuels USDT (recherche seulement).

Source principale Binance Futures (fapi), contrôle croisé Bybit v5.
Points d'accès publics en lecture seulement. Aucune clé, aucun ordre.

BIAIS A LIRE AVANT TOUT USAGE
Le classement d'aujourd'hui appliqué à 2021-2024 est un biais d'anticipation
et du survivant. Seuls les gagnants actuels y figurent et les jetons morts
manquent. Le panier ne remplace donc pas l'univers figé de STRAT-20261031-01.
Toute stratégie testée dessus doit porter ce biais ou utiliser un univers
reconstruit à la date.

REGLE D'ENTREE AU CLASSEMENT (essai U03, déclaré le 01/11/2026)
Le top 30 se forme sur le volume médian à 30 jours de tous les perpétuels retenus.
Le volume 24 h reste affiché et sert encore à la règle de pointe, inchangée.
La règle précédente (volume 24 h, essais U01 et U02) est rejouée comme témoin sur
la même collecte. Un panier se cite par l'horodatage de sa collecte. Une relance
crée d'autres fichiers et ne remplace jamais un panier déjà publié.

Usage
    python screener_univers.py                      collecte puis analyse
    python screener_univers.py --reuse-raw FICHIER  analyse sans nouvel appel
    python screener_univers.py --sorties DOSSIER --cache DOSSIER  rejeu hors du dépôt
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# PONDERATIONS DU SCORE COMPOSITE (somme = 1). Fixées avant la première
# exécution. Chaque critère est converti en rang centile parmi les N paires
# du classement, 100 étant le meilleur. Une valeur manquante vaut 0.
# ---------------------------------------------------------------------------
WEIGHTS = {
    "volume_median_30j": 0.20,       # plus haut = mieux (Binance, klines)
    "glissement_50k": 0.25,          # plus bas = mieux (moyenne achat et vente)
    "ecart": 0.10,                   # plus bas = mieux
    "financement_abs_annualise": 0.10,  # plus bas = mieux, valeur absolue
    "financement_p95_8h": 0.05,      # plus bas = mieux
    "anciennete": 0.15,              # plus haut = mieux
    "diversification_btc": 0.10,     # 1 - corrélation BTC sur 180 j, plus haut = mieux
    "glissement_50k_bybit": 0.05,    # plus bas = mieux (plateforme de repli)
}
assert abs(sum(WEIGHTS.values()) - 1) < 1e-9

# ---------------------------------------------------------------------------
# REGLES DU PANIER. Fixées avant la première exécution.
# ---------------------------------------------------------------------------
TOP_N = 30
REGLE_TOP = "volume_median_30j"      # essai U03, remplace "volume_24h" (U01 et U02)
JOURS_VOLUME_MEDIAN = 30             # bougies 1 j closes exigées pour entrer au classement
PANIER_MIN = 10
PANIER_MAX = 15
ANCIENNETE_MIN_J = 365               # corrélation et financement sur un an
JOURS_MIN_FENETRE_RECHERCHE = 180    # jours de cotation exigés avant la fin de fenêtre
FIN_FENETRE_RECHERCHE = dt.datetime(2024, 6, 30, tzinfo=dt.timezone.utc)
GLISSEMENT_50K_MAX_BPS = 25.0        # médiane, moyenne achat et vente, Binance
ECART_MAX_BPS = 5.0                  # médiane, Binance
VOLUME_MEDIAN_30J_MIN = 30e6         # USDT par jour, Binance
FINANCEMENT_ABS_MAX_PCT = 30.0       # % annualisé en valeur absolue
RATIO_POINTE_VOLUME_MAX = 5.0        # volume 24 h / médiane 30 j
PLAFOND_CORR_SUITE = (0.85, 0.875, 0.90, 0.925, 0.95)  # corrélation 180 j, assouplie seulement si < PANIER_MIN
ANCRES = ("BTCUSDT", "ETHUSDT")      # entrent d'abord si éligibles, sans plafond entre elles

# ---------------------------------------------------------------------------
# PARAMETRES DE COLLECTE
# ---------------------------------------------------------------------------
NOTIONNELS = (1_000, 10_000, 50_000)
PROFONDEUR_BANDES_BPS = (10, 50)
SNAPSHOTS_DEFAUT = 6
INTERVALLE_SNAPSHOT_S = 150
LIMITE_CARNET_BINANCE = 500          # poids 10
LIMITE_CARNET_BYBIT = 500
FENETRES_CORR = (90, 180, 365)
COUVERTURE_MIN_FENETRE = 0.9         # part minimale de jours présents pour calculer

BINANCE = "https://fapi.binance.com"
BYBIT = "https://api.bybit.com"
BINANCE_MARGE = "https://www.binance.com/bapi/margin/v1/public/margin/vip/spec/list-all"

STABLES = {
    "USDC", "USDT", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "USDE", "USDS", "USD1", "RLUSD", "PYUSD",
    "EURI", "EURC", "AEUR", "USDD", "FRAX", "GUSD", "LUSD", "SUSD", "USD0", "USDG", "BFUSD", "USDF",
    "USDX", "XUSD", "U",
}
ACTIFS_REELS_NOMS = {"XAU", "XAG", "XPT", "XPD", "XAUT", "XAUM", "PAXG", "KAU", "KAG"}
SOUS_TYPES_EXCLUS = {"TradFi", "RWA", "Pre-IPO", "Pre-Market", "Index"}
BYBIT_TYPES_NON_CRYPTO = {"stock", "ETF", "commodity", "forex"}
ALIAS_BASE = {"BEAMX": "BEAM", "PUMPFUN": "PUMP"}       # même jeton, ticker différent entre plateformes

BIAIS = (
    "Le classement d'aujourd'hui appliqué à 2021-2024 est un biais d'anticipation et du survivant. "
    "Seuls les gagnants actuels y figurent et les jetons morts manquent. "
    "Ce panier ne remplace donc PAS l'univers figé de STRAT-20261031-01. "
    "Il sert aux recherches futures. Toute stratégie testée dessus doit porter ce biais ou utiliser un univers reconstruit à la date."
)
ALERTE = (
    "Piratage Binance fin octobre 2026 et retraits suspendus, reprise annoncée le 01/11, selon NOTE_STRATEGIE_ET_REGIME.md (information non revérifiée ici). "
    "Les données publiques restent lisibles mais ne préjugent pas d'une exécution sur cette plateforme."
)

JOURS_FR = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")

RACINE = Path(__file__).resolve().parent
SORTIES = RACINE / "resultats"
CACHE = RACINE.parent / "user_data" / "data" / "_screener_cache"


def maintenant() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(ms_ou_dt) -> str:
    if isinstance(ms_ou_dt, (int, float)):
        ms_ou_dt = dt.datetime.fromtimestamp(ms_ou_dt / 1000, dt.timezone.utc)
    return ms_ou_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(f"[{iso(maintenant())}] {msg}", flush=True)


class ClientPublic:
    """GET public avec reprises, respect de Retry-After et suivi du poids Binance."""

    def __init__(self) -> None:
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "screener-univers-recherche/1.0"
        self.dernier: dict[str, float] = {}
        self.appels = 0
        self.incidents: list[str] = []

    def get(self, url: str, params: dict | None = None, delai_min: float = 0.05, essais: int = 6):
        for essai in range(essais):
            cle = url.split("/")[2] + ("/fr" if "fundingRate" in url else "")
            attente = self.dernier.get(cle, 0) + delai_min - time.monotonic()
            if attente > 0:
                time.sleep(attente)
            self.dernier[cle] = time.monotonic()
            self.appels += 1
            try:
                r = self.s.get(url, params=params, timeout=30)
            except requests.RequestException as e:
                self.incidents.append(f"{iso(maintenant())} réseau {url} {type(e).__name__}")
                time.sleep(2 ** essai)
                continue
            if r.status_code == 418:
                raise RuntimeError(f"IP bannie temporairement par {url} (418), arrêt pour respecter la plateforme")
            if r.status_code == 429:
                pause = int(r.headers.get("Retry-After", 60))
                self.incidents.append(f"{iso(maintenant())} 429 {url}, pause {pause} s")
                time.sleep(pause)
                continue
            if r.status_code >= 500:
                self.incidents.append(f"{iso(maintenant())} {r.status_code} {url}")
                time.sleep(2 ** essai)
                continue
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code} sur {url} {params} : {r.text[:200]}")
            poids = r.headers.get("X-MBX-USED-WEIGHT-1M")
            if poids and int(poids) > 1800:
                self.incidents.append(f"{iso(maintenant())} poids Binance {poids}, pause 30 s")
                time.sleep(30)
            donnees = r.json()
            if isinstance(donnees, dict) and "retCode" in donnees:
                if donnees["retCode"] in (10006, 10018):
                    time.sleep(5)
                    continue
                if donnees["retCode"] != 0:
                    raise RuntimeError(f"Bybit retCode {donnees['retCode']} {donnees.get('retMsg')} sur {url} {params}")
            return donnees
        raise RuntimeError(f"Échec après {essais} essais sur {url} {params}")


# ---------------------------------------------------------------------------
# Univers
# ---------------------------------------------------------------------------
def base_normalisee(base: str) -> str:
    m = re.fullmatch(r"(?:1000000|100000|10000|1000|100)?([A-Z0-9]+?)(?:1000)?", base)
    b = m.group(1) if m else base
    return ALIAS_BASE.get(b, b)


def multiplicateur(base: str) -> int:
    m = re.match(r"^(1000000|100000|10000|1000|100)[A-Z]", base)
    if m:
        return int(m.group(1))
    return 1000 if re.fullmatch(r"[A-Z]+1000", base) else 1


def raison_exclusion_binance(s: dict) -> str | None:
    if s.get("quoteAsset") != "USDT":
        return "cotation autre que USDT"
    ct = s.get("contractType")
    if ct == "TRADIFI_PERPETUAL":
        return f"actif réel ou action ({s.get('underlyingType')})"
    if ct != "PERPETUAL":
        return f"contrat daté ({ct})"
    if s.get("status") != "TRADING":
        return f"statut {s.get('status')}"
    if s.get("underlyingType") != "COIN":
        return f"sous-jacent {s.get('underlyingType')}"
    sous = set(s.get("underlyingSubType") or [])
    if sous & SOUS_TYPES_EXCLUS:
        return f"sous-type {sorted(sous & SOUS_TYPES_EXCLUS)}"
    if base_normalisee(s["baseAsset"]) in STABLES:
        return "stablecoin"
    if base_normalisee(s["baseAsset"]) in ACTIFS_REELS_NOMS:
        return "actif réel par nom"
    return None


def volume_median_recent(c: ClientPublic, sym: str, now_ms: int) -> tuple[float | None, int]:
    """Médiane du volume quotidien sur les 30 dernières bougies closes, None si elles n'y sont pas toutes."""
    brut = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "limit": JOURS_VOLUME_MEDIAN + 1})
    vols = [float(k[7]) for k in brut if k[6] < now_ms][-JOURS_VOLUME_MEDIAN:]
    return (float(np.median(vols)) if len(vols) >= JOURS_VOLUME_MEDIAN else None), len(vols)


def classer_par_volume(retenus: list, top_n: int) -> tuple[list, list, list]:
    """Pose les deux rangs. Renvoie le top sur la médiane, le top témoin sur 24 h et les non classables."""
    par_24h = sorted(retenus, key=lambda x: -x["volume_24h"])
    for rang, x in enumerate(par_24h, 1):
        x["rang_volume_24h"] = rang
    classables = sorted((x for x in retenus if x.get("volume_median_30j") is not None), key=lambda x: -x["volume_median_30j"])
    for rang, x in enumerate(classables, 1):
        x["rang_volume_median"] = rang
    non_classables = [x for x in par_24h if x.get("volume_median_30j") is None]
    return classables[:top_n], par_24h[:top_n], non_classables


def collecter_univers(c: ClientPublic, top_n: int, now_ms: int) -> dict:
    temps = c.get(f"{BINANCE}/fapi/v1/time")["serverTime"]
    ei = c.get(f"{BINANCE}/fapi/v1/exchangeInfo")
    tick = {t["symbol"]: t for t in c.get(f"{BINANCE}/fapi/v1/ticker/24hr")}
    heure_tickers_binance = iso(maintenant())
    retenus, exclusions = [], []
    for s in ei["symbols"]:
        vol = float(tick.get(s["symbol"], {}).get("quoteVolume", 0) or 0)
        raison = raison_exclusion_binance(s)
        if raison:
            exclusions.append({"plateforme": "binance", "symbole": s["symbol"], "raison": raison,
                               "volume_24h_usdt": vol, "contrat": s.get("contractType"), "statut": s.get("status")})
            continue
        retenus.append({
            "symbole": s["symbol"], "base": s["baseAsset"], "base_norm": base_normalisee(s["baseAsset"]),
            "listing_ms": s["onboardDate"], "sous_types": s.get("underlyingSubType") or [],
            "volume_24h": vol, "dernier_prix": float(tick.get(s["symbol"], {}).get("lastPrice", 0) or 0),
            "fermeture_ticker_ms": tick.get(s["symbol"], {}).get("closeTime"),
        })
    log(f"Volume médian 30 j des {len(retenus)} perpétuels retenus")
    erreurs_classement = []
    for x in retenus:
        try:
            x["volume_median_30j"], x["jours_volume"] = volume_median_recent(c, x["symbole"], now_ms)
        except Exception as e:  # consigné, jamais remplacé par une valeur inventée
            x["volume_median_30j"], x["jours_volume"] = None, 0
            erreurs_classement.append(f"klines classement {x['symbole']} {e}")
    top, top_24h, non_classables = classer_par_volume(retenus, top_n)
    for x in non_classables:
        exclusions.append({"plateforme": "binance", "symbole": x["symbole"],
                           "raison": f"moins de {JOURS_VOLUME_MEDIAN} bougies 1 j closes, hors classement",
                           "volume_24h_usdt": x["volume_24h"], "contrat": "PERPETUAL", "statut": "TRADING"})

    # Bybit
    instruments, curseur = [], ""
    while True:
        p = {"category": "linear", "limit": 1000}
        if curseur:
            p["cursor"] = curseur
        r = c.get(f"{BYBIT}/v5/market/instruments-info", p)["result"]
        instruments += r["list"]
        curseur = r.get("nextPageCursor") or ""
        if not curseur:
            break
    tick_by = {t["symbol"]: t for t in c.get(f"{BYBIT}/v5/market/tickers", {"category": "linear"})["result"]["list"]}
    bybit = {}
    types_bybit_non_crypto = {}
    for i in instruments:
        sym = i["symbol"]
        vol = float(tick_by.get(sym, {}).get("turnover24h", 0) or 0)
        raison = None
        if i.get("settleCoin") != "USDT" or i.get("quoteCoin") != "USDT":
            raison = "règlement autre que USDT"
        elif i.get("contractType") != "LinearPerpetual":
            raison = f"contrat daté ({i.get('contractType')})"
        elif i.get("status") != "Trading":
            raison = f"statut {i.get('status')}"
        elif i.get("symbolType") in BYBIT_TYPES_NON_CRYPTO:
            raison = f"actif réel ou action ({i.get('symbolType')})"
            types_bybit_non_crypto[base_normalisee(i["baseCoin"])] = i.get("symbolType")
        elif base_normalisee(i["baseCoin"]) in STABLES:
            raison = "stablecoin"
        if raison:
            exclusions.append({"plateforme": "bybit", "symbole": sym, "raison": raison, "volume_24h_usdt": vol,
                               "contrat": i.get("contractType"), "statut": i.get("status")})
            continue
        bybit[base_normalisee(i["baseCoin"])] = {
            "symbole": sym, "base": i["baseCoin"], "listing_ms": int(i["launchTime"]), "volume_24h": vol,
            "dernier_prix": float(tick_by.get(sym, {}).get("lastPrice", 0) or 0), "type": i.get("symbolType") or "",
        }
    classement_bybit = sorted(bybit.items(), key=lambda kv: -kv[1]["volume_24h"])
    for rang, (b, v) in enumerate(classement_bybit, 1):
        v["rang"] = rang
    return {
        "heure_serveur_binance_ms": temps,
        "heure_exchangeinfo_ms": ei.get("serverTime"),
        "heure_tickers_binance": heure_tickers_binance,
        "heure_collecte_tickers": iso(maintenant()),
        "n_contrats_binance": len(ei["symbols"]),
        "n_perp_crypto_retenus": len(retenus),
        "n_classables": len(retenus) - len(non_classables),
        "regle_top": REGLE_TOP,
        "top": top,
        "top_volume_24h": top_24h,
        "collectes": list({x["symbole"]: x for x in top + top_24h}.values()),
        "tous_volumes": [{k: x.get(k) for k in ("symbole", "volume_24h", "rang_volume_24h", "volume_median_30j", "rang_volume_median", "jours_volume")}
                         for x in sorted(retenus, key=lambda x: x["rang_volume_24h"])],
        "erreurs_classement": erreurs_classement,
        "bybit": bybit,
        "bybit_top_bases": [b for b, _ in classement_bybit[:top_n]],
        "bybit_types_non_crypto": types_bybit_non_crypto,
        "exclusions": exclusions,
    }


# ---------------------------------------------------------------------------
# Historique
# ---------------------------------------------------------------------------
def klines_binance(c: ClientPublic, sym: str, now_ms: int) -> dict:
    brut = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "limit": 400})
    lignes = [[k[0], float(k[4]), float(k[7])] for k in brut if k[6] < now_ms]
    premier = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "startTime": 0, "limit": 1})
    return {"lignes": lignes, "premiere_bougie_ms": premier[0][0] if premier else None}


def financement_binance(c: ClientPublic, sym: str, debut_ms: int, fin_ms: int) -> list:
    sortie, curseur = [], debut_ms
    while curseur < fin_ms:
        lot = c.get(f"{BINANCE}/fapi/v1/fundingRate",
                    {"symbol": sym, "startTime": curseur, "endTime": fin_ms, "limit": 1000}, delai_min=0.65)
        if not lot:
            break
        sortie += [[x["fundingTime"], float(x["fundingRate"])] for x in lot]
        if len(lot) < 1000:
            break
        curseur = lot[-1]["fundingTime"] + 1
    return sortie


def financement_bybit(c: ClientPublic, sym: str, debut_ms: int, fin_ms: int) -> list:
    sortie, curseur = [], fin_ms
    while curseur > debut_ms:
        lot = c.get(f"{BYBIT}/v5/market/funding/history",
                    {"category": "linear", "symbol": sym, "startTime": debut_ms, "endTime": curseur, "limit": 200})["result"]["list"]
        if not lot:
            break
        sortie += [[int(x["fundingRateTimestamp"]), float(x["fundingRate"])] for x in lot]
        if len(lot) < 200:
            break
        curseur = min(int(x["fundingRateTimestamp"]) for x in lot) - 1
    return sorted(sortie)


def taux_marge(c: ClientPublic) -> dict:
    sortie = {"binance": {}, "bybit": {}, "erreurs": [], "heure": iso(maintenant())}
    try:
        d = c.get(BINANCE_MARGE)
        for a in d.get("data") or []:
            niv0 = next((x for x in a.get("specs", []) if str(x.get("vipLevel")) == "0"), None)
            if niv0 and niv0.get("dailyInterestRate") is not None:
                sortie["binance"][a["assetName"]] = float(niv0["dailyInterestRate"])
    except Exception as e:  # lacune consignée, jamais remplacée par une valeur inventée
        sortie["erreurs"].append(f"Binance marge {type(e).__name__} {e}")
    try:
        d = c.get(f"{BYBIT}/v5/spot-margin-trade/data")
        for bloc in d["result"].get("vipCoinList", []):
            if bloc.get("vipLevel") == "No VIP":
                for a in bloc.get("list", []):
                    if a.get("hourlyBorrowRate") not in (None, "") and a.get("borrowable") is True:
                        sortie["bybit"][a["currency"]] = float(a["hourlyBorrowRate"])
    except Exception as e:
        sortie["erreurs"].append(f"Bybit marge {type(e).__name__} {e}")
    return sortie


# ---------------------------------------------------------------------------
# Carnets
# ---------------------------------------------------------------------------
def simuler_marche(niveaux: list, notionnel: float) -> tuple[float | None, float]:
    """Parcourt le carnet en consommant `notionnel` USDT. Renvoie prix moyen et notionnel servi."""
    reste, qte = notionnel, 0.0
    for prix, taille in niveaux:
        dispo = prix * taille
        pris = min(dispo, reste)
        qte += pris / prix
        reste -= pris
        if reste <= 1e-9:
            break
    servi = notionnel - reste
    return (servi / qte if qte > 0 else None), servi


def mesurer_carnet(bids: list, asks: list) -> dict:
    bids = [(float(p), float(q)) for p, q in bids]
    asks = [(float(p), float(q)) for p, q in asks]
    if not bids or not asks:
        return {"erreur": "carnet vide"}
    bb, ba = bids[0][0], asks[0][0]
    mid = (bb + ba) / 2
    couv_bid, couv_ask = (1 - bids[-1][0] / mid) * 1e4, (asks[-1][0] / mid - 1) * 1e4
    m = {"mid": mid, "ecart_bps": (ba - bb) / mid * 1e4,
         "profondeur_carnet_bid_usdt": sum(p * q for p, q in bids),
         "profondeur_carnet_ask_usdt": sum(p * q for p, q in asks),
         "couverture_bid_bps": couv_bid, "couverture_ask_bps": couv_ask}
    for b in PROFONDEUR_BANDES_BPS:
        m[f"prof_{b}bps_bid"] = sum(p * q for p, q in bids if p >= mid * (1 - b / 1e4))
        m[f"prof_{b}bps_ask"] = sum(p * q for p, q in asks if p <= mid * (1 + b / 1e4))
        # Le carnet s'arrête avant la bande : la valeur n'est alors qu'une borne basse.
        m[f"prof_{b}bps_bid_tronquee"] = couv_bid < b
        m[f"prof_{b}bps_ask_tronquee"] = couv_ask < b
    for n in NOTIONNELS:
        pa, sa = simuler_marche(asks, n)
        pv, sv = simuler_marche(bids, n)
        m[f"gliss_achat_{n}"] = (pa / mid - 1) * 1e4 if pa and sa >= n * 0.999 else None
        m[f"gliss_vente_{n}"] = (1 - pv / mid) * 1e4 if pv and sv >= n * 0.999 else None
    return m


def instantane(c: ClientPublic, top: list, bybit: dict, numero: int) -> dict:
    heure = iso(maintenant())
    res = {"numero": numero, "heure": heure, "binance": {}, "bybit": {}, "erreurs": []}
    for x in top:
        sym = x["symbole"]
        try:
            d = c.get(f"{BINANCE}/fapi/v1/depth", {"symbol": sym, "limit": LIMITE_CARNET_BINANCE})
            res["binance"][sym] = mesurer_carnet(d["bids"], d["asks"])
        except Exception as e:
            res["erreurs"].append(f"{heure} depth Binance {sym} {e}")
        by = bybit.get(x["base_norm"])
        if by:
            try:
                d = c.get(f"{BYBIT}/v5/market/orderbook",
                          {"category": "linear", "symbol": by["symbole"], "limit": LIMITE_CARNET_BYBIT})["result"]
                res["bybit"][sym] = mesurer_carnet(d["b"], d["a"])
            except Exception as e:
                res["erreurs"].append(f"{heure} carnet Bybit {by['symbole']} {e}")
    return res


# ---------------------------------------------------------------------------
# Collecte complète
# ---------------------------------------------------------------------------
def collecter(top_n: int, n_snap: int, intervalle: int) -> dict:
    c = ClientPublic()
    debut = maintenant()
    now_ms = int(time.time() * 1000)
    log("Univers et tickers")
    u = collecter_univers(c, top_n, now_ms)
    debut_fin = now_ms - 365 * 86400_000
    brut = {"debut_collecte": iso(debut), "univers": u, "klines": {}, "financement_binance": {},
            "financement_bybit": {}, "erreurs": list(u["erreurs_classement"]),
            "parametres": {"top_n": top_n, "snapshots": n_snap, "intervalle_s": intervalle, "regle_top": REGLE_TOP}}

    # Le classement retenu et le classement témoin sur 24 h sont collectés ensemble,
    # pour comparer les deux règles sur les mêmes mesures.
    collectes = u["collectes"]
    log(f"Klines de référence et de {len(collectes)} paires ({len(u['top'])} classées, {len(collectes) - len(u['top'])} témoins 24 h en plus)")
    symboles = [x["symbole"] for x in collectes]
    for sym in dict.fromkeys(["BTCUSDT", "ETHUSDT"] + symboles):
        try:
            brut["klines"][sym] = klines_binance(c, sym, now_ms)
        except Exception as e:
            brut["erreurs"].append(f"klines {sym} {e}")
    brut["heure_klines"] = iso(maintenant())

    log("Financement, un an, Binance et Bybit")
    for i, x in enumerate(collectes, 1):
        sym = x["symbole"]
        try:
            brut["financement_binance"][sym] = financement_binance(c, sym, debut_fin, now_ms)
        except Exception as e:
            brut["erreurs"].append(f"financement Binance {sym} {e}")
        by = u["bybit"].get(x["base_norm"])
        if by:
            try:
                brut["financement_bybit"][sym] = financement_bybit(c, by["symbole"], debut_fin, now_ms)
            except Exception as e:
                brut["erreurs"].append(f"financement Bybit {by['symbole']} {e}")
        log(f"  {i}/{len(collectes)} {sym} : {len(brut['financement_binance'].get(sym, []))} périodes Binance, "
            f"{len(brut['financement_bybit'].get(sym, []))} Bybit")
    brut["heure_financement"] = iso(maintenant())

    log("Taux d'emprunt sur marge spot, sources publiques")
    brut["marge"] = taux_marge(c)

    brut["instantanes"] = []
    for k in range(n_snap):
        log(f"Instantané de carnets {k + 1}/{n_snap}")
        brut["instantanes"].append(instantane(c, collectes, u["bybit"], k + 1))
        if k + 1 < n_snap:
            time.sleep(intervalle)

    brut["fin_collecte"] = iso(maintenant())
    brut["appels_http"] = c.appels
    brut["incidents_http"] = c.incidents
    return brut


# ---------------------------------------------------------------------------
# Analyse
# ---------------------------------------------------------------------------
def stats_financement(lignes: list, fin: dt.datetime) -> dict:
    if not lignes:
        return {}
    df = pd.DataFrame(lignes, columns=["t", "r"]).drop_duplicates("t").sort_values("t")
    df = df[df["t"] >= (fin - dt.timedelta(days=365)).timestamp() * 1000]
    if df.empty:
        return {}
    ecarts = df["t"].diff().div(3_600_000)
    ecarts = ecarts.fillna(ecarts.median()).clip(lower=0.25)
    if ecarts.isna().all():
        ecarts = pd.Series(8.0, index=df.index)
    eq8h = df["r"] * 8 / ecarts
    jours = (df["t"].iloc[-1] - df["t"].iloc[0]) / 86_400_000 + ecarts.iloc[-1] / 24
    annee = df["r"].sum() / jours * 365 * 100
    d90 = df[df["t"] >= (fin - dt.timedelta(days=90)).timestamp() * 1000]
    jours90 = (d90["t"].iloc[-1] - d90["t"].iloc[0]) / 86_400_000 + ecarts.iloc[-1] / 24 if len(d90) > 1 else float("nan")
    return {
        "n_periodes": int(len(df)),
        "couverture_j": round(float(jours), 1),
        "intervalle_h_median": float(ecarts.median()),
        "mediane_periode_pct": float(df["r"].median() * 100),
        "mediane_8h_pct": float(eq8h.median() * 100),
        "moyenne_annualisee_pct": float(annee),
        "moyenne_annualisee_90j_pct": float(d90["r"].sum() / jours90 * 365 * 100) if len(d90) > 1 else None,
        "part_negative_pct": float((df["r"] < 0).mean() * 100),
        "p95_8h_pct": float(eq8h.quantile(0.95) * 100),
        "p95_periode_pct": float(df["r"].quantile(0.95) * 100),
    }


def serie_rendements(kl: dict) -> pd.Series:
    df = pd.DataFrame(kl["lignes"], columns=["t", "close", "qv"])
    s = np.log(df["close"].astype(float)).diff()
    s.index = pd.to_datetime(df["t"], unit="ms", utc=True)
    return s.dropna()


def correlation(a: pd.Series, b: pd.Series, n: int, fin: pd.Timestamp) -> tuple[float | None, float | None, int]:
    debut = fin - pd.Timedelta(days=n)
    x = pd.concat([a, b], axis=1, join="inner").loc[lambda d: d.index > debut]
    x.columns = ["a", "b"]
    x = x.dropna()
    if len(x) < n * COUVERTURE_MIN_FENETRE:
        return None, None, len(x)
    corr = float(x["a"].corr(x["b"]))
    beta = float(x["a"].cov(x["b"]) / x["b"].var())
    return corr, beta, len(x)


def agreger_carnets(instantanes: list, plateforme: str, sym: str) -> dict:
    mes = [s[plateforme][sym] for s in instantanes if sym in s.get(plateforme, {}) and "erreur" not in s[plateforme][sym]]
    out = {"n_instantanes": len(mes)}
    if not mes:
        return out
    cles = [k for k in mes[0] if k != "mid"]
    for k in cles:
        v = [m[k] for m in mes if m.get(k) is not None]
        if k.endswith("_tronquee"):
            out[f"{k}_instantanes"] = int(sum(v))
            continue
        out[f"{k}_med"] = statistics.median(v) if v else None
        if k.startswith("gliss") or k == "ecart_bps":
            out[f"{k}_max"] = max(v) if v else None
        out[f"{k}_n"] = len(v)
    return out


def rang_centile(s: pd.Series, plus_haut_mieux: bool) -> pd.Series:
    n = s.notna().sum()
    if n == 0:
        return pd.Series(0.0, index=s.index)
    r = s.rank(ascending=plus_haut_mieux, method="average")
    return ((r - 1) / max(n - 1, 1) * 100).fillna(0.0)


def analyser(brut: dict, plafond_corr=PLAFOND_CORR_SUITE) -> dict:
    u = brut["univers"]
    fin_dt = dt.datetime.fromisoformat(brut["debut_collecte"].replace("Z", "+00:00"))
    instant = brut["instantanes"]
    anomalies = list(brut.get("erreurs", []))
    for s in instant:
        anomalies += s.get("erreurs", [])
    anomalies += brut["marge"].get("erreurs", [])

    rends = {s: serie_rendements(k) for s, k in brut["klines"].items() if k["lignes"]}
    if "BTCUSDT" not in rends or "ETHUSDT" not in rends:
        raise RuntimeError("Klines BTC ou ETH manquantes, corrélation impossible")
    fin_corr = rends["BTCUSDT"].index.max()

    lignes = []
    for x in u["top"]:
        sym = x["symbole"]
        by = u["bybit"].get(x["base_norm"])
        l = {
            "rang_volume_24h": x["rang_volume_24h"], "rang_volume_median": x.get("rang_volume_median"), "symbole": sym, "paire_freqtrade": f"{x['base']}/USDT:USDT",
            "sous_types": "|".join(x["sous_types"]), "alpha": "Alpha" in x["sous_types"],
            "volume_24h_usdt": x["volume_24h"], "listing_binance": iso(x["listing_ms"])[:10],
            "anciennete_j": (fin_dt.timestamp() * 1000 - x["listing_ms"]) / 86_400_000,
        }
        kl = brut["klines"].get(sym)
        if kl and kl["lignes"]:
            l["volume_median_30j_usdt"] = float(np.median([k[2] for k in kl["lignes"][-30:]]))
            l["ratio_pointe_volume"] = x["volume_24h"] / l["volume_median_30j_usdt"] if l["volume_median_30j_usdt"] else None
            l["premiere_bougie_binance"] = iso(kl["premiere_bougie_ms"])[:10] if kl.get("premiere_bougie_ms") else None
            r = rends.get(sym)
            if r is not None:
                for n in FENETRES_CORR:
                    for ref, nom in (("BTCUSDT", "btc"), ("ETHUSDT", "eth")):
                        co, be, nobs = correlation(r, rends[ref], n, fin_corr)
                        l[f"corr_{nom}_{n}j"] = co
                        if ref == "BTCUSDT":
                            l[f"beta_btc_{n}j"] = be
                            l[f"nobs_{n}j"] = nobs
        for cle, v in stats_financement(brut["financement_binance"].get(sym, []), fin_dt).items():
            l[f"fin_{cle}"] = v
        ag = agreger_carnets(instant, "binance", sym)
        for k, v in ag.items():
            l[f"bn_{k}"] = v
        if ag.get("gliss_achat_50000_med") is not None and ag.get("gliss_vente_50000_med") is not None:
            l["bn_gliss_50k_moy_bps"] = (ag["gliss_achat_50000_med"] + ag["gliss_vente_50000_med"]) / 2
        # Contrôle croisé
        if by:
            l["bybit_symbole"] = by["symbole"]
            l["bybit_rang_volume"] = by.get("rang")
            l["bybit_volume_24h_usdt"] = by["volume_24h"]
            l["bybit_listing"] = iso(by["listing_ms"])[:10]
            l["bybit_type"] = by.get("type", "")
            mb, my = multiplicateur(x["base"]), multiplicateur(by["base"])
            ecarts_mid = [((sn["bybit"][sym]["mid"] / my) / (sn["binance"][sym]["mid"] / mb) - 1) * 100 for sn in instant
                          if sym in sn.get("bybit", {}) and sym in sn.get("binance", {})
                          and "mid" in sn["bybit"][sym] and "mid" in sn["binance"][sym]]
            if ecarts_mid:
                l["ecart_prix_binance_bybit_pct"] = statistics.median(ecarts_mid)
            ag_by = agreger_carnets(instant, "bybit", sym)
            for k, v in ag_by.items():
                l[f"by_{k}"] = v
            if ag_by.get("gliss_achat_50000_med") is not None and ag_by.get("gliss_vente_50000_med") is not None:
                l["by_gliss_50k_moy_bps"] = (ag_by["gliss_achat_50000_med"] + ag_by["gliss_vente_50000_med"]) / 2
            for cle, v in stats_financement(brut["financement_bybit"].get(sym, []), fin_dt).items():
                l[f"fin_by_{cle}"] = v
        # Emprunt sur marge spot, instantané
        tx_bn = brut["marge"]["binance"].get(x["base_norm"])
        tx_by = brut["marge"]["bybit"].get(x["base_norm"])
        l["emprunt_marge_binance_vip0_annuel_pct"] = tx_bn * 365 * 100 if tx_bn is not None else None
        l["emprunt_marge_bybit_novip_annuel_pct"] = tx_by * 24 * 365 * 100 if tx_by is not None else None
        lignes.append(l)
    df = pd.DataFrame(lignes).set_index("symbole", drop=False)

    # Score composite
    df["diversification_btc"] = 1 - pd.to_numeric(df.get("corr_btc_180j"), errors="coerce")
    df["fin_abs_annualise"] = pd.to_numeric(df.get("fin_moyenne_annualisee_pct"), errors="coerce").abs()
    comp = pd.DataFrame(index=df.index)
    comp["volume_median_30j"] = rang_centile(pd.to_numeric(df["volume_median_30j_usdt"], errors="coerce"), True)
    comp["glissement_50k"] = rang_centile(pd.to_numeric(df["bn_gliss_50k_moy_bps"], errors="coerce"), False)
    comp["ecart"] = rang_centile(pd.to_numeric(df["bn_ecart_bps_med"], errors="coerce"), False)
    comp["financement_abs_annualise"] = rang_centile(df["fin_abs_annualise"], False)
    comp["financement_p95_8h"] = rang_centile(pd.to_numeric(df["fin_p95_8h_pct"], errors="coerce"), False)
    comp["anciennete"] = rang_centile(df["anciennete_j"], True)
    comp["diversification_btc"] = rang_centile(df["diversification_btc"], True)
    comp["glissement_50k_bybit"] = rang_centile(pd.to_numeric(df.get("by_gliss_50k_moy_bps"), errors="coerce"), False)
    df["score"] = sum(comp[k] * p for k, p in WEIGHTS.items())
    for k in WEIGHTS:
        df[f"comp_{k}"] = comp[k].round(1)
    df = df.sort_values("score", ascending=False)
    df["rang_score"] = range(1, len(df) + 1)

    # Eligibilité
    jours_fenetre = lambda row: (FIN_FENETRE_RECHERCHE.timestamp() * 1000 - pd.Timestamp(row["listing_binance"], tz="UTC").timestamp() * 1000) / 86_400_000
    raisons_toutes = {}
    for sym, row in df.iterrows():
        r = []
        if row["anciennete_j"] < ANCIENNETE_MIN_J:
            r.append(f"ancienneté {row['anciennete_j']:.0f} j < {ANCIENNETE_MIN_J}")
        if jours_fenetre(row) < JOURS_MIN_FENETRE_RECHERCHE:
            r.append(f"moins de {JOURS_MIN_FENETRE_RECHERCHE} j cotés avant le 30/06/2024")
        if pd.isna(row.get("corr_btc_180j")):
            r.append("corrélation 180 j indisponible")
        g = row.get("bn_gliss_50k_moy_bps")
        if pd.isna(g) or g > GLISSEMENT_50K_MAX_BPS:
            r.append(f"glissement 50k {g:.1f} bps > {GLISSEMENT_50K_MAX_BPS:.0f}" if not pd.isna(g) else "glissement 50k indisponible")
        e = row.get("bn_ecart_bps_med")
        if pd.isna(e) or e > ECART_MAX_BPS:
            r.append(f"écart {e:.2f} bps > {ECART_MAX_BPS:.0f}" if not pd.isna(e) else "écart indisponible")
        v = row.get("volume_median_30j_usdt")
        if pd.isna(v) or v < VOLUME_MEDIAN_30J_MIN:
            r.append(f"volume médian 30 j {v / 1e6:.1f} M$ < {VOLUME_MEDIAN_30J_MIN / 1e6:.0f}" if not pd.isna(v) else "volume médian indisponible")
        f = row.get("fin_abs_annualise")
        if pd.isna(f) or f > FINANCEMENT_ABS_MAX_PCT:
            r.append(f"financement {f:.1f} % par an > {FINANCEMENT_ABS_MAX_PCT:.0f}" if not pd.isna(f) else "financement indisponible")
        p = row.get("ratio_pointe_volume")
        if not pd.isna(p) and p > RATIO_POINTE_VOLUME_MAX:
            r.append(f"pointe de volume x{p:.1f} > x{RATIO_POINTE_VOLUME_MAX:.0f}")
        if pd.isna(row.get("bybit_symbole")):
            r.append("absent de Bybit (repli impossible)")
        ep = row.get("ecart_prix_binance_bybit_pct")
        if not pd.isna(ep) and abs(ep) > 2:
            r.append(f"prix incohérent avec Bybit ({ep:.1f} %), homonyme possible")
        raisons_toutes[sym] = r
    df["raisons_non_eligible"] = [" ; ".join(raisons_toutes[s]) for s in df.index]
    df["eligible"] = df["raisons_non_eligible"] == ""

    # Matrice de corrélation sur 180 jours
    syms_corr = [s for s in df.index if s in rends]
    mat = pd.concat([rends[s].rename(s) for s in syms_corr], axis=1)
    mat = mat[mat.index > fin_corr - pd.Timedelta(days=180)]
    corr180 = mat.corr(min_periods=int(180 * COUVERTURE_MIN_FENETRE))

    # Sélection gloutonne
    def selection(cap: float) -> tuple[list, list]:
        choisis, rejets = [], []
        ordre = [s for s in ANCRES if s in df.index and df.loc[s, "eligible"]]
        ordre += [s for s in df.index if df.loc[s, "eligible"] and s not in ordre]
        for s in ordre:
            if len(choisis) >= PANIER_MAX:
                rejets.append({"symbole": s, "raison": f"panier complet à {PANIER_MAX}"})
                continue
            if s in ANCRES:
                choisis.append(s)
                continue
            if choisis:
                v = corr180.loc[s, choisis]
                if v.max() > cap:
                    rejets.append({"symbole": s, "raison": f"corrélation 180 j {v.max():.3f} avec {v.idxmax()} > {cap}"})
                    continue
            choisis.append(s)
        return choisis, rejets

    panier, rejets, cap_retenu, essais = [], [], None, []
    for cap in plafond_corr:
        panier, rejets = selection(cap)
        cap_retenu = cap
        essais.append({"plafond": cap, "n": len(panier)})
        if len(panier) >= PANIER_MIN:
            break
    if len(panier) < PANIER_MIN:
        anomalies.append(f"Panier de {len(panier)} paires seulement, sous le minimum de {PANIER_MIN}, malgré le plafond {cap_retenu}. "
                         "Le nombre d'éligibles est insuffisant.")
    df["dans_panier"] = df.index.isin(panier)
    df["raison_rejet_panier"] = ""
    for r in rejets:
        df.loc[r["symbole"], "raison_rejet_panier"] = r["raison"]

    # Contrôles
    # Contrôle à mesure égale : Bybit ne donne ici que le volume 24 h, on compare donc les deux tops sur 24 h.
    top_ctrl = u.get("top_volume_24h", u["top"])
    bn_bases = {x["base_norm"]: x["symbole"] for x in top_ctrl}
    communs = [b for b in u["bybit_top_bases"] if b in bn_bases]
    seulement_bybit = [b for b in u["bybit_top_bases"] if b not in bn_bases]
    seulement_binance = [x["base_norm"] for x in top_ctrl if x["base_norm"] not in u["bybit_top_bases"]]
    conflits = [x["symbole"] for x in u["top"] if x["base_norm"] in u["bybit_types_non_crypto"]]
    if conflits:
        anomalies.append(f"Tickers classés crypto chez Binance mais action, ETF, matière ou devise chez Bybit, homonymes à vérifier : {conflits}")
    decal = (u["heure_serveur_binance_ms"] - (u["heure_exchangeinfo_ms"] or u["heure_serveur_binance_ms"])) / 3_600_000
    if abs(decal) > 0.1:
        anomalies.append(f"Le serverTime de /fapi/v1/exchangeInfo retarde de {decal:.1f} h sur /fapi/v1/time. "
                         "La réponse exchangeInfo paraît servie depuis un cache. Les statuts de contrats peuvent dater de quelques heures.")
    return {"df": df, "corr180": corr180, "panier": panier, "rejets": rejets, "plafond": cap_retenu, "essais_plafond": essais,
            "controle": {"communs": communs, "seulement_bybit": seulement_bybit, "seulement_binance": seulement_binance},
            "anomalies": anomalies, "exclusions": pd.DataFrame(u["exclusions"])}


# ---------------------------------------------------------------------------
# Sorties
# ---------------------------------------------------------------------------
def fmt(v, n=2, vide="[n.d.]"):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return vide
    return f"{v:,.{n}f}".replace(",", " ")


def table_md(entetes: list, lignes: list) -> str:
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in lignes]
    return "\n".join(out)


def ecrire_markdown(brut: dict, an: dict, chemin: Path, chemins: dict) -> None:
    df, panier = an["df"], an["panier"]
    u = brut["univers"]
    instant = brut["instantanes"]
    heures = [s["heure"] for s in instant]
    m = []
    m.append(f"# Screener d'univers des perpétuels USDT, {brut['debut_collecte']}\n")
    m.append("Document de recherche. Aucune recommandation d'investissement, aucune promesse de gain. Aucun changement de statut de stratégie.\n")
    m.append("## 1. Biais et alerte, à lire d'abord\n")
    m.append(BIAIS + "\n")
    m.append(ALERTE + "\n")
    m.append("## 2. Sources et horodatage\n")
    m.append(table_md(["Donnée", "Source", "Heure UTC"], [
        ["Contrats et volume 24 h", "Binance /fapi/v1/exchangeInfo et /fapi/v1/ticker/24hr", u.get("heure_tickers_binance", u["heure_collecte_tickers"])],
        ["Contrôle croisé", "Bybit /v5/market/instruments-info et /v5/market/tickers", u["heure_collecte_tickers"]],
        ["Bougies 1 j, volume médian, corrélations", "Binance /fapi/v1/klines", brut["heure_klines"]],
        ["Financement sur un an", "Binance /fapi/v1/fundingRate et Bybit /v5/market/funding/history", brut["heure_financement"]],
        ["Taux d'emprunt sur marge spot", "bapi web Binance list-all (non documenté) et Bybit /v5/spot-margin-trade/data", brut["marge"]["heure"]],
        [f"{len(instant)} instantanés de carnets", "Binance /fapi/v1/depth (500 niveaux) et Bybit /v5/market/orderbook (500 niveaux)", f"{heures[0]} à {heures[-1]}" if heures else "[aucun]"],
    ]) + "\n")
    m.append(f"Collecte de {brut['debut_collecte']} à {brut['fin_collecte']}. {brut.get('appels_http', '[n.d.]')} appels HTTP. {len(brut.get('incidents_http', []))} incidents HTTP repris.\n")
    regle_mediane = brut.get("parametres", {}).get("regle_top") == REGLE_TOP
    jour = dt.datetime.fromisoformat(heures[0].replace("Z", "+00:00")) if heures else None
    if jour is not None:
        nom_jour = JOURS_FR[jour.weekday()]
        semaine = "un week-end" if jour.weekday() >= 5 else "un jour de semaine"
        m.append(f"Les instantanés sont pris un {nom_jour} UTC, donc {semaine}. ")
    m.append("Tous les instantanés tombent dans une même courte fenêtre. Ils ne mesurent donc pas la variation de liquidité sur plusieurs jours ni sur les heures ouvrées.\n")
    horo_panier = brut["debut_collecte"].replace(":", "").replace("-", "")
    m.append(f"Ce panier est figé par son horodatage {horo_panier}. Une relance crée d'autres fichiers et ne le remplace pas.\n")

    m.append("## 3. Méthode\n")
    if regle_mediane:
        m.append(f"L'univers part de {u['n_contrats_binance']} contrats Binance. Il en reste {u['n_perp_crypto_retenus']} perpétuels crypto USDT après exclusions, dont {u['n_classables']} ont {JOURS_VOLUME_MEDIAN} bougies 1 j closes. Les {len(df)} premiers par volume médian sur {JOURS_VOLUME_MEDIAN} jours forment le classement. Le volume 24 h reste affiché et ne sert plus qu'à la règle de pointe.\n")
    else:
        m.append(f"L'univers part de {u['n_contrats_binance']} contrats Binance. Il en reste {u['n_perp_crypto_retenus']} perpétuels crypto USDT après exclusions. Les {len(df)} premiers par volume 24 h forment le classement.\n")
    m.append("Le glissement simule un ordre au marché qui parcourt le carnet réel, mesuré contre le prix médian du carnet. Il inclut donc le demi-écart mais pas les frais. Le chiffre retenu est la médiane des instantanés, et le pire instantané figure dans le CSV.\n")
    m.append("Un perpétuel n'a pas d'emprunt. Son coût de portage est le financement. La moyenne annualisée est la somme des taux divisée par la durée couverte puis ramenée à 365 jours. Elle se lit du point de vue d'une position acheteuse, qui paie quand le taux est positif. Le 95e centile et la médiane sont exprimés par équivalent 8 h, car les intervalles varient de 1 h à 8 h selon les contrats.\n")
    m.append("Le taux d'emprunt sur marge spot est un instantané de niveau de base, sans historique. Le point d'accès Binance est celui du site web et n'est pas documenté, il peut changer sans préavis.\n")
    m.append("Pondérations du score, écrites en tête du script et fixées avant la première exécution.\n")
    m.append(table_md(["Critère", "Poids"], [[k, f"{v:.0%}"] for k, v in WEIGHTS.items()]) + "\n")
    m.append("Règles du panier. Une paire doit avoir au moins "
             f"{ANCIENNETE_MIN_J} jours d'ancienneté et {JOURS_MIN_FENETRE_RECHERCHE} jours de cotation avant le 30/06/2024. "
             f"Elle doit afficher un glissement à 50 000 USDT d'au plus {GLISSEMENT_50K_MAX_BPS:.0f} bps, un écart d'au plus {ECART_MAX_BPS:.0f} bps et un volume médian sur 30 jours d'au moins {VOLUME_MEDIAN_30J_MIN / 1e6:.0f} M USDT. "
             f"Le financement annualisé doit rester sous {FINANCEMENT_ABS_MAX_PCT:.0f} % en valeur absolue et le volume 24 h sous {RATIO_POINTE_VOLUME_MAX:.0f} fois la médiane sur 30 jours. La paire doit aussi exister sur Bybit à un prix cohérent. "
             f"BTC et ETH entrent d'abord, puis les autres par score décroissant, jusqu'à {PANIER_MAX} paires. Une paire est écartée si sa corrélation sur 180 jours dépasse le plafond avec une paire déjà choisie. Le plafond part de {PLAFOND_CORR_SUITE[0]} et ne s'assouplit par paliers que si le panier compte moins de {PANIER_MIN} paires.\n")
    m.append(f"Plafond effectif {an['plafond']}. Essais {an['essais_plafond']}.\n")

    m.append("## 4. Panier retenu\n")
    lignes = []
    for s in sorted(panier, key=lambda s: df.loc[s, "rang_score"]):
        r = df.loc[s]
        lignes.append([s, int(r["rang_score"]), fmt(r["score"], 1), fmt(r["volume_median_30j_usdt"] / 1e6, 0), fmt(r["bn_gliss_50k_moy_bps"], 2),
                       fmt(r["fin_moyenne_annualisee_pct"], 2), fmt(r["corr_btc_180j"], 2), fmt(r["beta_btc_180j"], 2), r["listing_binance"]])
    m.append(table_md(["Paire", "Rang score", "Score", "Vol. médian 30 j (M USDT)", "Gliss. 50k (bps)", "Financement annualisé (%)", "Corr. BTC 180 j", "Bêta BTC 180 j", "Listing"], lignes) + "\n")
    m.append("Écartées par la sélection alors qu'elles étaient éligibles.\n")
    m.append(table_md(["Paire", "Raison"], [[r["symbole"], r["raison"]] for r in an["rejets"]] or [["aucune", ""]]) + "\n")
    if an.get("temoin"):
        t = an["temoin"]
        m.append(f"Témoin sur cette même collecte, avec l'ancienne entrée au classement par volume 24 h. Panier de {len(t['panier'])} paires, plafond {t['plafond']}. Présentes seulement dans le témoin {', '.join(sorted(set(t['panier']) - set(panier))) or 'aucune'}. Présentes seulement dans le panier retenu {', '.join(sorted(set(panier) - set(t['panier']))) or 'aucune'}.\n")

    m.append(f"## 5. Classement des {len(df)} paires\n")
    lignes = []
    for s, r in df.iterrows():
        lignes.append([int(r["rang_score"]), s, fmt(r["score"], 1), fmt(r.get("rang_volume_median"), 0), int(r["rang_volume_24h"]), fmt(r["volume_24h_usdt"] / 1e6, 0), fmt(r.get("volume_median_30j_usdt", float("nan")) / 1e6, 0), fmt(r.get("ratio_pointe_volume"), 1),
                       fmt(r.get("bn_ecart_bps_med"), 2), fmt(r.get("bn_gliss_achat_1000_med"), 2), fmt(r.get("bn_gliss_vente_1000_med"), 2),
                       fmt(r.get("bn_gliss_achat_10000_med"), 2), fmt(r.get("bn_gliss_vente_10000_med"), 2),
                       fmt(r.get("bn_gliss_achat_50000_med"), 2), fmt(r.get("bn_gliss_vente_50000_med"), 2), "oui" if r["dans_panier"] else ("non" if r["eligible"] else "inéligible")])
    m.append(table_md(["Rang", "Paire", "Score", "Rang vol. méd.", "Rang vol. 24 h", "Vol. 24 h (M)", "Vol. méd. 30 j (M)", "Vol. 24 h / méd.", "Écart (bps)", "Achat 1k", "Vente 1k", "Achat 10k", "Vente 10k", "Achat 50k", "Vente 50k", "Panier"], lignes) + "\n")
    m.append("Glissements en bps, médiane des instantanés Binance.\n")
    n_pointes = int((pd.to_numeric(df["ratio_pointe_volume"], errors="coerce") > RATIO_POINTE_VOLUME_MAX).sum())
    if regle_mediane:
        m.append(f"{n_pointes} paires sur {len(df)} affichent un volume 24 h supérieur à {RATIO_POINTE_VOLUME_MAX:.0f} fois leur médiane sur 30 jours. L'entrée au classement et le score reposent sur la médiane. La règle de pointe dépend encore du volume 24 h, donc du jour de mesure.\n")
    else:
        m.append(f"{n_pointes} paires sur {len(df)} affichent un volume 24 h supérieur à {RATIO_POINTE_VOLUME_MAX:.0f} fois leur médiane sur 30 jours. Le classement par volume 24 h est donc très sensible au jour de mesure, et c'est pourquoi le score repose sur la médiane.\n")
    m.append("Motifs d'inéligibilité.\n")
    m.append(table_md(["Paire", "Motifs"], [[s, r["raisons_non_eligible"]] for s, r in df.iterrows() if not r["eligible"]] or [["aucune", ""]]) + "\n")

    lignes = []
    for s, r in df.iterrows():
        for prefixe, nom in (("bn", "Binance"), ("by", "Bybit")):
            for b in PROFONDEUR_BANDES_BPS:
                for cote in ("bid", "ask"):
                    n = r.get(f"{prefixe}_prof_{b}bps_{cote}_tronquee_instantanes")
                    if n is not None and n == n and n > 0:
                        lignes.append([s, nom, f"{b} bps", cote, int(n), fmt(r.get(f"{prefixe}_couverture_{cote}_bps_med"), 1), fmt(r.get(f"{prefixe}_prof_{b}bps_{cote}_med", float("nan")) / 1e6, 2)])
    if regle_mediane:
        m.append(f"Bandes de profondeur tronquées. Le carnet de {LIMITE_CARNET_BINANCE} niveaux s'arrête parfois avant la bande demandée. La valeur est alors une borne basse. Ces bandes n'entrent ni dans le score ni dans l'éligibilité.\n")
        m.append(table_md(["Paire", "Plateforme", "Bande", "Côté", "Instantanés tronqués", "Couverture médiane (bps)", "Profondeur lue, borne basse (M USDT)"], lignes or [["aucune", "", "", "", "", "", ""]]) + "\n")

    m.append("## 6. Financement et emprunt\n")
    lignes = []
    for s, r in df.iterrows():
        lignes.append([s, int(r.get("fin_n_periodes", 0) or 0), fmt(r.get("fin_couverture_j"), 0), fmt(r.get("fin_mediane_8h_pct"), 4), fmt(r.get("fin_moyenne_annualisee_pct"), 2),
                       fmt(r.get("fin_part_negative_pct"), 1), fmt(r.get("fin_p95_8h_pct"), 4), fmt(r.get("fin_by_moyenne_annualisee_pct"), 2),
                       fmt(r.get("emprunt_marge_binance_vip0_annuel_pct"), 2, "[non disponible]"), fmt(r.get("emprunt_marge_bybit_novip_annuel_pct"), 2, "[non disponible]")])
    m.append(table_md(["Paire", "Périodes", "Jours couverts", "Médiane 8 h (%)", "Moy. annualisée (%)", "Part négative (%)", "P95 8 h (%)", "Moy. annualisée Bybit (%)", "Emprunt marge Binance (% an)", "Emprunt marge Bybit (% an)"], lignes) + "\n")
    m.append("## 7. Corrélations et bêta\n")
    lignes = []
    for s, r in df.iterrows():
        lignes.append([s, fmt(r.get("corr_btc_90j"), 2), fmt(r.get("corr_btc_180j"), 2), fmt(r.get("corr_btc_365j"), 2), fmt(r.get("corr_eth_90j"), 2), fmt(r.get("corr_eth_180j"), 2), fmt(r.get("corr_eth_365j"), 2),
                       fmt(r.get("beta_btc_90j"), 2), fmt(r.get("beta_btc_180j"), 2), fmt(r.get("beta_btc_365j"), 2), fmt(r["anciennete_j"], 0), r["listing_binance"]])
    m.append(table_md(["Paire", "BTC 90", "BTC 180", "BTC 365", "ETH 90", "ETH 180", "ETH 365", "Bêta 90", "Bêta 180", "Bêta 365", "Âge (j)", "Listing"], lignes) + "\n")
    m.append("Rendements quotidiens en logarithme, clôture à clôture à 00:00 UTC, bougies closes seulement. Une fenêtre couverte à moins de 90 % reste vide.\n")
    autres = [s for s in panier if s != "BTCUSDT"]
    n_beta = sum(1 for s in autres if pd.notna(df.loc[s, "beta_btc_180j"]) and df.loc[s, "beta_btc_180j"] > 1)
    m.append(f"Dans le panier, le bêta à BTC sur 180 jours dépasse 1 pour {n_beta} paires sur {len(autres)} hors BTC. BTC contre lui-même vaut 1 par construction et n'est pas compté.\n")

    c = an["controle"]
    m.append("## 8. Contrôle croisé Bybit\n")
    if regle_mediane:
        m.append("Ce contrôle compare les deux tops par volume 24 h, seule mesure relevée chez Bybit.\n")
    m.append(f"{len(c['communs'])} bases sont communes aux deux classements de {len(df)} paires. Seulement dans le classement Bybit {', '.join(c['seulement_bybit']) or 'aucune'}. Seulement dans le classement Binance {', '.join(c['seulement_binance']) or 'aucune'}.\n")
    lignes = []
    for s, r in df.iterrows():
        vb, vy = r.get("volume_24h_usdt"), r.get("bybit_volume_24h_usdt")
        lignes.append([s, r.get("bybit_symbole") if isinstance(r.get("bybit_symbole"), str) else "[absent]", fmt(r.get("bybit_rang_volume"), 0), fmt(vy / 1e6 if vy == vy else None, 0),
                       fmt(vy / vb if (vy == vy and vb) else None, 2), fmt(r.get("by_ecart_bps_med"), 2), fmt(r.get("by_gliss_50k_moy_bps"), 2), fmt(r.get("ecart_prix_binance_bybit_pct"), 3)])
    m.append(table_md(["Paire", "Symbole Bybit", "Rang Bybit", "Vol. 24 h Bybit (M)", "Ratio Bybit / Binance", "Écart Bybit (bps)", "Gliss. 50k Bybit (bps)", "Écart de prix médian (%)"], lignes) + "\n")

    m.append("L'écart de prix est la médiane, sur les instantanés, du prix médian du carnet Bybit contre celui de Binance, multiplicateurs de contrat retirés.\n")
    m.append("## 9. Exclusions\n")
    ex = an["exclusions"]
    if len(ex):
        comptes = ex.groupby(["plateforme", "raison"]).agg(n=("symbole", "count"), volume=("volume_24h_usdt", "sum")).reset_index().sort_values(["plateforme", "n"], ascending=[True, False])
        m.append(table_md(["Plateforme", "Raison", "Contrats", "Volume 24 h cumulé (M USDT)"], [[r.plateforme, r.raison, r.n, fmt(r.volume / 1e6, 0)] for r in comptes.itertuples()]) + "\n")
        top_ex = ex[ex["plateforme"] == "binance"].sort_values("volume_24h_usdt", ascending=False).head(15)
        m.append("Plus gros volumes exclus chez Binance.\n")
        m.append(table_md(["Symbole", "Raison", "Volume 24 h (M USDT)"], [[r.symbole, r.raison, fmt(r.volume_24h_usdt / 1e6, 0)] for r in top_ex.itertuples()]) + "\n")
    m.append(f"Liste complète dans {chemins['exclusions'].name}.\n")
    m.append("Les jetons Alpha de Binance restent dans le classement car ils sont crypto, et le CSV les signale dans la colonne alpha.\n")

    m.append("## 10. Anomalies et lacunes\n")
    if an["anomalies"]:
        m.append(table_md(["N°", "Constat"], [[i, a] for i, a in enumerate(an["anomalies"], 1)]) + "\n")
    else:
        m.append("Aucune erreur de collecte.\n")
    m.append("Sources : Binance Futures REST public (fapi.binance.com), Bybit v5 REST public (api.bybit.com), bapi web public de Binance pour la marge. Aucune authentification.\n")
    chemin.write_text("\n".join(m), encoding="utf-8")


def ecrire_sorties(brut: dict, an: dict, horo: str, dossier: Path) -> dict:
    dossier.mkdir(parents=True, exist_ok=True)
    chemins = {
        "csv": dossier / f"screener_{horo}.csv",
        "json": dossier / f"screener_{horo}.json",
        "md": dossier / f"screener_{horo}.md",
        "exclusions": dossier / f"screener_{horo}_exclusions.csv",
        "corr180": dossier / f"screener_{horo}_corr180j.csv",
        "panier": dossier / f"screener_{horo}_panier.csv",
    }
    if brut["univers"].get("tous_volumes"):
        chemins["volumes"] = dossier / f"screener_{horo}_volumes_tous.csv"
        pd.DataFrame(brut["univers"]["tous_volumes"]).to_csv(chemins["volumes"], index=False, encoding="utf-8")
    df = an["df"]
    df.to_csv(chemins["csv"], index=False, encoding="utf-8")
    an["exclusions"].sort_values(["plateforme", "volume_24h_usdt"], ascending=[True, False]).to_csv(chemins["exclusions"], index=False, encoding="utf-8")
    an["corr180"].round(4).to_csv(chemins["corr180"], encoding="utf-8")
    colonnes = ["rang_score", "symbole", "paire_freqtrade", "score", "volume_median_30j_usdt", "bn_gliss_50k_moy_bps", "fin_moyenne_annualisee_pct",
                "corr_btc_180j", "beta_btc_180j", "listing_binance", "bybit_symbole"]
    df[df["dans_panier"]][colonnes].to_csv(chemins["panier"], index=False, encoding="utf-8")
    enr = {
        "avertissement_biais": BIAIS, "alerte_binance": ALERTE,
        "debut_collecte": brut["debut_collecte"], "fin_collecte": brut["fin_collecte"],
        "heures": {"tickers": brut["univers"]["heure_collecte_tickers"], "klines": brut["heure_klines"], "financement": brut["heure_financement"],
                   "marge": brut["marge"]["heure"], "instantanes": [s["heure"] for s in brut["instantanes"]]},
        "ponderations": WEIGHTS,
        "regles_panier": {"anciennete_min_j": ANCIENNETE_MIN_J, "jours_min_avant_2024_06_30": JOURS_MIN_FENETRE_RECHERCHE,
                          "glissement_50k_max_bps": GLISSEMENT_50K_MAX_BPS, "ecart_max_bps": ECART_MAX_BPS,
                          "volume_median_30j_min": VOLUME_MEDIAN_30J_MIN, "financement_abs_max_pct": FINANCEMENT_ABS_MAX_PCT,
                          "ratio_pointe_max": RATIO_POINTE_VOLUME_MAX, "plafond_corr_suite": PLAFOND_CORR_SUITE,
                          "plafond_effectif": an["plafond"], "essais_plafond": an["essais_plafond"]},
        "regle_top": brut.get("parametres", {}).get("regle_top", "volume_24h"),
        "panier_fige_par_horodatage": horo,
        "instantanes_week_end": all(dt.datetime.fromisoformat(s["heure"].replace("Z", "+00:00")).weekday() >= 5 for s in brut["instantanes"]),
        "temoin_regle_volume_24h": an.get("temoin"),
        "panier": an["panier"], "panier_freqtrade": [df.loc[s, "paire_freqtrade"] for s in an["panier"]],
        "rejets": an["rejets"], "controle_bybit": an["controle"], "anomalies": an["anomalies"],
        "incidents_http": brut.get("incidents_http", []), "appels_http": brut.get("appels_http"),
        "classement": json.loads(df.to_json(orient="records")),
    }
    chemins["json"].write_text(json.dumps(enr, ensure_ascii=False, indent=1), encoding="utf-8")
    ecrire_markdown(brut, an, chemins["md"], chemins)
    return chemins


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=TOP_N)
    ap.add_argument("--snapshots", type=int, default=SNAPSHOTS_DEFAUT)
    ap.add_argument("--intervalle", type=int, default=INTERVALLE_SNAPSHOT_S)
    ap.add_argument("--reuse-raw", type=Path, help="réutilise une collecte brute sans nouvel appel réseau")
    ap.add_argument("--sorties", type=Path, default=SORTIES)
    ap.add_argument("--cache", type=Path, default=CACHE, help="dossier de la collecte brute, pour un rejeu hors du dépôt")
    args = ap.parse_args()

    if args.reuse_raw:
        with gzip.open(args.reuse_raw, "rt", encoding="utf-8") as f:
            brut = json.load(f)
        log(f"Collecte réutilisée {args.reuse_raw}, heure {brut['debut_collecte']}")
    else:
        brut = collecter(args.top, args.snapshots, args.intervalle)
        args.cache.mkdir(parents=True, exist_ok=True)
        chemin = args.cache / f"brut_{brut['debut_collecte'].replace(':', '').replace('-', '')}.json.gz"
        with gzip.open(chemin, "wt", encoding="utf-8") as f:
            json.dump(brut, f)
        log(f"Collecte brute enregistrée {chemin}")
    horo = brut["debut_collecte"].replace(":", "").replace("-", "")
    an = analyser(brut)
    if "top_volume_24h" in brut["univers"]:
        temoin = analyser({**brut, "univers": {**brut["univers"], "top": brut["univers"]["top_volume_24h"]}})
        an["temoin"] = {"panier": temoin["panier"], "plafond": temoin["plafond"], "rejets": temoin["rejets"],
                        "classement": temoin["df"]["symbole"].tolist(),
                        "eligibles": temoin["df"][temoin["df"]["eligible"]]["symbole"].tolist()}
        log(f"Témoin règle volume 24 h : {len(temoin['panier'])} paires {temoin['panier']}")
    chemins = ecrire_sorties(brut, an, horo, args.sorties)
    log(f"Panier {len(an['panier'])} paires, plafond {an['plafond']} : {an['panier']}")
    for k, v in chemins.items():
        log(f"Sortie {k} {v}")
    if an["anomalies"]:
        log(f"{len(an['anomalies'])} anomalies consignées")
    return 0


if __name__ == "__main__":
    sys.exit(main())
