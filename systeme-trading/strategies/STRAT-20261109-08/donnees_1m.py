"""Données 1 minute et intérêt ouvert 5 minutes de STRAT-20261109-08, en flux (fiche § 9, option (c) + (b)).

- Seuls les mois où le symbole est éligible au moins un jour (âge ≥ 30 j, médiane 30 j du volume ≥ 20 M USDT, lue
  sur la veille) sont téléchargés (option c).
- Chaque archive est vérifiée (SHA-256), lue, puis **effacée du cache** si elle n'y était pas avant (option b).
- Format compact conservé : candidats au seuil le plus lâche, et minutes autour d'eux et de leur placebo.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
import donnees_binance as db  # noqa: E402

RACINE_M = "data/futures/um/monthly"
RACINE_J = "data/futures/um/daily"


class LectureEphemere:
    """Enveloppe d'une source : efface du cache local toute archive (et sa somme) téléchargée par cet appel."""

    def __init__(self, source):
        self.source = source
        self.cache = getattr(source, "cache", None)

    def lire(self, cle: str):
        local = (self.cache / cle) if self.cache is not None else None
        deja = bool(local is not None and local.exists())
        z = self.source.lire(cle)
        if local is not None and not deja:
            for f in (local, local.with_name(local.name + ".CHECKSUM")):
                try:
                    f.unlink()
                except FileNotFoundError:
                    pass
        return z


# Décision de Jonathan et Téo du 12/11/2026 (fiche § 13, constat B1 de revues/AUDIT_STRAT-08_FABLE.md) :
# l'archive date ses lignes 5 minutes trop tôt depuis mars 2024 (archive(t) = API(t + 5 min), 13 824 lignes sur 13 824).
# Le décalage s'applique à TOUT l'historique : avant mars 2024 l'information arrive 5 minutes plus tard qu'en réalité
# (prudent), après elle est à l'heure. Aucune avance possible, et aucune dépendance à la date de bascule.
DECALAGE_METRICS = pd.Timedelta(minutes=5)


def lire_metrics_contrats(z: bytes) -> pd.Series:
    """Intérêt ouvert en contrats (`sum_open_interest`), indexé à `create_time` + 5 minutes (heure d'observation retenue).
    Les valeurs nulles, négatives ou vides sont rejetées : une ligne à zéro est un incident de la source, pas une
    liquidation (constat M2 de l'audit, 12/08/2024)."""
    with zipfile.ZipFile(io.BytesIO(z)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f)
    if "create_time" not in df.columns or "sum_open_interest" not in df.columns:
        raise ValueError("colonnes metrics inattendues : " + ",".join(df.columns))
    s = pd.Series(pd.to_numeric(df["sum_open_interest"], errors="coerce").values, index=pd.to_datetime(df["create_time"]).values)
    s.index = pd.DatetimeIndex(s.index).round("min") + DECALAGE_METRICS
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s[s > 0]


def mois_eligibles(volume_jour: pd.DataFrame, liquidite_min: float = 20e6, age_min_j: int = 30,
                   exclus: set | None = None, debut=None, fin=None) -> dict:
    """{symbole: [mois 'AAAA-MM']} où le symbole est éligible au moins un jour. Lecture sur la veille seulement."""
    exclus = exclus or set()
    v = volume_jour.fillna(0)
    actif = v > 0
    prem = {s: actif.index[actif[s].to_numpy()][0] for s in v.columns if actif[s].any()}
    med = v.rolling(30, min_periods=20).median().shift(1)
    out = {}
    for s in v.columns:
        if s in exclus or s not in prem:
            continue
        el = (med[s] >= liquidite_min) & ((v.index - prem[s]).days >= age_min_j + 1)
        if debut is not None:
            el &= v.index >= pd.Timestamp(debut)
        if fin is not None:
            el &= v.index < pd.Timestamp(fin)
        jours = v.index[el.to_numpy()]
        if len(jours):
            out[s] = sorted({d.strftime("%Y-%m") for d in jours})
    return out


def jours_eligibles(volume_jour: pd.DataFrame, s: str, liquidite_min: float = 20e6, age_min_j: int = 30) -> pd.Series:
    v = volume_jour[s].fillna(0)
    prem = v.index[(v > 0).to_numpy()][0]
    med = volume_jour.fillna(0)[s].rolling(30, min_periods=20).median().shift(1)
    return (med >= liquidite_min) & ((v.index - prem).days >= age_min_j + 1)


def charger_1m(source, s: str, mois: str, fin) -> tuple[pd.DataFrame | None, int]:
    """Klines 1 minute d'un mois ; archive mensuelle, sinon journalières. Retourne (données, jours introuvables)."""
    z = source.lire(f"{RACINE_M}/klines/{s}/1m/{s}-1m-{mois}.zip")
    if z is not None:
        x = db.lire_klines(z)
        return x[x.index < db.naif(fin)], 0
    morceaux, manquants = [], 0
    for d in pd.date_range(f"{mois}-01", pd.Period(mois).end_time.normalize(), freq="D"):
        if d >= db.naif(fin):
            break
        zj = source.lire(f"{RACINE_J}/klines/{s}/1m/{s}-1m-{d.date().isoformat()}.zip")
        if zj is None:
            manquants += 1
            continue
        morceaux.append(db.lire_klines(zj))
    if not morceaux:
        return None, manquants
    x = pd.concat(morceaux)
    x = x[~x.index.duplicated(keep="first")].sort_index()
    return x[x.index < db.naif(fin)], manquants


def charger_oi(source, s: str, mois: str, fin) -> tuple[pd.Series | None, int]:
    morceaux, manquants = [], 0
    for d in pd.date_range(f"{mois}-01", pd.Period(mois).end_time.normalize(), freq="D"):
        if d >= db.naif(fin):
            break
        z = source.lire(f"{RACINE_J}/metrics/{s}/{s}-metrics-{d.date().isoformat()}.zip")
        if z is None:
            manquants += 1
            continue
        morceaux.append(lire_metrics_contrats(z))
    if not morceaux:
        return None, manquants
    x = pd.concat(morceaux)
    x = x[~x.index.duplicated(keep="last")].sort_index()
    return x[x.index <= db.naif(fin)], manquants


def compacter(k1: pd.DataFrame, intervalles) -> dict:
    """Minutes conservées (float32) : ouverture, haut, bas, clôture, volume, indexées en minutes depuis l'époque."""
    if not intervalles:
        return {}
    masque = np.zeros(len(k1), dtype=bool)
    idx = k1.index
    for a, b in intervalles:
        masque |= (idx >= a) & (idx <= b)
    x = k1[masque]
    minutes = ((x.index - pd.Timestamp(0)) // pd.Timedelta(minutes=1)).astype("int64")
    return {"minute": np.asarray(minutes), **{c: x[c].to_numpy(np.float32) for c in ("open", "high", "low", "close", "volume_usdt")}}


def relire_compact(d: dict) -> pd.DataFrame:
    idx = pd.Timestamp(0) + pd.to_timedelta(d["minute"], unit="min")
    return pd.DataFrame({c: d[c].astype(float) for c in ("open", "high", "low", "close", "volume_usdt")}, index=idx)
