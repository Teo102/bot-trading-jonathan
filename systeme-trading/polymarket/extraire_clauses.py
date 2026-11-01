#!/usr/bin/env python3
"""Extraction des clauses de résolution des marchés du collecteur CLOB (Gamma, lecture publique).

Recherche uniquement. Aucun ordre, aucune clé, aucune lecture de .env ou secrets/.
Sorties, dans polymarket/resultats/ :
  <horodatage>_clauses.json   texte réel des règles, champs UMA et repères mécaniques par marché
  <horodatage>_delais.csv     mesure des délais et des contestations sur des marchés résolus
  <horodatage>_delais.json    agrégats de cette mesure, avec l'état officiel /v2/resolutions de la Data API

Les repères mécaniques ne notent rien : ils signalent seulement les mots à relire à la main.
La note de chaque marché est posée à la main dans REGISTRE_MARCHES_UMA.md.

Usage :
  extraire_clauses.py --prefixe 20261031T224031Z
  extraire_clauses.py --prefixe 20261031T224031Z --delais --delais-jours 180 --delais-max 3000
"""
import argparse
import csv
import json
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

GAMMA = "https://gamma-api.polymarket.com"
DATA = "https://data-api.polymarket.com"
ICI = Path(__file__).resolve().parent
RESULTATS = ICI / "resultats"
UA = {"User-Agent": "systeme-trading-recherche/1.0 (lecture publique)"}

CHAMPS_MARCHE = [
    "id", "question", "conditionId", "slug", "endDate", "umaEndDate", "closedTime", "resolutionSource", "description",
    "umaBond", "umaReward", "customLiveness", "umaResolutionStatus", "umaResolutionStatuses", "resolvedBy", "questionID",
    "negRisk", "negRiskMarketID", "negRiskOther", "negRiskRequestID", "groupItemTitle", "fallbackResolutionType",
    "resolutionMechanism", "restricted", "active", "closed", "acceptingOrders", "tradingEligible", "version", "bestBid", "bestAsk",
    "outcomePrices", "volumeNum", "createdAt", "updatedAt", "automaticallyResolved",
]
CHAMPS_EVENEMENT = ["id", "title", "slug", "description", "resolutionSource", "endDate", "startTime", "negRisk", "negRiskAugmented", "volume", "commentCount"]

# Repères de relecture. Un repère présent signale un mot à lire en contexte, pas un défaut.
REPERES = {
    "officiellement": r"\bofficial(?:ly)?\b",
    "annonce": r"\bannounc\w*",
    "confirmation": r"\bconfirm\w*",
    "consensus_presse": r"credible report\w*|consensus of",
    "source_primaire_citee": r"\bprimary (?:resolution )?source\b|resolution source",
    "date_publication": r"\bpublish\w*|\brelease[sd]?\b|\breported\b",
    "fuseau": r"\bET\b|\bEST\b|\bEDT\b|\bUTC\b|\bPT\b|\bPST\b|Eastern",
    "clause_5050": r"50[- ]?50|50/50|\bunknown\b",
    "annulation_autre": r"\bresolve[sd]? to [\"“']?(?:No|Other|the [\"“']?Other)|otherwise|if no\b",
    "recomptage_contentieux": r"\brecount\w*|\bcertif\w*|\blegal challenge\w*|\brunoff\w*|\bcourt\b|\bcontested\b",
    "seuil": r"\babove\b|\bbelow\b|\bat least\b|\bmore than\b|\bfewer than\b|\bgreater than\b|\bless than\b|\bbetween\b|\bor more\b|\bor higher\b",
    "discretion": r"\bat (?:its|the) (?:sole )?discretion\b|\bsolely\b|\bin (?:its|the) judgment\b",
    "repli": r"\bif .{0,60}(?:unavailable|not available|not published|no longer|does not|fails)\b|\bwill be used\b|\bfallback\b",
}


