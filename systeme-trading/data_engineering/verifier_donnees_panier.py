#!/usr/bin/env python3
"""Contrôle et coupe des données freqtrade du panier, sans réseau.

freqtrade 2026.10 garde les lots entiers renvoyés par l'API et dépasse donc la
fin demandée (constaté sur BTC, bougies 1 j jusqu'au 04/02/2025 pour une fin au
30/06/2024). Ce script consigne pour chaque paire et chaque type de données la
date réelle de début et la fin brute, puis coupe les fichiers à la fin de fenêtre
pour que rien ne déborde sur les blocs de validation des stratégies.

Usage : python verifier_donnees_panier.py PANIER_CSV SORTIE_CSV
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "user_data" / "data" / "binance" / "futures"
FIN = pd.Timestamp("2024-06-30 23:59:59", tz="UTC")
TYPES = {"1d-futures": pd.Timedelta(days=1), "1h-mark": pd.Timedelta(hours=1), "1h-funding_rate": None}


def main(panier_csv: str, sortie_csv: str) -> int:
    panier = pd.read_csv(panier_csv)
    lignes = []
    for _, p in panier.iterrows():
        nom = p["paire_freqtrade"].replace("/", "_").replace(":", "_")
        for suffixe, pas in TYPES.items():
            f = DONNEES / f"{nom}-{suffixe}.feather"
            l = {"paire": p["paire_freqtrade"], "type": suffixe, "listing_binance": p["listing_binance"]}
            if not f.exists():
                l["statut"] = "fichier absent"
                lignes.append(l)
                continue
            d = pd.read_feather(f)
            l["debut_reel"] = d["date"].min().strftime("%Y-%m-%d %H:%M")
            l["fin_brute"] = d["date"].max().strftime("%Y-%m-%d %H:%M")
            l["lignes_brutes"] = len(d)
            coupe = d[d["date"] <= FIN].reset_index(drop=True)
            l["lignes_apres_coupe"] = len(coupe)
            l["fin_apres_coupe"] = coupe["date"].max().strftime("%Y-%m-%d %H:%M") if len(coupe) else None
            ecarts = coupe["date"].diff().dropna()
            attendu = pas if pas is not None else (ecarts.median() if len(ecarts) else None)
            l["intervalle_median"] = str(ecarts.median()) if len(ecarts) else None
            l["trous"] = int((ecarts > attendu).sum()) if attendu is not None else None
            l["plus_grand_trou"] = str(ecarts.max()) if len(ecarts) else None
            if len(coupe) < len(d):
                temp = f.with_suffix(".tmp")
                coupe.to_feather(temp, compression_level=9, compression="lz4")
                temp.replace(f)
                l["statut"] = "coupé à la fin de fenêtre"
            else:
                l["statut"] = "sans dépassement"
            lignes.append(l)
    sortie = pd.DataFrame(lignes)
    sortie.to_csv(sortie_csv, index=False, encoding="utf-8")
    print(sortie.to_string())
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
