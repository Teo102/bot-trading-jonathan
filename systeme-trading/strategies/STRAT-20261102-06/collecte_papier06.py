#!/usr/bin/env python3
"""Collecte des données publiques du papier de STRAT-06-bis (PLAN_PAPIER_COHORTES.md § 2). Aucune clé, aucun ordre.

Trois fichiers CSV en ajout seul, au format long, chacun avec l'heure de lecture :
- `jours.csv`       : date, symbole, close, volume (USDT), lu_utc — bougies 1 j closes seulement ;
- `heures.csv`      : heure, symbole, open, close, mark_high, mark_low, lu_utc — bougies 1 h closes seulement ;
- `financement.csv` : heure, symbole, taux, lu_utc.
Une ligne écrite n'est jamais réécrite, et une clé déjà connue n'est pas réécrite : la première observation fait foi
(la donnée telle qu'elle était connue à la date). Chaque ajout est inscrit dans `journal_collecte.csv` avec
l'empreinte SHA-256 des octets ajoutés. Les révisions éventuelles de la source se voient au rejeu hebdomadaire sur
les archives (`rejeu_cohortes06.py`).

Univers collecté : perpétuels USDT (`contractType` PERPETUAL) dont l'actif sous-jacent est une crypto
(`underlyingType` COIN, leçon L10), plus les symboles déjà collectés. Les volumes journaliers remontent à la première
bougie de chaque symbole, comme les archives de la v1, pour dater la cotation par le premier jour de volume.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import time
from pathlib import Path

import pandas as pd

FAPI = "https://fapi.binance.com"
DEBUT = pd.Timestamp("2019-09-01")
UNE_HEURE = pd.Timedelta(hours=1)
UN_JOUR = pd.Timedelta(days=1)
COLS = {"jours": ["date", "symbole", "close", "volume", "lu_utc"],
        "heures": ["heure", "symbole", "open", "close", "mark_high", "mark_low", "lu_utc"],
        "financement": ["heure", "symbole", "taux", "lu_utc"]}
CLES = {"jours": ["date", "symbole"], "heures": ["heure", "symbole"], "financement": ["heure", "symbole"]}


def ms(t: pd.Timestamp) -> int:
    return int(pd.Timestamp(t).timestamp() * 1000)


def de_ms(x) -> pd.Timestamp:
    return pd.Timestamp(int(x), unit="ms")


class Http:
    """Appels publics à l'API Binance Futures, avec reprises et une pause pour rester sous la limite de poids."""

    def __init__(self, pause: float = 0.12, essais: int = 5):
        import requests
        self.s, self.pause, self.essais, self.appels = requests.Session(), pause, essais, 0

    def get(self, chemin: str, params: dict | None = None):
        for i in range(self.essais):
            self.appels += 1
            try:
                r = self.s.get(FAPI + chemin, params=params, timeout=30)
                if r.status_code == 200:
                    time.sleep(self.pause)
                    return r.json()
                if r.status_code in (418, 429) or r.status_code >= 500:
                    time.sleep(5 * (i + 1))
                    continue
                return None  # 400 : symbole inconnu ou retiré
            except Exception:  # noqa: BLE001
                time.sleep(2 * (i + 1))
        raise RuntimeError(f"Échec après {self.essais} essais : {chemin} {params}")


