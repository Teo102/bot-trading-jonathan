#!/usr/bin/env python3
"""Relève le prix du marché APRÈS l'écriture et le commit des prévisions (protocole « estimer sans voir le prix »).

Deux temps, car l'API Polymarket n'est pas joignable de partout :
  1. lire      (machine qui joint l'API) : meilleur achat et meilleure vente du jeton « Yes » sur le carnet CLOB,
                pour chaque ligne du journal sans prix. N'affiche que des comptes.
  2. appliquer (dépôt) : remplit bid, ask, milieu et heure_lecture_prix_utc des lignes sans prix. Ne touche à
                aucune autre colonne, et jamais à une ligne qui a déjà un prix.
Usage : python3 -B relever_prix.py lire JOURNAL.csv candidats.json prix.json
        python3 -B relever_prix.py appliquer prix.json"""
import csv, datetime as dt, json, sys, time
from pathlib import Path

ICI = Path(__file__).resolve().parent
JOURNAL = ICI / "JOURNAL_CALIBRATION.csv"
CLOB = "https://clob.polymarket.com"


def lire(journal, candidats, sortie):
    import requests
    jetons = {m["conditionId"]: json.loads(m["clobTokenIds"])[0] for m in json.loads(Path(candidats).read_text())["candidats"]}
    a_lire = [l["condition_id"] for l in csv.DictReader(open(journal, newline="")) if not l["milieu"]]
    out, manques = {}, 0
    for cid in a_lire:
        b = None
        for essai in range(4):
            try:
                r = requests.get(f"{CLOB}/book", params={"token_id": jetons[cid]}, timeout=20)
                if r.status_code == 200:
                    b = r.json(); break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1 + essai)
        achats = [float(x["price"]) for x in (b or {}).get("bids", [])]
        ventes = [float(x["price"]) for x in (b or {}).get("asks", [])]
        if not achats or not ventes:
            manques += 1; continue
        bid, ask = max(achats), min(ventes)
        assert 0 <= bid <= ask <= 1
        out[cid] = {"bid": bid, "ask": ask, "milieu": round((bid + ask) / 2, 4),
                    "heure_lecture_prix_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    Path(sortie).write_text(json.dumps(out, indent=1))
    print(f"{len(out)} carnets lus, {manques} sans achat ou sans vente, sur {len(a_lire)} lignes sans prix")


def appliquer(prix):
    P = json.loads(Path(prix).read_text())
    with JOURNAL.open(newline="") as f:
        r = csv.DictReader(f); colonnes = r.fieldnames; lignes = list(r)
    n = 0
    for l in lignes:
        if not l["milieu"] and l["condition_id"] in P:
            for k in ("bid", "ask", "milieu", "heure_lecture_prix_utc"):
                l[k] = P[l["condition_id"]][k]
            n += 1
    with JOURNAL.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes); w.writeheader(); w.writerows(lignes)
    print(f"{n} lignes complétées par leur prix ; {sum(1 for l in lignes if not l['milieu'])} restent sans prix")


if __name__ == "__main__":
    {"lire": lire, "appliquer": appliquer}[sys.argv[1]](*sys.argv[2:])
