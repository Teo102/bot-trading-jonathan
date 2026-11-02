"""Tests synthétiques de STRAT-20261102-06 (fiche § 9). Aucune donnée de marché, aucun réseau.
Exécution : python -B test_strat06.py"""
import sys

sys.dont_write_bytecode = True
import copy
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import moteur_xsmom as m  # noqa: E402
import univers_cotations as uc  # noqa: E402
import donnees_binance as db  # noqa: E402
import run_essai06 as r6  # noqa: E402
import test_moteur_synthetique as ts  # noqa: E402
import test_donnees_et_essai as td  # noqa: E402

DEBUT = pd.Timestamp("2022-01-01")
PC = uc.ParamsCotation(liquidite_min=0.0)  # volumes synthétiques faibles


def marche_cotations(graine=1, n=30, jours=400, derive_jeunes=0.0, financement_jeunes=0.0, vieux=6):
    """`vieux` symboles actifs dès le début (anciens) ; les autres cotés à des dates étalées.
    derive_jeunes : dérive horaire ajoutée pendant les 60 premiers jours de cotation (négative = baisse)."""
    rng = np.random.default_rng(graine)
    j, h, f = ts.marche(n_sym=n, jours=jours, graine=graine)
    noms = [f"S{i:02d}" for i in range(n)]
    cotation = {s: (DEBUT if i < vieux else DEBUT + pd.Timedelta(days=int(rng.integers(20, jours - 80)))) for i, s in enumerate(noms)}
    lr = np.log(h["close"]).diff().fillna(0.0)
    for s, L in cotation.items():
        jeune = (lr.index >= L) & (lr.index < L + pd.Timedelta(days=60))
        lr.loc[jeune, s] += derive_jeunes
    close = 100 * np.exp(lr.cumsum())
    open_ = close.shift(1).fillna(100.0)
    h = {"open": open_, "close": close, "mark_high": np.maximum(open_, close) * 1.002, "mark_low": np.minimum(open_, close) * 0.998}
    j = {"close": close.resample("D").last(), "volume": j["volume"].copy()}
    for s, L in cotation.items():
        if L > DEBUT:
            j["volume"].loc[j["volume"].index < L, s] = 0.0
            j["close"].loc[j["close"].index < L, s] = np.nan
            for k in h:
                h[k].loc[h[k].index < L, s] = np.nan
            jeune = (f.index >= L) & (f.index < L + pd.Timedelta(days=60))
            f.loc[jeune, s] = financement_jeunes
    return j, h, f, cotation


