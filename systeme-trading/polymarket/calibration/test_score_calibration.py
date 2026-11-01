"""Tests de score_calibration.py sur journaux synthétiques. Exécution : python -B test_score_calibration.py"""
import sys

sys.dont_write_bytecode = True
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_calibration as s  # noqa: E402


def journal(n=200, biais=0.0, graine=1, mi_mandat=False):
    rng = np.random.default_rng(graine)
    vrai = rng.uniform(0.05, 0.95, n)
    y = (rng.uniform(size=n) < vrai).astype(int)
    milieu = np.clip(vrai + rng.normal(0, 0.08, n), 0.02, 0.98)
    propre = np.clip(vrai + biais + rng.normal(0, 0.02, n), 0.01, 0.99)
    return pd.DataFrame({"evenement": [f"E{i // 2}" for i in range(n)], "mi_mandat": "oui" if mi_mandat else "non",
                         "annule": "non", "issue_resolue": y, "proba_propre": propre, "milieu": milieu,
                         "bid": milieu - 0.005, "ask": milieu + 0.005})


class Tests(unittest.TestCase):
    def test_meilleure_information_bat_le_marche(self):
        out = s.scorer(journal(n=3000), iterations=300)  # 100 prévisions ne suffisent pas, voir MODE_EMPLOI § 4
        self.assertLess(out["brier_difference"], 0)
        self.assertGreater(out["gain_moyen_ic95"][0], 0)  # le gain par pari détecte plus tôt que le Brier

    def test_biais_degrade_le_score(self):
        out = s.scorer(journal(biais=0.25), iterations=200)
        self.assertGreater(out["brier_difference"], 0)

    def test_mi_mandat_et_annules_exclus(self):
        j = pd.concat([journal(50), journal(50, mi_mandat=True)])
        j.iloc[0, j.columns.get_loc("annule")] = "oui"
        self.assertEqual(s.scorer(j, iterations=50)["resolues_retenues"], 49)

    def test_paliers(self):
        bon = s.scorer(journal(n=300), iterations=300)
        self.assertFalse(bon["palier1_arret"])
        mauvais = s.scorer(journal(n=300, biais=0.25), iterations=300)
        self.assertTrue(mauvais["palier1_arret"])
        self.assertIsNone(s.scorer(journal(n=60), iterations=50)["palier1_arret"])

    def test_pari_taker(self):
        r = pd.DataFrame({"proba_propre": [0.8, 0.2, 0.505], "milieu": [0.5, 0.5, 0.5], "bid": [0.49] * 3,
                          "ask": [0.51] * 3, "y": [1, 1, 1]})
        g, pris = s.pari(r)
        self.assertEqual(pris.tolist(), [True, True, False])
        self.assertAlmostEqual(g[0], 1 / 0.51 - 1)
        self.assertAlmostEqual(g[1], -1.0)

    def test_journal_vide(self):
        self.assertEqual(s.scorer(s.charger(s.ICI / "JOURNAL_CALIBRATION.csv"))["resolues_retenues"], 0)


if __name__ == "__main__":
    unittest.main()
