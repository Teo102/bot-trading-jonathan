#!/usr/bin/env python3
"""Ajoute un lot de prévisions au journal, sans prix (colonnes bid, ask, milieu et heure laissées vides).
Le prix se relève ensuite par `relever_prix.py`, après le commit du lot : l'horodatage Git prouve l'ordre.
Refuse d'écrire une prévision pour un marché déjà présent au journal (une correction est une nouvelle ligne, faite à la main).
Usage : python3 -B saisir_lot.py lots/lot_20261109_previsions.py lots/candidats_sans_prix_20261109T205024Z.json"""
import csv, datetime as dt, importlib.util, json, sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
JOURNAL = ICI / "JOURNAL_CALIBRATION.csv"


def main(lot_py, candidats_json, auteur="Claude"):
    spec = importlib.util.spec_from_file_location("lot", lot_py); lot = importlib.util.module_from_spec(spec); spec.loader.exec_module(lot)
    cands = json.loads(Path(candidats_json).read_text())["candidats"]
    with JOURNAL.open(newline="") as f:
        lignes = list(csv.DictReader(f)); colonnes = list(csv.DictReader(open(JOURNAL, newline="")).fieldnames)
    deja = {l["condition_id"] for l in lignes}
    now = dt.datetime.now(dt.timezone.utc)
    jour = now.strftime("%Y%m%d")
    n = sum(1 for l in lignes if l["id"].startswith(f"CAL-{jour}-"))
    evenements, ajout = set(), []
    for idx, p, cat, grappe, g, base, sources in lot.LOT:
        m = cands[idx]
        assert m["outcomes"] in ('["Yes", "No"]', ["Yes", "No"]), m["outcomes"]
        assert 0.01 <= p <= 0.99 and max(g[0], g[1], g[4]) < 3, (idx, p, g)
        assert m["conditionId"] not in deja and m["evenement_id"] not in evenements, f"doublon {idx}"
        evenements.add(m["evenement_id"]); n += 1
        fin = dt.datetime.fromisoformat(m["endDate"].replace("Z", "+00:00"))
        ajout.append({"id": f"CAL-{jour}-{n:02d}", "horodatage_prevision_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "auteur": auteur,
                      "condition_id": m["conditionId"], "slug": m["slug"], "question": m["question"], "issue_evaluee": "Yes", "categorie": cat,
                      "evenement": m["evenement_slug"] or m["evenement_id"], "date_fin_gamma_utc": m["endDate"], "mi_mandat": "non",
                      "bid": "", "ask": "", "milieu": "", "heure_lecture_prix_utc": "", "proba_propre": f"{p:.3f}".rstrip("0").rstrip("."),
                      "base_de_la_proba": base, "sources": sources, "note_F": g[0], "note_S": g[1], "note_L": g[4], "note_totale_grille": sum(g),
                      "horizon_jours": round((fin - now).total_seconds() / 86400, 1), "issue_resolue": "", "horodatage_resolution_utc": "",
                      "litige": "", "annule": "",
                      "commentaire": "prix non vu à l'écriture ; grille F S A C L V M = " + " ".join(map(str, g)) + (f" ; grappe {grappe}" if grappe else "")})
    with JOURNAL.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes)
        for a in ajout:
            w.writerow(a)
    print(f"{len(ajout)} prévisions ajoutées à {JOURNAL.name} à {now:%Y-%m-%dT%H:%M:%SZ}, sans prix")


if __name__ == "__main__":
    main(*sys.argv[1:3])
