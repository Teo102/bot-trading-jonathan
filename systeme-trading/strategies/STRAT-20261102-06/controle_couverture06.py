#!/usr/bin/env python3
"""Contrôle sans prix de STRAT-20261102-06 (fiche § 4 et § 3.2) : noms éligibles par semaine, part de semaines vides,
et candidats « faux nouveaux noms » (renommages) à relire avant le gel. Volumes seulement, aucun prix, aucun rendement.
Les trois blocs sont comptés, hors échantillon compris, comme l'audit de l'univers l'a déjà fait (volumes connus).

Usage : python -B controle_couverture06.py --cache ~/cache_binance_vision
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

import run_essai06 as r6

db, m, uc = r6.db, r6.m, r6.uc
sys.path.insert(0, str(r6.S03))
import controle_taille_univers as ctu  # noqa: E402

BLOCS = [("developpement", "2021-01-04", "2024-06-24"), ("validation", "2024-07-01", "2025-07-21"),
         ("hors_echantillon", "2025-08-04", "2026-10-19")]


def mesurer(vol, pc, debut_donnees, p):
    jours = {"volume": vol.rename(columns={"BTCUSDT": "BTC"})}
    jc = m.couper_zombies(jours, {}, None)[0]
    prem = uc.premiers_volumes(jc["volume"])
    lignes = []
    for bloc, a, b in BLOCS:
        for t in pd.date_range(a, b, freq="W-MON"):
            el = uc.eligibles(jc, t, pc, debut_donnees, prem)
            lignes.append({"lundi": t.date(), "bloc": bloc, "eligibles": len(el), "noms": ",".join(s for s, _ in el)})
    return pd.DataFrame(lignes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    a = ap.parse_args(argv)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    c6, c3 = r6.charger_configs()
    pc, p = r6.params_cotation(c6, c3), r6.r3.params_depuis(c3)
    vol = ctu.volumes(source, db.symboles_usdt(source), r6.DEBUT_DONNEES, pd.Timestamp("2026-10-19"))
    df = mesurer(vol, pc, r6.DEBUT_DONNEES, p)
    ren = uc.candidats_renommage(vol, r6.DEBUT_DONNEES)
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(__file__).resolve().parent / "resultats"
    out.mkdir(exist_ok=True)
    df.to_csv(out / f"couverture06_{h}.csv", index=False)
    ren.to_csv(out / f"candidats_renommage_{h}.csv", index=False)
    l = [f"# Contrôle sans prix de STRAT-20261102-06 — {h}", "",
         "Volumes seulement ; aucun prix, aucun rendement. Hors échantillon compté sur les volumes, déjà connus.", "",
         "| Bloc | Semaines | Semaines vides | Part vide | Éligibles moyen | Noms différents |", "|---|---:|---:|---:|---:|---:|"]
    for b, g_ in df.groupby("bloc", sort=False):
        noms = {n for x in g_.noms if x for n in x.split(",")}
        l.append(f"| {b} | {len(g_)} | {(g_.eligibles == 0).sum()} | {(g_.eligibles == 0).mean():.1%} | {g_.eligibles.mean():.2f} | {len(noms)} |")
    dev = df[df.bloc == "developpement"]
    l += ["", f"Règle de la fiche § 4 : {'révision requise' if (dev.eligibles == 0).mean() > 0.40 else 'respectée'} "
          f"({(dev.eligibles == 0).mean():.1%} de semaines vides en développement, seuil 40 %).",
          f"Candidats renommage à relire avant le gel : {len(ren)} paires (`candidats_renommage_{h}.csv`)."]
    (out / f"couverture06_{h}.md").write_text("\n".join(l) + "\n")
    print("\n".join(l))
    return 0


if __name__ == "__main__":
    sys.exit(main())