class Client:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(UA)
        self.appels = 0
        self.incidents = []

    def get(self, chemin, params=None, base=GAMMA):
        url = f"{base}{chemin}"
        for essai in range(4):
            self.appels += 1
            try:
                r = self.s.get(url, params=params, timeout=30)
            except requests.RequestException as exc:
                self.incidents.append({"url": url, "params": params, "erreur": repr(exc)})
                time.sleep(1.5 * (essai + 1))
                continue
            if r.status_code == 200:
                return r.json()
            self.incidents.append({"url": url, "params": params, "statut": r.status_code})
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2.0 * (essai + 1))
                continue
            return None
        return None


def maintenant():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def reperes(texte):
    sortie = {}
    for nom, motif in REPERES.items():
        trouve = re.search(motif, texte or "", flags=re.I | re.S)
        sortie[nom] = bool(trouve)
    return sortie


def parse_date(valeur):
    if not valeur:
        return None
    texte = str(valeur).strip().replace(" ", "T").replace("+00", "+00:00") if "T" not in str(valeur) else str(valeur).strip()
    texte = texte.replace("Z", "+00:00")
    if texte.endswith("+00:00:00"):
        texte = texte[:-3]
    try:
        dt = datetime.fromisoformat(texte)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def extraire(prefixe, client):
    lignes = list(csv.DictReader(open(RESULTATS / f"{prefixe}_marches.csv", encoding="utf-8")))
    sortie = []
    for ligne in lignes:
        cid = ligne["condition_id"]
        lu = iso(maintenant())
        brut = client.get("/markets", {"condition_ids": cid})
        if not brut:
            sortie.append({"rang": ligne["rang"], "echantillon": ligne["echantillon"], "condition_id": cid, "lu_utc": lu, "echec": True})
            print(f"ECHEC {cid}", file=sys.stderr)
            continue
        m = brut[0]
        fiche = {k: m.get(k) for k in CHAMPS_MARCHE}
        evts = m.get("events") or [{}]
        fiche["evenement"] = {k: evts[0].get(k) for k in CHAMPS_EVENEMENT}
        fiche["n_evenements"] = len(evts)
        fiche["rang"] = int(ligne["rang"])
        fiche["echantillon"] = ligne["echantillon"]
        fiche["categorie_collecteur"] = ligne["categorie"]
        fiche["mi_mandat"] = ligne["mi_mandat"] == "True"
        fiche["lu_utc"] = lu
        fiche["longueur_regles"] = len(m.get("description") or "")
        fiche["reperes"] = reperes(m.get("description") or "")
        sortie.append(fiche)
        time.sleep(0.12)
    return sortie


def etats_resolution(client, conditions):
    """État de résolution par condition, lu par lots de 20 sur /v2/resolutions."""
    etats = {}
    for i in range(0, len(conditions), 20):
        lot = conditions[i:i + 20]
        rep = client.get("/v2/resolutions", {"condition": ",".join(lot)}, base=DATA)
        for ligne in (rep or {}).get("data", []):
            etats[ligne.get("condition_id")] = ligne
        time.sleep(0.12)
    return etats


def lire_prix(valeur):
    """Convention du schéma : 0 Non, 1e18 Oui, 5e17 égalité, 69 non renseigné. Autre valeur rendue telle quelle."""
    return {"0": "non", "1000000000000000000": "oui", "500000000000000000": "50-50", "69": "vide", None: "absent"}.get(valeur, str(valeur))


