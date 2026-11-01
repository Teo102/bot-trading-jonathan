#!/usr/bin/env python3
"""Audit des données de STRAT-20261031-03 : balayage Binance et univers à la date.

Dates et volumes seulement. De chaque bougie, le script ne garde que l'heure d'ouverture
et le volume en USDT (indices 0 et 7). Il ne lit aucun prix et ne calcule aucun rendement.
Le carnet (fiche § 2.5) est hors de ce script, car un instantané passé ne se rejoue pas.

Points d'accès publics en lecture seule, sans clé. Aucun ordre.

Usage : python -I audit_univers.py [--cache DOSSIER] [--ref 2026-10-31]
Sortie : resultats/audit_univers_<horodatage UTC>.json
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

FAPI = "https://fapi.binance.com"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
VISION = "https://data.binance.vision"
CATALOGUE = "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query"
DETAIL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
DEBUT_MS = int(pd.Timestamp("2019-09-01", tz="UTC").timestamp() * 1000)
SORTIES = Path(__file__).resolve().parent / "resultats"

# Règles préenregistrées de la fiche, § 1.3 et § 3. Rien n'est optimisé ici.
TOP = 30
ANCIENNETE = 90
FENETRE_VOLUME = 30
SEUIL_ARRET_J = 3
STABLES = ["USDC", "BUSD", "TUSD", "DAI", "FDUSD", "USDP", "USD1", "USDE", "RLUSD", "BFUSD", "PYUSD"]
INDICES_ABSENTS = ["FOOTBALLUSDT", "BLUEBIRDUSDT", "DOTECOUSDT"]
BLOCS = {
    "developpement": ("2021-01-04", "2024-06-24"),
    "validation": ("2024-07-01", "2025-07-21"),
    "hors_echantillon": ("2025-08-04", "2026-10-19"),
}
SEMAINE_EXCLUE = "2025-07-28"  # fiche § 3, semaine à cheval, dans aucun bloc
FENETRE_ANNONCE_J = 90  # au-delà, le titre désigne un autre événement que cet arrêt (BLZ, 859 j)

# Valeurs publiées par la fiche le 31/10/2026, avant le rejeu. Servent seulement au relevé d'écarts.
PUBLIE = {
    "contrats_actifs_coin": 519, "exchangeinfo_total": 942, "perp_usdt": 659, "perp_trading": 522, "perp_settling": 136, "perp_attente": 1,
    "vision_klines": 1056, "vision_klines_usdt": 900, "vision_financement": 988, "vision_marque": 1039, "vision_metrics": 1052,
    "arretes_avec_klines_vision": 162, "arretes_avec_financement_vision": 162, "arretes_avec_marque_vision": 162, "arretes_avec_metrics_vision": 160,
    "balayes": 924, "avec_volume": 919, "vivants": 757, "arretes": 162, "arretes_settling": 135, "arretes_absents_ei": 27,
    "arrets_2020": 1, "arrets_2021": 2, "arrets_2022": 14, "arrets_2023": 3, "arrets_2024": 29, "arrets_2025": 46, "arrets_2026": 67,
    "delivery_egale_dernier_volume": 135, "interruptions_sup_7j": 0, "onboard_avance_sup_2j": 12, "onboard_avance_max_j": 424,
    "zombies_noms": 152, "zombies_mediane_j": 270.5, "zombies_max_j": 1597, "zombies_ftt": 284, "zombies_sc": 330,
    "candidats_04_01_2021": 58,
    "dev_semaines": 182, "dev_cand_min": 58, "dev_cand_med": 130, "dev_cand_max": 244, "dev_r30_min": 17.61, "dev_r30_med": 111.48, "dev_noms": 147, "dev_arretes_moy": 4.09, "dev_absents_moy": 2.20,
    "val_semaines": 56, "val_cand_min": 243, "val_cand_med": 278.5, "val_cand_max": 385, "val_r30_min": 86.38, "val_r30_med": 125.32, "val_noms": 93, "val_arretes_moy": 1.25, "val_absents_moy": 0.14,
    "hors_semaines": 64, "hors_cand_min": 398, "hors_cand_med": 504.5, "hors_cand_max": 517, "hors_r30_min": 34.66, "hors_r30_med": 74.27, "hors_noms": 107, "hors_arretes_moy": 0.11, "hors_absents_moy": 0,
    "noms_top30": 235, "noms_arretes": 39, "noms_absents": 11, "part_presences_arretes_pct": 9.0, "part_presences_absents_pct": 4.5, "rotation_noms_semaine": 2.14, "arrets_sous_30j": 7,
    "annonces_articles": 446, "annonces_titres_futures": 78, "annonces_rapprochees": 46, "annonces_delai_median_j": 6.5, "annonces_delai_min_j": 0, "annonces_delai_max_j": 56,
}


def horo() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(*a) -> None:
    print(horo(), *a, file=sys.stderr, flush=True)


class Client:
    """Client public avec reprises et respect du poids Binance."""

    def __init__(self) -> None:
        self.s = requests.Session()
        self.appels = 0
        self.incidents: list[str] = []

    def get(self, url: str, params: dict | None = None, timeout: int = 60, essais: int = 6) -> requests.Response:
        for i in range(essais):
            self.appels += 1
            try:
                r = self.s.get(url, params=params, timeout=timeout)
            except requests.RequestException as e:
                self.incidents.append(f"{horo()} {url} {type(e).__name__}")
                time.sleep(2 * (i + 1))
                continue
            if r.status_code in (418, 429) or r.status_code >= 500:
                attente = int(r.headers.get("Retry-After", 5 * (i + 1)))
                self.incidents.append(f"{horo()} {url} HTTP {r.status_code}, attente {attente} s")
                time.sleep(attente)
                continue
            if int(r.headers.get("X-MBX-USED-WEIGHT-1M", 0) or 0) > 1800:
                time.sleep(20)
            return r
        raise RuntimeError(f"Échec après {essais} essais : {url}")


def lister_dossiers(c: Client, prefixe: str) -> list[str]:
    """Sous-dossiers d'un préfixe de l'archive publique."""
    sortie: list[str] = []
    marqueur = ""
    while True:
        r = c.get(S3, {"delimiter": "/", "prefix": prefixe, "marker": marqueur}, timeout=120)
        r.raise_for_status()
        sortie += re.findall(r"<Prefix>" + re.escape(prefixe) + r"([^/<]+)/</Prefix>", r.text)
        suite = re.search(r"<NextMarker>([^<]+)</NextMarker>", r.text)
        if "<IsTruncated>true" not in r.text or not suite:
            return sortie
        marqueur = suite.group(1)


def lister_cles(c: Client, prefixe: str, max_pages: int = 1) -> list[str]:
    """Clés d'un préfixe, ordre alphabétique, donc chronologique pour ces archives."""
    sortie: list[str] = []
    marqueur = ""
    for _ in range(max_pages):
        r = c.get(S3, {"prefix": prefixe, "marker": marqueur}, timeout=120)
        r.raise_for_status()
        cles = re.findall(r"<Key>([^<]+)</Key>", r.text)
        sortie += cles
        if "<IsTruncated>true" not in r.text or not cles:
            break
        marqueur = cles[-1]
    return sortie


