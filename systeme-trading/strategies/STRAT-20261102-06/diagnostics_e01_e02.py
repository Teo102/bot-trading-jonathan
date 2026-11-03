#!/usr/bin/env python3
"""Diagnostics a posteriori sur E01 et E02 de STRAT-20261102-06 (03/11/2026). Blocs déjà consommés, déclarés.

A. Profil par tranche d'âge à l'entrée et par rang de semaine de détention (lignes des shorts).
B. Régression à deux facteurs du rendement hebdomadaire net : BTC, et panier des alts anciennes et liquides moins BTC
   (univers figé de STRAT-03 : 30 noms, ancienneté 180 j continue, médiane ≥ 50 M USDT, memecoins exclus). Erreurs
   de Newey-West (4 retards). Rendements du panier sur clôtures journalières (dimanche à dimanche) : décalage d'une
   heure avec les semaines de la stratégie (lundi 01:00), déclaré.
C. Classement des noms vendus par ancienneté au comptant sur Binance (premier mois d'archive spot 1d de
   data.binance.vision ; actif de base pour les contrats « 1000X »). Limite : une cotation au comptant hors Binance
   n'est pas vue.

Aucune donnée postérieure au 2025-07-28T02:00:00Z (verrou de E02). Ne change aucune règle, ne compte pas dans N.
Usage : python -B diagnostics_e01_e02.py --cache ~/cache_binance_vision [--sans-reseau]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import moteur_xsmom as m  # noqa: E402
import run_essai as r3  # noqa: E402
import run_essai06 as r6  # noqa: E402

VERROU = pd.Timestamp("2025-07-28 02:00:00")
TRANCHES = [(7, 13, "7-13 j"), (14, 27, "14-27 j"), (28, 60, "28-60 j")]
LISTE_S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/{s}/1d/"


def tableau(df: pd.DataFrame) -> str:
    """Tableau Markdown sans dépendance (tabulate peut manquer sur le serveur)."""
    def f(v):
        return f"{v:.4f}" if isinstance(v, (float, np.floating)) else str(v)
    lignes = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lignes += ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lignes)


def lignes_shorts(lig: pd.DataFrame) -> pd.DataFrame:
    x = lig[(lig["statut"] != "absent") & (lig["symbole"] != "BTC")].copy()
    x["lundi"] = pd.to_datetime(x["lundi"])
    x["g"] = x["pnl_prix"] + x["financement"]
    return x


def rang_de_detention(x: pd.DataFrame) -> pd.Series:
    """1 pour la première semaine d'une série de semaines consécutives du même nom, 2 pour la suivante, etc."""
    out = pd.Series(0, index=x.index)
    for _, g in x.sort_values("lundi").groupby("symbole"):
        rang, prec = 0, None
        for i, t in g["lundi"].items():
            rang = rang + 1 if prec is not None and (t - prec).days == 7 else 1
            out[i], prec = rang, t
    return out


def profil_age(lig: pd.DataFrame, cotation: dict) -> pd.DataFrame:
    x = lignes_shorts(lig)
    x["age"] = [(t - cotation[s]).days if s in cotation else np.nan for s, t in zip(x["symbole"], x["lundi"])]
    x["tranche"] = None
    for a, b, nom in TRANCHES:
        x.loc[(x["age"] >= a) & (x["age"] <= b), "tranche"] = nom
    x["rang"] = rang_de_detention(x).clip(upper=4).map({1: "1re", 2: "2e", 3: "3e", 4: "4e et +"})
    tot = x["g"].sum()
    rows = []
    for cle in ("tranche", "rang"):
        for k, g in x.groupby(cle):
            st = g[g["statut"] == "stop"]
            rows.append({"axe": cle, "groupe": k, "lignes": len(g), "gain": g["g"].sum(), "part_gain_shorts": g["g"].sum() / tot if tot else np.nan,
                         "gain_moyen_ligne": g["g"].mean(), "taux_stop": len(st) / len(g), "perte_moyenne_stop": st["g"].mean() if len(st) else np.nan})
    return pd.DataFrame(rows)


def newey_west(X: np.ndarray, y: np.ndarray, retards: int = 4):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    n = len(y)
    xtx_inv = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, retards + 1):
        w = 1 - l / (retards + 1)
        G = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += w * (G + G.T)
    se = np.sqrt(np.diag(xtx_inv @ S @ xtx_inv))
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    return beta, se, r2, n


def facteurs(jc: dict, lundis, p3) -> pd.DataFrame:
    close = jc["close"]
    rows = []
    for t in lundis:
        a, b = t - pd.Timedelta(days=1), t + pd.Timedelta(days=6)
        if a not in close.index or b not in close.index:
            continue
        r = close.loc[b] / close.loc[a] - 1
        u = m.univers(jc, t, p3)
        ra = r.reindex(u).dropna()
        rows.append({"lundi": t, "btc": r.get("BTC", np.nan), "alts": ra.mean() if len(ra) else np.nan, "n_alts": len(ra)})
    f = pd.DataFrame(rows).set_index("lundi")
    f["alts_moins_btc"] = f["alts"] - f["btc"]
    return f


def regression(sem: pd.DataFrame, f: pd.DataFrame) -> dict:
    s = sem.assign(lundi=pd.to_datetime(sem["lundi"])).set_index("lundi")["net"]
    s, f = s[~s.index.duplicated()], f[~f.index.duplicated()]
    d = pd.concat([s, f], axis=1, join="inner").dropna()
    out = {"semaines": len(d)}
    if len(d) < 10:
        return {**out, "note": "moins de 10 semaines exploitables, régression non calculée"}
    for nom, cols in (("un_facteur", ["btc"]), ("deux_facteurs", ["btc", "alts_moins_btc"])):
        X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in cols])
        b, se, r2, n = newey_west(X, d["net"].to_numpy(float))
        out[nom] = {"alpha_hebdo": b[0], "alpha_annualise": b[0] * 52, "t_alpha": b[0] / se[0], "r2": r2,
                    **{f"beta_{c}": b[i + 1] for i, c in enumerate(cols)}, **{f"t_{c}": b[i + 1] / se[i + 1] for i, c in enumerate(cols)}}
    return out


