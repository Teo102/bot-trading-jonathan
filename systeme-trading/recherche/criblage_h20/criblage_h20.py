#!/usr/bin/env python3
"""Criblage de H20 (écart de financement Binance–Bybit), règle figée le 23/11/2026 avant tout téléchargement
(`REGLE_CRIBLAGE_H20.md`). Lit le financement des deux plateformes et le volume journalier de Binance (univers).
Aucun prix d'entrée ni de sortie : le résultat est une borne haute. Aucun ordre, aucune clé.

Usage (serveur) : python -B criblage_h20.py --cache /root/cache_binance_vision --cache-bybit /root/cache_bybit_financement
"""
from __future__ import annotations

import argparse, datetime as dt, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
RACINE_DEPOT = ICI.parent.parent
sys.path.insert(0, str(RACINE_DEPOT / "strategies" / "STRAT-20261031-03"))

DEBUT, FIN = pd.Timestamp("2021-01-01"), pd.Timestamp("2026-11-01")
FEN = pd.Timedelta(hours=8)
ENTREE, SORTIE, MAX_PAIRES, TAILLE_UNIVERS, AGE_MIN = 0.0002, 0.00005, 10, 30, pd.Timedelta(days=60)
FRAIS_BINANCE, FRAIS_BYBIT, GLISS_TOP10, GLISS_AUTRES, FRAIS_TENEUR = 0.0005, 0.00055, 0.0002, 0.0005, 0.0002
LEVIER_CAPITAL = 2.0          # marge pleine de chaque côté : capital = 2 × notionnel
BYBIT = "https://api.bybit.com/v5/market/funding/history"


# ---------------------------------------------------------------- fonctions pures (testées)

def fenetres(versements: pd.Series) -> pd.Series:
    """Somme des versements par fenêtre de 8 h ; index = fin de la fenêtre. Un versement en T appartient à la
    fenêtre qui se termine en T (T moins une minute, arrondi vers le bas à 8 h, plus 8 h)."""
    if versements is None or not len(versements):
        return pd.Series(dtype=float)
    debut = (versements.index - pd.Timedelta(minutes=1)).floor("8h")
    return versements.groupby(debut + FEN).sum().sort_index()


def trimestres(debut=DEBUT, fin=FIN):
    return list(pd.date_range(debut, fin - pd.Timedelta(days=1), freq="QS"))


def choisir_univers(volumes_mois: pd.Series, premier_bin: dict, premier_byb: dict, q: pd.Timestamp, n=TAILLE_UNIVERS):
    """Les n plus gros volumes du mois précédant q parmi les symboles cotés sur les deux plateformes depuis 60 jours."""
    out = []
    for s, v in volumes_mois.sort_values(ascending=False).items():
        if not (v > 0):
            continue
        a, b = premier_bin.get(s), premier_byb.get(s)
        if a is not None and b is not None and a <= q - AGE_MIN and b <= q - AGE_MIN:
            out.append(s)
            if len(out) == n:
                break
    return out


