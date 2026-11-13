#!/usr/bin/env python3
"""Audit de DISPONIBILITÉ des données d'options BTC de Deribit pour H34 (13/11/2026).

On liste, on compte, on vérifie des champs et des dates. AUCUN calcul de prime de variance, aucun rendement,
aucune comparaison implicite contre réalisée, aucun P&L. Les niveaux de volatilité implicite ne sont jamais
écrits dans la sortie : seuls leur présence, leur type et la part de valeurs nulles sont comptés.

Points d'accès publics seulement, sans clé ni compte :
  https://www.deribit.com/api/v2/public/...       (instruments vivants, cotations du moment, DVOL, indice)
  https://history.deribit.com/api/v2/public/...   (instruments et transactions expirés)

Sections :
  A. instruments expirés et vivants (échéances, années, prix d'exercice, couverture des décisions hebdomadaires)
  B. transactions historiques sur un échantillon de jours (champs, densité, monnaie, échéances)
  C. cotations historiques d'une option expirée (carnet, ticker, prix de marque, bougies)
  D. DVOL et volatilité historique (profondeur, fréquence, champs)
  E. indice et sous-jacent (profondeur)

Usage :
  systeme-trading/.venv/bin/python -I audit_options_deribit.py [--cache-instruments CHEMIN] [--pages-max 35]
Sortie : recherche/audit_options/audit_options_<horodatage UTC>.json
"""
from __future__ import annotations

import argparse
import calendar
import collections
import datetime as dt
import json
import math
import statistics
import time
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent
WWW = "www.deribit.com"
HIST = "history.deribit.com"
PAUSE = 0.35            # secondes entre deux appels
APPELS: list[dict] = []
DERNIERES_TRANSACTIONS: list[dict] = []
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "audit-donnees-options/1.0"
UTC = dt.timezone.utc
JOUR_MS = 86_400_000

# Jours d'échantillon (UTC). Deux jours de krach demandés : 12/05/2022 et 10/10/2025.
JOURS = ["2019-06-12", "2021-06-16", "2022-05-12", "2023-03-08", "2024-01-17", "2025-10-10", "2026-11-11"]


def ms(d: dt.datetime) -> int:
    return int(d.timestamp() * 1000)


def iso(t_ms: int | float | None) -> str | None:
    if t_ms is None:
        return None
    return dt.datetime.fromtimestamp(t_ms / 1000, UTC).strftime("%Y-%m-%d %H:%M")


def appel(hote: str, methode: str, params: dict, timeout: int = 180) -> dict:
    """Appel GET d'un point d'accès public. Retourne {'ok', 'result' | 'erreur'}. La vérification SSL reste active."""
    url = f"https://{hote}/api/v2/public/{methode}"
    t0 = time.time()
    entree = {"hote": hote, "methode": methode, "params": {k: v for k, v in params.items()}}
    try:
        r = SESSION.get(url, params=params, timeout=timeout)
        entree["http"] = r.status_code
        entree["octets"] = len(r.content)
        try:
            corps = r.json()
        except ValueError:
            corps = {"error": {"message": "réponse non JSON", "texte": r.text[:200]}}
    except requests.RequestException as e:  # certificat, réseau, délai
        corps = {"error": {"message": f"{type(e).__name__}: {str(e)[:200]}"}}
        entree["http"] = None
    entree["secondes"] = round(time.time() - t0, 2)
    if "result" in corps:
        entree["ok"] = True
        sortie = {"ok": True, "result": corps["result"]}
    else:
        entree["ok"] = False
        entree["erreur"] = corps.get("error")
        sortie = {"ok": False, "erreur": corps.get("error")}
    APPELS.append(entree)
    time.sleep(PAUSE)
    return sortie


# ---------------------------------------------------------------- échéances

def dernier_vendredi(annee: int, mois: int) -> int:
    dernier = calendar.monthrange(annee, mois)[1]
    d = dt.date(annee, mois, dernier)
    while d.weekday() != 4:
        d -= dt.timedelta(days=1)
    return d.day


