#!/usr/bin/env python3
"""STRAT-20261031-04 : comptage des signaux, SANS AUCUN RENDEMENT.

But unique : dire si l'historique gratuit peut contenir au moins 100 trades avec les règles
figées dans parametres_geles.json. Le script ne lit aucun prix postérieur à la bougie
d'entrée et ne calcule ni gain, ni perte, ni taux de réussite. La seule valeur future lue
est l'ouverture de la bougie 15 min suivante, pour vérifier les annulations d'entrée et
la distance prévue au stop et à l'objectif.

Données : data.binance.vision (metrics 5 min, bougies 15 min, financement), REST public
Binance pour le mois en cours. Cache hors dépôt, passé par --cache.
Sortie : resultats/compte_signaux_<horodatage UTC>.json et signaux_sans_rendement_<...>.csv
"""
import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
RES = ICI / "resultats"
FICHIER_P = ICI / "parametres_geles.json"
P = json.loads(FICHIER_P.read_text())
VISION = "https://data.binance.vision/data/futures/um"
FAPI = "https://fapi.binance.com"
SES = requests.Session()
SES.headers["User-Agent"] = "recherche-donnees-publiques/1.0"
BARRE = pd.Timedelta(minutes=15)
BASCULE_ARCHIVE = pd.Timestamp("2024-03-04", tz="UTC")


def telecharger(url, dest, essais=5):
    """Retourne 'ok', 'absent' ou 'echec'. Un fichier absent est mémorisé par un .absent."""
    if dest.exists():
        return "ok"
    marque = dest.with_suffix(".absent")
    if marque.exists():
        return "absent"
    for i in range(essais):
        try:
            r = SES.get(url, timeout=60)
            if r.status_code == 200:
                tmp = dest.with_suffix(".tmp")
                tmp.write_bytes(r.content)
                tmp.rename(dest)
                return "ok"
            if r.status_code == 404:
                marque.write_text("")
                return "absent"
        except requests.RequestException:
            pass
        time.sleep(1 + i * 2)
    return "echec"


def jours(d0, d1):
    while d0 <= d1:
        yield d0
        d0 += timedelta(days=1)


def mois(d0, d1):
    y, m = d0.year, d0.month
    while (y, m) <= (d1.year, d1.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def lire_zip_csv(chemin):
    with zipfile.ZipFile(chemin) as z:
        with z.open(z.namelist()[0]) as f:
            return pd.read_csv(f)


def collecter(symbol, debut, fin, cache):
    """Télécharge metrics (quotidien), bougies 15m et financement (mensuels)."""
    d = cache / symbol
    d.mkdir(parents=True, exist_ok=True)
    taches = []
    for j in jours(debut, fin):
        n = f"{symbol}-metrics-{j}.zip"
        taches.append((f"{VISION}/daily/metrics/{symbol}/{n}", d / n, "metrics"))
    mois_courant = (fin.year, fin.month)
    for y, m in mois(debut, fin):
        if (y, m) == mois_courant:
            continue
        n = f"{symbol}-15m-{y}-{m:02d}.zip"
        taches.append((f"{VISION}/monthly/klines/{symbol}/15m/{n}", d / n, "klines"))
        n = f"{symbol}-fundingRate-{y}-{m:02d}.zip"
        taches.append((f"{VISION}/monthly/fundingRate/{symbol}/{n}", d / n, "funding"))
    bilan = {}
    with cf.ThreadPoolExecutor(12) as ex:
        res = ex.map(lambda t: (t[2], telecharger(t[0], t[1])), taches)
        for sorte, etat in res:
            bilan.setdefault(sorte, {}).setdefault(etat, 0)
            bilan[sorte][etat] += 1
    return bilan


def get_rest(url, params, essais=5):
    """GET public avec reprises : un délai dépassé isolé ne doit pas perdre tout le comptage."""
    for i in range(essais):
        try:
            r = SES.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == essais - 1:
                raise
            time.sleep(2 + 3 * i)


def rest_klines(symbol, debut_ms, fin_ms):
    lignes = []
    while debut_ms < fin_ms:
        r = get_rest(f"{FAPI}/fapi/v1/klines", {"symbol": symbol, "interval": "15m", "limit": 1500,
                                                "startTime": debut_ms, "endTime": fin_ms})
        d = r.json()
        if not d:
            break
        lignes += d
        debut_ms = d[-1][0] + 900_000
        time.sleep(0.1)
    return pd.DataFrame([[x[0], float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])] for x in lignes],
                        columns=["open_time", "open", "high", "low", "close", "volume"])


