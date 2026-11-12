"""Détection sans anticipation des cascades de liquidations de STRAT-20261109-08 (fiche § 3).

Convention de temps (UTC, sans fuseau) :
- une barre 1 minute d'ouverture `o` couvre [o, o + 1 min) ; son `close` est le prix à l'instant o + 1 min ;
- le prix à l'instant t est donc le `close` de la barre ouverte à t − 1 min ;
- l'intérêt ouvert (metrics, champ `sum_open_interest`, en **contrats**, et non en valeur : la valeur baisse
  mécaniquement avec le prix) est pris à l'heure t fournie par `donnees_1m.lire_metrics_contrats`, c'est-à-dire
  `create_time` + 5 minutes sur tout l'historique (décision du 12/11/2026, fiche § 13). Ce module ne décale rien lui-même.

Une cascade candidate est déclarée en t (pas de 5 minutes) si, sur [t − 15 min, t] :
  rendement ≤ −X  et  variation de l'intérêt ouvert ≤ −Y.
Seules les barres d'ouverture ≤ t − 1 min et l'intérêt ouvert d'horodatage ≤ t sont lus.

Départage (décision du 12/11/2026) : quand plusieurs cascades tombent au même instant, le plus gros volume en USDT sur
les 15 minutes précédentes passe d'abord, puis l'ordre alphabétique du symbole pour les égalités exactes. Les deux sont
connus à t. Toute fonction qui attribue des places passe par `ordonner`, jamais par l'ordre du fichier.
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


def ordonner(c: pd.DataFrame) -> pd.DataFrame:
    """Ordre de traitement unique : heure, puis volume 15 min décroissant, puis symbole. Tri stable, donc le résultat
    ne dépend pas de l'ordre des lignes en entrée."""
    c = c.copy()
    if "volume_15m" not in c.columns:
        c["volume_15m"] = 0.0
    if "symbole" not in c.columns:
        c["symbole"] = "_"
    return c.sort_values(["t", "volume_15m", "symbole"], ascending=[True, False, True], kind="mergesort")


def attribuer(ev: pd.DataFrame, k: int, tenue: pd.Timedelta) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attribution des k emplacements si chaque position durait `tenue` (aucune issue lue). Retourne (prises, ignorées).
    Les cascades simultanées sont départagées par `ordonner`."""
    o = ordonner(ev)
    fins, prises, ignorees = [], [], []
    for i, t in zip(o.index, o["t"]):
        fins = [f for f in fins if f > t]
        if len(fins) >= k:
            ignorees.append(i)
        else:
            fins.append(t + tenue); prises.append(i)
    return o.loc[prises], o.loc[ignorees]


def dedoublonner(c: pd.DataFrame, refractaire: pd.Timedelta) -> pd.DataFrame:
    """Un événement par symbole puis rien pendant `refractaire`, compté depuis l'événement (aucune issue lue).
    La fiche compte la pause depuis la sortie : `refractaire` = H donne donc une borne haute du nombre d'événements,
    `refractaire` = 2 H (tenue complète puis pause) une borne basse."""
    garde, dernier = [], {}
    for r in ordonner(c)[list(c.columns)].itertuples(index=False):
        s = getattr(r, "symbole", "_")
        if s in dernier and r.t < dernier[s] + refractaire:
            continue
        garde.append(r); dernier[s] = r.t
    return pd.DataFrame(garde, columns=c.columns)


def fenetres_a_garder(instants, avant=pd.Timedelta(minutes=20), apres=pd.Timedelta(hours=12, minutes=20),
                      decalage_placebo=pd.Timedelta(hours=24)) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Union des intervalles de minutes à conserver : autour de chaque candidat et autour de son placebo (+24 h).
    `apres` couvre la tenue la plus longue de la grille (12 h), le retard maximal (10 min, essai E11) et 10 min de marge."""
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
