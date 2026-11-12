#!/usr/bin/env python3
"""Lanceur des essais de STRAT-20261109-08 (fiche § 6, § 7). Refus stricts :
- tout essai tant que `statut_regles` ne vaut pas « figees » ;
- un essai déjà daté au registre (un essai ne se relance pas) ;
- E13 tant que le constat m1 est ouvert (le format compact ne garde que les baisses) ;
- E15 et E16 tant que les essais E01 à E12 et E14 ne sont pas tous datés **et** que la décision écrite
  `portes_avant_hors_echantillon = "franchies"` n'est pas dans la configuration ; E16 avant E15.
Verrou (m2) : le magasin de minutes refuse toute lecture au-delà de la fin du bloc de l'essai.

Usage : python3 -B run_essai08.py --essai E01 --candidats resultats/candidats_<h>.csv --compact ~/strat08_compact --cache ~/cache_binance_vision
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI.parent / "STRAT-20261102-06"))
import moteur_intraday as mi  # noqa: E402

CONFIG, REGISTRE, SORTIES = ICI / "config_strat08.json", ICI / "REGISTRE_ESSAIS.csv", ICI / "resultats"
FACTEURS = [ICI.parent / "STRAT-20261102-06" / "resultats" / f"DIAG_{e}_facteurs.csv" for e in ("E01", "E02", "E19")]
AVANT_HE = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E14"]


class Refus(RuntimeError):
    pass


def lire_registre(registre: Path) -> dict:
    with registre.open() as f:
        return {r["id_essai"]: r for r in csv.DictReader(f)}


def params(c: dict, essai: str) -> mi.ParamsIntraday:
    b = dict(c["params_base"])
    b.update(c["essais"][essai].get("surcharges", {}))
    return mi.ParamsIntraday(x=b["x"], y=b["y"], s=b["s"], h=pd.Timedelta(hours=b["h_heures"]), d=pd.Timedelta(minutes=b["d_minutes"]),
                             k=int(b["k"]), stops_par_jour=int(b["stops_par_jour"]), frais=b["frais"], gliss_entree=b["gliss_entree"],
                             gliss_sortie=b["gliss_sortie"], gliss_stop=b["gliss_stop"],
                             placebo=pd.Timedelta(hours=b.get("placebo_heures", 0)), sens=int(b.get("sens", 1)))


def controles(essai: str, c: dict, registre: Path) -> None:
    if c.get("statut_regles") != "figees":
        raise Refus("Règles de STRAT-08 non figées (config_strat08.json). Aucun essai lancé.")
    if essai not in c["essais"]:
        raise Refus(f"{essai} inconnu.")
    reg = lire_registre(registre)
    if essai not in reg:
        raise Refus(f"{essai} absent du registre.")
    if reg[essai]["date"].strip():
        raise Refus(f"{essai} déjà lancé le {reg[essai]['date']}. Un essai ne se relance pas.")
    if essai == "E13":
        raise Refus("E13 refusé : constat m1 ouvert (le format compact ne garde que les cascades à la baisse). Décision attendue.")
    if essai in ("E15", "E16"):
        manquants = [e for e in AVANT_HE if not reg[e]["date"].strip()]
        if manquants:
            raise Refus(f"Hors échantillon refusé : essais non lancés {manquants}.")
        if c.get("portes_avant_hors_echantillon") != "franchies":
            raise Refus("Hors échantillon refusé : décision écrite « portes_avant_hors_echantillon = franchies » absente.")
        if essai == "E16" and not reg["E15"]["date"].strip():
            raise Refus("E16 ne se lance qu'après E15.")


def facteurs() -> pd.DataFrame:
    f = pd.concat([pd.read_csv(x, index_col=0, parse_dates=True) for x in FACTEURS if x.exists()])
    f = f[~f.index.duplicated()]
    f["alts_moins_btc"] = f["alts"] - f["btc"]
    return f


def alpha_deux_facteurs(w: pd.Series, f: pd.DataFrame) -> dict:
    import diagnostics_e01_e02 as dg
    d = pd.concat([w.rename("net"), f[["btc", "alts_moins_btc"]]], axis=1, join="inner").dropna()
    if len(d) < 10:
        return {"semaines": len(d), "note": "insuffisant"}
    X = np.column_stack([np.ones(len(d)), d["btc"], d["alts_moins_btc"]])
    b, se, r2, n = dg.newey_west(X, d["net"].to_numpy(float))
    return {"semaines": n, "alpha_hebdo": float(b[0]), "alpha_annualise": float(b[0] * 52), "t_alpha": float(b[0] / se[0]),
            "beta_btc": float(b[1]), "beta_alts_moins_btc": float(b[2]), "r2": float(r2)}


def metriques(pos: pd.DataFrame, w: pd.Series, c: dict, fac: pd.DataFrame) -> dict:
    import run_essai as r3
    b = c["bootstrap"]
    r = w.to_numpy(float)
    sd = r.std(ddof=1) if len(r) > 1 else float("nan")
    cum = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], cum]))[1:] - cum)) if len(r) else 0.0
    net = float(r.sum())
    out = {"positions": int(len(pos)), "semaines": int(len(r)), "semaines_avec_position": int((r != 0).sum()),
           "net_brut100": net, "moyenne_hebdo": float(r.mean()) if len(r) else float("nan"),
           "sharpe_hebdo_annualise": float(r.mean() / sd * np.sqrt(52)) if sd and sd > 0 else float("nan"),
           "ic90": r3.bootstrap_blocs(r, b["bloc_semaines"], b["tirages"], b["graine"], b["niveau"]) if len(r) > 8 else [float("nan")] * 2,
           "drawdown_brut100": dd, "alpha": alpha_deux_facteurs(w, fac)}
    if len(pos):
        p = pos.assign(t_sortie=pd.to_datetime(pos["t_sortie"]))
        out.update({"stops": int((p["statut"] == "stop").sum()), "taux_stop": float((p["statut"] == "stop").mean()),
                    "net_moyen_position": float(p["net"].mean()),
                    "t_moyen_position": float(p["net"].mean() / (p["net"].std(ddof=1) / np.sqrt(len(p)))) if len(p) > 2 else float("nan"),
                    "frais": float(p["frais"].sum()), "financement": float(p["financement"].sum()),
                    "par_annee": {str(k): float(v) for k, v in p.groupby(p["t_sortie"].dt.year)["net"].sum().items()},
                    "part_max_symbole": float(p.groupby("symbole")["net"].sum().max() / net) if net > 0 else None,
                    "part_max_mois": float(p.groupby(p["t_sortie"].dt.to_period("M"))["net"].sum().max() / net) if net > 0 else None,
                    "part_max_jour": float(p.groupby(p["t_sortie"].dt.normalize())["net"].sum().max() / net) if net > 0 else None})
    return out


def executer(essai: str, candidats: pd.DataFrame, compact: Path, c: dict | None = None, registre: Path = REGISTRE,
             sorties: Path = SORTIES, financement: dict | None = None, financement_compte: bool = True) -> dict:
    c = c or json.loads(CONFIG.read_text())
    controles(essai, c, registre)
    p = params(c, essai)
    nom_bloc = c["essais"][essai]["bloc"]
    debut, fin = (pd.Timestamp(x) for x in c["blocs"][nom_bloc])
    ev = candidats.copy()
    ev["t"] = pd.to_datetime(ev["t"])
    ev = ev[(ev["t"] >= debut) & (ev["t"] < fin)]
    magasin = mi.MagasinCompact(compact, fin)
    pos, ecarts = mi.simuler(ev, magasin, p, fin, financement)
    w = mi.semaines(pos, debut, fin - pd.Timedelta(days=1))
    fac = facteurs()
    mt = metriques(pos, w, c, fac)
    mt["ecarts"], mt["financement_compte"] = ecarts, financement_compte
    if nom_bloc == "dev+val":
        mt["sous_blocs"] = {}
        for nb in ("developpement", "validation"):
            a, b = (pd.Timestamp(x) for x in c["blocs"][nb])
            pb = pos[(pd.to_datetime(pos["t_sortie"]) >= a) & (pd.to_datetime(pos["t_sortie"]) < b)] if len(pos) else pos
            mt["sous_blocs"][nb] = metriques(pb, w[(w.index >= a - pd.Timedelta(days=6)) & (w.index < b)], c, fac)
    if nom_bloc == "hors_echantillon" and len(pos):
        ex = pd.to_datetime(c["journees_exclues_robustesse"])
        hors = pos[~pd.to_datetime(pos["t_entree"]).dt.normalize().isin(ex)]
        mt["net_hors_journees_exclues"] = float(hors["net"].sum())
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sorties.mkdir(exist_ok=True)
    pos.to_csv(sorties / f"{essai}_positions.csv", index=False)
    w.rename("net").to_csv(sorties / f"{essai}_semaines.csv")
    meta = {"horodatage": h, "essai": essai, "variante": c["essais"][essai]["variante"], "bloc": nom_bloc, "debut": str(debut), "fin": str(fin),
            "params": {k: str(v) for k, v in p.__dict__.items()}}
    (sorties / f"{essai}_metriques.json").write_text(json.dumps({"meta": meta, "metriques": mt}, ensure_ascii=False, indent=1, default=str))
    al = mt["alpha"]
    md = (f"# {essai} de STRAT-20261109-08 — {meta['variante']}\n\nPassage du {h}. Bloc {nom_bloc} ({debut.date()} au {fin.date()}). "
          f"Résultat de recherche, aucun ordre.\n\n| Mesure | Valeur |\n|---|---:|\n"
          f"| Positions, stops | {mt['positions']}, {mt.get('stops', 0)} |\n| Net, brut 100 % | {mt['net_brut100']:+.2%} |\n"
          f"| Sharpe hebdomadaire annualisé | {mt['sharpe_hebdo_annualise']:.3f} |\n| IC 90 % de la moyenne hebdomadaire | [{mt['ic90'][0]:+.3%} ; {mt['ic90'][1]:+.3%}] |\n"
          f"| Alpha à deux facteurs annualisé (t) | {al.get('alpha_annualise', float('nan')):+.2%} ({al.get('t_alpha', float('nan')):.2f}) |\n"
          f"| Drawdown, brut 100 % | {-mt['drawdown_brut100']:+.2%} |\n| Net moyen par position (t) | {mt.get('net_moyen_position', float('nan')):+.4%} ({mt.get('t_moyen_position', float('nan')):.2f}) |\n"
          f"| Frais, financement | {mt.get('frais', 0):.2%}, {mt.get('financement', 0):.2%} |\n\n"
          f"Événements écartés : {json.dumps(ecarts, ensure_ascii=False)}. Financement compté : {financement_compte}.\n")
    (sorties / f"{essai}_metriques.md").write_text(md)
    reg = lire_registre(registre)
    reg[essai].update({"date": h, "positions": str(mt["positions"]), "net_brut100": f"{mt['net_brut100']:.4f}",
                       "sharpe_hebdo_annualise": f"{mt['sharpe_hebdo_annualise']:.4f}", "ic90_bas": f"{mt['ic90'][0]:.6f}",
                       "ic90_haut": f"{mt['ic90'][1]:.6f}", "dd": f"{mt['drawdown_brut100']:.4f}"})
    with registre.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(next(iter(reg.values())).keys()))
        wr.writeheader(); wr.writerows(reg.values())
    return {"meta": meta, "metriques": mt, "positions": pos, "rapport": md}


def charger_financement(cache: Path, symboles, debut, fin) -> dict:
    import donnees_binance as db
    src = db.VisionHTTP(Path(cache).expanduser())
    return {s: db.charger_symbole(src, s, "financement", debut, fin) for s in symboles}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", required=True)
    ap.add_argument("--candidats", required=True)
    ap.add_argument("--compact", default=str(Path.home() / "strat08_compact"))
    ap.add_argument("--cache", required=True, help="cache data.binance.vision, pour le financement")
    a = ap.parse_args(argv)
    c = json.loads(CONFIG.read_text())
    try:
        controles(a.essai, c, REGISTRE)
        cand = pd.read_csv(a.candidats)
        debut, fin = (pd.Timestamp(x) for x in c["blocs"][c["essais"][a.essai]["bloc"]])
        syms = sorted(set(cand.loc[(pd.to_datetime(cand["t"]) >= debut) & (pd.to_datetime(cand["t"]) < fin), "symbole"]))
        fin_fin = min(fin, pd.Timestamp("2026-11-01"))
        out = executer(a.essai, cand, Path(a.compact).expanduser(), c, financement=charger_financement(a.cache, syms, debut, fin_fin))
    except Refus as e:
        print(f"REFUS : {e}", file=sys.stderr)
        return 2
    print(out["rapport"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