def rest_funding(symbol, debut_ms):
    r = get_rest(f"{FAPI}/fapi/v1/fundingRate", {"symbol": symbol, "limit": 1000, "startTime": debut_ms})
    return pd.DataFrame([[x["fundingTime"], float(x["fundingRate"])] for x in r.json()], columns=["t", "f"])


def charger(symbol, debut, fin, cache):
    d = cache / symbol
    # Bougies 15 min. Certains fichiers anciens n'ont pas de ligne d'en-tête.
    k = []
    for y, m in mois(debut, fin):
        c = d / f"{symbol}-15m-{y}-{m:02d}.zip"
        if c.exists():
            with zipfile.ZipFile(c) as z, z.open(z.namelist()[0]) as f:
                t = pd.read_csv(f, header=None, usecols=range(6))
            if str(t.iloc[0, 0]) == "open_time":
                t = t.iloc[1:]
            t.columns = ["open_time", "open", "high", "low", "close", "volume"]
            k.append(t.astype(float))
    debut_mois = int(datetime(fin.year, fin.month, 1, tzinfo=timezone.utc).timestamp() * 1000)
    k.append(rest_klines(symbol, debut_mois, int(time.time() * 1000)))
    kl = pd.concat(k).drop_duplicates("open_time").sort_values("open_time")
    kl["ts"] = pd.to_datetime(kl.open_time.astype("int64"), unit="ms", utc=True)
    kl = kl.set_index("ts")[["open", "high", "low", "close", "volume"]]
    # La bougie du mois en cours encore ouverte est exclue.
    kl = kl[kl.index + BARRE <= pd.Timestamp.now(tz="UTC")]
    # OI 5 min.
    m = []
    fichiers_ok = 0
    for j in jours(debut, fin):
        c = d / f"{symbol}-metrics-{j}.zip"
        if c.exists():
            try:
                t = lire_zip_csv(c)[["create_time", "sum_open_interest"]]
            except (zipfile.BadZipFile, KeyError, ValueError):
                continue
            m.append(t)
            fichiers_ok += 1
    oi = pd.concat(m)
    oi["ts"] = pd.to_datetime(oi.create_time, utc=True, errors="coerce")
    n_brut = len(oi)
    oi = oi.dropna(subset=["ts"]).drop_duplicates("ts").sort_values("ts").set_index("ts")["sum_open_interest"].astype(float)
    # Correction d'anticipation (resultats/alignement_archive_*.json et bascule_horodatage_*.csv) :
    # à partir de la bascule, create_time précède de 5 minutes l'instant réel de l'observation.
    idx = oi.index.to_series()
    oi.index = pd.DatetimeIndex(idx.where(idx < BASCULE_ARCHIVE, idx + pd.Timedelta(minutes=5)))
    oi = oi[~oi.index.duplicated()].sort_index()
    # Financement.
    f = []
    for y, mo in mois(debut, fin):
        c = d / f"{symbol}-fundingRate-{y}-{mo:02d}.zip"
        if c.exists():
            t = lire_zip_csv(c)
            f.append(pd.DataFrame({"t": t.iloc[:, 0], "f": t.iloc[:, 2]}))
    f.append(rest_funding(symbol, debut_mois))
    fu = pd.concat(f)
    fu["ts"] = pd.to_datetime(fu.t.astype("int64"), unit="ms", utc=True)
    fu = fu.drop_duplicates("ts").sort_values("ts").set_index("ts")["f"].astype(float)
    qualite = {"fichiers_metrics_lus": fichiers_ok, "lignes_oi_brutes": n_brut, "lignes_oi_uniques": int(len(oi))}
    return kl, oi, fu, qualite


