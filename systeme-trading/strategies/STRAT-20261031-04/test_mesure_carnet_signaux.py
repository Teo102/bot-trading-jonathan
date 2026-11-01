#!/usr/bin/env python3
"""Tests hors réseau de la formule de glissement et du comptage. Lancer : python test_mesure_carnet_signaux.py

Ils portent sur le calcul seulement. Aucun rendement n'est lu. Le carnet réel est l'instantané conservé
dans resultats/carnet_reel_*.json (marché calme) : il valide l'ordre de grandeur, pas une cascade.
"""
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

import compte_signaux as cs  # noqa: E402
import mesure_carnet_signaux as mc  # noqa: E402

RES = ICI / "resultats"
SIGNAUX = RES / "signaux_sans_rendement_20261031T232359Z.csv"
ANCIEN = RES / "mesure_carnet_signaux_20261031T232517Z.json"


def carnet_uniforme(milieu, profondeur_usd, pas=2000):
    """Carnet vendeur de profondeur égale en dollars par palier, jusqu'à 1 % du milieu."""
    return [(milieu * (1 + 0.01 * (i + 0.5) / pas), profondeur_usd / pas / (milieu * (1 + 0.01 * (i + 0.5) / pas)))
            for i in range(pas)]


class Formule(unittest.TestCase):
    def test_valeur_de_reference(self):
        # 10 000 $ sur 1 667 446 $ à 1 % : 0,003 %, et non 0,30 %.
        self.assertAlmostEqual(mc.glissement_moyen_pct(10_000, 1_667_446), 0.0029986, places=6)

    def test_demi_ecart_additif(self):
        self.assertAlmostEqual(mc.glissement_moyen_pct(10_000, 1_000_000, 0.02), 0.025)

    def test_inverse(self):
        n = mc.ticket_pour_glissement_usd(0.30, 1_000_000, 0.05)
        self.assertAlmostEqual(mc.glissement_moyen_pct(n, 1_000_000, 0.05), 0.30)

    def test_parcours_sur_carnet_uniforme(self):
        # Le parcours d'un carnet uniforme doit redonner la formule, sans facteur 100.
        for n in [10_000, 100_000, 500_000]:
            reel = mc.parcours_carnet_pct(carnet_uniforme(100.0, 1_000_000), 100.0, n)
            self.assertAlmostEqual(reel / mc.glissement_moyen_pct(n, 1_000_000), 1, places=2)

    def test_carnet_trop_court(self):
        self.assertIsNone(mc.parcours_carnet_pct([(100.0, 1.0)], 100.0, 10_000))


class Tranches(unittest.TestCase):
    def test_egale_la_formule_sous_la_premiere_tranche(self):
        tr = [(1, 1_000_000.0), (2, 3_000_000.0)]
        self.assertAlmostEqual(mc.glissement_par_tranches_pct(100_000, tr, 0.02), mc.glissement_moyen_pct(100_000, 1_000_000, 0.02))

    def test_calcul_a_la_main_au_dela_de_un_pct(self):
        # 100 k$ sur 40 k$ à 1 % puis 200 k$ à 2 %. 40 k$ en moyenne à 0,5 %. 60 k$ de 1 % à 1,375 %, en moyenne à 1,1875 %.
        attendu = (40_000 * 0.5 + 60_000 * 1.1875) / 100_000
        self.assertAlmostEqual(mc.glissement_par_tranches_pct(100_000, [(1, 40_000.0), (2, 200_000.0)]), attendu)

    def test_ticket_hors_releve(self):
        self.assertTrue(pd.isna(mc.glissement_par_tranches_pct(300_000, [(1, 40_000.0), (2, 200_000.0)])))

    def test_inverse(self):
        tr = [(1, 40_000.0), (2, 200_000.0), (3, 500_000.0)]
        n = mc.ticket_par_tranches_usd(0.6, tr, 0.02)
        self.assertAlmostEqual(mc.glissement_par_tranches_pct(n, tr, 0.02), 0.6, places=6)

    def test_valeur_non_atteinte(self):
        self.assertEqual(mc.ticket_par_tranches_usd(5.0, [(1, 40_000.0), (2, 200_000.0)]), float("inf"))

    def test_ancienne_sortie_etait_cent_fois_trop_haute(self):
        ancien = json.loads(ANCIEN.read_text())["carnet_par_classe"]["autres"]
        self.assertAlmostEqual(ancien["gliss_entree_pct_10000"] / mc.glissement_moyen_pct(10_000, ancien["ask1_apres_usd_mediane"]), 100, delta=1)


