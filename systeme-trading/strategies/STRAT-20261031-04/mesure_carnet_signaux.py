#!/usr/bin/env python3
"""STRAT-20261031-04 : profondeur de carnet au moment des signaux, et arithmétique des coûts.

Aucun rendement réalisé n'est lu. Trois mesures :
  1. Profondeur (bookDepth de data.binance.vision, depuis 2023-01-01) dans les 10 minutes qui suivent
     chaque signal, comparée à la médiane de la veille. Sert à calibrer le glissement.
     Le demi-écart vient de mesure_demi_ecart_signaux.py (--demi-ecart).
  2. Taux de réussite d'équilibre de chaque signal, calculé par construction à partir de l'entrée,
     du stop et de l'objectif prévus, sous coûts de base et stressés.
  3. Comparaison des séries OI : REST openInterestHist contre archive metrics sur un jour récent.

Usage : python mesure_carnet_signaux.py --signaux resultats/signaux_....csv --cache <dossier>
        [--demi-ecart resultats/demi_ecart_signaux_....csv]
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
P = json.loads((ICI / "parametres_geles.json").read_text())
VISION = "https://data.binance.vision/data/futures/um"
FAPI = "https://fapi.binance.com"
SES = requests.Session()
SES.headers["User-Agent"] = "recherche-donnees-publiques/1.0"


def glissement_moyen_pct(n, profondeur_1pct_usd, demi_ecart_pct=0.0):
    """Glissement moyen d'un ordre au marché, en pourcent du milieu du carnet.

    Si les D dollars cumulés à 1 % sont répartis uniformément, un ordre de N dollars atteint
    N / D x 1 % et paie en moyenne la moitié de cet écart, soit N / (2 x D) pour cent, plus le demi-écart.
    Le résultat est déjà en pourcent : aucun facteur 100 à appliquer.
    Au-delà de N = D, le modèle sort de la tranche mesurée : utiliser glissement_par_tranches_pct.
    """
    return n / (2 * profondeur_1pct_usd) + demi_ecart_pct


def ticket_pour_glissement_usd(glissement_pct, profondeur_1pct_usd, demi_ecart_pct=0.0):
    """Ticket auquel glissement_moyen_pct atteint une valeur donnée. Inverse de la formule."""
    return 2 * profondeur_1pct_usd * (glissement_pct - demi_ecart_pct)


def glissement_par_tranches_pct(n, tranches, demi_ecart_pct=0.0):
    """Glissement moyen en parcourant les tranches cumulées d'un même relevé bookDepth, sans extrapoler.

    tranches = [(1, D1), (2, D2), ...], écart en pourcent et dollars cumulés. Répartition uniforme dans chaque tranche.
    Sous D1, le résultat égale glissement_moyen_pct. NaN si le ticket dépasse la dernière tranche.
    """
    if not tranches or n > tranches[-1][1]:
        return np.nan
    p0, d0, aire = 0.0, 0.0, 0.0
    for p1, d1 in tranches:
        if d1 > d0:
            m = min(n, d1) - d0
            aire += m * (p0 + (p0 + (p1 - p0) * m / (d1 - d0))) / 2
            if n <= d1:
                return aire / n + demi_ecart_pct
            p0, d0 = p1, d1
    return np.nan


def ticket_par_tranches_usd(glissement_pct, tranches, demi_ecart_pct=0.0):
    """Ticket auquel glissement_par_tranches_pct atteint une valeur. inf si elle n'est pas atteinte dans le relevé."""
    if not tranches:
        return np.nan
    bas, haut = 0.0, float(tranches[-1][1])
    if glissement_par_tranches_pct(haut, tranches, demi_ecart_pct) < glissement_pct:
        return np.inf
    for _ in range(60):
        milieu = (bas + haut) / 2
        if milieu > 0 and glissement_par_tranches_pct(milieu, tranches, demi_ecart_pct) < glissement_pct:
            bas = milieu
        else:
            haut = milieu
    return haut


def tranches_du_releve(t, ts, signe):
    """Tranches cumulées ±1 à ±5 % du relevé ts. signe = 1 pour les vendeurs, -1 pour les acheteurs."""
    x = t[t.ts == ts]
    out = []
    for k in range(1, 6):
        v = x[x.percentage == signe * k].notional
        if len(v):
            out.append((k, float(v.iloc[0])))
    return out


def parcours_carnet_pct(niveaux_ask, milieu, n):
    """Parcours réel d'un achat de n dollars, en pourcent du milieu. None si le carnet est trop court."""
    reste, quantite = n, 0.0
    for prix, qte in niveaux_ask:
        usd = min(reste, prix * qte)
        quantite += usd / prix
        reste -= usd
        if reste <= 0:
            return (n / quantite / milieu - 1) * 100
    return None


