#!/usr/bin/env python3
"""APR net d'un portage de financement delta neutre (STRAT-20261031-02).

Recherche seulement : aucun ordre, aucune clé, points d'accès publics en lecture.
L'APR historique n'est pas un rendement attendu : il ne compte aucun sinistre
de plateforme, aucun ADL, aucun dépeg.

Absence de biais d'anticipation :
- le signal en t n'utilise que les taux réglés jusqu'à t inclus ;
- l'entrée se fait après le règlement t, le taux de t n'est donc pas encaissé ;
- le test de liquidation entre t-1 et t utilise les bougies de cet intervalle.
Le contrôle `controles_biais` le vérifie sur données réelles et synthétiques.

Usage :
  apr_net.py --plan                 exécute le registre E01 à E12 (paramètres figés)
  apr_net.py --seuil-entree 15 ...  essai libre, marqué LIBRE, à inscrire au registre
  apr_net.py --financement-brut     décrit le marché depuis le cache, sans simulation, pas un essai
  apr_net.py --stress-adl           pires baisses spot sur 4 h, calées et glissantes, sans simulation, pas un essai
  apr_net.py --controle-financement recalcule le financement des trades d'une exécution depuis les fichiers bruts
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import sys
import time
from dataclasses import dataclass, replace, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.stats import norm

ICI = Path(__file__).resolve().parent
H4_MS = 4 * 3600 * 1000
PAS_MS = {"4h": H4_MS, "15m": 15 * 60 * 1000}
PAS_BYBIT = {"4h": "240", "15m": "15"}
EXECUTION_REFERENCE = "20261031T224137Z"  # fiche § 9, script archivé dans resultats/
HEURES_AN = 365.0 * 24.0
MAJEURS = {"BTC", "ETH"}
PARAMS_GLISS = {True: 0.02, False: 0.05}  # % par jambe et par côté, valeurs de la fiche § 1
FRAIS = {  # preneur, grille de base, en %
    "binance": {"spot": 0.10, "perp": 0.05},
    "bybit": {"spot": 0.10, "perp": 0.055},
}
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "strat-20261031-02-recherche/1.0"

# Découpage de la fiche, § 3.
DEV = ("2021-01-01", "2024-06-30 23:59:59")
VAL = ("2024-07-01", "2025-07-31 23:59:59")
HE = ("2025-08-01", "2026-10-31 23:59:59")
FIN_DEV_VAL = VAL[1]


@dataclass(frozen=True)
class Params:
    seuil_entree: float = 10.0  # %/an sur le notionnel
    seuil_sortie: float = 3.0   # %/an
    fenetre_h: int = 24
    levier: float = 1.0
    reequilibrage: float = 25.0  # % d'écart de prix
    mult_couts: float = 1.0
    gliss_majeurs: float = 0.02  # % par jambe et par côté
    gliss_alts: float = 0.05
    marge_maintenance: float = 0.5  # %


# ---------------------------------------------------------------- téléchargement

def get_json(url: str, params: dict | None = None, essais: int = 5):
    derniere = None
    for k in range(essais):
        try:
            r = SESSION.get(url, params=params, timeout=30)
            if r.status_code in (418, 429):
                time.sleep(30)
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:  # réseau ou JSON invalide
            derniere = e
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"échec {url} {params} : {derniere}")


def binance_funding(sym: str, debut: int, fin: int) -> pd.DataFrame:
    lignes, cur = [], debut
    while cur < fin:
        d = get_json("https://fapi.binance.com/fapi/v1/fundingRate",
                     {"symbol": sym, "startTime": cur, "endTime": fin, "limit": 1000})
        if not d:
            break
        lignes += [(int(x["fundingTime"]), float(x["fundingRate"])) for x in d]
        cur = int(d[-1]["fundingTime"]) + 1
        if len(d) < 1000:
            break
        time.sleep(0.1)
    return pd.DataFrame(lignes, columns=["t", "taux"])


def bybit_funding(sym: str, debut: int, fin: int) -> pd.DataFrame:
    lignes, cur = [], fin
    while cur > debut:
        d = get_json("https://api.bybit.com/v5/market/funding/history",
                     {"category": "linear", "symbol": sym, "endTime": cur, "limit": 200})
        if d.get("retCode") != 0:
            raise RuntimeError(f"Bybit {sym} : {d.get('retMsg')}")
        rows = d["result"]["list"]
        if not rows:
            break
        lignes += [(int(x["fundingRateTimestamp"]), float(x["fundingRate"])) for x in rows]
        plus_ancien = min(int(x["fundingRateTimestamp"]) for x in rows)
        if plus_ancien >= cur:
            break
        cur = plus_ancien - 1
        time.sleep(0.05)
    df = pd.DataFrame(lignes, columns=["t", "taux"])
    return df[df.t >= debut]


def binance_bougies(sym: str, marche: str, debut: int, fin: int, pas: str = "4h") -> pd.DataFrame:
    url = ("https://api.binance.com/api/v3/klines" if marche == "spot"
           else "https://fapi.binance.com/fapi/v1/klines")
    lignes, cur = [], debut
    while cur < fin:
        d = get_json(url, {"symbol": sym, "interval": pas, "startTime": cur, "endTime": fin, "limit": 1000})
        if not d:
            break
        lignes += [(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4])) for x in d]
        cur = int(d[-1][0]) + PAS_MS[pas]
        if len(d) < 1000:
            break
        time.sleep(0.1)
    return pd.DataFrame(lignes, columns=["t", "o", "h", "l", "c"])


def bybit_bougies(sym: str, marche: str, debut: int, fin: int, pas: str = "4h") -> pd.DataFrame:
    cat = "spot" if marche == "spot" else "linear"
    lignes, cur = [], fin
    while cur > debut:
        d = get_json("https://api.bybit.com/v5/market/kline",
                     {"category": cat, "symbol": sym, "interval": PAS_BYBIT[pas], "start": debut, "end": cur, "limit": 1000})
        if d.get("retCode") != 0:
            raise RuntimeError(f"Bybit {sym} {cat} : {d.get('retMsg')}")
        rows = d["result"]["list"]
        if not rows:
            break
        lignes += [(int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4])) for x in rows]
        plus_ancien = min(int(x[0]) for x in rows)
        if plus_ancien <= debut or plus_ancien >= cur:
            break
        cur = plus_ancien - 1
        time.sleep(0.05)
    return pd.DataFrame(lignes, columns=["t", "o", "h", "l", "c"])


def en_cache(chemin: Path, charger, rafraichir: bool, manifeste: dict) -> pd.DataFrame:
    """Lit le cache ou télécharge. Note dans le manifeste la source et le contenu réel."""
    origine = "cache"
    if chemin.exists() and not rafraichir:
        df = pd.read_csv(chemin)
    else:
        df = charger()
        df = df.drop_duplicates("t").sort_values("t").reset_index(drop=True)
        with gzip.GzipFile(chemin, "wb", mtime=0) as f:
            f.write(df.to_csv(index=False).encode())
        origine = "téléchargé"
    brut = df.to_csv(index=False).encode()
    stat = chemin.stat() if chemin.exists() else None
    manifeste[chemin.name] = {
        "origine": origine,
        "fichier_modifie_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat() if stat else None,
        "lignes": len(df),
        "premier_utc": str(pd.to_datetime(df.t.iloc[0], unit="ms")) if len(df) else None,
        "dernier_utc": str(pd.to_datetime(df.t.iloc[-1], unit="ms")) if len(df) else None,
        "sha256": hashlib.sha256(brut).hexdigest(),
    }
    return df


def charger_paire(plateforme: str, base: str, debut_ms: int, fin_ms: int, dossier: Path,
                  rafraichir: bool, manifeste: dict) -> dict:
    sym = f"{base}USDT"
    f_fund = binance_funding if plateforme == "binance" else bybit_funding
    f_boug = binance_bougies if plateforme == "binance" else bybit_bougies
    fund = en_cache(dossier / f"{plateforme}_{sym}_financement.csv.gz",
                    lambda: f_fund(sym, debut_ms, fin_ms), rafraichir, manifeste)
    spot = en_cache(dossier / f"{plateforme}_{sym}_spot4h.csv.gz",
                    lambda: f_boug(sym, "spot", debut_ms, fin_ms), rafraichir, manifeste)
    perp = en_cache(dossier / f"{plateforme}_{sym}_perp4h.csv.gz",
                    lambda: f_boug(sym, "perp", debut_ms, fin_ms), rafraichir, manifeste)
    return {"fund": fund, "spot": spot, "perp": perp}


def charger_fred(dossier: Path, rafraichir: bool, manifeste: dict) -> pd.Series | None:
    chemin = dossier / "fred_DFF.csv.gz"
    try:
        if rafraichir or not chemin.exists():
            r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": "DFF"}, timeout=60)
            r.raise_for_status()
            with gzip.GzipFile(chemin, "wb", mtime=0) as f:
                f.write(r.content)
        df = pd.read_csv(chemin)
        df.columns = ["date", "taux"]
        df["taux"] = pd.to_numeric(df.taux, errors="coerce")
        s = df.dropna().set_index(pd.to_datetime(df.dropna().date)).taux
        manifeste["fred_DFF"] = {"premier": str(s.index[0].date()), "dernier": str(s.index[-1].date()),
                                 "derniere_valeur_pct": float(s.iloc[-1])}
        return s
    except Exception as e:  # lacune déclarée, pas bloquante
        manifeste["fred_DFF"] = {"erreur": str(e)}
        return None


# ---------------------------------------------------------------- préparation

def preparer(brut: dict) -> tuple[pd.DataFrame, dict]:
    """Aligne chaque règlement sur le prix d'ouverture de la bougie 4 h qui le contient."""
    fund = brut["fund"].copy()
    fund["ts"] = pd.to_datetime(fund.t, unit="ms").dt.round("min")
    fund = fund.drop_duplicates("ts").sort_values("ts").reset_index(drop=True)
    delta = fund.ts.diff().dt.total_seconds() / 3600.0
    trous = int((delta > 8.01).sum())
    fund["intervalle_h"] = delta.where(delta <= 8.01, 8.0).fillna(8.0)
    fund["ann"] = fund.taux * 100.0 * HEURES_AN / fund.intervalle_h

    def cote(df, nom):
        d = df.copy()
        d["ts"] = pd.to_datetime(d.t, unit="ms")
        return d.sort_values("ts")[["ts", "o", "h", "l", "c"]].rename(
            columns={c: f"{c}_{nom}" for c in "ohlc"})

    spot, perp = cote(brut["spot"], "s"), cote(brut["perp"], "p")
    x = pd.merge_asof(fund, spot, on="ts", tolerance=pd.Timedelta("4h"))
    x = pd.merge_asof(x, perp, on="ts", tolerance=pd.Timedelta("4h"))

    # Plus haut du perpétuel entre ce règlement et le suivant.
    ouv = perp.ts.values
    hauts = perp.h_p.values
    tt = x.ts.values
    hi = np.full(len(x), np.nan)
    for i in range(len(x)):
        g = max(np.searchsorted(ouv, tt[i], side="right") - 1, 0)
        d = np.searchsorted(ouv, tt[i + 1], side="left") if i + 1 < len(x) else g + 1
        d = max(d, g + 1)
        hi[i] = np.nanmax(hauts[g:d]) if d > g and g < len(hauts) else np.nan
    x["hi_apres"] = hi
    infos = {"trous_financement": trous, "reglements": len(fund),
             "intervalle_median_h": float(fund.intervalle_h.median()),
             "reglements_sans_prix": int(x[["o_s", "o_p"]].isna().any(axis=1).sum())}
    return x, infos