def trimestre_de(t: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(year=t.year, month=3 * ((t.month - 1) // 3) + 1, day=1)


def cout_ordre(rang: int, teneur: bool) -> float:
    """Coût d'un ordre sur une jambe (hors frais propres à la plateforme pour le preneur)."""
    return 0.0 if teneur else (GLISS_TOP10 if rang <= 10 else GLISS_AUTRES)


def cout_aller(rang: int, teneur: bool = False) -> float:
    """Entrée ou sortie : deux ordres, un sur chaque plateforme."""
    if teneur:
        return 2 * FRAIS_TENEUR
    return FRAIS_BINANCE + FRAIS_BYBIT + 2 * cout_ordre(rang, False)


def simuler(diff: pd.DataFrame, univers: dict, debut=DEBUT, fin=FIN):
    """diff : écart Bybit − Binance par fenêtre (index = fin de fenêtre, colonnes = symboles, NaN si une plateforme
    manque). univers : {début de trimestre: [symboles classés]}. Renvoie les positions et les flux datés, en
    fraction du notionnel d'une position (le passage au capital se fait ensuite)."""
    D = diff.rolling(3, min_periods=3).mean()
    ouvertes, positions, flux = {}, [], []          # flux : (t, symbole, nature, montant_preneur, montant_teneur)
    temps = diff.index[(diff.index > debut) & (diff.index <= fin)]

    def fermer(s, t, motif):
        p = ouvertes.pop(s)
        c, ct = cout_aller(p["rang"]), cout_aller(p["rang"], True)
        flux.append((t, s, "sortie", -c, -ct))
        p.update({"sortie": t, "motif": motif, "couts": p["couts"] + c, "couts_teneur": p["couts_teneur"] + ct})
        positions.append(p)

    for t in temps:
        u = univers.get(trimestre_de(t), [])
        rang = {s: i + 1 for i, s in enumerate(u)}
        # 1. revenu de la fenêtre qui se termine en t, pour les positions ouvertes avant t
        for s in list(ouvertes):
            x = diff.at[t, s] if s in diff.columns else np.nan
            if not np.isfinite(x):
                fermer(s, t, "fenetre_manquante")
                continue
            r = ouvertes[s]["signe"] * x
            ouvertes[s]["brut"] += r
            ouvertes[s]["fenetres"] += 1
            flux.append((t, s, "financement", r, r))
        # 2. sorties
        for s in list(ouvertes):
            d = D.at[t, s] if s in D.columns else np.nan
            if s not in rang:
                fermer(s, t, "hors_univers")
            elif not np.isfinite(d):
                fermer(s, t, "fenetre_manquante")
            elif abs(d) < SORTIE or np.sign(d) != ouvertes[s]["signe"]:
                fermer(s, t, "seuil")
        # 3. entrées, plus grands |D| d'abord, égalité par ordre alphabétique
        libres = MAX_PAIRES - len(ouvertes)
        if libres > 0:
            cands = []
            for s in u:
                if s in ouvertes or s not in D.columns:
                    continue
                d = D.at[t, s]
                if np.isfinite(d) and abs(d) >= ENTREE:
                    cands.append((-abs(d), s, d))
            for _, s, d in sorted(cands)[:libres]:
                c, ct = cout_aller(rang[s]), cout_aller(rang[s], True)
                ouvertes[s] = {"symbole": s, "entree": t, "signe": int(np.sign(d)), "D_entree": float(d), "rang": rang[s],
                               "brut": 0.0, "fenetres": 0, "couts": c, "couts_teneur": ct}
                flux.append((t, s, "entree", -c, -ct))
    for s in list(ouvertes):
        fermer(s, temps[-1] if len(temps) else fin, "fin_de_periode")
    f = pd.DataFrame(flux, columns=["t", "symbole", "nature", "preneur", "teneur"])
    p = pd.DataFrame(positions)
    if len(p):
        p["net"] = p["brut"] - p["couts"]
        p["net_teneur"] = p["brut"] - p["couts_teneur"]
    return p, f


def au_capital(montant_notionnel: float, levier_capital=LEVIER_CAPITAL) -> float:
    """Une position vaut 1/10 du notionnel total ; le capital vaut levier_capital × notionnel total."""
    return montant_notionnel / MAX_PAIRES / levier_capital


def blocs_et_criteres(f: pd.DataFrame, p: pd.DataFrame, debut=DEBUT, fin=FIN):
    f = f.copy()
    f["cap"] = f["preneur"].map(au_capital)
    f["cap_teneur"] = f["teneur"].map(au_capital)
    f["an"] = f["t"].dt.year
    f["mois"] = f["t"].dt.strftime("%Y-%m")
    blocs = {}
    for an in range(debut.year, fin.year + 1):
        a, b = max(pd.Timestamp(f"{an}-01-01"), debut), min(pd.Timestamp(f"{an + 1}-01-01"), fin)
        if b <= a:
            continue
        g = f[(f["t"] > a) & (f["t"] <= b)]
        duree = (b - a).days / 365.25
        fin_ = g[g.nature == "financement"]["cap"].sum()
        couts = -g[g.nature != "financement"]["cap"].sum()
        net = g["cap"].sum()
        blocs[str(an)] = {"duree_annees": round(duree, 3), "financement_brut": fin_, "couts": couts, "net": net,
                          "net_annualise": net / duree, "net_annualise_teneur": g["cap_teneur"].sum() / duree,
                          "net_annualise_levier3": 3 * net / duree,
                          "positions_ouvertes": int(((p["entree"] > a) & (p["entree"] <= b)).sum()) if len(p) else 0}
    na = {k: v["net_annualise"] for k, v in blocs.items()}
    meilleur = max(na, key=na.get)
    autres = [k for k in blocs if k != meilleur]
    hors = sum(blocs[k]["net"] for k in autres) / sum(blocs[k]["duree_annees"] for k in autres)
    total = f["cap"].sum()
    par_paire = f.groupby("symbole")["cap"].sum()
    par_mois = f.groupby("mois")["cap"].sum()
    crit = {
        "1_au_moins_4_blocs_a_5pct": {"valeur": sum(v >= 0.05 for v in na.values()), "seuil": 4},
        "2_positif_chaque_bloc_hors_meilleur": {"valeur": {k: round(na[k], 5) for k in autres}, "meilleur": meilleur},
        "3_hors_meilleure_annee_3pct": {"valeur": hors, "seuil": 0.03},
        "4_concentration": {"part_max_paire": float(par_paire.max() / total) if total > 0 else None,
                            "paire": par_paire.idxmax() if len(par_paire) else None,
                            "part_max_mois": float(par_mois.max() / total) if total > 0 else None,
                            "mois": par_mois.idxmax() if len(par_mois) else None},
        "5_au_moins_100_positions": {"valeur": int(len(p)), "seuil": 100},
    }
    ok = {
        "1": crit["1_au_moins_4_blocs_a_5pct"]["valeur"] >= 4,
        "2": all(na[k] > 0 for k in autres),
        "3": hors >= 0.03,
        "4": total > 0 and crit["4_concentration"]["part_max_paire"] <= 0.30 and crit["4_concentration"]["part_max_mois"] <= 0.25,
        "5": len(p) >= 100,
    }
    return blocs, crit, ok, {"net_total_capital": total, "net_annualise_total": total / ((fin - debut).days / 365.25)}


# ---------------------------------------------------------------- données

def bybit_financement(sym, cache: Path, session, debut=DEBUT - pd.Timedelta(days=120), fin=FIN):
    """Historique complet de Bybit (linéaire), paginé vers l'arrière, mis en cache. Série indexée à la minute."""
    f = cache / f"{sym}.json"
    if f.exists():
        lignes = json.loads(f.read_text())
    else:
        lignes, fin_ms, debut_ms = [], int(fin.timestamp() * 1000), int(debut.timestamp() * 1000)
        while True:
            for essai in range(6):
                try:
                    r = session.get(BYBIT, params={"category": "linear", "symbol": sym, "endTime": fin_ms, "limit": 200}, timeout=30)
                    j = r.json()
                    break
                except Exception:
                    time.sleep(2 + 3 * essai)
            else:
                raise RuntimeError(f"Bybit injoignable pour {sym}")
            if j.get("retCode") != 0:
                break
            lot = j["result"]["list"]
            if not lot:
                break
            lignes += [(int(x["fundingRateTimestamp"]), float(x["fundingRate"])) for x in lot]
            plus_ancien = min(int(x["fundingRateTimestamp"]) for x in lot)
            if len(lot) < 200 or plus_ancien <= debut_ms:
                break
            fin_ms = plus_ancien - 1
            time.sleep(0.12)
        f.write_text(json.dumps(lignes))
    if not lignes:
        return None
    s = pd.Series({pd.Timestamp(t, unit="ms").round("min"): r for t, r in lignes}).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s[s.index < fin]


def main(argv=None):
    import requests
    import donnees_binance as db
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--cache-bybit", required=True)
    a = ap.parse_args(argv)
    debut_execution = dt.datetime.now(dt.timezone.utc)
    src = db.VisionHTTP(Path(a.cache).expanduser())
    cb = Path(a.cache_bybit).expanduser()
    cb.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    syms = db.symboles_usdt(src)
    Q = trimestres()
    # volumes du mois civil précédant chaque trimestre (Binance)
    volumes = {}
    for q in Q:
        m0 = q - pd.offsets.MonthBegin(1)
        j = db.charger_jours(src, syms, m0, q)
        v = j["volume"]
        volumes[q] = v[(v.index >= m0) & (v.index < q)].sum()
    premier_bin, premier_byb, fin_bin, fin_byb, fen_bin, fen_byb = {}, {}, {}, {}, {}, {}

    def charger(s):
        if s in premier_bin or s in premier_byb or s in fin_bin:
            return
        b = db.charger_symbole(src, s, "financement", DEBUT - pd.Timedelta(days=120), FIN)
        fin_bin[s] = None
        if b is not None and len(b):
            premier_bin[s] = b.index.min()
            fen_bin[s] = fenetres(b)
        y = bybit_financement(s, cb, sess)
        if y is not None and len(y):
            premier_byb[s] = y.index.min()
            fen_byb[s] = fenetres(y)

    univers = {}
    for q in Q:
        classes = volumes[q].sort_values(ascending=False)
        retenus = []
        for s, v in classes.items():                      # on ne charge que ce qu'il faut pour remplir 30 places
            if not (v > 0) or len(retenus) == TAILLE_UNIVERS:
                break
            charger(s)
            if choisir_univers(pd.Series({s: v}), premier_bin, premier_byb, q, 1):
                retenus.append(s)
        univers[q] = retenus
    communs = sorted(set().union(*univers.values()))
    diff = pd.DataFrame({s: fen_byb[s].sub(fen_bin[s]) for s in communs if s in fen_bin and s in fen_byb})   # NaN si une plateforme manque
    diff = diff.sort_index()
    p, f = simuler(diff, univers)
    blocs, crit, ok, tot = blocs_et_criteres(f, p)
    h = debut_execution.strftime("%Y%m%dT%H%M%SZ")
    R = {"genere_utc": h, "regle": "REGLE_CRIBLAGE_H20.md (figée le 23/11/2026)", "borne_haute": "financement seul, sans écart de prix ni liquidation",
         "periode": [str(DEBUT), str(FIN)], "symboles_binance_archives": len(syms), "symboles_communs_utilises": len(communs),
         "univers": {str(q.date()): u for q, u in univers.items()},
         "taille_univers_par_trimestre": {str(q.date()): len(u) for q, u in univers.items()},
         "blocs": blocs, "criteres": crit, "criteres_remplis": ok, "verdict": "passe" if all(ok.values()) else "ecartee", **tot,
         "motifs_de_sortie": p["motif"].value_counts().to_dict() if len(p) else {},
         "duree_mediane_fenetres": float(p["fenetres"].median()) if len(p) else None,
         "part_positions_nettes_positives": float((p["net"] > 0).mean()) if len(p) else None,
         "duree_s": round((dt.datetime.now(dt.timezone.utc) - debut_execution).total_seconds(), 1)}
    (ICI / f"criblage_h20_{h}.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False))
    p.to_csv(ICI / f"positions_h20_{h}.csv", index=False)
    print(json.dumps({"verdict": R["verdict"], "criteres_remplis": ok, "net_annualise_par_bloc": {k: round(v["net_annualise"], 4) for k, v in blocs.items()},
                      "positions": len(p), "symboles_communs": len(communs), "duree_s": R["duree_s"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
