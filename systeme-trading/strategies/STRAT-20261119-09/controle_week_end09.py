#!/usr/bin/env python3
"""Contrôle sans rendement de STRAT-20261119-09 (fiche § 5), lancé sur accord de Jonathan et Téo le 19/11/2026.

Ce que le script lit : la liste des contrats, le volume horaire du week-end (pour l'univers) et, pour chaque
week-end, le prix du perpétuel à la clôture du vendredi et à l'heure de décision, plus les clôtures des jours
ouvrés précédents (pour σ). C'est le mouvement qui DÉFINIT le signal.

Ce qu'il ne lit jamais : aucun prix après l'heure de décision d'un week-end n'entre dans le calcul de ce week-end
(chaque calcul commence par couper les données à la décision ; un test le vérifie avec des prix empoisonnés), et
les données ne sont pas téléchargées au-delà de la dernière décision (lundi 16/11/2026 13:00 UTC). Aucune issue
de position, aucun rendement de stratégie.

Précisions de règles, écrites avant tout rendement et soumises à Jonathan et Téo au gel :
- heures pleines : les bougies de Binance commencent à l'heure pile, donc la décision des actions est prise à
  08:00 New York (1 h 30 avant l'ouverture de 09:30) et la sortie à 12:00 (2 h 30 après) ;
- σ : écart-type des 20 derniers rendements entre deux jours ouvrés consécutifs, clôture à l'heure de clôture du
  groupe ; le rendement du lundi (qui couvre le week-end et la réouverture) est exclu ;
- K = 6 au total par week-end : les matières premières décident d'abord (dimanche), les actions prennent les places
  restantes le lundi, classées par |M|/σ.

Usage : python -I -B controle_week_end09.py [--sorties resultats]
"""
import argparse, collections, datetime as dt, json, time
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, requests

ICI = Path(__file__).resolve().parent
NY, UTC = ZoneInfo("America/New_York"), dt.timezone.utc
FAPI = "https://fapi.binance.com"
K_SIGMA, K_POS, N_SIGMA, SEUIL_VOLUME = 1.0, 6, 20, 0.5e6
MATIERES = ["BZUSDT", "CLUSDT", "XAGUSDT", "XAUUSDT"]
TEMOINS = ["BTCUSDT", "ETHUSDT"]
PREMIER_VENDREDI, DERNIER_VENDREDI = dt.date(2026, 5, 8), dt.date(2026, 11, 13)
VENDREDIS_UNIVERS = [dt.date(2026, 9, 25) + dt.timedelta(weeks=i) for i in range(8)]   # 8 week-ends du 25/09 au 13/11
# Jours fériés de la bourse de New York tombant un vendredi ou un lundi dans la période [calendrier du CME à vérifier au gel]
FERIES = {dt.date(2026, 5, 25): "Memorial Day", dt.date(2026, 6, 19): "Juneteenth",
          dt.date(2026, 7, 3): "Independence Day (observé)", dt.date(2026, 9, 7): "Labor Day"}
APPELS = []
session = requests.Session()


def ny(jour, h, m=0):
    """Heure de New York → datetime UTC naïf (comme les index des bougies)."""
    return dt.datetime(jour.year, jour.month, jour.day, h, m, tzinfo=NY).astimezone(UTC).replace(tzinfo=None)


def calendrier(vendredi, groupe):
    """Clôture du vendredi, décision, réouverture et sortie (H = 2 h, en heures pleines), en UTC naïf."""
    if groupe == "mp":    # CME Globex : vendredi 17:00 → dimanche 18:00
        d = vendredi + dt.timedelta(days=2)
        return {"cloture": ny(vendredi, 17), "decision": ny(d, 17), "reouverture": ny(d, 18), "sortie": ny(d, 20)}
    d = vendredi + dt.timedelta(days=3)    # actions : vendredi 16:00 → lundi 09:30
    return {"cloture": ny(vendredi, 16), "decision": ny(d, 8), "reouverture": ny(d, 9, 30), "sortie": ny(d, 12)}


def exclu(vendredi):
    return vendredi in FERIES or (vendredi + dt.timedelta(days=3)) in FERIES


def heure_cloture(groupe):
    return 17 if groupe == "mp" else 16


def couper(df, t):
    """Toutes les lectures d'un week-end passent par ici : rien après l'heure de décision."""
    return df[df.index <= t]


def sigma(df, vendredi, groupe):
    """σ des 20 derniers rendements entre jours ouvrés consécutifs, lundi exclu, clôtures ≤ clôture du vendredi."""
    h = heure_cloture(groupe)
    jours = [vendredi - dt.timedelta(days=i) for i in range(70, -1, -1)]
    cl = [(j, df["open"].get(ny(j, h))) for j in jours if j.weekday() < 5]
    r = [b / a - 1 for (ja, a), (jb, b) in zip(cl, cl[1:])
         if a is not None and b is not None and (jb - ja).days == 1 and jb.weekday() != 0]
    return float(np.std(r[-N_SIGMA:], ddof=1)) if len(r) >= N_SIGMA else None