def premier_valide(x: pd.DataFrame) -> pd.Timestamp | None:
    ok = x.dropna(subset=["o_s", "o_p"])
    return ok.ts.iloc[0] if len(ok) else None


# ---------------------------------------------------------------- simulation

def simuler(x: pd.DataFrame, p: Params, base: str, plateforme: str, debut, fin,
            forcer_cloture: bool = True) -> tuple[pd.DataFrame, list[dict]]:
    """Machine à états, un pas par règlement. Capital de départ : 1."""
    sig = x.set_index("ts").ann.rolling(f"{p.fenetre_h}h").mean().values
    ok = (x.ts >= pd.Timestamp(debut)) & (x.ts <= pd.Timestamp(fin)) & x.o_s.notna() & x.o_p.notna()
    idx = np.flatnonzero(ok.values)
    if len(idx) == 0:
        return pd.DataFrame(), []
    fs = FRAIS[plateforme]["spot"] / 100.0 * p.mult_couts
    fp = FRAIS[plateforme]["perp"] / 100.0 * p.mult_couts
    g = (p.gliss_majeurs if base in MAJEURS else p.gliss_alts) / 100.0 * p.mult_couts
    mmr = p.marge_maintenance / 100.0
    L = p.levier
    S_, F_, f_, hi_, dt_, ts_ = (x.o_s.values, x.o_p.values, x.taux.values, x.hi_apres.values,
                                 x.intervalle_h.values, x.ts.values)
    E, Q, M = 1.0, 0.0, 0.0
    pos = False
    prevS = prevF = Preb = 0.0
    prev_i = None
    lignes, trades = [], []
    tr = None

    def ouvrir_trade(t, S, F, E):
        return {"entree": t, "base_entree_pb": (F / S - 1) * 1e4, "signal_entree": None, "capital_entree": E,
                "financement": 0.0, "pnl_base": 0.0, "frais": 0.0, "glissement": 0.0, "reequilibrages": 0}

    for pas, i in enumerate(idx):
        t, S, F, f, sg = ts_[i], S_[i], F_[i], f_[i], sig[i]
        inc = dict(fund=0.0, fee=0.0, slip=0.0, base=0.0, liq=0.0, reeq=0.0, rebs=0, closes=0, liqs=0,
                   dt=dt_[i], dt_pos=0.0, notional_dt=0.0)
        if pos:
            inc["dt_pos"] = dt_[i]
            inc["notional_dt"] = Q * F * dt_[i] / HEURES_AN
            prix_liq = (M + Q * prevF) / (Q * (1.0 + mmr))
            hi = hi_[prev_i]
            if not np.isnan(hi) and hi >= prix_liq:
                # Liquidation : marge perdue, spot vendu au règlement suivant.
                avant = Q * prevS + M
                inc["fee"] = Q * S * fs
                inc["slip"] = Q * S * g
                E = Q * S - inc["fee"] - inc["slip"]
                inc["liq"] = E + inc["fee"] + inc["slip"] - avant
                pos = False
                inc["liqs"] = 1
                inc["closes"] = 1
                tr.update(sortie=t, motif="liquidation", base_sortie_pb=(F / S - 1) * 1e4, capital_sortie=E)
                tr["frais"] += inc["fee"]
                tr["glissement"] += inc["slip"]
                trades.append(tr)
                tr = None
            else:
                inc["base"] = Q * ((S - prevS) - (F - prevF))
                inc["fund"] = f * Q * F  # le court encaisse si le taux est positif
                M += Q * (prevF - F) + inc["fund"]
                tr["financement"] += inc["fund"]
                tr["pnl_base"] += inc["base"]
                valeur = Q * S + M
                dernier = forcer_cloture and pas == len(idx) - 1
                if sg < p.seuil_sortie or dernier:
                    inc["fee"] = Q * S * fs + Q * F * fp
                    inc["slip"] = (Q * S + Q * F) * g
                    E = valeur - inc["fee"] - inc["slip"]
                    pos = False
                    inc["closes"] = 1
                    tr.update(sortie=t, motif="fin de période" if (dernier and not sg < p.seuil_sortie) else "signal",
                              base_sortie_pb=(F / S - 1) * 1e4, capital_sortie=E)
                    tr["frais"] += inc["fee"]
                    tr["glissement"] += inc["slip"]
                    trades.append(tr)
                    tr = None
                elif abs(F / Preb - 1.0) * 100.0 >= p.reequilibrage:
                    nouv = (valeur / (1.0 + 1.0 / L)) / S
                    dq = abs(nouv - Q)
                    inc["fee"] = dq * S * fs + dq * F * fp
                    inc["slip"] = dq * (S + F) * g
                    inc["reeq"] = inc["fee"] + inc["slip"]
                    M = valeur - inc["fee"] - inc["slip"] - nouv * S
                    Q, Preb = nouv, F
                    inc["rebs"] = 1
                    tr["frais"] += inc["fee"]
                    tr["glissement"] += inc["slip"]
                    tr["reequilibrages"] += 1
        elif not (pas == len(idx) - 1 and forcer_cloture) and sg >= p.seuil_entree:
            # Entrée après le règlement t : le taux de t n'est pas encaissé.
            N = E / (1.0 + 1.0 / L)
            Q = N / S
            inc["fee"] = Q * S * fs + Q * F * fp
            inc["slip"] = (Q * S + Q * F) * g
            M = E - N - inc["fee"] - inc["slip"]
            Preb = F
            pos = True
            tr = ouvrir_trade(t, S, F, E)
            tr["signal_entree"] = float(sg)
            tr["frais"] += inc["fee"]
            tr["glissement"] += inc["slip"]
        prevS, prevF, prev_i = S, F, i
        eq = Q * S + M if pos else E
        lignes.append({"ts": t, "capital": eq, "pos": int(pos), **inc})
    df = pd.DataFrame(lignes).set_index("ts")
    # Rapprochement de la décomposition.
    ecart = (df.capital.iloc[-1] - 1.0) - (df.fund.sum() + df.base.sum() - df.fee.sum() - df.slip.sum() + df.liq.sum())
    if abs(ecart) > 1e-8:
        raise AssertionError(f"décomposition non rapprochée {plateforme} {base} : {ecart}")
    return df, trades