class Univers(unittest.TestCase):
    def test_age_sans_anticipation_et_troncature(self):
        j, h, f, cot = marche_cotations(3)
        ecarts = 0
        for t in ts.lundis(j, depuis=DEBUT + pd.Timedelta(days=30)):
            plein = uc.eligibles(j, t, PC, DEBUT)
            tron = uc.eligibles({k: v.loc[v.index < t] for k, v in j.items()}, t, PC, DEBUT)
            ecarts += int(plein != tron)
            for s, _ in plein:
                self.assertTrue(7 <= (t - cot[s]).days <= 60)
        self.assertEqual(ecarts, 0)

    def test_anciens_jamais_nouveaux(self):
        j, h, f, cot = marche_cotations(4)
        for t in ts.lundis(j, depuis=DEBUT + pd.Timedelta(days=8)):
            self.assertFalse({s for s, _ in uc.eligibles(j, t, PC, DEBUT)} & {f"S{i:02d}" for i in range(6)})

    def test_liste_close_et_multiplicateur(self):
        vol = pd.DataFrame(1e8, index=pd.date_range(DEBUT, periods=200), columns=["XUSDT", "1000XUSDT", "NEWUSDT", "BTC"])
        vol.loc[vol.index < DEBUT + pd.Timedelta(days=50), "XUSDT"] = 0
        vol.loc[vol.index < DEBUT + pd.Timedelta(days=100), ["1000XUSDT", "NEWUSDT"]] = 0
        t = DEBUT + pd.Timedelta(days=120)
        while t.weekday() != 0:
            t += pd.Timedelta(days=1)
        noms = [s for s, _ in uc.eligibles({"volume": vol}, t, uc.ParamsCotation(liquidite_min=0), DEBUT)]
        self.assertIn("NEWUSDT", noms)
        self.assertNotIn("1000XUSDT", noms)  # X déjà coté avant
        noms2 = [s for s, _ in uc.eligibles({"volume": vol}, t, uc.ParamsCotation(liquidite_min=0, faux_nouveaux=frozenset({"NEWUSDT"})), DEBUT)]
        self.assertNotIn("NEWUSDT", noms2)

    def test_liquidite_depuis_la_cotation(self):
        vol = pd.DataFrame(0.0, index=pd.date_range(DEBUT, periods=200), columns=["AUSDT"])
        L = DEBUT + pd.Timedelta(days=100)
        vol.loc[vol.index >= L, "AUSDT"] = 25e6
        t = L + pd.Timedelta(days=10)
        while t.weekday() != 0:
            t += pd.Timedelta(days=1)
        self.assertEqual(len(uc.eligibles({"volume": vol}, t, uc.ParamsCotation(), DEBUT)), 1)  # médiane sur les jours cotés seuls
        self.assertEqual(len(uc.eligibles({"volume": vol}, t, uc.ParamsCotation(liquidite_min=30e6), DEBUT)), 0)

    def test_memecoins_exclus_en_variante(self):
        vol = pd.DataFrame(0.0, index=pd.date_range(DEBUT, periods=200), columns=["1000PEPEUSDT"])
        vol.loc[vol.index >= DEBUT + pd.Timedelta(days=100), "1000PEPEUSDT"] = 1e8
        t = pd.Timestamp("2022-04-25")
        self.assertEqual(len(uc.eligibles({"volume": vol}, t, uc.ParamsCotation(), DEBUT)), 1)
        self.assertEqual(len(uc.eligibles({"volume": vol}, t, uc.ParamsCotation(exclus=frozenset({"PEPE"})), DEBUT)), 0)


class Cible(unittest.TestCase):
    def test_couverture_et_inverse(self):
        j, h, f, cot = marche_cotations(5)
        t = [x for x in ts.lundis(j) if uc.eligibles(j, x, PC, DEBUT)][0]
        poids, n = uc.fabrique_cible(PC, DEBUT)(j, t, None)
        shorts = [s for s, w in poids.items() if w < 0]
        self.assertEqual(len(shorts), n)
        self.assertAlmostEqual(poids["BTC"], n)
        inv, _ = uc.fabrique_cible(uc.ParamsCotation(liquidite_min=0, inverse=True), DEBUT)(j, t, None)
        self.assertAlmostEqual(inv["BTC"], -n)
        sans, _ = uc.fabrique_cible(uc.ParamsCotation(liquidite_min=0, couverture=False), DEBUT)(j, t, None)
        self.assertNotIn("BTC", sans)

    def test_semaine_vide(self):
        j, h, f, cot = marche_cotations(6)
        lun = ts.lundis(j, depuis=DEBUT + pd.Timedelta(days=1))[:2]  # aucune cotation de plus de 7 jours si tôt
        sem, lig = m.backtest(j, h, f, lun, m.Params(stop=None), notionnel=1 / 12, fonction_cible=uc.fabrique_cible(PC, DEBUT))
        self.assertEqual(sem.net.iloc[0], 0.0)
        self.assertEqual(len(lig), 0)


