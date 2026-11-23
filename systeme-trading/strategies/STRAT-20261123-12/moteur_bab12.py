#!/usr/bin/env python3
"""Moteur de STRAT-20261123-12 (fiche § 3 et § 4) : bêta faible contre bêta fort sur les perpétuels USDT liquides.

Les dates sont celles des bougies journalières (ouverture à 00:00 UTC) : la clôture de la bougie du dimanche est le prix
du lundi à 00:00 UTC, heure de décision de la fiche. Le hors échantillon (à partir du 01/07/2024) est verrouillé.
Usage (serveur) : python -B moteur_bab12.py --cache /root/cache_binance_vision --sorties resultats
"""
import argparse, datetime as dt, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
VERROU = pd.Timestamp("2024-07-01")
LIQ_MIN, AGE_MIN, FEN_BETA, OBS_MIN, PART, NMIN, B_MIN, B_MAX, COUT = 20e6, 90, 60, 50, 0.20, 3, 0.2, 3.0, 0.001
INDICES = {"BTCDOMUSDT", "DEFIUSDT", "FOOTBALLUSDT", "BLUEBIRDUSDT"}
STABLES = {"USDC", "BUSD", "TUSD", "FDUSD", "DAI", "USDP"}
BLOCS = {"developpement": ("2021-01-03", "2022-12-25"), "validation": ("2023-01-01", "2024-06-23")}   # dimanches de décision


def exclu(s):
    return s in INDICES or "DOM" in s or s[:-4] in STABLES


def univers(close, vol, d):
    """Contrats éligibles à la décision d (bougie du dimanche) : âge, liquidité, exclusions."""
    h = close[close.index <= d]
    out = []
    for s in close.columns:
        if exclu(s) or not np.isfinite(h[s].iloc[-1]):
            continue
        prem = h[s].first_valid_index()
        if prem is None or prem > d - pd.Timedelta(days=AGE_MIN):
            continue
        med = vol[s][(vol.index <= d) & (vol.index > d - pd.Timedelta(days=30))].median()
        if np.isfinite(med) and med >= LIQ_MIN:
            out.append(s)
    return out


def betas(close, d, syms, ref="BTCUSDT"):
    r = np.log(close[close.index <= d]).diff().iloc[-FEN_BETA:]
    x = r[ref]
    out = {}
    for s in syms:
        y = r[s]
        ok = y.notna() & x.notna()
        if ok.sum() < OBS_MIN:
            continue
        b = np.cov(y[ok], x[ok], ddof=1)[0, 1] / np.var(x[ok], ddof=1)
        out[s] = float(min(B_MAX, max(B_MIN, b)))
    return out


def poids(b):
    """Poids signés : 20 % de bêtas faibles à l'achat, 20 % de forts à la vente, neutres au bêta, brut 100 %."""
    if not b:
        return {}
    tri = sorted(b, key=lambda s: (b[s], s))
    n = max(NMIN, int(math.floor(PART * len(tri))))
    if 2 * n > len(tri):
        return {}
    bas, haut = tri[:n], tri[-n:]
    bl, bh = np.mean([b[s] for s in bas]), np.mean([b[s] for s in haut])
    gl, gh = 1 / bl, 1 / bh
    tot = gl + gh
    w = {s: (gl / tot) / n for s in bas}
    w.update({s: -(gh / tot) / n for s in haut})
    return w


def rendement_contrat(close, s, d, d7):
    """Rendement de d à d7 ; un contrat retiré sort à sa dernière clôture connue après d."""
    p0 = close.at[d, s]
    seg = close.loc[(close.index > d) & (close.index <= d7), s].dropna()
    return float(seg.iloc[-1] / p0 - 1) if len(seg) else 0.0


def financement_semaine(fin, s, d, d7):
    f = fin.get(s)
    if f is None or not len(f):
        return 0.0
    t0, t1 = d + pd.Timedelta(days=1), d7 + pd.Timedelta(days=1)       # du lundi 00:00 exclu au lundi suivant 00:00 inclus
    return float(f[(f.index > t0) & (f.index <= t1)].sum())


def simuler(close, vol, fin, debut, fin_bloc, cout=COUT):
    assert pd.Timestamp(fin_bloc) + pd.Timedelta(days=8) <= VERROU, "hors échantillon verrouillé"
    dims = pd.date_range(debut, fin_bloc, freq="W-SUN")
    prec, rows, contrib = {}, [], []
    for d in dims:
        d7 = d + pd.Timedelta(days=7)
        w = poids(betas(close, d, univers(close, vol, d)))
        rot = sum(abs(w.get(s, 0) - prec.get(s, 0)) for s in set(w) | set(prec))
        brut, fi = 0.0, 0.0
        for s, x in w.items():
            r = rendement_contrat(close, s, d, d7)
            f = financement_semaine(fin, s, d, d7)
            brut += x * r
            fi += -x * f
            contrib.append({"dimanche": d, "symbole": s, "poids": x, "contribution": x * r - x * f})
        rows.append({"dimanche": d, "positions": len(w), "brut": brut, "financement": fi, "couts": cout * rot,
                     "net": brut + fi - cout * rot, "btc": rendement_contrat(close, "BTCUSDT", d, d7)})
        prec = w
    return pd.DataFrame(rows).set_index("dimanche"), pd.DataFrame(contrib)


