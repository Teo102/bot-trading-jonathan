"""Score d'encombrement de STRAT-20261102-05 (fiche § 3), branché sur le moteur de STRAT-20261031-03.

Sans réseau, sans clé, sans ordre. Toutes les lectures se font sur des données strictement antérieures au lundi t.

- F_i : somme des taux de financement des `fenetre_f` jours avant t, divisée par `fenetre_f` (taux journalier
  équivalent, insensible aux intervalles de 8 h, 4 h ou 1 h). Exige au moins un événement chaque jour de la fenêtre.
- O_i : log(intérêt ouvert en USD du jour t − 1 / celui du jour t − 1 − fenetre_o), dernière valeur de chaque jour.
- C_i = poids_f · z(F_i) + poids_o · z(O_i), z transversal borné à ± borne_z. Poids nul : la mesure est ignorée.
- Le moteur met en long le score le plus haut : le score rendu vaut −C (short des plus encombrés), ou +C si `inverse`.
Un nom sans mesure complète sort du classement de la semaine (règle H1 étendue).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

UN_JOUR = pd.Timedelta(days=1)


@dataclass(frozen=True)
class ParamsScore:
    fenetre_f: int = 7
    fenetre_o: int = 7
    poids_f: float = 1.0
    poids_o: float = 1.0
    borne_z: float = 3.0
    inverse: bool = False  # contrôle E19 : long des plus encombrés


def taux_journalier(financement: pd.DataFrame, t: pd.Timestamp, noms, fenetre: int) -> pd.Series:
    debut = t - fenetre * UN_JOUR
    f = financement.loc[(financement.index >= debut) & (financement.index < t)]
    jours_attendus = pd.date_range(debut, t - UN_JOUR, freq="D")
    out = {}
    for s in noms:
        if s not in f.columns:
            continue
        ev = f[s].dropna()
        if set(ev.index.normalize()) >= set(jours_attendus):  # au moins un événement chaque jour
            out[s] = float(ev.sum()) / fenetre
    return pd.Series(out, dtype=float)


def variation_oi(oi_jour: pd.DataFrame, t: pd.Timestamp, noms, fenetre: int) -> pd.Series:
    d1, d0 = (t - UN_JOUR).normalize(), (t - (1 + fenetre) * UN_JOUR).normalize()
    oi = oi_jour.loc[oi_jour.index < t]
    out = {}
    for s in noms:
        if s not in oi.columns:
            continue
        a, b = oi[s].get(d0, np.nan), oi[s].get(d1, np.nan)
        if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
            out[s] = float(np.log(b / a))
    return pd.Series(out, dtype=float)


def z_borne(x: pd.Series, borne: float) -> pd.Series:
    if len(x) < 2 or not np.isfinite(x.std(ddof=0)) or x.std(ddof=0) == 0:
        return pd.Series(0.0, index=x.index)
    return ((x - x.mean()) / x.std(ddof=0)).clip(-borne, borne)


def encombrement(financement, oi_jour, t, noms, ps: ParamsScore) -> pd.Series:
    """C_i sur les noms qui ont toutes les mesures demandées (poids non nuls)."""
    parts = []
    if ps.poids_f:
        parts.append(("f", taux_journalier(financement, t, noms, ps.fenetre_f), ps.poids_f))
    if ps.poids_o:
        parts.append(("o", variation_oi(oi_jour, t, noms, ps.fenetre_o), ps.poids_o))
    if not parts:
        return pd.Series(dtype=float)
    communs = set(noms)
    for _, x, _ in parts:
        communs &= set(x.index)
    communs = sorted(communs)
    c = pd.Series(0.0, index=communs)
    for _, x, w in parts:
        c = c + w * z_borne(x.loc[communs], ps.borne_z)
    return c


def fabrique_scores(financement: pd.DataFrame, oi_jour: pd.DataFrame, ps: ParamsScore):
    """Fonction de score au format attendu par moteur_xsmom.backtest."""
    def f(jours, t, noms, p):
        c = encombrement(financement, oi_jour, t, noms, ps)
        return c if ps.inverse else -c
    return f