def evenement(df, vendredi, groupe):
    """Mouvement du week-end M, σ et signal pour un contrat, à partir des seules données ≤ décision."""
    c = calendrier(vendredi, groupe)
    df = couper(df, c["decision"])
    p0, p1 = df["open"].get(c["cloture"]), df["open"].get(c["decision"])
    s = sigma(df, vendredi, groupe)
    if p0 is None or p1 is None or s is None or s <= 0:
        return None
    m = p1 / p0 - 1
    return {"M": m, "sigma": s, "rapport": abs(m) / s, "signal": abs(m) >= K_SIGMA * s, "sens": -1 if m > 0 else 1}


def plafonner(sig_mp, sig_act, k=K_POS):
    """Places du week-end : matières premières d'abord, puis actions dans les places restantes, par |M|/σ décroissant,
    égalité tranchée par l'ordre alphabétique. Entrées : listes de (symbole, rapport)."""
    tri = lambda L: sorted(L, key=lambda x: (-x[1], x[0]))
    mp = tri(sig_mp)[:k]
    return mp, tri(sig_act)[:k - len(mp)]


def get(url, params):
    for essai in range(5):
        try:
            r = session.get(url, params=params, timeout=60)
            APPELS.append(r.status_code)
            if r.status_code == 200:
                time.sleep(0.25)
                return r.json()
            if r.status_code in (400, 404):
                return None
        except requests.exceptions.RequestException:
            APPELS.append("erreur")
        time.sleep(3 + 3 * essai)
    raise RuntimeError(f"échec {url} {params}")


def bougies(sym, debut, fin):
    """Bougies 1 h du perpétuel, de debut à fin inclus (UTC naïf) : ouverture et volume en USDT."""
    lignes, t = [], int(debut.replace(tzinfo=UTC).timestamp() * 1000)
    f = int(fin.replace(tzinfo=UTC).timestamp() * 1000)
    while t <= f:
        k = get(f"{FAPI}/fapi/v1/klines", {"symbol": sym, "interval": "1h", "startTime": t, "endTime": f, "limit": 1500}) or []
        if not k:
            break
        lignes += k
        t = int(k[-1][0]) + 3_600_000
        if len(k) < 1500:
            break
    if not lignes:
        return pd.DataFrame(columns=["open", "qv"])
    df = pd.DataFrame({"open": [float(x[1]) for x in lignes], "qv": [float(x[7]) for x in lignes]},
                      index=pd.to_datetime([int(x[0]) for x in lignes], unit="ms"))
    return df[~df.index.duplicated()].sort_index()


