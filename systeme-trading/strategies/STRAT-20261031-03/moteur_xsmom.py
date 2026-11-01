#!/usr/bin/env python3
"""Moteur de recherche de STRAT-20261031-03, momentum transversal résiduel (fiche § 1.3 à § 1.5).

Code neuf, sans réseau, sans clé, sans ordre. Il ne lit aucun fichier de marché : il reçoit des tableaux
en mémoire. Avant E01, il ne tourne que sur des données synthétiques (fiche § 1.7).

Entrées (index UTC, colonnes = symboles) :
- `jours` : dict de DataFrame journaliers, clés "close" et "volume" (volume en USDT). Index = date du jour UTC.
- `heures` : dict de DataFrame 1 h, clés "open", "close", "mark_high", "mark_low". Index = ouverture de la bougie.
- `financement` : DataFrame d'événements de financement, index = heure de l'événement, valeur = taux.

Conventions écrites (hypothèses du moteur, à relire avec la fiche) :
- H1. Un rendement journalier manquant dans la fenêtre de bêta (60 j) exclut le symbole du classement de la semaine.
- H2. Le financement s'applique au notionnel d'entrée de la ligne, pour chaque événement dans ]entrée ; sortie].
- H3. « Vivant » : volume non nul le jour t − 1, lu sur les seules données antérieures à t.
- H4. Une ligne stoppée ou délistée ne revient au portefeuille qu'au lundi suivant (fiche § 1.3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

UN_JOUR = pd.Timedelta(days=1)
UNE_HEURE = pd.Timedelta(hours=1)


@dataclass(frozen=True)
class Params:
    taille_univers: int = 30
    fenetre_volume: int = 30
    anciennete: int = 90
    fenetre_classement: int = 21
    fenetre_beta: int = 60
    k: int = 3
    stop: float | None = 0.30
    frais: float = 0.0005
    glissement: float = 0.0005
    glissement_stop: float = 0.0030
    facteur: str = "BTC"
    exclus: frozenset = field(default_factory=frozenset)


# ---------------------------------------------------------------- nettoyage

def couper_zombies(jours: dict, heures: dict, financement: pd.DataFrame | None):
    """Coupe chaque série après son dernier jour de volume non nul (fiche § 2.4), financement compris.

    Retourne des copies et le dict {symbole: dernier jour de volume}."""
    vol = jours["volume"]
    dernier = {}
    jours = {k: v.copy() for k, v in jours.items()}
    heures = {k: v.copy() for k, v in heures.items()}
    financement = None if financement is None else financement.copy()
    for s in vol.columns:
        actifs = vol.index[vol[s].fillna(0) > 0]
        if len(actifs) == 0:
            for k in jours:
                jours[k][s] = np.nan
            for k in heures:
                heures[k][s] = np.nan
            if financement is not None and s in financement:
                financement[s] = np.nan
            dernier[s] = None
            continue
        fin = actifs[-1]
        dernier[s] = fin
        limite = fin + UN_JOUR  # fin du dernier jour actif
        for k in jours:
            jours[k].loc[jours[k].index > fin, s] = np.nan
        for k in heures:
            heures[k].loc[heures[k].index >= limite, s] = np.nan
        if financement is not None and s in financement:
            financement.loc[financement.index >= limite, s] = np.nan
    return jours, heures, financement, dernier


# ---------------------------------------------------------------- univers et signal

def univers(jours: dict, t: pd.Timestamp, p: Params) -> list[str]:
    """Univers du lundi t, lu sur les seuls jours < t (fiche § 1.3)."""
    vol = jours["volume"].loc[jours["volume"].index < t]
    if vol.empty:
        return []
    candidats = []
    veille = t - UN_JOUR
    for s in vol.columns:
        if s == p.facteur or s in p.exclus:
            continue
        v = vol[s]
        actifs = v.index[v.fillna(0) > 0]
        if len(actifs) == 0 or actifs[0] > t - pd.Timedelta(days=p.anciennete):
            continue
        if veille not in v.index or not (v.get(veille, 0) or 0) > 0:
            continue
        fenetre = pd.date_range(t - pd.Timedelta(days=p.fenetre_volume), veille, freq="D")
        med = v.reindex(fenetre).fillna(0).median()
        candidats.append((-med, s))
    candidats.sort()
    return [s for _, s in candidats[: p.taille_univers]]


def scores(jours: dict, t: pd.Timestamp, noms: list[str], p: Params) -> pd.Series:
    """S_i = somme sur 21 j de (r_i − β_i r_BTC), β sur 60 j, jours < t seulement."""
    close = jours["close"].loc[jours["close"].index < t]
    r = np.log(close).diff()
    fen = r.iloc[-p.fenetre_beta:]
    if len(fen) < p.fenetre_beta or fen[p.facteur].isna().any():
        return pd.Series(dtype=float)
    x = fen[p.facteur].to_numpy()
    out = {}
    for s in noms:
        y = fen[s].to_numpy()
        if np.isnan(y).any():  # H1
            continue
        xc = x - x.mean()
        beta = float((xc * (y - y.mean())).sum() / (xc * xc).sum())
        resid = y[-p.fenetre_classement:] - beta * x[-p.fenetre_classement:]
        out[s] = float(resid.sum())
    return pd.Series(out, dtype=float)


def selection(sc: pd.Series, k: int) -> tuple[list[str], list[str]]:
    """Long des k plus hauts, short des k plus bas ; égalité départagée par ordre alphabétique."""
    if len(sc) < 2 * k:
        return [], []
    df = pd.DataFrame({"s": sc.index, "v": sc.values})
    hauts = df.sort_values(["v", "s"], ascending=[False, True])["s"].tolist()[:k]
    bas = df.sort_values(["v", "s"], ascending=[True, True])["s"].tolist()[:k]
    return hauts, bas


def signal(jours: dict, t: pd.Timestamp, p: Params) -> tuple[list[str], list[str]]:
    return selection(scores(jours, t, univers(jours, t, p), p), p.k)


# ---------------------------------------------------------------- exécution d'une ligne

def jouer_ligne(heures: dict, financement, s: str, sens: int, t_in: pd.Timestamp, t_out: pd.Timestamp,
                notionnel: float, p: Params) -> dict:
    """Une ligne de la semaine, de t_in (ouverture 1 h) à t_out (ouverture 1 h), stop et délistage compris.

    Le coût d'entrée et de sortie n'est pas compté ici : il dépend du portefeuille voisin (rotation)."""
    o = heures["open"][s]
    px_in = o.get(t_in, np.nan)
    if not np.isfinite(px_in):
        return {"symbole": s, "sens": sens, "statut": "absent"}
    fen = heures["open"].index[(heures["open"].index >= t_in) & (heures["open"].index < t_out)]
    niveau = None if p.stop is None else px_in * (1 - sens * p.stop)
    sortie, t_sortie, statut = None, t_out, "semaine"
    for h in fen:
        oh = o.get(h, np.nan)
        if not np.isfinite(oh):  # données finies : délistage en cours de semaine
            prec = h - UNE_HEURE
            sortie = heures["close"][s].get(prec, np.nan)
            t_sortie, statut = h, "delistage"
            break
        if niveau is not None:
            touche = (heures["mark_low"][s][h] <= niveau) if sens > 0 else (heures["mark_high"][s][h] >= niveau)
            if touche:
                brut = min(niveau, oh) if sens > 0 else max(niveau, oh)  # pire du niveau et de l'ouverture
                sortie = brut * (1 - sens * p.glissement_stop)
                t_sortie, statut = h, "stop"
                break
    if sortie is None:
        px_out = o.get(t_out, np.nan)
        if not np.isfinite(px_out):  # plus de bougie à l'heure de sortie
            prec = t_out - UNE_HEURE
            sortie = heures["close"][s].get(prec, np.nan)
            statut = "delistage"
        else:
            sortie = px_out
    rend = sens * (sortie / px_in - 1)
    fin_ = 0.0
    if financement is not None and s in financement:
        ev = financement[s]
        ev = ev[(ev.index > t_in) & (ev.index <= t_sortie)].dropna()
        fin_ = float(-sens * ev.sum() * notionnel)  # H2 : long paie un taux positif
    cout_sortie_force = 0.0
    if statut == "stop":
        cout_sortie_force = notionnel * (1 + rend) * p.frais  # glissement de stop déjà dans le prix
    elif statut == "delistage":
        cout_sortie_force = notionnel * (1 + rend) * (p.frais + p.glissement)
    return {"symbole": s, "sens": sens, "statut": statut, "entree": px_in, "sortie": sortie, "t_sortie": t_sortie,
            "pnl_prix": notionnel * rend, "financement": fin_, "cout_sortie_force": cout_sortie_force,
            "valeur_fin": notionnel * (1 + rend) * sens}


# ---------------------------------------------------------------- boucle hebdomadaire

def cout_de_rotation(tenues: dict, cible: dict, p: Params) -> float:
    """Coût sur le seul écart entre la valeur signée tenue et la cible ; un passage long → short paie les deux côtés."""
    return sum(abs(cible.get(s, 0.0) - tenues.get(s, 0.0)) for s in set(tenues) | set(cible)) * (p.frais + p.glissement)


def backtest(jours: dict, heures: dict, financement, lundis, p: Params, notionnel: float = 1.0 / 6):
    """Retourne (semaines, lignes). Notionnel par ligne en part du capital (1/6 = brut 100 %)."""
    jours, heures, financement, _ = couper_zombies(jours, heures, financement)
    tenues: dict[str, float] = {}  # valeur signée détenue à la sortie précédente, lignes non soldées
    semaines, lignes = [], []
    lundis = list(lundis)
    for i, t in enumerate(lundis[:-1]):
        t_in, t_out = t + UNE_HEURE, lundis[i + 1] + UNE_HEURE
        longs, shorts = signal(jours, t, p)
        cible = {s: notionnel for s in longs} | {s: -notionnel for s in shorts}
        # rotation au lundi t_in : coût sur l'écart entre la tenue et la cible
        cout_rotation = cout_de_rotation(tenues, cible, p)
        tenues = {}
        tot = {"pnl_prix": 0.0, "financement": 0.0, "cout": cout_rotation, "long": 0.0, "short": 0.0}
        for s, n in cible.items():
            sens = 1 if n > 0 else -1
            r = jouer_ligne(heures, financement, s, sens, t_in, t_out, notionnel, p)
            r["lundi"] = t
            lignes.append(r)
            if r["statut"] == "absent":
                continue
            tot["pnl_prix"] += r["pnl_prix"]
            tot["financement"] += r["financement"]
            tot["cout"] += r["cout_sortie_force"]
            tot["long" if sens > 0 else "short"] += r["pnl_prix"] + r["financement"]
            if r["statut"] == "semaine":
                tenues[s] = r["valeur_fin"]
        net = tot["pnl_prix"] + tot["financement"] - tot["cout"]
        semaines.append({"lundi": t, "longs": ",".join(longs), "shorts": ",".join(shorts), **tot, "net": net})
    if semaines and tenues:  # solde final des lignes encore tenues, imputé à la dernière semaine
        solde = sum(abs(v) for v in tenues.values()) * (p.frais + p.glissement)
        semaines[-1]["cout"] += solde
        semaines[-1]["net"] -= solde
    return pd.DataFrame(semaines), pd.DataFrame(lignes)


def statistiques(semaines: pd.DataFrame, rend_btc: pd.Series | None = None) -> dict:
    """Sharpe annualisé (52 semaines) et bêta hebdomadaire sur BTC, à brut 100 %."""
    r = semaines["net"].to_numpy(dtype=float)
    out = {"semaines": int(len(r)), "moyenne": float(r.mean()) if len(r) else float("nan")}
    sd = r.std(ddof=1) if len(r) > 1 else float("nan")
    out["sharpe_annualise"] = float(r.mean() / sd * np.sqrt(52)) if sd and np.isfinite(sd) and sd > 0 else float("nan")
    if rend_btc is not None and len(r) > 2:
        x = rend_btc.to_numpy(dtype=float)
        xc = x - x.mean()
        out["beta_btc"] = float((xc * (r - r.mean())).sum() / (xc * xc).sum())
    return out