def analyser_etats(etats, lignes_contestees, lignes_calmes):
    def bilan(lignes):
        rangs = [etats[x["condition_id"]] for x in lignes if x["condition_id"] in etats]
        issues = Counter()
        for e in rangs:
            issues[(lire_prix(e.get("proposed_price")), lire_prix(e.get("reproposed_price")), lire_prix(e.get("price")))] += 1
        return {
            "lignes": len(lignes), "etats_lus": len(rangs),
            "was_disputed": sum(1 for e in rangs if e.get("was_disputed")),
            "new_version_q": sum(1 for e in rangs if e.get("new_version_q")),
            "extended_review": sum(1 for e in rangs if e.get("extended_review")),
            "final_differ_premiere_proposition": sum(
                1 for e in rangs if lire_prix(e.get("proposed_price")) not in ("vide", "absent") and lire_prix(e.get("price")) not in ("vide", "absent")
                and lire_prix(e.get("proposed_price")) != lire_prix(e.get("price"))),
            "final_50_50": sum(1 for e in rangs if lire_prix(e.get("price")) == "50-50"),
            "statuts": dict(Counter(e.get("status") for e in rangs).most_common()),
            "triplets_premiere_seconde_finale": {" / ".join(k): v for k, v in issues.most_common(12)},
        }
    return {"contestes_selon_gamma": bilan(lignes_contestees), "non_contestes_echantillon": bilan(lignes_calmes)}


def collecter_resolus(client, debut, fin, plafond, tag_id=None):
    """Marchés fermés dont la date de fin tombe dans la fenêtre. Tri par volume décroissant."""
    vus, sortie = set(), []
    for offset in range(0, plafond, 100):
        params = {
            "closed": "true", "limit": 100, "offset": offset, "order": "volumeNum", "ascending": "false",
            "end_date_min": iso(debut), "end_date_max": iso(fin),
        }
        if tag_id:
            params["tag_id"] = tag_id
        rows = client.get("/markets", params)
        if not rows:
            break
        for m in rows:
            cle = m.get("conditionId")
            if cle and cle not in vus:
                vus.add(cle)
                sortie.append(m)
        if len(rows) < 100:
            break
        time.sleep(0.15)
    return sortie


def statuts_de(m):
    statuts = m.get("umaResolutionStatuses")
    if isinstance(statuts, str):
        try:
            statuts = json.loads(statuts)
        except ValueError:
            statuts = [statuts]
    return statuts or []


def ligne_delai(m, perimetre):
    statuts = statuts_de(m)
    fin_prevue, cloture = parse_date(m.get("endDate")), parse_date(m.get("closedTime"))
    heures = round((cloture - fin_prevue).total_seconds() / 3600, 2) if cloture and fin_prevue else None
    conteste = any(str(x).lower() == "disputed" for x in statuts)
    # Indice indirect : le DVM clôt ses tours à 24:00 UTC, et ces marchés ferment peu après. Ce n'est pas une preuve de vote.
    indice_dvm = bool(conteste and cloture and cloture.hour == 0 and statuts[-1:] == ["disputed"])
    return {
        "perimetre": perimetre, "question": m.get("question"), "condition_id": m.get("conditionId"), "volume_usd": m.get("volumeNum"),
        "end_date": m.get("endDate"), "closed_time": m.get("closedTime"), "uma_bond": m.get("umaBond"), "uma_reward": m.get("umaReward"),
        "custom_liveness": m.get("customLiveness"), "statuts_uma": json.dumps(statuts), "conteste": conteste, "indice_dvm": indice_dvm,
        "heures_fin_a_cloture": heures, "cloture_avant_fin": bool(heures is not None and heures < 0),
    }


METHODE_QUANTILE = "interpolation linéaire entre rangs (défaut de numpy)"


def quantile(vals, q):
    """Quantile d'une liste triée, par interpolation linéaire entre rangs."""
    pos = q * (len(vals) - 1)
    bas = int(pos)
    haut = min(bas + 1, len(vals) - 1)
    return vals[bas] + (vals[haut] - vals[bas]) * (pos - bas)


