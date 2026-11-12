"""Moteur intra-journalier de STRAT-20261109-08 (fiche § 3, § 13 ; audit m2, m4). Sans réseau, sans clé, sans ordre.

Principe : chaque position est indépendante des autres une fois ouverte. Le moteur parcourt les cascades dans l'ordre
unique de `detection_cascades.ordonner` (heure, volume 15 min décroissant, symbole) ; pour chacune, il vérifie les
contraintes **avec la seule information connue à l'heure d'entrée**, puis simule la position minute par minute.

Règle m4 (ordre dans une même minute) :
- la minute d'entrée compte pour le stop : entrée à l'ouverture, puis le plus bas de la même minute est lu ;
- une sortie à l'ouverture d'une minute précède le plus bas de cette minute (qui n'est donc pas lu).

Règle m2 (verrou) : le magasin de minutes refuse toute lecture au-delà de sa borne ; une position n'est ouverte que si
sa sortie au plus tard (entrée + H) tombe avant la fin du bloc.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

import detection_cascades as dc

UNE_MIN = pd.Timedelta(minutes=1)


class Verrou(RuntimeError):
    pass


@dataclass(frozen=True)
class ParamsIntraday:
    x: float = 0.04                       # chute minimale sur 15 min
    y: float = 0.03                       # baisse minimale de l'intérêt ouvert (contrats) sur 15 min
    s: float = 0.05                       # stop sous le prix d'entrée
    h: pd.Timedelta = pd.Timedelta(hours=4)   # tenue maximale ; aussi pause après la sortie
    d: pd.Timedelta = pd.Timedelta(minutes=5)  # retard d'entrée (décision 4 du 12/11)
    k: int = 5                            # positions simultanées
    stops_par_jour: int = 2               # après ce nombre de stops dans le jour UTC, plus d'entrée
    frais: float = 0.0005                 # par côté
    gliss_entree: float = 0.0010
    gliss_sortie: float = 0.0005
    gliss_stop: float = 0.0030
    placebo: pd.Timedelta = pd.Timedelta(0)   # E14 : entrée décalée de 24 h
    sens: int = 1                         # +1 long (base) ; -1 réservé à E13 (non calculable, m1)


class MagasinCompact:
    """Minutes du format compact (un npz par symbole et par mois), avec une borne de lecture stricte."""

    def __init__(self, dossier: Path, borne: pd.Timestamp):
        self.dossier, self.borne, self._cache = Path(dossier), pd.Timestamp(borne), {}

    def _symbole(self, s: str) -> pd.DataFrame:
        if s not in self._cache:
            morceaux = []
            for f in sorted((self.dossier / s).glob("*.npz")):
                d = dict(np.load(f))
                idx = pd.Timestamp(0) + pd.to_timedelta(d["minute"], unit="min")
                morceaux.append(pd.DataFrame({c: d[c].astype(float) for c in ("open", "high", "low", "close")}, index=idx))
            x = pd.concat(morceaux) if morceaux else pd.DataFrame(columns=["open", "high", "low", "close"])
            x = x[~x.index.duplicated(keep="first")].sort_index()
            self._cache = {s: x[x.index < self.borne]}  # un symbole en mémoire à la fois
        return self._cache[s]

    def minutes(self, s: str, a: pd.Timestamp, b: pd.Timestamp) -> pd.DataFrame:
        if b >= self.borne:
            raise Verrou(f"Lecture de {s} jusqu'à {b} refusée : borne {self.borne}.")
        x = self._symbole(s)
        return x[(x.index >= a) & (x.index <= b)]


def jouer_position(m: pd.DataFrame, te: pd.Timestamp, p: ParamsIntraday) -> dict:
    """Une position de te (ouverture) à te + H (ouverture) au plus tard. `m` : minutes de te à te + H incluses."""
    if te not in m.index or not np.isfinite(m.at[te, "open"]):
        return {"statut": "absent"}
    sens = p.sens
    entree = m.at[te, "open"] * (1 + sens * p.gliss_entree)
    niveau = entree * (1 - sens * p.s)
    fin = te + p.h
    for t, r in m[(m.index >= te) & (m.index < fin)].iterrows():
        if t > te and np.isfinite(r["open"]) and (r["open"] <= niveau if sens > 0 else r["open"] >= niveau):
            brut = r["open"]  # saut à l'ouverture sous le niveau
            return {"statut": "stop", "t_sortie": t, "entree": entree, "sortie": brut * (1 - sens * p.gliss_stop)}
        touche = (r["low"] <= niveau) if sens > 0 else (r["high"] >= niveau)
        if np.isfinite(r["low"]) and touche:
            brut = min(niveau, r["open"]) if sens > 0 else max(niveau, r["open"])
            return {"statut": "stop", "t_sortie": t, "entree": entree, "sortie": brut * (1 - sens * p.gliss_stop)}
    suite = m[(m.index >= fin) & (m.index <= fin + pd.Timedelta(minutes=10))]["open"].dropna()
    if len(suite):
        t_s, brut = suite.index[0], suite.iloc[0]
    else:
        av = m[m.index < fin]["close"].dropna()
        if not len(av):
            return {"statut": "absent"}
        t_s, brut = fin, av.iloc[-1]
    return {"statut": "temps", "t_sortie": t_s, "entree": entree, "sortie": brut * (1 - sens * p.gliss_sortie)}


def financement_paye(fin: pd.Series | None, te: pd.Timestamp, ts: pd.Timestamp, sens: int, notionnel: float) -> float:
    """Long : paie un taux positif. Versements d'heure dans (te, ts]."""
    if fin is None or not len(fin):
        return 0.0
    v = fin[(fin.index > te) & (fin.index <= ts)].dropna()
    return float(sens * v.sum() * notionnel)


