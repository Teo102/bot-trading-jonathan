#!/usr/bin/env python3
"""Audit des données de H33 (week-end des perpétuels non crypto de Binance), 19/11/2026.

Disponibilité et structure seulement : AUCUN rendement, aucune variation de prix calculée, aucun écart à la réouverture
mesuré. On lit des listes de contrats, des dates, des volumes, des taux de financement (des coûts) et, pour le prix
d'indice, seulement le fait qu'il bouge ou non pendant la fermeture (plus haut différent du plus bas sur l'heure).
Sources publiques sans clé : fapi.binance.com et data.binance.vision.

Usage : python3 -I -B audit_week_end.py
"""
import collections, datetime as dt, json, re, time
from pathlib import Path
import pandas as pd, requests

ICI = Path(__file__).resolve().parent
FAPI, S3 = "https://fapi.binance.com", "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
FIN = pd.Timestamp("2026-11-16")            # dernier week-end complet : 14-15/11/2026
ECHANTILLON = ["XAUUSDT", "XAGUSDT", "CLUSDT", "BZUSDT", "TSLAUSDT", "NVDAUSDT", "MSTRUSDT", "SPYUSDT", "QQQUSDT", "COINUSDT"]
APPELS = []
s = requests.Session()


def get(url, params=None, json_=True):
    for essai in range(4):
        try:
            r = s.get(url, params=params, timeout=60)
            APPELS.append((url.split("/")[2], r.status_code))
            if r.status_code == 200:
                time.sleep(0.15)
                return r.json() if json_ else r.text
            if r.status_code in (400, 404):
                return None
        except requests.exceptions.RequestException:
            APPELS.append((url.split("/")[2], "erreur"))
        time.sleep(2 + 2 * essai)
    return None


def liste_s3(prefixe):
    out, marqueur = [], ""
    while True:
        t = get(S3, {"prefix": prefixe, "delimiter": "/", "marker": marqueur}, json_=False) or ""
        out += re.findall(r"<Key>([^<]+)</Key>", t)
        suite = re.search(r"<NextMarker>([^<]+)</NextMarker>", t)
        if "<IsTruncated>true" not in t or not suite:
            return out
        marqueur = suite.group(1)


def fermeture(type_sous_jacent):
    """Fenêtre de fermeture du sous-jacent, en UTC, au format (jour de début, heure, durée en heures).
    Matières premières (CME Globex) : vendredi 21:00 → dimanche 22:00 (heure d'hiver ; 1 h plus tôt en été) [simplifié].
    Actions américaines : vendredi 20:00 → lundi 13:30 (séance régulière ; avant-séance non comptée) [simplifié]."""
    return (4, 21, 49) if type_sous_jacent == "COMMODITY" else (4, 20, 65)


