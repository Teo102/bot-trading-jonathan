#!/usr/bin/env python3
"""Score du journal de calibration Polymarket (JOURNAL_CALIBRATION.csv). Sans réseau, sans ordre.

Usage : python -B score_calibration.py [--journal JOURNAL_CALIBRATION.csv] [--graine 20261101]

Mesures, sur les seules prévisions résolues, non annulées et hors mi-mandat :
- Brier propre contre Brier du milieu de marché, différence et IC 95 % par bootstrap sur les événements ;
- perte logarithmique des deux côtés ;
- table de calibration par tranches de 10 points ;
- gain hypothétique d'un pari de 1 $ au prix taker (ask pour acheter oui, 1 − bid pour acheter non),
  pris seulement quand l'écart propre − milieu dépasse le demi-écart affiché.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
OBJECTIF = 100


def charger(chemin: Path) -> pd.DataFrame:
    df = pd.read_csv(chemin, dtype={"condition_id": str, "evenement": str})
    return df


def retenues(df: pd.DataFrame) -> pd.DataFrame:
    ok = df["issue_resolue"].isin([0, 1, "0", "1"])
    ok &= ~df["annule"].astype(str).str.lower().isin(["oui", "1", "true"])
    ok &= ~df["mi_mandat"].astype(str).str.lower().isin(["oui", "1", "true"])
    r = df[ok].copy()
    r["y"] = r["issue_resolue"].astype(int)
    for c in ("proba_propre", "milieu", "bid", "ask"):
        r[c] = r[c].astype(float)
    return r


def pari(r: pd.DataFrame) -> np.ndarray:
    """Gain par pari de 1 $ de mise, taker, ou 0 si aucun pari."""
    g = np.zeros(len(r))
    demi = (r["ask"] - r["bid"]).to_numpy() / 2
    ecart = (r["proba_propre"] - r["milieu"]).to_numpy()
    y = r["y"].to_numpy()
    ask, bid = r["ask"].to_numpy(), r["bid"].to_numpy()
    achat_oui = ecart > demi
    achat_non = ecart < -demi
    g[achat_oui] = y[achat_oui] / ask[achat_oui] - 1
    g[achat_non] = (1 - y[achat_non]) / (1 - bid[achat_non]) - 1
    return g, achat_oui | achat_non


def bootstrap_evenements(r: pd.DataFrame, valeur, iterations: int, graine: int):
    rng = np.random.default_rng(graine)
    groupes = [g for _, g in r.groupby("evenement")]
    if len(groupes) < 5:
        return [float("nan"), float("nan")]
    tirages = []
    for _ in range(iterations):
        idx = rng.integers(0, len(groupes), len(groupes))
        tirages.append(valeur(pd.concat([groupes[i] for i in idx])))
    return [float(np.quantile(tirages, 0.025)), float(np.quantile(tirages, 0.975))]


def scorer(df: pd.DataFrame, iterations: int = 5000, graine: int = 20261101) -> dict:
    r = retenues(df)
    out = {"prevues": int(len(df)), "resolues_retenues": int(len(r)), "objectif": OBJECTIF,
           "evenements": int(r["evenement"].nunique()) if len(r) else 0}
    if len(r) == 0:
        out["lecture"] = "aucune prévision résolue"
        return out
    eps = 1e-6
    p, q, y = r["proba_propre"].clip(eps, 1 - eps), r["milieu"].clip(eps, 1 - eps), r["y"]
    out["brier_propre"] = float(((p - y) ** 2).mean())
    out["brier_marche"] = float(((q - y) ** 2).mean())
    diff = lambda d: float((((d["proba_propre"] - d["y"]) ** 2) - ((d["milieu"] - d["y"]) ** 2)).mean())
    out["brier_difference"] = diff(r)
    out["brier_difference_ic95"] = bootstrap_evenements(r, diff, iterations, graine)
    out["logloss_propre"] = float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())
    out["logloss_marche"] = float(-(y * np.log(q) + (1 - y) * np.log(1 - q)).mean())
    g, pris = pari(r)
    out["paris_pris"] = int(pris.sum())
    out["gain_moyen_par_dollar"] = float(g[pris].mean()) if pris.any() else float("nan")
    gain = lambda d: (lambda gg, pp: float(gg[pp].mean()) if pp.any() else 0.0)(*pari(d))
    out["gain_moyen_ic95"] = bootstrap_evenements(r, gain, iterations, graine) if pris.any() else [float("nan")] * 2
    tranches = pd.cut(r["proba_propre"], np.linspace(0, 1, 11), include_lowest=True)
    t = r.groupby(tranches, observed=True).agg(n=("y", "size"), proba_moyenne=("proba_propre", "mean"),
                                                frequence=("y", "mean"), milieu_moyen=("milieu", "mean"))
    out["calibration"] = [{"tranche": str(k), **{c: (float(v) if c != "n" else int(v)) for c, v in row.items()}}
                          for k, row in t.iterrows()]
    out["lecture"] = ("échantillon insuffisant" if len(r) < OBJECTIF or out["evenements"] < 30
                      else "échantillon atteint, critères du MODE_EMPLOI § 4 applicables")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", default=str(ICI / "JOURNAL_CALIBRATION.csv"))
    ap.add_argument("--graine", type=int, default=20261101)
    a = ap.parse_args(argv)
    print(json.dumps(scorer(charger(Path(a.journal)), graine=a.graine), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
