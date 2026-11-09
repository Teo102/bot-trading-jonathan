#!/usr/bin/env python3
"""Criblage de faisabilité de STRAT-07 (portage de financement conditionnel aux pointes), 09/11/2026.

Étape 1 de l'entonnoir (`REGISTRE_HYPOTHESES.md`) : aucune fiche, aucun prix d'entrée ni de sortie. Lit seulement le
financement (archives fundingRate), les volumes journaliers des perpétuels (filtre de liquidité) et la liste des paires
au comptant. Période : 01/01/2021 au 28/07/2025 02:00 UTC (blocs déjà consommés par STRAT-03, 05 et 06, contamination
déclarée). La période postérieure reste réservée au hors échantillon de STRAT-07.

Règle de décision écrite AVANT le calcul (recherche/criblage_strat07/CRIBLAGE_STRAT-07.md § 2).

Usage (serveur) : python3 -B criblage_strat07.py --cache ~/cache_binance_vision
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
RACINE_DEPOT = ICI.parent.parent
sys.path.insert(0, str(RACINE_DEPOT / "strategies" / "STRAT-20261031-03"))
sys.path.insert(0, str(RACINE_DEPOT / "recherche" / "audit_donnees"))

DEBUT, FIN = pd.Timestamp("2021-01-01"), pd.Timestamp("2025-07-28 02:00:00")
GRILLE = [(0.30, 0.10), (0.50, 0.10), (0.50, 0.20)]   # (seuil d'entrée, seuil de sortie), annualisés, déclarés d'avance
COUT_ALLER_RETOUR = 0.005   # 4 jambes : comptant 0,10 % x 2, perpétuel 0,05 % x 2, glissement 0,05 % x 4
LIQUIDITE_MIN = 20e6        # médiane du volume journalier du perpétuel sur 30 jours (comme STRAT-06)
EMPLACEMENTS = 10           # portefeuille indicatif : 10 positions, chacune 1/10 du capital (moitié comptant, moitié marge)
TAUX_COURT = 0.03875        # référence de STRAT-02 et de H10


def annualiser(taux: pd.Series) -> pd.Series:
    """Taux par versement -> taux annualisé, avec l'intervalle observé entre versements (1, 4 ou 8 heures)."""
    pas_h = taux.index.to_series().diff().dt.total_seconds().div(3600)
    pas_h = pas_h.fillna(pas_h.median() if pas_h.notna().any() else 8).clip(lower=1, upper=8)
    return taux * (365 * 24 / pas_h)


def episodes(taux: pd.Series, eligible: pd.Series, seuil_in: float, seuil_out: float) -> list[dict]:
    """Sans anticipation : on observe le versement i ; si son annualisé ≥ seuil_in et que le nom est éligible ce jour,
    on entre après ; on encaisse les versements suivants ; on sort après le premier versement observé sous seuil_out
    (encaissé). Un taux négatif pendant la tenue se paie. `eligible` : booléen journalier."""
    ann = annualiser(taux)
    out, dedans, debut, cumul, n = [], False, None, 0.0, 0
    for t, r, a in zip(taux.index, taux.values, ann.values):
        if dedans:
            cumul += r; n += 1
            if a < seuil_out:
                out.append({"debut": debut, "fin": t, "versements": n, "brut": cumul,
                            "heures": (t - debut).total_seconds() / 3600}); dedans = False
        elif a >= seuil_in and bool(eligible.get(t.normalize(), False)):
            dedans, debut, cumul, n = True, t, 0.0, 0
    if dedans and n:
        out.append({"debut": debut, "fin": taux.index[-1], "versements": n, "brut": cumul,
                    "heures": (taux.index[-1] - debut).total_seconds() / 3600, "ouvert_au_verrou": True})
    return out


def portefeuille(eps: pd.DataFrame, emplacements: int = EMPLACEMENTS) -> dict:
    """Premier arrivé, premier servi ; un épisode est pris s'il reste un emplacement libre à son début."""
    pris, libres_a = [], []
    for e in eps.sort_values("debut").itertuples():
        libres_a = [f for f in libres_a if f > e.debut]
        if len(libres_a) < emplacements:
            pris.append(e.net); libres_a.append(e.fin)
    ans = (FIN - DEBUT).days / 365.25
    # notionnel d'un emplacement = capital / (2 x emplacements) : moitié comptant, moitié marge du short
    r = float(np.sum(pris)) / (2 * emplacements) / ans
    return {"episodes_pris": len(pris), "episodes_refuses": int(len(eps) - len(pris)), "rendement_annuel_capital": r}


