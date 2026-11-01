#!/usr/bin/env python3
"""STRAT-20261031-04 : demi-écart du carnet autour de chaque signal, SANS AUCUN RENDEMENT.

Source : archive publique bookTicker de data.binance.vision (meilleur achat, meilleur vendeur).
Fenêtres : la bougie signal [T - 15 min, T[ et les 10 minutes qui suivent [T, T + 10 min], comme
dans mesure_carnet_signaux.py. Aucune valeur postérieure à T + 10 min n'est lue.
L'archive quotidienne s'arrête avant la fin de la période : les signaux sans fichier restent vides.

Usage : python mesure_demi_ecart_signaux.py --signaux resultats/signaux_....csv --cache <dossier>
Sortie : resultats/demi_ecart_signaux_<horodatage UTC>.csv et .json
"""
import argparse
import concurrent.futures as cf
import json
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
RES = ICI / "resultats"
VISION = "https://data.binance.vision/data/futures/um/daily/bookTicker"
SES = requests.Session()
SES.headers["User-Agent"] = "recherche-donnees-publiques/1.0"


def telecharger(sym, jour, cache):
    d = cache / sym
    d.mkdir(parents=True, exist_ok=True)
    n = f"{sym}-bookTicker-{jour}.zip"
    c = d / n
    if c.exists():
        return c
    if (d / (n + ".absent")).exists():
        return None
    for i in range(4):
        try:
            with SES.get(f"{VISION}/{sym}/{n}", timeout=300, stream=True) as r:
                if r.status_code == 404:
                    (d / (n + ".absent")).write_text("")
                    return None
                if r.status_code == 200:
                    tmp = d / (n + ".tmp")
                    with open(tmp, "wb") as f:
                        for bloc in r.iter_content(1 << 20):
                            f.write(bloc)
                    tmp.rename(c)
                    return c
        except requests.RequestException:
            pass
        time.sleep(1 + 2 * i)
    return None


def extraire(c, t0_ms, t1_ms):
    """Lignes du fichier entre t0 et t1. Certains fichiers n'ont pas d'en-tête."""
    noms = ["update_id", "bid", "bid_q", "ask", "ask_q", "transaction_time", "event_time"]
    with zipfile.ZipFile(c) as z, z.open(z.namelist()[0]) as f:
        tete = f.readline().decode()
    entete = tete.startswith("update_id")
    parts = []
    with zipfile.ZipFile(c) as z, z.open(z.namelist()[0]) as f:
        for ch in pd.read_csv(f, header=0 if entete else None, names=noms, usecols=["bid", "ask", "event_time"], chunksize=2_000_000):
            ch = ch[(ch.event_time >= t0_ms) & (ch.event_time < t1_ms)]
            if len(ch):
                parts.append(ch)
    return pd.concat(parts) if parts else pd.DataFrame(columns=["bid", "ask", "event_time"])


def demi_ecart_par_seconde(t):
    """Demi-écart en pourcent du milieu, dernière valeur de chaque seconde pour ne pas sur-pondérer les rafales."""
    x = t.assign(sec=(t.event_time // 1000)).sort_values("event_time").groupby("sec").last()
    mid = (x.bid + x.ask) / 2
    return (x.ask - x.bid) / 2 / mid * 100


def mesurer(r, cache):
    T = r["T"]
    d0, d1 = T - timedelta(minutes=15), T + timedelta(minutes=10)
    jours = sorted({d0.date().isoformat(), d1.date().isoformat()})
    ms = lambda x: int(x.timestamp() * 1000)
    parts = []
    for j in jours:
        c = telecharger(r.symbole, j, cache)
        if c is None:
            return {"symbole": r.symbole, "T": T, "fichier_complet": False}
        parts.append(extraire(c, ms(d0), ms(d1)))
    t = pd.concat(parts)
    if t.empty:
        return {"symbole": r.symbole, "T": T, "fichier_complet": False}
    avant = t[t.event_time < ms(T)]
    apres = t[t.event_time >= ms(T)]
    res = {"symbole": r.symbole, "T": T, "fichier_complet": True, "secondes_bougie": 0, "secondes_apres": 0}
    if len(avant):
        h = demi_ecart_par_seconde(avant)
        res.update(secondes_bougie=int(len(h)), demi_ecart_bougie_mediane_pct=float(h.median()),
                   demi_ecart_bougie_q95_pct=float(h.quantile(.95)), demi_ecart_bougie_max_pct=float(h.max()))
    if len(apres):
        h = demi_ecart_par_seconde(apres)
        res.update(secondes_apres=int(len(h)), demi_ecart_entree_mediane_pct=float(h.median()),
                   demi_ecart_entree_q95_pct=float(h.quantile(.95)))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signaux", required=True)
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    debut = datetime.now(timezone.utc)
    stamp = debut.strftime("%Y%m%dT%H%M%SZ")
    v = pd.read_csv(a.signaux, parse_dates=["T"])
    w = v[v["T"] >= pd.Timestamp("2023-01-03", tz="UTC")]
    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda t: mesurer(t[1], cache), w.iterrows()))
    d = pd.DataFrame(res)
    d["classe"] = np.where(d.symbole.isin(["BTCUSDT", "ETHUSDT"]), "BTC_ETH", "autres")
    RES.mkdir(exist_ok=True)
    d.to_csv(RES / f"demi_ecart_signaux_{stamp}.csv", index=False)
    rap = {"debut_utc": debut.isoformat(timespec="seconds"), "fichier_signaux": Path(a.signaux).name,
           "avertissement": "Aucun rendement lu. Fenêtres limitées à T - 15 min et T + 10 min.",
           "signaux": int(len(d)), "signaux_mesures": int(d.fichier_complet.sum()),
           "dernier_signal_mesure": str(d[d.fichier_complet]["T"].max())}
    m = d[d.fichier_complet]
    rap["par_classe"] = {}
    for cl, g in m.groupby("classe"):
        e = {"signaux_mesures": int(len(g))}
        for col in ["demi_ecart_entree_mediane_pct", "demi_ecart_entree_q95_pct", "demi_ecart_bougie_mediane_pct",
                    "demi_ecart_bougie_q95_pct", "demi_ecart_bougie_max_pct"]:
            e[f"{col}_mediane"] = round(float(g[col].median()), 4)
            e[f"{col}_q90"] = round(float(g[col].quantile(.9)), 4)
        rap["par_classe"][cl] = e
    rap["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (RES / f"demi_ecart_signaux_{stamp}.json").write_text(json.dumps(rap, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(rap, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