def resume_heures(sous):
    """Délai fin à clôture. Les clôtures avant la date de fin n'ont pas de délai : elles sortent et sont comptées à part."""
    vals = sorted(x["heures_fin_a_cloture"] for x in sous if x["heures_fin_a_cloture"] is not None and x["heures_fin_a_cloture"] >= 0)
    if not vals:
        return {"n": 0, "n_marches": len(sous), "n_exclus": len(sous)}
    return {
        "n": len(vals), "n_marches": len(sous), "n_exclus": len(sous) - len(vals), "methode_quantile": METHODE_QUANTILE,
        "mediane_h": round(quantile(vals, 0.5), 1), "p75_h": round(quantile(vals, 0.75), 1),
        "p90_h": round(quantile(vals, 0.9), 1), "max_h": round(vals[-1], 1),
    }


def agreger(lignes):
    vol = lambda sous: round(sum(float(x["volume_usd"] or 0) for x in sous), 2)
    contestes = [x for x in lignes if x["conteste"]]
    calmes = [x for x in lignes if not x["conteste"]]
    return {
        "marches": len(lignes), "avec_statuts_uma": sum(1 for x in lignes if x["statuts_uma"] != "[]"),
        "contestes": len(contestes), "part_marches_contestes": round(len(contestes) / max(1, len(lignes)), 4),
        "volume_usd": vol(lignes), "volume_conteste_usd": vol(contestes), "part_volume_contestee": round(vol(contestes) / max(1.0, vol(lignes)), 4),
        "indice_dvm": sum(1 for x in lignes if x["indice_dvm"]),
        "delai_sans_contestation": resume_heures(calmes), "delai_contestes": resume_heures(contestes),
        "delai_indice_dvm": resume_heures([x for x in lignes if x["indice_dvm"]]),
        "cautions": dict(Counter(str(x["uma_bond"]) for x in lignes).most_common()),
        "liveness_s": dict(Counter(str(x["custom_liveness"]) for x in lignes).most_common()),
    }


