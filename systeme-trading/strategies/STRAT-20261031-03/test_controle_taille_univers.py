"""Test hors ligne de controle_taille_univers.py. Exécution : python -B test_controle_taille_univers.py"""
import sys

sys.dont_write_bytecode = True
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import controle_taille_univers as c  # noqa: E402
import donnees_binance as db  # noqa: E402
import run_essai as re_  # noqa: E402
import test_donnees_et_essai as td  # noqa: E402

BLOCS = [("developpement", "2021-01-04", "2021-03-29"), ("validation", "2021-04-05", "2021-06-28")]


class Taille(unittest.TestCase):
    def test_comptes_coherents_sans_prix(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            td.faux_vision(tmp, n_sym=40, jours=440, debut="2020-05-01")
            src = db.VisionLocale(tmp)
            vol = c.volumes(src, db.symboles_usdt(src), pd.Timestamp("2020-05-01"), pd.Timestamp("2021-06-28"))
            self.assertEqual(vol.index.max(), pd.Timestamp("2021-06-27"))  # verrou : rien du lundi évalué ni après
            p = re_.params_depuis(re_.charger_config())
            df = c.mesurer(vol, p, frozenset(), BLOCS)
            self.assertEqual(len(df), 26)
            self.assertTrue((df["sans_seuil"] <= 30).all())
            for r in ("absolu_50M", "relatif_20pct", "indexe_marche"):
                self.assertTrue((df[r] <= df["sans_seuil"]).all(), r)
            syn = c.synthese(df, BLOCS)
            self.assertEqual(len(syn), 8)
            self.assertIn("| developpement |", c.rapport(df, syn, {"horodatage": "x", "symboles": 41, "statut": "test"}))
            # diagnostic : un trou d'archive de 3 jours fait perdre le nom en mode strict, pas avec 7 jours tolérés
            vol2 = vol.copy()
            vol2.loc[pd.Timestamp("2021-02-10"):pd.Timestamp("2021-02-12"), "S03USDT"] = float("nan")
            dg = c.diagnostic(vol2, p, pd.Timestamp("2021-02-08"), pd.Timestamp("2021-02-15"))
            self.assertIn("S03USDT", dg["symbole"].tolist())
            self.assertEqual(int(dg.set_index("symbole").loc["S03USDT", "jours_absents"]), 3)
            import moteur_xsmom as m
            p7 = m.Params(**{**p.__dict__, "trou_max_jours": 7})
            self.assertNotIn("S03USDT", c.diagnostic(vol2, p7, pd.Timestamp("2021-02-08"), pd.Timestamp("2021-02-15"))["symbole"].tolist() if len(c.diagnostic(vol2, p7, pd.Timestamp("2021-02-08"), pd.Timestamp("2021-02-15"))) else [])
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
