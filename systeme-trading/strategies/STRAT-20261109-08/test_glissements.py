"""Tests hors ligne de la mesure des glissements. Exécution : python3 -B test_glissements.py"""
import sys, io, zipfile, unittest
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import mesure_glissements as mg


def bande():
    t0 = pd.Timestamp("2022-03-01 10:05")
    # ventes agressives (acheteur passif = True) et achats agressifs (False)
    return pd.DataFrame({"prix": [100.0, 100.2, 100.4, 99.0, 98.0], "qte": [10.0, 30.0, 100.0, 50.0, 100.0],
                         "t": [t0, t0 + pd.Timedelta(seconds=1), t0 + pd.Timedelta(seconds=2), t0 + pd.Timedelta(seconds=3), t0 + pd.Timedelta(seconds=4)],
                         "acheteur_teneur": [False, False, False, True, True]})


class Glissement(unittest.TestCase):
    def test_achat(self):
        g = mg.glissement(bande(), pd.Timestamp("2022-03-01 10:05"), 5000.0, True)
        # 1 000 à 100, 3 006 à 100,2, reste 994 à 100,4
        qte = 10 + 30 + 994 / 100.4
        self.assertAlmostEqual(g["glissement"], (5000 / qte) / 100 - 1, places=10)
        self.assertTrue(g["rempli"])

    def test_vente(self):
        g = mg.glissement(bande(), pd.Timestamp("2022-03-01 10:05"), 9900.0, False)
        # référence = premier prix ≥ τ (100) ; 4 950 à 99, 4 950 à 98
        qte = 50 + 4950 / 98
        self.assertAlmostEqual(g["glissement"], 1 - (9900 / qte) / 100, places=10)

    def test_non_rempli(self):
        g = mg.glissement(bande(), pd.Timestamp("2022-03-01 10:05"), 1e9, True)
        self.assertFalse(g["rempli"])
        self.assertIsNone(g["glissement"])

    def test_lecture_et_entete(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("a.csv", "agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker\n1,100.5,2,1,1,1646128800000,true\n2,100.6,1,2,2,1646128801000,false\n")
        df = mg.lire_aggtrades(b.getvalue())
        self.assertEqual(len(df), 2)
        self.assertTrue(df["acheteur_teneur"].iloc[0])
        self.assertEqual(df["t"].iloc[0], pd.Timestamp("2022-03-01 10:00"))

    def test_lecture_par_fenetres_et_microsecondes(self):
        b = io.BytesIO()
        lignes = [f"{i},{100 + i / 100},1,{i},{i},{1735689600000000 + i * 60_000_000},{'true' if i % 2 else 'false'}" for i in range(10)]
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("a.csv", "\n".join(lignes) + "\n")   # sans en-tête, temps en microsecondes (archives récentes)
        t0 = pd.Timestamp("2025-01-01 00:00")
        tout = mg.lire_aggtrades(b.getvalue(), morceau=3)
        self.assertEqual(len(tout), 10)
        f = mg.lire_aggtrades(b.getvalue(), [(t0 + pd.Timedelta(minutes=2), t0 + pd.Timedelta(minutes=4)),
                                             (t0 + pd.Timedelta(minutes=8), t0 + pd.Timedelta(minutes=20))], morceau=3)
        self.assertEqual([x.minute for x in f["t"]], [2, 3, 8, 9])
        self.assertEqual(list(f["acheteur_teneur"]), [False, True, False, True])
        self.assertTrue(mg.lire_aggtrades(b.getvalue(), [(t0 + pd.Timedelta(hours=5), t0 + pd.Timedelta(hours=6))]).empty)

    def test_echantillon_hors_he_et_reproductible(self):
        c = pd.DataFrame({"symbole": ["A", "B", "C"], "t": ["2023-01-01 10:00", "2024-06-01 10:00", "2025-09-01 10:00"],
                          "rendement_15m": -0.05, "var_oi_15m": -0.04, "volume_15m": 1.0})
        e1, e2 = mg.echantillon(c, 50), mg.echantillon(c, 50)
        self.assertEqual(list(e1["symbole"]), list(e2["symbole"]))
        self.assertNotIn("C", set(e1["symbole"]))  # hors échantillon exclu

    def test_regle(self):
        self.assertEqual(mg.plafond_retenu(0.001, [0.0005] * 10), 0.001)
        self.assertAlmostEqual(mg.plafond_retenu(0.001, [0.0012, 0.0021, 0.003, 0.0041]), 0.0033)


if __name__ == "__main__":
    unittest.main(verbosity=1)