def classe_echeance(t_ms: int) -> str:
    d = dt.datetime.fromtimestamp(t_ms / 1000, UTC).date()
    if d.weekday() != 4:
        return "quotidienne"
    if d.day == dernier_vendredi(d.year, d.month):
        return "trimestrielle" if d.month in (3, 6, 9, 12) else "mensuelle"
    return "hebdomadaire"


def resume_instruments(liste: list[dict], maintenant_ms: int) -> dict:
    noms = collections.Counter(x["instrument_name"] for x in liste)
    par_annee = collections.defaultdict(lambda: collections.Counter())
    echeances_par_annee = collections.defaultdict(lambda: collections.defaultdict(set))
    premiere = {}
    croise = collections.Counter()
    strikes_par_echeance = collections.defaultdict(set)
    duree_vie = collections.defaultdict(list)
    for x in liste:
        e = x["expiration_timestamp"]
        c = classe_echeance(e)
        a = dt.datetime.fromtimestamp(e / 1000, UTC).year
        par_annee[a][c] += 1
        par_annee[a]["total"] += 1
        echeances_par_annee[a][c].add(e)
        premiere[c] = min(premiere.get(c, e), e)
        croise[(c, x.get("settlement_period"))] += 1
        strikes_par_echeance[e].add(x.get("strike"))
        if x.get("creation_timestamp"):
            duree_vie[c].append((e - x["creation_timestamp"]) / JOUR_MS)
    strikes_annee = collections.defaultdict(list)
    for e, s in strikes_par_echeance.items():
        strikes_annee[dt.datetime.fromtimestamp(e / 1000, UTC).year].append(len(s))
    annees = {}
    for a in sorted(par_annee):
        annees[str(a)] = {
            "instruments": dict(par_annee[a]),
            "echeances_distinctes": {c: len(v) for c, v in echeances_par_annee[a].items()},
            "strikes_par_echeance_mediane": statistics.median(strikes_annee[a]) if strikes_annee[a] else None,
            "strikes_par_echeance_max": max(strikes_annee[a]) if strikes_annee[a] else None,
        }
    champs = collections.Counter()
    for x in liste[:: max(1, len(liste) // 500)]:
        for k in x:
            champs[k] += 1
    return {
        "n_instruments": len(liste),
        "n_noms_distincts": len(noms),
        "doublons_de_nom": sum(1 for v in noms.values() if v > 1),
        "premiere_echeance": iso(min(x["expiration_timestamp"] for x in liste)) if liste else None,
        "derniere_echeance": iso(max(x["expiration_timestamp"] for x in liste)) if liste else None,
        "echeances_futures_dans_la_liste": sum(1 for x in liste if x["expiration_timestamp"] > maintenant_ms),
        "creation_absente": sum(1 for x in liste if not x.get("creation_timestamp")),
        "premiere_echeance_par_classe": {c: iso(v) for c, v in sorted(premiere.items())},
        "classe_contre_settlement_period": {f"{c} / {p}": n for (c, p), n in sorted(croise.items())},
        "duree_de_vie_mediane_jours": {c: round(statistics.median(v), 1) for c, v in duree_vie.items() if v},
        "par_annee_d_echeance": annees,
        "champs_echantillon": sorted(champs),
    }


def couverture_hebdo(liste: list[dict], livraisons: dict[str, float], maintenant_ms: int) -> dict:
    """Pour chaque vendredi 08:00 UTC : quelles échéances étaient cotées À CETTE DATE (création <= t < échéance) ?
    On compte seulement la liste des instruments (critère T4) ; le prix de livraison du jour sert à centrer les
    prix d'exercice (largeur de bande), jamais à calculer un rendement."""
    par_echeance = collections.defaultdict(list)
    for x in liste:
        par_echeance[x["expiration_timestamp"]].append((x.get("creation_timestamp") or 0, x.get("strike"),
                                                         x.get("option_type")))
    echeances = sorted(par_echeance)
    t = dt.datetime(2019, 1, 4, 8, tzinfo=UTC)
    res = collections.defaultdict(lambda: collections.Counter())
    exemples_manquants = []
    while ms(t) < maintenant_ms - 9 * JOUR_MS:
        tm = ms(t)
        a = str(t.year)
        res[a]["vendredis"] += 1
        proche = [e for e in echeances if tm + 5 * JOUR_MS <= e <= tm + 9 * JOUR_MS]
        mois = [e for e in echeances if tm + 21 * JOUR_MS <= e <= tm + 49 * JOUR_MS]
        s = livraisons.get(t.strftime("%Y-%m-%d"))
        ok7 = False
        for e in proche:
            cotes = [(k, ty) for (c, k, ty) in par_echeance[e] if c <= tm]
            if not cotes:
                continue
            res[a]["avec_echeance_5_9j_cotee"] += 1 if not ok7 else 0
            ok7 = True
            if s:
                puts = {k for k, ty in cotes if ty == "put" and 0.85 * s <= k < 0.97 * s}
                calls = {k for k, ty in cotes if ty == "call" and 1.03 * s < k <= 1.15 * s}
                atm = {k for k, ty in cotes if 0.97 * s <= k <= 1.03 * s}
                if len(puts) >= 2 and len(calls) >= 2 and atm:
                    res[a]["echeance_5_9j_avec_2puts_2calls_3a15pct_et_atm"] += 1
                    break
        if not ok7 and len(exemples_manquants) < 10:
            exemples_manquants.append(t.strftime("%Y-%m-%d"))
        if any(any(c <= tm for (c, _, _) in par_echeance[e]) for e in mois):
            res[a]["avec_echeance_21_49j_cotee"] += 1
        if not s:
            res[a]["sans_prix_de_livraison"] += 1
        t += dt.timedelta(days=7)
    return {"par_annee": {a: dict(v) for a, v in sorted(res.items())}, "vendredis_sans_echeance_5_9j": exemples_manquants}


# ---------------------------------------------------------------- transactions

def tranche_echeance(jours: float) -> str:
    for borne, nom in ((1, "<1j"), (3, "1-3j"), (10, "3-10j"), (40, "10-40j"), (100, "40-100j")):
        if jours < borne:
            return nom
    return ">=100j"


def tranche_monnaie(m: float) -> str:
    a = abs(m)
    for borne, nom in ((0.03, "|ln K/S|<3%"), (0.15, "3-15%"), (0.30, "15-30%")):
        if a < borne:
            return nom
    return ">=30%"


def analyser_jour(jour: str, trades: list[dict], tronque: bool) -> dict:
    n = len(trades)
    champs = collections.Counter()
    types = collections.defaultdict(set)
    for tr in trades:
        for k, v in tr.items():
            champs[k] += 1
            types[k].add(type(v).__name__)
    iv_nul = sum(1 for tr in trades if tr.get("iv") in (0, 0.0))
    iv_absent = sum(1 for tr in trades if tr.get("iv") is None)
    blocs = sum(1 for tr in trades if tr.get("block_trade_id"))
    liq = sum(1 for tr in trades if tr.get("liquidation"))
    combo = sum(1 for tr in trades if tr.get("combo_id"))
    instr, echeances, strikes = set(), set(), set()
    t_ech = collections.Counter()
    t_mon = collections.Counter()
    heures = collections.Counter()
    # cible d'un strangle hebdomadaire : échéance 3-10 jours, ailes à 3-15 % hors de la monnaie
    cible_heures_put, cible_heures_call = set(), set()
    cible_strikes = set()
    cible_n = 0
    fen_0709 = {"n": 0, "strikes_3_10j": set()}
    for tr in trades:
        nom = tr["instrument_name"]
        p = nom.split("-")
        if len(p) != 4:
            continue
        instr.add(nom)
        exp = dt.datetime.strptime(p[1], "%d%b%y").replace(hour=8, tzinfo=UTC)
        echeances.add(p[1])
        k = float(p[2])
        strikes.add(k)
        jours = (ms(exp) - tr["timestamp"]) / JOUR_MS
        t_ech[tranche_echeance(jours)] += 1
        s = tr.get("index_price")
        h = dt.datetime.fromtimestamp(tr["timestamp"] / 1000, UTC).hour
        heures[h] += 1
        if s:
            m = math.log(k / s)
            t_mon[tranche_monnaie(m)] += 1
            if 3 <= jours < 10:
                if p[3] == "P" and -0.15 <= m <= -0.03:
                    cible_heures_put.add(h); cible_strikes.add(k); cible_n += 1
                if p[3] == "C" and 0.03 <= m <= 0.15:
                    cible_heures_call.add(h); cible_strikes.add(k); cible_n += 1
        if 7 <= h < 9:
            fen_0709["n"] += 1
            if 3 <= jours < 10:
                fen_0709["strikes_3_10j"].add(k)
    ts = [tr["timestamp"] for tr in trades]
    return {
        "jour": jour,
        "transactions": n,
        "tronque_par_plafond_de_pages": tronque,
        "premiere": iso(min(ts)) if ts else None,
        "derniere": iso(max(ts)) if ts else None,
        "champs_presence": {k: f"{v}/{n}" for k, v in sorted(champs.items())},
        "champs_types": {k: sorted(v) for k, v in sorted(types.items())},
        "iv_nulle": iv_nul, "iv_absente": iv_absent,
        "transactions_de_bloc": blocs, "liquidations": liq, "combos": combo,
        "instruments_distincts": len(instr), "echeances_distinctes": len(echeances),
        "strikes_distincts": len(strikes),
        "par_tranche_echeance": dict(t_ech), "par_tranche_monnaie": dict(t_mon),
        "heures_avec_transaction": len(heures),
        "cible_strangle_3_10j_3_15pct": {
            "transactions": cible_n, "strikes_distincts": len(cible_strikes),
            "heures_avec_put": len(cible_heures_put), "heures_avec_call": len(cible_heures_call),
            "heures_avec_put_et_call": len(cible_heures_put & cible_heures_call),
        },
        "fenetre_07_09_utc": {"transactions": fen_0709["n"], "strikes_3_10j": len(fen_0709["strikes_3_10j"])},
    }


def transactions_du_jour(jour: str, pages_max: int, hote: str = HIST) -> tuple[list[dict], bool, int]:
    d0 = dt.datetime.strptime(jour, "%Y-%m-%d").replace(tzinfo=UTC)
    debut, fin = ms(d0), ms(d0) + JOUR_MS - 1
    vus, trades, pages = set(), [], 0
    tronque = False
    while True:
        r = appel(hote, "get_last_trades_by_currency_and_time",
                  {"currency": "BTC", "kind": "option", "start_timestamp": debut, "end_timestamp": fin,
                   "count": 1000, "sorting": "asc"})
        pages += 1
        if not r["ok"]:
            break
        lot = r["result"].get("trades", [])
        for tr in lot:
            if tr["trade_id"] not in vus:
                vus.add(tr["trade_id"]); trades.append(tr)
        if not r["result"].get("has_more") or not lot:
            break
        dernier = lot[-1]["timestamp"]
        debut = dernier if dernier > debut else debut + 1
        if pages >= pages_max:
            tronque = True
            break
    return trades, tronque, pages


# ---------------------------------------------------------------- forme d'une réponse sans valeur

def forme(res) -> dict:
    """Décrit une réponse (clés, longueurs, bornes temporelles) sans recopier de niveau de prix ou de volatilité."""
    if isinstance(res, list):
        d = {"type": "liste", "longueur": len(res)}
        if res and isinstance(res[0], list):
            d["element"] = f"liste de {len(res[0])} nombres"
            d["premier_horodatage"] = iso(res[0][0]); d["dernier_horodatage"] = iso(res[-1][0])
        elif res and isinstance(res[0], dict):
            d["cles"] = sorted(res[0].keys())
        return d
    if isinstance(res, dict):
        d = {"type": "objet", "cles": sorted(res.keys())}
        for k in ("ticks", "data", "bids", "asks"):
            if k in res and isinstance(res[k], list):
                d[f"longueur_{k}"] = len(res[k])
                if k in ("ticks",) and res[k]:
                    d["premier_horodatage"] = iso(res[k][0]); d["dernier_horodatage"] = iso(res[k][-1])
                if k == "data" and res[k] and isinstance(res[k][0], list):
                    d["premier_horodatage"] = iso(res[k][0][0]); d["dernier_horodatage"] = iso(res[k][-1][0])
        if "status" in res:
            d["status"] = res["status"]
        if isinstance(res.get("volume"), list):
            d["ticks_avec_volume_non_nul"] = sum(1 for v in res["volume"] if v)
        if isinstance(res.get("timestamp"), int):
            d["horodatage_de_l_objet"] = iso(res["timestamp"])
        if "state" in res:
            d["state"] = res["state"]
        for k in ("mark_iv", "bid_iv", "ask_iv", "greeks", "best_bid_price", "underlying_price"):
            if k in res:
                d[f"champ_{k}"] = type(res[k]).__name__
        return d
    return {"type": type(res).__name__}


def tester(hote, methode, params) -> dict:
    r = appel(hote, methode, params)
    if r["ok"]:
        return {"hote": hote, "methode": methode, "ok": True, "forme": forme(r["result"])}
    return {"hote": hote, "methode": methode, "ok": False, "erreur": r["erreur"]}


# ---------------------------------------------------------------- programme

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-instruments", default=None,
                    help="fichier JSON local de get_instruments expirés (évite un second téléchargement de 78 Mo)")
    ap.add_argument("--pages-max", type=int, default=60)
    args = ap.parse_args()
    t_debut = time.time()
    horo = dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    maintenant = ms(dt.datetime.now(UTC))
    sortie: dict = {"horodatage_utc": horo, "regles": "aucun rendement, aucune valeur de volatilité implicite"}

    # A. instruments ---------------------------------------------------------
    print("A. instruments")
    if args.cache_instruments and Path(args.cache_instruments).exists():
        hist = json.loads(Path(args.cache_instruments).read_text())["result"]
        sortie["A_source_liste_expiree"] = f"cache local d'un appel identique ({args.cache_instruments})"
    else:
        r = appel(HIST, "get_instruments", {"currency": "BTC", "kind": "option", "expired": "true"})
        hist = r["result"] if r["ok"] else []
        sortie["A_source_liste_expiree"] = "appel direct"
    r_www_exp = appel(WWW, "get_instruments", {"currency": "BTC", "kind": "option", "expired": "true"})
    r_www_act = appel(WWW, "get_instruments", {"currency": "BTC", "kind": "option", "expired": "false"})
    www_exp = r_www_exp["result"] if r_www_exp["ok"] else []
    www_act = r_www_act["result"] if r_www_act["ok"] else []
    noms_hist = {x["instrument_name"] for x in hist}
    sortie["A_history_expired"] = resume_instruments(hist, maintenant)
    fut = [x for x in hist if x["expiration_timestamp"] > maintenant]
    sortie["A_history_expired"]["echeances_futures_detail"] = dict(collections.Counter(
        f"{iso(x['expiration_timestamp'])} is_active={x.get('is_active')} state={x.get('state')}" for x in fut))
    sortie["A_www_expired"] = {"n": len(www_exp),
                               "premiere_echeance": iso(min((x["expiration_timestamp"] for x in www_exp), default=None)),
                               "derniere_echeance": iso(max((x["expiration_timestamp"] for x in www_exp), default=None)),
                               "presents_dans_history": sum(1 for x in www_exp if x["instrument_name"] in noms_hist)}
    sortie["A_www_actifs"] = resume_instruments(www_act, maintenant) if www_act else {"n": 0}
    sortie["A_www_actifs"]["presents_dans_history"] = sum(1 for x in www_act if x["instrument_name"] in noms_hist)

    # prix de livraison quotidiens (08:00 UTC) : profondeur, et centrage des bandes de prix d'exercice
    livraisons, offset, total = {}, 0, None
    while True:
        r = appel(WWW, "get_delivery_prices", {"index_name": "btc_usd", "offset": offset, "count": 1000})
        if not r["ok"]:
            sortie["A_livraisons_erreur"] = r["erreur"]; break
        lot = r["result"].get("data", [])
        total = r["result"].get("records_total")
        for x in lot:
            livraisons[x["date"]] = x["delivery_price"]
        offset += len(lot)
        if not lot or offset >= (total or 0) or offset > 5000:
            break
    sortie["E_prix_de_livraison_btc_usd"] = {"n_jours": len(livraisons), "records_total": total,
                                              "premier_jour": min(livraisons) if livraisons else None,
                                              "dernier_jour": max(livraisons) if livraisons else None,
                                              "champs": ["date", "delivery_price"]}
    union = {x["instrument_name"]: x for x in hist}
    for x in www_act + www_exp:
        union.setdefault(x["instrument_name"], x)
    sortie["A_couverture_hebdomadaire"] = couverture_hebdo(list(union.values()), livraisons, maintenant)

    # B. transactions --------------------------------------------------------
    print("B. transactions")
    r = appel(HIST, "get_last_trades_by_currency_and_time",
              {"currency": "BTC", "kind": "option", "start_timestamp": ms(dt.datetime(2015, 1, 1, tzinfo=UTC)),
               "end_timestamp": maintenant, "count": 1, "sorting": "asc"})
    premiere_tr = r["result"]["trades"][0]["timestamp"] if r["ok"] and r["result"].get("trades") else None
    sortie["B_premiere_transaction_options_btc"] = iso(premiere_tr)
    r = appel(HIST, "get_last_trades_by_instrument_and_time",
              {"instrument_name": "BTC-15JUL16-600-C", "start_timestamp": 0, "end_timestamp": maintenant,
               "count": 10, "sorting": "asc"})
    sortie["B_par_instrument_2016"] = ({"ok": True, "n": len(r["result"].get("trades", [])),
                                        "has_more": r["result"].get("has_more"),
                                        "cles": sorted(r["result"]["trades"][0].keys()) if r["result"].get("trades") else []}
                                       if r["ok"] else {"ok": False, "erreur": r["erreur"]})
    r = appel(WWW, "get_last_trades_by_currency_and_time",
              {"currency": "BTC", "kind": "option", "start_timestamp": ms(dt.datetime(2022, 5, 12, tzinfo=UTC)),
               "end_timestamp": ms(dt.datetime(2022, 5, 12, 1, tzinfo=UTC)), "count": 10, "sorting": "asc"})
    sortie["B_www_meme_requete_2022"] = ({"ok": True, "n": len(r["result"].get("trades", []))} if r["ok"]
                                         else {"ok": False, "erreur": r["erreur"]})
    jours = []
    for j in JOURS:
        pm = 10 if j.startswith("2019") else args.pages_max
        trades, tronque, pages = transactions_du_jour(j, pm)
        a = analyser_jour(j, trades, tronque)
        a["pages"] = pages
        jours.append(a)
        if j == JOURS[-1]:
            DERNIERES_TRANSACTIONS.extend(trades)
        if j == "2019-06-12" and trades:
            nom19 = collections.Counter(tr["instrument_name"] for tr in trades).most_common(1)[0][0]
            r = appel(HIST, "get_last_trades_by_instrument_and_time",
                      {"instrument_name": nom19, "start_timestamp": 0, "end_timestamp": maintenant,
                       "count": 1000, "sorting": "asc"})
            sortie["B_par_instrument_2019"] = ({"instrument": nom19, "n_premiere_page": len(r["result"].get("trades", [])),
                                                "has_more": r["result"].get("has_more"),
                                                "premiere": iso(r["result"]["trades"][0]["timestamp"]) if r["result"].get("trades") else None}
                                               if r["ok"] else {"ok": False, "erreur": r["erreur"]})
        print(f"  {j} : {len(trades)} transactions, {pages} pages, tronqué={tronque}")
    sortie["B_jours"] = jours

    # C. cotations historiques -----------------------------------------------
    print("C. cotations")
    exp_ms = ms(dt.datetime(2024, 12, 27, 8, tzinfo=UTC))
    candidates = [x for x in hist if x["expiration_timestamp"] == exp_ms and x["option_type"] == "call"]
    choisi = min(candidates, key=lambda x: abs(x["strike"] - 100000))["instrument_name"] if candidates else "BTC-27DEC24-100000-C"
    # option expirée récente la plus traitée le dernier jour d'échantillon (échéance passée)
    der = collections.Counter(tr["instrument_name"] for tr in DERNIERES_TRANSACTIONS
                              if dt.datetime.strptime(tr["instrument_name"].split("-")[1], "%d%b%y")
                              .replace(hour=8, tzinfo=UTC) < dt.datetime.now(UTC))
    recent = der.most_common(1)[0][0] if der else None
    # option vivante la plus ancienne (création la plus lointaine), prix d'exercice proche de la dernière livraison
    s_der = livraisons[max(livraisons)] if livraisons else None
    vieux = sorted(www_act, key=lambda x: (x.get("creation_timestamp") or maintenant,
                                           abs(x["strike"] - s_der) if s_der else 0))
    actif = vieux[0] if vieux else None
    tests = []
    fin_vie = exp_ms - 1
    for nom in [choisi] + ([recent] if recent else []):
        for hote in (WWW, HIST):
            tests.append({"instrument": nom, **tester(hote, "ticker", {"instrument_name": nom})})
            tests.append({"instrument": nom, **tester(hote, "get_order_book", {"instrument_name": nom, "depth": 5})})
            tests.append({"instrument": nom, **tester(hote, "get_mark_price_history",
                                                       {"instrument_name": nom, "start_timestamp": fin_vie - 10 * JOUR_MS,
                                                        "end_timestamp": fin_vie})})
            tests.append({"instrument": nom, **tester(hote, "get_tradingview_chart_data",
                                                       {"instrument_name": nom, "start_timestamp": fin_vie - 30 * JOUR_MS,
                                                        "end_timestamp": fin_vie, "resolution": "60"})})
            tests.append({"instrument": nom, **tester(hote, "get_book_summary_by_instrument", {"instrument_name": nom})})
        fin_vie = maintenant
    if actif:
        nom = actif["instrument_name"]
        c0 = actif.get("creation_timestamp") or maintenant - 90 * JOUR_MS
        tests.append({"instrument": nom + " (actif)", **tester(WWW, "ticker", {"instrument_name": nom})})
        for fen, debut in (("depuis la création", c0), ("10 derniers jours", maintenant - 10 * JOUR_MS),
                           ("dernier jour", maintenant - JOUR_MS)):
            t = tester(WWW, "get_mark_price_history", {"instrument_name": nom, "start_timestamp": debut,
                                                       "end_timestamp": maintenant})
            tests.append({"instrument": nom + f" (actif, {fen})", **t})
        tests.append({"instrument": nom + " (actif)", **tester(WWW, "get_tradingview_chart_data",
                                                                 {"instrument_name": nom, "start_timestamp": c0,
                                                                  "end_timestamp": maintenant, "resolution": "60"})})
        sortie["C_actif_creation"] = iso(c0)
    tests.append({"instrument": "toutes options BTC (instantané)",
                  **tester(WWW, "get_book_summary_by_currency", {"currency": "BTC", "kind": "option"})})
    sortie["C_tests_cotations"] = tests

    # D. DVOL et volatilité historique ----------------------------------------
    print("D. DVOL")
    dvol, fin, cont, pages = [], maintenant, None, 0
    while pages < 6:
        p = {"currency": "BTC", "start_timestamp": ms(dt.datetime(2017, 1, 1, tzinfo=UTC)), "end_timestamp": fin,
             "resolution": "1D"}
        r = appel(WWW, "get_volatility_index_data", p)
        pages += 1
        if not r["ok"]:
            sortie["D_dvol_erreur"] = r["erreur"]; break
        lot = r["result"].get("data", [])
        dvol.extend(lot)
        cont = r["result"].get("continuation")
        if not lot or not cont:
            break
        fin = cont
    ts = sorted({x[0] for x in dvol})
    trous = sum(1 for a, b in zip(ts, ts[1:]) if b - a > JOUR_MS)
    sortie["D_dvol_1D"] = {"points": len(ts), "premier": iso(ts[0]) if ts else None, "dernier": iso(ts[-1]) if ts else None,
                           "pages": pages, "element": "horodatage, ouverture, haut, bas, clôture", "trous_de_plus_d_un_jour": trous}
    for res, debut in (("3600", dt.datetime(2021, 3, 24, tzinfo=UTC)), ("60", dt.datetime(2021, 5, 19, tzinfo=UTC)),
                       ("1", dt.datetime(2021, 5, 19, tzinfo=UTC))):
        r = appel(WWW, "get_volatility_index_data", {"currency": "BTC", "start_timestamp": ms(debut),
                                                      "end_timestamp": ms(debut) + JOUR_MS, "resolution": res})
        sortie[f"D_dvol_{res}s_le_{debut:%Y-%m-%d}"] = forme(r["result"]) if r["ok"] else {"erreur": r["erreur"]}
    r = appel(WWW, "get_historical_volatility", {"currency": "BTC"})
    sortie["D_volatilite_historique"] = forme(r["result"]) if r["ok"] else {"erreur": r["erreur"]}

    # E. indice et sous-jacent -------------------------------------------------
    print("E. indice")
    for nom, hote in (("BTC-PERPETUAL", WWW), ("BTC-25JUN21", WWW), ("BTC-25JUN21", HIST)):
        r = appel(hote, "get_tradingview_chart_data", {"instrument_name": nom,
                                                       "start_timestamp": ms(dt.datetime(2016, 1, 1, tzinfo=UTC)),
                                                       "end_timestamp": maintenant, "resolution": "1D"})
        sortie[f"E_bougies_1D_{nom}_{hote}"] = forme(r["result"]) if r["ok"] else {"erreur": r["erreur"]}
    r = appel(WWW, "get_tradingview_chart_data", {"instrument_name": "BTC-PERPETUAL",
                                                  "start_timestamp": ms(dt.datetime(2019, 6, 12, tzinfo=UTC)),
                                                  "end_timestamp": ms(dt.datetime(2019, 6, 13, tzinfo=UTC)), "resolution": "1"})
    sortie["E_bougies_1min_BTC-PERPETUAL_2019-06-12"] = forme(r["result"]) if r["ok"] else {"erreur": r["erreur"]}
    r = appel(WWW, "get_index_chart_data", {"index_name": "btc_usd", "range": "all"})
    sortie["E_indice_btc_usd_range_all"] = forme(r["result"]) if r["ok"] else {"erreur": r["erreur"]}

    # bilan des appels ---------------------------------------------------------
    par = collections.Counter((a["hote"], a["methode"], a["ok"]) for a in APPELS)
    sortie["appels"] = {"n": len(APPELS), "erreurs": sum(1 for a in APPELS if not a["ok"]),
                        "par_methode": {f"{h} {m} ok={o}": n for (h, m, o), n in sorted(par.items())},
                        "octets_total": sum(a.get("octets") or 0 for a in APPELS),
                        "erreurs_detail": [{k: a.get(k) for k in ("hote", "methode", "http", "erreur")}
                                           for a in APPELS if not a["ok"]]}
    sortie["duree_secondes"] = round(time.time() - t_debut, 1)
    chemin = ICI / f"audit_options_{horo}.json"
    chemin.write_text(json.dumps(sortie, ensure_ascii=False, indent=1))
    print(chemin, sortie["appels"]["n"], "appels", sortie["appels"]["erreurs"], "erreurs", sortie["duree_secondes"], "s")


if __name__ == "__main__":
    main()