def premier_mois_spot(sym: str, cache: dict, sans_reseau: bool) -> str | None:
    base = m.nom_de_base(sym) + "USDT"
    if base in cache:
        return cache[base]
    if sans_reseau:
        return None
    try:
        with urllib.request.urlopen(LISTE_S3.format(s=base), timeout=30) as rep:
            texte = rep.read().decode()
        mois = sorted(re.findall(rf"{base}-1d-(\d{{4}}-\d{{2}})\.zip<", texte))
        cache[base] = mois[0] if mois else "aucun"
    except Exception as e:  # noqa: BLE001
        cache[base] = f"erreur: {type(e).__name__}"
    return cache[base]


def classer(lig: pd.DataFrame, cotation: dict, cache: dict, sans_reseau: bool) -> pd.DataFrame:
    x = lignes_shorts(lig)
    g = x.groupby("symbole")["g"].sum()
    tot = g.sum()
    rows = []
    for s, gain in g.items():
        L = cotation.get(s)
        pm = premier_mois_spot(s, cache, sans_reseau)
        if pm is None or str(pm).startswith("erreur") or L is None:
            classe = "inconnu"
        elif pm == "aucun":
            classe = "sans comptant Binance"
        else:
            ecart = (L - pd.Timestamp(pm + "-01")).days
            classe = "ancien au comptant (> 180 j avant le perpétuel)" if ecart > 180 else "comptant récent (≤ 180 j)"
        rows.append({"symbole": s, "cotation_perp": None if L is None else str(L.date()), "premier_mois_spot": pm, "classe": classe,
                     "gain": gain, "part": gain / tot if tot else np.nan})
    return pd.DataFrame(rows).sort_values("gain", ascending=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    ap.add_argument("--sans-reseau", action="store_true", help="saute la partie C (listes spot)")
    ap.add_argument("--resultats", default=str(r6.SORTIES))
    ap.add_argument("--debut-donnees", default=str(r6.DEBUT_DONNEES.date()))
    a = ap.parse_args(argv)
    res = Path(a.resultats)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    c6, c3 = r6.charger_configs()
    p3 = r3.params_depuis(c3)
    essais = {e: (pd.read_csv(res / f"{e}_semaines.csv"), pd.read_csv(res / f"{e}_lignes.csv")) for e in ("E01", "E02")}
    debut = pd.Timestamp(a.debut_donnees)
    jours = db.charger_jours(source, db.symboles_usdt(source), debut, VERROU)
    jours = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in jours.items()}
    jc = m.couper_zombies(jours, {}, None)[0]
    vol = jours["volume"].fillna(0) > 0
    seuil = debut + pd.Timedelta(days=2)
    cotation = {s: vol.index[vol[s].to_numpy()][0] for s in vol.columns if vol[s].any()}
    cotation = {s: L for s, L in cotation.items() if L > seuil}
    h = r3.horo().replace(":", "").replace("-", "")
    cache_spot_f = res / "diag_premiers_mois_spot.json"
    cache_spot = json.loads(cache_spot_f.read_text()) if cache_spot_f.exists() else {}
    md = [f"# Diagnostics a posteriori de E01 et E02 — STRAT-20261102-06\n",
          f"Passage {h}. Blocs consommés, aucune donnée après {VERROU} UTC. Aucune règle modifiée, hors N. Résultat de recherche.\n"]
    tous_sem = []
    for e, (sem, lig) in essais.items():
        pa = profil_age(lig, cotation)
        pa.to_csv(res / f"DIAG_{e}_profil_age.csv", index=False)
        md += [f"\n## {e} — A. Profil par âge et par rang de détention\n", tableau(pa), ""]
        lundis = pd.to_datetime(sem["lundi"]).tolist()
        f = facteurs(jc, lundis, p3)
        f.to_csv(res / f"DIAG_{e}_facteurs.csv")
        rg = regression(sem, f)
        md += [f"\n## {e} — B. Régression (Newey-West, 4 retards)\n", "```", json.dumps(rg, indent=1, default=float), "```",
               f"Panier d'alts : {f['n_alts'].mean():.1f} noms en moyenne.\n"]
        tous_sem.append((sem, f))
        if not a.sans_reseau:
            cl = classer(lig, cotation, cache_spot, a.sans_reseau)
            cl.to_csv(res / f"DIAG_{e}_classement_noms.csv", index=False)
            parts = cl.groupby("classe").agg(noms=("symbole", "count"), gain=("gain", "sum"), part=("part", "sum")).reset_index()
            md += [f"\n## {e} — C. Classement des {len(cl)} noms vendus\n", tableau(parts),
                   "\nDix premiers contributeurs :\n", tableau(cl.head(10)), ""]
    sem_t = pd.concat([s for s, _ in tous_sem], ignore_index=True)
    f_t = pd.concat([f for _, f in tous_sem])
    md += ["\n## E01 + E02 — B. Régression sur 238 semaines\n", "```", json.dumps(regression(sem_t, f_t), indent=1, default=float), "```"]
    if cache_spot:
        cache_spot_f.write_text(json.dumps(cache_spot, indent=1, sort_keys=True))
    sortie = res / f"DIAG_E01_E02_{h}.md"
    sortie.write_text("\n".join(md) + "\n")
    print(sortie.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
