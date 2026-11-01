#!/usr/bin/env python3
"""Simulateur maker Polymarket avec file d'attente FIFO et antisélection.

Recherche uniquement. Aucun appel réseau, aucune clé, aucun ordre. Le script relit les fichiers
déjà produits par `clob_collector.py` (préfixe UTC) :
    <prefixe>_complet.json, <prefixe>_trades_normalises.csv.gz, <prefixe>_ws_evenements.jsonl.gz

Deux couches, rapportées séparément.
  (a) Rejeu exact sur la fenêtre WebSocket : niveaux reconstruits depuis `price_change`, file FIFO,
      trades `last_trade_price`, annulations devant nous réparties au prorata [hypothèse H3].
  (b) Rejeu approché sur l'historique REST des trades : file devant nous tirée de l'instantané du
      carnet, aucun départ devant nous hors trades, ordre annulé et reposé quand le meilleur prix bouge.

Les conventions suivent `clob_collector.py` : tout est exprimé en jeton 0, `sens_maker_jeton0`
vaut +1 quand le maker achète le jeton 0 (taker vendeur), le markout vaut sens × (milieu futur − prix).

Usage :
    python simulateur_file_attente.py                          # deux préfixes par défaut
    python simulateur_file_attente.py --prefixes 20261101T001303Z
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import math
import pathlib
from dataclasses import dataclass, field

import numpy as np

ICI = pathlib.Path(__file__).resolve().parent
RESULTATS = ICI / "resultats"
PREFIXES_DEFAUT = ["20261101T001303Z", "20261031T224031Z"]
EPS = 1e-9
SEED = 20261031
ITERATIONS = 2000
TAILLE_USD = 100.0          # notionnel visé par ordre, en prix du jeton 0 [choix, non optimisé]
HORIZONS_REST = {"1min": 60, "5min": 300, "1h": 3600, "derniere": None}
HORIZONS_WS = {"1min": 60, "fin_fenetre": None}
AGE_PERIME_S = 1800         # au-delà, le milieu de référence est signalé comme périmé
MIN_GROUPES = 5             # sous ce nombre d'événements, l'intervalle est seulement indicatif
FENETRE_APPARIEMENT_MS = 2000


# --------------------------------------------------------------------------------------------
# Mécanique de file, partagée par les deux couches (testée dans test_simulateur_file_attente.py)
# --------------------------------------------------------------------------------------------

@dataclass
class Ordre:
    """Ordre fictif posé en bout de file. sens +1 = bid (achat jeton 0), -1 = ask (vente jeton 0)."""
    sens: int
    prix: float
    taille: float
    devant: float               # parts devant nous dans la file, au même prix
    t_pose: float
    restant: float = field(init=False)
    rempli: float = 0.0

    def __post_init__(self) -> None:
        self.restant = self.taille


def touche(ordre: Ordre, prix_trade: float, sens_maker: int) -> int:
    """0 si le trade ne nous concerne pas, 1 s'il traite à notre prix, 2 s'il traite au-delà."""
    if sens_maker != ordre.sens:
        return 0
    # Bid : un taker vendeur traite à notre prix ou plus bas. Ask : un taker acheteur, à notre prix ou plus haut.
    ecart = (ordre.prix - prix_trade) * ordre.sens
    if abs(ecart) <= EPS:
        return 1
    return 2 if ecart > 0 else 0


def consommer(ordre: Ordre, prix_trade: float, taille_trade: float, sens_maker: int) -> float:
    """Applique un trade à l'ordre, renvoie la quantité remplie (FIFO).

    À notre prix : le volume consomme d'abord la file devant nous, puis notre ordre.
    Au-delà de notre prix : le taker a traité à un prix moins bon que le nôtre, donc le niveau réel
    était vide devant nous. Avec notre ordre présent, ce trade nous aurait servis en premier :
    file devant remise à zéro et remplissage de min(reste, taille du trade) [H2].
    """
    contact = touche(ordre, prix_trade, sens_maker)
    if contact == 0 or ordre.restant <= EPS:
        return 0.0
    if contact == 2:
        ordre.devant = 0.0
        q = min(ordre.restant, taille_trade)
    else:
        absorbe = min(ordre.devant, taille_trade)
        ordre.devant -= absorbe
        q = min(ordre.restant, taille_trade - absorbe)
    q = max(q, 0.0)
    ordre.restant -= q
    ordre.rempli += q
    return q


def annuler_devant(ordre: Ordre, annule: float, niveau_avant: float) -> None:
    """Annulation de `annule` parts sur un niveau qui en comptait `niveau_avant` (sans nous).

    Hypothèse H3 : les annulations frappent la file au prorata, donc la part devant nous
    recule de annule × devant / niveau_avant.
    """
    if annule <= 0 or niveau_avant <= EPS:
        return
    ordre.devant = max(0.0, ordre.devant - annule * ordre.devant / niveau_avant)


def arrondi_tick(prix: float, tick: float, sens: int) -> float:
    """Bid arrondi vers le bas, ask vers le haut, au pas de prix."""
    n = prix / tick
    n = math.floor(n + EPS) if sens > 0 else math.ceil(n - EPS)
    return round(n * tick, 6)


def cible(variante: str, sens: int, bb: float, ba: float, tick: float) -> float:
    if variante == "meilleur":
        return bb if sens > 0 else ba
    milieu = (bb + ba) / 2
    return arrondi_tick(milieu - 0.01 * sens, tick, sens)   # milieu ± 1 cent


def fee_per_share(price, rate, exponent):
    return rate * (price * (1 - price)) ** exponent


# --------------------------------------------------------------------------------------------
# Chargement
# --------------------------------------------------------------------------------------------

def charger_marches(prefixe: str) -> tuple[dict, dict]:
    d = json.load(open(RESULTATS / f"{prefixe}_complet.json"))
    marches = {}
    for groupe in ("top", "supplement"):
        for m in d[groupe]:
            tick = float(m.get("pas_prix") or 0.01)
            marches[m["condition_id"]] = {
                "condition_id": m["condition_id"], "question": m["question"], "echantillon": groupe,
                "mi_mandat": bool(m["mi_mandat"]), "evenement": m.get("groupe_evenement") or m["condition_id"],
                "token0": m["token0"], "token1": m["token1"], "tick": tick,
                "taille_min": float(m.get("taille_min") or 5.0),
                "bb": float(m["meilleur_bid"]), "ba": float(m["meilleur_ask"]), "milieu": float(m["milieu"]),
                "ecart": float(m["ecart_cents"]) / 100, "bid_parts_1c": float(m["bid_parts_1c"] or 0),
                "ask_parts_1c": float(m["ask_parts_1c"] or 0),
                "fee_rate": float(m.get("fee_rate") or 0), "fee_exponent": float(m.get("fee_exponent") or 1),
                "rebate_rate": float(m.get("rebate_rate") or 0),
                "recompense_jour_usd": m.get("recompense_jour_usd"),
                "recompense_ecart_max_cents": m.get("recompense_ecart_max_cents"),
                "recompense_taille_min": m.get("recompense_taille_min"),
                "recompense_estimee_1000usd_jour": m.get("recompense_estimee_1000usd_jour"),
            }
    meta = {"fin_ts": float(d["heure_serveur_clob"]), "debut_utc": d["debut_utc"], "ws": d.get("websocket", {}),
            "n_temoins": len(d.get("temoin_resolus") or [])}
    return marches, meta


def charger_trades(prefixe: str, ids: set) -> dict:
    """Trades REST par marché, ordre chronologique. Le fichier est trié du plus récent au plus ancien ;
    on l'inverse avant un tri stable, pour garder l'ordre d'origine dans une même seconde [H6]."""
    lignes: dict[str, list] = {}
    with gzip.open(RESULTATS / f"{prefixe}_trades_normalises.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            if r["condition_id"] in ids:
                lignes.setdefault(r["condition_id"], []).append(
                    (float(r["ts"]), float(r["prix_jeton0"]), float(r["taille_parts"]), int(r["sens_maker_jeton0"])))
    out = {}
    for cid, rows in lignes.items():
        rows.reverse()
        rows.sort(key=lambda x: x[0])
        a = np.array(rows, dtype=float)
        out[cid] = {"t": a[:, 0], "p": a[:, 1], "z": a[:, 2], "dir": a[:, 3].astype(int)}
    return out


# --------------------------------------------------------------------------------------------
# Couche (b) : rejeu approché sur l'historique REST
# --------------------------------------------------------------------------------------------

def ecart_estime(tr: dict, tick: float, repli: float) -> float:
    """Écart médian observé entre le dernier prix d'ask traité et le dernier prix de bid traité,
    quand les deux datent de moins de 300 s. Repli : écart de l'instantané."""
    last = {1: None, -1: None}
    obs = []
    for t, p, d in zip(tr["t"], tr["p"], tr["dir"]):
        last[d] = (t, p)
        if last[1] and last[-1] and abs(last[1][0] - last[-1][0]) <= 300:
            s = last[-1][1] - last[1][1]
            if s > EPS:
                obs.append(s)
    if len(obs) < 20:
        return max(repli, tick)
    return max(round(float(np.median(obs)) / tick) * tick, tick)


def profondeur_niveau(m: dict, sens: int) -> float:
    """Parts au meilleur niveau, tirées de la bande ±1 cent de l'instantané [H1].
    Avec un pas de 0,001, la bande couvre plusieurs niveaux : on divise par leur nombre."""
    total = m["bid_parts_1c"] if sens > 0 else m["ask_parts_1c"]
    best = m["bb"] if sens > 0 else m["ba"]
    borne = m["milieu"] - 0.01 if sens > 0 else m["milieu"] + 0.01
    n = int(math.floor(abs(best - borne) / m["tick"] + EPS)) + 1
    return total / max(n, 1)


def milieu_proxy(tr: dict, s: float):
    """Milieu reconstruit depuis le dernier trade : bid traité p → p + s/2, ask traité a → a − s/2 [H4]."""
    mids = tr["p"] + tr["dir"] * s / 2
    return tr["t"], mids


def asof(times, values, cibles):
    idx = np.searchsorted(times, cibles, side="right") - 1
    v = np.where(idx >= 0, values[np.clip(idx, 0, None)], np.nan)
    age = np.where(idx >= 0, cibles - times[np.clip(idx, 0, None)], np.inf)
    return v, age


def simuler_rest(m: dict, tr: dict, *, variante: str, alpha: float, naif: bool = False) -> dict:
    """Renvoie remplissages et épisodes d'ordres pour un marché."""
    tick, s = m["tick"], ecart_estime(tr, m["tick"], m["ecart"])
    taille = max(m["taille_min"], round(TAILLE_USD / max(m["milieu"], 0.01)))
    fills, episodes = [], []
    if naif:
        for t, p, z, d in zip(tr["t"], tr["p"], tr["z"], tr["dir"]):
            fills.append((t, d, p, z, 1))
        return {"fills": fills, "episodes": episodes, "ecart": s, "taille": taille}
    q = {1: alpha * profondeur_niveau(m, 1), -1: alpha * profondeur_niveau(m, -1)}
    ordres: dict[int, Ordre | None] = {1: None, -1: None}
    bb = ba = None

    def clore(o: Ordre, t: float, motif: str) -> None:
        episodes.append({"sens": o.sens, "prix": o.prix, "t_pose": o.t_pose, "t_fin": t, "taille": o.taille,
                         "rempli": o.rempli, "motif": motif})

    for t, p, z, d in zip(tr["t"], tr["p"], tr["z"], tr["dir"]):
        o = ordres[d]
        if o is not None:
            contact = touche(o, p, d)
            qte = consommer(o, p, z, d)
            if qte > 0:
                fills.append((t, d, o.prix, qte, contact))
            if o.restant <= EPS:
                clore(o, t, "rempli")
                ordres[d] = None
        # Mise à jour de l'état du carnet depuis ce trade, à écart constant [H4].
        if d > 0:
            bb, ba = p, round(p + s, 6)
        else:
            ba, bb = p, round(p - s, 6)
        if bb <= 0 or ba >= 1:
            continue
        for sens in (1, -1):
            c = cible(variante, sens, bb, ba, tick)
            o = ordres[sens]
            if o is not None and abs(o.prix - c) <= EPS:
                continue
            if o is not None:
                clore(o, t, "annule_partiel" if o.rempli > 0 else "annule")
            ordres[sens] = Ordre(sens, c, taille, q[sens], t)
    for o in ordres.values():
        if o is not None:
            clore(o, float(tr["t"][-1]), "ouvert_fin")
    return {"fills": fills, "episodes": episodes, "ecart": s, "taille": taille}


def markouts_rest(m: dict, tr: dict, sim: dict, fin_ts: float) -> dict:
    """Markout par horizon sur les remplissages simulés, en jeton 0."""
    times, mids = milieu_proxy(tr, sim["ecart"])
    out = {}
    if not sim["fills"]:
        return {h: None for h in HORIZONS_REST}
    f = np.array(sim["fills"], dtype=float)
    t, d, p, z = f[:, 0], f[:, 1], f[:, 2], f[:, 3]
    reb = fee_per_share(p, m["fee_rate"], m["fee_exponent"]) * m["rebate_rate"]
    for h, sec in HORIZONS_REST.items():
        if sec is None:
            v, age = np.full(len(t), m["milieu"]), np.zeros(len(t))
            ok = np.ones(len(t), dtype=bool)
        else:
            cibles = t + sec
            v, age = asof(times, mids, cibles)
            ok = cibles <= fin_ts
        out[h] = {"m": d[ok] * (v[ok] - p[ok]), "z": z[ok], "n": p[ok] * z[ok], "r": reb[ok],
                  "n_censures": int((~ok).sum()), "perimes": int((age[ok] > AGE_PERIME_S).sum())}
    return out


def opportunite_non_remplis(m: dict, tr: dict, sim: dict, fin_ts: float, sec: int = 3600) -> dict:
    """Markout qu'aurait eu un remplissage au moment de l'annulation d'un ordre jamais rempli.
    Sert à lire la sélection : on est rempli quand le prix vient contre nous, pas quand il s'en va."""
    times, mids = milieu_proxy(tr, sim["ecart"])
    eps_ = [e for e in sim["episodes"] if e["motif"] == "annule" and e["t_fin"] + sec <= fin_ts]
    if not eps_:
        return {"n": 0}
    t = np.array([e["t_fin"] for e in eps_])
    d = np.array([e["sens"] for e in eps_])
    p = np.array([e["prix"] for e in eps_])
    v, _ = asof(times, mids, t + sec)
    mk = d * (v - p)
    return {"n": len(eps_), "moy_cents": float(np.nanmean(mk) * 100)}


# --------------------------------------------------------------------------------------------
# Couche (a) : rejeu exact sur la fenêtre WebSocket
# --------------------------------------------------------------------------------------------

def charger_ws(prefixe: str, marches: dict) -> dict:
    """Flux par marché en jeton 0. Les `price_change` du jeton 1 sont des miroirs et sont ignorés."""
    jetons = {}
    for cid, m in marches.items():
        jetons[m["token0"]] = (cid, 0)
        jetons[m["token1"]] = (cid, 1)
    flux: dict[str, list] = {}
    with gzip.open(RESULTATS / f"{prefixe}_ws_evenements.jsonl.gz", "rt") as f:
        for ligne in f:
            e = json.loads(ligne)
            ts = float(e.get("timestamp") or 0)
            typ = e.get("event_type")
            if "price_changes" in e:
                for pc in e["price_changes"]:
                    cid, j = jetons.get(pc["asset_id"], (None, None))
                    if cid is None or j != 0:
                        continue
                    flux.setdefault(cid, []).append({
                        "ts": ts, "type": "niveau", "sens": 1 if pc["side"] == "BUY" else -1,
                        "prix": round(float(pc["price"]), 6), "taille": float(pc["size"]),
                        "bb": float(pc["best_bid"]) if pc.get("best_bid") else None,
                        "ba": float(pc["best_ask"]) if pc.get("best_ask") else None})
            elif typ == "best_bid_ask":
                cid, j = jetons.get(e["asset_id"], (None, None))
                if cid is None or j != 0:
                    continue
                flux.setdefault(cid, []).append({"ts": ts, "type": "bbo", "bb": float(e["best_bid"]),
                                                 "ba": float(e["best_ask"])})
            elif typ == "last_trade_price":
                cid, j = jetons.get(e["asset_id"], (None, None))
                if cid is None:
                    continue
                prix, taker_achat = float(e["price"]), e["side"] == "BUY"
                if j == 1:   # taker acheteur du jeton 1 = taker vendeur du jeton 0 à 1 − prix
                    prix, taker_achat = 1 - prix, not taker_achat
                flux.setdefault(cid, []).append({"ts": ts, "type": "trade", "prix": round(prix, 6),
                                                 "taille": float(e["size"]), "sens_maker": -1 if taker_achat else 1})
    for cid in flux:
        flux[cid].sort(key=lambda x: (x["ts"], 0 if x["type"] == "trade" else 1))
    return flux


def apparier(flux: list) -> None:
    """Sépare chaque baisse de niveau en part traitée et part annulée [H5].
    Une baisse est attribuée à un trade du même côté et du même prix à ±2 s, dans la limite de son volume."""
    niveaux: dict = {}
    trades = [e for e in flux if e["type"] == "trade"]
    reste = [t["taille"] for t in trades]
    for e in flux:
        if e["type"] != "niveau":
            continue
        cle = (e["sens"], e["prix"])
        avant = niveaux.get(cle)
        niveaux[cle] = e["taille"]
        e["avant"] = avant
        e["annule"] = 0.0
        if avant is None or e["taille"] >= avant:
            continue
        baisse = avant - e["taille"]
        for i, tr in enumerate(trades):
            if reste[i] <= EPS or abs(tr["ts"] - e["ts"]) > FENETRE_APPARIEMENT_MS:
                continue
            if tr["sens_maker"] == e["sens"] and abs(tr["prix"] - e["prix"]) <= EPS:
                pris = min(reste[i], baisse)
                reste[i] -= pris
                baisse -= pris
            if baisse <= EPS:
                break
        e["annule"] = max(baisse, 0.0)


def simuler_ws(m: dict, flux: list, variante: str) -> dict:
    apparier(flux)
    niveaux: dict = {}
    bb = ba = None
    ordres: dict[int, Ordre | None] = {1: None, -1: None}
    fills, poses, jamais = [], 0, 0
    etats = []   # (ts, milieu)
    for e in flux:
        if e["type"] == "trade":
            o = ordres[e["sens_maker"]]
            if o is not None:
                q = consommer(o, e["prix"], e["taille"], e["sens_maker"])
                if q > 0:
                    fills.append((e["ts"], o.sens, o.prix, q, 1))
                if o.restant <= EPS:
                    ordres[o.sens] = None
            continue
        if e["type"] == "niveau":
            cle = (e["sens"], e["prix"])
            niveaux[cle] = e["taille"]
            o = ordres[e["sens"]]
            if o is not None and abs(o.prix - e["prix"]) <= EPS and e.get("avant") is not None:
                annuler_devant(o, e["annule"], e["avant"])
                o.devant = min(o.devant, e["taille"])
        if e.get("bb") is not None and e.get("ba") is not None:
            bb, ba = e["bb"], e["ba"]
        if bb is None or ba is None or bb >= ba:
            continue
        etats.append((e["ts"], (bb + ba) / 2))
        for sens in (1, -1):
            c = cible(variante, sens, bb, ba, m["tick"])
            o = ordres[sens]
            if o is not None and abs(o.prix - c) <= EPS:
                continue
            connu = niveaux.get((sens, round(c, 6)))
            if connu is None:
                # Taille du niveau inconnue : on n'invente pas de file, on attend une mise à jour.
                ordres[sens] = None
                jamais += 1
                continue
            taille = max(m["taille_min"], round(TAILLE_USD / max(m["milieu"], 0.01)))
            ordres[sens] = Ordre(sens, c, taille, connu, e["ts"])
            poses += 1
    return {"fills": fills, "poses": poses, "attentes_niveau_inconnu": jamais, "etats": etats}


def markouts_ws(sim: dict) -> dict:
    out = {}
    if not sim["fills"] or not sim["etats"]:
        return {h: None for h in HORIZONS_WS}
    et = np.array(sim["etats"])
    fin = et[-1, 0]
    for h, sec in HORIZONS_WS.items():
        rows = []
        for t, d, p, z, *_ in sim["fills"]:
            if sec is None:
                v = et[-1, 1]
            else:
                if t + sec * 1000 > fin:
                    continue
                v = et[np.searchsorted(et[:, 0], t + sec * 1000, side="right") - 1, 1]
            rows.append((d * (v - p), z, p * z))
        out[h] = rows
    return out


# --------------------------------------------------------------------------------------------
# Agrégation et bootstrap par événement
# --------------------------------------------------------------------------------------------

def bootstrap(series: list[dict], rng) -> dict:
    """series : un dict par marché avec m, z, n, r et l'événement. Rééchantillonne des événements entiers."""
    par_ev: dict[str, list] = {}
    for s in series:
        par_ev.setdefault(s["ev"], []).append(s)
    evs = sorted(par_ev)
    if not evs:
        return {}
    sm = np.array([sum(float((x["m"] * x["z"]).sum()) for x in par_ev[e]) for e in evs])
    sz = np.array([sum(float(x["z"].sum()) for x in par_ev[e]) for e in evs])
    sn = np.array([sum(float(x["n"].sum()) for x in par_ev[e]) for e in evs])
    sr = np.array([sum(float((x["r"] * x["z"]).sum()) for x in par_ev[e]) for e in evs])
    nf = int(sum(len(x["m"]) for x in series))
    res = {"n_remplissages": nf, "n_evenements": len(evs), "n_marches": len(series),
           "parts": float(sz.sum()), "notionnel_usd": float(sn.sum())}
    if sz.sum() <= 0:
        return res
    res["cents_part"] = float(sm.sum() / sz.sum() * 100)
    res["net_1000"] = float((sm.sum() + sr.sum()) / sn.sum() * 1000)
    res["rebate_1000"] = float(sr.sum() / sn.sum() * 1000)
    if len(evs) >= 2:
        w = rng.multinomial(len(evs), np.full(len(evs), 1 / len(evs)), size=ITERATIONS).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            c = w @ sm / (w @ sz) * 100
            n = (w @ (sm + sr)) / (w @ sn) * 1000
        res["cents_ic"] = [float(x) for x in np.nanpercentile(c, [2.5, 97.5])]
        res["net_ic"] = [float(x) for x in np.nanpercentile(n, [2.5, 97.5])]
    res["indicatif"] = len(evs) < MIN_GROUPES
    return res


GROUPES = {
    "hors mi-mandat": lambda m: not m["mi_mandat"],
    "mi-mandat (à part)": lambda m: m["mi_mandat"],
    "hors mi-mandat, frais actifs": lambda m: (not m["mi_mandat"]) and m["fee_rate"] > 0,
}
VARIANTES = [("naif", "meilleur", 0.0, True), ("file nulle, meilleur prix", "meilleur", 0.0, False),
             ("file x1, meilleur prix", "meilleur", 1.0, False),
             ("file x0,5, meilleur prix", "meilleur", 0.5, False), ("file x1, milieu ±1 c", "milieu_1c", 1.0, False),
             ("file x0,5, milieu ±1 c", "milieu_1c", 0.5, False)]


def lancer(prefixe: str, rng) -> dict:
    marches, meta = charger_marches(prefixe)
    trades = charger_trades(prefixe, set(marches))
    fin = meta["fin_ts"]
    par_marche, agreg = [], []
    series = {v[0]: {h: [] for h in HORIZONS_REST} for v in VARIANTES}
    for lab in ("dont remplis à notre prix", "dont niveau traversé"):
        series[lab] = {h: [] for h in HORIZONS_REST}
    opp = {v[0]: [] for v in VARIANTES}
    for cid, m in marches.items():
        tr = trades.get(cid)
        if tr is None or len(tr["t"]) == 0:
            continue
        naif_vol = {1: float(tr["z"][tr["dir"] > 0].sum()), -1: float(tr["z"][tr["dir"] < 0].sum())}
        for nom, var, alpha, naif in VARIANTES:
            sim = simuler_rest(m, tr, variante=var, alpha=alpha, naif=naif)
            mk = markouts_rest(m, tr, sim, fin)
            for h, x in mk.items():
                if x is not None:
                    series[nom][h].append({**x, "ev": m["evenement"], "cid": cid})
            if nom == "file x1, meilleur prix":
                for c, lab in ((1, "dont remplis à notre prix"), (2, "dont niveau traversé")):
                    sub = {**sim, "fills": [f for f in sim["fills"] if f[4] == c]}
                    for h, x in markouts_rest(m, tr, sub, fin).items():
                        if x is not None:
                            series[lab][h].append({**x, "ev": m["evenement"], "cid": cid})
            ep = sim["episodes"]
            n_ep = len(ep)
            n_ep_rempli = sum(1 for e in ep if e["rempli"] > EPS)
            parts = sum(f[3] for f in sim["fills"])
            jours = max((tr["t"][-1] - tr["t"][0]) / 86400, 1e-6)
            o = opportunite_non_remplis(m, tr, sim, fin) if not naif else {"n": 0}
            if o["n"]:
                opp[nom].append((m, o))
            h1 = mk.get("1h")
            par_marche.append({
                "prefixe": prefixe, "variante": nom, "question": m["question"], "mi_mandat": m["mi_mandat"],
                "evenement": m["evenement"], "tick": m["tick"], "ecart_estime_cents": round(sim["ecart"] * 100, 3),
                "ecart_instantane_cents": round(m["ecart"] * 100, 3), "taille_ordre_parts": sim["taille"],
                "file_bid_parts": round(alpha * profondeur_niveau(m, 1), 2) if not naif else 0,
                "file_ask_parts": round(alpha * profondeur_niveau(m, -1), 2) if not naif else 0,
                "trades": len(tr["t"]), "jours": round(jours, 2), "ordres_poses": n_ep,
                "ordres_remplis_au_moins_en_partie": n_ep_rempli,
                "taux_ordres_remplis": round(n_ep_rempli / n_ep, 4) if n_ep else None,
                "remplissages": len(sim["fills"]), "parts_remplies": round(parts, 2),
                "parts_par_jour": round(parts / jours, 2),
                "part_du_volume_naif": round(parts / max(naif_vol[1] + naif_vol[-1], EPS), 6),
                "cents_part_1h": round(float((h1["m"] * h1["z"]).sum() / h1["z"].sum() * 100), 4) if h1 and h1["z"].sum() else None,
                "fee_rate": m["fee_rate"], "rebate_rate": m["rebate_rate"],
                "recompense_jour_usd": m["recompense_jour_usd"], "recompense_ecart_max_cents": m["recompense_ecart_max_cents"],
                "recompense_estimee_1000usd_jour": m["recompense_estimee_1000usd_jour"],
                "opportunite_non_remplis_1h_cents": round(o["moy_cents"], 4) if o.get("n") else None,
                "n_non_remplis_mesures": o.get("n", 0),
            })
    for nom in series:
        for g, filtre in GROUPES.items():
            for h in HORIZONS_REST:
                sel = [s for s in series[nom][h] if filtre(marches[s["cid"]])]
                b = bootstrap(sel, rng)
                cens = sum(s["n_censures"] for s in sel)
                per = sum(s["perimes"] for s in sel)
                agreg.append({"prefixe": prefixe, "variante": nom, "groupe": g, "horizon": h, **b,
                              "n_censures": cens, "n_milieu_perime": per})
    # Sélection : remplis contre non remplis, groupe principal, variante de base
    sel_opp = [o for m, o in opp["file x1, meilleur prix"] if not m["mi_mandat"]]
    opp_moy = (float(np.average([o["moy_cents"] for o in sel_opp], weights=[o["n"] for o in sel_opp])), sum(o["n"] for o in sel_opp)) if sel_opp else (None, 0)

    # Couche WebSocket
    flux = charger_ws(prefixe, marches)
    ws_rows = []
    for var in ("meilleur", "milieu_1c"):
        for cid, fl in flux.items():
            m = marches[cid]
            sim = simuler_ws(m, [dict(e) for e in fl], var)
            mk = markouts_ws(sim)
            n_tr = sum(1 for e in fl if e["type"] == "trade")
            row = {"prefixe": prefixe, "variante": var, "question": m["question"], "mi_mandat": m["mi_mandat"],
                   "evenements_jeton0": len(fl), "trades_ws": n_tr, "ordres_poses": sim["poses"],
                   "attentes_niveau_inconnu": sim["attentes_niveau_inconnu"], "remplissages": len(sim["fills"]),
                   "parts_remplies": round(sum(f[3] for f in sim["fills"]), 2)}
            for h, rows in mk.items():
                if rows:
                    zs = sum(r[1] for r in rows)
                    row[f"cents_part_{h}"] = round(sum(r[0] * r[1] for r in rows) / zs * 100, 4)
                    row[f"n_{h}"] = len(rows)
            ws_rows.append(row)
    return {"prefixe": prefixe, "meta": meta, "par_marche": par_marche, "agreg": agreg, "ws": ws_rows,
            "opp_non_remplis": opp_moy, "n_marches": len(marches),
            "n_trades": int(sum(len(t["t"]) for t in trades.values()))}


# --------------------------------------------------------------------------------------------
# Écriture
# --------------------------------------------------------------------------------------------

def ecrire_csv(chemin: pathlib.Path, rows: list[dict]) -> None:
    cles = []
    for r in rows:
        for k in r:
            if k not in cles:
                cles.append(k)
    with open(chemin, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cles)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, list) else v) for k, v in r.items()})