def mesurer_delais(client, jours, plafond, horodatage, tags, echantillon_calme=600):
    fin = maintenant()
    debut = fin - timedelta(days=jours)
    lignes, offsets = [], {}
    for slug in tags:
        info = client.get(f"/tags/slug/{slug}")
        if not info or not info.get("id"):
            offsets[slug] = "étiquette introuvable"
            continue
        bruts = collecter_resolus(client, debut, fin, plafond, tag_id=info["id"])
        offsets[slug] = len(bruts)
        lignes.extend(ligne_delai(m, slug) for m in bruts)
    bruts = collecter_resolus(client, debut, fin, plafond)
    offsets["toutes_categories"] = len(bruts)
    lignes.extend(ligne_delai(m, "toutes_categories") for m in bruts)
    uniques = {}
    for x in lignes:
        if x["perimetre"] != "toutes_categories":
            uniques.setdefault(x["condition_id"], x)
    perimetre = list(uniques.values())
    globales = [x for x in lignes if x["perimetre"] == "toutes_categories"]
    contestes = [x for x in perimetre if x["conteste"]]
    calmes = [x for x in perimetre if not x["conteste"]]
    random.Random(20261031).shuffle(calmes)
    calmes = calmes[:echantillon_calme]
    etats = etats_resolution(client, [x["condition_id"] for x in contestes + calmes])
    for x in lignes:
        e = etats.get(x["condition_id"]) or {}
        x["was_disputed"] = e.get("was_disputed")
        x["prix_proposition_1"], x["prix_proposition_2"], x["prix_final"] = (lire_prix(e.get(k)) for k in ("proposed_price", "reproposed_price", "price"))
        x["heure_cloture_utc"] = parse_date(x["closed_time"]).hour if parse_date(x["closed_time"]) else None
    if lignes:
        with open(RESULTATS / f"{horodatage}_delais.csv", "w", newline="", encoding="utf-8") as f:
            noms = list(dict.fromkeys(k for x in lignes for k in x))
            ecr = csv.DictWriter(f, fieldnames=noms)
            ecr.writeheader()
            ecr.writerows(lignes)
    votes = [x for x in perimetre if x.get("was_disputed")]
    bilan_votes = {
        "n": len(votes), "part_marches": round(len(votes) / max(1, len(perimetre)), 4),
        "volume_usd": round(sum(float(x["volume_usd"] or 0) for x in votes), 2),
        "part_volume": round(sum(float(x["volume_usd"] or 0) for x in votes) / max(1.0, sum(float(x["volume_usd"] or 0) for x in perimetre)), 4),
        "delai": resume_heures(votes),
        "cloture_entre_00h_et_01h_utc": sum(1 for x in votes if x["heure_cloture_utc"] == 0),
        "final_differ_premiere": sum(1 for x in votes if x["prix_proposition_1"] != x["prix_final"]),
        "avec_seconde_proposition": sum(1 for x in votes if x["prix_proposition_2"] not in ("vide", "absent")),
        "final_differ_seconde": sum(1 for x in votes if x["prix_proposition_2"] not in ("vide", "absent") and x["prix_proposition_2"] != x["prix_final"]),
    }
    agregats = {
        "etats_v2": analyser_etats(etats, contestes, calmes), "graine_echantillon_calme": 20261031, "marches_passes_au_vote_was_disputed": bilan_votes,
        "lu_utc": iso(maintenant()), "fenetre_debut": iso(debut), "fenetre_fin": iso(fin), "plafond_par_etiquette": plafond, "lus_par_etiquette": offsets,
        "politique_macro_tech_uniques": agreger(perimetre), "toutes_categories_top_volume": agreger(globales),
        "contestes_perimetre_par_volume": [
            {k: x[k] for k in ("question", "volume_usd", "end_date", "closed_time", "statuts_uma", "heures_fin_a_cloture", "indice_dvm", "uma_bond")}
            for x in sorted((y for y in perimetre if y["conteste"]), key=lambda y: -float(y["volume_usd"] or 0))[:25]
        ],
    }
    with open(RESULTATS / f"{horodatage}_delais.json", "w", encoding="utf-8") as f:
        json.dump(agregats, f, ensure_ascii=False, indent=1)
    return agregats


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prefixe", required=True, help="préfixe des fichiers du collecteur")
    p.add_argument("--delais", action="store_true", help="mesurer aussi les délais sur des marchés résolus")
    p.add_argument("--delais-jours", type=int, default=180)
    p.add_argument("--delais-max", type=int, default=3000, help="plafond de marchés lus par étiquette")
    p.add_argument("--delais-tags", default="politics,economy,tech,ai", help="étiquettes Gamma du périmètre")
    args = p.parse_args()

    client = Client()
    horodatage = maintenant().strftime("%Y%m%dT%H%M%SZ")
    debut = iso(maintenant())
    fiches = extraire(args.prefixe, client)
    etats = etats_resolution(client, [x["conditionId"] for x in fiches if x.get("conditionId")])
    for fiche in fiches:
        fiche["etat_v2"] = etats.get(fiche.get("conditionId"))
    charge = {"debut_utc": debut, "fin_utc": iso(maintenant()), "source": f"{GAMMA}/markets?condition_ids=", "prefixe_collecteur": args.prefixe, "marches": fiches}
    if args.delais:
        agregats = mesurer_delais(client, args.delais_jours, args.delais_max, horodatage, args.delais_tags.split(","))
        print(json.dumps(agregats, ensure_ascii=False, indent=1))
    charge["appels_http"] = client.appels
    charge["incidents"] = client.incidents
    chemin = RESULTATS / f"{horodatage}_clauses.json"
    chemin.write_text(json.dumps(charge, ensure_ascii=False, indent=1), encoding="utf-8")
    echecs = sum(1 for x in fiches if x.get("echec"))
    print(f"{chemin} : {len(fiches)} marchés, {echecs} échecs, {client.appels} appels, {len(client.incidents)} incidents")


if __name__ == "__main__":
    main()
