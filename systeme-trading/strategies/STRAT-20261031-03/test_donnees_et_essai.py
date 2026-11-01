"""Tests hors ligne du chargeur d'archives et du lanceur d'essais. Aucune donnée de marché, aucun réseau.

Exécution : python -B test_donnees_et_essai.py
Un faux data.binance.vision est écrit dans un dossier temporaire depuis des marches aléatoires.
"""
import sys

sys.dont_write_bytecode = True
import copy
import hashlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import run_essai as re_  # noqa: E402
import test_moteur_synthetique as ts  # noqa: E402

R = db.RACINE


def ms(idx):
    return ((idx - pd.Timestamp(0)) // pd.Timedelta(milliseconds=1)).astype("int64")


def zipper(df: pd.DataFrame, nom: str, entete: bool) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr(nom.replace(".zip", ".csv"), df.to_csv(index=False, header=entete))
    return b.getvalue()


def poser(racine: Path, cle: str, donnees: bytes, somme: str | None = None):
    p = racine / cle
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(donnees)
    (racine / (cle + ".CHECKSUM")).write_text(f"{somme or hashlib.sha256(donnees).hexdigest()}  {p.name}\n")


def faux_vision(racine: Path, n_sym=14, jours=420, debut="2020-06-01", graine=3, piege_apres=None):
    j, h, f = ts.marche(n_sym=n_sym, jours=jours, graine=graine, debut=pd.Timestamp(debut))
    noms = {"BTC": "BTCUSDT", **{f"S{i:02d}": f"S{i:02d}USDT" for i in range(n_sym)}}
    vol_h = j["volume"]  # volume journalier synthétique, réparti sur 24 h
    for court, sym in noms.items():
        o, c = h["open"][court], h["close"][court]
        hi, lo = h["mark_high"][court], h["mark_low"][court]
        if piege_apres is not None:  # prix absurdes après la fin du bloc : ne doivent jamais être lus
            apres = o.index >= piege_apres
            o, c, hi, lo = (x.where(~apres, 1e9) for x in (o, c, hi, lo))
        vh = (vol_h[court].reindex(o.index, method="ffill") / 24) * 5000  # volumes en dizaines de M$
        k1h = pd.DataFrame({"open_time": ms(o.index), "open": o, "high": hi, "low": lo, "close": c,
                            "volume": 1.0, "close_time": 0, "quote_volume": vh, "count": 1, "tb": 0, "tbq": 0, "ignore": 0})
        d = k1h.set_index(o.index).resample("D").agg({"open_time": "first", "open": "first", "high": "max", "low": "min",
                                                       "close": "last", "volume": "sum", "close_time": "first",
                                                       "quote_volume": "sum", "count": "sum", "tb": "sum", "tbq": "sum", "ignore": "first"})
        fr = pd.DataFrame({"calc_time": ms(f.index) + 3, "interval": 8, "rate": 0.0001})
        for mo, g in k1h.groupby(o.index.to_period("M")):
            entete = str(mo) >= "2021-03"  # les archives récentes ont un en-tête
            poser(racine, f"{R}/klines/{sym}/1h/{sym}-1h-{mo}.zip", zipper(g, "x.zip", entete))
            poser(racine, f"{R}/markPriceKlines/{sym}/1h/{sym}-1h-{mo}.zip", zipper(g, "x.zip", entete))
        for mo, g in d.groupby(d.index.to_period("M")):
            poser(racine, f"{R}/klines/{sym}/1d/{sym}-1d-{mo}.zip", zipper(g, "x.zip", str(mo) >= "2021-03"))
        for mo, g in fr.groupby(f.index.to_period("M")):
            poser(racine, f"{R}/fundingRate/{sym}/{sym}-fundingRate-{mo}.zip", zipper(g, "x.zip", True))
    return noms


def config_test(statut="figees"):
    c = re_.charger_config()
    c = copy.deepcopy(c)
    c["statut_regles"] = statut
    c["params_base"]["volume_min"] = 0  # volumes synthétiques
    c["params_base"]["taille_univers"] = 10
    c["blocs"] = {"developpement": {"essai": "E01", "premier_lundi": "2021-01-04", "dernier_lundi": "2021-05-24",
                                    "fin_donnees_prix": "2021-05-31T02:00:00Z"}}
    c["bootstrap"]["tirages"] = 500
    return c


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.vision = cls.tmp / "vision"
        faux_vision(cls.vision, piege_apres=pd.Timestamp("2021-05-31 02:00"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def registre(self):
        r = self.tmp / f"registre_{self._testMethodName}.csv"
        shutil.copy(re_.REGISTRE, r)
        return r


class Chargeur(Base):
    def test_listing_et_entetes(self):
        src = db.VisionLocale(self.vision)
        self.assertIn("S00USDT", db.symboles_usdt(src))
        x = db.charger_symbole(src, "S00USDT", "1h", pd.Timestamp("2021-02-01"), pd.Timestamp("2021-04-01"))
        self.assertEqual(x.index.min(), pd.Timestamp("2021-02-01"))  # mois sans en-tête puis avec
        self.assertEqual(len(x), (31 + 28) * 24)

    def test_verrou_de_bloc(self):
        src = db.VisionLocale(self.vision)
        fin = pd.Timestamp("2021-05-31T02:00:00Z")
        x = db.charger_symbole(src, "S01USDT", "1h", pd.Timestamp("2021-05-01"), fin)
        self.assertLess(x.index.max(), db.naif(fin))
        self.assertLess(x["close"].max(), 1e6)  # le piège posé après la fin n'est jamais lu
        self.assertNotIn("2021-06", db.mois(pd.Timestamp("2021-01-01"), fin))

    def test_somme_invalide_refusee(self):
        cle = f"{R}/klines/S02USDT/1d/S02USDT-1d-2021-01.zip"
        sauv = (self.vision / (cle + ".CHECKSUM")).read_text()
        (self.vision / (cle + ".CHECKSUM")).write_text("0" * 64 + "  x\n")
        try:
            with self.assertRaises(db.ErreurSomme):
                db.VisionLocale(self.vision).lire(cle)
        finally:
            (self.vision / (cle + ".CHECKSUM")).write_text(sauv)

    def test_financement_arrondi(self):
        x = db.charger_symbole(db.VisionLocale(self.vision), "S00USDT", "financement", pd.Timestamp("2021-01-01"), pd.Timestamp("2021-02-01"))
        self.assertTrue((x.index.hour % 8 == 0).all() and (x.index.minute == 0).all())


class Comblement(unittest.TestCase):
    """Trou de 2 jours dans les mensuelles (cas réel des 26-27/02/2022), journalières présentes."""

    def test_trou_comble_par_les_journalieres(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            faux_vision(tmp, n_sym=3, jours=300, debut="2020-06-01")
            sym, mo = "S00USDT", "2020-10"
            trou = [pd.Timestamp("2020-10-17"), pd.Timestamp("2020-10-18")]
            for nature, chemin, pas in (("1d", "klines/{s}/1d/{s}-1d-{m}.zip", "D"), ("1h", "klines/{s}/1h/{s}-1h-{m}.zip", "h"),
                                        ("marque", "markPriceKlines/{s}/1h/{s}-1h-{m}.zip", "h")):
                cle = f"{R}/" + chemin.format(s=sym, m=mo)
                with zipfile.ZipFile(tmp / cle) as z:
                    df = pd.read_csv(z.open(z.namelist()[0]), header=None)
                t = pd.to_datetime(df[0], unit="ms")
                garde = ~t.dt.normalize().isin(trou)
                poser(tmp, cle, zipper(df[garde], "x.zip", False))
                for d in trou:  # archives journalières du trou
                    cj = f"{db.RACINE_J}/" + chemin.replace("{m}", "{d}").format(s=sym, d=d.date().isoformat())
                    jour = df[(t.dt.normalize() == d).values].copy()
                    jour.columns = ["open_time"] + [f"c{i}" for i in range(1, jour.shape[1])]  # en-tête réaliste
                    poser(tmp, cj, zipper(jour, "x.zip", True))
            src = db.VisionLocale(tmp)
            j: dict = {}
            x1 = db.charger_symbole(src, sym, "1d", pd.Timestamp("2020-09-01"), pd.Timestamp("2020-12-01"), j)
            xh = db.charger_symbole(src, sym, "1h", pd.Timestamp("2020-09-01"), pd.Timestamp("2020-12-01"), j)
            self.assertTrue(all(d in x1.index for d in trou))
            self.assertEqual(len(xh), (30 + 31 + 30) * 24)
            self.assertEqual(j["1d"][sym]["jours_comble"], ["2020-10-17", "2020-10-18"])
            self.assertEqual(j["1h"][sym]["jours_introuvables"], [])
        finally:
            shutil.rmtree(tmp)


class TrouMoteur(unittest.TestCase):
    def test_trou_en_semaine_n_est_pas_un_delistage(self):
        jj, hh, ff = ts.marche(graine=31)
        s = "S05"
        t_in = pd.Timestamp("2022-05-02 01:00")
        for k in hh:
            hh[k].loc[pd.Timestamp("2022-05-04 00:00"):pd.Timestamp("2022-05-05 23:00"), s] = np.nan  # 48 h absentes
        r = re_.m.jouer_ligne(hh, ff, s, -1, t_in, t_in + pd.Timedelta(days=7), 1.0, re_.m.Params(stop=None))
        self.assertEqual(r["statut"], "semaine")
        self.assertAlmostEqual(r["sortie"], hh["open"].loc[t_in + pd.Timedelta(days=7), s])

    def test_trou_a_l_heure_de_sortie(self):
        jj, hh, ff = ts.marche(graine=32)
        s = "S06"
        t_in = pd.Timestamp("2022-05-02 01:00")
        t_out = t_in + pd.Timedelta(days=7)
        for k in hh:
            hh[k].loc[t_out:t_out + pd.Timedelta(hours=2), s] = np.nan
        r = re_.m.jouer_ligne(hh, ff, s, 1, t_in, t_out, 1.0, re_.m.Params(stop=None))
        self.assertEqual(r["statut"], "semaine")
        self.assertAlmostEqual(r["sortie"], hh["open"].loc[t_out + pd.Timedelta(hours=3), s])


class Lanceur(Base):
    def test_refus_regles_non_figees(self):
        with self.assertRaises(re_.Refus):
            re_.executer("E01", db.VisionLocale(self.vision), config_test("proposees"), self.registre(), self.tmp / "o1")

    def test_refus_hors_echantillon(self):
        with self.assertRaises(re_.Refus):
            re_.controles("E25", config_test(), self.registre())

    def test_config_reelle_figee_le_01_11(self):
        c = re_.charger_config()
        self.assertEqual(c["statut_regles"], "figees")  # gel du 01/11/2026, toute modification ouvre une nouvelle stratégie
        self.assertEqual(c["params_base"]["trou_max_jours"], 7)
        self.assertIn("LUNC", c["exclusions"]["memecoins_liste_close_2026-11-01"])

    def test_bout_en_bout_puis_refus_de_relance(self):
        reg = self.registre()
        out = re_.executer("E01", db.VisionLocale(self.vision), config_test(), reg, self.tmp / "o2")
        mt = out["metriques"]
        self.assertEqual(mt["semaines"], 21)
        self.assertGreater(mt["lignes"], 0)
        for k in ("sharpe_net_annualise", "beta_btc_hebdo", "alpha_annualise_residuel"):
            self.assertTrue(np.isfinite(mt[k]), k)
        self.assertLess(abs(mt["beta_btc_hebdo"]), 1.0)
        e01 = pd.read_csv(reg).set_index("id_essai").loc["E01"]
        self.assertTrue(isinstance(e01["date"], str) and e01["date"].startswith("20"))
        self.assertTrue((self.tmp / "o2" / "E01_metriques.md").exists())
        with self.assertRaises(re_.Refus):
            re_.executer("E01", db.VisionLocale(self.vision), config_test(), reg, self.tmp / "o3")

    def test_bootstrap_blocs(self):
        x = np.random.default_rng(0).normal(0.01, 0.02, 200)
        lo, hi = re_.bootstrap_blocs(x, 4, 2000, 1, 0.90)
        self.assertLess(lo, x.mean())
        self.assertGreater(hi, x.mean())


if __name__ == "__main__":
    unittest.main(verbosity=2)
