#!/usr/bin/env python3
"""Collecte en avant des cotations d'options BTC de Deribit pour H34 (prime de variance à risque défini).

Lancée le 23/11/2026 sur accord de Jonathan et Téo. Collecte de données seulement : aucun rendement calculé, aucune
prime de variance mesurée, aucun ordre, aucune clé. Source publique : www.deribit.com/api/v2/public.

Chaque passage (prévu toutes les heures) écrit un instantané :
- options BTC d'échéance ≤ 45 jours et de prix d'exercice entre 0,5 et 1,6 fois l'indice (zone des strangles et de
  leurs ailes), avec achat, vente, marque, volatilité implicite de marque, sous-jacent, intérêt ouvert et volume ;
- l'indice btc_usd à l'heure de l'instantané.
Fichier quotidien compressé en ajout seul (`cotations_AAAA-MM-JJ.csv.gz`, un membre gzip par instantané) et journal des
passages (`journal_collecte.csv` : heure, nombre de lignes, empreinte SHA-256 de la réponse brute). Arrêt propre si
le disque libre passe sous 300 Mo.

Usage : python -I -B collecte_deribit34.py --sorties /root/options34_data
"""
import argparse, csv, datetime as dt, gzip, hashlib, io, json, shutil, time
from pathlib import Path
import requests

API = "https://www.deribit.com/api/v2/public"
ECHEANCE_MAX_J, BORNE_BASSE, BORNE_HAUTE, DISQUE_MIN_MO = 45, 0.5, 1.6, 300
MOIS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}
COLONNES = ["utc", "instrument", "echeance_utc", "jours", "prix_exercice", "type", "achat_btc", "vente_btc", "marque_btc",
            "iv_marque", "sous_jacent", "sous_jacent_nom", "indice", "interet_ouvert", "volume", "creation_utc"]


def lire_instrument(nom):
    """BTC-26MAR27-40000-C → (échéance à 08:00 UTC, prix d'exercice, type)."""
    _, d, k, t = nom.split("-")
    jour, mois, an = int(d[:-5]), MOIS[d[-5:-2]], 2000 + int(d[-2:])
    return dt.datetime(an, mois, jour, 8, tzinfo=dt.timezone.utc), float(k), t


def filtrer(resume, indice, maintenant):
    lignes = []
    for x in resume:
        try:
            ech, k, t = lire_instrument(x["instrument_name"])
        except (ValueError, KeyError):
            continue
        jours = (ech - maintenant).total_seconds() / 86400
        if not (0 < jours <= ECHEANCE_MAX_J) or not (BORNE_BASSE * indice <= k <= BORNE_HAUTE * indice):
            continue
        lignes.append({"utc": maintenant.strftime("%Y-%m-%dT%H:%M:%SZ"), "instrument": x["instrument_name"],
                       "echeance_utc": ech.strftime("%Y-%m-%dT%H:%M:%SZ"), "jours": round(jours, 4), "prix_exercice": k, "type": t,
                       "achat_btc": x.get("bid_price"), "vente_btc": x.get("ask_price"), "marque_btc": x.get("mark_price"),
                       "iv_marque": x.get("mark_iv"), "sous_jacent": x.get("underlying_price"), "sous_jacent_nom": x.get("underlying_index"),
                       "indice": indice, "interet_ouvert": x.get("open_interest"), "volume": x.get("volume"),
                       "creation_utc": dt.datetime.fromtimestamp(x["creation_timestamp"] / 1000, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                       if x.get("creation_timestamp") else ""})
    return sorted(lignes, key=lambda l: (l["echeance_utc"], l["prix_exercice"], l["type"]))


def ecrire(sorties, lignes, maintenant, empreinte, n_brut):
    sorties = Path(sorties)
    sorties.mkdir(parents=True, exist_ok=True)
    f = sorties / f"cotations_{maintenant:%Y-%m-%d}.csv.gz"
    neuf = not f.exists()
    tampon = io.StringIO()
    w = csv.DictWriter(tampon, fieldnames=COLONNES)
    if neuf:
        w.writeheader()
    w.writerows(lignes)
    with gzip.open(f, "at", newline="") as g:          # un membre gzip de plus : ajout seul
        g.write(tampon.getvalue())
    j = sorties / "journal_collecte.csv"
    neuf_j = not j.exists()
    with j.open("a", newline="") as h:
        wj = csv.writer(h)
        if neuf_j:
            wj.writerow(["utc", "options_recues", "lignes_ecrites", "sha256_reponse", "fichier"])
        wj.writerow([maintenant.strftime("%Y-%m-%dT%H:%M:%SZ"), n_brut, len(lignes), empreinte, f.name])
    return f


def get(session, chemin, params):
    for essai in range(5):
        try:
            r = session.get(f"{API}/{chemin}", params=params, timeout=30)
            if r.status_code == 200:
                return r.content
        except requests.exceptions.RequestException:
            pass
        time.sleep(3 + 5 * essai)
    raise RuntimeError(f"Deribit injoignable : {chemin}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sorties", required=True)
    a = ap.parse_args()
    libre = shutil.disk_usage(Path(a.sorties).parent if Path(a.sorties).exists() else "/").free / 1e6
    if libre < DISQUE_MIN_MO:
        raise SystemExit(f"arrêt : disque libre {libre:.0f} Mo < {DISQUE_MIN_MO} Mo")
    s = requests.Session()
    maintenant = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    brut = get(s, "get_book_summary_by_currency", {"currency": "BTC", "kind": "option"})
    indice = json.loads(get(s, "get_index_price", {"index_name": "btc_usd"}))["result"]["index_price"]
    resume = json.loads(brut)["result"]
    lignes = filtrer(resume, indice, maintenant)
    f = ecrire(a.sorties, lignes, maintenant, hashlib.sha256(brut).hexdigest(), len(resume))
    print(json.dumps({"utc": maintenant.strftime("%Y-%m-%dT%H:%M:%SZ"), "options_recues": len(resume), "lignes": len(lignes),
                      "fichier": f.name, "disque_libre_mo": round(libre)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
