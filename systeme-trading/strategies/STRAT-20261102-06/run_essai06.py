#!/usr/bin/env python3
"""Lance E01 ou E02 de STRAT-20261102-06 et l'inscrit au registre. Mêmes garde-fous que STRAT-03 et STRAT-05.

Usage : python -B run_essai06.py --essai E01 --cache ~/cache_binance_vision
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
import univers_cotations as uc  # noqa: E402

CONFIG = ICI / "config_strat06.json"
REGISTRE = ICI / "REGISTRE_ESSAIS.csv"
SORTIES = ICI / "resultats"
DEBUT_DONNEES = pd.Timestamp("2019-09-01")  # début des perpétuels USDT de Binance : un nom actif avant est « ancien »
NOTIONNEL = 1.0 / 12  # brut 100 % : 6 shorts à 1/12 et la couverture BTC à 6/12


def charger_configs(chemin: Path = CONFIG):
    c6 = json.loads(chemin.read_text())
    c3 = json.loads((ICI / c6["reprise_infrastructure"]).resolve().read_text())
    return c6, c3


def params_cotation(c6: dict, c3: dict, **surcharges) -> uc.ParamsCotation:
    u, pf, ex = c6["univers"], c6["portefeuille"], c3["exclusions"]
    exclus = set(ex["stablecoins_et_indexes"] + ex["indices"])
    if not str(u.get("memecoins", "inclus")).startswith("inclus"):
        exclus |= set(ex["memecoins_liste_close_2026-11-01"])
    pc = dict(age_min_j=u["age_min_j"], age_max_j=u["age_max_j"], liquidite_min=float(u["liquidite_min_usdt"]),
              fenetre_liquidite_max_j=u["fenetre_liquidite_max_j"], noms_max=u["noms_max"],
              multiple_couverture=float(pf["multiple_couverture"]), exclus=frozenset(exclus),
              faux_nouveaux=frozenset(u.get("faux_nouveaux_noms", [])))
    fichier_nc = ICI / "exclusions_non_coin.json"
    if fichier_nc.exists():
        pc["faux_nouveaux"] = pc["faux_nouveaux"] | frozenset(json.loads(fichier_nc.read_text())["symboles"])
    pc.update(surcharges)
    return uc.ParamsCotation(**pc)


def portes_internes(mt: dict) -> dict:
    net = mt["rendement_net_total_brut100"]
    return {"rendement_net_positif": net > 0, "alpha_positif": mt["alpha_hebdo_residuel"] > 0,
            "concentration_nom_ok": (mt["part_max_nom_du_gain"] <= 0.25) if net > 0 else None,
            "concentration_mois_ok": (mt["part_max_mois_du_gain"] <= 0.40) if net > 0 else None,
            "drawdown_brut100_ok": mt["drawdown_max_brut100"] < 0.50,
            "part_semaines_vides": mt["semaines_vides"] / mt["semaines"] if mt["semaines"] else None}


def executer(essai: str, source, c6=None, c3=None, registre: Path = REGISTRE, sorties: Path = SORTIES, symboles=None,
             debut_donnees: pd.Timestamp = DEBUT_DONNEES, exiger_non_coin: bool = True) -> dict:
    if c6 is None:
        c6, c3 = charger_configs()
    if c6.get("statut_regles") != "figees":
        raise r3.Refus("Règles de STRAT-06 non figées (config_strat06.json, statut_regles). Aucun essai lancé.")
    if exiger_non_coin and not (ICI / "exclusions_non_coin.json").exists():
        raise r3.Refus("exclusions_non_coin.json absent : lancer exclusions_non_coin.py avant tout essai (fiche § 3.2).")
    bloc = r3.controles(essai, c6, registre)
    if c3.get("statut_regles") != "figees":
        raise r3.Refus("L'infrastructure de STRAT-03 n'est plus figée : refus.")
    p = r3.params_depuis(c3)
    pc = params_cotation(c6, c3)
    lundis = r3.lundis_du_bloc(bloc)
    fin = db.naif(bloc["fin_donnees_prix"])
    syms = symboles or db.symboles_usdt(source)
    comblement: dict = {}
    jours = db.charger_jours(source, syms, debut_donnees, fin, journal=comblement)
    jours = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in jours.items()}
    jc = m.couper_zombies(jours, {}, None)[0]
    cible = uc.fabrique_cible(pc, debut_donnees)
    choix = {t: cible(jc, t, p)[0] for t in lundis[:-1]}
    noms = sorted({s for d in choix.values() for s in d if s != "BTC"} | {"BTCUSDT"})
    heures, fin_df, qualite = db.charger_heures(source, noms, lundis[0] - pd.Timedelta(days=1), fin, journal=comblement)
    btc = r3.rendements_btc(heures, lundis)
    ren = {"BTCUSDT": "BTC"}
    heures = {k: v.rename(columns=ren) for k, v in heures.items()}
    fin_df = fin_df.rename(columns=ren)
    utiles = ["BTC"] + [s for s in noms if s != "BTCUSDT"]
    heures = {k: v.reindex(columns=utiles) for k, v in heures.items()}
    qualite["comblement"] = {n: {"symboles": len(v), "jours_combles": sum(len(x["jours_comble"]) for x in v.values()),
                                 "jours_introuvables": sum(len(x["jours_introuvables"]) for x in v.values())}
                             for n, v in comblement.items()}
    qualite["sans_archive_1h"] = sorted(set(utiles) - set(heures["open"].dropna(axis=1, how="all").columns))
    qualite["noms_differents"] = len(noms) - 1
    sem, lig = m.backtest(jours, heures, fin_df, lundis, p, notionnel=NOTIONNEL, fonction_cible=uc.fabrique_cible(pc, debut_donnees))
    if lig.empty:
        raise r3.Refus("Aucune ligne jouée sur le bloc : univers vide, vérifier les données avant tout verdict.")
    mt = r3.metriques(sem, lig, btc, c6)
    mt["portes_internes"] = portes_internes(mt)
    h = r3.horo()
    meta = {"horodatage": h, "essai": essai, "bloc": [k for k, b in c6["blocs"].items() if b["essai"] == essai][0],
            "premier_lundi": bloc["premier_lundi"], "dernier_lundi": bloc["dernier_lundi"], "fin_donnees": bloc["fin_donnees_prix"],
            "empreinte": db.empreinte({**{f"j_{k}": v for k, v in jours.items()}, **{f"h_{k}": v for k, v in heures.items()}}),
            "config06_sha256": hashlib.sha256(json.dumps(c6, sort_keys=True).encode()).hexdigest(),
            "config03_sha256": hashlib.sha256(json.dumps(c3, sort_keys=True).encode()).hexdigest(),
            "qualite": qualite, "incidents": len(getattr(source, "incidents", [])), "appels": getattr(source, "appels", None)}
    sorties.mkdir(exist_ok=True)
    (sorties / f"{essai}_metriques.json").write_text(json.dumps({"meta": meta, "metriques": mt}, ensure_ascii=False, indent=1, default=str))
    md = r3.rapport_md(essai, mt, meta).replace("STRAT-20261031-03", "STRAT-20261102-06")
    pi = mt["portes_internes"]
    md += (f"\nPortes calculables sur cet essai : rendement net > 0 : {pi['rendement_net_positif']} ; alpha sur BTC > 0 : "
           f"{pi['alpha_positif']} ; concentration nom : {pi['concentration_nom_ok']} ; mois : {pi['concentration_mois_ok']} ; "
           f"drawdown < 50 % : {pi['drawdown_brut100_ok']}. Semaines sans position : {mt['semaines_vides']} sur {mt['semaines']}. "
           f"Noms différents vendus : {qualite['noms_differents']}. Jambe longue = couverture BTC, jambe courte = jeunes cotations. "
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