def mesures(s):
    sh = float(s.mean() / s.std(ddof=1) * math.sqrt(52)) if s.std(ddof=1) > 0 else None
    cap = (1 + s).cumprod()
    return {"semaines": len(s), "net_annualise": float(s.sum() / (len(s) / 52)), "sharpe": sh,
            "baisse_max": float((1 - cap / cap.cummax()).max())}


def evaluer(res, res2, contrib):
    out, portes = {}, {}
    for k in res:
        a, b = res[k], res2[k]
        out[k] = {"base": mesures(a["net"]), "couts_doubles": mesures(b["net"]), "correlation_btc": float(a["net"].corr(a["btc"])),
                  "brut_annualise": float(a["brut"].sum() / (len(a) / 52)), "financement_annualise": float(a["financement"].sum() / (len(a) / 52)),
                  "couts_annualises": float(a["couts"].sum() / (len(a) / 52))}
    tout = pd.concat(res.values())
    an = tout["net"].groupby(tout.index.year).sum()
    meilleur = an.idxmax()
    gain = tout["net"].sum()
    c = contrib.groupby("symbole")["contribution"].sum()
    mo = tout["net"].groupby(tout.index.strftime("%Y-%m")).sum()
    out["par_annee"] = {str(y): float(v) for y, v in an.items()}
    out["concentration"] = {"part_max_contrat": float(c.max() / gain) if gain > 0 else None, "contrat": c.idxmax() if len(c) else None,
                            "part_max_mois": float(mo.max() / gain) if gain > 0 else None, "mois": mo.idxmax() if len(mo) else None}
    out["semaines_avec_position"] = int((tout["positions"] > 0).sum())
    portes["P1_sharpe_0_8_chaque_bloc"] = all((out[k]["base"]["sharpe"] or -9) >= 0.8 for k in res)
    portes["P2_annees_positives_hors_meilleure"] = all(v > 0 for y, v in an.items() if y != meilleur)
    portes["P3_couts_doubles_positifs"] = all(out[k]["couts_doubles"]["net_annualise"] > 0 for k in res)
    portes["P4_correlation_btc_bornee"] = all(abs(out[k]["correlation_btc"]) <= 0.3 for k in res)
    portes["P5_concentration"] = gain > 0 and out["concentration"]["part_max_contrat"] <= 0.25 and out["concentration"]["part_max_mois"] <= 0.40
    portes["P6_au_moins_120_semaines"] = out["semaines_avec_position"] >= 120
    return out, {k: bool(v) for k, v in portes.items()}


def main():
    import donnees_binance as db
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--sorties", default=str(ICI / "resultats"))
    a = ap.parse_args()
    src = db.VisionHTTP(Path(a.cache))
    syms = [s for s in db.symboles_usdt(src) if not exclu(s)]
    debut_l, fin_l = pd.Timestamp("2020-09-01"), VERROU
    j = db.charger_jours(src, syms, debut_l, fin_l)
    close, vol = j["close"], j["volume"]
    close, vol = close[close.index < VERROU], vol[vol.index < VERROU]
    # financement des seuls contrats qui entrent au moins une fois dans l'univers
    entres = set()
    for d in pd.date_range(BLOCS["developpement"][0], BLOCS["validation"][1], freq="W-SUN"):
        entres |= set(univers(close, vol, d))
    fin = {s: db.charger_symbole(src, s, "financement", debut_l, fin_l) for s in sorted(entres)}
    res, res2, contribs = {}, {}, []
    for k, (d0, d1) in BLOCS.items():
        res[k], c = simuler(close, vol, fin, d0, d1)
        res2[k], _ = simuler(close, vol, fin, d0, d1, 2 * COUT)
        contribs.append(c)
    out, portes = evaluer(res, res2, pd.concat(contribs))
    h = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    R = {"genere_utc": h, "symboles_archives": len(syms), "contrats_entres_dans_l_univers": len(entres), "resultats": out, "portes": portes,
         "verdict_E01": "passe" if all(portes.values()) else "rejetee"}
    o = Path(a.sorties)
    o.mkdir(parents=True, exist_ok=True)
    (o / f"E01_{h}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str))
    pd.concat(res).to_csv(o / f"E01_semaines_{h}.csv")
    print(json.dumps({"verdict_E01": R["verdict_E01"], "portes": portes, "par_annee": out["par_annee"],
                      **{k: out[k] for k in BLOCS}}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