def telecharger(sym, jour, cache):
    d = cache / sym
    d.mkdir(parents=True, exist_ok=True)
    n = f"{sym}-bookDepth-{jour}.zip"
    c = d / n
    if c.exists():
        return c
    for i in range(4):
        try:
            r = SES.get(f"{VISION}/daily/bookDepth/{sym}/{n}", timeout=60)
            if r.status_code == 200:
                c.write_bytes(r.content)
                return c
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(1 + 2 * i)
    return None


def lire(c):
    with zipfile.ZipFile(c) as z, z.open(z.namelist()[0]) as f:
        t = pd.read_csv(f)
    t["ts"] = pd.to_datetime(t["timestamp"], utc=True)
    return t


def releves_vivants(s):
    """Retire les relevés identiques au précédent. Un cumul à 1 % qui ne bouge pas en 30 s n'est pas un carnet vivant.

    L'archive contient des côtés gelés pendant des heures (ETH acheteur à 567 295 $ tout le 10/10/2025,
    avec la même valeur à -1 % et -2 %, alors que le côté vendeur varie). Ces valeurs ne sont pas des carnets vides.
    """
    return s[s != s.shift(1)]


def minimum_fenetre(s, vivants, debut, fin, part_min=0.5):
    """Minimum des relevés vivants, ou NaN si moins de la moitié de la fenêtre est vivante. Renvoie (valeur, gelé)."""
    brut = s[(s.index >= debut) & (s.index <= fin)]
    bon = vivants[(vivants.index >= debut) & (vivants.index <= fin)]
    if not len(brut):
        return np.nan, False
    if len(bon) < part_min * len(brut):
        return np.nan, True
    return float(bon.min()), False


def mesurer(r, cache):
    T = r["T"]
    jours = sorted({(T - timedelta(days=1)).date().isoformat(), T.date().isoformat(),
                    (T + timedelta(minutes=10)).date().isoformat()})
    parts = []
    for j in jours:
        c = telecharger(r.symbole, j, cache)
        if c is not None:
            parts.append(lire(c))
    if not parts:
        return None
    t = pd.concat(parts)
    res = {"symbole": r.symbole, "T": T}
    for pct, nom in [(1, "ask1"), (-1, "bid1")]:
        s = t[t.percentage == pct].set_index("ts").sort_index()["notional"].astype(float)
        v = releves_vivants(s)
        ref = v[(v.index >= T - timedelta(hours=25)) & (v.index < T - timedelta(hours=1))]
        res[f"{nom}_ref_usd"] = float(ref.median()) if len(ref) else np.nan
        res[f"{nom}_apres_usd"], res[f"{nom}_apres_gele"] = minimum_fenetre(s, v, T, T + timedelta(minutes=10))
        res[f"{nom}_pendant_min_usd"], res[f"{nom}_pendant_gele"] = minimum_fenetre(s, v, T - timedelta(minutes=15), T - timedelta(seconds=1))
    # Tranches du relevé le plus mince, pour parcourir le carnet au-delà de 1 % sans extrapoler.
    for nom, signe, val, a0, a1, col in [("ask1", 1, "ask1_apres_usd", T, T + timedelta(minutes=10), "ask1_apres_tranches"),
                                         ("bid1", -1, "bid1_pendant_min_usd", T - timedelta(minutes=15), T - timedelta(seconds=1), "bid1_pendant_tranches")]:
        s = t[t.percentage == signe].set_index("ts").sort_index()["notional"].astype(float)
        fen = s[(s.index >= a0) & (s.index <= a1)]
        if signe == -1:  # sensibilité : minimum brut, valeurs gelées gardées
            res["bid1_pendant_min_brut_usd"] = float(fen.min()) if len(fen) else np.nan
        vivants = releves_vivants(s)
        vivants = vivants[(vivants.index >= a0) & (vivants.index <= a1)]
        res[col] = tranches_du_releve(t, vivants.idxmin(), signe) if not np.isnan(res[val]) else []
    return res


