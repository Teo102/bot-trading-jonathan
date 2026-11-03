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


def calculer_concentration_noms(lig: pd.DataFrame, gain_total: float, facteur: str = "BTC") -> tuple[float, str | None]:
    """Part du gain net du meilleur nom parmi les jeunes cotations vendues (hors couverture).

    Règles § 3, § 7 (ebcb777, L11) : "nom" désigne les jeunes cotations vendues, à l'exclusion
    de la couverture BTC. La formule héritée de STRAT-03 intégrait à tort le benchmark de couverture.
    """
    actives = lig[(lig["statut"] != "absent") & (lig["symbole"] != facteur)]
    if actives.empty or gain_total <= 0:
        return float("nan"), None
    g = actives["pnl_prix"] + actives["financement"]
    gains = actives.assign(g=g).groupby("symbole")["g"].sum()
    if gains.empty:
        return float("nan"), None
    return float(gains.max() / gain_total), str(gains.idxmax())


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
    part_max_nom, nom_max = calculer_concentration_noms(lig, mt["rendement_net_total_brut100"], pc.facteur)
    mt["part_max_nom_du_gain"] = part_max_nom
    mt["nom_max"] = nom_max
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
    md = r3.rapport_md(essai, mt, meta).replace("STRAT-20261031-03", "STRAT-20261102-06").replace("porte que sur E25", "porte que sur E19/E20")
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


# ---------------------------------------------------------------- variantes E03 à E18 (03/11/2026)

ESSAIS_BASE = ("E01", "E02")
CONTROLE = "CDV"  # contrôle de reproduction de la base sur dév. + val., hors registre, non compté dans N


def metriques_completes(sem, lig, btc, c6, pc, notionnel) -> dict:
    mt = r3.metriques(sem, lig, btc, c6)
    part, nom = calculer_concentration_noms(lig, mt["rendement_net_total_brut100"], pc.facteur)
    mt["part_max_nom_du_gain"], mt["nom_max"] = part, nom
    actives = lig[lig["statut"] != "absent"]
    mt["esperance_par_ligne_R_notionnel"] = (float(mt["rendement_net_total_brut100"] / len(actives) / (r3.DISTANCE_R * notionnel))
                                             if len(actives) else float("nan"))
    mt["portes_internes"] = portes_internes(mt)
    return mt