def volume_week_end(df, vendredis):
    """Volume horaire médian (USDT) des heures de fermeture des actions, de la clôture du vendredi à la décision."""
    v = [df.loc[(df.index >= c["cloture"]) & (df.index < c["decision"]), "qv"]
         for c in (calendrier(f, "act") for f in vendredis)]
    v = pd.concat(v) if v else pd.Series(dtype=float)
    return float(v.median()) if len(v) else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sorties", default=str(ICI / "resultats"))
    a = ap.parse_args()
    debut = dt.datetime.now(UTC)
    coupure = calendrier(DERNIER_VENDREDI, "act")["decision"]          # 16/11/2026 13:00 UTC, aucune donnée au-delà
    ex = get(f"{FAPI}/fapi/v1/exchangeInfo", None)
    actions = sorted(x["symbol"] for x in ex["symbols"] if x.get("underlyingType") == "EQUITY"
                     and x.get("status") == "TRADING" and x.get("quoteAsset") == "USDT")
    # 1. univers des actions : volume horaire médian du week-end sur 8 semaines
    vols, d8 = {}, calendrier(VENDREDIS_UNIVERS[0], "act")["cloture"] - dt.timedelta(hours=1)
    for s in actions:
        vols[s] = volume_week_end(bougies(s, d8, coupure), VENDREDIS_UNIVERS)
    univers = sorted(s for s, v in vols.items() if v >= SEUIL_VOLUME)
    # 2. historique complet de l'univers, des matières premières et des témoins, coupé à la dernière décision
    d0 = ny(PREMIER_VENDREDI - dt.timedelta(days=75), 0)
    data = {s: bougies(s, d0, coupure) for s in MATIERES + univers + TEMOINS}
    vendredis = [PREMIER_VENDREDI + dt.timedelta(weeks=i) for i in range((DERNIER_VENDREDI - PREMIER_VENDREDI).days // 7 + 1)]
    lignes, evts = [], []
    for v in vendredis:
        if exclu(v):
            lignes.append({"vendredi": str(v), "exclu": True})
            continue
        L = {"vendredi": str(v), "exclu": False}
        sig = {}
        for g, syms in (("mp", MATIERES), ("act", univers), ("temoin_mp", TEMOINS), ("temoin_act", TEMOINS)):
            gc = "mp" if g in ("mp", "temoin_mp") else "act"
            e = {s: evenement(data[s], v, gc) for s in syms}
            e = {s: x for s, x in e.items() if x is not None}
            sig[g] = [(s, x["rapport"], x["sens"]) for s, x in e.items() if x["signal"]]
            L[f"{g}_eligibles"], L[f"{g}_signaux"] = len(e), len(sig[g])
            L[f"{g}_achats"] = sum(1 for _, _, sens in sig[g] if sens > 0)
            for s, x in e.items():      # tous les événements éligibles : |M|/σ et sens, jamais d'issue
                evts.append({"vendredi": str(v), "groupe": g, "symbole": s, "rapport": round(x["rapport"], 3),
                             "sens": "achat" if x["sens"] > 0 else "vente", "signal": x["signal"]})
        mp, act = plafonner([(s, r) for s, r, _ in sig["mp"]], [(s, r) for s, r, _ in sig["act"]])
        L["positions_mp"], L["positions_act"] = len(mp), len(act)
        n = L["mp_signaux"] + L["act_signaux"]
        L["part_meme_sens"] = (max(L["mp_achats"] + L["act_achats"], n - L["mp_achats"] - L["act_achats"]) / n) if n else None
        lignes.append(L)
    df = pd.DataFrame(lignes)
    c = df[~df["exclu"]]
    res = {
        "genere_utc": debut.strftime("%Y-%m-%dT%H:%M:%SZ"), "coupure_donnees_utc": str(coupure),
        "regle": "mouvement définissant le signal seulement ; aucun prix après la décision ; aucun rendement",
        "parametres": {"k": K_SIGMA, "K": K_POS, "N_sigma": N_SIGMA, "seuil_volume_usdt": SEUIL_VOLUME},
        "actions_cotees": len(actions), "univers_actions": univers,
        "volumes_univers": {s: round(vols[s]) for s in univers},
        "proches_du_seuil": {s: round(v) for s, v in sorted(vols.items(), key=lambda x: -x[1]) if 0.3e6 <= v < SEUIL_VOLUME},
        "week_ends": len(df), "week_ends_exclus": [str(v) for v in vendredis if exclu(v)], "week_ends_comptes": len(c),
        "signaux_par_week_end_moyenne": {g: round(float(c[f"{g}_signaux"].mean()), 2) for g in ("mp", "act", "temoin_mp", "temoin_act")},
        "signaux_total": {g: int(c[f"{g}_signaux"].sum()) for g in ("mp", "act", "temoin_mp", "temoin_act")},
        "positions_apres_plafond_moyenne": round(float((c["positions_mp"] + c["positions_act"]).mean()), 2),
        "positions_apres_plafond_total": int((c["positions_mp"] + c["positions_act"]).sum()),
        "week_ends_sans_signal": int(((c["mp_signaux"] + c["act_signaux"]) == 0).sum()),
        "week_ends_au_plafond": int(((c["mp_signaux"] + c["act_signaux"]) > K_POS).sum()),
        "part_meme_sens_mediane": round(float(c["part_meme_sens"].dropna().median()), 3),
        "projection_52_week_ends_positions": round(float((c["positions_mp"] + c["positions_act"]).mean()) * 52),
        "exigence_2_signaux_par_week_end": bool((c["mp_signaux"] + c["act_signaux"]).mean() >= 2),
        "appels": {"total": len(APPELS), "erreurs": [x for x in APPELS if x != 200]},
    }
    res["duree_s"] = round((dt.datetime.now(UTC) - debut).total_seconds(), 1)
    out = Path(a.sorties)
    out.mkdir(parents=True, exist_ok=True)
    h = debut.strftime("%Y%m%dT%H%M%SZ")
    (out / f"controle_{h}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    df.to_csv(out / f"controle_week_ends_{h}.csv", index=False)
    pd.DataFrame(evts).to_csv(out / f"controle_evenements_{h}.csv", index=False)
    (out / f"univers_{h}.txt").write_text("\n".join(MATIERES + univers) + "\n")
    print(json.dumps({k: res[k] for k in ("univers_actions", "week_ends_comptes", "signaux_par_week_end_moyenne",
                                          "positions_apres_plafond_moyenne", "exigence_2_signaux_par_week_end", "duree_s")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