def lire_volumes_api(c: Client, sym: str) -> tuple[list[tuple[int, float]], str | None]:
    """Bougies 1 d, heure d'ouverture et volume en USDT. Le reste de la ligne est jeté."""
    lignes: list[tuple[int, float]] = []
    debut = DEBUT_MS
    while True:
        r = c.get(f"{FAPI}/fapi/v1/klines", {"symbol": sym, "interval": "1d", "startTime": debut, "limit": 1000})
        if r.status_code == 400:
            return lignes, str(r.json().get("code"))
        r.raise_for_status()
        k = r.json()
        lignes += [(int(x[0]), float(x[7])) for x in k]
        if len(k) < 1000:
            return lignes, None
        debut = int(k[-1][0]) + 86_400_000
        time.sleep(0.13)


def lire_volumes_archive(c: Client, sym: str) -> list[tuple[int, float]]:
    """Archive mensuelle 1 d, en mémoire, colonnes 0 et 7 seulement."""
    lignes: list[tuple[int, float]] = []
    for cle in lister_cles(c, f"data/futures/um/monthly/klines/{sym}/1d/", max_pages=3):
        if not cle.endswith(".zip"):
            continue
        r = c.get(f"{VISION}/{cle}", timeout=120)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z, z.open(z.namelist()[0]) as f:
            df = pd.read_csv(f, header=None, usecols=[0, 7], dtype=str)
        df = df[df[0].str.fullmatch(r"\d+")]
        lignes += [(int(a), float(b)) for a, b in zip(df[0], df[7])]
    return lignes


