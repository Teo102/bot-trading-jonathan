#!/usr/bin/env python3
"""Stabilité d'un jour à l'autre de l'entrée au top 30, règle médiane contre règle 24 h.

Rejoue les deux règles sur les bougies 1 j closes de Binance, sur les perpétuels listés
dans le fichier volumes d'une collecte. Le volume d'une bougie close sert d'approximation
du volume 24 h. Mesure seulement l'entrée au classement, pas le panier, car les carnets
passés ne sont pas disponibles. L'univers est celui d'aujourd'hui, avec son biais du survivant.

Usage : python stabilite_top30.py VOLUMES_CSV SORTIE_JSON [--jours 14] [--top 30]
Point d'accès public en lecture seule. Aucune clé, aucun ordre.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screener_univers import BINANCE, JOURS_VOLUME_MEDIAN, ClientPublic, iso, log, maintenant  # noqa: E402


def tops_par_jour(volumes: pd.DataFrame, jours: int, top: int) -> dict:
    """volumes : une colonne par symbole, une ligne par jour clos, dans l'ordre du temps."""
    sortie = {}
    for fin in volumes.index[-jours:]:
        fenetre = volumes.loc[:fin].tail(JOURS_VOLUME_MEDIAN)
        complets = fenetre.columns[fenetre.notna().sum() >= JOURS_VOLUME_MEDIAN]
        mediane = fenetre[complets].median().sort_values(ascending=False)
        jour = volumes.loc[fin].dropna().sort_values(ascending=False)
        sortie[fin] = {"mediane": mediane.index[:top].tolist(), "volume_jour": jour.index[:top].tolist()}
    return sortie


def rotation(tops: dict, regle: str) -> list:
    dates = list(tops)
    lignes = []
    for avant, apres in zip(dates, dates[1:]):
        a, b = set(tops[avant][regle]), set(tops[apres][regle])
        lignes.append({"date": apres, "entrees": sorted(b - a), "sorties": sorted(a - b), "n_changes": len(b - a)})
    return lignes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("volumes_csv", type=Path)
    ap.add_argument("sortie_json", type=Path)
    ap.add_argument("--jours", type=int, default=14)
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    symboles = pd.read_csv(args.volumes_csv)["symbole"].tolist()
    c = ClientPublic()
    debut = iso(maintenant())
    now_ms = int(time.time() * 1000)
    series, erreurs = {}, []
    log(f"Bougies 1 j de {len(symboles)} perpétuels")
    for s in symboles:
        try:
            brut = c.get(f"{BINANCE}/fapi/v1/klines", {"symbol": s, "interval": "1d", "limit": JOURS_VOLUME_MEDIAN + args.jours + 1})
            series[s] = {iso(k[0])[:10]: float(k[7]) for k in brut if k[6] < now_ms}
        except Exception as e:  # consigné, jamais remplacé par une valeur inventée
            erreurs.append(f"{s} {e}")
    volumes = pd.DataFrame(series).sort_index()
    tops = tops_par_jour(volumes, args.jours + 1, args.top)
    res = {
        "debut": debut, "fin": iso(maintenant()), "source": "Binance /fapi/v1/klines 1d", "n_symboles": len(series), "erreurs": erreurs,
        "appels_http": c.appels, "incidents_http": c.incidents, "top": args.top, "jours_comparés": args.jours,
        "rotation_mediane": rotation(tops, "mediane"), "rotation_volume_jour": rotation(tops, "volume_jour"), "tops": tops,
    }
    for regle in ("mediane", "volume_jour"):
        n = [l["n_changes"] for l in res[f"rotation_{regle}"]]
        res[f"resume_{regle}"] = {"moyenne_changes_par_jour": float(np.mean(n)), "max": int(max(n)), "min": int(min(n)), "total": int(sum(n))}
        log(f"{regle} : {res[f'resume_{regle}']}")
    args.sortie_json.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Sortie {args.sortie_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