def equilibre(v):
    """Taux de réussite d'équilibre p* = perte nette / (gain net + perte nette). Aucun résultat lu.

    Convention : le frais preneur est compté aussi à l'objectif, bien que ce soit un ordre limite.
    C'est prudent, car parametres_geles.json ne fige aucun frais d'ordre limite. objectif_sans_frais
    borne l'effet de ce choix. Les scénarios couts_xN ne multiplient que le glissement.
    frais_et_glissement_x2 est le stress de validation-edge § 4.5.
    """
    frais = P["frais_taker_par_cote"]
    scenarios = {"frais_seuls": (0, 1, 1), "couts_x1": (1, 1, 1), "couts_x2": (2, 1, 1), "couts_x4": (4, 1, 1),
                 "frais_et_glissement_x2": (2, 2, 1), "couts_x1_objectif_sans_frais": (1, 1, 0)}
    out = {}
    for nom, (mult, mult_frais, frais_objectif) in scenarios.items():
        g = []
        for _, r in v.iterrows():
            cl = "BTC_ETH" if r.symbole in ("BTCUSDT", "ETHUSDT") else "autres"
            gl = P["glissement_base"][cl]
            cout_gagnant = mult_frais * frais * (1 + frais_objectif) + mult * (gl["entree"] + gl["objectif"])
            cout_perdant = mult_frais * 2 * frais + mult * (gl["entree"] + gl["stop"])
            gain = (r.objectif - r.entree_approx) / r.entree_approx - cout_gagnant
            perte = (r.entree_approx - r.stop) / r.entree_approx + cout_perdant
            g.append((gain, perte))
        a = np.array(g)
        pos = a[:, 0] > 0
        p = a[pos, 1] / (a[pos, 0] + a[pos, 1])
        out[nom] = {
            "signaux": int(len(a)),
            "gain_net_prevu_negatif_ou_nul": int((~pos).sum()),
            "part_gain_net_negatif_ou_nul": round(float((~pos).mean()), 3),
            "reussite_equilibre_mediane_si_gain_positif": round(float(np.median(p)), 3) if len(p) else None,
            "reussite_equilibre_q25": round(float(np.quantile(p, .25)), 3) if len(p) else None,
            "reussite_equilibre_q75": round(float(np.quantile(p, .75)), 3) if len(p) else None,
        }
    return out


