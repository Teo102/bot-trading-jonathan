#!/usr/bin/env python3
"""Critères du verdict de STRAT-06-bis (FICHE_STRAT-06-BIS.md § 2), calculés sur la série stressée du papier.

- Arrêt anticipé, à tout moment : drawdown de la série stressée quotidienne > 40 % (équivalent brut 100 %).
- Point d'étape à 26 semaines : net cumulé de la série stressée ≤ 0 → rejet.
- Verdict à 52 semaines, toutes requises : Sharpe annualisé des semaines civiles > 0,8 ; alpha à deux facteurs > 0
  (méthode du diagnostic B : BTC et panier des alts anciennes moins BTC, Newey-West 4 retards) ; aucun nom > 25 % et
  aucun mois > 40 % du gain net ; au moins 300 lignes de shorts.
Avant les dates, le script rend un état d'avancement et refuse tout verdict. Aucun ordre.

Usage : python3 -B verdict_bis06.py [--donnees resultats/paper_cohortes/donnees]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import paper_cohortes06 as pc6  # noqa: E402


def drawdown(cumul: pd.Series) -> float:
    if cumul.empty:
        return 0.0
    c = np.concatenate([[0.0], cumul.to_numpy(float)])
    return float((np.maximum.accumulate(c) - c).max())


def etat_verdict(cb: dict, quotidien: pd.DataFrame, semaines: pd.DataFrame, lignes: pd.DataFrame, jour0, h_eval,
                 facteurs: pd.DataFrame | None = None) -> dict:
    v = cb["verdict"]
    serie = v["serie"]
    n_sem = (pd.Timestamp(h_eval) - pd.Timestamp(jour0)).days / 7
    q = quotidien.set_index("heure")[serie].astype(float) if len(quotidien) else pd.Series(dtype=float)
    out = {"semaines_ecoulees": round(n_sem, 2), "cumul": float(q.iloc[-1]) if len(q) else 0.0, "drawdown": drawdown(q)}
    out["arret_anticipe"] = out["drawdown"] > v["drawdown_arret"]
    s = semaines[(semaines["serie"] == serie)].copy() if len(semaines) else semaines
    hebdo = pc6.hebdomadaire(semaines) if len(semaines) else pd.DataFrame()
    r = hebdo[serie].astype(float) if len(hebdo) and serie in hebdo else pd.Series(dtype=float)
    out["semaines_civiles"] = int(len(r))
    out["sharpe"] = float(r.mean() / r.std(ddof=1) * np.sqrt(52)) if len(r) > 2 and r.std(ddof=1) > 0 else float("nan")
    l = lignes[(lignes["serie"] == serie) & (lignes["statut"] != "absent")] if len(lignes) else lignes
    sh = l[l["sens"].astype(float) < 0] if len(l) else l
    out["lignes_shorts"] = int(len(sh))
    gain = float(s["net"].astype(float).sum()) if len(s) else 0.0
    if len(sh) and gain > 0:
        g = (sh["pnl_prix"].astype(float) + sh["financement"].astype(float)).groupby(sh["symbole"]).sum()
        out["part_max_nom"] = float(g.max() / gain)
        mois = pd.to_datetime(s["t_out"].astype(str).str.rstrip("Z")).dt.to_period("M")
        out["part_max_mois"] = float(s["net"].astype(float).groupby(mois).sum().max() / gain)
    else:
        out["part_max_nom"] = out["part_max_mois"] = None
    if facteurs is not None and len(r) >= 10:
        import diagnostics_e01_e02 as dg
        w = hebdo.set_index("semaine")[serie].astype(float)
        d = pd.concat([w.rename("net"), facteurs[["btc", "alts_moins_btc"]]], axis=1, join="inner").dropna()
        if len(d) >= 10:
            X = np.column_stack([np.ones(len(d)), d["btc"], d["alts_moins_btc"]])
            b, se, r2, n = dg.newey_west(X, d["net"].to_numpy(float))
            out["alpha"] = {"semaines": n, "alpha_annualise": float(b[0] * 52), "t": float(b[0] / se[0]), "r2": float(r2)}
    if out["arret_anticipe"]:
        out["decision"] = "rejet (arrêt anticipé : drawdown > 40 %)"
    elif n_sem < v["point_etape_semaines"]:
        out["decision"] = "en cours, aucun verdict avant le point d'étape"
    elif n_sem < v["semaines"]:
        out["decision"] = "rejet au point d'étape" if out["cumul"] <= 0 else "poursuite après le point d'étape, sans changement de règle"
    else:
        ok = (out["sharpe"] > v["sharpe_min"] and (out.get("alpha") or {}).get("alpha_annualise", -1) > v["alpha_min"]
              and out["part_max_nom"] is not None and out["part_max_nom"] <= v["part_max_nom"]
              and out["part_max_mois"] is not None and out["part_max_mois"] <= v["part_max_mois"]
              and out["lignes_shorts"] >= v["lignes_shorts_min"])
        out["decision"] = "verdict favorable" if ok else "rejet au verdict"
    return out


def facteurs_depuis(jours: dict, semaines_lundi) -> pd.DataFrame:
    """Facteurs du diagnostic B, sur les clôtures journalières collectées (univers figé de STRAT-03)."""
    import diagnostics_e01_e02 as dg
    import run_essai as r3
    import run_essai06 as r6
    c6, c3 = r6.charger_configs()
    import moteur_xsmom as m
    jc = m.couper_zombies(jours, {}, None)[0]
    return dg.facteurs(jc, list(semaines_lundi), r3.params_depuis(c3))


def main(argv=None) -> int:
    import collecte_papier06 as cp
    ap = argparse.ArgumentParser()
    ap.add_argument("--donnees", default=str(pc6.SORTIES / "donnees"))
    a = ap.parse_args(argv)
    cb = pc6.charger_config_bis()
    mode = "compte" if cb["statut"] == "figee" else "a_blanc"
    d = pc6.SORTIES / mode
    jour0 = pd.Timestamp(cb["jour_0"] if mode == "compte" else cb["jour_0_a_blanc"])
    lire = lambda n: pd.read_csv(d / n, dtype=str, keep_default_na=False) if (d / n).exists() else pd.DataFrame()
    q, s, l = lire("serie_quotidienne.csv"), lire("semaines_cohortes.csv"), lire("lignes.csv")
    if len(q):
        q["heure"] = pd.to_datetime(q["heure"].str.rstrip("Z"))
    if len(s):
        for c in ("t_in", "t_out", "lundi"):
            s[c] = pd.to_datetime(s[c].str.rstrip("Z"))
        s["net"] = s["net"].astype(float); s["provisoire"] = False; s["cohorte"] = s["cohorte"].astype(int)
    h_eval = q["heure"].max() if len(q) else jour0
    fac = None
    if len(s):
        jours = cp.Collecteur(Path(a.donnees)).charger_jours()
        lundis = sorted(set(pc6.hebdomadaire(s)["semaine"]))
        fac = facteurs_depuis(jours, lundis) if lundis else None
    out = etat_verdict(cb, q, s, l, jour0, h_eval, fac)
    out.update({"mode": mode, "jour_0": str(jour0.date()), "heure_evaluation": pc6.iso(h_eval)})
    print(json.dumps(out, indent=1, ensure_ascii=False, default=float))
    (d / "verdict_etat.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