def panier(series: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Somme de capitaux égaux, un par paire, sans rééquilibrage entre paires."""
    index = sorted(set().union(*[set(s.index) for s in series.values()]))
    add = ["fund", "fee", "slip", "base", "liq", "reeq", "rebs", "closes", "liqs", "dt", "dt_pos", "notional_dt"]
    tot = pd.DataFrame(0.0, index=index, columns=["capital"] + add)
    for s in series.values():
        tot["capital"] += s.capital.reindex(index).ffill().fillna(1.0)
        for c in add:
            tot[c] += s[c].reindex(index).fillna(0.0)
    return tot


# ---------------------------------------------------------------- mesures

def stats(df: pd.DataFrame, debut, fin, cap0: float, taux_fixe: float, fred: pd.Series | None) -> dict | None:
    debut, fin = pd.Timestamp(debut), pd.Timestamp(fin)
    sel = df[(df.index >= debut) & (df.index <= fin)]
    if len(sel) < 2:
        return None
    avant = df[df.index < debut]
    eq0 = avant.capital.iloc[-1] if len(avant) else cap0
    t0 = avant.index[-1] if len(avant) else sel.index[0]
    ans = (sel.index[-1] - t0).total_seconds() / (365.0 * 86400.0)
    if ans <= 0:
        return None
    ret = sel.capital.iloc[-1] / eq0 - 1.0
    chemin = pd.concat([pd.Series([eq0]), sel.capital.reset_index(drop=True)])
    dd = float((chemin / chemin.cummax() - 1.0).min())
    jour = sel.capital.resample("D").last().ffill()
    rj = pd.concat([pd.Series([eq0]), jour.reset_index(drop=True)]).pct_change().dropna()
    excedent_j = rj - taux_fixe / 100.0 / 365.0
    sharpe = float(excedent_j.mean() / excedent_j.std() * math.sqrt(365.0)) if excedent_j.std() > 0 else float("nan")
    res = {
        "debut_effectif": str(t0), "fin_effective": str(sel.index[-1]), "duree_ans": round(ans, 3),
        "apr_net_pct": 100.0 * ret / ans,
        "taux_court_pct": taux_fixe,
        "excedent_pct": 100.0 * ret / ans - taux_fixe,
        "financement_pct": 100.0 * sel.fund.sum() / eq0 / ans,
        "frais_pct": -100.0 * sel.fee.sum() / eq0 / ans,
        "glissement_pct": -100.0 * sel.slip.sum() / eq0 / ans,
        "dont_reequilibrage_pct": -100.0 * sel.reeq.sum() / eq0 / ans,
        "pnl_base_pct": 100.0 * sel.base.sum() / eq0 / ans,
        "liquidation_pct": 100.0 * sel.liq.sum() / eq0 / ans,
        "financement_brut_notionnel_pct": 100.0 * sel.fund.sum() / sel.notional_dt.sum() if sel.notional_dt.sum() > 0 else float("nan"),
        "temps_en_position_pct": 100.0 * sel.dt_pos.sum() / sel.dt.sum(),
        "drawdown_max_pct": 100.0 * dd,
        "sharpe_exces_taux_fixe": sharpe,
        "trades_clos": int(sel.closes.sum()),
        "reequilibrages": int(sel.rebs.sum()),
        "liquidations": int(sel.liqs.sum()),
    }
    if fred is not None:
        f = fred[(fred.index >= t0.normalize()) & (fred.index <= sel.index[-1])]
        res["taux_fred_dff_moyen_pct"] = float(f.mean()) if len(f) else float("nan")
        res["excedent_fred_pct"] = res["apr_net_pct"] - res["taux_fred_dff_moyen_pct"]
    return res


def fenetres(fin_effective: pd.Timestamp) -> list[tuple[str, str, str]]:
    w = [(str(a), f"{a}-01-01", f"{a}-12-31 23:59:59") for a in range(2021, fin_effective.year + 1)]
    w.append(("12_derniers_mois", str(fin_effective - pd.Timedelta(days=365)), str(fin_effective)))
    w += [("developpement", *DEV), ("validation", *VAL), ("hors_echantillon", *HE),
          ("toute_la_periode", DEV[0], HE[1])]
    return w


def sharpe_repere(n_essais: int, ans: float) -> float:
    """Espérance du meilleur Sharpe annualisé de n essais sans edge (Bailey et López de Prado)."""
    gamma = 0.5772156649
    e = (1 - gamma) * norm.ppf(1 - 1 / n_essais) + gamma * norm.ppf(1 - 1 / (n_essais * math.e))
    return float(e / math.sqrt(ans))


def carnet(plateforme: str, base: str, tailles: list[float]) -> list[dict]:
    sym = f"{base}USDT"
    res = []
    for marche in ("spot", "perp"):
        horo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        try:
            if plateforme == "binance":
                url = "https://api.binance.com/api/v3/depth" if marche == "spot" else "https://fapi.binance.com/fapi/v1/depth"
                d = get_json(url, {"symbol": sym, "limit": 1000}, essais=2)
                bids, asks = d["bids"], d["asks"]
            else:
                cat = "spot" if marche == "spot" else "linear"
                d = get_json("https://api.bybit.com/v5/market/orderbook",
                             {"category": cat, "symbol": sym, "limit": 200 if marche == "spot" else 500}, essais=2)
                bids, asks = d["result"]["b"], d["result"]["a"]
            bids = [(float(a), float(b)) for a, b in bids]
            asks = [(float(a), float(b)) for a, b in asks]
            mid = (bids[0][0] + asks[0][0]) / 2.0
            for taille in tailles:
                for sens, livre in (("achat", asks), ("vente", bids)):
                    reste, cout, qte = taille, 0.0, 0.0
                    for prix, q in livre:
                        val = min(reste, prix * q)
                        cout += val
                        qte += val / prix
                        reste -= val
                        if reste <= 0:
                            break
                    moy = cout / qte if qte > 0 else float("nan")
                    res.append({"horodatage_utc": horo, "plateforme": plateforme, "paire": base, "marche": marche,
                                "taille_usd": taille, "sens": sens, "mid": mid,
                                "glissement_pct": abs(moy / mid - 1.0) * 100.0,
                                "carnet_epuise": reste > 0,
                                "hypothese_pct": 0.02 if base in MAJEURS else 0.05})
        except Exception as e:  # lacune déclarée
            res.append({"horodatage_utc": horo, "plateforme": plateforme, "paire": base, "marche": marche,
                        "erreur": str(e)})
        time.sleep(0.2)
    return res


# ---------------------------------------------------------------- contrôles

def controles_biais(x: pd.DataFrame, base: str, plateforme: str, p: Params) -> dict:
    res = {}
    # 1. Synthétique : un pic isolé ne doit pas être encaissé par l'entrée qu'il déclenche.
    n = 40
    ts = pd.date_range("2024-01-01", periods=n, freq="8h")
    syn = pd.DataFrame({"ts": ts, "taux": 0.0, "intervalle_h": 8.0, "o_s": 100.0, "o_p": 100.0, "hi_apres": 100.0})
    k = 20
    syn.loc[k, "taux"] = 0.01
    syn["ann"] = syn.taux * 100.0 * HEURES_AN / syn.intervalle_h
    q = replace(p, fenetre_h=8, mult_couts=0.0)
    df, tr = simuler(syn, q, base, plateforme, ts[0], ts[-1])
    res["synthetique_entree_au_pic"] = bool(tr and pd.Timestamp(tr[0]["entree"]) == ts[k])
    res["synthetique_pic_non_encaisse"] = bool(abs(df.fund.sum()) < 1e-12)
    # 2. Le taux suivant, lui, est encaissé.
    syn2 = syn.copy()
    syn2.loc[k + 1, "taux"] = 0.002
    syn2["ann"] = syn2.taux * 100.0 * HEURES_AN / syn2.intervalle_h
    df2, _ = simuler(syn2, q, base, plateforme, ts[0], ts[-1])
    res["synthetique_taux_suivant_encaisse"] = bool(df2.fund.sum() > 0)
    # 3. Données réelles : modifier le futur ne change rien au passé.
    valides = np.flatnonzero(x[["o_s", "o_p"]].notna().all(axis=1).values)
    debut, fin = x.ts.iloc[valides[0]], x.ts.iloc[-1]
    ref, _ = simuler(x, p, base, plateforme, debut, fin, forcer_cloture=False)
    alea = np.random.default_rng(20261031)
    ecarts = []
    for coupe in np.linspace(valides[len(valides) // 4], len(x) - 10, 5).astype(int):
        y = x.copy()
        apres = y.index > coupe
        y.loc[apres, "taux"] = alea.normal(0, 0.005, apres.sum())
        y.loc[apres, "ann"] = y.loc[apres, "taux"] * 100.0 * HEURES_AN / y.loc[apres, "intervalle_h"]
        y.loc[apres, ["o_s", "o_p", "hi_apres"]] *= 3.0
        z, _ = simuler(y, p, base, plateforme, debut, fin, forcer_cloture=False)
        tc = x.ts.iloc[coupe]
        ecarts.append(float((ref.capital[ref.index <= tc] - z.capital[z.index <= tc]).abs().max()))
    res["reel_ecart_max_avant_coupe"] = max(ecarts)
    res["reel_futur_sans_effet"] = max(ecarts) == 0.0
    res["tout_passe"] = all(v for k_, v in res.items() if isinstance(v, bool))
    return res


# ---------------------------------------------------------------- programme

def fmt_table(df: pd.DataFrame, colonnes: list[str]) -> str:
    return df[colonnes].to_string(index=False, float_format=lambda v: f"{v:,.2f}")


def executer_essai(eid: str, nom: str, p: Params, donnees: dict, debuts: dict, fin: str,
                   taux: float, fred) -> dict:
    """Simule toutes les paires de chaque plateforme. Rend séries, trades et résultats."""
    sortie = {"id": eid, "nom": nom, "params": asdict(p), "series": {}, "trades": []}
    for pf, paires in donnees.items():
        series = {}
        for base, x in paires.items():
            df, tr = simuler(x, p, base, pf, debuts[pf], fin)
            if len(df) == 0:
                continue
            series[base] = df
            for t in tr:
                sortie["trades"].append({"essai": eid, "plateforme": pf, "paire": base, **t})
        if series:
            sortie["series"][pf] = {"paires": series, "panier": panier(series)}
    return sortie


def resultats_essai(ess: dict, fin_eff: pd.Timestamp, taux: float, fred, seulement=None) -> list[dict]:
    lignes = []
    for pf, bloc in ess["series"].items():
        cibles = {"PANIER": (bloc["panier"], float(len(bloc["paires"])))}
        cibles.update({b: (s, 1.0) for b, s in bloc["paires"].items()})
        for nom, (df, cap) in cibles.items():
            for lib, a, b in fenetres(fin_eff):
                if seulement and lib not in seulement:
                    continue
                st = stats(df, a, b, cap, taux, fred)
                if st:
                    lignes.append({"essai": ess["id"], "variante": ess["nom"], "plateforme": pf, "paire": nom,
                                   "periode": lib, **st})
    return lignes


def financement_brut(plateformes, paires, dossier: Path, taux: float, sortie: Path) -> pd.DataFrame:
    """Description du marché, sans règle ni coût : ce n'est pas un essai du registre."""
    lignes = []
    for pf in plateformes:
        for base in paires:
            x, _ = preparer(charger_paire(pf, base, 0, 0, dossier, False, {}))
            x = x.dropna(subset=["taux"]).set_index("ts")
            fin = x.index[-1]
            per = [(str(an), pd.Timestamp(f"{an}-01-01"), pd.Timestamp(f"{an}-12-31 23:59:59"))
                   for an in range(2021, fin.year + 1)]
            per += [("12_derniers_mois", fin - pd.Timedelta(days=365), fin),
                    ("90_derniers_jours", fin - pd.Timedelta(days=90), fin)]
            for lib, a, b in per:
                s = x[(x.index > a) & (x.index <= b)]
                if len(s) < 2:
                    continue
                moy = 100.0 * s.taux.sum() / s.intervalle_h.sum() * HEURES_AN
                bornes = bornes_marche(s, pf, base, taux)
                lignes.append({"plateforme": pf, "paire": base, "periode": lib, "premier_utc": str(s.index[0]),
                               "dernier_utc": str(s.index[-1]), "reglements": len(s),
                               "financement_moyen_notionnel_pct": moy,
                               "part_taux_negatifs_pct": 100.0 * (s.taux < 0).mean(),
                               "brut_sur_capital_levier1_pct": moy / 2.0,
                               "ecart_au_taux_court_avant_couts_pct": moy / 2.0 - taux, **bornes})
    df = pd.DataFrame(lignes)
    df.to_csv(sortie, index=False, float_format="%.4f")
    return df


def meilleur_chemin(gains: np.ndarray, cout_aller_retour: float) -> float:
    """Meilleur cumul possible en connaissant l'avenir : à chaque règlement, en position ou non.

    La moitié du coût s'applique à l'entrée, l'autre à la sortie. Sans composition.
    """
    hors, dedans = 0.0, -math.inf
    demi = cout_aller_retour / 2.0
    for g in gains:
        hors, dedans = max(hors, dedans - demi), max(dedans, hors - demi) + g
    return max(hors, dedans - demi)


def bornes_marche(s: pd.DataFrame, plateforme: str, base: str, taux: float) -> dict:
    """Bornes valables pour toute règle de signal, y compris sélective. Ce ne sont pas des règles testées.

    Capital hors position à 0 % : la meilleure règle encaisse tous les taux positifs et évite
    tous les négatifs, d'où la somme des taux positifs.
    Capital hors position rémunéré au taux court : la position ne compte que là où elle bat ce taux,
    l'excédent maximal est positif par construction. La marge reste sans rendement, la base est ignorée.
    """
    ans = s.intervalle_h.sum() / HEURES_AN
    pos = 100.0 * s.taux.clip(lower=0).sum() / ans
    g_ = (PARAMS_GLISS[base in MAJEURS]) / 100.0
    aller_retour = 2.0 * (FRAIS[plateforme]["spot"] + FRAIS[plateforme]["perp"]) / 100.0 + 4.0 * g_
    res = {"somme_taux_positifs_notionnel_pct": pos}
    for L, nom in ((1.0, "levier1"), (2.0, "levier2")):
        part = 1.0 / (1.0 + 1.0 / L)
        gains = s.taux.values * part - taux / 100.0 * s.intervalle_h.values / HEURES_AN
        utile = gains > 0
        res[f"borne_capital_{nom}_oisif_0_pct"] = pos * part
        res[f"part_reglements_utiles_{nom}_pct"] = 100.0 * utile.mean()
        res[f"episodes_utiles_{nom}"] = int((utile & ~np.r_[False, utile[:-1]]).sum())
        res[f"exces_prescience_{nom}_oisif_remunere_sans_couts_pct"] = 100.0 * gains[utile].sum() / ans
        res[f"exces_prescience_{nom}_oisif_remunere_net_couts_pct"] = 100.0 * meilleur_chemin(gains, aller_retour * part) / ans
    return res


def stress_adl(plateformes, paires, debut, dossier: Path, sortie: Path, manifeste: dict, rafraichir: bool) -> pd.DataFrame:
    """Pires baisses spot sur 4 h : calées sur les bougies 4 h, puis glissantes sur des bougies de 15 min.

    Sans simulation. Le bas d'une bougie est un dernier prix, une mèche, pas un prix d'exécution.
    La fenêtre glissante part de chaque ouverture de 15 min et couvre les 16 bougies suivantes.
    """
    part = 1.0 / (1.0 + 1.0 / Params().levier)
    k = 16
    lignes = []
    for pf in plateformes:
        f_boug = binance_bougies if pf == "binance" else bybit_bougies
        bruts = {b: charger_paire(pf, b, 0, 0, dossier, False, {}) for b in paires}
        debut_pf = max(pd.Timestamp(debut), *[premier_valide(preparer(v)[0]) for v in bruts.values()])
        for base in paires:
            r4 = bruts[base]["spot"]
            r4 = r4.set_index(pd.to_datetime(r4.t, unit="ms")).sort_index()
            r4 = r4[r4.index >= debut_pf]
            debut_ms = int(debut_pf.timestamp() * 1000)
            fin_ms = int(r4.t.iloc[-1]) + H4_MS - 1
            brut15 = en_cache(dossier / f"{pf}_{base}USDT_spot15m.csv.gz",
                              lambda: f_boug(f"{base}USDT", "spot", debut_ms, fin_ms, "15m"), rafraichir, manifeste)
            d = brut15.set_index(pd.to_datetime(brut15.t, unit="ms")).sort_index()
            d = d[(d.index >= debut_pf) & (d.t <= fin_ms)]
            grille = pd.date_range(d.index[0], d.index[-1], freq="15min")
            manque = len(grille) - len(d)
            d = d.reindex(grille)

            # Recoupement : les bas de 15 min doivent retrouver le bas de chaque bougie 4 h.
            bas15 = d.l.groupby(d.index.floor("4h")).min()
            communs = r4.iloc[:-1].index.intersection(bas15.index)
            ecart_bas = float(((bas15[communs] / r4.l[communs] - 1.0).abs() * 100.0).max())
            ouv15 = d.o.reindex(communs)
            ecart_ouv = float(((ouv15 / r4.o[communs] - 1.0).abs() * 100.0).max())

            co, lo = r4.c / r4.o - 1.0, r4.l / r4.o - 1.0
            gl_bas = d.l.rolling(k, min_periods=1).min().shift(-(k - 1)) / d.o - 1.0
            gl_fin = d.c.shift(-(k - 1)) / d.o - 1.0
            ligne = {"plateforme": pf, "paire": base, "debut": str(d.index[0]), "fin": str(d.index[-1]),
                     "bougies_15m": int(d.o.notna().sum()), "bougies_15m_manquantes": manque,
                     "recoupement_bas_ecart_max_pct": ecart_bas, "recoupement_ouverture_ecart_max_pct": ecart_ouv}
            for nom, serie in (("cloture_sur_ouverture_4h_calee", co), ("bas_sur_ouverture_4h_calee", lo),
                               ("glissant_fin_de_fenetre_4h", gl_fin), ("glissant_bas_4h", gl_bas)):
                ligne[f"{nom}_pct"] = 100.0 * serie.min()
                ligne[f"{nom}_date"] = str(serie.idxmin())
                ligne[f"{nom}_perte_capital_paire_pct"] = 100.0 * serie.min() * part
            lignes.append(ligne)
    df = pd.DataFrame(lignes)
    df.to_csv(sortie, index=False, float_format="%.4f")
    return df


def controle_financement(horo_ref: str, sorties: Path, dossier: Path, sortie: Path) -> pd.DataFrame:
    """Recalcule le financement des trades sans rééquilibrage, sans passer par `preparer` ni `simuler`.

    Deux recalculs, à partir des fichiers bruts :
    - exact : taux × quantité d'entrée × ouverture de la bougie 4 h du perpétuel à chaque règlement ;
    - notionnel fixe : taux × notionnel d'entrée, sans suivre le prix. L'écart mesure alors l'effet du prix.
    Les trades rééquilibrés sont exclus, leur quantité change en cours de route.
    Le CSV des trades est arrondi à 6 décimales, soit environ 0,01 pb de notionnel.
    """
    tr = pd.read_csv(sorties / f"{horo_ref}_apr_net_trades.csv", parse_dates=["entree", "sortie"])
    lignes = []
    for (pf, base), v in tr.groupby(["plateforme", "paire"], sort=False):
        f = pd.read_csv(dossier / f"{pf}_{base}USDT_financement.csv.gz")
        f["ts"] = pd.to_datetime(f.t, unit="ms").dt.round("min")
        f = f.drop_duplicates("ts").sort_values("ts")
        ouv = {}
        for marche in ("spot", "perp"):
            b = pd.read_csv(dossier / f"{pf}_{base}USDT_{marche}4h.csv.gz")
            ouv[marche] = pd.Series(b.o.values, index=pd.to_datetime(b.t, unit="ms"))
        sans = v[v.reequilibrages == 0]
        exact, fixe = [], []
        for t in sans.itertuples():
            n = t.capital_entree * Params().levier / (Params().levier + 1.0)
            q = n / ouv["spot"][t.entree.floor("4h")]
            w = f[(f.ts > t.entree) & (f.ts <= t.sortie)]
            prix = ouv["perp"].reindex(w.ts.dt.floor("4h")).values
            exact.append(((w.taux.values * q * prix).sum() - t.financement) / n * 1e4)
            fixe.append(((w.taux.values * n).sum() - t.financement) / n * 1e4)
        exact, fixe = np.abs(exact), np.abs(fixe)
        lignes.append({"plateforme": pf, "paire": base, "trades": len(v), "trades_sans_reequilibrage": len(sans),
                       "exact_ecart_moyen_pb": exact.mean(), "exact_ecart_max_pb": exact.max(),
                       "notionnel_fixe_ecart_moyen_pb": fixe.mean(), "notionnel_fixe_ecart_max_pb": fixe.max()})
    df = pd.DataFrame(lignes)
    df.to_csv(sortie, index=False, float_format="%.6f")
    return df


def ecrire_manifeste(chemin: Path, horo: str, mode: str, reference: str, donnees: dict | None = None) -> None:
    chemin.write_text(json.dumps({
        "horodatage_utc": horo, "mode": mode, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "execution_de_reference": reference, "donnees": donnees or {},
        "note": "Pas un essai du registre : aucune règle testée, aucun paramètre modifié.",
    }, ensure_ascii=False, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    d = Params()
    ap.add_argument("--plan", action="store_true", help="exécute le registre E01 à E12")
    ap.add_argument("--financement-brut", action="store_true",
                    help="décrit le financement du marché depuis le cache, sans règle ni coût, sans simulation")
    ap.add_argument("--stress-adl", action="store_true",
                    help="pires baisses spot sur 4 h, calées et glissantes sur 15 min, sans simulation")
    ap.add_argument("--controle-financement", action="store_true",
                    help="recalcule le financement des trades de --reference depuis les fichiers bruts")
    ap.add_argument("--reference", default=EXECUTION_REFERENCE, help="horodatage de l'exécution contrôlée")
    ap.add_argument("--plateformes", nargs="+", default=["binance", "bybit"], choices=sorted(FRAIS))
    ap.add_argument("--paires", nargs="+", default=["BTC", "ETH", "XRP", "BNB", "ADA", "LINK"])
    ap.add_argument("--debut", default=DEV[0])
    ap.add_argument("--fin", default=HE[1])
    ap.add_argument("--seuil-entree", type=float, default=d.seuil_entree, help="%%/an")
    ap.add_argument("--seuil-sortie", type=float, default=d.seuil_sortie, help="%%/an")
    ap.add_argument("--fenetre-h", type=int, default=d.fenetre_h)
    ap.add_argument("--levier", type=float, default=d.levier)
    ap.add_argument("--reequilibrage", type=float, default=d.reequilibrage, help="%% d'écart de prix")
    ap.add_argument("--mult-couts", type=float, default=d.mult_couts)
    ap.add_argument("--glissement-majeurs", type=float, default=d.gliss_majeurs, help="%% par jambe et par côté")
    ap.add_argument("--glissement-alts", type=float, default=d.gliss_alts)
    ap.add_argument("--marge-maintenance", type=float, default=d.marge_maintenance, help="%%")
    ap.add_argument("--taux-court", type=float, default=3.875, help="%%/an, milieu Fed 3,75-4 de la note de régime")
    ap.add_argument("--tailles-carnet", type=float, nargs="+", default=[10000.0, 100000.0])
    ap.add_argument("--sans-carnet", action="store_true")
    ap.add_argument("--rafraichir", action="store_true", help="retélécharge au lieu d'utiliser le cache")
    ap.add_argument("--donnees", type=Path, default=ICI / "donnees")
    ap.add_argument("--sorties", type=Path, default=ICI / "resultats")
    a = ap.parse_args()
    a.donnees.mkdir(parents=True, exist_ok=True)
    a.sorties.mkdir(parents=True, exist_ok=True)
    horo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pfx = a.sorties / f"{horo}_apr_net"
    journal = io.StringIO()

    if a.financement_brut:
        sortie = Path(str(pfx) + "_financement_brut.csv")
        v = financement_brut(a.plateformes, a.paires, a.donnees, a.taux_court, sortie)
        print(f"Description du marché, sans règle ni coût, pas un essai. Source : cache, voir le manifeste du plan. {horo} UTC")
        print("Moyenne du financement sur le notionnel, %/an. Un portage à levier 1 n'en touche que la moitié sur le capital.")
        tab = v.pivot(index=["plateforme", "paire"], columns="periode", values="financement_moyen_notionnel_pct")
        print(tab.to_string(float_format=lambda x: f"{x:.2f}"))
        print("\nPart des taux négatifs sur 12 mois et 90 jours, %")
        tab2 = v[v.periode.isin(["12_derniers_mois", "90_derniers_jours"])].pivot(
            index=["plateforme", "paire"], columns="periode", values="part_taux_negatifs_pct")
        print(tab2.to_string(float_format=lambda x: f"{x:.1f}"))
        print("\nBornes sur 12 mois, %/an. Ce ne sont pas des règles testées.")
        print(v[v.periode == "12_derniers_mois"].drop(columns=["periode", "premier_utc", "dernier_utc"]).T.to_string(
            float_format=lambda x: f"{x:.2f}"))
        ecrire_manifeste(Path(str(pfx) + "_financement_brut_manifeste.json"), horo, "financement_brut", EXECUTION_REFERENCE)
        print(f"\nSortie : {sortie}")
        return 0

    if a.stress_adl:
        sortie = Path(str(pfx) + "_stress_adl.csv")
        mf: dict = {}
        v = stress_adl(a.plateformes, a.paires, a.debut, a.donnees, sortie, mf, a.rafraichir)
        print(f"Pires baisses spot sur 4 h, sans simulation, pas un essai. {horo} UTC")
        print(v.T.to_string(float_format=lambda x: f"{x:.2f}"))
        ecrire_manifeste(Path(str(pfx) + "_stress_adl_manifeste.json"), horo, "stress_adl", EXECUTION_REFERENCE, mf)
        print(f"\nSortie : {sortie}")
        return 0

    if a.controle_financement:
        sortie = Path(str(pfx) + "_controle_financement.csv")
        v = controle_financement(a.reference, a.sorties, a.donnees, sortie)
        print(f"Recalcul séparé du financement, exécution {a.reference}, écarts en pb du notionnel. {horo} UTC")
        print(v.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        ecrire_manifeste(Path(str(pfx) + "_controle_financement_manifeste.json"), horo, "controle_financement", a.reference)
        print(f"\nSortie : {sortie}")
        return 0

    def dire(*m):
        t = " ".join(str(x) for x in m)
        print(t, flush=True)
        journal.write(t + "\n")

    base_p = Params(a.seuil_entree, a.seuil_sortie, a.fenetre_h, a.levier, a.reequilibrage, a.mult_couts,
                    a.glissement_majeurs, a.glissement_alts, a.marge_maintenance)
    if a.plan and base_p != Params():
        ap.error("--plan exige les paramètres figés de la fiche")
    dire(f"STRAT-20261031-02 apr_net.py, exécution {horo} UTC, mode {'PLAN E01-E12' if a.plan else 'LIBRE'}")
    dire("L'APR historique n'est pas un rendement attendu. Aucun sinistre de plateforme n'y figure.")

    now_ms = int(time.time() * 1000)
    debut_ms = int(pd.Timestamp(a.debut).timestamp() * 1000) - 7 * 86400 * 1000
    fin_ms = min(int(pd.Timestamp(a.fin).timestamp() * 1000), now_ms)
    manifeste, lacunes, infos = {}, [], {}
    donnees: dict[str, dict[str, pd.DataFrame]] = {}
    bruts: dict[str, dict[str, dict]] = {}
    for pf in a.plateformes:
        donnees[pf] = {}
        bruts[pf] = {}
        for base in a.paires:
            try:
                brut = charger_paire(pf, base, debut_ms, fin_ms, a.donnees, a.rafraichir, manifeste)
                if brut["fund"].empty or brut["spot"].empty or brut["perp"].empty:
                    raise RuntimeError("série vide")
                x, inf = preparer(brut)
                donnees[pf][base] = x
                bruts[pf][base] = brut
                infos[f"{pf}_{base}"] = {**inf, "premier_valide": str(premier_valide(x))}
                dire(f"  données {pf} {base} : {inf['reglements']} règlements, début valide {premier_valide(x)}, "
                     f"dernier {x.ts.iloc[-1]}, trous {inf['trous_financement']}, sans prix {inf['reglements_sans_prix']}")
            except Exception as e:  # lacune déclarée, la paire est retirée
                lacunes.append(f"{pf} {base} : {e}")
                dire(f"  LACUNE {pf} {base} : {e}")
    fred = charger_fred(a.donnees, a.rafraichir, manifeste)
    if fred is None:
        lacunes.append("FRED DFF indisponible : contrôle secondaire absent")

    debuts = {pf: max(pd.Timestamp(a.debut), *[premier_valide(x) for x in p.values()])
              for pf, p in donnees.items() if p}
    for pf, t in debuts.items():
        dire(f"  début commun du panier {pf} : {t}")

    # Contrôles avant tout résultat.
    ctrl = {}
    for pf, paires in donnees.items():
        for base in ("BTC", "ADA"):
            if base in paires:
                ctrl[f"{pf}_{base}"] = controles_biais(paires[base], base, pf, base_p)
    ok_ctrl = all(c["tout_passe"] for c in ctrl.values())
    dire(f"Contrôle du biais d'anticipation : {'réussi' if ok_ctrl else 'ÉCHEC'} {json.dumps(ctrl, ensure_ascii=False)}")
    if not ok_ctrl:
        dire("Arrêt : biais détecté, aucun résultat publié.")
        (Path(str(pfx) + "_journal.txt")).write_text(journal.getvalue())
        return 2

    # Essais.
    if a.plan:
        b = Params()
        tous = {
            "E01": ("base", b, HE[1]),
            "E02": ("base couts x2", replace(b, mult_couts=2.0), HE[1]),
            "E03": ("entree 8", replace(b, seuil_entree=8.0), FIN_DEV_VAL),
            "E04": ("entree 12", replace(b, seuil_entree=12.0), FIN_DEV_VAL),
            "E05": ("sortie 2.4", replace(b, seuil_sortie=2.4), FIN_DEV_VAL),
            "E06": ("sortie 3.6", replace(b, seuil_sortie=3.6), FIN_DEV_VAL),
            "E07": ("fenetre 16h", replace(b, fenetre_h=16), FIN_DEV_VAL),
            "E08": ("fenetre 32h", replace(b, fenetre_h=32), FIN_DEV_VAL),
            "E09": ("reequilibrage 20", replace(b, reequilibrage=20.0), FIN_DEV_VAL),
            "E10": ("reequilibrage 30", replace(b, reequilibrage=30.0), FIN_DEV_VAL),
            "E11": ("levier 2", replace(b, levier=2.0), FIN_DEV_VAL),
            "E12": ("temoin toujours en position",
                    replace(b, seuil_entree=-1e9, seuil_sortie=-1e9), FIN_DEV_VAL),
        }
    else:
        tous = {"LIBRE": ("essai libre, à inscrire au registre", base_p, a.fin)}

    essais = {}
    for eid, (nom, p, fin) in tous.items():
        essais[eid] = executer_essai(eid, nom, p, donnees, debuts, fin, a.taux_court, fred)
        dire(f"  essai {eid} ({nom}) simulé, fin {fin}")

    ref_id = "E01" if a.plan else "LIBRE"
    ref = essais[ref_id]
    fin_eff = max(b["panier"].index[-1] for b in ref["series"].values())
    lignes_ref = resultats_essai(ref, fin_eff, a.taux_court, fred)
    res = pd.DataFrame(lignes_ref)
    res.to_csv(str(pfx) + "_resultats.csv", index=False, float_format="%.4f")
    pd.DataFrame(ref["trades"]).to_csv(str(pfx) + "_trades.csv", index=False, float_format="%.6f")

    colonnes = ["periode", "duree_ans", "apr_net_pct", "excedent_pct", "financement_pct", "frais_pct", "glissement_pct", "dont_reequilibrage_pct",
                "pnl_base_pct", "liquidation_pct", "financement_brut_notionnel_pct", "temps_en_position_pct",
                "drawdown_max_pct", "trades_clos", "reequilibrages", "liquidations"]
    if fred is not None:
        colonnes.insert(4, "excedent_fred_pct")
    for pf in ref["series"]:
        dire(f"\n=== {ref_id} {ref['nom']}, panier {pf}, capital égal par paire, % par an du capital total ===")
        dire(fmt_table(res[(res.plateforme == pf) & (res.paire == "PANIER")], colonnes))
        dire(f"\n--- {ref_id}, {pf}, par paire, 12 derniers mois et toute la période ---")
        vue = res[(res.plateforme == pf) & (res.paire != "PANIER") & res.periode.isin(["12_derniers_mois", "toute_la_periode"])]
        dire(fmt_table(vue, ["paire"] + colonnes))

    # Sensibilité, stress et critères (plan seulement).
    criteres, stress = [], []
    if a.plan:
        sens = []
        for eid, ess in essais.items():
            sens += resultats_essai(ess, fin_eff, a.taux_court, fred,
                                    seulement={"developpement", "validation"} if eid not in ("E01", "E02")
                                    else {"developpement", "validation", "hors_echantillon", "toute_la_periode", "12_derniers_mois"})
            # Bloc développement + validation, calculé d'un seul tenant.
            for pf, bloc in ess["series"].items():
                st = stats(bloc["panier"], DEV[0], FIN_DEV_VAL, float(len(bloc["paires"])), a.taux_court, fred)
                sens.append({"essai": eid, "variante": ess["nom"], "plateforme": pf, "paire": "PANIER",
                             "periode": "dev+val", **st})
        sens = pd.DataFrame(sens)
        sens.to_csv(str(pfx) + "_sensibilite.csv", index=False, float_format="%.4f")
        n_essais = len(tous) * len(ref["series"])
        for pf in ref["series"]:
            dire(f"\n=== Sensibilité déclarée, panier {pf}, développement + validation ===")
            v = sens[(sens.plateforme == pf) & (sens.paire == "PANIER") & (sens.periode == "dev+val")]
            dire(fmt_table(v, ["essai", "variante", "apr_net_pct", "excedent_pct", "temps_en_position_pct",
                               "drawdown_max_pct", "trades_clos", "liquidations"]))

            # Critères annoncés, évalués une fois sur le hors échantillon.
            q = lambda e, per: sens[(sens.essai == e) & (sens.plateforme == pf) & (sens.paire == "PANIER") & (sens.periode == per)].iloc[0]
            he, he2, tout = q("E01", "hors_echantillon"), q("E02", "hors_echantillon"), q("E01", "toute_la_periode")
            voisins = [q(e, "dev+val").apr_net_pct for e in ("E03", "E04", "E05", "E06")]
            liq_paires = sum(int(s.liqs.sum()) for s in ref["series"][pf]["paires"].values())
            pan = ref["series"][pf]["panier"]
            mois = (pan.fund + pan.base - pan.fee - pan.slip + pan.liq).groupby(pan.index.to_period("M")).sum()
            net = float(mois.sum())
            part = float(mois.max() / net * 100.0) if net > 0 else float("nan")
            repere = sharpe_repere(n_essais, float(he.duree_ans))
            c = [
                ("1. APR net HE > taux court", he.apr_net_pct, a.taux_court, he.apr_net_pct > a.taux_court),
                ("2. APR net HE couts x2 > taux court", he2.apr_net_pct, a.taux_court, he2.apr_net_pct > a.taux_court),
                ("3. Drawdown total < 10 %", tout.drawdown_max_pct, -10.0, tout.drawdown_max_pct > -10.0),
                ("4. Aucune liquidation, levier 1", liq_paires, 0, liq_paires == 0),
                ("5. Voisins ±20 % au-dessus du taux court, dev+val (pire)", min(voisins), a.taux_court, min(voisins) > a.taux_court),
                ("6. Part du meilleur mois < 50 % du gain net", part, 50.0, net > 0 and part < 50.0),
                ("7a. Trades total >= 100", tout.trades_clos, 100, tout.trades_clos >= 100),
                ("7b. Trades HE >= 30", he.trades_clos, 30, he.trades_clos >= 30),
                ("8. Sharpe HE > repère tests multiples", he.sharpe_exces_taux_fixe, repere, he.sharpe_exces_taux_fixe > repere),
            ]
            dire(f"\n=== Critères annoncés, panier {pf}, {n_essais} séries comptées ===")
            for nom, val, seuil, passe in c:
                dire(f"  {'passe' if passe else 'ÉCHEC'}  {nom} : {val:.2f} (seuil {seuil:.2f})")
                criteres.append({"plateforme": pf, "critere": nom, "valeur": val, "seuil": seuil, "passe": bool(passe)})
            passe_tout = all(x[3] for x in c)
            dire(f"  Espérance en R (validation-edge § 5) : non applicable, à trancher.")
            dire(f"  Critère d'échec annoncé pour {pf} : {'non déclenché' if passe_tout else 'DÉCLENCHÉ'}.")
            criteres.append({"plateforme": pf, "critere": "BILAN", "valeur": float(passe_tout), "seuil": 1.0, "passe": passe_tout})
        pd.DataFrame(criteres).to_csv(str(pfx) + "_criteres.csv", index=False, float_format="%.4f")

        # Stress hors simulation : arithmétique sur chiffres réels.
        dire("\n=== Risques non simulés, mesurés à part (pas des prévisions) ===")
        for pf, paires in donnees.items():
            for base, x in paires.items():
                r4 = bruts[pf][base]["spot"]  # toutes les bougies 4 h, pas seulement celles des règlements
                r4 = r4.set_index(pd.to_datetime(r4.t, unit="ms")).sort_index()
                r4 = r4[r4.index >= debuts[pf]]
                ret = r4.c / r4.o - 1.0  # clôture sur ouverture d'une bougie calée, pas la pire baisse sur 4 h
                bas = r4.l / r4.o - 1.0  # le bas est une mèche, voir --stress-adl pour la fenêtre glissante
                part_notionnel = 1.0 / (1.0 + 1.0 / Params().levier)
                stress.append({"type": "ADL, couverture refaite après 4 h", "plateforme": pf, "paire": base,
                               "pire_cloture_sur_ouverture_4h_calee_pct": 100.0 * ret.min(), "date": str(ret.idxmin()),
                               "perte_capital_paire_pct": 100.0 * ret.min() * part_notionnel,
                               "pire_bas_sur_ouverture_4h_calee_pct": 100.0 * bas.min(), "date_bas": str(bas.idxmin()),
                               "perte_capital_paire_au_bas_pct": 100.0 * bas.min() * part_notionnel})
            d_ = pd.DataFrame([s for s in stress if s["plateforme"] == pf and s["type"].startswith("ADL")])
            dire(f"  {pf}, ADL : pire clôture sur ouverture d'une bougie spot 4 h calée, et pire bas sur ouverture, levier 1 :")
            dire("  " + d_[["paire", "pire_cloture_sur_ouverture_4h_calee_pct", "perte_capital_paire_pct", "date",
                            "pire_bas_sur_ouverture_4h_calee_pct", "perte_capital_paire_au_bas_pct", "date_bas"]].to_string(
                index=False, float_format=lambda v: f"{v:.2f}").replace("\n", "\n  "))
            for per in ("12_derniers_mois", "toute_la_periode"):
                e = res[(res.plateforme == pf) & (res.paire == "PANIER") & (res.periode == per)].iloc[0]
                exc = e.excedent_pct
                for perte in (100.0, 50.0):
                    seuil_p = max(exc, 0.0) / perte * 100.0
                    stress.append({"type": "seuil de sinistre", "plateforme": pf, "periode": per, "perte_si_sinistre_pct": perte,
                                   "excedent_pct": exc, "proba_annuelle_seuil_pct": seuil_p})
                    dire(f"  {pf}, {per} : excédent {exc:.2f} %/an, annulé par {seuil_p:.2f} % de probabilité annuelle "
                         f"d'un sinistre à {perte:.0f} % de perte.")
                for dep in (2.0, 5.0, 10.0):
                    stress.append({"type": "dépeg USDT", "plateforme": pf, "periode": per, "baisse_usdt_pct": dep,
                                   "perte_capital_pct": dep,
                                   "annees_excedent": dep / exc if exc > 0 else float("nan")})
                dire(f"  {pf}, {per} : un USDT à -5 % coûte ≈ 5 % du capital en dollars, soit "
                     + (f"{5.0 / exc:.1f} années d'excédent." if exc > 0 else "sans excédent à opposer."))
        pd.DataFrame(stress).to_csv(str(pfx) + "_stress.csv", index=False, float_format="%.4f")

    # Base réelle à l'entrée et à la sortie.
    tr = pd.DataFrame(ref["trades"])
    if len(tr):
        tr["net"] = tr.capital_sortie - tr.capital_entree
        dire("\n=== Trades de l'essai de référence ===")
        g = tr.groupby(["plateforme", "paire"]).agg(
            trades=("net", "size"), gain_moyen_capital=("net", "mean"), base_entree_pb=("base_entree_pb", "mean"),
            base_sortie_pb=("base_sortie_pb", "mean"), pnl_base_moyen=("pnl_base", "mean"),
            liquidations=("motif", lambda m: int((m == "liquidation").sum()))).reset_index()
        dire(g.to_string(index=False, float_format=lambda v: f"{v:.5f}"))

    # Carnets : relevé du jour, comparé aux hypothèses de glissement.
    if not a.sans_carnet:
        c = []
        for pf in a.plateformes:
            for base in a.paires:
                c += carnet(pf, base, a.tailles_carnet)
        c = pd.DataFrame(c)
        c.to_csv(str(pfx) + "_carnet.csv", index=False, float_format="%.6f")
        if "erreur" in c.columns and c.erreur.notna().any():
            lacunes += [f"carnet {r.plateforme} {r.paire} {r.marche} : {r.erreur}" for r in c[c.erreur.notna()].itertuples()]
        v = c[c.get("glissement_pct").notna()] if "glissement_pct" in c else c
        if len(v):
            dire(f"\n=== Glissement mesuré sur carnet, relevé du jour, {v.horodatage_utc.min()} à {v.horodatage_utc.max()} UTC ===")
            t_ = v.groupby(["plateforme", "paire", "marche", "taille_usd"]).glissement_pct.max().unstack("taille_usd").reset_index()
            t_.columns = [str(x) for x in t_.columns]
            dire(t_.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    meta = {
        "horodatage_utc": horo, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "mode": "plan" if a.plan else "libre", "params_base": asdict(base_p),
        "frais_pct": FRAIS, "taux_court_pct": a.taux_court, "debuts_paniers": {k: str(v) for k, v in debuts.items()},
        "fin_effective": str(fin_eff), "controles_biais": ctrl, "lacunes": lacunes, "infos_series": infos,
        "donnees": manifeste, "essais": {k: {"nom": v[0], "params": asdict(v[1]), "fin": v[2]} for k, v in tous.items()},
        "sources": ["https://fapi.binance.com/fapi/v1/fundingRate", "https://fapi.binance.com/fapi/v1/klines",
                    "https://api.binance.com/api/v3/klines", "https://api.bybit.com/v5/market/funding/history",
                    "https://api.bybit.com/v5/market/kline", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"],
        "avertissement": "L'APR historique n'est pas un rendement attendu.",
    }
    Path(str(pfx) + "_manifeste.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str))
    if lacunes:
        dire("\nLacunes :", "; ".join(lacunes))
    dire(f"\nSorties : {pfx}_*")
    Path(str(pfx) + "_journal.txt").write_text(journal.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())
