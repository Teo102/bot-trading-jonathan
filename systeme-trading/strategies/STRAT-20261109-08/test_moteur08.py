"""Tests synthétiques du moteur et du lanceur de STRAT-20261109-08 (règle m4, verrou m2, contraintes). Aucun réseau.
Exécution : python3 -B test_moteur08.py"""
import sys

sys.dont_write_bytecode = True
import copy
import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import moteur_intraday as mi  # noqa: E402
import run_essai08 as r8  # noqa: E402

P = mi.ParamsIntraday()
T0 = pd.Timestamp("2022-03-01 10:00")


def minutes_plates(debut="2022-03-01", jours=3, prix=100.0):
    idx = pd.date_range(debut, periods=jours * 1440, freq="min")
    return pd.DataFrame({"open": prix, "high": prix, "low": prix, "close": prix}, index=idx)


class Magasin:
    """Faux magasin en mémoire, avec la même borne que MagasinCompact."""
    def __init__(self, donnees: dict, borne):
        self.d, self.borne = donnees, pd.Timestamp(borne)
    def minutes(self, s, a, b):
        if b >= self.borne:
            raise mi.Verrou("borne")
        x = self.d[s]
        return x[(x.index >= a) & (x.index <= b)]


def ev(symboles, t=T0, volumes=None):
    volumes = volumes or [1.0] * len(symboles)
    return pd.DataFrame({"symbole": symboles, "t": [t] * len(symboles), "rendement_15m": -0.05, "var_oi_15m": -0.04, "volume_15m": volumes})


class Position(unittest.TestCase):
    def test_sortie_au_temps(self):
        m = minutes_plates()
        te = T0 + P.d
        m.loc[m.index >= te + pd.Timedelta(minutes=30), ["open", "high", "low", "close"]] = 102.0
        r = mi.jouer_position(m, te, P)
        self.assertEqual(r["statut"], "temps")
        self.assertEqual(r["t_sortie"], te + P.h)
        self.assertAlmostEqual(r["entree"], 100 * 1.001)
        self.assertAlmostEqual(r["sortie"], 102 * (1 - 0.0005))

    def test_m4_stop_dans_la_minute_d_entree(self):
        m = minutes_plates()
        te = T0 + P.d
        m.loc[te, "low"] = 90.0
        r = mi.jouer_position(m, te, P)
        self.assertEqual(r["statut"], "stop")
        self.assertEqual(r["t_sortie"], te)
        niveau = 100 * 1.001 * 0.95
        self.assertAlmostEqual(r["sortie"], niveau * (1 - 0.003))

    def test_m4_sortie_a_l_ouverture_avant_le_plus_bas(self):
        m = minutes_plates()
        te = T0 + P.d
        m.loc[te + P.h, "low"] = 50.0  # plus bas énorme dans la minute de sortie : jamais lu
        r = mi.jouer_position(m, te, P)
        self.assertEqual(r["statut"], "temps")

    def test_saut_sous_le_niveau(self):
        m = minutes_plates()
        te = T0 + P.d
        t2 = te + pd.Timedelta(minutes=7)
        m.loc[m.index >= t2, ["open", "high", "low", "close"]] = 80.0
        r = mi.jouer_position(m, te, P)
        self.assertEqual(r["statut"], "stop")
        self.assertEqual(r["t_sortie"], t2)
        self.assertAlmostEqual(r["sortie"], 80 * (1 - 0.003))  # au pire : l'ouverture, sous le niveau

    def test_entree_absente(self):
        m = minutes_plates().drop(T0 + P.d)
        self.assertEqual(mi.jouer_position(m, T0 + P.d, P)["statut"], "absent")