def executer_variante(essai: str, source, c6=None, c3=None, registre: Path = REGISTRE, sorties: Path = SORTIES, symboles=None,
                      debut_donnees: pd.Timestamp = DEBUT_DONNEES, exiger_non_coin: bool = True, variantes: dict | None = None) -> dict:
    """E03 à E18 sur dév. + val. (238 semaines), ou CDV : la base sur le même bloc, comparée à E01 et E02, sans registre."""
    import variantes06 as v6
    if c6 is None:
        c6, c3 = charger_configs()
    if c6.get("statut_regles") != "figees" or c3.get("statut_regles") != "figees":
        raise r3.Refus("Règles de STRAT-06 ou infrastructure de STRAT-03 non figées. Aucun essai lancé.")
    if exiger_non_coin and not (ICI / "exclusions_non_coin.json").exists():
        raise r3.Refus("exclusions_non_coin.json absent : aucun essai.")
    d = variantes if variantes is not None else v6.charger_variantes()
    p_base, pc_base = r3.params_depuis(c3), params_cotation(c6, c3)
    controle = essai == CONTROLE
    if controle:
        for e in ESSAIS_BASE:
            if not v6.ligne_registre(e, registre)["date"].strip():
                raise r3.Refus(f"Contrôle de reproduction refusé : {e} n'est pas encore lancé.")
        v = {"variante": "base (controle de reproduction, hors registre)"}
    else:
        v = v6.valider(essai, d, registre, pc_base, p_base)
    pc, p, sp = v6.params_variante(v, pc_base, p_base, c3["exclusions"]["memecoins_liste_close_2026-11-01"])
    if not controle:
        v6.verifier_couts_registre(essai, registre, p)
    bloc = d["bloc"]
    dates = v6.dates_bloc(bloc, sp["calendrier"])
    fin = db.naif(bloc["fin_donnees_prix"])
    nt = v6.notionnel(pc)
    syms = symboles or db.symboles_usdt(source)
    comblement: dict = {}
    jours = db.charger_jours(source, syms, debut_donnees, fin, journal=comblement)
    jours = {k: x.rename(columns={"BTCUSDT": "BTC"}) for k, x in jours.items()}
    jc, _, _, dernier = m.couper_zombies(jours, {}, None)
    exclus_e16: dict = {}

    def cible():
        return v6.fabrique_cible_variante(pc, debut_donnees, dernier, sp["filtre_anticipe_delistage_j"], fin, exclus_e16)
    f0 = cible()
    choix = {t: f0(jc, t, p)[0] for t in dates[:-1]}
    noms = sorted({s for x in choix.values() for s in x if s != "BTC"} | {"BTCUSDT"})
    heures, fin_df, qualite = db.charger_heures(source, noms, dates[0] - pd.Timedelta(days=1), fin, journal=comblement)
    btc = r3.rendements_btc(heures, dates)
    ren = {"BTCUSDT": "BTC"}
    heures = {k: x.rename(columns=ren) for k, x in heures.items()}
    fin_df = fin_df.rename(columns=ren)
    utiles = ["BTC"] + [s for s in noms if s != "BTCUSDT"]
    heures = {k: x.reindex(columns=utiles) for k, x in heures.items()}
    qualite["comblement"] = {n: {"symboles": len(x), "jours_combles": sum(len(y["jours_comble"]) for y in x.values()),
                                 "jours_introuvables": sum(len(y["jours_introuvables"]) for y in x.values())}
                             for n, x in comblement.items()}
    qualite["sans_archive_1h"] = sorted(set(utiles) - set(heures["open"].dropna(axis=1, how="all").columns))
    qualite["noms_differents"] = len(noms) - 1
    sem, lig = m.backtest(jours, heures, fin_df, dates, p, notionnel=nt, fonction_cible=cible())
    if lig.empty:
        raise r3.Refus("Aucune ligne jouée sur le bloc : vérifier les données avant tout verdict.")
    mt = metriques_completes(sem, lig, btc, c6, pc, nt)
    mt["sous_blocs"] = {}
    for nom_b, (s_b, l_b) in v6.decouper(sem, lig, bloc["coupure_sous_blocs"]).items():
        if len(s_b) > 2 and not l_b.empty:
            mt["sous_blocs"][nom_b] = metriques_completes(s_b, l_b, btc, c6, pc, nt)
    h = r3.horo()
    meta = {"horodatage": h, "essai": essai, "bloc": bloc["nom"], "calendrier": sp["calendrier"],
            "premier_lundi": str(dates[0].date()), "dernier_lundi": str(dates[-2].date()), "fin_donnees": bloc["fin_donnees_prix"],
            "variante": v["variante"], "surcharges": {k: v.get(k, {}) for k in ("cotation", "moteur", "special")},
            "notionnel_par_ligne": nt, "exclusions_anticipees_e16": exclus_e16,
            "empreinte": db.empreinte({**{f"j_{k}": x for k, x in jours.items()}, **{f"h_{k}": x for k, x in heures.items()}}),
            "config06_sha256": hashlib.sha256(json.dumps(c6, sort_keys=True).encode()).hexdigest(),
            "config03_sha256": hashlib.sha256(json.dumps(c3, sort_keys=True).encode()).hexdigest(),
            "variantes_sha256": hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest(),
            "qualite": qualite, "incidents": len(getattr(source, "incidents", [])), "appels": getattr(source, "appels", None)}
    sorties.mkdir(exist_ok=True)
    prefixe = "CDV_controle_reproduction" if controle else essai
    md = r3.rapport_md(essai, mt, meta).replace("STRAT-20261031-03", "STRAT-20261102-06").replace("porte que sur E25", "porte que sur E19/E20")
    if sp["calendrier"] != "lundi":
        md = md.replace(", lundis ", f", {sp['calendrier']}s ")
    md += (f"\nVariante : {v['variante']}. Surcharges : {json.dumps(meta['surcharges'], ensure_ascii=False)}. "
           f"Notionnel par ligne : {nt:.4f}. Commentaire du registre : {v.get('commentaire_registre', '')}.\n")
    if sp["filtre_anticipe_delistage_j"]:
        md += f"Filtre anticipé E16 : {len(exclus_e16)} dates avec au moins un nom retiré, {sum(len(x) for x in exclus_e16.values())} retraits.\n"
    md += "\n| Sous-bloc | Semaines | Net brut 100 % | Sharpe | Alpha annualisé | DD | Nom max | Mois max | Portes net, alpha, nom, mois, DD |\n|---|---:|---:|---:|---:|---:|---:|---:|---|\n"
    for nom_b, x in [("total", mt)] + list(mt["sous_blocs"].items()):
        pi = x["portes_internes"]
        md += (f"| {nom_b} | {x['semaines']} | {x['rendement_net_total_brut100']:+.2%} | {x['sharpe_net_annualise']:.3f} | "
               f"{x['alpha_annualise_residuel']:+.2%} | {-x['drawdown_max_brut100']:+.2%} | {x['part_max_nom_du_gain']:.1%} ({x['nom_max']}) | "
               f"{x['part_max_mois_du_gain']:.1%} | {pi['rendement_net_positif']}, {pi['alpha_positif']}, {pi['concentration_nom_ok']}, "
               f"{pi['concentration_mois_ok']}, {pi['drawdown_brut100_ok']} |\n")
    md += ("\nPortes de groupe (fiche § 7) : 9 voisins sur 11 rentables (E03 à E12, E14), E16 et E17 > 0, E18 < 0. "
           "E13 et E18 ne sont jamais éligibles. Résultat de recherche, aucun ordre.\n")
    if controle:
        md += comparer_reproduction(sem, sorties)
    (sorties / f"{prefixe}_metriques.json").write_text(json.dumps({"meta": meta, "metriques": mt}, ensure_ascii=False, indent=1, default=str))
    (sorties / f"{prefixe}_metriques.md").write_text(md)
    sem.to_csv(sorties / f"{prefixe}_semaines.csv", index=False)
    lig.to_csv(sorties / f"{prefixe}_lignes.csv", index=False)
    if not controle:
        r3.ecrire_registre(essai, mt, h, registre)
    return {"meta": meta, "metriques": mt, "rapport": md}


