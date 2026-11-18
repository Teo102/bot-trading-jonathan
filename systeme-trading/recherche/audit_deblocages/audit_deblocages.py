#!/usr/bin/env python3
"""Audit de DISPONIBILITÉ et de QUALITÉ des calendriers de déblocages de jetons pour H28 (17/11/2026).

On liste, on compte, on vérifie des champs et des dates. AUCUN prix, AUCUN rendement, aucune bougie, aucun volume.
Les champs de prix présents dans certaines réponses (prix du jeton, capitalisation, intérêt ouvert, financement,
montants en dollars) sont retirés dès la lecture par `sans_prix` et ne sont jamais écrits dans la sortie.

Points d'accès publics seulement, sans clé ni compte, vérification SSL active :
  https://defillama-datasets.llama.fi/emissionsProtocolsList et /emissions/<protocole>   (calendriers d'aujourd'hui)
  https://api.coingecko.com/api/v3/coins/list?include_platform=true                       (un seul appel)
  https://fapi.binance.com/fapi/v1/exchangeInfo                                          (perpétuels vivants)
  https://s3-ap-northeast-1.amazonaws.com/data.binance.vision (listes de dossiers)       (perpétuels retirés)
  https://web.archive.org/cdx/search/cdx et /web/<horodatage>id_/<url>                   (instantanés datés)
  github.com en HTML, et un clone git public d'une copie détachée du dépôt emissions-adapters (lecture de
  l'historique seulement, aucun code du dépôt n'est exécuté)

Sections :
  A. couverture des 375 protocoles
  B. recoupement avec les perpétuels USDT de Binance (vivants et retirés)
  C. nombre d'événements (critère T3)
  D. connaissance à la date (critère T4) : historique git, Wayback Machine, comparaison d'instantanés
  E. survivants

Usage :
  systeme-trading/.venv/bin/python -I audit_deblocages.py [--cache DOSSIER] [--depot CHEMIN_CLONE]
Sortie : recherche/audit_deblocages/audit_deblocages_<horodatage UTC>.json
"""
from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import gzip
import hashlib
import json
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests

ICI = Path(__file__).resolve().parent
UTC = dt.timezone.utc
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "audit-donnees-deblocages/1.0"
APPELS: list[dict] = []
PAUSES = {
    "defillama-datasets.llama.fi": 0.3,
    "web.archive.org": 1.5,
    "api.coingecko.com": 1.0,
    "fapi.binance.com": 0.5,
    "s3-ap-northeast-1.amazonaws.com": 0.25,
    "github.com": 1.0,
    "api.github.com": 1.0,
    "archive.softwareheritage.org": 1.0,
    "api.llama.fi": 1.0,
}
CLES_PRIX = re.compile(r"price|mcap|usd|openinterest|funding|futures|volume|marketcap", re.I)
CACHE: Path | None = None

DATASETS = "https://defillama-datasets.llama.fi"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

CATS_INITIES = {"insiders", "privateSale"}
SEUILS = (0.01, 0.02)
ANNEES = list(range(2021, 2027))
DEV = (dt.date(2021, 1, 1), dt.date(2024, 6, 30))
HORS = (dt.date(2025, 7, 1), dt.date(2026, 10, 31))
FORK_DEPOT = "https://github.com/Omni-Chain-Protocols/emissions-adapters.git"

# Alias manuels, écrits avant le comptage et signalés comme tels : le symbole CoinGecko d'aujourd'hui diffère du
# ticker Binance (renommage), ou le gecko_id de DefiLlama n'existe plus dans la liste CoinGecko.
ALIAS_BINANCE = {
    "beam-2": ["BEAMX"], "ronin": ["RONIN"], "polygon-ecosystem-token": ["MATIC"], "matic-network": ["MATIC"],
    "the-open-network": ["TON"], "ton": ["TON"], "lombard": ["BARD"], "lombard-protocol": ["BARD"],
    "mantra-dao": ["OM"], "mantra": ["OM"], "iota": ["IOTA"], "omni-network": ["OMNI"],
}

# Dix gros protocoles pour la Wayback Machine : slug d'aujourd'hui puis anciens slugs possibles.
DIX = {
    "arbitrum-foundation": ["arbitrum"],
    "optimism-foundation": ["optimism"],
    "aptos": [],
    "sui-foundation": ["sui"],
    "sei": [],
    "starknet-bridge": ["starknet"],
    "celestia": [],
    "worldcoin": [],
    "pyth": ["pyth-network"],
    "jito": [],
}


# ---------------------------------------------------------------- utilitaires

def maintenant() -> dt.datetime:
    return dt.datetime.now(UTC)


def jour(ts: float | int | None) -> dt.date | None:
    if ts is None:
        return None
    try:
        return dt.datetime.fromtimestamp(float(ts), UTC).date()
    except (OverflowError, OSError, ValueError):
        return None


def iso(d: dt.date | None) -> str | None:
    return d.isoformat() if d else None


def sans_prix(o):
    """Retire récursivement toute clé de prix, de capitalisation ou de montant en dollars."""
    if isinstance(o, dict):
        return {k: sans_prix(v) for k, v in o.items() if not CLES_PRIX.search(str(k))}
    if isinstance(o, list):
        return [sans_prix(v) for v in o]
    return o


def get(url: str, params: dict | None = None, kind: str = "json", timeout: int = 90, cache: bool = False):
    """GET public avec pause par hôte, journal d'appels et cache optionnel. Rend None en cas d'échec."""
    hote = urlparse(url).netloc
    cle = None
    if cache and CACHE is not None:
        cle = CACHE / (hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest() + ".bin")
        if cle.exists():
            contenu = cle.read_bytes()
            APPELS.append({"hote": hote, "url": url[:160], "statut": 200, "octets": len(contenu), "cache": True})
            return decode(contenu, kind)
    time.sleep(PAUSES.get(hote, 0.5))
    t0 = time.time()
    try:
        r = SESSION.get(url, params=params, timeout=timeout)
    except requests.RequestException as e:
        APPELS.append({"hote": hote, "url": url[:160], "statut": None, "erreur": repr(e)[:200], "s": round(time.time() - t0, 2)})
        return None
    entree = {"hote": hote, "url": url[:160], "statut": r.status_code, "octets": len(r.content), "s": round(time.time() - t0, 2)}
    APPELS.append(entree)
    if r.status_code != 200:
        entree["erreur"] = r.text[:160]
        return None
    if cle is not None:
        cle.write_bytes(r.content)
    try:
        return decode(r.content, kind)
    except Exception as e:  # noqa: BLE001
        entree["erreur"] = "décodage : " + repr(e)[:150]
        return None


def decode(contenu: bytes, kind: str):
    if contenu[:2] == b"\x1f\x8b":
        contenu = gzip.decompress(contenu)
    if kind == "json":
        return json.loads(contenu)
    return contenu.decode("utf-8", "replace")


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


