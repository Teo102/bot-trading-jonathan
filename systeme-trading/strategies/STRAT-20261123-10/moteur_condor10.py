#!/usr/bin/env python3
"""Moteur de STRAT-20261123-10 (fiche § 3 et § 4) : condor hebdomadaire sur options BTC de Deribit, à risque défini.

Bloc de développement seulement (2021-2024) : le moteur refuse toute date à partir du 01/01/2025.
Usage (serveur) : python -I -B moteur_condor10.py --donnees /root/strat10_data --sorties resultats
"""
import argparse, datetime as dt, gzip, json, math
from pathlib import Path
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
VERROU_HORS_ECHANTILLON = dt.date(2025, 1, 1)
Z_COURT, Z_AILE, RISQUE = 1.0, 2.0, 0.02
T_ANNEES = 7 / 365
GLISS_MIN_BTC, GLISS_PART, FRAIS_PART_S, FRAIS_PLAFOND, LIVR_PART_S = 0.0003, 0.08, 0.0003, 0.125, 0.00015
MOIS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def etiquette(d):
    """Date d'échéance au format Deribit : 5FEB21."""
    return f"{d.day}{MOIS[d.month - 1]}{d.year % 100:02d}"


def legs_disponibles(tr, echeance):
    """Transactions de l'échéance visée : prix d'exercice, type, dernière marque par instrument."""
    x = tr[tr["instrument_name"].str.split("-").str[1] == etiquette(echeance)].copy()
    if not len(x):
        return x
    p = x["instrument_name"].str.split("-")
    x["k"], x["type"] = p.str[2].astype(float), p.str[3]
    return x


def choisir(prix_exercice, cible, sens):
    """Le plus proche au niveau ou en dessous (sens -1) ou au niveau ou au-dessus (sens +1) de la cible."""
    c = [k for k in prix_exercice if (k <= cible if sens < 0 else k >= cible)]
    return (max(c) if sens < 0 else min(c)) if c else None


def semaine(tr, v, livraison, cout=1.0):
    """Une semaine. Renvoie un dict avec 'rendement' (0 si pas de position) et le détail."""
    assert v < VERROU_HORS_ECHANTILLON, "hors échantillon verrouillé"
    ech = v + dt.timedelta(days=7)
    res = {"vendredi": str(v), "position": False, "rendement": 0.0}
    if tr is None or not len(tr) or livraison is None:
        res["motif"] = "donnees_absentes"
        return res
    S = float(tr["index_price"].median())
    x = legs_disponibles(tr, ech)
    if not len(x):
        res["motif"] = "echeance_non_traitee"
        return res
    m = (x["k"] / S - 1).abs()
    iv = x.loc[m <= 0.05, "iv"]
    if len(iv) < 3:
        iv = x.loc[m <= 0.10, "iv"]
    if len(iv) < 3:
        res["motif"] = "volatilite_absente"
        return res
    sig = float(iv.median()) / 100
    r = sig * math.sqrt(T_ANNEES)
    puts, calls = sorted(set(x.loc[x.type == "P", "k"])), sorted(set(x.loc[x.type == "C", "k"]))
    kp, kc = choisir(puts, S * math.exp(-Z_COURT * r), -1), choisir(calls, S * math.exp(Z_COURT * r), 1)
    kpw, kcw = choisir(puts, S * math.exp(-Z_AILE * r), -1), choisir(calls, S * math.exp(Z_AILE * r), 1)
    if None in (kp, kc, kpw, kcw) or not (kpw < kp and kcw > kc):
        res["motif"] = "jambes_absentes"
        return res
    der = x.sort_values("timestamp").groupby(["k", "type"])["mark_price"].last()
    jambes = {"put_vendu": (kp, "P", -1), "call_vendu": (kc, "C", -1), "put_achete": (kpw, "P", 1), "call_achete": (kcw, "C", 1)}
    credit = 0.0
    for nom, (k, t, sens) in jambes.items():
        mk = float(der[(k, t)])
        g = cout * max(GLISS_MIN_BTC, GLISS_PART * mk)
        px = mk + g if sens > 0 else max(mk - g, 0.0)
        frais = cout * min(FRAIS_PART_S * S, FRAIS_PLAFOND * mk * S)
        credit += (-sens) * px * S - frais
        res[nom] = {"k": k, "marque_btc": mk}
    if credit <= 0:
        res["motif"] = "credit_non_positif"
        return res
    ST = float(livraison)
    intr = {"put_vendu": max(0.0, kp - ST), "call_vendu": max(0.0, ST - kc), "put_achete": max(0.0, kpw - ST), "call_achete": max(0.0, ST - kcw)}
    paiement = -intr["put_vendu"] - intr["call_vendu"] + intr["put_achete"] + intr["call_achete"]
    livr = sum(cout * min(LIVR_PART_S * ST, FRAIS_PLAFOND * v_) for v_ in intr.values() if v_ > 0)
    perte_max = max(kp - kpw, kcw - kc) - credit
    if perte_max <= 0:
        res["motif"] = "perte_max_non_positive"
        return res
    pnl = credit + paiement - livr
    res.update({"position": True, "S": S, "sigma": sig, "S_T": ST, "credit_usd": credit, "paiement_usd": paiement,
                "frais_livraison_usd": livr, "perte_max_usd": perte_max, "pnl_usd": pnl, "rendement": RISQUE * pnl / perte_max})
    return res