def signaux(symbol, kl, oi, fu, p):
    """Calcule les signaux. Convention : ts = ouverture de la bougie, T = ts + 15 min = clôture."""
    x = kl.copy()
    x["T"] = x.index + BARRE
    # OI à la clôture : dernière valeur à T au plus, âgée de 10 minutes au plus.
    a = pd.merge_asof(x[["T"]].reset_index(), oi.rename("oi").reset_index().rename(columns={"ts": "t_oi"}),
                      left_on="T", right_on="t_oi", direction="backward",
                      tolerance=pd.Timedelta(minutes=10)).set_index("ts")
    x["oi"] = a["oi"]
    n = p["fenetre_oi_bougies"]
    H = p["horizon_reference_bougies"]
    x["d_oi"] = x.oi / x.oi.shift(n) - 1
    pc = x.close.shift(1)
    tr = pd.concat([x.high - x.low, (x.high - pc).abs(), (x.low - pc).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(H).mean().shift(1)
    x["vol_med"] = x.volume.rolling(H).median().shift(1)
    x["ampl"] = x.high - x.low
    x["meche"] = (x[["open", "close"]].min(axis=1) - x.low) / x.ampl.replace(0, np.nan)
    x["plus_haut_f"] = x.high.rolling(n).max()
    x["plus_bas_f"] = x.low.rolling(n).min()
    x["close_av"] = x.close.shift(n)
    b = pd.merge_asof(x[["T"]].reset_index(), fu.rename("fund").reset_index().rename(columns={"ts": "t_f"}),
                      left_on="T", right_on="t_f", direction="backward").set_index("ts")
    x["fund"] = b["fund"]
    x["c_oi"] = x.d_oi <= p["seuil_chute_oi"]
    x["c_prix"] = (x.close < x.close_av) & (x.low <= x.plus_bas_f)
    x["c_meche"] = x.meche >= p["ratio_meche_min"]
    x["c_ampl"] = x.ampl >= p["multiple_amplitude_atr"] * x.atr
    x["c_vol"] = x.volume >= p["multiple_volume_median"] * x.vol_med
    x["c_fund"] = x.fund <= p["financement_max_par_8h"]
    x["oi_valide"] = x.d_oi.notna()
    conds = ["c_oi", "c_prix", "c_meche", "c_ampl", "c_vol", "c_fund"]
    x["signal"] = x[conds].all(axis=1)
    entonnoir = {"bougies": int(len(x)), "oi_valide": int(x.oi_valide.sum())}
    cumul = pd.Series(True, index=x.index)
    for c in conds:
        entonnoir[f"seul_{c}"] = int(x[c].sum())
        cumul = cumul & x[c]
        entonnoir[f"cumul_{c}"] = int(cumul.sum())
    entonnoir["sans_oi_prix_meche_ampl_vol_fund"] = int(x[[c for c in conds if c != "c_oi"]].all(axis=1).sum())
    sig = x[x.signal].copy()
    sig["symbole"] = symbol
    # Prix d'entrée approché pour les annulations : ouverture de la bougie 15 min suivante.
    # L'entrée réelle se fera à T + 5 min (publication de l'OI) ; le test utilisera les bougies 5 min.
    sig["entree_approx"] = x.open.shift(-1).reindex(sig.index)
    sig["stop"] = sig.low - p["tampon_stop_atr"] * sig.atr
    sig["objectif"] = sig.low + p["retracement_objectif"] * (sig.plus_haut_f - sig.low)
    sig["rr_prevu"] = (sig.objectif - sig.entree_approx) / (sig.entree_approx - sig.stop)
    sig["dist_stop_pct"] = (sig.entree_approx - sig.stop) / sig.entree_approx * 100
    sig["annule"] = (sig.entree_approx <= sig.stop) | (sig.entree_approx >= sig.objectif) | sig.entree_approx.isna()
    return sig, entonnoir, x


def appliquer_regles(tous, p, delai="signal"):
    """Délai de 24 h par actif, une entrée par bougie, 3 positions au plus avec détention supposée de 24 h.

    delai = "signal" : la règle figée telle que comptée en C02. Tout signal qui passe le délai relance
    les 24 h, même s'il est ensuite annulé ou s'il ne devient pas une entrée.
    delai = "non_annule" : un signal annulé ne relance pas les 24 h. Variante de comptage, jamais retenue.
    delai = "entree" : seule une entrée réelle relance les 24 h. Variante de comptage, jamais retenue.

    La vraie durée de détention dépend du résultat, donc elle n'est pas lue ici. Sous la règle figée,
    la limite de positions n'écarte rien (voir limite_positions_ecarte), donc le nombre n'en dépend pas.
    """
    if delai not in ("signal", "non_annule", "entree"):
        raise ValueError(delai)
    tous = tous.sort_values(["T", "d_oi"]).copy()
    H = pd.Timedelta(minutes=15 * p["horizon_reference_bougies"])
    garde_delai, pris = [], []
    dernier = {}
    ouvertes = []
    dernier_T = None
    for r in tous.itertuples():
        s, T = r.symbole, r.T
        if s in dernier and T - dernier[s] < H:
            garde_delai.append(False)
            pris.append(False)
            continue
        garde_delai.append(True)
        if delai == "signal" or (delai == "non_annule" and not r.annule):
            dernier[s] = T
        if r.annule:
            pris.append(False)
            continue
        ouvertes = [t for t in ouvertes if t > T]
        # Une seule nouvelle entrée par bougie, la plus forte chute d'OI passe d'abord (tri ci-dessus).
        if len(ouvertes) < p["positions_max"] and T != dernier_T:
            ouvertes.append(T + H)
            dernier_T = T
            pris.append(True)
            if delai == "entree":
                dernier[s] = T
        else:
            pris.append(False)
    tous["apres_delai"] = garde_delai
    tous["pris"] = pris
    v = tous[tous.apres_delai & ~tous.annule].copy()
    # Épisodes indépendants : signaux tous actifs confondus séparés d'au moins 24 h. v est déjà trié par T.
    v["episode"] = (v["T"].diff() >= H).cumsum().astype(int)
    return tous, v


def strat01_short(symbol, kl):
    """État approché de STRAT-01 côté short, par la règle de la fiche 01. Sans stop, donc une borne haute."""
    j = kl.resample("1D").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    bas20 = j.low.rolling(20).min().shift(1)
    haut10 = j.high.rolling(10).max().shift(1)
    ma200 = j.close.rolling(200).mean()
    court = False
    etat = []
    for c, b, h, m in zip(j.close, bas20, haut10, ma200):
        if court and c > h:
            court = False
        if not court and c < b and c < m:
            court = True
        etat.append(court)
    return pd.Series(etat, index=j.index + pd.Timedelta(days=1))  # connu à la clôture du jour


def bloc(ts):
    d = ts.date().isoformat()
    for nom, (a, b) in P["decoupage"].items():
        if a <= d <= b:
            return nom
    return "hors_decoupage"


def resume(v):
    pris = v[v.pris]
    return {
        "signaux_valides": int(len(v)),
        "trades": int(len(pris)),
        "bougies_distinctes": int(v["T"].nunique()),
        "limite_positions_ecarte": int(v["T"].nunique() - len(pris)),
        "episodes_independants": int(v.episode.nunique()),
        "par_bloc_trades": pris.groupby(pris["T"].map(bloc)).size().to_dict(),
        "par_bloc_episodes": v.groupby(v["T"].map(bloc)).episode.nunique().to_dict(),
        "par_annee_trades": pris.groupby(pris["T"].dt.year).size().to_dict(),
        "par_symbole_trades": pris.groupby("symbole").size().to_dict(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    debut_run = datetime.now(timezone.utc)
    stamp = debut_run.strftime("%Y%m%dT%H%M%SZ")
    debut = date.fromisoformat(P["decoupage"]["developpement"][0]) - timedelta(days=2)
    debut = max(debut, date(2021, 12, 1))
    fin = date.fromisoformat(P["decoupage"]["hors_echantillon"][1]) - timedelta(days=1)
    rap = {"debut_utc": debut_run.isoformat(timespec="seconds"), "sha256_parametres": hashlib.sha256(FICHIER_P.read_bytes()).hexdigest(),
           "periode_donnees": [str(debut), str(fin)], "telechargement": {}, "qualite": {}, "entonnoir": {},
           "correction_archive": f"create_time + 5 min à partir de {BASCULE_ARCHIVE.date()}",
           "avertissement": "Aucun rendement calculé. Comptage de signaux uniquement."}
    toutes, kls, ois, fus = [], {}, {}, {}
    for s in P["univers"]:
        t0 = time.time()
        rap["telechargement"][s] = collecter(s, debut, fin, cache)
        print(s, rap["telechargement"][s], f"{time.time() - t0:.0f} s", flush=True)
        kl, oi, fu, q = charger(s, debut, fin, cache)
        sig, ent, x = signaux(s, kl, oi, fu, P)
        # Qualité OI : couverture des pas de 5 min, et sur les 1 % de bougies les plus amples.
        grille = pd.date_range(oi.index.min().floor("D"), oi.index.max(), freq="5min")
        q["taux_couverture_5min"] = round(oi.reindex(grille).notna().mean(), 4)
        ext = x[x.ampl / x.close >= (x.ampl / x.close).quantile(0.99)]
        q["oi_valide_toutes_bougies"] = round(x.oi_valide.mean(), 4)
        q["oi_valide_1pct_bougies_les_plus_amples"] = round(ext.oi_valide.mean(), 4)
        par_an = x.groupby(x.index.year).oi_valide.mean().round(4)
        q["oi_valide_par_annee"] = {int(k): float(v) for k, v in par_an.items()}
        q["ecart_max_oi_heures"] = round(oi.index.to_series().diff().max() / pd.Timedelta(hours=1), 2)
        q["premiere_oi"] = str(oi.index.min())
        q["derniere_oi"] = str(oi.index.max())
        rap["qualite"][s], rap["entonnoir"][s] = q, ent
        toutes.append(sig)
        kls[s], ois[s], fus[s] = kl, oi, fu
    tous = pd.concat(toutes)
    tous, v = appliquer_regles(tous, P)
    rap["base"] = resume(v)
    rap["signaux_bruts"] = int(len(tous))
    rap["signaux_apres_delai"] = int(tous.apres_delai.sum())
    rap["signaux_annules_prix"] = int((tous.apres_delai & tous.annule).sum())
    # Lecture du délai : deux variantes de comptage déclarées (C05, C06), jamais retenues à la place de la base.
    rap["variantes_delai"] = {}
    for nom in ("non_annule", "entree"):
        t2, v2d = appliquer_regles(tous.drop(columns=["apres_delai", "pris"]), P, delai=nom)
        rap["variantes_delai"][nom] = dict(resume(v2d), signaux_apres_delai=int(t2.apres_delai.sum()),
                                           signaux_annules_prix=int((t2.apres_delai & t2.annule).sum()))
    # Filtre du § 3 de commun-trading (ratio minimal de 2) : effet sur le nombre, sans rendement.
    v2 = v[v.rr_prevu >= 2]
    rap["part_rr_prevu_ge_2"] = round(float((v.rr_prevu >= 2).mean()), 3) if len(v) else None
    rap["rr_prevu_mediane"] = round(float(v.rr_prevu.median()), 3) if len(v) else None
    rap["dist_stop_pct_mediane"] = round(float(v.dist_stop_pct.median()), 3) if len(v) else None
    rap["dist_stop_pct_q90"] = round(float(v.dist_stop_pct.quantile(.9)), 3) if len(v) else None
    rap["signaux_rr_ge_2"] = int(len(v2))
    # Opposition à STRAT-01 : part des signaux où la règle 01 serait short sur le même actif.
    etats = {s: strat01_short(s, kls[s]) for s in P["univers"]}
    o = [bool(etats[r.symbole].asof(r["T"])) if pd.notna(etats[r.symbole].asof(r["T"])) else False
         for _, r in v.iterrows()]
    rap["part_signaux_strat01_short_meme_actif"] = round(float(np.mean(o)), 3) if o else None
    # Régime au moment du signal : clôture de la veille sous sa moyenne 200 jours (connue au moment du signal).
    sous_ma200 = []
    for _, r in v.iterrows():
        j = kls[r.symbole].resample("1D").agg({"close": "last"}).dropna().close
        ma = j.rolling(200).mean()
        cut = r["T"].floor("D") - pd.Timedelta(days=1)
        if cut in ma.index and pd.notna(ma[cut]):
            sous_ma200.append(bool(j[cut] < ma[cut]))
    rap["signaux_avec_ma200_connue"] = len(sous_ma200)
    rap["part_signaux_sous_ma200"] = round(float(np.mean(sous_ma200)), 3) if sous_ma200 else None
    # Sensibilité du seul NOMBRE au seuil d'OI (±20 %). La base reste figée, rien n'est sélectionné ici.
    rap["sensibilite_nombre"] = {}
    for fact, nom in [(0.8, "seuil_oi_-4pct"), (1.2, "seuil_oi_-6pct")]:
        p2 = dict(P, seuil_chute_oi=P["seuil_chute_oi"] * fact)
        ts = pd.concat([signaux(s, kls[s], ois[s], fus[s], p2)[0] for s in P["univers"]])
        _, v3 = appliquer_regles(ts, p2)
        rap["sensibilite_nombre"][nom] = resume(v3) if len(v3) else {"signaux_valides": 0}
    # Colonnes conservées : aucune valeur postérieure à l'entrée.
    cols = ["symbole", "T", "d_oi", "meche", "ampl", "atr", "volume", "vol_med", "fund", "entree_approx", "stop",
            "objectif", "rr_prevu", "dist_stop_pct", "pris", "episode"]
    RES.mkdir(exist_ok=True)
    v[cols].round({c: 6 for c in cols if c not in ("symbole", "T", "pris", "episode")}).to_csv(RES / f"signaux_sans_rendement_{stamp}.csv", index=False)
    rap["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (RES / f"compte_signaux_{stamp}.json").write_text(json.dumps(rap, ensure_ascii=False, indent=1, default=str))
    print(json.dumps({k: rap[k] for k in ["signaux_bruts", "signaux_apres_delai", "signaux_annules_prix", "base", "variantes_delai", "sensibilite_nombre", "part_rr_prevu_ge_2", "rr_prevu_mediane", "dist_stop_pct_mediane", "part_signaux_strat01_short_meme_actif", "part_signaux_sous_ma200", "signaux_avec_ma200_connue", "correction_archive"]}, ensure_ascii=False, indent=1, default=str))
    print("écrit :", stamp)


if __name__ == "__main__":
    main()