class Moteur(unittest.TestCase):
    P0 = m.Params(frais=0.0, glissement=0.0, glissement_stop=0.0)

    def run_(self, j, h, f, pc, p=None):
        return m.backtest(j, h, f, ts.lundis(j), p or self.P0, notionnel=1 / 12, fonction_cible=uc.fabrique_cible(pc, DEBUT))

    def test_strat03_inchangee(self):
        j, h, f = ts.marche(graine=7)
        a, _ = m.backtest(j, h, f, ts.lundis(j)[:6], m.Params())
        b, _ = m.backtest(j, h, f, ts.lundis(j)[:6], m.Params(), fonction_cible=None)
        pd.testing.assert_frame_equal(a, b)

    def test_notionnel_de_la_couverture(self):
        j, h, f, cot = marche_cotations(8)
        sem, lig = self.run_(j, h, f, PC)
        x = lig[(lig.symbole == "BTC") & (lig.statut == "semaine")].iloc[0]
        n = len(sem.loc[sem.lundi == x.lundi, "shorts"].iloc[0].split(","))
        self.assertAlmostEqual(abs(x.valeur_fin) / (x.sortie / x.entree), n / 12, places=9)

    def test_financement_negatif_paye_par_le_short(self):
        j, h, f, cot = marche_cotations(9, financement_jeunes=-0.001)
        sem, lig = self.run_(j, h, f, PC)
        sh = lig[(lig.sens == -1) & (lig.statut != "absent")]
        self.assertLess(sh.financement.sum(), 0)

    def test_derive_plantee_detectee_et_inverse_perd(self):
        j, h, f, cot = marche_cotations(10, derive_jeunes=-0.0006)
        base, _ = self.run_(j, h, f, PC)
        inv, _ = self.run_(j, h, f, uc.ParamsCotation(liquidite_min=0, inverse=True))
        self.assertGreater(base.net.sum(), 0)
        self.assertLess(inv.net.sum(), 0)

    def test_aucun_edge_fantome(self):
        moy = []
        for g in range(12):
            j, h, f, cot = marche_cotations(300 + g)
            s, _ = self.run_(j, h, f, PC)
            s = s[s.longs != ""]
            if len(s):
                moy.append(s.net.mean())
        moy = np.array(moy)
        z = moy.mean() / (moy.std(ddof=1) / np.sqrt(len(moy)))
        self.assertLess(abs(z), 3.0)