def evaluer(sem):
    """Portes de la fiche § 4 sur la série hebdomadaire (semaines sans position à 0)."""
    s = pd.Series([x["rendement"] for x in sem["base"]], index=pd.to_datetime([x["vendredi"] for x in sem["base"]]))
    s2 = pd.Series([x["rendement"] for x in sem["couts_doubles"]], index=s.index)
    ans = (s.index[-1] - s.index[0]).days / 365.25 + 7 / 365.25
    cap = (1 + s).cumprod()
    dd = float((1 - cap / cap.cummax()).max())
    par_an = s.groupby(s.index.year).sum()
    gain = s.sum()
    pos = sum(1 for x in sem["base"] if x["position"])
    sharpe = float(s.mean() / s.std(ddof=1) * math.sqrt(52)) if s.std(ddof=1) > 0 else None
    r = {"semaines": len(s), "semaines_avec_position": pos, "net_annualise": float(gain / ans),
         "sharpe_annualise": sharpe, "par_annee": {str(k): float(v) for k, v in par_an.items()},
         "net_annualise_couts_doubles": float(s2.sum() / ans), "drawdown_max": dd,
         "part_max_d_une_semaine": float(s.max() / gain) if gain > 0 else None,
         "pire_semaine": float(s.min()), "meilleure_semaine": float(s.max()),
         "semaines_a_perte_max": int(sum(1 for x in sem["base"] if x["position"] and x["rendement"] <= -RISQUE * 0.999)),
         "taux_gagnant": float(np.mean([x["rendement"] > 0 for x in sem["base"] if x["position"]])) if pos else None}
    portes = {"net_annualise_positif": r["net_annualise"] > 0, "sharpe_au_moins_1": (sharpe or 0) >= 1.0,
              "3_annees_positives_sur_4": int((par_an > 0).sum()) >= 3, "couts_doubles_positif": r["net_annualise_couts_doubles"] > 0,
              "drawdown_au_plus_20pct": dd <= 0.20, "au_moins_150_semaines": pos >= 150,
              "aucune_semaine_plus_de_25pct": r["part_max_d_une_semaine"] is not None and r["part_max_d_une_semaine"] <= 0.25}
    return r, {k: bool(v) for k, v in portes.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donnees", required=True)
    ap.add_argument("--sorties", default=str(ICI / "resultats"))
    a = ap.parse_args()
    d = Path(a.donnees)
    liv = json.loads((d / "livraisons_btc_usd.json").read_text())
    vend = sorted(dt.date.fromisoformat(f.name[:10]) for f in (d / "transactions").glob("*.csv.gz"))
    vend = [v for v in vend if v < VERROU_HORS_ECHANTILLON and dt.date(2021, 1, 1) <= v]
    sem = {"base": [], "couts_doubles": []}
    for v in vend:
        tr = pd.read_csv(d / "transactions" / f"{v}.csv.gz")
        l_ = liv.get(str(v + dt.timedelta(days=7)))
        sem["base"].append(semaine(tr, v, l_, 1.0))
        sem["couts_doubles"].append(semaine(tr, v, l_, 2.0))
    r, portes = evaluer(sem)
    out = Path(a.sorties)
    out.mkdir(parents=True, exist_ok=True)
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    motifs = pd.Series([x.get("motif", "position") for x in sem["base"]]).value_counts().to_dict()
    R = {"genere_utc": h, "bloc": "developpement 2021-2024", "parametres": {"z_court": Z_COURT, "z_aile": Z_AILE, "risque": RISQUE},
         "resultats": r, "portes": portes, "verdict_E01": "passe" if all(portes.values()) else "rejetee", "motifs": motifs}
    (out / f"E01_{h}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str))
    pd.DataFrame([{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in x.items()} for x in sem["base"]]).to_csv(out / f"E01_semaines_{h}.csv", index=False)
    print(json.dumps({"verdict_E01": R["verdict_E01"], "portes": portes, **{k: r[k] for k in ("net_annualise", "sharpe_annualise", "par_annee", "drawdown_max", "semaines_avec_position")}}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
