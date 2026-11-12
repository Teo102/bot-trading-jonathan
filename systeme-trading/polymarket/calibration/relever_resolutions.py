#!/usr/bin/env python3
"""Relève les résolutions des prévisions du journal (mode d'emploi, règle 9). Aucun ordre, lecture publique.

Deux temps, comme `relever_prix.py` :
  1. lire      (machine qui joint l'API) : pour chaque ligne sans issue, lit l'état du marché sur Gamma. N'écrit que les
               marchés clos et résolus. Le prix des marchés encore ouverts n'est ni écrit ni affiché, pour que le
               prévisionniste reste aveugle sur les événements qu'il pourrait reprévoir.
  2. appliquer (dépôt) : remplit issue_resolue, horodatage_resolution_utc, litige et annule des lignes sans issue.
               Ne touche à aucune autre colonne, et jamais à une ligne déjà résolue.
Issue : 1 si le jeton de l'issue évaluée (« Yes », premier jeton) vaut 1 à la clôture, 0 s'il vaut 0, annule = oui à 0,5.
Usage : python3 -B relever_resolutions.py lire JOURNAL.csv resolutions.json
        python3 -B relever_resolutions.py appliquer resolutions.json"""
import csv, datetime as dt, json, sys, time
from pathlib import Path

ICI = Path(__file__).resolve().parent
JOURNAL = ICI / "JOURNAL_CALIBRATION.csv"
GAMMA = "https://gamma-api.polymarket.com"


def _marche(s, cid):
    for extra in ({}, {"closed": "true"}):
        for essai in range(4):
            try:
                r = s.get(f"{GAMMA}/markets", params={"condition_ids": cid, **extra}, timeout=30)
                if r.status_code == 200:
                    for m in r.json():
                        if (m.get("conditionId") or "").lower() == cid.lower():
                            return m
                    break
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1 + essai)
    return None


def lire(journal, sortie):
    import requests
    s = requests.Session()
    lignes = [l for l in csv.DictReader(open(journal, newline="")) if not l["issue_resolue"] and l["annule"] != "oui"]
    out, etats = {}, {"introuvable": 0, "ouvert": 0, "clos_sans_issue": 0, "resolu": 0}
    for l in lignes:
        m = _marche(s, l["condition_id"])
        if m is None:
            etats["introuvable"] += 1; continue
        if not m.get("closed"):
            etats["ouvert"] += 1; continue
        try:
            p = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
        except (TypeError, ValueError):
            p = []
        statut = str(m.get("umaResolutionStatus") or "")
        historique = str(m.get("umaResolutionStatuses") or "")
        base = {"horodatage_resolution_utc": m.get("closedTime") or "", "litige": "oui" if "disput" in (statut + historique).lower() else "non",
                "statut_uma": statut, "lu_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "slug": l["slug"]}
        if len(p) == 2 and p[0] in (0.0, 1.0) and p[0] + p[1] == 1.0:
            out[l["condition_id"]] = {**base, "issue_resolue": int(p[0]), "annule": "non"}; etats["resolu"] += 1
        elif len(p) == 2 and p[0] == 0.5 and p[1] == 0.5:
            out[l["condition_id"]] = {**base, "issue_resolue": "", "annule": "oui"}; etats["resolu"] += 1
        else:
            etats["clos_sans_issue"] += 1   # clos, issue pas encore fixée à 0 ou 1 : on attend
    Path(sortie).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(lignes)} lignes sans issue : {etats}")


def _iso(h: str) -> str:
    """Heure de clôture Gamma (« 2026-11-10 18:03:27.63+00 ») ramenée au format du journal (« 2026-11-10T18:03:27Z »)."""
    try:
        x = h.strip().replace(" ", "T")
        if x.endswith("+00"):
            x += ":00"
        return dt.datetime.fromisoformat(x).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return h


def appliquer(resolutions):
    R = json.loads(Path(resolutions).read_text())
    with JOURNAL.open(newline="") as f:
        r = csv.DictReader(f); colonnes = r.fieldnames; lignes = list(r)
    n = 0
    for l in lignes:
        x = R.get(l["condition_id"])
        if x and not l["issue_resolue"] and l["annule"] != "oui":
            l["issue_resolue"], l["annule"], l["litige"], l["horodatage_resolution_utc"] = x["issue_resolue"], x["annule"], x["litige"], _iso(x["horodatage_resolution_utc"])
            n += 1
    with JOURNAL.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes); w.writeheader(); w.writerows(lignes)
    print(f"{n} lignes complétées par leur résolution")


if __name__ == "__main__":
    {"lire": lire, "appliquer": appliquer}[sys.argv[1]](*sys.argv[2:])
