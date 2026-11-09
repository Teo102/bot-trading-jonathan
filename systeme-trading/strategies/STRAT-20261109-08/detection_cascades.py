"""Détection sans anticipation des cascades de liquidations de STRAT-20261109-08 (fiche § 3).

Convention de temps (UTC, sans fuseau) :
- une barre 1 minute d'ouverture `o` couvre [o, o + 1 min) ; son `close` est le prix à l'instant o + 1 min ;
- le prix à l'instant t est donc le `close` de la barre ouverte à t − 1 min ;
- l'intérêt ouvert (metrics, champ `sum_open_interest`, en **contrats**, et non en valeur : la valeur baisse
  mécaniquement avec le prix) est pris à l'horodatage t. La sémantique de cet horodatage reste à vérifier (fiche § 2).

Une cascade candidate est déclarée en t (pas de 5 minutes) si, sur [t − 15 min, t] :
  rendement ≤ −X  et  variation de l'intérêt ouvert ≤ −Y.
Seules les barres d'ouverture ≤ t − 1 min et l'intérêt ouvert d'horodatage ≤ t sont lus.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UNE_MIN = pd.Timedelta(minutes=1)
FENETRE = pd.Timedelta(minutes=15)


def prix_a(k1: pd.DataFrame, instants: pd.DatetimeIndex) -> pd.Series:
    """Prix à chaque instant t = close de la barre ouverte à t − 1 min (NaN si absente)."""
    return pd.Series(k1["close"].reindex(instants - UNE_MIN).to_numpy(), index=instants)


def candidats(k1: pd.DataFrame, oi: pd.Series, x_min: float = 0.03, y_min: float = 0.02,
              fenetre: pd.Timedelta = FENETRE) -> pd.DataFrame:
    """Toutes les cascades candidates au seuil le plus lâche de la grille (X 3 %, Y 2 % par défaut).
    Retourne t, rendement 15 min, variation d'intérêt ouvert 15 min, volume 15 min (USDT)."""
    oi = oi[~oi.index.duplicated(keep="last")].sort_index()
    t = oi.index[(oi.index >= k1.index.min() + fenetre + UNE_MIN) & (oi.index <= k1.index.max() + UNE_MIN)]
    if not len(t):
        return pd.DataFrame(columns=["t", "rendement_15m", "var_oi_15m", "volume_15m"])
    p_t, p_0 = prix_a(k1, t), prix_a(k1, t - fenetre)
    oi_t = oi.reindex(t)
    oi_0 = oi.reindex(t - fenetre)
    r = p_t.to_numpy() / p_0.to_numpy() - 1
    d = oi_t.to_numpy() / oi_0.to_numpy() - 1
    vol = k1["volume_usdt"].rolling("15min").sum().reindex(t - UNE_MIN).to_numpy()  # barres ouvertes dans [t-15, t)
    ok = np.isfinite(r) & np.isfinite(d) & (r <= -x_min) & (d <= -y_min)
    return pd.DataFrame({"t": t[ok], "rendement_15m": r[ok], "var_oi_15m": d[ok], "volume_15m": vol[ok]}).reset_index(drop=True)


def filtrer(c: pd.DataFrame, x: float, y: float) -> pd.DataFrame:
    return c[(c["rendement_15m"] <= -x) & (c["var_oi_15m"] <= -y)]


def dedoublonner(c: pd.DataFrame, refractaire: pd.Timedelta) -> pd.DataFrame:
    """Un événement par symbole puis rien pendant `refractaire` (durée de tenue maximale, sans lire l'issue)."""
    garde, dernier = [], {}
    for r in c.sort_values("t").itertuples(index=False):
        s = getattr(r, "symbole", "_")
        if s in dernier and r.t < dernier[s] + refractaire:
            continue
        garde.append(r); dernier[s] = r.t
    return pd.DataFrame(garde, columns=c.columns)


def fenetres_a_garder(instants, avant=pd.Timedelta(minutes=20), apres=pd.Timedelta(hours=12, minutes=10),
                      decalage_placebo=pd.Timedelta(hours=24)) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Union des intervalles de minutes à conserver : autour de chaque candidat et autour de son placebo (+24 h).
    `apres` couvre la tenue la plus longue de la grille (12 h) et le retard maximal (5 min)."""
    iv = []
    for t in instants:
        for base in (t, t + decalage_placebo):
            iv.append((base - avant, base + apres))
    iv.sort()
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out
