#!/usr/bin/env python3
"""Contrôle sans rendement de STRAT-20261109-08 (fiche § 5) et construction du format compact (§ 9).

Pour chaque symbole et chaque mois éligible : téléchargement éphémère des klines 1 minute et des metrics, détection des
cascades candidates au seuil le plus lâche (X 3 %, Y 2 %), conservation des minutes autour des candidats et de leur
placebo (+24 h), effacement des archives brutes. Puis comptage des cascades de base (X 4 %, Y 3 %) par bloc, mois et
symbole, avec une tenue de 4 h supposée pour les doublons et l'occupation (aucune issue de position n'est lue).

Reprise possible : un mois déjà traité (marqueur présent) est sauté.
Usage (serveur) : python3 -B controle_cascades.py --cache ~/cache_binance_vision --compact ~/strat08_compact
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
import detection_cascades as dc  # noqa: E402
import donnees_1m as d1  # noqa: E402
import donnees_binance as db  # noqa: E402

BLOCS = [("developpement", "2021-01-01", "2024-01-01"), ("validation", "2024-01-01", "2025-07-28"),
         ("hors_echantillon", "2025-07-28", "2026-11-01")]
FIN = pd.Timestamp("2026-11-01")
BASE = {"x": 0.04, "y": 0.03, "h": pd.Timedelta(hours=4), "k": 5}
DISQUE_MIN_GO = 0.3


def exclusions() -> set:
    c3 = json.loads((ICI.parent / "STRAT-20261031-03" / "config_strat03.json").read_text())["exclusions"]
    ex = set(f"{x}USDT" for x in c3["stablecoins_et_indexes"] + c3["indices"])
    nc = ICI.parent / "STRAT-20261102-06" / "exclusions_non_coin.json"
    if nc.exists():
        ex |= set(json.loads(nc.read_text())["symboles"])
    return ex


def mois_suivant(m: str) -> str:
    return str(pd.Period(m) + 1)


def traiter_symbole(src, s: str, mois: list[str], el_jour: pd.Series, dossier: Path, journal: dict) -> list[dict]:
    """Flux d'un symbole : mois après mois, avec la queue du mois précédent pour la fenêtre de 15 minutes et le report
    des fenêtres qui débordent sur le mois suivant (chargé au besoin, même s'il n'est pas éligible)."""
    tous, queue_k, queue_oi, reports = [], None, None, []
    a_faire = list(mois)
    vus = set()
    while a_faire:
        m = a_faire.pop(0)
        if m in vus:
            continue
        vus.add(m)
        marque = dossier / s / f"{m}.json"
        if marque.exists() and not reports:
            info = json.loads(marque.read_text())
            tous += info.get("candidats", [])
            queue_k = queue_oi = None
            continue
        if shutil.disk_usage(dossier).free / 1e9 < DISQUE_MIN_GO:
            raise RuntimeError(f"Disque presque plein avant {s} {m} : arrêt propre, relancer après libération.")
        k1, mq_k = d1.charger_1m(src, s, m, FIN)
        oi, mq_oi = d1.charger_oi(src, s, m, FIN) if m in mois else (None, 0)
        journal.setdefault(s, {})[m] = {"jours_1m_introuvables": mq_k, "jours_metrics_introuvables": mq_oi}
        if k1 is None:
            queue_k = queue_oi = None
            continue
        k_det = pd.concat([queue_k, k1]) if queue_k is not None and (k1.index.min() - queue_k.index.max()) <= pd.Timedelta(minutes=1) else k1
        cands = []
        if oi is not None and m in mois:
            o_det = pd.concat([queue_oi, oi]) if queue_oi is not None else oi
            c = dc.candidats(k_det, o_det)
            c = c[(c["t"] >= k1.index.min()) & (c["t"] < k1.index.max() + pd.Timedelta(minutes=2))]
            c = c[[bool(el_jour.get(t.normalize(), False)) for t in c["t"]]]
            cands = [{"symbole": s, "t": str(r.t), "rendement_15m": float(r.rendement_15m), "var_oi_15m": float(r.var_oi_15m),
                      "volume_15m": float(r.volume_15m)} for r in c.itertuples()]
        intervalles = dc.fenetres_a_garder([pd.Timestamp(x["t"]) for x in cands]) + reports
        garder = [(a, b) for a, b in intervalles if a <= k1.index.max() and b >= k1.index.min()]
        reports = [(max(a, k1.index.max() + pd.Timedelta(minutes=1)), b) for a, b in intervalles if b > k1.index.max()]
        comp = d1.compacter(k1, garder)
        (dossier / s).mkdir(parents=True, exist_ok=True)
        if comp:
            np.savez_compressed(dossier / s / f"{m}.npz", **comp)
        if m in mois:
            marque.write_text(json.dumps({"candidats": cands, "minutes_gardees": int(len(comp.get("minute", [])))}))
        tous += cands
        queue_k, queue_oi = k1.tail(20), (oi.tail(5) if oi is not None else None)
        if reports and mois_suivant(m) not in a_faire and mois_suivant(m) not in vus and pd.Period(mois_suivant(m)).start_time < FIN:
            a_faire.insert(0, mois_suivant(m))  # mois chargé seulement pour les fenêtres reportées
    return tous


def occupation_ignoree(ev: pd.DataFrame, k: int, h: pd.Timedelta) -> int:
    """Cascades sans emplacement libre si chaque position durait h (borne haute de l'occupation, sans issue lue)."""
    fins, ignores = [], 0
    for t in ev.sort_values("t")["t"]:
        fins = [f for f in fins if f > t]
        if len(fins) >= k:
            ignores += 1
        else:
            fins.append(t + h)
    return ignores


def rapport(c: pd.DataFrame) -> tuple[str, dict]:
    c = c.copy()
    c["t"] = pd.to_datetime(c["t"])
    base = dc.dedoublonner(dc.filtrer(c, BASE["x"], BASE["y"]), BASE["h"])
    R = {"candidats_lache": int(len(c)), "cascades_base": int(len(base)), "blocs": {}}
    l = ["# Contrôle sans rendement de STRAT-20261109-08", "",
         "Cascades détectées seulement : aucune issue de position lue. Base : X = 4 %, Y = 3 % (intérêt ouvert en contrats), un événement par symbole puis 4 h de pause.", "",
         "| Bloc | Cascades de base | Symboles | Par semaine | Heures avec plus de 5 symboles | Ignorées faute d'emplacement (K = 5, tenue 4 h) | Exigence |",
         "|---|---:|---:|---:|---:|---:|---|"]
    for nom, a, b in BLOCS:
        x = base[(base["t"] >= a) & (base["t"] < b)]
        sem = max((pd.Timestamp(b) - pd.Timestamp(a)).days / 7, 1)
        heures = x.groupby(x["t"].dt.floor("h"))["symbole"].nunique()
        ign = occupation_ignoree(x, BASE["k"], BASE["h"])
        exig = 300 if nom == "developpement" else (100 if nom == "hors_echantillon" else None)
        R["blocs"][nom] = {"cascades": int(len(x)), "symboles": int(x["symbole"].nunique()), "par_semaine": len(x) / sem,
                           "heures_plus_de_5": int((heures > 5).sum()), "ignorees_k": ign, "jouables": int(len(x) - ign),
                           "par_annee": x.groupby(x["t"].dt.year).size().to_dict(),
                           "top_symboles": x["symbole"].value_counts().head(10).to_dict()}
        etat = "—" if exig is None else (f"≥ {exig} jouables : {'oui' if len(x) - ign >= exig else 'NON'}")
        l.append(f"| {nom} | {len(x)} | {x['symbole'].nunique()} | {len(x)/sem:.1f} | {(heures > 5).sum()} | {ign} | {etat} |")
    l += ["", "Par année (base) : " + ", ".join(f"{y} {n}" for y, n in base.groupby(base['t'].dt.year).size().items()) + ".",
          f"Candidats au seuil le plus lâche (X 3 %, Y 2 %, avant pause) : {len(c)}.", "",
          "Le 10 et le 11/10/2025 : " + str(int(((base['t'] >= '2025-10-10') & (base['t'] < '2025-10-12')).sum())) + " cascades de base."]
    return "\n".join(l) + "\n", R


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    ap.add_argument("--compact", default=str(Path.home() / "strat08_compact"))
    ap.add_argument("--max-symboles", type=int, default=0)
    ap.add_argument("--debut-volumes", default="2020-11-01")
    a = ap.parse_args(argv)
    brut = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache).expanduser())
    src = d1.LectureEphemere(brut)
    dossier = Path(a.compact).expanduser()
    dossier.mkdir(parents=True, exist_ok=True)
    syms = [s for s in db.symboles_usdt(brut) if s not in exclusions()]
    jours = db.charger_jours(brut, syms, pd.Timestamp(a.debut_volumes), FIN)
    vol = jours["volume"]
    me = d1.mois_eligibles(vol, debut="2021-01-01", fin=FIN)
    cibles = sorted(me)[: a.max_symboles] if a.max_symboles else sorted(me)
    journal, tous = {}, []
    for i, s in enumerate(cibles, 1):
        el = d1.jours_eligibles(vol, s)
        tous += traiter_symbole(src, s, me[s], el, dossier, journal)
        print(f"[{i}/{len(cibles)}] {s} : {len(me[s])} mois, {len(tous)} candidats cumulés", flush=True)
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ICI / "resultats"
    out.mkdir(exist_ok=True)
    c = pd.DataFrame(tous, columns=["symbole", "t", "rendement_15m", "var_oi_15m", "volume_15m"])
    c.to_csv(out / f"candidats_{h}.csv", index=False)
    md, R = rapport(c) if len(c) else ("Aucun candidat.\n", {})
    R.update({"symboles": len(cibles), "mois_eligibles": int(sum(len(v) for v in me.values())),
              "manques": {s: {m: v for m, v in x.items() if v["jours_1m_introuvables"] or v["jours_metrics_introuvables"]} for s, x in journal.items()}})
    md += f"\nSymboles traités : {len(cibles)} ; mois éligibles : {R['mois_eligibles']}. Compact : `{dossier}`.\n"
    (out / f"controle_cascades_{h}.md").write_text(md)
    (out / f"controle_cascades_{h}.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False))
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
