#!/usr/bin/env python3
"""Mesure des glissements de STRAT-20261109-08 sur un échantillon de cascades (constat M5, décision du 12/11/2026).

Méthode (« lecture de la bande ») : pour un ordre au marché de Q USDT lancé à l'instant τ, on cumule les transactions
agressives du même côté (aggTrades) à partir de τ jusqu'à Q, et l'on compare leur prix moyen au premier prix de la
minute (l'ouverture que le moteur utilise). C'est une approximation : notre ordre aurait consommé la liquidité que
d'autres ont consommée.

Trois mesures par cascade :
- entrée : achat de Q à t + 5 min (comparé à l'ouverture de cette minute) ;
- stop, indicateur indirect : vente de Q au début de la minute au plus bas de la fenêtre [t − 15 min, t), en pleine
  cascade (aucune position n'est simulée, aucun rendement lu) ;
- sortie au temps : vente de Q à t + 5 min + 4 h (comparée à l'ouverture de cette minute ; aucun prix d'entrée n'est
  rapproché, aucun rendement lu).

Échantillon : 50 cascades de base (X 4 %, Y 3 %, pause 4 h) tirées avec une graine fixe parmi celles du développement
et de la validation seulement (avant le 28/07/2025) : le hors échantillon reste intact. Fichiers aggTrades de plus de
300 Mo écartés (disque) et remplacés par le tirage suivant ; cela écarte les plus liquides et biaise la mesure vers le
haut, donc dans le sens prudent.

Règle de décision écrite avant la mesure (fiche § 15) : pour le gel, chaque glissement retenu vaut le plus grand de
l'hypothèse de la fiche et du 75e centile mesuré pour Q = 10 000 USDT, arrondi au centième de point supérieur.

Usage (serveur) : python3 -B mesure_glissements.py --candidats resultats/candidats_<h>.csv --cache ~/cache_binance_vision
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI.parent.parent / "recherche" / "audit_donnees"))
import detection_cascades as dc  # noqa: E402

HYPOTHESES = {"entree": 0.0010, "stop": 0.0030, "sortie": 0.0005}
TAILLES = (10_000.0, 50_000.0)
FIN_ECHANTILLON = pd.Timestamp("2025-07-28")
MAX_OCTETS = 300e6
GRAINE = 20261112
D, H = pd.Timedelta(minutes=5), pd.Timedelta(hours=4)


def lire_aggtrades(z: bytes) -> pd.DataFrame:
    """Colonnes : prix, quantité, temps, acheteur_teneur (True : l'acheteur est passif, donc vente agressive)."""
    with zipfile.ZipFile(io.BytesIO(z)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f, header=None, dtype=str)
    df = df[df[0].str.fullmatch(r"\d+", na=False)]
    t = df[5].astype("int64")
    unite = "us" if t.max() > 10**14 else "ms"
    return pd.DataFrame({"prix": df[1].astype(float).values, "qte": df[2].astype(float).values,
                         "t": pd.to_datetime(t, unit=unite).values,
                         "acheteur_teneur": df[6].str.lower().isin(["true", "1"]).values}).sort_values("t", kind="mergesort")


def glissement(tr: pd.DataFrame, tau: pd.Timestamp, q: float, achat: bool) -> dict | None:
    """Prix moyen des transactions agressives du côté voulu depuis τ jusqu'à Q USDT, contre le premier prix ≥ τ."""
    apres = tr[tr["t"] >= tau]
    if apres.empty:
        return None
    ref = float(apres["prix"].iloc[0])
    cote = apres[~apres["acheteur_teneur"]] if achat else apres[apres["acheteur_teneur"]]
    if cote.empty:
        return None
    quote = (cote["prix"] * cote["qte"]).to_numpy()
    cum = np.cumsum(quote)
    i = int(np.searchsorted(cum, q))
    if i >= len(cum):
        return {"reference": ref, "glissement": None, "secondes": None, "rempli": False}
    reste = q - (cum[i - 1] if i else 0.0)
    qte = cote["qte"].to_numpy()[:i].sum() + reste / cote["prix"].iloc[i]
    vwap = q / qte
    g = vwap / ref - 1 if achat else 1 - vwap / ref
    return {"reference": ref, "glissement": float(g), "secondes": float((cote["t"].iloc[i] - tau).total_seconds()), "rempli": True}


def echantillon(cand: pd.DataFrame, n: int, graine: int = GRAINE) -> pd.DataFrame:
    c = cand.copy()
    c["t"] = pd.to_datetime(c["t"])
    base = dc.dedoublonner(dc.filtrer(c[c["t"] < FIN_ECHANTILLON], 0.04, 0.03), H)
    return base.sample(frac=1.0, random_state=graine).reset_index(drop=True)  # ordre de tirage complet, pris dans l'ordre


def plafond_retenu(hyp: float, mesures: list[float]) -> float:
    if not mesures:
        return hyp
    p75 = float(np.percentile(mesures, 75))
    return max(hyp, math.ceil(p75 * 1e4) / 1e4)


def main(argv=None) -> int:
    import audit_donnees_intraday as au
    import donnees_1m as d1
    import donnees_binance as db
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidats", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--n", type=int, default=50)
    a = ap.parse_args(argv)
    brut = db.VisionHTTP(Path(a.cache).expanduser())
    src = d1.LectureEphemere(brut)
    tirage = echantillon(pd.read_csv(a.candidats), a.n)
    lignes, ecartes = [], {"trop_gros": 0, "absent": 0}
    for r in tirage.itertuples(index=False):
        if len(lignes) >= a.n:
            break
        te, tx = r.t + D, r.t + D + H
        jours = sorted({x.normalize() for x in (r.t - pd.Timedelta(minutes=16), te, tx + pd.Timedelta(minutes=5))})
        cles = [f"data/futures/um/daily/aggTrades/{r.symbole}/{r.symbole}-aggTrades-{j.date().isoformat()}.zip" for j in jours]
        tailles = [sum(o["taille"] for o in au.lister(k)[0] if o["cle"] == k) for k in cles]
        if any(t == 0 for t in tailles):
            ecartes["absent"] += 1; continue
        if max(tailles) > MAX_OCTETS or shutil.disk_usage(Path(a.cache).expanduser()).free < sum(tailles) + 2e8:
            ecartes["trop_gros"] += 1; continue
        tr = pd.concat([lire_aggtrades(src.lire(k)) for k in cles]).sort_values("t", kind="mergesort")
        fen = tr[(tr["t"] >= r.t - pd.Timedelta(minutes=15)) & (tr["t"] < r.t)]
        if fen.empty:
            ecartes["absent"] += 1; continue
        minute_bas = fen.loc[fen["prix"].idxmin(), "t"].floor("min")
        ligne = {"symbole": r.symbole, "t": str(r.t), "volume_15m": float(r.volume_15m)}
        for q in TAILLES:
            for nom, tau, achat in (("entree", te, True), ("stop", minute_bas, False), ("sortie", tx, False)):
                g = glissement(tr, tau, q, achat)
                ligne[f"{nom}_{int(q)}"] = None if g is None else g["glissement"]
                ligne[f"{nom}_{int(q)}_s"] = None if g is None else g["secondes"]
        lignes.append(ligne)
        print(f"[{len(lignes)}/{a.n}] {r.symbole} {r.t}", flush=True)
        del tr
    df = pd.DataFrame(lignes)
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ICI / "resultats"
    out.mkdir(exist_ok=True)
    df.to_csv(out / f"glissements_{h}.csv", index=False)
    R = {"cascades": len(df), "ecartes": ecartes, "hypotheses": HYPOTHESES, "mesures": {}, "retenus_pour_le_gel": {}}
    l = [f"# Mesure des glissements de STRAT-08 — {h}", "", f"{len(df)} cascades du développement et de la validation, tirées avec la graine {GRAINE}. "
         f"Écartées : {ecartes}. Aucun rendement lu.", "", "| Mesure | Taille | Médiane | 75e centile | 90e centile | Remplis | Hypothèse de la fiche |", "|---|---:|---:|---:|---:|---:|---:|"]
    for nom in HYPOTHESES:
        for q in TAILLES:
            col = f"{nom}_{int(q)}"
            v = df[col].dropna().to_list() if col in df else []
            R["mesures"][col] = {"n": len(v), "mediane": float(np.median(v)) if v else None, "p75": float(np.percentile(v, 75)) if v else None,
                                 "p90": float(np.percentile(v, 90)) if v else None}
            m = R["mesures"][col]
            f = lambda x: "—" if x is None else f"{x:.3%}"
            l.append(f"| {nom} | {int(q):,} USDT | {f(m['mediane'])} | {f(m['p75'])} | {f(m['p90'])} | {len(v)}/{len(df)} | {HYPOTHESES[nom]:.2%} |")
        R["retenus_pour_le_gel"][nom] = plafond_retenu(HYPOTHESES[nom], df[f"{nom}_10000"].dropna().to_list() if f"{nom}_10000" in df else [])
    l += ["", "Règle écrite avant la mesure : glissement retenu = max(hypothèse, 75e centile mesuré à 10 000 USDT), arrondi au centième de point supérieur.",
          "**Retenus pour le gel :** " + ", ".join(f"{k} {v:.2%}" for k, v in R["retenus_pour_le_gel"].items()) + ".",
          "", "Limite : lecture de la bande (la liquidité consommée par d'autres) ; le stop est mesuré par un indicateur indirect, en pleine cascade, sans simuler de position."]
    (out / f"glissements_{h}.md").write_text("\n".join(l) + "\n")
    (out / f"glissements_{h}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
    print("\n".join(l))
    return 0


if __name__ == "__main__":
    sys.exit(main())
