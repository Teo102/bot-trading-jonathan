"""Univers et cible de STRAT-20261102-06 (fiche § 3) : jeunes cotations vendues à découvert, couverture BTC.

Sans réseau, sans clé, sans ordre. Tout se lit sur les jours strictement antérieurs au lundi t.

- Date de cotation L = premier jour de volume non nul. Un symbole déjà actif dans les `marge_debut_j` premiers jours
  des données chargées est réputé ancien : sa vraie date de cotation est inconnue, il ne peut pas être « nouveau ».
- Âge t − L entre age_min et age_max jours ; vivant (volume non nul en t − 1) ; médiane du volume journalier sur
  les jours max(L, t − 30) à t − 1 au moins égale à liquidite_min ; au plus noms_max noms, les plus traités.
- Faux nouveaux noms exclus : liste close (renommages, migrations) et contrats multiplicateurs « 1000X »
  dont l'actif de base X avait déjà un perpétuel coté avant L.
- Cible : −1 par nom retenu, BTC à +multiple × nombre de noms (neutralité en dollars si multiple = 1).
  Contrôle inversé : signes opposés. Semaine sans nom : aucune position.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "STRAT-20261031-03"))
import moteur_xsmom as m  # noqa: E402

UN_JOUR = pd.Timedelta(days=1)


@dataclass(frozen=True)
class ParamsCotation:
    age_min_j: int = 7
    age_max_j: int = 60
    liquidite_min: float = 20e6
    fenetre_liquidite_max_j: int = 30
    noms_max: int = 6
    multiple_couverture: float = 1.0
    couverture: bool = True
    inverse: bool = False
    marge_debut_j: int = 2
    facteur: str = "BTC"
    exclus: frozenset = field(default_factory=frozenset)          # stablecoins, indices, et memecoins si E15
    faux_nouveaux: frozenset = field(default_factory=frozenset)  # symboles complets, liste close


def premiers_volumes(vol: pd.DataFrame) -> dict:
    """{symbole: premier jour de volume non nul}. Sans anticipation : seul un premier volume antérieur à t sert en t."""
    a = vol.fillna(0) > 0
    out = {}
    for s in vol.columns:
        idx = a.index[a[s].to_numpy()]
        if len(idx):
            out[s] = idx[0]
    return out


def eligibles(jours: dict, t: pd.Timestamp, pc: ParamsCotation, debut_donnees: pd.Timestamp,
              premiers: dict | None = None) -> list[tuple[str, float]]:
    vol = jours["volume"]
    if premiers is None:
        premiers = premiers_volumes(vol.loc[vol.index < t])
    premiers = {s: d for s, d in premiers.items() if d < t}
    seuil_ancien = debut_donnees + pc.marge_debut_j * UN_JOUR
    veille = t - UN_JOUR
    out = []
    for s, L in premiers.items():
        if L <= seuil_ancien or s == pc.facteur or s in pc.faux_nouveaux or m.est_exclu(s, pc.exclus):
            continue
        age = (t - L).days
        if not (pc.age_min_j <= age <= pc.age_max_j):
            continue
        v = vol[s]
        if not (v.get(veille, 0) or 0) > 0:
            continue
        base = m.nom_de_base(s) + "USDT"
        if base != s and base in premiers and premiers[base] < L:  # 1000X coté après X : même actif
            continue
        debut_f = max(L, t - pc.fenetre_liquidite_max_j * UN_JOUR)
        med = v.reindex(pd.date_range(debut_f, veille, freq="D")).fillna(0).median()
        if med >= pc.liquidite_min:
            out.append((s, float(med)))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out[: pc.noms_max]


def fabrique_cible(pc: ParamsCotation, debut_donnees: pd.Timestamp):
    """Fonction de cible au format de moteur_xsmom.backtest(fonction_cible=...)."""
    cache = {}

    def f(jours, t, p):
        cle = id(jours["volume"])
        if cle not in cache:
            cache.clear()
            cache[cle] = premiers_volumes(jours["volume"])
        noms = [s for s, _ in eligibles(jours, t, pc, debut_donnees, cache[cle])]
        signe = 1 if pc.inverse else -1
        poids = {s: float(signe) for s in noms}
        if noms and pc.couverture:
            poids[pc.facteur] = -signe * pc.multiple_couverture * len(noms)
        return poids, len(noms)
    return f


def candidats_renommage(vol: pd.DataFrame, debut_donnees: pd.Timestamp, ecart_j: int = 5) -> pd.DataFrame:
    """Paires (ancien, nouveau) où l'ancien s'arrête à ± ecart_j jours de la cotation du nouveau.
    À relire à la main avant le gel : la liste close se fixe sur cette base (fiche § 3.2). Volumes seuls."""
    a = vol.fillna(0) > 0
    prem = premiers_volumes(vol)
    fins = {s: a.index[a[s].to_numpy()][-1] for s in prem}
    lignes = []
    for nouveau, L in prem.items():
        if L <= debut_donnees + 2 * UN_JOUR:
            continue
        for ancien, fin in fins.items():
            if ancien != nouveau and abs((fin - L).days) <= ecart_j and fin < vol.index[-1] - 10 * UN_JOUR:
                lignes.append({"nouveau": nouveau, "cotation": L.date(), "ancien": ancien,
                               "dernier_volume_ancien": fin.date(), "ecart_j": (fin - L).days})
    return pd.DataFrame(lignes)