RE_DEST = [
    re.compile(r"unlock(?:ed)? from (.+?) on \{timestamp\}", re.I),
    re.compile(r"\{tokens\[0\]\} of (.+?) tokens will be unlocked", re.I),
    re.compile(r"per (?:week|day) from (.+?) on \{timestamp\}", re.I),
    re.compile(r"from (.+?) on \{timestamp\}", re.I),
]


def destinataire(desc: str | None) -> str:
    for rx in RE_DEST:
        m = rx.search(desc or "")
        if m:
            return m.group(1).strip()
    return ""


def type_evt(e: dict) -> str:
    t = e.get("unlockType")
    if t:
        return "cliff" if t == "cliff" else "linear"
    d = (e.get("description") or "").strip()
    if d.startswith("A cliff") or RE_DEST[1].search(d):
        return "cliff"
    if d.lower().startswith("linear"):
        return "linear"
    return "autre"


def normalise_evts(evts) -> list[dict]:
    """Événements en forme commune : jour, type, jetons (premier nombre), destinataire, catégorie si donnée."""
    if isinstance(evts, str):
        try:
            evts = ast.literal_eval(evts)
        except (ValueError, SyntaxError):
            try:
                evts = json.loads(evts)
            except ValueError:
                return []
    out = []
    for e in evts or []:
        if not isinstance(e, dict):
            continue
        n = e.get("noOfTokens") or [None]
        try:
            jetons = float(n[0]) if n and n[0] is not None else None
        except (TypeError, ValueError):
            jetons = None
        out.append({
            "jour": jour(e.get("timestamp")),
            "type": type_evt(e),
            "jetons": jetons,
            "dest": destinataire(e.get("description")),
            "cat": e.get("category"),
        })
    return [e for e in out if e["jour"] is not None]


# ---------------------------------------------------------------- A. couverture

def section_a() -> tuple[list[str], dict[str, dict], dict]:
    liste = get(f"{DATASETS}/emissionsProtocolsList")
    protos: dict[str, dict] = {}
    echecs = []
    for slug in liste:
        d = get(f"{DATASETS}/emissions/{slug}", cache=True)
        if not isinstance(d, dict):
            echecs.append(slug)
            continue
        d = sans_prix(d)
        m = d.get("metadata") or {}
        evts = normalise_evts(m.get("events") or [])
        total = m.get("total")
        maxs = (d.get("supplyMetrics") or {}).get("maxSupply")
        denom, source_denom = (total, "metadata.total") if isinstance(total, (int, float)) and total > 0 else (
            (maxs, "supplyMetrics.maxSupply") if isinstance(maxs, (int, float)) and maxs > 0 else (None, "absent"))
        cats = collections.Counter(e["cat"] for e in evts)
        types = collections.Counter(e["type"] for e in evts)
        dd = d.get("documentedData") or {}
        jours = [e["jour"] for e in evts]
        protos[slug] = {
            "slug": slug,
            "name": d.get("name"),
            "gecko_id": d.get("gecko_id"),
            "token": m.get("token"),
            "pId": d.get("pId"),
            "protocolIds": [str(x) for x in (m.get("protocolIds") or [])],
            "total": total,
            "denominateur": denom,
            "source_denominateur": source_denom,
            "n_evts": len(evts),
            "premier": iso(min(jours)) if jours else None,
            "dernier": iso(max(jours)) if jours else None,
            "categories": dict(cats),
            "types": dict(types),
            "part_cliff": round(types.get("cliff", 0) / len(evts), 3) if evts else None,
            "categories_declarees": {k: v for k, v in (d.get("categories") or {}).items()},
            "documentedData_series": len(dd.get("data") or []) if isinstance(dd, dict) else 0,
            "notes": len(m.get("notes") or []),
            "evts": evts,
        }
    # agrégats
    vals = list(protos.values())
    agg = {
        "liste": len(liste),
        "fichiers_lus": len(protos),
        "echecs": echecs,
        "avec_gecko_id": sum(1 for p in vals if p["gecko_id"]),
        "token_coingecko": sum(1 for p in vals if not p["gecko_id"] and str(p["token"] or "").startswith("coingecko:")),
        "token_adresse": sum(1 for p in vals if not p["gecko_id"] and ":" in str(p["token"] or "") and not str(p["token"]).startswith("coingecko:")),
        "sans_evenement": sum(1 for p in vals if p["n_evts"] == 0),
        "evenements_total": sum(p["n_evts"] for p in vals),
        "evts_par_type": dict(sum((collections.Counter(p["types"]) for p in vals), collections.Counter())),
        "evts_par_categorie": dict(sum((collections.Counter({str(k): v for k, v in p["categories"].items()}) for p in vals), collections.Counter())),
        "protocoles_par_categorie": dict(collections.Counter(str(c) for p in vals for c in p["categories"])),
        "denominateur": dict(collections.Counter(p["source_denominateur"] for p in vals)),
        "premiere_date_min": min((p["premier"] for p in vals if p["premier"]), default=None),
        "derniere_date_max": max((p["dernier"] for p in vals if p["dernier"]), default=None),
        "premieres_dates_par_annee": dict(sorted(collections.Counter((p["premier"] or "aucune")[:4] for p in vals).items())),
        "dernieres_dates_par_annee": dict(sorted(collections.Counter((p["dernier"] or "aucune")[:4] for p in vals).items())),
    }
    # emissionsIndex et emissionsBreakdown : champs seulement
    idx = get(f"{DATASETS}/emissionsIndex")
    agg["emissionsIndex"] = None
    if isinstance(idx, dict) and isinstance(idx.get("data"), list) and idx["data"]:
        agg["emissionsIndex"] = {"lignes": len(idx["data"]), "champs_sans_prix": sorted(sans_prix(idx["data"][0]).keys()),
                                 "champs_de_prix_retires": sorted(k for k in idx["data"][0] if CLES_PRIX.search(k))}
    agg["emissionsBreakdown"] = {}
    for u in (f"{DATASETS}/emissionsBreakdown", "https://api.llama.fi/emissionsBreakdown"):
        b = get(u)
        if b is None:
            agg["emissionsBreakdown"][u] = {"statut": APPELS[-1]["statut"], "erreur": APPELS[-1].get("erreur")}
        else:
            ex = (next(iter(b.values()), {}) if isinstance(b, dict) else (b[0] if isinstance(b, list) and b else {}))
            agg["emissionsBreakdown"][u] = {"type": type(b).__name__, "taille": len(b) if hasattr(b, "__len__") else None,
                                           "champs_sans_prix": sorted(sans_prix(ex).keys())[:40] if isinstance(ex, dict) else None}
    return liste, protos, agg


# ---------------------------------------------------------------- B. recoupement Binance

MULT = re.compile(r"^(1000000|100000|10000|1000|1M)(.+)$")


def base_de(sym: str) -> tuple[str, str]:
    base = sym[:-4] if sym.endswith("USDT") else sym
    m = MULT.match(base)
    if m and not base[0:2] == "1I":
        return m.group(2), m.group(1)
    return base, ""