class Collecteur:
    def __init__(self, dossier: Path, http=None):
        self.d, self.http = Path(dossier), http
        self.d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------ fichiers en ajout seul
    def _fichier(self, nom: str) -> Path:
        return self.d / f"{nom}.csv"

    def _lire(self, nom: str) -> pd.DataFrame:
        f = self._fichier(nom)
        if not f.exists():
            return pd.DataFrame(columns=COLS[nom])
        num = {c: "float64" for c in COLS[nom] if c not in CLES[nom] + ["lu_utc"]}
        return pd.read_csv(f, dtype={"symbole": "category", CLES[nom][0]: str, "lu_utc": str, **num})

    def _ajouter(self, nom: str, lignes: list[dict], lu: pd.Timestamp) -> int:
        """Ajoute seulement les clés jamais vues. Inscrit l'ajout et son empreinte au journal de collecte."""
        if not lignes:
            return 0
        deja = self._lire(nom)
        vus = set(zip(*(deja[c].astype(str) for c in CLES[nom]))) if len(deja) else set()
        nouv = []
        for l in lignes:
            k = tuple(str(l[c]) for c in CLES[nom])
            if k in vus:
                continue
            vus.add(k)
            nouv.append({**l, "lu_utc": lu.strftime("%Y-%m-%dT%H:%M:%SZ")})
        if not nouv:
            return 0
        tampon = io.StringIO()
        w = csv.DictWriter(tampon, fieldnames=COLS[nom])
        neuf = not self._fichier(nom).exists()
        if neuf:
            w.writeheader()
        w.writerows(nouv)
        octets = tampon.getvalue().encode()
        with self._fichier(nom).open("ab") as f:
            f.write(octets)
        jc = self.d / "journal_collecte.csv"
        neuf_j = not jc.exists()
        with jc.open("a", newline="") as f:
            wj = csv.writer(f)
            if neuf_j:
                wj.writerow(["lu_utc", "fichier", "lignes", "sha256"])
            wj.writerow([lu.strftime("%Y-%m-%dT%H:%M:%SZ"), f"{nom}.csv", len(nouv), hashlib.sha256(octets).hexdigest()])
        return len(nouv)

    # ------------------------------------------------ univers
    def symboles(self) -> list[str]:
        info = self.http.get("/fapi/v1/exchangeInfo") or {}
        live = {s["symbol"] for s in info.get("symbols", []) if s.get("quoteAsset") == "USDT"
                and s.get("contractType") == "PERPETUAL" and s.get("underlyingType", "COIN") == "COIN"}
        deja = set(self._lire("jours")["symbole"].dropna().unique())
        return sorted(live | deja)

    # ------------------------------------------------ mises à jour
    def maj_jours(self, maintenant: pd.Timestamp, symboles: list[str] | None = None) -> int:
        """Bougies 1 j closes, depuis la dernière date connue de chaque symbole (ou sa première bougie)."""
        deja = self._lire("jours")
        dernier = deja.groupby("symbole")["date"].max().to_dict() if len(deja) else {}
        lignes = []
        for s in symboles or self.symboles():
            debut = pd.Timestamp(dernier[s]) + UN_JOUR if s in dernier else DEBUT
            while debut < maintenant.normalize():
                k = self.http.get("/fapi/v1/klines", {"symbol": s, "interval": "1d", "startTime": ms(debut), "limit": 1500}) or []
                closes = [x for x in k if de_ms(x[6]) < maintenant]
                for x in closes:
                    lignes.append({"date": de_ms(x[0]).strftime("%Y-%m-%d"), "symbole": s, "close": float(x[4]), "volume": float(x[7])})
                if len(k) < 1500 or not closes:
                    break
                debut = de_ms(closes[-1][0]) + UN_JOUR
        return self._ajouter("jours", lignes, maintenant)

    def maj_heures(self, symboles: list[str], depuis: pd.Timestamp, maintenant: pd.Timestamp) -> int:
        """Bougies 1 h closes du contrat et du prix de marque."""
        deja = self._lire("heures")
        dernier = deja.groupby("symbole")["heure"].max().to_dict() if len(deja) else {}
        lignes = []
        for s in symboles:
            debut = pd.Timestamp(dernier[s]) + UNE_HEURE if s in dernier else pd.Timestamp(depuis).floor("h")
            while debut < maintenant.floor("h"):
                p = {"symbol": s, "interval": "1h", "startTime": ms(debut), "limit": 1500}
                k = [x for x in (self.http.get("/fapi/v1/klines", p) or []) if de_ms(x[6]) < maintenant]
                mk = {x[0]: x for x in (self.http.get("/fapi/v1/markPriceKlines", p) or []) if de_ms(x[6]) < maintenant}
                for x in k:
                    if x[0] not in mk:
                        continue  # heure sans prix de marque : non écrite, relue au prochain passage
                    lignes.append({"heure": de_ms(x[0]).strftime("%Y-%m-%d %H:%M:%S"), "symbole": s, "open": float(x[1]),
                                   "close": float(x[4]), "mark_high": float(mk[x[0]][2]), "mark_low": float(mk[x[0]][3])})
                if len(k) < 1500 or not k:
                    break
                debut = de_ms(k[-1][0]) + UNE_HEURE
        return self._ajouter("heures", lignes, maintenant)

    def maj_financement(self, symboles: list[str], depuis: pd.Timestamp, maintenant: pd.Timestamp) -> int:
        deja = self._lire("financement")
        dernier = deja.groupby("symbole")["heure"].max().to_dict() if len(deja) else {}
        lignes = []
        for s in symboles:
            debut = pd.Timestamp(dernier[s]) + pd.Timedelta(minutes=1) if s in dernier else pd.Timestamp(depuis)
            while debut < maintenant:
                f = self.http.get("/fapi/v1/fundingRate", {"symbol": s, "startTime": ms(debut), "limit": 1000}) or []
                f = [x for x in f if de_ms(x["fundingTime"]) <= maintenant]
                for x in f:
                    h = de_ms(x["fundingTime"]).round("min")  # comme donnees_binance.lire_financement
                    lignes.append({"heure": h.strftime("%Y-%m-%d %H:%M:%S"), "symbole": s, "taux": float(x["fundingRate"])})
                if len(f) < 1000 or not f:
                    break
                debut = de_ms(f[-1]["fundingTime"]) + pd.Timedelta(minutes=1)
        return self._ajouter("financement", lignes, maintenant)

    # ------------------------------------------------ lecture au format du moteur
    @staticmethod
    def _premiere(df: pd.DataFrame, cles: list[str]) -> tuple[pd.DataFrame, int]:
        if df.empty:
            return df, 0
        doublons = df.duplicated(cles, keep="first")   # le fichier est écrit dans l'ordre des lectures : la première ligne fait foi
        if not doublons.any():
            return df, 0
        return df[~doublons], int(doublons.sum())

    def charger_jours(self) -> dict:
        d, _ = self._premiere(self._lire("jours"), CLES["jours"])
        if d.empty:
            return {"close": pd.DataFrame(), "volume": pd.DataFrame()}
        d["date"] = pd.to_datetime(d["date"])
        out = {k: d.pivot(index="date", columns="symbole", values=k).sort_index() for k in ("close", "volume")}
        idx = pd.date_range(min(v.index.min() for v in out.values()), max(v.index.max() for v in out.values()), freq="D")
        return {k: v.reindex(idx).rename(columns={"BTCUSDT": "BTC"}) for k, v in out.items()}

    def charger_heures(self) -> dict:
        d, _ = self._premiere(self._lire("heures"), CLES["heures"])
        if d.empty:
            return {k: pd.DataFrame() for k in ("open", "close", "mark_high", "mark_low")}
        d["heure"] = pd.to_datetime(d["heure"])
        idx = pd.date_range(d["heure"].min(), d["heure"].max(), freq="h")
        return {k: d.pivot(index="heure", columns="symbole", values=k).reindex(idx).rename(columns={"BTCUSDT": "BTC"})
                for k in ("open", "close", "mark_high", "mark_low")}

    def charger_financement(self) -> pd.DataFrame:
        d, _ = self._premiere(self._lire("financement"), CLES["financement"])
        if d.empty:
            return pd.DataFrame()
        d["heure"] = pd.to_datetime(d["heure"])
        return d.pivot(index="heure", columns="symbole", values="taux").sort_index().rename(columns={"BTCUSDT": "BTC"})


def noms_a_suivre(signaux_csv: Path) -> set[str]:
    """Symboles (format API) de tous les signaux écrits : leurs heures et leur financement sont collectés."""
    if not Path(signaux_csv).exists():
        return set()
    s = pd.read_csv(signaux_csv, dtype=str, keep_default_na=False)
    return {x for v in s["shorts"] for x in v.split(",") if x}