class ReleveGele(unittest.TestCase):
    def serie(self, valeurs):
        return pd.Series(valeurs, index=pd.date_range("2025-10-10", periods=len(valeurs), freq="30s", tz="UTC"), dtype=float)

    def test_cote_gele_exclu(self):
        s = self.serie([5656.0] * 30)
        val, gele = mc.minimum_fenetre(s, mc.releves_vivants(s), s.index[0], s.index[-1])
        self.assertTrue(gele)
        self.assertTrue(pd.isna(val))

    def test_carnet_vivant_garde_son_minimum(self):
        s = self.serie([100.0, 90.0, 36.0, 80.0, 70.0, 60.0])
        self.assertEqual(mc.minimum_fenetre(s, mc.releves_vivants(s), s.index[0], s.index[-1]), (36.0, False))

    def test_fenetre_vide(self):
        s = self.serie([100.0, 90.0])
        val, gele = mc.minimum_fenetre(s, mc.releves_vivants(s), s.index[-1] + pd.Timedelta(hours=1), s.index[-1] + pd.Timedelta(hours=2))
        self.assertFalse(gele)
        self.assertTrue(pd.isna(val))


class CarnetReel(unittest.TestCase):
    def test_ordre_de_grandeur(self):
        fichiers = sorted(RES.glob("carnet_reel_*.json"))
        self.assertTrue(fichiers, "instantané absent, lancer releve_carnet_reel.py")
        for fichier in fichiers:
            actifs = json.loads(fichier.read_text())["actifs"]
            self.assertGreaterEqual(len(actifs), 5)
            for s, e in actifs.items():
                for n in [10_000, 100_000]:
                    reel = mc.parcours_carnet_pct(e["asks_jusqu_a_1pct"], e["milieu"], n)
                    corrige = mc.glissement_moyen_pct(n, e["profondeur_1pct_usd"], e["demi_ecart_pct"])
                    ancien = n / (2 * e["profondeur_1pct_usd"]) * 100
                    self.assertLess(max(reel / corrige, corrige / reel), 4, f"{fichier.name} {s} {n}")
                    self.assertGreater(ancien / reel, 4, f"{fichier.name} {s} {n}")


class Comptage(unittest.TestCase):
    def tableau(self, lignes):
        t = pd.DataFrame(lignes, columns=["symbole", "T", "d_oi", "annule"])
        t["T"] = pd.to_datetime(t["T"], utc=True)
        return t

    def test_une_entree_par_bougie_avant_la_limite(self):
        t = self.tableau([("A", "2024-01-01 00:00", -.06, False), ("B", "2024-01-01 00:00", -.08, False),
                          ("C", "2024-01-01 00:00", -.07, False)])
        _, v = cs.appliquer_regles(t, cs.P)
        self.assertEqual(len(v), 3)
        self.assertEqual(int(v.pris.sum()), 1)
        self.assertEqual(v[v.pris].symbole.iloc[0], "B")  # la plus forte chute passe d'abord

    def test_limite_de_positions(self):
        t = self.tableau([(s, f"2024-01-01 0{i}:00", -.06, False) for i, s in enumerate("ABCD")])
        _, v = cs.appliquer_regles(t, cs.P)
        self.assertEqual(int(v.pris.sum()), 3)

    def test_lectures_du_delai(self):
        t = self.tableau([("A", "2024-01-01 00:00", -.06, True), ("A", "2024-01-01 06:00", -.06, False)])
        self.assertEqual(int(cs.appliquer_regles(t, cs.P)[1].pris.sum()), 0)  # règle comptée : l'annulé relance
        self.assertEqual(int(cs.appliquer_regles(t, cs.P, delai="non_annule")[1].pris.sum()), 1)
        t = self.tableau([("B", "2024-01-01 00:00", -.09, False), ("A", "2024-01-01 00:00", -.06, False),
                          ("A", "2024-01-01 06:00", -.06, False)])
        self.assertEqual(int(cs.appliquer_regles(t, cs.P)[1].query("symbole == 'A'").pris.sum()), 0)
        self.assertEqual(int(cs.appliquer_regles(t, cs.P, delai="entree")[1].query("symbole == 'A'").pris.sum()), 1)

    def test_fichier_publie(self):
        v = pd.read_csv(SIGNAUX, parse_dates=["T"])
        self.assertEqual((len(v), int(v.pris.sum()), v["T"].nunique()), (92, 65, 65))

    def test_equilibre_inchange(self):
        e = mc.equilibre(pd.read_csv(SIGNAUX, parse_dates=["T"]))
        self.assertEqual([e[k]["gain_net_prevu_negatif_ou_nul"] for k in ("couts_x1", "couts_x2", "couts_x4")], [21, 33, 55])
        self.assertEqual(e["couts_x1"]["reussite_equilibre_mediane_si_gain_positif"], 0.809)

    def test_stress_complet_et_frais_a_l_objectif(self):
        # Coûts ×2 de validation-edge § 4.5 : frais et glissement doublés. Frais preneur compté à l'objectif, borné ici.
        e = mc.equilibre(pd.read_csv(SIGNAUX, parse_dates=["T"]))
        self.assertEqual(e["frais_et_glissement_x2"]["gain_net_prevu_negatif_ou_nul"], 36)
        self.assertEqual(e["couts_x1_objectif_sans_frais"]["gain_net_prevu_negatif_ou_nul"], 18)
        self.assertEqual(e["frais_seuls"]["reussite_equilibre_mediane_si_gain_positif"], 0.769)


if __name__ == "__main__":
    unittest.main()
