#!/usr/bin/env python3
"""Relevé du carnet d'ordres de STRAT-20261119-09 (fiche § 2 et § 5) : écart affiché et profondeur, sans aucun prix
de position ni rendement. Une ligne par contrat et par passage, en ajout seul.

Profondeur = somme des ordres (prix × quantité, en USDT) à moins de 0,1 % et de 0,5 % du milieu, de chaque côté.
Source publique sans clé : fapi.binance.com/fapi/v1/depth (1 000 niveaux).

Usage : python -I -B releve_carnet09.py --univers univers.txt --sortie releve_carnet09.csv --etiquette samedi
"""
import argparse, csv, datetime as dt, time
from pathlib import Path
import requests

FAPI = "https://fapi.binance.com"
TEMOINS = ["BTCUSDT", "ETHUSDT"]
CHAMPS = ["utc", "etiquette", "symbole", "meilleur_achat", "meilleure_vente", "ecart_relatif",
          "achat_0_1pct_usdt", "vente_0_1pct_usdt", "achat_0_5pct_usdt", "vente_0_5pct_usdt", "niveaux_achat", "niveaux_vente"]


def profondeur(niveaux, milieu, seuil, cote):
    return sum(p * q for p, q in niveaux if (milieu - p if cote == "achat" else p - milieu) / milieu <= seuil)


def mesurer(carnet):
    a = [(float(p), float(q)) for p, q in carnet["bids"]]
    v = [(float(p), float(q)) for p, q in carnet["asks"]]
    if not a or not v:
        return None
    milieu = (a[0][0] + v[0][0]) / 2
    return {"meilleur_achat": a[0][0], "meilleure_vente": v[0][0], "ecart_relatif": round(v[0][0] / a[0][0] - 1, 8),
            "achat_0_1pct_usdt": round(profondeur(a, milieu, 0.001, "achat")), "vente_0_1pct_usdt": round(profondeur(v, milieu, 0.001, "vente")),
            "achat_0_5pct_usdt": round(profondeur(a, milieu, 0.005, "achat")), "vente_0_5pct_usdt": round(profondeur(v, milieu, 0.005, "vente")),
            "niveaux_achat": len(a), "niveaux_vente": len(v)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--univers", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--etiquette", default="")
    x = ap.parse_args()
    syms = [l.strip() for l in Path(x.univers).read_text().splitlines() if l.strip()] + TEMOINS
    sortie = Path(x.sortie)
    neuf = not sortie.exists()
    s = requests.Session()
    with sortie.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS)
        if neuf:
            w.writeheader()
        for sym in syms:
            ligne = {"utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "etiquette": x.etiquette, "symbole": sym}
            for essai in range(3):
                try:
                    r = s.get(f"{FAPI}/fapi/v1/depth", params={"symbol": sym, "limit": 1000}, timeout=30)
                    if r.status_code == 200 and (m := mesurer(r.json())):
                        ligne.update(m)
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(3)
            w.writerow(ligne)
            time.sleep(0.5)
    print(sortie, len(syms), "contrats")


if __name__ == "__main__":
    main()
