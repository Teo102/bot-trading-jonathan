#!/usr/bin/env python3
"""Chargement des archives publiques data.binance.vision pour STRAT-20261031-03 (fiche § 2 et § 4).

Sans clé, sans ordre. Lit les archives mensuelles des perpétuels USDT-M :
- klines 1 d (clôture et volume en USDT, colonnes 4 et 7) pour tous les symboles, afin de classer l'univers ;
- klines 1 h, prix de marque 1 h et financement, pour les seuls symboles entrés dans l'univers et BTC.

**Verrou de bloc.** Chaque appel reçoit une heure de fin (`fin`). Aucun mois postérieur n'est téléchargé et toute
ligne d'heure ≥ `fin` est jetée à la lecture, avant tout calcul. Le cache local garde les zip bruts, vérifiés par
leur fichier `.CHECKSUM` (SHA-256) ; un zip sans somme valide est refusé.

Source : `VisionHTTP` (réseau) ou `VisionLocale` (dossier qui reproduit l'arborescence, pour les tests).
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

VISION = "https://data.binance.vision"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
RACINE = "data/futures/um/monthly"
RACINE_J = "data/futures/um/daily"  # archives journalières, pour combler les trous des mensuelles


class ErreurSomme(RuntimeError):
    pass


# ---------------------------------------------------------------- sources

class VisionHTTP:
    def __init__(self, cache: Path, essais: int = 6):
        import requests
        self.s = requests.Session()
        self.cache = Path(cache)
        self.essais = essais
        self.incidents: list[str] = []
        self.appels = 0

    def _get(self, url, params=None, timeout=120):
        for i in range(self.essais):
            self.appels += 1
            try:
                r = self.s.get(url, params=params, timeout=timeout)
            except Exception as e:  # noqa: BLE001
                self.incidents.append(f"{url} {type(e).__name__}")
                time.sleep(2 * (i + 1))
                continue
            if r.status_code in (418, 429) or r.status_code >= 500:
                self.incidents.append(f"{url} HTTP {r.status_code}")
                time.sleep(5 * (i + 1))
                continue
            return r
        raise RuntimeError(f"Échec après {self.essais} essais : {url}")

    def lister(self, prefixe: str) -> list[str]:
        """Sous-dossiers d'un préfixe (pagination S3)."""
        out, marqueur = [], ""
        while True:
            r = self._get(S3, {"delimiter": "/", "prefix": prefixe, "marker": marqueur})
            r.raise_for_status()
            out += re.findall(r"<Prefix>" + re.escape(prefixe) + r"([^/<]+)/</Prefix>", r.text)
            suite = re.search(r"<NextMarker>([^<]+)</NextMarker>", r.text)
            if "<IsTruncated>true" not in r.text or not suite:
                return out
            marqueur = suite.group(1)

    def lire(self, cle: str) -> bytes | None:
        """Zip vérifié, depuis le cache ou le réseau. None si l'archive n'existe pas (404)."""
        local = self.cache / cle
        somme_locale = local.with_name(local.name + ".CHECKSUM")
        if local.exists() and somme_locale.exists():
            donnees = local.read_bytes()
            verifier(donnees, somme_locale.read_text(), cle)
            return donnees
        r = self._get(f"{VISION}/{cle}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        rs = self._get(f"{VISION}/{cle}.CHECKSUM")
        rs.raise_for_status()
        verifier(r.content, rs.text, cle)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(r.content)
        somme_locale.write_text(rs.text)
        return r.content


class VisionLocale:
    """Même interface, sur un dossier local qui reproduit l'arborescence de data.binance.vision."""

    def __init__(self, racine: Path):
        self.racine = Path(racine)
        self.incidents: list[str] = []
        self.appels = 0

    def lister(self, prefixe: str) -> list[str]:
        d = self.racine / prefixe
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []

    def lire(self, cle: str) -> bytes | None:
        self.appels += 1
        p = self.racine / cle
        if not p.exists():
            return None
        donnees = p.read_bytes()
        verifier(donnees, (self.racine / (cle + ".CHECKSUM")).read_text(), cle)
        return donnees


def verifier(donnees: bytes, texte_somme: str, cle: str) -> None:
    attendu = texte_somme.strip().split()[0].lower()
    if hashlib.sha256(donnees).hexdigest() != attendu:
        raise ErreurSomme(f"Somme SHA-256 invalide : {cle}")


# ---------------------------------------------------------------- lecture

def naif(ts) -> pd.Timestamp:
    """Heure UTC sans fuseau, convention de tout le moteur."""
    ts = pd.Timestamp(ts)
    return ts.tz_convert("UTC").tz_localize(None) if ts.tzinfo is not None else ts


def mois(debut: pd.Timestamp, fin: pd.Timestamp) -> list[str]:
    """Mois de debut à celui de fin inclus (fin exclusive à la seconde près, donc le mois de fin est lu puis tronqué)."""
    m = pd.period_range(naif(debut).to_period("M"), (naif(fin) - pd.Timedelta(seconds=1)).to_period("M"), freq="M")
    return [str(x) for x in m]


def _ms_vers_ts(s: pd.Series) -> pd.DatetimeIndex:
    v = s.astype("int64")
    unite = "us" if v.max() > 10**14 else "ms"  # certaines archives récentes passent en microsecondes
    return pd.to_datetime(v, unit=unite)


def lire_klines(z: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(z)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f, header=None, dtype=str)
    df = df[df[0].str.fullmatch(r"\d+", na=False)]  # retire l'en-tête éventuel
    out = pd.DataFrame({"open": df[1].astype(float).values, "high": df[2].astype(float).values,
                        "low": df[3].astype(float).values, "close": df[4].astype(float).values,
                        "volume_usdt": df[7].astype(float).values}, index=_ms_vers_ts(df[0]).values)
    out.index.name = "open_time"
    return out


def lire_financement(z: bytes) -> pd.Series:
    with zipfile.ZipFile(io.BytesIO(z)) as zf, zf.open(zf.namelist()[0]) as f:
        df = pd.read_csv(f, header=None, dtype=str)
    df = df[df[0].str.fullmatch(r"\d+", na=False)]
    taux = df[2] if df.shape[1] >= 3 else df[1]  # calc_time, funding_interval_hours, last_funding_rate
    idx = _ms_vers_ts(df[0]).values
    s = pd.Series(taux.astype(float).values, index=idx)
    # l'heure de calcul tombe parfois quelques ms après l'heure ronde : arrondi à la minute
    s.index = pd.DatetimeIndex(s.index).round("min")
    return s


def _serie(source, cles: list[str], lecteur, fin: pd.Timestamp):
    morceaux = []
    for cle in cles:
        z = source.lire(cle)
        if z is None:
            continue
        x = lecteur(z)
        morceaux.append(x[x.index < naif(fin)])  # verrou de bloc
    if not morceaux:
        return None
    x = pd.concat(morceaux)
    return x[~x.index.duplicated(keep="last")].sort_index()


CHEMINS_J = {"1d": "klines/{s}/1d/{s}-1d-{d}.zip", "1h": "klines/{s}/1h/{s}-1h-{d}.zip",
             "marque": "markPriceKlines/{s}/1h/{s}-1h-{d}.zip"}


def combler(source, sym: str, nature: str, x, debut, fin, journal: dict | None = None):
    """Comble les trous d'une série mensuelle par les archives journalières (ex. 26-27/02/2022, diagnostic du
    01/11/2026). Seuls les jours compris entre la première et la dernière ligne observée sont cherchés : un actif
    arrêté n'est pas prolongé. Les jours introuvables restent absents et sont comptés."""
    if x is None or not len(x):
        return x
    pas = "D" if nature == "1d" else "h"
    attendu = pd.date_range(max(x.index.min(), naif(debut)), x.index.max(), freq=pas)
    manquants = attendu.difference(x.index)
    if not len(manquants):
        return x
    jours = sorted({d.normalize() for d in manquants})
    ajouts, trouves, introuvables = [], [], []
    for d in jours:
        z = source.lire(f"{RACINE_J}/" + CHEMINS_J[nature].format(s=sym, d=d.date().isoformat()))
        if z is None:
            introuvables.append(d.date().isoformat())
            continue
        y = lire_klines(z)
        ajouts.append(y[y.index < naif(fin)])
        trouves.append(d.date().isoformat())
    if journal is not None:
        journal.setdefault(nature, {})[sym] = {"jours_comble": trouves, "jours_introuvables": introuvables}
    if not ajouts:
        return x
    y = pd.concat([x] + ajouts)
    return y[~y.index.duplicated(keep="first")].sort_index()  # la mensuelle prime en cas de doublon


def charger_symbole(source, sym: str, nature: str, debut: pd.Timestamp, fin: pd.Timestamp, journal: dict | None = None):
    ms = mois(debut, fin)
    if nature in CHEMINS_J:
        modele = {"1d": "klines/{s}/1d/{s}-1d-{m}.zip", "1h": "klines/{s}/1h/{s}-1h-{m}.zip",
                  "marque": "markPriceKlines/{s}/1h/{s}-1h-{m}.zip"}[nature]
        cles = [f"{RACINE}/" + modele.format(s=sym, m=m) for m in ms]
        return combler(source, sym, nature, _serie(source, cles, lire_klines, fin), debut, fin, journal)
    if nature == "financement":
        cles = [f"{RACINE}/fundingRate/{sym}/{sym}-fundingRate-{m}.zip" for m in ms]
        return _serie(source, cles, lire_financement, fin)
    raise ValueError(nature)


def symboles_usdt(source) -> list[str]:
    return sorted(s for s in source.lister(f"{RACINE}/klines/") if s.endswith("USDT"))


def charger_jours(source, symboles, debut, fin, fils=8, journal: dict | None = None) -> dict:
    with ThreadPoolExecutor(fils) as ex:
        res = dict(zip(symboles, ex.map(lambda s: charger_symbole(source, s, "1d", debut, fin, journal), symboles)))
    res = {s: v for s, v in res.items() if v is not None and len(v)}
    close = pd.DataFrame({s: v["close"] for s, v in res.items()})
    vol = pd.DataFrame({s: v["volume_usdt"] for s, v in res.items()})
    idx = pd.date_range(close.index.min(), close.index.max(), freq="D")
    return {"close": close.reindex(idx), "volume": vol.reindex(idx)}


def charger_heures(source, symboles, debut, fin, fils=8, journal: dict | None = None):
    def un(s):
        return s, charger_symbole(source, s, "1h", debut, fin, journal), charger_symbole(source, s, "marque", debut, fin, journal), \
            charger_symbole(source, s, "financement", debut, fin)
    with ThreadPoolExecutor(fils) as ex:
        res = list(ex.map(un, symboles))
    k = {s: c for s, c, _, _ in res if c is not None}
    mk = {s: m for s, _, m, _ in res if m is not None}
    fi = {s: f for s, _, _, f in res if f is not None}
    idx = pd.date_range(min(v.index.min() for v in k.values()), max(v.index.max() for v in k.values()), freq="h")
    heures = {"open": pd.DataFrame({s: v["open"] for s, v in k.items()}).reindex(idx),
              "close": pd.DataFrame({s: v["close"] for s, v in k.items()}).reindex(idx)}
    # prix de marque : repli sur le contrat si l'archive de marque manque, signalé
    repli = sorted(set(k) - set(mk))
    heures["mark_high"] = pd.DataFrame({s: (mk[s]["high"] if s in mk else k[s]["high"]) for s in k}).reindex(idx)
    heures["mark_low"] = pd.DataFrame({s: (mk[s]["low"] if s in mk else k[s]["low"]) for s in k}).reindex(idx)
    financement = pd.DataFrame(fi).sort_index() if fi else pd.DataFrame()
    return heures, financement, {"marque_repli_contrat": repli, "sans_financement": sorted(set(k) - set(fi))}


def empreinte(tableaux: dict) -> str:
    h = hashlib.sha256()
    for nom in sorted(tableaux):
        h.update(nom.encode())
        h.update(pd.util.hash_pandas_object(tableaux[nom], index=True).values.tobytes())
    return h.hexdigest()


if __name__ == "__main__":
    print(json.dumps({"doc": __doc__.splitlines()[0]}, ensure_ascii=False))
