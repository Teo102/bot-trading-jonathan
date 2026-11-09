"""Tests hors ligne du criblage de STRAT-07. Exécution : python3 -B test_criblage_strat07.py"""
import sys, unittest
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import criblage_strat07 as c


def serie(taux, pas_h=8, debut="2022-01-01"):
    idx = pd.date_range(debut, periods=len(taux), freq=f"{pas_h}h")
    return pd.Series(taux, index=idx)


class Episodes(unittest.TestCase):
    def test_annualisation(self):
        s = serie([0.0001] * 5, 8)
        self.assertAlmostEqual(c.annualiser(s).iloc[-1], 0.0001 * 1095)
        s4 = serie([0.0001] * 5, 4)
        self.assertAlmostEqual(c.annualiser(s4).iloc[-1], 0.0001 * 2190)

    def test_sans_anticipation(self):
        # 0,05 % par 8 h = 54,75 %/an : au-dessus de 30 % ; 0,00005 = 5,5 %/an : sous 10 %
        taux = [0.00001, 0.0005, 0.0005, 0.0005, 0.00005, 0.00001]
        s = serie(taux)
        el = pd.Series(True, index=pd.date_range("2021-12-01", "2022-02-01"))
        e = c.episodes(s, el, 0.30, 0.10)
        self.assertEqual(len(e), 1)
        # entrée après le 1er versement haut (non encaissé) ; encaisse 0,0005 x 2 puis 0,00005 (sortie)
        self.assertAlmostEqual(e[0]["brut"], 0.0005 * 2 + 0.00005)
        self.assertEqual(e[0]["versements"], 3)

    def test_non_eligible_et_taux_negatif(self):
        taux = [0.0005, -0.001, 0.00001]
        s = serie(taux)
        self.assertEqual(c.episodes(s, pd.Series(False, index=pd.date_range("2021-12-01", "2022-02-01")), 0.30, 0.10), [])
        el = pd.Series(True, index=pd.date_range("2021-12-01", "2022-02-01"))
        e = c.episodes(s, el, 0.30, 0.10)
        self.assertAlmostEqual(e[0]["brut"], -0.001)  # le taux négatif se paie, et il fait sortir

    def test_portefeuille(self):
        eps = pd.DataFrame({"debut": pd.to_datetime(["2022-01-01", "2022-01-01", "2022-01-02"]),
                            "fin": pd.to_datetime(["2022-01-03", "2022-01-03", "2022-01-04"]), "net": [0.02, 0.02, 0.02]})
        p = c.portefeuille(eps, emplacements=1)
        self.assertEqual(p["episodes_pris"], 1)
        self.assertEqual(p["episodes_refuses"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
