#!/usr/bin/env python3
"""Lance E01 ou E02 de STRAT-20261102-05 et l'inscrit au registre. Mêmes garde-fous que STRAT-03 :
refus si `config_strat05.json` n'est pas figée, si l'essai a déjà une date, ou s'il est hors échantillon.

Usage : python -B run_essai05.py --essai E01 --cache ~/cache_binance_vision
Rappel (fiche § 0) : E01 et E02 servent seulement à éliminer. Résultat de recherche, aucun ordre.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
S03 = ICI.parent / "STRAT-20261031-03"
sys.path.insert(0, str(S03))
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import moteur_xsmom as m  # noqa: E402
import run_essai as r3  # noqa: E402
import controle_taille_univers as ctu  # noqa: E402
import donnees_metrics as dm  # noqa: E402
import signal_encombrement as se  # noqa: E402

CONFIG = ICI / "config_strat05.json"
REGISTRE = ICI / "REGISTRE_ESSAIS.csv"
SORTIES = ICI / "resultats"


def charger_configs(chemin: Path = CONFIG):
    c5 = json.loads(chemin.read_text())
    c3 = json.loads((ICI / c5["reprise_infrastructure"]).resolve().read_text())
    return c5, c3


def params_score(c5: dict) -> se.ParamsScore:
    s = c5["score"]
    return se.ParamsScore(fenetre_f=s["fenetre_financement_j"], fenetre_o=s["fenetre_interet_ouvert_j"],
                          poids_f=s["poids_financement"], poids_o=s["poids_interet_ouvert"], borne_z=s["borne_z"])


def portes_internes(mt: dict) -> dict:
    """Mesures de la fiche § 6 calculables sur un seul essai (les autres portes demandent E03 à E19)."""
    prix_net = mt["pnl_prix"] - mt["couts"]
    return {"rendement_net_positif": mt["rendement_net_total_brut100"] > 0,
            "prix_net_de_couts": prix_net, "prix_seul_positif_ou_nul": prix_net >= 0,
            "concentration_nom_ok": (mt["part_max_nom_du_gain"] <= 0.25) if mt["rendement_net_total_brut100"] > 0 else None,
            "concentration_mois_ok": (mt["part_max_mois_du_gain"] <= 0.40) if mt["rendement_net_total_brut100"] > 0 else None,
            "drawdown_brut100_ok": mt["drawdown_max_brut100"] < 0.50}


def executer(essai: str, source, c5=None, c3=None, registre: Path = REGISTRE, sorties: Path = SORTIES, symboles=None) -> dict:
    if c5 is None:
        c5, c3 = charger_configs()
    if c5.get("statut_regles") != "figees":
        raise r3.Refus("Règles de STRAT-05 non figées (config_strat05.json, statut_regles). Aucun essai lancé.")
    bloc = r3.controles(essai, c5, registre)
    if c3.get("statut_regles") != "figees":
        raise r3.Refus("L'infrastructure de STRAT-03 n'est plus figée : refus.")
    p = r3.params_depuis(c3)
    ps = params_score(c5)
    lundis = r3.lundis_du_bloc(bloc)
    fin = db.naif(bloc["fin_donnees_prix"])
    debut_jours = lundis[0] - pd.Timedelta(days=p.anciennete + p.fenetre_volume + 10)
    syms = symboles or db.symboles_usdt(source)
    comblement: dict = {}
    jours = db.charger_jours(source, syms, debut_jours, fin, journal=comblement)
    jours = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in jours.items()}
    jc = m.couper_zombies(jours, {}, None)[0]
    univ = {t: m.univers(jc, t, p) for t in lundis[:-1]}
    noms = sorted(set().union(*univ.values()) | {"BTCUSDT"})
    heures, fin_df, qualite = db.charger_heures(source, noms, lundis[0] - pd.Timedelta(days=max(ps.fenetre_f, 1) + 1), fin, journal=comblement)
    btc = r3.rendements_btc(heures, lundis)
    oi = dm.charger_oi(source, dm.jours_requis(univ, (ps.fenetre_o,)), fin, journal=qualite)
    ren = {"BTCUSDT": "BTC"}
    heures = {k: v.rename(columns=ren) for k, v in heures.items()}
    fin_df = fin_df.rename(columns=ren)
    utiles = ["BTC"] + [s for s in noms if s != "BTCUSDT"]
    jours = {k: v.reindex(columns=utiles) for k, v in jours.items()}
    heures = {k: v.reindex(columns=utiles) for k, v in heures.items()}
    qualite["comblement"] = {n: {"symboles": len(v), "jours_combles": sum(len(x["jours_comble"]) for x in v.values()),
                                 "jours_introuvables": sum(len(x["jours_introuvables"]) for x in v.values())}
                             for n, v in comblement.items()}
    qualite["sans_archive_1h"] = sorted(set(utiles) - set(heures["open"].dropna(axis=1, how="all").columns))
    sem, lig = m.backtest(jours, heures, fin_df, lundis, p, notionnel=1.0 / 6, fonction_scores=se.fabrique_scores(fin_df, oi, ps))
    mt = r3.metriques(sem, lig, btc, c5)
    mt["portes_internes"] = portes_internes(mt)
    h = r3.horo()
    meta = {"horodatage": h, "essai": essai, "bloc": [k for k, b in c5["blocs"].items() if b["essai"] == essai][0],
            "premier_lundi": bloc["premier_lundi"], "dernier_lundi": bloc["dernier_lundi"], "fin_donnees": bloc["fin_donnees_prix"],
            "empreinte": db.empreinte({**{f"j_{k}": v for k, v in jours.items()}, **{f"h_{k}": v for k, v in heures.items()}, "oi": oi}),
            "config05_sha256": hashlib.sha256(json.dumps(c5, sort_keys=True).encode()).hexdigest(),
            "config03_sha256": hashlib.sha256(json.dumps(c3, sort_keys=True).encode()).hexdigest(),
            "qualite": qualite, "incidents": len(getattr(source, "incidents", [])), "appels": getattr(source, "appels", None)}
    sorties.mkdir(exist_ok=True)
    (sorties / f"{essai}_metriques.json").write_text(json.dumps({"meta": meta, "metriques": mt}, ensure_ascii=False, indent=1, default=str))
    md = r3.rapport_md(essai, mt, meta).replace("STRAT-20261031-03", "STRAT-20261102-05")
    pi = mt["portes_internes"]
    md += (f"\nPortes calculables sur cet essai : rendement net > 0 : {pi['rendement_net_positif']} ; prix net de coûts : "
           f"{100 * pi['prix_net_de_couts']:+.2f} % ({'passe' if pi['prix_seul_positif_ou_nul'] else 'échoue'}) ; concentration nom : "
           f"{pi['concentration_nom_ok']} ; mois : {pi['concentration_mois_ok']} ; drawdown < 50 % : {pi['drawdown_brut100_ok']}. "
           f"Intérêt ouvert : {qualite.get('oi_jours_demandes')} jours demandés, {qualite.get('oi_jours_introuvables')} introuvables. "
           "Rappel : ce bloc sert seulement à éliminer (fiche § 0).\n")
    (sorties / f"{essai}_metriques.md").write_text(md)
    sem.to_csv(sorties / f"{essai}_semaines.csv", index=False)
    lig.to_csv(sorties / f"{essai}_lignes.csv", index=False)
    r3.ecrire_registre(essai, mt, h, registre)
    return {"meta": meta, "metriques": mt, "rapport": md}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    a = ap.parse_args(argv)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    try:
        out = executer(a.essai, source)
    except r3.Refus as e:
        print(f"REFUS : {e}", file=sys.stderr)
        return 2
    print(out["rapport"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