def comparer_oi(cache):
    """REST 5 min contre archive, BTC, jour J-3 (accessible dans les 30 jours du REST)."""
    j = (datetime.now(timezone.utc) - timedelta(days=3)).date()
    n = f"BTCUSDT-metrics-{j}.zip"
    c = cache / n
    r = SES.get(f"{VISION}/daily/metrics/BTCUSDT/{n}", timeout=60)
    if r.status_code != 200:
        return {"erreur": f"archive {r.status_code}"}
    c.write_bytes(r.content)
    m = pd.read_csv(zipfile.ZipFile(c).open(n.replace(".zip", ".csv")))
    m["ts"] = pd.to_datetime(m.create_time, utc=True)
    m = m.set_index("ts").sum_open_interest.astype(float)
    t0 = int(datetime(j.year, j.month, j.day, tzinfo=timezone.utc).timestamp() * 1000)
    lignes, cur = [], t0
    while cur < t0 + 86_400_000:
        q = SES.get(f"{FAPI}/futures/data/openInterestHist",
                    params={"symbol": "BTCUSDT", "period": "5m", "limit": 500, "startTime": cur,
                            "endTime": t0 + 86_399_000}, timeout=30)
        q.raise_for_status()
        d = q.json()
        if not d:
            break
        lignes += d
        cur = d[-1]["timestamp"] + 300_000
    s = pd.DataFrame(lignes)
    s["ts"] = pd.to_datetime(s.timestamp, unit="ms", utc=True)
    s = s.set_index("ts").sumOpenInterest.astype(float)
    x = pd.concat([m.rename("archive"), s.rename("rest")], axis=1)
    both = x.dropna()
    dec = {}
    for k in range(-2, 3):
        a = x.archive.shift(k).dropna()
        cm = a.index.intersection(s.index)
        dec[str(k)] = round(float((a[cm] / s[cm] - 1).abs().mean()), 8)
    return {"jour": str(j), "lignes_archive": int(m.size), "pas_uniques_archive_minutes": sorted(set((m.sort_index().index.to_series().diff().dropna() / pd.Timedelta(minutes=1)).astype(int).tolist()))[:8],
            "lignes_rest": int(s.size), "communes": int(len(both)),
            "ecart_relatif_moyen_par_decalage_de_pas": dec,
            "ecart_relatif_max_sans_decalage": round(float((both.archive / both.rest - 1).abs().max()), 8)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signaux", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--demi-ecart", default=None, help="CSV de mesure_demi_ecart_signaux.py")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    debut = datetime.now(timezone.utc)
    stamp = debut.strftime("%Y%m%dT%H%M%SZ")
    v = pd.read_csv(a.signaux, parse_dates=["T"])
    rap = {"debut_utc": debut.isoformat(timespec="seconds"), "fichier_signaux": Path(a.signaux).name,
           "avertissement": "Aucun rendement réalisé lu.", "equilibre": equilibre(v),
           "equilibre_trades_pris": equilibre(v[v.pris]), "comparaison_oi": None}
    try:
        rap["comparaison_oi"] = comparer_oi(cache)
    except Exception as e:  # lacune consignée
        rap["comparaison_oi"] = {"ECHEC": f"{type(e).__name__}: {e}"}
    w = v[v["T"] >= pd.Timestamp("2023-01-03", tz="UTC")]
    with cf.ThreadPoolExecutor(6) as ex:
        res = [x for x in ex.map(lambda t: mesurer(t[1], cache), w.iterrows()) if x]
    d = pd.DataFrame(res)
    d["ratio_ask1"] = d.ask1_apres_usd / d.ask1_ref_usd
    d["ratio_bid1"] = d.bid1_apres_usd / d.bid1_ref_usd
    d["ratio_bid1_pendant"] = d.bid1_pendant_min_usd / d.bid1_ref_usd
    d["ratio_ask1_pendant"] = d.ask1_pendant_min_usd / d.ask1_ref_usd
    d["classe"] = np.where(d.symbole.isin(["BTCUSDT", "ETHUSDT"]), "BTC_ETH", "autres")
    # Demi-écart mesuré par signal. Là où l'archive bookTicker s'arrête, médiane de la classe, comptée à part.
    d["demi_ecart_entree_pct"], d["demi_ecart_stop_pct"] = np.nan, np.nan
    if a.demi_ecart:
        h = pd.read_csv(a.demi_ecart, parse_dates=["T"])
        cle = d[["symbole", "T"]].merge(h, on=["symbole", "T"], how="left")
        d["demi_ecart_entree_pct"] = cle.demi_ecart_entree_mediane_pct.to_numpy()
        d["demi_ecart_stop_pct"] = cle.demi_ecart_bougie_q95_pct.to_numpy()
        rap["fichier_demi_ecart"] = Path(a.demi_ecart).name
    bloc = {}
    for cl, g in d.groupby("classe"):
        g = g.copy()
        e = {"signaux_mesures": int(len(g)), "demi_ecart_signaux_mesures": int(g.demi_ecart_entree_pct.notna().sum()),
             "signaux_gele_vendeurs_apres": int(g.ask1_apres_gele.sum()), "signaux_gele_acheteurs_pendant": int(g.bid1_pendant_gele.sum()),
             "signaux_stop_exploitables": int(g.bid1_pendant_min_usd.notna().sum()), "signaux_entree_exploitables": int(g.ask1_apres_usd.notna().sum()),
             "signaux_acheteurs_geles_liste": [f"{r.symbole} {r.T}" for r in g[g.bid1_pendant_gele].itertuples()]}
        for col in ["demi_ecart_entree_pct", "demi_ecart_stop_pct"]:
            if g[col].notna().any():
                e[f"{col}_mediane_mesuree"] = round(float(g[col].median()), 4)
                e[f"{col}_q90_mesuree"] = round(float(g[col].quantile(.9)), 4)
            g[col] = g[col].fillna(g[col].median()).fillna(0.0)
        for col in ["ratio_ask1", "ratio_bid1", "ratio_ask1_pendant", "ratio_bid1_pendant"]:
            e[f"{col}_mediane"] = round(float(g[col].median()), 3)
            e[f"{col}_q10"] = round(float(g[col].quantile(.1)), 3)
        for col in ["ask1_ref_usd", "ask1_apres_usd", "bid1_ref_usd", "bid1_apres_usd", "bid1_pendant_min_usd"]:
            e[f"{col}_mediane"] = round(float(g[col].median()))
        e["bid1_pendant_min_usd_plus_faible"] = round(float(g.bid1_pendant_min_usd.min()))
        cotes = [("entree", g.ask1_apres_usd, g.demi_ecart_entree_pct), ("stop", g.bid1_pendant_min_usd, g.demi_ecart_stop_pct)]
        for n in [10_000, 100_000, 500_000]:
            for cote, prof, h in cotes:
                total = glissement_moyen_pct(n, prof, h)
                impact = glissement_moyen_pct(n, prof)
                e[f"gliss_{cote}_pct_{n}"] = round(float(total.median()), 4)
                e[f"gliss_{cote}_pct_{n}_q90"] = round(float(total.quantile(.9)), 4)
                e[f"gliss_{cote}_pct_{n}_max"] = round(float(total.max()), 4)
                e[f"impact_seul_{cote}_pct_{n}"] = round(float(impact.median()), 4)
                e[f"part_ticket_au_dela_1pct_{cote}_{n}"] = round(float((n > prof.dropna()).mean()), 3)
        # Ticket auquel l'estimation atteint l'hypothèse de base. Au-delà de la profondeur à 1 %, extrapolation.
        base = P["glissement_base"][cl]
        for cote, prof, h in cotes:
            t = ticket_pour_glissement_usd(base[cote] * 100, prof, h)
            e[f"ticket_atteignant_base_{cote}_usd_mediane"] = round(float(t.median()))
            e[f"ticket_atteignant_base_{cote}_usd_q10"] = round(float(t.quantile(.1)))
        # Queue de distribution : le 90e centile cache les pires signaux, qui restent listés ici.
        for n in [10_000, 100_000]:
            total = glissement_moyen_pct(n, g.bid1_pendant_min_usd, g.demi_ecart_stop_pct).dropna()
            for mult in (1, 2, 4):
                e[f"signaux_stop_{n}_au_dessus_base_x{mult}"] = int((total > mult * base["stop"] * 100).sum())
        # Parcours par tranches du même relevé : remplace l'extrapolation au-delà de 1 %.
        cotes_t = [("entree", "ask1_apres_tranches", "demi_ecart_entree_pct"), ("stop", "bid1_pendant_tranches", "demi_ecart_stop_pct")]
        for cote, col, hcol in cotes_t:
            exploit = g[g[col].map(len) > 0]
            for n in [10_000, 100_000, 500_000]:
                total = exploit.apply(lambda r: glissement_par_tranches_pct(n, r[col], r[hcol]), axis=1)
                e[f"tranches_{cote}_pct_{n}"] = round(float(total.median()), 4)
                e[f"tranches_{cote}_pct_{n}_q90"] = round(float(total.quantile(.9)), 4)
                e[f"tranches_{cote}_pct_{n}_max"] = round(float(total.max()), 4)
                e[f"tranches_{cote}_{n}_hors_releve"] = int(total.isna().sum())
                for mult in (1, 2, 4):
                    e[f"tranches_{cote}_{n}_au_dessus_base_x{mult}"] = int((total > mult * base[cote] * 100).sum())
            t = exploit.apply(lambda r: ticket_par_tranches_usd(base[cote] * 100, r[col], r[hcol]), axis=1)
            e[f"tranches_ticket_base_{cote}_usd_mediane"] = round(float(t.median()))
            e[f"tranches_ticket_base_{cote}_usd_q10"] = round(float(t.quantile(.1)))
            e[f"tranches_ticket_base_{cote}_non_atteint"] = int(np.isinf(t).sum())
        # Sensibilité : si l'on gardait les valeurs gelées comme de vrais carnets.
        for n in [10_000, 100_000]:
            brut = glissement_moyen_pct(n, g.bid1_pendant_min_brut_usd, g.demi_ecart_stop_pct).dropna()
            e[f"stop_{n}_geles_gardes_q90"] = round(float(brut.quantile(.9)), 4)
            e[f"stop_{n}_geles_gardes_au_dessus_base_x1"] = int((brut > base["stop"] * 100).sum())
        pires = g.dropna(subset=["bid1_pendant_min_usd"]).nsmallest(5, "bid1_pendant_min_usd")
        e["cinq_carnets_les_plus_vides_pendant_la_bougie"] = [
            {"symbole": r.symbole, "T": str(r.T), "bid1_pendant_min_usd": round(r.bid1_pendant_min_usd),
             "bid1_ref_usd": round(r.bid1_ref_usd), "tranches_usd": [[k, round(u)] for k, u in r.bid1_pendant_tranches],
             "stop_100000_tranches_pct": round(float(glissement_par_tranches_pct(100_000, r.bid1_pendant_tranches, r.demi_ecart_stop_pct)), 4)}
            for r in pires.itertuples()]
        bloc[cl] = e
    rap["carnet_par_classe"] = bloc
    rap["carnet_signaux_lacunaires"] = int((d[["ask1_apres_usd", "bid1_apres_usd", "ask1_ref_usd"]].isna().any(axis=1)
                                            & ~d.ask1_apres_gele & ~d.bid1_apres_gele).sum())
    rap["fin_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    RES.mkdir(exist_ok=True)
    (RES / f"mesure_carnet_signaux_{stamp}.json").write_text(json.dumps(rap, ensure_ascii=False, indent=1, default=str))
    print(json.dumps(rap, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
