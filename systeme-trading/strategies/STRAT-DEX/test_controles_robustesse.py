"""Tests synthétiques de controles_robustesse.py. Exécution : python -B test_controles_robustesse.py"""
import sys, unittest
import numpy as np, pandas as pd
sys.dont_write_bytecode = True
sys.path.insert(0, ".")
import controles_robustesse as cr

T = 200 * 86400


def cohorte(n_w=60, persist=0.0, graine=1):
    rng = np.random.default_rng(graine)
    lignes = []
    for w in range(n_w):
        talent = rng.normal()
        for periode in (0, 1):
            for k in range(5):
                t0 = T - (80 if periode == 0 else 20) * 86400 + k
                r = persist * talent + rng.normal()
                lignes.append(dict(wallet=f"W{w}", mint=f"M{w}_{periode}_{k}", t0=t0, cout=100.0, pnl=100 * r, sorti=True))
    return pd.DataFrame(lignes)


class Tests(unittest.TestCase):
    def test_fisher_unilateral(self):
        self.assertAlmostEqual(cr.fisher_unilateral(5, 0, 0, 5), 1 / 252, places=6)
        self.assertGreater(cr.fisher_unilateral(0, 5, 5, 0), 0.99)

    def test_aucune_persistance_sous_le_hasard(self):
        faux = sum(cr.evaluer(cohorte(persist=0.0, graine=g), T, set())["verdict"] == "persistance_soutenue" for g in range(20))
        self.assertLessEqual(faux, 2)

    def test_persistance_forte_detectee(self):
        self.assertEqual(cr.evaluer(cohorte(n_w=80, persist=2.0), T, set())["verdict"], "persistance_soutenue")

    def test_echantillon_insuffisant(self):
        self.assertEqual(cr.evaluer(cohorte(n_w=20, persist=2.0), T, set())["verdict"], "non_concluant_echantillon_insuffisant")

    def test_graine_retiree(self):
        q = cohorte(n_w=40, persist=2.0)
        graines = {(w, f"M{w[1:]}_1_0") for w in q.wallet.unique()}
        res = cr.evaluer(q, T, graines)
        self.assertEqual(res["variantes"]["sans_jeton_graine"]["wallets"], 40)


if __name__ == "__main__":
    unittest.main(verbosity=1)
