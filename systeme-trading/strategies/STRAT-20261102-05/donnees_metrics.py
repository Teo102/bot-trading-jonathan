"""Intérêt ouvert depuis les archives journalières `metrics` de data.binance.vision (STRAT-20261102-05, fiche § 8).

Même source et mêmes garanties que `../STRAT-20261031-03/donnees_binance.py` : sommes SHA-256, cache local, verrou de
bloc (aucune ligne d'heure ≥ fin n'est gardée). Seuls les jours nécessaires au score sont lus : t − 1 et
t − 1 − fenêtre pour chaque lundi et chaque nom de l'univers. Valeur retenue : la dernière ligne du jour du champ
`sum_open_interest_value` (USD).
"""
from __future__ import annotations

import io
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "STRAT-20261031-03"))
import donnees_binance as db  # noqa: E402

CHEMIN = "metrics/{s}/{s}-metrics-{d}.zip"


def lire_metrics(z: bytes) -> pd.Series:
    with zipfile.ZipFile(io.BytesIO(z)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f)
    if "create_time" not in df.columns or "sum_open_interest_value" not in df.columns:
        raise ValueError("colonnes metrics inattendues : " + ",".join(df.columns))
    ts = pd.to_datetime(df["create_time"])
    return pd.Series(pd.to_numeric(df["sum_open_interest_value"], errors="coerce").values, index=ts.values).sort_index()


def jours_requis(univers_par_lundi: dict, fenetres=(7,)) -> dict:
    """{symbole: {dates}} des jours à lire. Les clés de `univers_par_lundi` sont les lundis."""
    req: dict = {}
    for t, noms in univers_par_lundi.items():
        for s in noms:
            for w in set(fenetres):
                for k in (1, 1 + w):
                    req.setdefault(s, set()).add((t - pd.Timedelta(days=k)).normalize())
    return req


def charger_oi(source, requis: dict, fin, fils=8, journal: dict | None = None) -> pd.DataFrame:
    fin = db.naif(fin)
    taches = [(s, d) for s, ds in requis.items() for d in sorted(ds) if d < fin]

    def un(sd):
        s, d = sd
        z = source.lire(f"{db.RACINE_J}/" + CHEMIN.format(s=s, d=d.date().isoformat()))
        if z is None:
            return s, d, None
        x = lire_metrics(z)
        x = x[x.index < fin].dropna()  # verrou de bloc
        return s, d, (float(x.iloc[-1]) if len(x) else None)

    with ThreadPoolExecutor(fils) as ex:
        res = list(ex.map(un, taches))
    lignes = [(s, d, v) for s, d, v in res if v is not None]
    if journal is not None:
        journal["oi_jours_demandes"] = len(taches)
        journal["oi_jours_introuvables"] = sum(1 for _, _, v in res if v is None)
    if not lignes:
        return pd.DataFrame()
    return pd.DataFrame(lignes, columns=["s", "d", "v"]).pivot(index="d", columns="s", values="v").sort_index()