def main():
    debut = dt.datetime.now(dt.timezone.utc)
    R = {"genere_utc": debut.strftime("%Y-%m-%dT%H:%M:%SZ"), "regle": "aucun rendement, aucune variation de prix calculée"}
    # A. contrats
    ex = get(f"{FAPI}/fapi/v1/exchangeInfo") or {}
    nc = [x for x in ex.get("symbols", []) if x.get("underlyingType") not in (None, "COIN") and x.get("quoteAsset") in ("USDT", "USDC")]
    rows = []
    for x in nc:
        L = pd.Timestamp(int(x["onboardDate"]), unit="ms")
        samedis = pd.date_range(L.normalize() + pd.Timedelta(days=1), FIN, freq="W-SAT")
        rows.append({"symbole": x["symbol"], "type": x.get("underlyingType"), "sous_type": ",".join(x.get("underlyingSubType") or []),
                     "contrat": x.get("contractType"), "statut": x.get("status"), "cotation": str(L.date()), "week_ends": len(samedis)})
    df = pd.DataFrame(rows)
    R["A_contrats"] = {"total": len(df), "par_type": df["type"].value_counts().to_dict(),
                       "week_ends_par_type": df.groupby("type")["week_ends"].agg(["count", "median", "max", "sum"]).to_dict("index"),
                       "cotations_par_mois": df["cotation"].str[:7].value_counts().sort_index().to_dict()}
    # B. archives publiques pour l'échantillon
    R["B_archives"] = {}
    for sym in ECHANTILLON:
        r = {}
        for nom, pre in (("klines_1h", f"data/futures/um/monthly/klines/{sym}/1h/"), ("indice_1h", f"data/futures/um/monthly/indexPriceKlines/{sym}/1h/"),
                         ("marque_1h", f"data/futures/um/monthly/markPriceKlines/{sym}/1h/"), ("financement", f"data/futures/um/monthly/fundingRate/{sym}/"),
                         ("klines_1h_jour", f"data/futures/um/daily/klines/{sym}/1h/")):
            cles = [k for k in liste_s3(pre) if k.endswith(".zip")]
            mois = sorted(m.group(1) for k in cles if (m := re.search(r"(\d{4}-\d{2}(?:-\d{2})?)\.zip$", k)))  # correctif : une date par fichier
            r[nom] = {"fichiers": len(cles), "premier": mois[0] if mois else None, "dernier": mois[-1] if mois else None}
        R["B_archives"][sym] = r
    # C. le prix d'indice bouge-t-il pendant la fermeture ? (6 derniers week-ends et un week-end d'avril 2026 pour l'or)
    R["C_indice_fermeture"] = {}
    typ = dict(zip(df["symbole"], df["type"]))
    vendredis = list(pd.date_range(FIN - pd.Timedelta(days=45), FIN, freq="W-FRI"))
    for sym in ECHANTILLON:
        j0, h0, duree = fermeture(typ.get(sym))
        res = []
        for v in vendredis + ([pd.Timestamp("2026-04-17")] if typ.get(sym) == "COMMODITY" else []):
            a = v + pd.Timedelta(hours=h0)
            k = get(f"{FAPI}/fapi/v1/indexPriceKlines", {"pair": sym, "interval": "1h", "startTime": int(a.timestamp() * 1000), "limit": duree}) or []
            kc = get(f"{FAPI}/fapi/v1/klines", {"symbol": sym, "interval": "1h", "startTime": int(a.timestamp() * 1000), "limit": duree}) or []
            bouge = sum(1 for x in k if float(x[2]) != float(x[3]))
            res.append({"vendredi": str(v.date()), "heures_indice": len(k), "heures_ou_l_indice_bouge": bouge,
                        "heures_contrat_avec_volume": sum(1 for x in kc if float(x[5]) > 0)})
        R["C_indice_fermeture"][sym] = res
    # D. volume du week-end contre la semaine (8 semaines, volume en USDT seulement) et écart affiché maintenant
    R["D_liquidite"] = {}
    for sym in ECHANTILLON:
        k = get(f"{FAPI}/fapi/v1/klines", {"symbol": sym, "interval": "1h", "startTime": int((FIN - pd.Timedelta(days=56)).timestamp() * 1000), "limit": 1500}) or []
        if not k:
            continue
        v = pd.Series([float(x[7]) for x in k], index=pd.to_datetime([int(x[0]) for x in k], unit="ms"))
        v = v[v.index < FIN]
        we = v[v.index.day_of_week >= 5]
        bt = get(f"{FAPI}/fapi/v1/ticker/bookTicker", {"symbol": sym}) or {}
        ecart = (float(bt["askPrice"]) / float(bt["bidPrice"]) - 1) if bt.get("bidPrice") and float(bt["bidPrice"]) > 0 else None
        R["D_liquidite"][sym] = {"volume_horaire_median_semaine_usdt": round(float(v[v.index.day_of_week < 5].median())),
                                 "volume_horaire_median_week_end_usdt": round(float(we.median())) if len(we) else None,
                                 "rapport_week_end_semaine": round(float(we.median() / v[v.index.day_of_week < 5].median()), 3) if len(we) else None,
                                 "ecart_affiche_jeudi_relatif": ecart, "heure_lecture_ecart": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    # E. financement : versements le week-end, intervalle, ordre de grandeur (un coût, pas un rendement)
    R["E_financement"] = {}
    for sym in ECHANTILLON:
        f = get(f"{FAPI}/fapi/v1/fundingRate", {"symbol": sym, "startTime": int((FIN - pd.Timedelta(days=56)).timestamp() * 1000), "limit": 1000}) or []
        if not f:
            continue
        t = pd.to_datetime([int(x["fundingTime"]) for x in f], unit="ms")
        r_ = pd.Series([abs(float(x["fundingRate"])) for x in f], index=t)
        R["E_financement"][sym] = {"versements": len(f), "intervalle_heures_median": float(pd.Series(t).diff().dt.total_seconds().median() / 3600),
                                   "versements_le_week_end": int((t.day_of_week >= 5).sum()),
                                   "taux_absolu_median_semaine": float(r_[r_.index.day_of_week < 5].median()),
                                   "taux_absolu_median_week_end": float(r_[r_.index.day_of_week >= 5].median()) if (t.day_of_week >= 5).any() else None}
    # F. nombre de décisions possibles (critère T3) : contrats-week-ends, avec un seuil de liquidité du week-end
    R["F_decisions"] = {"contrats_week_ends_total": int(df["week_ends"].sum()),
                        "par_type": df.groupby("type")["week_ends"].sum().to_dict(),
                        "matieres_premieres": df[df["type"] == "COMMODITY"][["symbole", "cotation", "week_ends"]].to_dict("records")}
    R["appels"] = {"total": len(APPELS), "par_hote": dict(collections.Counter(h for h, _ in APPELS)),
                   "erreurs": [a for a in APPELS if a[1] not in (200,)]}
    R["duree_s"] = round((dt.datetime.now(dt.timezone.utc) - debut).total_seconds(), 1)
    h = debut.strftime("%Y%m%dT%H%M%SZ")
    (ICI / f"audit_week_end_{h}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str))
    df.to_csv(ICI / f"contrats_non_crypto_{h}.csv", index=False)
    print(ICI / f"audit_week_end_{h}.json", R["appels"]["total"], "appels", R["duree_s"], "s")


if __name__ == "__main__":
    main()