def simuler(ev: pd.DataFrame, magasin: MagasinCompact, p: ParamsIntraday, fin_bloc: pd.Timestamp,
            financement: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Retourne (positions, compteurs d'événements écartés). `ev` : symbole, t, rendement_15m, var_oi_15m, volume_15m."""
    financement = financement or {}
    ev = dc.filtrer(ev, p.x, p.y)
    n = 1.0 / p.k
    ouvertes: list[tuple[pd.Timestamp, str]] = []   # (sortie, symbole)
    derniere_sortie: dict[str, pd.Timestamp] = {}
    stops: list[pd.Timestamp] = []
    lignes, ecarts = [], {"emplacement": 0, "symbole_ouvert": 0, "pause": 0, "stops_du_jour": 0, "fin_de_bloc": 0, "absent": 0}
    for r in dc.ordonner(ev).itertuples(index=False):
        te = r.t + p.placebo + p.d
        if te + p.h + pd.Timedelta(minutes=10) >= fin_bloc:
            ecarts["fin_de_bloc"] += 1; continue
        ouvertes = [(f, s) for f, s in ouvertes if f > te]
        if any(s == r.symbole for _, s in ouvertes):
            ecarts["symbole_ouvert"] += 1; continue
        if r.symbole in derniere_sortie and te < derniere_sortie[r.symbole] + p.h:
            ecarts["pause"] += 1; continue
        jour = te.normalize()
        if sum(1 for x in stops if jour <= x <= te) >= p.stops_par_jour:
            ecarts["stops_du_jour"] += 1; continue
        if len(ouvertes) >= p.k:
            ecarts["emplacement"] += 1; continue
        m = magasin.minutes(r.symbole, te, te + p.h + pd.Timedelta(minutes=10))
        pos = jouer_position(m, te, p)
        if pos["statut"] == "absent":
            ecarts["absent"] += 1; continue
        ts = pos["t_sortie"]
        rend = p.sens * (pos["sortie"] / pos["entree"] - 1)
        frais = 2 * p.frais * n
        fi = financement_paye(financement.get(r.symbole), te, ts, p.sens, n)
        lignes.append({"symbole": r.symbole, "t": r.t, "t_entree": te, "t_sortie": ts, "statut": pos["statut"],
                       "entree": pos["entree"], "sortie": pos["sortie"], "rendement": rend, "pnl_prix": rend * n,
                       "frais": frais, "financement": fi, "net": rend * n - frais - fi, "volume_15m": r.volume_15m})
        ouvertes.append((ts, r.symbole)); derniere_sortie[r.symbole] = ts
        if pos["statut"] == "stop":
            stops.append(ts)
    return pd.DataFrame(lignes), ecarts


def semaines(pos: pd.DataFrame, debut: pd.Timestamp, fin: pd.Timestamp) -> pd.Series:
    """Rendement net par semaine (lundi), daté à la sortie ; les semaines sans position valent 0 (m5 : fréquence hebdomadaire)."""
    lun = pd.date_range(pd.Timestamp(debut) - pd.Timedelta(days=pd.Timestamp(debut).dayofweek), fin, freq="W-MON")
    if pos.empty:
        return pd.Series(0.0, index=lun)
    w = pos.assign(lundi=pd.to_datetime(pos["t_sortie"]).dt.normalize() - pd.to_timedelta(pd.to_datetime(pos["t_sortie"]).dt.dayofweek, unit="D"))
    return w.groupby("lundi")["net"].sum().reindex(lun, fill_value=0.0)
