#!/usr/bin/env python3
"""Taille de l'univers de STRAT-20261031-03 par bloc, selon la règle de volume (préalable au gel de D6).

**Volumes seulement.** De chaque archive 1 d, le script ne garde que l'heure d'ouverture et le volume en USDT
(colonnes 0 et 7). Il ne lit aucun prix et ne calcule aucun rendement. Il lit les volumes des trois blocs, hors
échantillon compris, comme l'audit du 01/11/2026 (`audit_univers.py`) l'a déjà fait : cette lecture est déclarée.

Règles comparées, toutes après exclusions D6 a et c (listes), ancienneté D6 b (180 j continus) et test « vivant » :
- `sans_seuil`  : top 30 par médiane de volume sur 30 j (règle du 31/10 sans le seuil) ;
- `absolu_50M`  : top 30, puis médiane ≥ 50 M USDT (D6 c tel que proposé) ;
- `relatif_20pct` : top 30 ∩ les 20 % de candidats éligibles les plus traités ;
- `indexe_marche` : top 30, puis médiane ≥ 50 M × V_t / médiane de V sur le développement,
  V_t = somme des médianes du top 30 au lundi t.

Usage :
    python -B controle_taille_univers.py --cache ~/cache_binance_vision
    python -B controle_taille_univers.py --source-locale DOSSIER
Sorties : resultats/taille_univers_<horodatage>.csv (une ligne par lundi) et .md (synthèse par bloc).
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import moteur_xsmom as m  # noqa: E402
import run_essai as re_  # noqa: E402

BLOCS = [("developpement", "2021-01-04", "2024-06-24"), ("validation", "2024-07-01", "2025-07-21"),
         ("hors_echantillon", "2025-08-04", "2026-10-19")]
FIN_VOLUMES = pd.Timestamp("2026-10-19")  # dernier lundi évalué : jours lus < cette date
SEUIL = 50e6
REGLES = ["sans_seuil", "absolu_50M", "relatif_20pct", "indexe_marche"]


def lire_volumes_zip(z: bytes) -> pd.Series:
    with zipfile.ZipFile(io.BytesIO(z)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f, header=None, usecols=[0, 7], dtype=str)  # heure d'ouverture et volume USDT, rien d'autre
    df = df[df[0].str.fullmatch(r"\d+", na=False)]
    return pd.Series(df[7].astype(float).values, index=db._ms_vers_ts(df[0]).values)


def volumes(source, symboles, debut, fin, fils=8) -> pd.DataFrame:
    ms = db.mois(debut, fin)

    def un(sym):
        parts = []
        for mo in ms:
            z = source.lire(f"{db.RACINE}/klines/{sym}/1d/{sym}-1d-{mo}.zip")
            if z is not None:
                x = lire_volumes_zip(z)
                parts.append(x[x.index < db.naif(fin)])
        return sym, (pd.concat(parts) if parts else None)

    with ThreadPoolExecutor(fils) as ex:
        res = {s: v for s, v in ex.map(un, symboles) if v is not None and len(v)}
    vol = pd.DataFrame({s: v[~v.index.duplicated(keep="last")] for s, v in res.items()})
    return vol.reindex(pd.date_range(vol.index.min(), vol.index.max(), freq="D"))


def lundis(blocs=BLOCS):
    out = []
    for nom, a, b in blocs:
        out += [(t, nom) for t in pd.date_range(a, b, freq="W-MON")]
    return out


def mesurer(vol: pd.DataFrame, p: m.Params, memes: frozenset, blocs=BLOCS) -> pd.DataFrame:
    jours = {"volume": vol.rename(columns={"BTCUSDT": "BTC"})}
    jours["volume"] = m.couper_zombies({"volume": jours["volume"]}, {}, None)[0]["volume"]
    p_large = m.Params(**{**p.__dict__, "taille_univers": 10**6, "volume_min": 0.0})
    p_memes = m.Params(**{**p_large.__dict__, "exclus": p.exclus - memes})
    lignes = []
    for t, bloc in lundis(blocs):
        cand = m.candidats_classes(jours, t, p_large)
        top = cand[:30]
        meds = np.array([v for _, v in top])
        n_cand = len(cand)
        k20 = math.ceil(0.2 * n_cand)
        top_memes = [s for s, _ in m.candidats_classes(jours, t, p_memes)[:30]]
        lignes.append({
            "lundi": t.date(), "bloc": bloc, "candidats": n_cand,
            "sans_seuil": len(top),
            "absolu_50M": int((meds >= SEUIL).sum()),
            "relatif_20pct": min(len(top), k20),
            "V_t": float(meds.sum()),
            "vol_rang_6": float(meds[5]) if len(meds) > 5 else np.nan,
            "vol_rang_12": float(meds[11]) if len(meds) > 11 else np.nan,
            "vol_rang_30": float(meds[29]) if len(meds) > 29 else np.nan,
            "memes_qui_seraient_dans_le_top30": sum(m.est_exclu(s, memes) for s in top_memes),
            "_meds": meds,
        })
    df = pd.DataFrame(lignes)
    ref = df.loc[df["bloc"] == "developpement", "V_t"].median()
    df["seuil_indexe"] = SEUIL * df["V_t"] / ref
    df["indexe_marche"] = [int((r["_meds"] >= r["seuil_indexe"]).sum()) for _, r in df.iterrows()]
    return df.drop(columns="_meds")


def synthese(df: pd.DataFrame, blocs=BLOCS) -> pd.DataFrame:
    rows = []
    for (bloc, _, _), regle in [(b, r) for b in blocs for r in REGLES]:
        x = df.loc[df["bloc"] == bloc, regle]
        rows.append({"bloc": bloc, "regle": regle, "semaines": len(x), "mediane": float(x.median()), "min": int(x.min()),
                     "sous_30": int((x < 30).sum()), "sous_12": int((x < 12).sum()), "sous_6_vides": int((x < 6).sum())})
    return pd.DataFrame(rows)


def rapport(df, syn, meta) -> str:
    l = [f"# Taille de l'univers de STRAT-20261031-03 par bloc — {meta['horodatage']}", "",
         "Volumes 1 d seulement (colonnes heure et volume USDT), aucun prix, aucun rendement. Aucun essai consommé. "
         f"Symboles lus : {meta['symboles']}. Exclusions et ancienneté de `config_strat03.json` (statut {meta['statut']}), "
         f"interruption tolérée : {meta.get('trou_max_jours', 0)} j.", "",
         "| Bloc | Règle | Semaines | Médiane | Min | < 30 | < 12 | < 6 (vides) |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in syn.iterrows():
        l.append(f"| {r.bloc} | {r.regle} | {r.semaines} | {r.mediane:.0f} | {r['min']} | {r.sous_30} | {r.sous_12} | {r.sous_6_vides} |")
    l += ["", "| Bloc | Volume du 6e nom, min / médiane (M$) | 12e nom | 30e nom | Memecoins qui seraient dans le top 30, moyenne |",
          "|---|---|---|---|---:|"]
    for bloc, _, _ in BLOCS:
        x = df[df["bloc"] == bloc]
        f = lambda c: f"{x[c].min() / 1e6:.1f} / {x[c].median() / 1e6:.1f}"
        l.append(f"| {bloc} | {f('vol_rang_6')} | {f('vol_rang_12')} | {f('vol_rang_30')} | {x['memes_qui_seraient_dans_le_top30'].mean():.2f} |")
    l += ["", "Lecture prévue avant le gel : si `absolu_50M` passe souvent sous 12 noms en développement, le signal 3 + 3 "
          "ne vise plus les mêmes extrêmes d'une semaine à l'autre. Le choix de la règle se fait sur ce tableau, avant E01, "
          "et le choix est consigné dans la fiche § 0."]
    return "\n".join(l) + "\n"


def diagnostic(vol: pd.DataFrame, p: m.Params, avant: pd.Timestamp, apres: pd.Timestamp) -> pd.DataFrame:
    """Noms éligibles au lundi `avant` mais plus au lundi `apres` : jours nuls et jours absents de leur fenêtre
    d'ancienneté. Volumes seulement. Sert à séparer une vraie interruption de cotation d'un trou d'archive."""
    jours = {"volume": vol.rename(columns={"BTCUSDT": "BTC"})}
    p_large = m.Params(**{**p.__dict__, "taille_univers": 10**6, "volume_min": 0.0})
    a = {s for s, _ in m.candidats_classes(jours, avant, p_large)}
    b = {s for s, _ in m.candidats_classes(jours, apres, p_large)}
    fen = pd.date_range(apres - pd.Timedelta(days=p.anciennete), apres - pd.Timedelta(days=1), freq="D")
    lignes = []
    for s in sorted(a - b):
        v = jours["volume"][s].reindex(fen)
        absents = [d.date().isoformat() for d in v.index[v.isna()]]
        nuls = [d.date().isoformat() for d in v.index[v.fillna(-1) == 0]]
        lignes.append({"symbole": s, "jours_absents": len(absents), "jours_nuls": len(nuls),
                       "plus_long_trou": m.plus_long_trou(v.fillna(0).to_numpy() > 0),
                       "premiers_absents": " ".join(absents[:5]), "premiers_nuls": " ".join(nuls[:5])})
    return pd.DataFrame(lignes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    ap.add_argument("--sorties", default=str(ICI / "resultats"))
    ap.add_argument("--trou-max", type=int, default=None,
                    help="remplace trou_max_jours de la config pour ce comptage (comparaison, ne change pas la config)")
    ap.add_argument("--diagnostic", nargs=2, metavar=("LUNDI_AVANT", "LUNDI_APRES"),
                    help="liste les noms perdus entre deux lundis et leurs jours nuls ou absents")
    a = ap.parse_args(argv)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    config = re_.charger_config()
    p = re_.params_depuis(config)
    if a.trou_max is not None:
        p = m.Params(**{**p.__dict__, "trou_max_jours": a.trou_max})
    memes = frozenset(config["exclusions"]["memecoins_liste_close_2026-11-01"])
    debut = pd.Timestamp(BLOCS[0][1]) - pd.Timedelta(days=p.anciennete + p.fenetre_volume + 10)
    vol = volumes(source, db.symboles_usdt(source), debut, FIN_VOLUMES)
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(a.sorties)
    out.mkdir(exist_ok=True)
    if a.diagnostic:
        dg = diagnostic(vol, p, pd.Timestamp(a.diagnostic[0]), pd.Timestamp(a.diagnostic[1]))
        dg.to_csv(out / f"diagnostic_continuite_{h}.csv", index=False)
        print(dg.to_string(index=False))
        print(f"Noms perdus : {len(dg)}. Total jours absents : {int(dg['jours_absents'].sum()) if len(dg) else 0}, "
              f"jours nuls : {int(dg['jours_nuls'].sum()) if len(dg) else 0}.")
        return 0
    df = mesurer(vol, p, memes)
    syn = synthese(df)
    meta = {"horodatage": h, "symboles": vol.shape[1], "statut": config["statut_regles"], "trou_max_jours": p.trou_max_jours}
    df.to_csv(out / f"taille_univers_{h}.csv", index=False)
    (out / f"taille_univers_{h}.md").write_text(rapport(df, syn, meta))
    print(rapport(df, syn, meta))
    print(json.dumps({"incidents": len(getattr(source, "incidents", [])), "appels": getattr(source, "appels", None)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