class Lanceur(unittest.TestCase):
    def test_refus_tant_que_non_figee(self):
        c6, c3 = r6.charger_configs()
        self.assertEqual(c6["statut_regles"], "figees")
        c6 = copy.deepcopy(c6)
        c6["statut_regles"] = "proposees"
        with self.assertRaises(r6.r3.Refus):
            r6.executer("E01", None, c6, c3)

    def test_refus_sans_liste_non_crypto(self):
        c6, c3 = r6.charger_configs()
        c6 = copy.deepcopy(c6)
        c6["statut_regles"] = "figees"
        if not (r6.ICI / "exclusions_non_coin.json").exists():
            with self.assertRaises(r6.r3.Refus):
                r6.executer("E01", None, c6, c3)

    def test_faux_nouveaux_charges(self):
        c6, c3 = r6.charger_configs()
        pc = r6.params_cotation(c6, c3)
        for s in ("RENDERUSDT", "1000LUNCUSDT", "FRAXUSDT", "MANTRAUSDT", "DODOXUSDT"):
            self.assertIn(s, pc.faux_nouveaux)

    def test_bout_en_bout_sur_faux_vision(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            vision = tmp / "v"
            td.faux_vision(vision, n_sym=10, jours=420, debut="2020-06-01")
            # deux cotations tardives : leurs archives avant la cotation sont retirées
            for s, mois_debut in (("S08USDT", "2021-02"), ("S09USDT", "2021-03")):
                for fichier in vision.rglob(f"{s}-*.zip"):
                    mo = re.search(r"(\d{4}-\d{2})", fichier.name).group(1)
                    if mo < mois_debut:
                        fichier.unlink()
                        Path(str(fichier) + ".CHECKSUM").unlink()
            c6, c3 = r6.charger_configs()
            c6, c3 = copy.deepcopy(c6), copy.deepcopy(c3)
            c6["statut_regles"] = "figees"
            c6["univers"]["liquidite_min_usdt"] = 0
            c6["blocs"] = {"developpement": {"essai": "E01", "premier_lundi": "2021-02-01", "dernier_lundi": "2021-06-28",
                                             "fin_donnees_prix": "2021-07-05T02:00:00Z"}}
            c6["bootstrap"]["tirages"] = 200
            reg = tmp / "registre.csv"
            r_ = pd.read_csv(r6.REGISTRE, dtype=str, keep_default_na=False)
            r_["date"] = ""  # copie de test : les essais réels déjà consommés ne bloquent pas le test
            r_.to_csv(reg, index=False)
            out = r6.executer("E01", db.VisionLocale(vision), c6, c3, reg, tmp / "o", debut_donnees=pd.Timestamp("2020-06-01"), exiger_non_coin=False)
            mt = out["metriques"]
            self.assertEqual(mt["semaines"], 22)
            self.assertGreater(mt["lignes"], 0)
            self.assertLess(mt["semaines_vides"], 22)
            self.assertIn("alpha_positif", mt["portes_internes"])
            with self.assertRaises(r6.r3.Refus):
                r6.executer("E01", db.VisionLocale(vision), c6, c3, reg, tmp / "o2", debut_donnees=pd.Timestamp("2020-06-01"), exiger_non_coin=False)
        finally:
            shutil.rmtree(tmp)

    def test_concentration_exclut_couverture_btc(self):
        """Vérifie la règle de concentration selon § 3, § 7 et L11 :
        - une couverture à 40 % du gain avec des shorts sous 25 % : la porte est franchie
        - un short à 30 % : la porte échoue
        """
        # Cas 1 : couverture BTC à 40 % du gain, 3 shorts sous 25 % (chacun 20 %)
        lig1 = pd.DataFrame([
            {"symbole": "BTC", "statut": "semaine", "pnl_prix": 0.40, "financement": 0.0},
            {"symbole": "ALT1", "statut": "semaine", "pnl_prix": 0.20, "financement": 0.0},
            {"symbole": "ALT2", "statut": "semaine", "pnl_prix": 0.20, "financement": 0.0},
            {"symbole": "ALT3", "statut": "semaine", "pnl_prix": 0.20, "financement": 0.0},
        ])
        part1, nom1 = r6.calculer_concentration_noms(lig1, gain_total=1.0, facteur="BTC")
        self.assertAlmostEqual(part1, 0.20)
        self.assertIn(nom1, ["ALT1", "ALT2", "ALT3"])
        pi1 = r6.portes_internes({
            "rendement_net_total_brut100": 1.0, "alpha_hebdo_residuel": 0.01,
            "part_max_nom_du_gain": part1, "part_max_mois_du_gain": 0.30,
            "drawdown_max_brut100": 0.10, "semaines_vides": 0, "semaines": 10,
        })
        self.assertTrue(pi1["concentration_nom_ok"])

        # Cas 2 : un short à 30 % du gain net total (> 25 %) : la porte échoue
        lig2 = pd.DataFrame([
            {"symbole": "BTC", "statut": "semaine", "pnl_prix": 0.20, "financement": 0.0},
            {"symbole": "ALT_DOMINANT", "statut": "semaine", "pnl_prix": 0.30, "financement": 0.0},
            {"symbole": "ALT2", "statut": "semaine", "pnl_prix": 0.25, "financement": 0.0},
            {"symbole": "ALT3", "statut": "semaine", "pnl_prix": 0.25, "financement": 0.0},
        ])
        part2, nom2 = r6.calculer_concentration_noms(lig2, gain_total=1.0, facteur="BTC")
        self.assertEqual(nom2, "ALT_DOMINANT")
        self.assertAlmostEqual(part2, 0.30)
        pi2 = r6.portes_internes({
            "rendement_net_total_brut100": 1.0, "alpha_hebdo_residuel": 0.01,
            "part_max_nom_du_gain": part2, "part_max_mois_du_gain": 0.30,
            "drawdown_max_brut100": 0.10, "semaines_vides": 0, "semaines": 10,
        })
        self.assertFalse(pi2["concentration_nom_ok"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