def balayer(c: Client, symboles: list[str], cache: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Table longue symbole, jour, volume. Le cache évite un second balayage en cas de reprise."""
    cache.mkdir(parents=True, exist_ok=True)
    tables, refus = [], {}
    for i, sym in enumerate(symboles):
        chemin = cache / f"{sym}.csv"
        refus_chemin = cache / f"{sym}.refus"
        if refus_chemin.exists():
            refus[sym] = refus_chemin.read_text()
            continue
        if chemin.exists():
            df = pd.read_csv(chemin)
        else:
            lignes, code = lire_volumes_api(c, sym)
            if code:
                refus[sym] = code
                refus_chemin.write_text(code)
                continue
            df = pd.DataFrame(lignes, columns=["t", "v"])
            df.to_csv(chemin, index=False)
            time.sleep(0.13)
        df["sym"] = sym
        tables.append(df)
        if i % 100 == 0:
            log(f"balayage {i}/{len(symboles)}")
    tout = pd.concat(tables, ignore_index=True)
    tout["jour"] = pd.to_datetime(tout["t"], unit="ms", utc=True).dt.tz_localize(None).dt.floor("D")
    return tout[["sym", "jour", "v"]], refus


def lundis_blocs() -> list[tuple[pd.Timestamp, str]]:
    sortie = []
    for bloc, (a, b) in BLOCS.items():
        sortie += [(t, bloc) for t in pd.date_range(a, b, freq="7D")]
    return sortie


def univers_a_date(volumes: pd.DataFrame, exclus: set[str], top: int = TOP) -> tuple[dict, dict]:
    """Règle du § 1.3, sans aucune donnée postérieure à t.

    Volumes : matrice jours × symboles, 0 pour un jour sans bougie.
    Vivant à t : volume non nul le jour t − 1, seul fait connu au signal.
    Ancienneté : premier jour de volume non nul au plus tard à t − 90.
    """
    premier = (volumes > 0).idxmax()
    composition, details = {}, {}
    un_j = pd.Timedelta(days=1)
    for t, bloc in lundis_blocs():
        hier = t - un_j
        vivant = volumes.loc[hier] > 0
        ancien = premier <= t - pd.Timedelta(days=ANCIENNETE)
        a_vu = (volumes.loc[:hier] > 0).any()
        candidats = [s for s in volumes.columns if vivant[s] and ancien[s] and a_vu[s] and s not in exclus]
        fenetre = volumes.loc[t - pd.Timedelta(days=FENETRE_VOLUME):hier, candidats]
        assert len(fenetre) == FENETRE_VOLUME
        med = fenetre.median()
        ordre = sorted(candidats, key=lambda s: (-med[s], s))[:top]
        composition[t.strftime("%Y-%m-%d")] = ordre
        details[t.strftime("%Y-%m-%d")] = {"bloc": bloc, "candidats": len(candidats), "volume_rang_30": float(med[ordre[-1]]) if len(ordre) == top else None}
    return composition, details


def stats_univers(composition: dict, details: dict, arretes: set[str], absents: set[str], dernier: dict) -> dict:
    res: dict = {"blocs": {}}
    for bloc in BLOCS:
        dates = [d for d, v in details.items() if v["bloc"] == bloc]
        cand = [details[d]["candidats"] for d in dates]
        r30 = [details[d]["volume_rang_30"] / 1e6 for d in dates]
        noms = {s for d in dates for s in composition[d]}
        res["blocs"][bloc] = {
            "semaines": len(dates), "premier": dates[0], "dernier": dates[-1],
            "candidats_min": min(cand), "candidats_mediane": float(np.median(cand)), "candidats_max": max(cand),
            "volume_rang_30_min_MUSDT": round(min(r30), 2), "volume_rang_30_mediane_MUSDT": round(float(np.median(r30)), 2),
            "date_volume_rang_30_min": dates[int(np.argmin(r30))],
            "noms_uniques": len(noms),
            "arretes_moyenne_sur_30": round(float(np.mean([len(set(composition[d]) & arretes) for d in dates])), 2),
            "absents_ei_moyenne_sur_30": round(float(np.mean([len(set(composition[d]) & absents) for d in dates])), 2),
        }
    dates = list(composition)
    presences = collections.Counter(s for d in dates for s in composition[d])
    total = sum(presences.values())
    n_arr = sorted(s for s in presences if s in arretes)
    n_abs = sorted(s for s in presences if s in absents)
    entrees = sum(len(set(composition[b]) - set(composition[a])) for a, b in zip(dates, dates[1:]))
    res.update({
        "semaines": len(dates),
        "entrees_total": entrees,
        "transitions": len(dates) - 1,
        "noms_top30": len(presences),
        "noms_arretes": len(n_arr),
        "noms_absents_ei": len(n_abs),
        "liste_absents_ei": n_abs,
        "part_presences_arretes_pct": round(100 * sum(presences[s] for s in n_arr) / total, 2),
        "part_presences_absents_pct": round(100 * sum(presences[s] for s in n_abs) / total, 2),
        "rotation_noms_par_semaine": round(float(np.mean([len(set(composition[b]) - set(composition[a])) for a, b in zip(dates, dates[1:])])), 2),
    })
    derniere_presence = {}
    for d in dates:
        for s in composition[d]:
            derniere_presence[s] = d
    courts = []
    for s in n_arr:
        delai = (pd.Timestamp(dernier[s]) - pd.Timestamp(derniere_presence[s])).days
        if delai < 30:
            courts.append({"symbole": s, "delai_j": delai, "derniere_presence": derniere_presence[s], "dernier_volume": dernier[s]})
    res["arrets_sous_30j"] = sorted(courts, key=lambda x: (x["delai_j"], x["symbole"]))
    return res


def sondes(c: Client) -> dict:
    """Disponibilité des points d'accès. On garde les codes, les comptes et les dates, jamais les valeurs."""
    out: dict = {}

    def premier_temps(chemin: str, params: dict, cle) -> dict:
        r = c.get(f"{FAPI}{chemin}", params)
        if r.status_code != 200:
            return {"http": r.status_code, "code": r.json().get("code")}
        j = r.json()
        return {"http": 200, "lignes": len(j), "premiere_date": pd.Timestamp(cle(j[0]), unit="ms").strftime("%Y-%m-%d") if j else None}

    # startTime=0 renverrait les événements les plus récents, d'où un début explicite. Les taux ne sont pas lus.
    out["financement"] = {s: {
        "premier": premier_temps("/fapi/v1/fundingRate", {"symbol": s, "startTime": DEBUT_MS, "limit": 1}, lambda x: x["fundingTime"]),
        "dernier": premier_temps("/fapi/v1/fundingRate", {"symbol": s, "limit": 1}, lambda x: x["fundingTime"]),
    } for s in ["LUNAUSDT", "FTTUSDT", "SRMUSDT", "SCUSDT"]}
    out["luna_1h"] = {
        "markPriceKlines": premier_temps("/fapi/v1/markPriceKlines", {"symbol": "LUNAUSDT", "interval": "1h", "startTime": 0, "limit": 1}, lambda x: x[0]),
        "premiumIndexKlines": premier_temps("/fapi/v1/premiumIndexKlines", {"symbol": "LUNAUSDT", "interval": "1h", "startTime": 0, "limit": 1}, lambda x: x[0]),
        "indexPriceKlines": premier_temps("/fapi/v1/indexPriceKlines", {"pair": "LUNAUSDT", "interval": "1h", "startTime": 0, "limit": 1}, lambda x: x[0]),
    }
    oi = "/futures/data/openInterestHist"
    t_2021 = int(pd.Timestamp("2021-06-01", tz="UTC").timestamp() * 1000)
    out["interet_ouvert_api"] = {
        "BTC_recent": premier_temps(oi, {"symbol": "BTCUSDT", "period": "1d", "limit": 500}, lambda x: x["timestamp"]),
        "BTC_2021": premier_temps(oi, {"symbol": "BTCUSDT", "period": "1d", "limit": 30, "startTime": t_2021}, lambda x: x["timestamp"]),
        "FTT": premier_temps(oi, {"symbol": "FTTUSDT", "period": "1d", "limit": 30}, lambda x: x["timestamp"]),
    }

    def premiere_cle(prefixe: str) -> str | None:
        cles = [k for k in lister_cles(c, prefixe) if k.endswith(".zip")]
        return cles[0].rsplit("/", 1)[1] if cles else None

    out["archives_premier_fichier"] = {
        "metrics_BTC": premiere_cle("data/futures/um/daily/metrics/BTCUSDT/"),
        "metrics_LUNA": premiere_cle("data/futures/um/daily/metrics/LUNAUSDT/"),
        "bookDepth_BTC": premiere_cle("data/futures/um/daily/bookDepth/BTCUSDT/"),
        "bookTicker_BTC": premiere_cle("data/futures/um/daily/bookTicker/BTCUSDT/") or premiere_cle("data/futures/um/monthly/bookTicker/BTCUSDT/"),
    }
    return out


def annonces(c: Client, arretes: set[str], dernier: dict) -> dict:
    """Catalogue public non documenté. Titres et dates de publication, rapprochement par le titre."""
    articles: list[dict] = []
    page = 1
    while True:
        r = c.get(CATALOGUE, {"catalogId": 161, "pageNo": page, "pageSize": 50})
        r.raise_for_status()
        lot = r.json()["data"]["articles"]
        articles += lot
        if len(lot) < 50:
            break
        page += 1
        time.sleep(0.3)
    futures = [a for a in articles if re.search(r"futures|perpetual|contract", a["title"], re.I)]
    titres = []
    for a in futures:
        r = c.get(DETAIL, {"articleCode": a["code"]})
        r.raise_for_status()
        pub = (r.json().get("data") or {}).get("publishDate")
        titres.append({"titre": a["title"], "publication": pd.Timestamp(pub, unit="ms").strftime("%Y-%m-%d") if pub else None})
        time.sleep(0.2)
    # Rapprochement : racine du symbole présente comme mot en capitales dans le titre, publication avant l'arrêt.
    meilleurs: dict[str, dict] = {}
    hors_fenetre: dict[str, dict] = {}
    for t in titres:
        if not t["publication"]:
            continue
        jetons = set(re.findall(r"[0-9A-Z]{2,}", t["titre"]))
        for s in arretes:
            racine = s[:-4]
            if s in jetons or racine in jetons:
                delai = (pd.Timestamp(dernier[s]) - pd.Timestamp(t["publication"])).days
                if delai >= 0 and (s not in meilleurs or delai < meilleurs[s]["delai_j"]):
                    meilleurs[s] = {"delai_j": delai, "publication": t["publication"], "titre": t["titre"]}
    for s in list(meilleurs):
        if meilleurs[s]["delai_j"] > FENETRE_ANNONCE_J:
            hors_fenetre[s] = meilleurs.pop(s)
    delais = [v["delai_j"] for v in meilleurs.values()]
    dates = sorted(t["publication"] for t in titres if t["publication"])
    return {
        "articles": len(articles), "titres_futures": len(futures), "publication_min": dates[0] if dates else None, "publication_max": dates[-1] if dates else None,
        "rapproches": len(meilleurs), "delai_median_j": float(np.median(delais)) if delais else None,
        "delai_min_j": min(delais) if delais else None, "delai_max_j": max(delais) if delais else None,
        "fenetre_j": FENETRE_ANNONCE_J, "hors_fenetre": hors_fenetre, "detail": dict(sorted(meilleurs.items())), "titres": titres,
    }


def controle_calendrier(ref: pd.Timestamp) -> dict:
    """Tous les lundis de la première à la dernière borne, et ceux qui ne tombent dans aucun bloc."""
    dans_blocs = {t.strftime("%Y-%m-%d") for t, _ in lundis_blocs()}
    tous = pd.date_range(BLOCS["developpement"][0], ref, freq="7D")
    hors = [t.strftime("%Y-%m-%d") for t in tous if t.strftime("%Y-%m-%d") not in dans_blocs]
    return {
        "tous_les_rebalancements_sont_des_lundis": all(t.dayofweek == 0 for t, _ in lundis_blocs()),
        "lundis_du_premier_a_la_reference": len(tous),
        "lundis_dans_un_bloc": len(dans_blocs),
        "lundis_hors_bloc": [{"date": d, "jour_semaine": pd.Timestamp(d).day_name(), "sortie": (pd.Timestamp(d) + pd.Timedelta(days=7)).strftime("%Y-%m-%d")} for d in hors],
    }


def ecarts(mesure: dict) -> list[dict]:
    sortie = []
    for k, publie in PUBLIE.items():
        if k not in mesure:
            sortie.append({"mesure": k, "publie": publie, "rejoue": None, "etat": "non rejoue"})
        elif mesure[k] != publie:
            sortie.append({"mesure": k, "publie": publie, "rejoue": mesure[k], "etat": "ecart"})
    return sortie


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, default=Path("/tmp/audit_univers_cache"))
    p.add_argument("--ref", default="2026-10-31", help="Dernier jour pris en compte, figé pour rester comparable à l'audit initial")
    a = p.parse_args()
    debut = horo()
    ref = pd.Timestamp(a.ref)
    c = Client()

    log("exchangeInfo")
    ei = c.get(f"{FAPI}/fapi/v1/exchangeInfo").json()
    horo_ei = horo()
    sy = ei["symbols"]
    usdt_perp = [s for s in sy if s["quoteAsset"] == "USDT" and s["contractType"] == "PERPETUAL"]
    usdt_tous = [s for s in sy if s["quoteAsset"] == "USDT" and s["contractType"] in ("PERPETUAL", "TRADIFI_PERPETUAL")]
    statuts = collections.Counter(s["status"] for s in usdt_perp)
    actifs_coin = sum(s["status"] == "TRADING" and s["underlyingType"] == "COIN" for s in usdt_perp)
    infos = {s["symbol"]: s for s in usdt_tous}

    log("listing des archives")
    v_klines = lister_dossiers(c, "data/futures/um/monthly/klines/")
    v_fin = lister_dossiers(c, "data/futures/um/monthly/fundingRate/")
    v_marque = lister_dossiers(c, "data/futures/um/monthly/markPriceKlines/")
    v_metrics = lister_dossiers(c, "data/futures/um/daily/metrics/")
    horo_s3 = horo()
    v_usdt = [s for s in v_klines if s.endswith("USDT")]
    symboles = sorted(set(v_usdt) | set(infos))

    log(f"balayage de {len(symboles)} symboles")
    debut_balayage = horo()
    long, refus = balayer(c, symboles, a.cache)
    fin_balayage = horo()
    # Une réponse partielle de l'API a été observée au rejeu du 01/11/2026 07:54 UTC (MCDUSDT, 7 lignes puis 27).
    # Tout symbole dont le premier volume arrive plus de 2 jours après onboardDate est donc relu une fois.
    relectures = {}
    for s, j in long[long["v"] > 0].groupby("sym")["jour"].min().items():
        if s in infos and (j - pd.Timestamp(infos[s]["onboardDate"], unit="ms").floor("D")).days > 2:
            lignes, code = lire_volumes_api(c, s)
            avant = int((long["sym"] == s).sum())
            relectures[s] = {"lignes_avant": avant, "lignes_relecture": len(lignes), "code": code}
            if not code and len(lignes) > avant:
                d = pd.DataFrame(lignes, columns=["t", "v"])
                d.to_csv(a.cache / f"{s}.csv", index=False)
                d["sym"] = s
                d["jour"] = pd.to_datetime(d["t"], unit="ms", utc=True).dt.tz_localize(None).dt.floor("D")
                long = pd.concat([long[long["sym"] != s], d[["sym", "jour", "v"]]], ignore_index=True)
    long = long[long["jour"] <= ref]
    empreinte =hashlib.sha256(pd.util.hash_pandas_object(long.sort_values(["sym", "jour"]), index=False).values.tobytes()).hexdigest()

    # Ce que l'API refuse est relu dans l'archive, pour une mesure à part.
    log(f"refus API : {refus}")
    archives_refus = {}
    lignes_archive = []
    for s in sorted(refus):
        lignes = lire_volumes_archive(c, s)
        if lignes:
            d = pd.DataFrame(lignes, columns=["t", "v"]).drop_duplicates("t")
            d["jour"] = pd.to_datetime(d["t"], unit="ms").dt.floor("D")
            d["sym"] = s
            lignes_archive.append(d[["sym", "jour", "v"]])
            nz = d[d["v"] > 0]
            archives_refus[s] = {"code_api": refus[s], "premier_volume": nz["jour"].min().strftime("%Y-%m-%d"), "dernier_volume": nz["jour"].max().strftime("%Y-%m-%d")}
        else:
            archives_refus[s] = {"code_api": refus[s], "premier_volume": None, "dernier_volume": None}

    jours = pd.date_range(long["jour"].min(), ref, freq="D")
    volumes = long.pivot_table(index="jour", columns="sym", values="v", aggfunc="first").reindex(jours)
    lignes_par_sym = long.groupby("sym")["jour"].agg(["min", "max", "count"])
    nz = long[long["v"] > 0]
    premier = nz.groupby("sym")["jour"].min()
    dernier = nz.groupby("sym")["jour"].max()
    avec_volume = sorted(premier.index)
    limite = ref - pd.Timedelta(days=SEUIL_ARRET_J)
    arretes = {s for s in avec_volume if dernier[s] < limite}
    vivants = set(avec_volume) - arretes
    dernier_txt = {s: dernier[s].strftime("%Y-%m-%d") for s in avec_volume}

    absents = arretes - set(infos)
    settling = {s for s in arretes if infos.get(s, {}).get("status") == "SETTLING"}
    autres_statuts = {s: infos[s]["status"] for s in arretes & set(infos) if infos[s]["status"] != "SETTLING"}
    par_annee = collections.Counter(int(dernier[s].year) for s in arretes)
    delivery = [s for s in settling if pd.Timestamp(infos[s]["deliveryDate"], unit="ms").floor("D") == dernier[s]]

    interruptions = {}
    for s, g in nz.groupby("sym"):
        ecart = g["jour"].sort_values().diff().dt.days
        if (ecart > 7).any():
            interruptions[s] = int(ecart.max())
    onboard = {}
    for s in avec_volume:
        if s in infos:
            e = (premier[s] - pd.Timestamp(infos[s]["onboardDate"], unit="ms").floor("D")).days
            if e > 2:
                onboard[s] = e

    zombies = {}
    for s in arretes:
        apres = long[(long["sym"] == s) & (long["jour"] > dernier[s])]
        if len(apres):
            zombies[s] = {"lignes": len(apres), "toutes_a_volume_nul": bool((apres["v"] == 0).all())}
    z = [v["lignes"] for v in zombies.values()]
    sans_zombie = sorted(arretes - set(zombies))

    # Univers. Trois lectures, pour voir ce que chaque choix change.
    volumes0 = volumes.fillna(0.0)
    non_coin = {s for s, i in infos.items() if i["underlyingType"] != "COIN" or i["contractType"] == "TRADIFI_PERPETUAL"}
    stables = {f"{x}USDT" for x in STABLES}
    exclus_audit = {"BTCUSDT"} | stables | non_coin
    exclus_regle = exclus_audit | set(INDICES_ABSENTS)

    log("univers à la date")
    comp_a, det_a = univers_a_date(volumes0, exclus_audit)
    comp_r, det_r = univers_a_date(volumes0, exclus_regle)
    stats_a = stats_univers(comp_a, det_a, arretes, absents, dernier_txt)
    stats_r = stats_univers(comp_r, det_r, arretes, absents, dernier_txt)

    # Même règle, avec les symboles refusés par l'API relus dans l'archive.
    stats_x = None
    if lignes_archive:
        ax = pd.concat(lignes_archive)
        ax = ax[ax["jour"] <= ref]
        px = ax.pivot_table(index="jour", columns="sym", values="v", aggfunc="first").reindex(jours)
        vol_x = pd.concat([volumes, px], axis=1).fillna(0.0)
        arretes_x = set(arretes)
        absents_x = set(absents)
        dernier_x = dict(dernier_txt)
        for s, v in archives_refus.items():
            if v["dernier_volume"] and pd.Timestamp(v["dernier_volume"]) < limite:
                arretes_x.add(s)
                dernier_x[s] = v["dernier_volume"]
                if s not in infos:
                    absents_x.add(s)
        comp_x, det_x = univers_a_date(vol_x, exclus_regle)
        stats_x = stats_univers(comp_x, det_x, arretes_x, absents_x, dernier_x)
        stats_x["arretes_total"] = len(arretes_x)
        stats_x["absents_ei_total"] = len(absents_x)

    # Test de troncature : la composition à t ne doit pas changer si l'on efface tout ce qui suit t.
    troncature = []
    for t in ["2021-01-04", "2022-05-09", "2024-07-01", "2026-10-19"]:
        ts = pd.Timestamp(t)
        coupe = volumes0.copy()
        coupe.loc[coupe.index >= ts] = -1.0  # valeur impossible, toute lecture après t ferait échouer l'égalité
        hier = ts - pd.Timedelta(days=1)
        premier_c = (coupe.loc[:hier] > 0).idxmax()
        a_vu = (coupe.loc[:hier] > 0).any()
        cand = [s for s in coupe.columns if coupe.loc[hier, s] > 0 and a_vu[s] and premier_c[s] <= ts - pd.Timedelta(days=ANCIENNETE) and s not in exclus_audit]
        med = coupe.loc[ts - pd.Timedelta(days=FENETRE_VOLUME):hier, cand].median()
        ordre = sorted(cand, key=lambda s: (-med[s], s))[:TOP]
        troncature.append({"date": t, "identique": ordre == comp_a[t]})

    log("sondes")
    sonde = sondes(c)
    temoins_klines = {s: bool(s in lignes_par_sym.index) for s in ["LUNAUSDT", "SRMUSDT", "TOMOUSDT", "ANCUSDT", "BTSUSDT", "FTTUSDT", "SCUSDT"]}
    log("annonces")
    try:
        ann = annonces(c, arretes, dernier_txt)
    except Exception as e:  # catalogue non documenté, son absence ne doit pas annuler le reste
        ann = {"erreur": f"{type(e).__name__} {e}"}

    bloc_cle = {"developpement": "dev", "validation": "val", "hors_echantillon": "hors"}
    mesure = {
        "contrats_actifs_coin": actifs_coin, "exchangeinfo_total": len(sy), "perp_usdt": len(usdt_perp), "perp_trading": statuts["TRADING"], "perp_settling": statuts["SETTLING"], "perp_attente": statuts["PENDING_TRADING"],
        "vision_klines": len(v_klines), "vision_klines_usdt": len(v_usdt), "vision_financement": len(v_fin), "vision_marque": len(v_marque), "vision_metrics": len(v_metrics),
        "arretes_avec_klines_vision": len(arretes & set(v_klines)), "arretes_avec_financement_vision": len(arretes & set(v_fin)), "arretes_avec_marque_vision": len(arretes & set(v_marque)), "arretes_avec_metrics_vision": len(arretes & set(v_metrics)),
        "balayes": len(symboles), "avec_volume": len(avec_volume), "vivants": len(vivants), "arretes": len(arretes), "arretes_settling": len(settling), "arretes_absents_ei": len(absents),
        "delivery_egale_dernier_volume": len(delivery), "interruptions_sup_7j": len(interruptions), "onboard_avance_sup_2j": len(onboard), "onboard_avance_max_j": max(onboard.values()) if onboard else 0,
        "zombies_noms": len(z), "zombies_mediane_j": float(np.median(z)), "zombies_max_j": max(z), "zombies_ftt": zombies.get("FTTUSDT", {}).get("lignes"), "zombies_sc": zombies.get("SCUSDT", {}).get("lignes"),
        "candidats_04_01_2021": det_a["2021-01-04"]["candidats"],
        "noms_top30": stats_a["noms_top30"], "noms_arretes": stats_a["noms_arretes"], "noms_absents": stats_a["noms_absents_ei"],
        "part_presences_arretes_pct": round(stats_a["part_presences_arretes_pct"], 1), "part_presences_absents_pct": round(stats_a["part_presences_absents_pct"], 1),
        "rotation_noms_semaine": stats_a["rotation_noms_par_semaine"], "arrets_sous_30j": len(stats_a["arrets_sous_30j"]),
    }
    for y in range(2020, 2027):
        mesure[f"arrets_{y}"] = par_annee.get(y, 0)
    for b, k in bloc_cle.items():
        v = stats_a["blocs"][b]
        mesure.update({f"{k}_semaines": v["semaines"], f"{k}_cand_min": v["candidats_min"], f"{k}_cand_med": v["candidats_mediane"], f"{k}_cand_max": v["candidats_max"],
                       f"{k}_r30_min": v["volume_rang_30_min_MUSDT"], f"{k}_r30_med": v["volume_rang_30_mediane_MUSDT"], f"{k}_noms": v["noms_uniques"],
                       f"{k}_arretes_moy": v["arretes_moyenne_sur_30"], f"{k}_absents_moy": v["absents_ei_moyenne_sur_30"]})
    if "erreur" not in ann:
        mesure.update({"annonces_articles": ann["articles"], "annonces_titres_futures": ann["titres_futures"], "annonces_rapprochees": ann["rapproches"],
                       "annonces_delai_median_j": ann["delai_median_j"], "annonces_delai_min_j": ann["delai_min_j"], "annonces_delai_max_j": ann["delai_max_j"]})

    fin = horo()
    res = {
        "script": "audit_univers.py", "strategie": "STRAT-20261031-03", "debut_utc": debut, "fin_utc": fin,
        "portee": "Dates et volumes en USDT seulement. Aucun prix lu, aucun rendement calculé. Le carnet n'est pas rejoué.",
        "reference": {"dernier_jour_pris_en_compte": a.ref, "seuil_arret_j": SEUIL_ARRET_J},
        "horodatages": {"exchangeinfo": horo_ei, "listing_archives": horo_s3, "debut_balayage": debut_balayage, "fin_balayage": fin_balayage},
        "empreinte_volumes_sha256": empreinte,
        "mesures": mesure, "ecarts_avec_la_fiche_du_31_10": ecarts(mesure),
        "notes_sur_les_ecarts": {
            "part_presences_arretes_pct": "Valeur exacte dans univers, le 9,0 publié n'est pas l'arrondi de la mesure.",
            "rotation_noms_semaine": f"{stats_a['entrees_total']} entrées sur {stats_a['transitions']} transitions, soit {stats_a['entrees_total'] / stats_a['transitions']:.3f}. Divisé par {stats_a['semaines']} : {stats_a['entrees_total'] / stats_a['semaines']:.3f}.",
            "zombies_mediane_j": "Médiane sur les noms touchés. La valeur publiée est celle qui compte aussi les arrêtés sans ligne nulle.",
            "zombies_ftt": "Le 284 publié venait d'un téléchargement freqtrade de 498 lignes, ici toutes les lignes de l'API jusqu'à la référence.",
            "zombies_sc": "Le 330 publié venait d'un téléchargement freqtrade de 498 lignes, ici toutes les lignes de l'API jusqu'à la référence.",
            "annonces_delai_max_j": "La règle de rapprochement du premier audit n'a pas été conservée. Voici celle du script.",
        },
        "regles": {"top": TOP, "anciennete_j": ANCIENNETE, "fenetre_volume_j": FENETRE_VOLUME, "vivant": "volume non nul le jour t - 1", "semaine_exclue": SEMAINE_EXCLUE},
        "controle_calendrier": controle_calendrier(ref),
        "exclusions": {"stablecoins": sorted(stables), "non_coin_exchangeinfo": len(non_coin), "indices_absents_exchangeinfo": INDICES_ABSENTS},
        "contrats_arretes": {
            "absents_exchangeinfo": sorted(absents), "autres_statuts": autres_statuts, "par_annee": {str(k): v for k, v in sorted(par_annee.items())},
            "dernier_volume": {s: dernier_txt[s] for s in sorted(arretes)},
        },
        "sans_aucun_volume": sorted(set(lignes_par_sym.index) - set(avec_volume)),
        "refus_api": archives_refus,
        "relectures_reponses_partielles": relectures,
        "interruptions_sup_7j": interruptions,
        "onboard_avance_sup_2j": dict(sorted(onboard.items(), key=lambda x: -x[1])),
        "zombies": {"noms": len(z), "toutes_lignes_a_volume_nul": sum(v["toutes_a_volume_nul"] for v in zombies.values()), "sans_zombie": sans_zombie,
                    "mediane_sur_les_noms_touches": float(np.median(z)), "mediane_avec_les_arretes_sans_zombie": float(np.median(z + [0] * len(sans_zombie))),
                    "FTTUSDT": zombies.get("FTTUSDT"), "SCUSDT": zombies.get("SCUSDT")},
        "temoins_klines_api": temoins_klines,
        "sondes": sonde,
        "annonces": ann,
        "univers": {"audit_sans_retrait_des_3_indices": stats_a, "regle_1_3_avec_retrait_des_3_indices": stats_r, "regle_1_3_plus_symboles_relus_en_archive": stats_x},
        "indices_absents_dans_le_top30": {s: sum(s in v for v in comp_a.values()) for s in INDICES_ABSENTS},
        "test_troncature": troncature,
        "composition_hebdomadaire_regle_1_3": comp_r,
        "appels_http": c.appels, "incidents_http": c.incidents,
    }
    SORTIES.mkdir(parents=True, exist_ok=True)
    chemin = SORTIES / f"audit_univers_{debut.replace('-', '').replace(':', '')}.json"
    chemin.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    log(f"sortie {chemin}")
    print(chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