class Contraintes(unittest.TestCase):
    def test_k_et_departage_par_volume(self):
        syms = [f"S{i}USDT" for i in range(6)]
        mag = Magasin({s: minutes_plates() for s in syms}, "2022-03-10")
        pos, ec = mi.simuler(ev(syms, volumes=[6, 5, 4, 3, 2, 1]), mag, P, pd.Timestamp("2022-03-10"))
        self.assertEqual(len(pos), 5)
        self.assertNotIn("S5USDT", set(pos["symbole"]))  # le plus petit volume est écarté
        self.assertEqual(ec["emplacement"], 1)
        pos2, _ = mi.simuler(ev(syms[::-1], volumes=[1, 2, 3, 4, 5, 6]), mag, P, pd.Timestamp("2022-03-10"))
        self.assertEqual(set(pos2["symbole"]), set(pos["symbole"]))  # indépendant de l'ordre des lignes

    def test_pause_apres_sortie(self):
        mag = Magasin({"AUSDT": minutes_plates()}, "2022-03-10")
        e = pd.concat([ev(["AUSDT"]), ev(["AUSDT"], t=T0 + pd.Timedelta(hours=6)), ev(["AUSDT"], t=T0 + pd.Timedelta(hours=9))])
        pos, ec = mi.simuler(e, mag, P, pd.Timestamp("2022-03-10"))
        # 1re sortie à 14:05 ; 16:00 + 5 min < 14:05 + 4 h -> pause ; 19:00 + 5 min ≥ 18:05 -> pris
        self.assertEqual(len(pos), 2)
        self.assertEqual(ec["pause"], 1)

    def test_deux_stops_par_jour_sans_anticipation(self):
        m = minutes_plates()
        syms = ["AUSDT", "BUSDT", "CUSDT", "DUSDT"]
        donnees = {s: m.copy() for s in syms}
        for s in ("AUSDT", "BUSDT"):
            donnees[s].loc[T0 + P.d, "low"] = 90.0       # deux stops à 10:05
        donnees["DUSDT"].loc[T0 + pd.Timedelta(hours=3) + P.d, "low"] = 90.0
        mag = Magasin(donnees, "2022-03-10")
        e = pd.concat([ev(["AUSDT", "BUSDT"]), ev(["CUSDT"], t=T0 + pd.Timedelta(hours=2)),
                       ev(["DUSDT"], t=T0 - pd.Timedelta(minutes=30))])
        pos, ec = mi.simuler(e, mag, P, pd.Timestamp("2022-03-10"))
        self.assertIn("DUSDT", set(pos["symbole"]))   # entré avant les stops : pris
        self.assertNotIn("CUSDT", set(pos["symbole"]))  # après 2 stops dans la journée : écarté
        self.assertEqual(ec["stops_du_jour"], 1)
        e2 = pd.concat([ev(["AUSDT", "BUSDT"]), ev(["CUSDT"], t=pd.Timestamp("2022-03-02 01:00"))])
        pos2, _ = mi.simuler(e2, mag, P, pd.Timestamp("2022-03-10"))
        self.assertIn("CUSDT", set(pos2["symbole"]))  # le lendemain : repris

    def test_fin_de_bloc_et_verrou(self):
        mag = Magasin({"AUSDT": minutes_plates()}, "2022-03-01 14:00")
        pos, ec = mi.simuler(ev(["AUSDT"]), mag, P, pd.Timestamp("2022-03-01 14:00"))
        self.assertTrue(pos.empty)
        self.assertEqual(ec["fin_de_bloc"], 1)
        with self.assertRaises(mi.Verrou):
            mag.minutes("AUSDT", T0, pd.Timestamp("2022-03-01 14:00"))

    def test_financement_et_placebo(self):
        mag = Magasin({"AUSDT": minutes_plates()}, "2022-03-10")
        fin = pd.Series([0.001, 0.002], index=pd.to_datetime(["2022-03-01 08:00", "2022-03-01 12:00"]))
        pos, _ = mi.simuler(ev(["AUSDT"]), mag, P, pd.Timestamp("2022-03-10"), {"AUSDT": fin})
        self.assertAlmostEqual(pos["financement"].iloc[0], 0.002 / 5)  # seul le versement de 12:00 est dans (10:05, 14:05]
        pp, _ = mi.simuler(ev(["AUSDT"]), mag, replace(P, placebo=pd.Timedelta(hours=24)), pd.Timestamp("2022-03-10"))
        self.assertEqual(pp["t_entree"].iloc[0], T0 + pd.Timedelta(hours=24) + P.d)

    def test_magasin_compact_borne(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            m = minutes_plates()
            (tmp / "AUSDT").mkdir()
            mins = ((m.index - pd.Timestamp(0)) // pd.Timedelta(minutes=1)).astype("int64")
            np.savez_compressed(tmp / "AUSDT" / "2022-03.npz", minute=np.asarray(mins),
                                **{c: m[c].to_numpy(np.float32) for c in ("open", "high", "low", "close")}, volume_usdt=np.ones(len(m), np.float32))
            mag = mi.MagasinCompact(tmp, "2022-03-02")
            x = mag.minutes("AUSDT", T0, T0 + pd.Timedelta(hours=1))
            self.assertEqual(len(x), 61)
            with self.assertRaises(mi.Verrou):
                mag.minutes("AUSDT", T0, pd.Timestamp("2022-03-02"))
        finally:
            shutil.rmtree(tmp)

    def test_semaines(self):
        pos = pd.DataFrame({"t_sortie": pd.to_datetime(["2022-03-02 10:00", "2022-03-03 10:00", "2022-03-16 10:00"]), "net": [0.01, 0.02, -0.01]})
        w = mi.semaines(pos, pd.Timestamp("2022-02-28"), pd.Timestamp("2022-03-20"))
        self.assertEqual(list(w.round(4)), [0.03, 0.0, -0.01])


class Lanceur(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.reg = self.tmp / "registre.csv"
        shutil.copy(r8.REGISTRE, self.reg)
        self.c = json.loads(r8.CONFIG.read_text())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_refus(self):
        self.assertEqual(self.c["statut_regles"], "proposees")
        with self.assertRaises(r8.Refus):
            r8.controles("E01", self.c, self.reg)          # non figée
        c = copy.deepcopy(self.c); c["statut_regles"] = "figees"
        r8.controles("E01", c, self.reg)
        for e in ("E13", "E15", "E16", "E99"):
            with self.assertRaises(r8.Refus):
                r8.controles(e, c, self.reg)
        r_ = pd.read_csv(self.reg, dtype=str, keep_default_na=False)
        r_.loc[r_["id_essai"].isin(r8.AVANT_HE), "date"] = "2026-11-12T00:00:00Z"
        r_.to_csv(self.reg, index=False)
        with self.assertRaises(r8.Refus):
            r8.controles("E15", c, self.reg)               # décision écrite absente
        c["portes_avant_hors_echantillon"] = "franchies"
        r8.controles("E15", c, self.reg)
        with self.assertRaises(r8.Refus):
            r8.controles("E16", c, self.reg)               # avant E15
        with self.assertRaises(r8.Refus):
            r8.controles("E01", c, self.reg)               # déjà lancé

    def test_bout_en_bout(self):
        c = copy.deepcopy(self.c); c["statut_regles"] = "figees"
        c["blocs"]["developpement"] = ["2022-03-01", "2022-03-20"]
        c["bootstrap"]["tirages"] = 200
        syms = ["AUSDT", "BUSDT"]
        dossier = self.tmp / "compact"
        rng = np.random.default_rng(1)
        for s in syms:
            m = minutes_plates(jours=20)
            m["open"] = m["high"] = m["low"] = m["close"] = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, len(m))))
            (dossier / s).mkdir(parents=True)
            mins = ((m.index - pd.Timestamp(0)) // pd.Timedelta(minutes=1)).astype("int64")
            np.savez_compressed(dossier / s / "2022-03.npz", minute=np.asarray(mins),
                                **{k: m[k].to_numpy(np.float32) for k in ("open", "high", "low", "close")}, volume_usdt=np.ones(len(m), np.float32))
        cand = pd.DataFrame({"symbole": ["AUSDT", "BUSDT", "AUSDT", "AUSDT"],
                             "t": ["2022-03-02 10:00", "2022-03-02 10:00", "2022-03-05 03:00", "2022-03-19 23:00"],
                             "rendement_15m": [-0.05, -0.035, -0.06, -0.05], "var_oi_15m": [-0.04, -0.04, -0.035, -0.04], "volume_15m": [2.0, 1.0, 1.0, 1.0]})
        out = r8.executer("E01", cand, dossier, c, self.reg, self.tmp / "o", financement={}, financement_compte=False)
        mt = out["metriques"]
        self.assertEqual(mt["positions"], 2)   # BUSDT sous X ; la dernière déborde la fin du bloc
        self.assertEqual(mt["ecarts"]["fin_de_bloc"], 1)
        self.assertTrue((self.tmp / "o" / "E01_metriques.md").exists())
        self.assertTrue(r8.lire_registre(self.reg)["E01"]["date"])
        with self.assertRaises(r8.Refus):
            r8.executer("E01", cand, dossier, c, self.reg, self.tmp / "o", financement={})


if __name__ == "__main__":
    unittest.main(verbosity=1)