def main(argv=None) -> int:
    import donnees_binance as db
    import audit_donnees_intraday as au
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(Path.home() / "cache_binance_vision"))
    ap.add_argument("--max-symboles", type=int, default=0)
    a = ap.parse_args(argv)
    src = db.VisionHTTP(Path(a.cache).expanduser())
    perps = db.symboles_usdt(src)
    spot = set(au.symboles("data/spot/monthly/klines/"))
    syms = [s for s in perps if s in spot]
    if a.max_symboles:
        syms = syms[: a.max_symboles]
    # mois de première archive au comptant (la paire existe à la date)
    prem_spot = {}
    for s in syms:
        o = au.zips(au.lister(f"data/spot/monthly/klines/{s}/1d/")[0])
        prem_spot[s] = au.periode(o)[0]
    jours = db.charger_jours(src, syms, DEBUT - pd.Timedelta(days=40), FIN)
    vol = jours["volume"]
    liq = vol.fillna(0).rolling(30, min_periods=20).median().shift(1)   # médiane des 30 jours précédents
    toutes = {k: [] for k in GRILLE}
    for s in syms:
        f = db.charger_symbole(src, s, "financement", DEBUT, FIN)
        if f is None or not len(f) or s not in liq:
            continue
        f = f[f.index >= DEBUT]
        ps = pd.Timestamp(prem_spot[s] + "-01") if prem_spot.get(s) else None
        el = (liq[s] >= LIQUIDITE_MIN)
        if ps is not None:
            el &= el.index >= ps + pd.offsets.MonthBegin(1)   # comptant coté depuis au moins un mois entier
        else:
            el &= False
        for k in GRILLE:
            for e in episodes(f, el, *k):
                e["symbole"] = s
                toutes[k].append(e)
    R = {"periode": [str(DEBUT), str(FIN)], "symboles_avec_comptant": len(syms), "cout_aller_retour": COUT_ALLER_RETOUR,
         "emplacements": EMPLACEMENTS, "grille": {}}
    for k, lst in toutes.items():
        cle = f"entree_{int(k[0]*100)}_sortie_{int(k[1]*100)}"
        if not lst:
            R["grille"][cle] = {"episodes": 0}
            continue
        e = pd.DataFrame(lst)
        e["net"] = e["brut"] - COUT_ALLER_RETOUR
        e.to_csv(ICI / f"episodes_{cle}.csv", index=False)
        an = e.groupby(e["debut"].dt.year)
        R["grille"][cle] = {
            "episodes": len(e), "symboles": int(e.symbole.nunique()),
            "brut_median": float(e.brut.median()), "brut_moyen": float(e.brut.mean()),
            "net_median": float(e.net.median()), "net_moyen": float(e.net.mean()),
            "part_brut_sup_3x_cout": float((e.brut >= 3 * COUT_ALLER_RETOUR).mean()),
            "part_net_positif": float((e.net > 0).mean()),
            "duree_mediane_h": float(e.heures.median()), "duree_q90_h": float(e.heures.quantile(0.9)),
            "versements_medians": float(e.versements.median()),
            "par_annee": {str(y): {"episodes": len(g), "net_total": float(g.net.sum()), "net_median": float(g.net.median())} for y, g in an},
            "part_net_top10_symboles": float(e.groupby("symbole").net.sum().nlargest(10).sum() / e.net.sum()) if e.net.sum() > 0 else None,
            "portefeuille_indicatif": portefeuille(e),
        }
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (ICI / f"criblage_{h}.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False))
    base = R["grille"].get("entree_30_sortie_10", {})
    base50 = R["grille"].get("entree_50_sortie_10", {})
    def ok(g):
        return bool(g.get("episodes") and g["brut_median"] >= 3 * COUT_ALLER_RETOUR
                    and g["portefeuille_indicatif"]["rendement_annuel_capital"] > TAUX_COURT)
    verdict = "poursuite : fiche autorisée" if (ok(base) or ok(base50)) else "écartée sans fiche (comme H10)"
    lignes = [f"# Criblage de STRAT-07 — {h}", "", f"Période {DEBUT.date()} au {FIN} (blocs consommés). Financement et volumes seulement.", "",
              "| Seuils (entrée / sortie) | Épisodes | Brut médian | Net médian | Part brut ≥ 3 × coût | Durée médiane (h) | Rendement indicatif sur capital |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for cle, g in R["grille"].items():
        if g.get("episodes"):
            lignes.append(f"| {cle} | {g['episodes']} | {g['brut_median']:+.2%} | {g['net_median']:+.2%} | {g['part_brut_sup_3x_cout']:.0%} | "
                          f"{g['duree_mediane_h']:.0f} | {g['portefeuille_indicatif']['rendement_annuel_capital']:+.2%}/an |")
    lignes += ["", f"Règle (écrite avant calcul) : brut médian ≥ 3 × {COUT_ALLER_RETOUR:.1%} **et** rendement indicatif > {TAUX_COURT:.3%}/an, "
               "sur la grille 30/10 ou 50/10.", f"**Verdict du criblage : {verdict}.**", "",
               "Non mesurés : base comptant/perpétuel à l'entrée et à la sortie (probablement favorable), risque de plateforme, coût du capital immobilisé."]
    (ICI / f"criblage_{h}.md").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