def liste_s3(prefixe: str) -> list[str]:
    """Préfixes communs (dossiers) ou clés sous un préfixe, pagination par marker."""
    out, marker = [], ""
    for _ in range(20):
        txt = get(S3, params={"delimiter": "/", "prefix": prefixe, "marker": marker}, kind="text")
        if txt is None:
            break
        root = ET.fromstring(txt)
        pref = [e.text for e in root.findall("s3:CommonPrefixes/s3:Prefix", NS)]
        cles = [e.text for e in root.findall("s3:Contents/s3:Key", NS)]
        out += pref + cles
        if (root.findtext("s3:IsTruncated", namespaces=NS) or "false") != "true":
            break
        marker = root.findtext("s3:NextMarker", namespaces=NS) or (out[-1] if out else "")
    return out


def section_b(protos: dict[str, dict]) -> tuple[dict, dict]:
    cg = get("https://api.coingecko.com/api/v3/coins/list", params={"include_platform": "true"})
    cg = cg or []
    cg_par_id = {c["id"]: c for c in cg}
    cg_par_adr = collections.defaultdict(set)
    for c in cg:
        for _, adr in (c.get("platforms") or {}).items():
            if adr:
                cg_par_adr[str(adr).lower()].add(c["id"])
    n_par_sym = collections.Counter((c.get("symbol") or "").upper() for c in cg)

    ex = get("https://fapi.binance.com/fapi/v1/exchangeInfo") or {}
    contrats: dict[str, dict] = {}
    autres_types = set()
    for s in ex.get("symbols", []):
        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
            vivant = s.get("status") in ("TRADING", "PENDING_TRADING")
            contrats[s["symbol"]] = {
                "symbole": s["symbol"], "baseAsset": s.get("baseAsset"), "statut": s.get("status"),
                "cotation": iso(jour(s.get("onboardDate", 0) / 1000)),
                "retrait": None if vivant else iso(jour(s.get("deliveryDate", 0) / 1000)),
                "source": "exchangeInfo",
            }
        else:
            autres_types.add(s["symbol"])
    dossiers = liste_s3("data/futures/um/monthly/klines/")
    syms_s3 = sorted({d.rstrip("/").split("/")[-1] for d in dossiers})
    s3_usdt = [s for s in syms_s3 if s.endswith("USDT") and "_" not in s]
    absents = [s for s in s3_usdt if s not in contrats and s not in autres_types]
    for s in absents:
        contrats[s] = {"symbole": s, "baseAsset": None, "statut": "absent d'exchangeInfo", "cotation": None, "retrait": None, "source": "S3"}
    resume_binance = {
        "exchangeInfo_symboles": len(ex.get("symbols", [])),
        "perp_usdt_vivants": sum(1 for c in contrats.values() if c["source"] == "exchangeInfo" and c["retrait"] is None),
        "perp_usdt_settling": sum(1 for c in contrats.values() if c["statut"] == "SETTLING"),
        "s3_dossiers": len(syms_s3),
        "s3_usdt_sans_echeance": len(s3_usdt),
        "s3_absents_exchangeInfo": len(absents),
        "coingecko_ids": len(cg),
    }
    par_base = collections.defaultdict(list)
    for s, c in contrats.items():
        b, mult = base_de(s)
        par_base[b].append((s, mult))

    rec = {}
    for slug, p in protos.items():
        gid, voie = None, "non résolu"
        if p["gecko_id"]:
            gid, voie = p["gecko_id"], "gecko_id"
        elif str(p["token"] or "").startswith("coingecko:"):
            gid, voie = str(p["token"]).split(":", 1)[1], "token coingecko"
        elif ":" in str(p["token"] or ""):
            adr = str(p["token"]).split(":", 1)[1].lower()
            ids = sorted(cg_par_adr.get(adr, []))
            if ids:
                gid, voie = ids[0], "adresse" + (f" ({len(ids)} identifiants)" if len(ids) > 1 else "")
        c = (cg_par_id.get(gid) or cg_par_id.get(gid.lower())) if gid else None
        sym = (c.get("symbol") or "").upper() if c else None
        cands = list(par_base.get(sym, [])) if sym else []
        alias = [t for t in ALIAS_BINANCE.get((gid or "").lower(), []) if t != sym]
        for t in alias:
            cands += [x for x in par_base.get(t, []) if x not in cands]
        rec[slug] = {"gecko": gid, "voie": voie, "gecko_connu": c is not None, "symbole_cg": sym,
                     "alias_manuel": alias,
                     "ids_meme_symbole": n_par_sym.get(sym, 0) if sym else 0,
                     "contrats": [s for s, _ in cands]}

    # dates de cotation et de retrait par la liste S3 pour les contrats recoupés absents d'exchangeInfo,
    # et pour les contrats SETTLING (contrôle de la date de retrait).
    utiles = {s for r in rec.values() for s in r["contrats"]}
    a_lister = sorted(s for s in utiles if contrats[s]["source"] == "S3" or contrats[s]["statut"] == "SETTLING")
    for s in a_lister:
        cles = liste_s3(f"data/futures/um/monthly/klines/{s}/1d/")
        mois = sorted({m.group(1) for k in cles for m in [re.search(r"-1d-(\d{4}-\d{2})\.zip$", k)] if m})
        contrats[s]["mois_archive_premier"] = mois[0] if mois else None
        contrats[s]["mois_archive_dernier"] = mois[-1] if mois else None
        contrats[s]["mois_archive_n"] = len(mois)
        if contrats[s]["source"] == "S3" and mois:
            contrats[s]["cotation"] = mois[0] + "-01"
            y, mth = map(int, mois[-1].split("-"))
            fin = dt.date(y + (mth == 12), mth % 12 + 1, 1) - dt.timedelta(days=1)
            contrats[s]["retrait"] = fin.isoformat()
            contrats[s]["dates_approchees"] = "mois d'archive (premier jour du premier mois, dernier jour du dernier mois)"
    # contrôle de cohérence : un échantillon de contrats vivants recoupés, onboardDate contre premier mois d'archive
    vivants = sorted(s for s in utiles if contrats[s]["source"] == "exchangeInfo" and contrats[s]["retrait"] is None)
    controle = []
    for s in vivants[:: max(1, len(vivants) // 15)][:15]:
        cles = liste_s3(f"data/futures/um/monthly/klines/{s}/1d/")
        mois = sorted({m.group(1) for k in cles for m in [re.search(r"-1d-(\d{4}-\d{2})\.zip$", k)] if m})
        controle.append({"symbole": s, "onboardDate": contrats[s]["cotation"], "premier_mois_archive": mois[0] if mois else None})
    resume_binance["controle_onboard_vs_archive"] = controle

    # choix du contrat par protocole et ambiguïtés
    contrat_vers_protos = collections.defaultdict(list)
    for slug, r in rec.items():
        p = protos[slug]
        cs = [contrats[s] for s in r["contrats"]]
        r["choix"] = None
        r["ambiguites"] = []
        if not cs:
            continue
        if len(cs) > 1:
            r["ambiguites"].append(f"{len(cs)} contrats pour le symbole {r['symbole_cg']} : " + ", ".join(c["symbole"] for c in cs))
        cs.sort(key=lambda c: (c["retrait"] is not None, c["cotation"] or "9999"))
        ch = cs[0]
        r["choix"] = {k: ch.get(k) for k in ("symbole", "statut", "cotation", "retrait", "source")}
        r["periodes"] = [(c["cotation"], c["retrait"], c["symbole"]) for c in cs]
        if r.get("alias_manuel"):
            r["ambiguites"].append("alias manuel : " + ", ".join(r["alias_manuel"]))
        if r["ids_meme_symbole"] > 1:
            r["ambiguites"].append(f"symbole {r['symbole_cg']} partagé par {r['ids_meme_symbole']} identifiants CoinGecko")
        if p["premier"] and ch["cotation"] and ch["cotation"] < (dt.date.fromisoformat(p["premier"]) - dt.timedelta(days=180)).isoformat():
            r["ambiguites"].append(f"contrat coté le {ch['cotation']}, plus de 180 jours avant la première date du calendrier ({p['premier']})")
            r["suspect_cotation_anterieure"] = True
        for c in cs:
            contrat_vers_protos[c["symbole"]].append(slug)
    partages = {s: v for s, v in contrat_vers_protos.items() if len(v) > 1}
    for s, v in partages.items():
        gids = {rec[x]["gecko"] for x in v}
        for x in v:
            rec[x]["ambiguites"].append(f"contrat {s} partagé avec {len(v) - 1} autre(s) protocole(s) ({len(gids)} gecko_id distincts)")
    resume_binance["contrats_partages"] = partages
    return rec, {"binance": resume_binance, "contrats": contrats, "cg_n_par_sym": None}


# ---------------------------------------------------------------- C. comptes (T3)

def bloc(d: dt.date) -> str:
    if DEV[0] <= d <= DEV[1]:
        return "dev"
    if HORS[0] <= d <= HORS[1]:
        return "hors"
    if DEV[1] < d < HORS[0]:
        return "intervalle"
    if d > HORS[1]:
        return "apres"
    return "avant"


def dans_periodes(d: dt.date, periodes, marge_jours: int = 0) -> str | None:
    for cot, ret, sym in periodes:
        if not cot:
            continue
        c = dt.date.fromisoformat(cot) + dt.timedelta(days=marge_jours)
        r = dt.date.fromisoformat(ret) if ret else dt.date(2100, 1, 1)
        if c < d <= r:
            return sym
    return None


def section_c(protos: dict, rec: dict) -> tuple[dict, list[dict]]:
    # un seul protocole par gecko_id (celui qui a le plus d'événements), doublons notés
    par_gecko = collections.defaultdict(list)
    for slug, r in rec.items():
        if r.get("choix") and not r.get("suspect_cotation_anterieure"):
            par_gecko[r["gecko"]].append(slug)
    doublons = {g: v for g, v in par_gecko.items() if len(v) > 1}
    retenus = {max(v, key=lambda s: protos[s]["n_evts"]) for v in par_gecko.values()}

    evts = []
    for slug in sorted(retenus):
        p, r = protos[slug], rec[slug]
        den = p["denominateur"]
        if not den:
            continue
        for e in p["evts"]:
            if e["type"] != "cliff" or not e["jetons"] or e["jetons"] <= 0:
                continue
            d = e["jour"]
            sym = dans_periodes(d, r["periodes"])
            if not sym:
                continue
            evts.append({"slug": slug, "gecko": r["gecko"], "symbole": sym, "jour": d, "cat": str(e["cat"]),
                         "frac": e["jetons"] / den, "dest": e["dest"],
                         "cote_7j_avant": dans_periodes(d, r["periodes"], 7) is not None})

    def compte(liste, seuil, groupe: bool, filtre_7j=False):
        if filtre_7j:
            liste = [e for e in liste if e["cote_7j_avant"]]
        if groupe:
            g = collections.defaultdict(float)
            for e in liste:
                g[(e["slug"], e["jour"])] += e["frac"]
            items = [(k[0], k[1]) for k, v in g.items() if v >= seuil]
        else:
            items = [(e["slug"], e["jour"]) for e in liste if e["frac"] >= seuil]
        par_an = collections.Counter(d.year for _, d in items)
        par_bloc = collections.Counter(bloc(d) for _, d in items)
        jetons_bloc = collections.defaultdict(set)
        par_jeton_bloc = collections.defaultdict(collections.Counter)
        for s, d in items:
            jetons_bloc[bloc(d)].add(s)
            par_jeton_bloc[bloc(d)][s] += 1
        recurrents = {b: sum(n for s, n in c.items() if n >= 6) for b, c in par_jeton_bloc.items()}
        premiers = {}
        for s, d in sorted(items, key=lambda x: x[1]):
            premiers.setdefault(s, d)
        return {
            "premier_evenement_du_jeton_par_bloc": dict(collections.Counter(bloc(d) for d in premiers.values())),
            "non_recurrents_par_bloc": {b: sum(n for s, n in c.items() if n < 6) for b, c in par_jeton_bloc.items()},
            "par_annee": {str(a): par_an.get(a, 0) for a in ANNEES},
            "par_bloc": dict(par_bloc),
            "jetons_distincts_par_bloc": {b: len(v) for b, v in jetons_bloc.items()},
            "evts_de_jetons_a_6_evts_ou_plus_par_bloc": recurrents,
            "top_jetons_dev": par_jeton_bloc["dev"].most_common(8),
            "top_jetons_hors": par_jeton_bloc["hors"].most_common(8),
        }

    initi = [e for e in evts if e["cat"] in CATS_INITIES]
    res = {"protocoles_retenus": len(retenus), "doublons_gecko": doublons, "cliffs_cotes_toutes_tailles": len(evts),
           "cliffs_cotes_initie_toutes_tailles": len(initi), "comptes": {}}
    for seuil in SEUILS:
        k = f"{int(seuil * 100)}pct"
        res["comptes"][k] = {
            "initie_individuel": compte(initi, seuil, False),
            "initie_meme_jour": compte(initi, seuil, True),
            "initie_meme_jour_cote_7j_avant": compte(initi, seuil, True, True),
            "toutes_cat_individuel": compte(evts, seuil, False),
            "toutes_cat_meme_jour": compte(evts, seuil, True),
        }
    # catégories des cliffs cotés de plus de 1 %
    res["categories_cliffs_1pct_cotes"] = dict(collections.Counter(e["cat"] for e in evts if e["frac"] >= 0.01))
    # mêmes comptes sans condition de cotation (pour mesurer ce que le recoupement retire)
    tous = []
    for slug, p in protos.items():
        if not p["denominateur"]:
            continue
        for e in p["evts"]:
            if e["type"] == "cliff" and e["jetons"] and str(e["cat"]) in CATS_INITIES and e["jetons"] / p["denominateur"] >= 0.01:
                tous.append(e["jour"])
    res["initie_1pct_sans_condition_binance"] = {"par_annee": {str(a): sum(1 for d in tous if d.year == a) for a in ANNEES},
                                               "par_bloc": dict(collections.Counter(bloc(d) for d in tous))}
    return res, evts


# ---------------------------------------------------------------- D1. historique git

def section_git(depot: Path | None, protos: dict, evts_comptes: list[dict]) -> dict:
    res = {"depot_officiel": {}, "copie": FORK_DEPOT}
    for u in ("https://github.com/DefiLlama/emissions-adapters", "https://api.github.com/repos/DefiLlama/emissions-adapters"):
        get(u, kind="text")
        res["depot_officiel"][u] = APPELS[-1]["statut"]
    sh = get("https://archive.softwareheritage.org/api/1/origin/https://github.com/DefiLlama/emissions-adapters/get/")
    res["software_heritage"] = APPELS[-1]["statut"] if sh is None else "trouvé"
    page = get("https://github.com/search", params={"q": "emissions-adapters", "type": "repositories"}, kind="text") or ""
    res["copies_trouvees_recherche_github"] = sorted(set(re.findall(r"([A-Za-z0-9_.-]+/emissions-adapters)\b", page)))
    res["copies_meta"] = {}
    for full in res["copies_trouvees_recherche_github"]:
        m = get(f"https://api.github.com/repos/{full}")
        if isinstance(m, dict):
            res["copies_meta"][full] = {k: m.get(k) for k in ("fork", "created_at", "pushed_at", "default_branch", "size")}
    tmp = None
    if depot is None:
        tmp = tempfile.TemporaryDirectory()
        depot = Path(tmp.name) / "ea"
        t0 = time.time()
        r = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", "--quiet", "--no-checkout", FORK_DEPOT, str(depot)],
                           capture_output=True, text=True)
        APPELS.append({"hote": "github.com", "url": FORK_DEPOT + " (git clone)", "statut": 0 if r.returncode == 0 else r.returncode,
                       "s": round(time.time() - t0, 2)})
        if r.returncode != 0:
            res["erreur_clone"] = r.stderr[:300]
            return res

    def git(*a):
        return subprocess.run(["git", "-C", str(depot), *a], capture_output=True, text=True).stdout

    ref = "origin/master"
    res["commits_master"] = int(git("rev-list", "--count", ref).strip() or 0)
    res["premier_commit"] = git("log", "--reverse", "--format=%cI", ref).split("\n")[0]
    res["dernier_commit"] = git("log", "-1", "--format=%cI %s", ref).strip()
    # historique des fichiers de protocoles, renommages suivis
    log = git("log", ref, "--reverse", "-M", "--format=C|%H|%cI", "--name-status", "--", "protocols/")
    hist = collections.defaultdict(list)
    fichiers_par_commit = collections.Counter()
    cur = None
    lignes = log.split("\n")
    for ln in lignes:
        if ln.startswith("C|"):
            _, sha, date = ln.split("|", 2)
            cur = (sha, date)
        elif ln.strip() and cur:
            parts = ln.split("\t")
            st = parts[0][0]
            if st == "R" and len(parts) == 3:
                old, new = parts[1], parts[2]
                hist[new] = hist.pop(old, []) + [(cur[1], "R", cur[0])]
            else:
                hist[parts[-1]].append((cur[1], st, cur[0]))
            fichiers_par_commit[cur[0]] += 1
    au_master = set(git("ls-tree", "--name-only", ref, "protocols/").split())
    pid_vers_fichier = {}
    for f in au_master:
        txt = git("show", f"{ref}:{f}")
        for bloc_ids in re.findall(r"protocolIds\s*:\s*\[([^\]]*)\]", txt):
            for pid in re.findall(r"[\"'`]([^\"'`]+)[\"'`]", bloc_ids):
                pid_vers_fichier.setdefault(pid, f)
    res["fichiers_protocols_master"] = len(au_master)
    res["fichiers_protocols_historique"] = len(hist)
    fiche = {}
    for slug, p in protos.items():
        ids = set(p["protocolIds"]) | ({str(p["pId"])} if p["pId"] else set())
        f = next((pid_vers_fichier[i] for i in ids if i in pid_vers_fichier), None)
        voie = "protocolIds"
        if not f:
            base = re.sub(r"-(foundation|bridge|network|protocol|finance|l2|mainnet|exchange|dao|ecosystem)$", "", slug)
            for cand in (slug, base, p["gecko_id"] or ""):
                if cand and f"protocols/{cand}.ts" in hist:
                    f, voie = f"protocols/{cand}.ts", "nom de fichier"
                    break
        if f and f in hist:
            h = hist[f]
            ajout = next((d for d, st, _ in h if st == "A"), h[0][0])
            fiche[slug] = {"fichier": f, "voie": voie, "ajout": ajout[:10], "commits": len(h),
                           "commits_cibles": sum(1 for _, _, s in h if fichiers_par_commit[s] <= 3),
                           "dernier": h[-1][0][:10], "h": h}
    res["protocoles_avec_fichier"] = len(fiche)
    res["protocoles_avec_fichier_par_voie"] = dict(collections.Counter(v["voie"] for v in fiche.values()))
    res["ajouts_par_annee"] = dict(sorted(collections.Counter(v["ajout"][:4] for v in fiche.values()).items()))
    res["commits_par_fichier_mediane"] = sorted(v["commits"] for v in fiche.values())[len(fiche) // 2] if fiche else None

    # événements comptés (initiés, >= 1 %, coté) contre la date d'ajout du fichier
    classes = collections.Counter()
    par_bloc = collections.defaultdict(collections.Counter)
    proches = collections.Counter()
    exemples = []
    for e in evts_comptes:
        if e["cat"] not in CATS_INITIES or e["frac"] < 0.01:
            continue
        fi = fiche.get(e["slug"])
        if not fi:
            c = "pas de fichier dans la copie (ajouté après le 01/04/2026 ou autre source)"
        else:
            ajout = dt.date.fromisoformat(fi["ajout"])
            if ajout <= e["jour"] - dt.timedelta(days=7):
                c = "fichier présent 7 jours avant ou plus"
            elif ajout <= e["jour"]:
                c = "fichier ajouté moins de 7 jours avant"
            else:
                c = "fichier ajouté après l'événement"
            # commits ciblés qui touchent le fichier de 30 jours avant à 7 jours après l'événement
            n = sum(1 for d, st, s in fi["h"] if st != "A" and fichiers_par_commit[s] <= 3
                    and e["jour"] - dt.timedelta(days=30) <= dt.date.fromisoformat(d[:10]) <= e["jour"] + dt.timedelta(days=7))
            if e["jour"] <= dt.date(2026, 4, 1):
                proches["evts_couverts_par_la_copie"] += 1
                if n:
                    proches["avec_commit_cible_de_J-30_a_J+7"] += 1
                    if len(exemples) < 12:
                        exemples.append({"slug": e["slug"], "jour": iso(e["jour"]), "frac": round(e["frac"], 4), "cat": e["cat"],
                                         "commits": [(d[:10], s[:8]) for d, st, s in fi["h"] if st != "A" and fichiers_par_commit[s] <= 3
                                                     and e["jour"] - dt.timedelta(days=30) <= dt.date.fromisoformat(d[:10]) <= e["jour"] + dt.timedelta(days=7)]})
        classes[c] += 1
        par_bloc[bloc(e["jour"])][c] += 1
    res["evts_initie_1pct_cotes_vs_fichier"] = dict(classes)
    res["evts_initie_1pct_cotes_vs_fichier_par_bloc"] = {b: dict(v) for b, v in par_bloc.items()}
    res["modifs_proches_des_evts"] = dict(proches)
    res["exemples_modifs_proches"] = exemples
    res["messages_commits_exemples"] = {}
    for ex in exemples[:6]:
        for d, s in ex["commits"][:3]:
            res["messages_commits_exemples"][s] = git("log", "-1", "--format=%s", s).strip()[:100]
    for v in fiche.values():
        v.pop("h", None)
    res["fiches"] = fiche
    if tmp:
        tmp.cleanup()
    return res


# ---------------------------------------------------------------- D2. Wayback Machine

def cdx(url: str, prefixe: bool = False) -> list[dict]:
    params = {"url": url, "output": "json", "fl": "timestamp,statuscode,digest,length,original"}
    if prefixe:
        params.update({"matchType": "prefix", "collapse": "urlkey", "limit": "3000"})
    d = get("https://web.archive.org/cdx/search/cdx", params=params)
    if not d:
        return []
    cols = d[0]
    return [dict(zip(cols, r)) for r in d[1:]]


def capture(ts: str, url: str, kind="json"):
    return get(f"https://web.archive.org/web/{ts}id_/{url}", kind=kind, cache=True, timeout=120)


def evts_page_unlocks(html: str):
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html or "", re.S)
    if not m:
        return None, None
    try:
        d = json.loads(m.group(1))
    except ValueError:
        return None, None
    pp = sans_prix((d.get("props") or {}).get("pageProps") or {})
    em = pp.get("emissions") or {}
    return normalise_evts(em.get("events") or []), em.get("name")


def comparer(snap: list[dict], t_snap: dt.date, auj: list[dict], p_auj: dict, t_auj: dt.date) -> dict:
    """Compare les cliffs d'un instantané à ceux d'aujourd'hui pour un protocole."""
    den = p_auj["denominateur"] or 0
    cat_par_dest = {norm(dest): c for c, dests in (p_auj.get("categories_declarees") or {}).items() for dest in (dests or [])}
    A = [e for e in snap if e["type"] == "cliff" and e["jetons"]]
    B = [e for e in auj if e["type"] == "cliff" and e["jetons"]]
    libre_b = set(range(len(B)))
    res = []
    for e in A:
        meilleur, cl = None, None
        # 1. même jour, montant à 0,5 % près
        for j in list(libre_b):
            b = B[j]
            if b["jour"] == e["jour"] and abs(b["jetons"] - e["jetons"]) <= 0.005 * max(b["jetons"], e["jetons"]):
                meilleur, cl = j, "identique"
                break
        # 2. même jour, même destinataire, montant différent
        if meilleur is None:
            for j in list(libre_b):
                b = B[j]
                if b["jour"] == e["jour"] and (norm(b["dest"]) == norm(e["dest"])):
                    meilleur, cl = j, "même jour, montant modifié"
                    break
        # 3. même destinataire, montant à 2 % près, date à 120 jours près
        if meilleur is None:
            cands = [(abs((B[j]["jour"] - e["jour"]).days), j) for j in libre_b
                     if norm(B[j]["dest"]) == norm(e["dest"]) and abs(B[j]["jetons"] - e["jetons"]) <= 0.02 * max(B[j]["jetons"], e["jetons"])
                     and abs((B[j]["jour"] - e["jour"]).days) <= 120]
            if cands:
                meilleur, cl = min(cands)[1], "date déplacée"
        # 4. tout destinataire, montant à 10 % près, date à 30 jours près
        if meilleur is None:
            cands = [(abs((B[j]["jour"] - e["jour"]).days), j) for j in libre_b
                     if abs(B[j]["jetons"] - e["jetons"]) <= 0.10 * max(B[j]["jetons"], e["jetons"])
                     and 0 < abs((B[j]["jour"] - e["jour"]).days) <= 30]
            if cands:
                meilleur, cl = min(cands)[1], "date et montant modifiés"
        if meilleur is not None:
            libre_b.discard(meilleur)
            b = B[meilleur]
            cat = str(b["cat"])
            ecart = (b["jour"] - e["jour"]).days
        else:
            cl, cat, ecart, b = "absent aujourd'hui", str(cat_par_dest.get(norm(e["dest"]), "inconnue")), None, None
        res.append({"jour_snap": iso(e["jour"]), "jour_auj": iso(b["jour"]) if b else None, "ecart_jours": ecart,
                    "classe": cl, "cat": cat, "frac": round(e["jetons"] / den, 5) if den else None,
                    "frac_auj": round(b["jetons"] / den, 5) if (b and den) else None,
                    "passe_au_snap": e["jour"] <= t_snap})
    ajoutes = [{"jour": iso(B[j]["jour"]), "cat": str(B[j]["cat"]), "frac": round(B[j]["jetons"] / den, 5) if den else None,
                "passe_au_snap": B[j]["jour"] <= t_snap} for j in sorted(libre_b) if B[j]["jour"] <= t_auj]
    return {"snap": res, "ajoutes": ajoutes}


AVEC_PERP: set[str] = set()


def resume_comparaisons(comps: list[tuple[str, dict]], t_snap: dt.date, t_auj: dt.date) -> dict:
    """Agrège par période (passé à la date de l'instantané, ou futur alors et passé aujourd'hui) et par filtre."""
    out = {}
    filtres = {
        "cliffs_tous": lambda e: True,
        "initie_1pct": lambda e: e["cat"] in CATS_INITIES and (e["frac"] or 0) >= 0.01,
        "toutes_cat_1pct": lambda e: (e["frac"] or 0) >= 0.01,
    }
    comps_perp = [(s, c) for s, c in comps if s in AVEC_PERP]
    for nom, f in filtres.items():
        for periode, cond in (("passe_au_snap", lambda e: e["passe_au_snap"]),
                              ("annonce_puis_passe", lambda e: (not e["passe_au_snap"]) and e["jour_snap"] <= t_auj.isoformat())):
            sel = [e for _, c in comps for e in c["snap"] if f(e) and cond(e)]
            cl = collections.Counter(e["classe"] for e in sel)
            ecarts = sorted(e["ecart_jours"] for e in sel if e["ecart_jours"])
            if periode == "passe_au_snap":
                aj = [a for _, c in comps for a in c["ajoutes"] if a["passe_au_snap"] and f({"cat": a["cat"], "frac": a["frac"]})]
            else:
                aj = [a for _, c in comps for a in c["ajoutes"] if not a["passe_au_snap"] and f({"cat": a["cat"], "frac": a["frac"]})]
            out[f"{nom}/{periode}"] = {"evts_snap": len(sel), "classes": dict(cl), "ecarts_jours": ecarts[:40],
                                       "ajoutes_depuis": len(aj)}
            if nom == "initie_1pct":
                parp = collections.defaultdict(collections.Counter)
                for s, c in comps:
                    for e in c["snap"]:
                        if f(e) and cond(e):
                            parp[s][e["classe"]] += 1
                    for a in c["ajoutes"]:
                        if f({"cat": a["cat"], "frac": a["frac"]}) and (a["passe_au_snap"] == (periode == "passe_au_snap")):
                            parp[s]["ajouté depuis"] += 1
                out[f"{nom}/{periode}"]["par_protocole"] = {s: dict(v) for s, v in sorted(parp.items())}
                sel_p = [e for s, c in comps_perp for e in c["snap"] if f(e) and cond(e)]
                out[f"{nom}/{periode}"]["avec_perp_binance"] = {
                    "evts_snap": len(sel_p), "classes": dict(collections.Counter(e["classe"] for e in sel_p)),
                    "protocoles": len({s for s, c in comps_perp if any(f(e) and cond(e) for e in c["snap"])})}
    return out


def section_wayback(protos: dict, liste: list[str], t_auj: dt.date) -> dict:
    res = {}
    # 1. comptes d'instantanés pour dix gros protocoles
    dix = {}
    for slug, anciens in DIX.items():
        ligne = {}
        for s in [slug] + anciens:
            for u in (f"defillama-datasets.llama.fi/emissions/{s}", f"defillama.com/unlocks/{s}"):
                caps = cdx(u)
                ok = [c for c in caps if c["statuscode"] == "200"]
                ligne[u] = {"instantanes": len(caps), "statut_200": len(ok),
                            "dates_200": [c["timestamp"][:8] for c in ok]}
        dix[slug] = ligne
    res["dix_protocoles"] = dix
    # 2. préfixes archivés
    res["prefixes"] = {}
    for u in ("defillama-datasets.llama.fi/emissions/", "api.llama.fi/emission/"):
        caps = cdx(u, prefixe=True)
        res["prefixes"][u] = sorted({c["original"] for c in caps})
    res["prefixes"]["defillama.com/unlocks/ (nombre d'URL)"] = len(cdx("defillama.com/unlocks/", prefixe=True))
    # 3. instantanés de la liste des protocoles et apparition
    caps = [c for c in cdx("defillama-datasets.llama.fi/emissionsProtocolsList") if c["statuscode"] == "200"]
    vus, apparition, tailles = set(), {}, []
    digests = set()
    for c in caps:
        if c["digest"] in digests:
            continue
        digests.add(c["digest"])
        d = capture(c["timestamp"], "https://defillama-datasets.llama.fi/emissionsProtocolsList")
        if not isinstance(d, list):
            continue
        tailles.append((c["timestamp"][:8], len(d)))
        for s in d:
            if s not in vus:
                vus.add(s)
                apparition[s] = c["timestamp"][:8]
    res["liste_instantanes"] = tailles
    res["liste_apparition_par_annee"] = dict(sorted(collections.Counter(
        (apparition.get(s, "absent des instantanés")[:4]) for s in liste).items()))
    res["liste_disparus"] = sorted(s for s in vus if s not in set(liste))
    res["liste_apparition"] = {s: apparition.get(s) for s in liste}

    # 4. instantanés complets datés : api.llama.fi/emissions (2024) et emissionsIndex (2026)
    par_nom = {norm(p["name"]): s for s, p in protos.items()}
    par_gecko = collections.defaultdict(list)
    for s, p in protos.items():
        if p["gecko_id"]:
            par_gecko[p["gecko_id"]].append(s)
    par_pid = {str(p["pId"]): s for s, p in protos.items() if p["pId"]}

    def trouver(ligne: dict) -> str | None:
        if ligne.get("protocolSlug") in protos:
            return ligne["protocolSlug"]
        pid = str(ligne.get("protocolId") or "")
        if pid in par_pid:
            return par_pid[pid]
        if norm(ligne.get("name")) in par_nom:
            return par_nom[norm(ligne.get("name"))]
        g = ligne.get("gecko_id")
        if g and len(par_gecko.get(g, [])) == 1:
            return par_gecko[g][0]
        return None

    res["instantanes_complets"] = {}
    sources = [("https://api.llama.fi/emissions", "api.llama.fi/emissions"),
               ("https://defillama-datasets.llama.fi/emissionsIndex", "defillama-datasets.llama.fi/emissionsIndex")]
    for url, cle in sources:
        caps = [c for c in cdx(cle) if c["statuscode"] == "200"]
        choisis = caps if cle.startswith("api.") else (caps[:1] + caps[-1:] if len(caps) > 1 else caps)
        for c in choisis:
            d = capture(c["timestamp"], url)
            if isinstance(d, dict):
                d = d.get("data")
            if not isinstance(d, list):
                res["instantanes_complets"][f"{cle}@{c['timestamp']}"] = {"erreur": "illisible"}
                continue
            t_snap = dt.datetime.strptime(c["timestamp"][:8], "%Y%m%d").date()
            comps, non_trouves, noms = [], [], []
            for ligne in d:
                ligne = sans_prix(ligne)
                s = trouver(ligne)
                noms.append(ligne.get("name"))
                if not s:
                    non_trouves.append(ligne.get("name"))
                    continue
                comps.append((s, comparer(normalise_evts(ligne.get("events")), t_snap, protos[s]["evts"], protos[s], t_auj)))
            res["instantanes_complets"][f"{cle}@{c['timestamp']}"] = {
                "date": iso(t_snap), "protocoles": len(d), "relies_aujourdhui": len(comps),
                "absents_aujourdhui": non_trouves,
                "resume": resume_comparaisons(comps, t_snap, t_auj),
                "details_initie_1pct": [dict(e, slug=s) for s, cp in comps for e in cp["snap"]
                                        if e["cat"] in CATS_INITIES and (e["frac"] or 0) >= 0.01 and e["classe"] != "identique"][:80],
                "ajoutes_initie_1pct": [dict(a, slug=s) for s, cp in comps for a in cp["ajoutes"]
                                        if a["cat"] in CATS_INITIES and (a["frac"] or 0) >= 0.01][:80],
            }
    # 5. pages /unlocks/ des dix protocoles : plus ancien instantané lisible, comparé à aujourd'hui
    res["pages_unlocks"] = {}
    for slug, ligne in dix.items():
        if slug not in protos:
            continue
        caps = sorted((d, u) for u, v in ligne.items() if "/unlocks/" in u for d in v["dates_200"])
        # premier instantané, puis un instantané au moins 180 jours plus tard s'il existe
        choisis = []
        for d8, u in caps:
            if not choisis or (dt.datetime.strptime(d8, "%Y%m%d") - dt.datetime.strptime(choisis[-1][0], "%Y%m%d")).days >= 180:
                choisis.append((d8, u))
            if len(choisis) == 2:
                break
        sortie = []
        for d8, u in choisis:
            ts = next(c for c in cdx(u) if c["timestamp"].startswith(d8) and c["statuscode"] == "200")["timestamp"]
            html = capture(ts, "https://" + u, kind="text")
            ev, nom = evts_page_unlocks(html)
            if ev is None:
                sortie.append({"instantane": ts, "url": u, "evenements": None})
                continue
            t_snap = dt.datetime.strptime(d8, "%Y%m%d").date()
            cp = comparer(ev, t_snap, protos[slug]["evts"], protos[slug], t_auj)
            sortie.append({"instantane": ts, "url": u, "nom": nom, "evenements": len(ev),
                           "cliffs": sum(1 for e in ev if e["type"] == "cliff"),
                           "resume": resume_comparaisons([(slug, cp)], t_snap, t_auj),
                           "details_1pct": [e for e in cp["snap"] if (e["frac"] or 0) >= 0.01],
                           "ajoutes_1pct": [a for a in cp["ajoutes"] if (a["frac"] or 0) >= 0.01]})
        res["pages_unlocks"][slug] = sortie
    # 6. page du dépôt officiel dans la Wayback Machine
    res["depot_officiel_wayback"] = [c["timestamp"][:8] for c in cdx("github.com/DefiLlama/emissions-adapters") if c["statuscode"] == "200"]
    return res


# ---------------------------------------------------------------- E. survivants

def section_e(protos: dict, rec: dict, contrats: dict, wb: dict) -> dict:
    avec = {s: r for s, r in rec.items() if r.get("choix")}
    retires = {s: r for s, r in avec.items() if all(p[1] for p in r["periodes"])}
    # couverture des contrats vivants et retirés par les 375
    syms_couverts = {c for r in rec.values() for c in r["contrats"]}
    viv = [s for s, c in contrats.items() if c["retrait"] is None]
    ret = [s for s, c in contrats.items() if c["retrait"] is not None]
    disparus_2024 = {}
    for k, v in (wb.get("instantanes_complets") or {}).items():
        if k.startswith("api.llama.fi"):
            disparus_2024[k] = v.get("absents_aujourdhui")
    return {
        "protocoles_avec_perp": len(avec),
        "protocoles_dont_tous_les_contrats_sont_retires": len(retires),
        "liste_retires": {s: r["periodes"] for s, r in retires.items()},
        "contrats_vivants": len(viv), "contrats_vivants_couverts": sum(1 for s in viv if s in syms_couverts),
        "contrats_retires": len(ret), "contrats_retires_couverts": sum(1 for s in ret if s in syms_couverts),
        "protocoles_des_instantanes_2024_absents_aujourdhui": disparus_2024,
        "slugs_disparus_de_la_liste": wb.get("liste_disparus"),
    }


# ---------------------------------------------------------------- principal

def main():
    global CACHE
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=None, help="dossier de cache des réponses (hors dépôt)")
    ap.add_argument("--depot", type=Path, default=None, help="clone existant de la copie emissions-adapters")
    a = ap.parse_args()
    if a.cache:
        a.cache.mkdir(parents=True, exist_ok=True)
        CACHE = a.cache
    debut = maintenant()
    horo = debut.strftime("%Y%m%dT%H%M%SZ")
    t_auj = debut.date()
    print("A. couverture", flush=True)
    liste, protos, agg_a = section_a()
    print("B. recoupement Binance", flush=True)
    rec, bin_ = section_b(protos)
    print("C. comptes", flush=True)
    comptes, evts = section_c(protos, rec)
    print("D1. git", flush=True)
    g = section_git(a.depot, protos, evts)
    print("D2. Wayback", flush=True)
    AVEC_PERP.update(s for s, r in rec.items() if r.get("choix"))
    wb = section_wayback(protos, liste, t_auj)
    print("E. survivants", flush=True)
    surv = section_e(protos, rec, bin_["contrats"], wb)
    fin = maintenant()

    amb = {s: r["ambiguites"] for s, r in rec.items() if r.get("choix") and r["ambiguites"]}
    recoup = {
        "gecko_resolu": sum(1 for r in rec.values() if r["gecko"]),
        "gecko_connu_coingecko": sum(1 for r in rec.values() if r["gecko_connu"]),
        "voies": dict(collections.Counter(r["voie"].split(" (")[0] for r in rec.values())),
        "avec_perp_binance": sum(1 for r in rec.values() if r.get("choix")),
        "avec_perp_vivant": sum(1 for r in rec.values() if r.get("choix") and any(p[1] is None for p in r["periodes"])),
        "avec_ambiguite": len(amb),
        "ambiguites_par_type": dict(collections.Counter(re.sub(r"[0-9A-Z]{2,}|\d+", "#", x.split(" :")[0].split(" (")[0])
                                                        for v in amb.values() for x in v)),
        "suspects_cotation_anterieure": sorted(s for s, r in rec.items() if r.get("suspect_cotation_anterieure")),
        "ambiguites": amb,
        "table": {s: {"gecko": r["gecko"], "voie": r["voie"], "symbole": r["symbole_cg"], "contrats": r.get("periodes"),
                      "n_evts": protos[s]["n_evts"]} for s, r in rec.items()},
    }
    sortie = {
        "meta": {"debut_utc": debut.isoformat(), "fin_utc": fin.isoformat(), "duree_s": round((fin - debut).total_seconds(), 1),
                 "python": __import__("sys").version.split()[0], "requests": requests.__version__,
                 "regle": "aucun prix, aucun rendement ; champs de prix retirés à la lecture"},
        "A_couverture": {"agregats": agg_a,
                         "protocoles": {s: {k: v for k, v in p.items() if k != "evts"} for s, p in protos.items()}},
        "B_binance": bin_["binance"],
        "B_contrats_recoupes": {s: c for s, c in bin_["contrats"].items() if any(s in r["contrats"] for r in rec.values())},
        "B_recoupement": recoup,
        "C_comptes": comptes,
        "C_evenements_comptes_initie_1pct": [dict(e, jour=iso(e["jour"]), frac=round(e["frac"], 5)) for e in evts
                                             if e["cat"] in CATS_INITIES and e["frac"] >= 0.01],
        "D1_git": g,
        "D2_wayback": wb,
        "E_survivants": surv,
        "appels": {
            "total": len(APPELS),
            "reseau": sum(1 for x in APPELS if not x.get("cache")),
            "depuis_cache": sum(1 for x in APPELS if x.get("cache")),
            "par_hote": dict(collections.Counter(x["hote"] for x in APPELS)),
            "erreurs": [x for x in APPELS if x.get("statut") not in (200, 0)],
            "octets": sum(x.get("octets", 0) for x in APPELS),
        },
    }
    chemin = ICI / f"audit_deblocages_{horo}.json"
    chemin.write_text(json.dumps(sortie, ensure_ascii=False, indent=1, default=str))
    print(chemin, f"{len(APPELS)} appels, {sortie['meta']['duree_s']} s", flush=True)


if __name__ == "__main__":
    main()