def comparer_reproduction(sem: pd.DataFrame, sorties: Path, tolerance: float = 1e-9) -> str:
    """Compare semaine par semaine la base continue sur dév. + val. à E01 et E02. Écart admis : semaines de jonction
    (dernière de E01, première de E02) et dernière semaine (solde final). Tout autre écart arrête le train."""
    sources = [sorties / f"{e}_semaines.csv" for e in ESSAIS_BASE]
    if not all(x.exists() for x in sources):
        return "\nComparaison impossible : E01_semaines.csv ou E02_semaines.csv absent.\n"
    ref = pd.concat([pd.read_csv(x) for x in sources], ignore_index=True)
    a = sem.assign(lundi=pd.to_datetime(sem["lundi"])).set_index("lundi")["net"]
    b = ref.assign(lundi=pd.to_datetime(ref["lundi"])).set_index("lundi")["net"]
    commun = a.index.intersection(b.index)
    ecarts = (a.reindex(commun) - b.reindex(commun)).abs()
    admis = {pd.Timestamp("2024-06-24"), pd.Timestamp("2024-07-01"), a.index.max()}
    hors = ecarts[(ecarts > tolerance) & ~ecarts.index.isin(list(admis))]
    verdict = "REPRODUCTION CONFORME" if hors.empty and len(commun) == len(a) == len(b) else "ECART : ARRET DU TRAIN"
    return (f"\n## Contrôle de reproduction\n\nSemaines comparées : {len(commun)} (base continue {len(a)}, E01 + E02 {len(b)}). "
            f"Écart maximal hors semaines admises : {hors.max() if not hors.empty else 0:.2e}, sur {len(hors)} semaines. "
            f"Écart sur les semaines admises : {ecarts[ecarts.index.isin(list(admis))].to_dict()}. Verdict : **{verdict}**.\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    a = ap.parse_args(argv)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    try:
        out = executer(a.essai, source) if a.essai in ESSAIS_BASE else executer_variante(a.essai, source)
    except r3.Refus as e:
        print(f"REFUS : {e}", file=sys.stderr)
        return 2
    print(out["rapport"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
