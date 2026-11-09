#!/usr/bin/env python3
"""Audit Fable, STRAT-08, contrôle A3 : qualité brute des fichiers metrics (intérêt ouvert seulement, aucun prix).

Pour des jours du bloc de développement, des jours de krach connus et les jours de la bascule d'horodatage :
lignes, horodatages distincts, horodatages hors grille de 5 minutes, doublons de valeur différente, points de grille
manquants, valeurs vides, ordre. Le fichier brut est lu sans le lecteur de la stratégie, pour voir ce qu'il masque.

Usage : python3 -B a3_qualite_metrics.py
"""
import io, json, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "NEARUSDT", "ARBUSDT", "SUIUSDT", "1000PEPEUSDT"]
JOURS = ["2021-01-15", "2021-05-19", "2021-09-07", "2021-12-04", "2022-05-12", "2022-11-09", "2023-08-17",
         "2024-03-03", "2024-03-04", "2024-03-05", "2024-08-05", "2025-10-10", "2025-10-11"]


def un(sj):
    sym, j = sj
    for essai in range(5):  # la résolution de nom échoue parfois sous charge : on réessaie
        try:
            r = requests.get(f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{j}.zip", timeout=60)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(2 + essai)
    else:
        raise RuntimeError(f"réseau : {sym} {j}")
    if r.status_code != 200:
        return sym, j, None
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f)
    t = pd.to_datetime(df["create_time"])
    tm = t.dt.round("min")
    grille = pd.date_range(j, periods=288, freq="5min")
    v = pd.to_numeric(df["sum_open_interest"], errors="coerce")
    g = pd.DataFrame({"t": tm, "v": v}).groupby("t")["v"]
    return sym, j, {"lignes": int(len(df)), "horodatages_distincts": int(tm.nunique()),
                    "hors_grille_5min": int((~tm.isin(grille)).sum()),
                    "secondes_non_nulles": int((t.dt.second != 0).sum()),
                    "doublons_valeur_differente": int((g.nunique() > 1).sum()),
                    "grille_manquante": int((~grille.isin(tm)).sum()),
                    "valeurs_vides_ou_nulles": int((v.isna() | (v <= 0)).sum()),
                    "trie": bool(t.is_monotonic_increasing),
                    "premiere": str(t.min()), "derniere": str(t.max())}


with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(un, [(s, j) for s in SYMS for j in JOURS]))
R = {}
print("symbole jour | lignes | distincts | hors grille | sec≠0 | doublons val. diff. | grille manquante | vides | trié | première | dernière")
for sym, j, x in res:
    R[f"{sym} {j}"] = x
    if x is None:
        print(sym, j, "| archive absente")
    elif x["lignes"] != 288 or x["grille_manquante"] or x["hors_grille_5min"] or x["doublons_valeur_differente"] or x["valeurs_vides_ou_nulles"] or not x["trie"]:
        print(sym, j, "|", x["lignes"], "|", x["horodatages_distincts"], "|", x["hors_grille_5min"], "|", x["secondes_non_nulles"], "|",
              x["doublons_valeur_differente"], "|", x["grille_manquante"], "|", x["valeurs_vides_ou_nulles"], "|", x["trie"], "|", x["premiere"], "|", x["derniere"])
propres = sum(1 for _, _, x in res if x and x["lignes"] == 288 and not x["grille_manquante"] and not x["hors_grille_5min"] and not x["doublons_valeur_differente"] and not x["valeurs_vides_ou_nulles"] and x["trie"])
print(f"Fichiers propres (288 lignes, grille complète, triés, sans doublon ni vide) : {propres} sur {len(res)}")
h = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
(ICI / "resultats" / f"a3_qualite_metrics_{h}.json").write_text(json.dumps({"genere_utc": h, "detail": R}, indent=1))
