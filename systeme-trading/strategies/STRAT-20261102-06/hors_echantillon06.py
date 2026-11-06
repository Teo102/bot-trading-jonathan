"""Hors échantillon de STRAT-20261102-06 : E19 (base) puis E20 (coûts doublés), une seule fois chacun (fiche § 6, § 7).

Bloc et critères repris du registre gelé (ebcb777) et du § 7 de la fiche. Les points que la fiche laisse ouverts
(glissement au stop de E20, risque prévu du critère de drawdown, critère de 0,2 R, lectures descriptives) sont écrits
dans `hors_echantillon_strat06.json` et doivent être tranchés par une décision écrite **avant** E19 : le lanceur refuse
tant que `decision_ecrite` est vide ou que l'empreinte enregistrée ne correspond plus.

Enregistrer l'empreinte après la décision : python3 -B hors_echantillon06.py --enregistrer
Sans réseau dans ce module, sans clé, sans ordre. Résultat de recherche.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import run_essai06 as r6  # noqa: E402
import variantes06 as v6  # noqa: E402

SPEC = ICI / "hors_echantillon_strat06.json"
Refus = r6.r3.Refus


def charger_spec(chemin: Path = SPEC, exiger_decision: bool = True) -> dict:
    temoin = chemin.with_name(chemin.name + ".sha256")
    if not temoin.exists():
        raise Refus(f"{temoin.name} absent : enregistrer l'empreinte après la décision écrite.")
    if temoin.read_text().split()[0] != hashlib.sha256(chemin.read_bytes()).hexdigest():
        raise Refus("hors_echantillon_strat06.json modifié après l'enregistrement de son empreinte : refus.")
    d = json.loads(chemin.read_text())
    if exiger_decision and not str(d.get("decision_ecrite", "")).strip():
        raise Refus("decision_ecrite vide : les points ouverts (CS5, glissement au stop de E20, risque prévu, lectures) "
                    "doivent être tranchés par écrit avant E19.")
    if exiger_decision:
        for k, x in d.get("points_ouverts", {}).items():
            if str(x.get("statut", "")) != "tranche":
                raise Refus(f"Point ouvert « {k} » non tranché.")
    return d


def valider(essai: str, d: dict, registre: Path) -> dict:
    if essai not in d["essais"]:
        raise Refus(f"{essai} n'est pas un essai hors échantillon.")
    r = v6.ligne_registre(essai, registre)
    if r["date"].strip():
        raise Refus(f"{essai} déjà lancé le {r['date']}. Le hors échantillon ne se lance qu'une fois.")
    if "hors echantillon" not in r["bloc"].lower():
        raise Refus(f"{essai} : bloc du registre « {r['bloc']} », pas hors échantillon.")
    if r["variante"] != d["essais"][essai]["variante"]:
        raise Refus(f"{essai} : libellé du registre « {r['variante']} » différent de la spécification.")
    if r["timerange"] != d["bloc"]["timerange_registre"]:
        raise Refus(f"{essai} : période du registre {r['timerange']} différente de la spécification.")
    if essai == "E20" and not v6.ligne_registre("E19", registre)["date"].strip():
        raise Refus("E20 ne se lance qu'après E19.")
    n = len(v6.dates_bloc(d["bloc"])) - 1
    if str(n) != r["semaines"].strip():
        raise Refus(f"{essai} : {n} semaines calculées, {r['semaines']} au registre.")
    return {"variante": d["essais"][essai]["variante"], "moteur": d["essais"][essai].get("moteur", {}),
            "commentaire_registre": r["commentaire"]}


def part_financement_paye(lig: pd.DataFrame, notionnel: float, seuil: float = 0.10, facteur: str = "BTC") -> float:
    x = lig[(lig["statut"] != "absent") & (lig["symbole"] != facteur)].copy()
    if x.empty:
        return float("nan")
    jours = (pd.to_datetime(x["t_sortie"]) - (pd.to_datetime(x["lundi"]) + pd.Timedelta(hours=1))).dt.total_seconds() / 86400
    f = x["financement"] / notionnel / jours.clip(lower=1 / 24) * 365
    return float((f < -seuil).mean())


def verdict_e19(mt: dict, crit: dict, lignes_shorts: int) -> dict:
    net = mt["rendement_net_total_brut100"]
    dd_prevu = mt["drawdown_max_brut100"] * crit["exposition_brute_prevue"]
    portes = {
        "sharpe_sup_seuil": mt["sharpe_net_annualise"] > crit["sharpe_min"],
        "ic90_bas_positif": mt["ic90_moyenne_hebdo_blocs"][0] > crit["ic90_bas_min"],
        "alpha_btc_positif": mt["alpha_hebdo_residuel"] > crit["alpha_min"],
        "drawdown_au_risque_prevu": dd_prevu < crit["dd_max_au_risque_prevu"],
        "semaines_avec_position": (mt["semaines"] - mt["semaines_vides"]) >= crit["semaines_avec_position_min"],
        "lignes": lignes_shorts >= crit["lignes_min"],
        "concentration_nom": bool(net > 0 and mt["part_max_nom_du_gain"] <= crit["part_nom_max"]),
        "concentration_mois": bool(net > 0 and mt["part_max_mois_du_gain"] <= crit["part_mois_max"]),
    }
    return {"portes": {k: bool(v) for k, v in portes.items()}, "drawdown_au_risque_prevu": dd_prevu,
            "toutes_franchies": bool(all(portes.values()))}


def executer_hors_echantillon(essai: str, source, c6=None, c3=None, registre: Path = r6.REGISTRE, sorties: Path = r6.SORTIES,
                              symboles=None, debut_donnees: pd.Timestamp = r6.DEBUT_DONNEES, exiger_non_coin: bool = True,
                              spec: dict | None = None) -> dict:
    d = spec if spec is not None else charger_spec()
    v = valider(essai, d, registre)
    out = r6.executer_variante(essai, source, c6, c3, registre, sorties, symboles, debut_donnees, exiger_non_coin,
                               variantes=d, definition=v)
    mt, meta = out["metriques"], out["meta"]
    lig = pd.read_csv(sorties / f"{essai}_lignes.csv")
    nt = meta["notionnel_par_ligne"]
    shorts = int(((lig["statut"] != "absent") & (lig["symbole"] != "BTC")).sum())
    mt["descriptif"] = {"part_shorts_payant_plus_10pct_an": part_financement_paye(lig, nt),
                        "lignes_shorts": shorts, "semaines_avec_position": mt["semaines"] - mt["semaines_vides"]}
    crit = d["criteres"]
    md = out["rapport"] + f"\nSpécification hors échantillon : décision « {d.get('decision_ecrite', '')} ».\n"
    if essai == "E19":
        vd = verdict_e19(mt, crit, shorts)
        mt["verdict_e19"] = vd
        md += ("\n## Portes du hors échantillon (fiche § 7), E19\n\n| Porte | Résultat |\n|---|---|\n"
               + "".join(f"| {k} | {'franchie' if ok else 'ÉCHEC'} |\n" for k, ok in vd["portes"].items())
               + f"\nDrawdown à brut 100 % : {mt['drawdown_max_brut100']:.2%} ; au risque prévu "
                 f"({crit['exposition_brute_prevue']:.1%} d'exposition brute) : {vd['drawdown_au_risque_prevu']:.2%}.\n"
               + f"Sharpe {mt['sharpe_net_annualise']:.3f} contre seuil {crit['sharpe_min']}. Reste la porte E20 > 0.\n")
    else:
        e19 = json.loads((sorties / "E19_metriques.json").read_text())["metriques"]
        ok20 = mt["rendement_net_total_brut100"] > 0
        final = bool(e19["verdict_e19"]["toutes_franchies"] and ok20)
        mt["verdict_final"] = {"e19_toutes_franchies": e19["verdict_e19"]["toutes_franchies"], "e20_net_positif": bool(ok20),
                               "verdict": "papier autorise sous conditions CS4 à CS7" if final else "rejetee"}
        md += (f"\n## Verdict hors échantillon\n\nE20 net > 0 : {'franchie' if ok20 else 'ÉCHEC'}. "
               f"E19 toutes portes : {e19['verdict_e19']['toutes_franchies']}. **Verdict : {mt['verdict_final']['verdict']}.**\n")
    md += (f"\nLecture descriptive (non éliminatoire) : part des shorts payant plus de 10 %/an de financement "
           f"{mt['descriptif']['part_shorts_payant_plus_10pct_an']:.1%} (2021-2025 : 15,5 % ; 2025 : 35,6 %).\n")
    (sorties / f"{essai}_metriques.json").write_text(json.dumps({"meta": meta, "metriques": mt}, ensure_ascii=False, indent=1, default=str))
    (sorties / f"{essai}_metriques.md").write_text(md)
    out["rapport"] = md
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enregistrer", action="store_true", help="enregistre l'empreinte de la spécification (après décision)")
    a = ap.parse_args(argv)
    if a.enregistrer:
        d = json.loads(SPEC.read_text())
        if not str(d.get("decision_ecrite", "")).strip():
            print("REFUS : decision_ecrite vide.", file=sys.stderr)
            return 2
        h = hashlib.sha256(SPEC.read_bytes()).hexdigest()
        SPEC.with_name(SPEC.name + ".sha256").write_text(h + "  " + SPEC.name + "\n")
        print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
