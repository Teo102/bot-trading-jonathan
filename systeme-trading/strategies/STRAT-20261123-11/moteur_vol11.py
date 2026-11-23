#!/usr/bin/env python3
"""Moteur de STRAT-20261123-11 (fiche § 3 et § 4) : exposition BTC et ETH pilotée par la volatilité, longue seulement.

Développement 2018-2020 et validation 2021-2023. Le hors échantillon (à partir du 01/01/2024) est verrouillé : aucune
archive de 2024 ou après n'est demandée, et le moteur refuse toute date au-delà.
Usage (serveur) : python -B moteur_vol11.py --cache /root/cache_binance_vision --sorties resultats
"""
import argparse, datetime as dt, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
VERROU = pd.Timestamp("2024-01-01")
ACTIFS = ["BTCUSDT", "ETHUSDT"]
FENETRE, CIBLE, COUT = 30, 0.50, 0.0015
BLOCS = {"developpement": ("2018-01-01", "2021-01-01"), "validation": ("2021-01-01", "2024-01-01")}


def poids_cibles(prix: pd.DataFrame, t, cible=CIBLE, fenetre=FENETRE):
    """Poids de chaque actif dans sa moitié du capital, avec les seules clôtures ≤ t."""
    p = prix[prix.index <= t]
    r = np.log(p).diff().iloc[-fenetre:]
    vol = r.std(ddof=1) * math.sqrt(365)
    return {a: float(min(1.0, cible / vol[a])) if vol[a] > 0 else 0.0 for a in prix.columns}


def simuler(prix: pd.DataFrame, debut, fin, mode="pilote", cout=COUT, parts=None):
    """Valeur quotidienne du portefeuille de debut à fin. mode 'pilote' (fiche) ou 'detention' (référence).
    parts : part du capital par actif (0,5 et 0,5 par défaut)."""
    assert pd.Timestamp(fin) <= VERROU, "hors échantillon verrouillé"
    parts = parts or {a: 1 / len(prix.columns) for a in prix.columns}
    jours = prix.index[(prix.index >= pd.Timestamp(debut)) & (prix.index < pd.Timestamp(fin))]
    valeur, pos, rows, rotation = 1.0, {a: 0.0 for a in prix.columns}, [], 0.0   # pos : montant investi dans chaque actif
    for i, t in enumerate(jours):
        if i > 0:                                                         # dérive des positions avec les prix du jour
            hier = jours[i - 1]
            for a in pos:
                pos[a] *= prix.at[t, a] / prix.at[hier, a]
            valeur = sum(pos.values()) + liquide
        if i == 0 or t.weekday() == 0:                                    # lundi à la clôture de 00:00 UTC
            w = poids_cibles(prix, t) if mode == "pilote" else {a: 1.0 for a in prix.columns}
            cibles = {a: valeur * parts[a] * w[a] for a in prix.columns}
            echange = sum(abs(cibles[a] - pos[a]) for a in prix.columns)
            valeur -= cout * echange
            rotation += echange / max(valeur, 1e-12)
            cibles = {a: valeur * parts[a] * w[a] for a in prix.columns}
            pos = cibles
            liquide = valeur - sum(pos.values())
        rows.append((t, valeur))
    v = pd.Series(dict(rows))
    return v, rotation


def mesures(v: pd.Series):
    r = v.pct_change().dropna()
    ans = len(r) / 365
    sharpe = float(r.mean() / r.std(ddof=1) * math.sqrt(365)) if r.std(ddof=1) > 0 else None
    return {"rendement_annuel_compose": float(v.iloc[-1] / v.iloc[0]) ** (1 / ans) - 1 if ans > 0 else None,
            "volatilite": float(r.std(ddof=1) * math.sqrt(365)), "sharpe": sharpe,
            "baisse_max": float((1 - v / v.cummax()).max()), "rendement_total": float(v.iloc[-1] / v.iloc[0] - 1)}


def bloc(prix, debut, fin):
    sp, rot = simuler(prix, debut, fin, "pilote")
    sr, _ = simuler(prix, debut, fin, "detention")
    sp2, _ = simuler(prix, debut, fin, "pilote", 2 * COUT)
    sr2, _ = simuler(prix, debut, fin, "detention", 2 * COUT)
    mp, mr, mp2, mr2 = mesures(sp), mesures(sr), mesures(sp2), mesures(sr2)
    seul = {}
    for a in prix.columns:
        un = prix[[a]]
        seul[a] = {"pilote": mesures(simuler(un, debut, fin, "pilote")[0]), "detention": mesures(simuler(un, debut, fin, "detention")[0])}
        seul[a]["gain_sharpe"] = seul[a]["pilote"]["sharpe"] - seul[a]["detention"]["sharpe"]
    portes = {"P1_gain_sharpe_au_moins_0_15": mp["sharpe"] - mr["sharpe"] >= 0.15,
              "P2_baisse_max_au_plus_80pct": mp["baisse_max"] <= 0.8 * mr["baisse_max"],
              "P3_rendement_positif": mp["rendement_annuel_compose"] > 0,
              "P4_gain_sharpe_couts_doubles_positif": mp2["sharpe"] - mr2["sharpe"] > 0,
              "P5_chaque_actif_gagne": all(seul[a]["gain_sharpe"] > 0 for a in prix.columns)}
    return {"pilote": mp, "reference": mr, "gain_sharpe": mp["sharpe"] - mr["sharpe"], "rotation_par_an": rot / (len(sp) / 365),
            "couts_doubles": {"pilote": mp2, "reference": mr2}, "par_actif": seul,
            "par_annee": {str(y): {"pilote": float(g.iloc[-1] / g.iloc[0] - 1), "reference": float(sr[sr.index.year == y].iloc[-1] / sr[sr.index.year == y].iloc[0] - 1)}
                          for y, g in sp.groupby(sp.index.year)},
            "portes": {k: bool(x) for k, x in portes.items()}}


def charger(cache):
    import donnees_binance as db
    src = db.VisionHTTP(Path(cache))
    cl = {}
    for a in ACTIFS:
        morceaux = []
        for m in pd.date_range("2017-08-01", VERROU - pd.Timedelta(days=1), freq="MS"):
            z = src.lire(f"data/spot/monthly/klines/{a}/1d/{a}-1d-{m:%Y-%m}.zip")
            if z is not None:
                morceaux.append(db.lire_klines(z)["close"])
        s = pd.concat(morceaux)
        cl[a] = s[~s.index.duplicated()].sort_index()
    prix = pd.DataFrame(cl).dropna()
    return prix[prix.index < VERROU]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--sorties", default=str(ICI / "resultats"))
    a = ap.parse_args()
    prix = charger(a.cache)
    R = {"genere_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "parametres": {"fenetre": FENETRE, "cible": CIBLE, "cout": COUT},
         "donnees": {"premier_jour": str(prix.index.min().date()), "dernier_jour": str(prix.index.max().date()), "jours": len(prix)},
         "blocs": {k: bloc(prix, *v) for k, v in BLOCS.items()}}
    R["verdict"] = "passe" if all(all(b["portes"].values()) for b in R["blocs"].values()) else "rejetee"
    out = Path(a.sorties)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"E01_{R['genere_utc']}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str))
    print(json.dumps({"verdict": R["verdict"], **{k: {"gain_sharpe": round(b["gain_sharpe"], 3), "portes": b["portes"],
                      "pilote": {x: round(y, 3) for x, y in b["pilote"].items()}, "reference": {x: round(y, 3) for x, y in b["reference"].items()}}
                      for k, b in R["blocs"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
