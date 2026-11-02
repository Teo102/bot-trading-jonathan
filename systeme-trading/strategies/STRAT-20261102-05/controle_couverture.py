#!/usr/bin/env python3
"""Couverture du financement et de l'intérêt ouvert par semaine (fiche § 4), développement et validation seulement.

Lit les volumes (pour l'univers), le financement et l'intérêt ouvert. **Aucun prix, aucun rendement.** Le hors
échantillon n'est pas lu. Règle de la fiche : si plus de 20 % des noms de l'univers manquent sur plus de 10 % des
semaines, la fiche se révise avant le gel.

Usage : python -B controle_couverture.py --cache ~/cache_binance_vision
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

import run_essai05 as r5  # charge les chemins de STRAT-03

db, m, ctu, dm, se = r5.db, r5.m, r5.ctu, r5.dm, r5.se


def mesurer(vol, financement, oi, lundis, p, ps):
    jours = {"volume": vol.rename(columns={"BTCUSDT": "BTC"})}
    jc = m.couper_zombies(jours, {}, None)[0]
    lignes = []
    for t, bloc in lundis:
        u = m.univers(jc, t, p)
        f = se.taux_journalier(financement, t, u, ps.fenetre_f)
        o = se.variation_oi(oi, t, u, ps.fenetre_o) if len(oi) else pd.Series(dtype=float)
        c = set(f.index) & set(o.index)
        lignes.append({"lundi": t.date(), "bloc": bloc, "univers": len(u), "avec_financement": len(f),
                       "avec_interet_ouvert": len(o), "classables": len(c),
                       "part_manquante": 1 - len(c) / len(u) if u else 1.0})
    return pd.DataFrame(lignes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    a = ap.parse_args(argv)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    c5, c3 = r5.charger_configs()
    p, ps = r5.r3.params_depuis(c3), r5.params_score(c5)
    blocs = [(k, b) for k, b in c5["blocs"].items()]
    lundis = [(t, k) for k, b in blocs for t in pd.date_range(b["premier_lundi"], b["dernier_lundi"], freq="W-MON")]
    fin = db.naif(blocs[-1][1]["fin_donnees_prix"])
    debut = lundis[0][0] - pd.Timedelta(days=p.anciennete + p.fenetre_volume + 10)
    vol = ctu.volumes(source, db.symboles_usdt(source), debut, fin)
    jc = m.couper_zombies({"volume": vol.rename(columns={"BTCUSDT": "BTC"})}, {}, None)[0]
    univ = {t: m.univers(jc, t, p) for t, _ in lundis}
    noms = sorted(set().union(*univ.values()))
    fins = {s: db.charger_symbole(source, s, "financement", lundis[0][0] - pd.Timedelta(days=30), fin) for s in noms}
    financement = pd.DataFrame({s: v for s, v in fins.items() if v is not None}).sort_index()
    q: dict = {}
    oi = dm.charger_oi(source, dm.jours_requis(univ, (ps.fenetre_o,)), fin, journal=q)
    df = mesurer(vol, financement, oi, lundis, p, ps)
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(__file__).resolve().parent / "resultats"
    out.mkdir(exist_ok=True)
    df.to_csv(out / f"couverture_{h}.csv", index=False)
    mauvaises = (df["part_manquante"] > 0.20).mean()
    lignes = [f"# Couverture du signal de STRAT-20261102-05 — {h}", "",
              "Volumes, financement et intérêt ouvert seulement ; aucun prix, aucun rendement ; hors échantillon non lu.", "",
              "| Bloc | Semaines | Univers moyen | Classables moyen | Semaines à plus de 20 % de noms manquants |", "|---|---:|---:|---:|---:|"]
    for b, g in df.groupby("bloc", sort=False):
        lignes.append(f"| {b} | {len(g)} | {g.univers.mean():.1f} | {g.classables.mean():.1f} | {(g.part_manquante > 0.20).sum()} |")
    lignes += ["", f"Intérêt ouvert : {q.get('oi_jours_demandes')} jours demandés, {q.get('oi_jours_introuvables')} introuvables.",
               f"Règle de la fiche § 4 : {'révision requise' if mauvaises > 0.10 else 'respectée'} "
               f"({100 * mauvaises:.1f} % des semaines à plus de 20 % de noms manquants, seuil 10 %)."]
    (out / f"couverture_{h}.md").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
