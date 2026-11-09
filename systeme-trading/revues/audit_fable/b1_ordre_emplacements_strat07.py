#!/usr/bin/env python3
"""Audit Fable, STRAT-07, contrôle B1 : le « premier arrivé, premier servi » du criblage dépend-il de l'ordre des symboles ?

Diagnostic sur les épisodes déjà lus par le criblage du 09/11/2026 (financement seul, blocs consommés). Aucune donnée
nouvelle, aucune règle choisie, hors N : il ne peut que qualifier un chiffre déjà publié. Publié quel que soit le résultat.

Le criblage trie les épisodes par heure de début. Les versements tombent aux mêmes heures pour tous les symboles :
beaucoup d'épisodes commencent au même instant, et le tri les départage par l'ordre du fichier, c'est-à-dire l'ordre
alphabétique des symboles. On refait le portefeuille (même fonction) avec d'autres départages.

Usage : python3 -B b1_ordre_emplacements_strat07.py <dossier des episodes_*.csv>"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd

ICI = Path(__file__).resolve().parent
DEBUT, FIN = pd.Timestamp("2021-01-01"), pd.Timestamp("2025-07-28 02:00:00")
ANS = (FIN - DEBUT).days / 365.25
TAUX_COURT = 0.03875


def portefeuille(e: pd.DataFrame, k: int = 10):
    """Même logique que `criblage_strat07.portefeuille`, sur un ordre déjà fixé (tri stable par début)."""
    pris, libres = [], []
    for r in e.sort_values("debut", kind="stable").itertuples():
        libres = [f for f in libres if f > r.debut]
        if len(libres) < k:
            pris.append(r.Index); libres.append(r.fin)
    return pris


R = {}
for cle in ("entree_50_sortie_10", "entree_30_sortie_10"):
    e = pd.read_csv(Path(sys.argv[1]) / f"episodes_{cle}.csv", parse_dates=["debut", "fin"])
    rdt = lambda idx: float(e.loc[idx, "net"].sum()) / 20 / ANS
    publie = rdt(portefeuille(e))  # ordre du fichier = ordre alphabétique des symboles
    alpha = rdt(portefeuille(e.sort_values("symbole", kind="stable")))
    inverse = rdt(portefeuille(e.sort_values("symbole", ascending=False, kind="stable")))
    rng = np.random.default_rng(20261109)
    tirages = np.array([rdt(portefeuille(e.sample(frac=1, random_state=int(rng.integers(1 << 31))))) for _ in range(2000)])
    meme_instant = float(e["debut"].duplicated(keep=False).mean())
    pris = portefeuille(e)
    p = e.loc[pris]
    par_an = (p.groupby(p["debut"].dt.year)["net"].sum() / 20).round(4).to_dict()
    tous = float(e["net"].sum()) / 20 / ANS
    R[cle] = {"episodes": int(len(e)), "pris_ordre_publie": len(pris), "part_debuts_simultanes": round(meme_instant, 3),
              "rendement_publie": round(publie, 4), "ordre_alphabetique": round(alpha, 4), "ordre_alphabetique_inverse": round(inverse, 4),
              "aleatoire_2000_tirages": {"min": round(float(tirages.min()), 4), "q05": round(float(np.quantile(tirages, .05)), 4),
                                         "mediane": round(float(np.median(tirages)), 4), "q95": round(float(np.quantile(tirages, .95)), 4),
                                         "max": round(float(tirages.max()), 4),
                                         "part_sous_le_taux_court": round(float((tirages <= TAUX_COURT).mean()), 4),
                                         "part_au_dessus_du_publie": round(float((tirages >= publie).mean()), 4)},
              "contribution_par_annee_de_debut_points_de_capital": par_an,
              "part_2021_dans_le_gain_pris": round(float(p[p["debut"].dt.year == 2021]["net"].sum() / p["net"].sum()), 3),
              "rendement_annuel_hors_episodes_debutes_en_2021": round(float(p[p["debut"].dt.year != 2021]["net"].sum()) / 20 / ((FIN - pd.Timestamp("2022-01-01")).days / 365.25), 4),
              "top5_symboles_part_du_gain_pris": round(float(p.groupby("symbole")["net"].sum().nlargest(5).sum() / p["net"].sum()), 3),
              "duree_mediane_pris_h": float(p["heures"].median()),
              "ouverts_au_verrou_pris": int(p["ouvert_au_verrou"].fillna(False).astype(bool).sum())}
    print(cle, json.dumps(R[cle], indent=1, ensure_ascii=False))
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"b1_ordre_emplacements_strat07_{h}.json").write_text(json.dumps({"genere_utc": h, **R}, indent=1, ensure_ascii=False))