def fnum(x, nd=2):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def fic(ic, nd=2):
    return f"[{fnum(ic[0], nd)} ; {fnum(ic[1], nd)}]" if ic else "—"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefixes", nargs="+", default=PREFIXES_DEFAUT)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    runs = [lancer(p, rng) for p in args.prefixes]
    ecrire_csv(RESULTATS / f"{stamp}_file_attente_agrege.csv", [r for run in runs for r in run["agreg"]])
    ecrire_csv(RESULTATS / f"{stamp}_file_attente_par_marche.csv", [r for run in runs for r in run["par_marche"]])
    ecrire_csv(RESULTATS / f"{stamp}_file_attente_ws.csv", [r for run in runs for r in run["ws"]])
    json.dump({"genere_utc": stamp, "runs": [{k: v for k, v in r.items() if k != "par_marche"} for r in runs]},
              open(RESULTATS / f"{stamp}_file_attente_complet.json", "w"), indent=1, default=str)
    print(stamp)
    for run in runs:
        print("==", run["prefixe"], run["n_marches"], "marchés", run["n_trades"], "trades")
        for a in run["agreg"]:
            if a["groupe"] in ("hors mi-mandat", "mi-mandat (à part)"):
                print(f"{a['variante']:<26} {a['groupe']:<20} {a['horizon']:<9} n={a.get('n_remplissages',0):>6} "
                      f"ev={a.get('n_evenements',0):>2} c/part={fnum(a.get('cents_part'),3):>7} {fic(a.get('cents_ic'),3):>20} "
                      f"net$/1000={fnum(a.get('net_1000')):>7} {fic(a.get('net_ic')):>20}")
        print("opportunité non remplis 1h (¢/part, n) :", run["opp_non_remplis"])
        for w in run["ws"]:
            if w["remplissages"] or w["trades_ws"]:
                print("WS", w)


if __name__ == "__main__":
    main()
