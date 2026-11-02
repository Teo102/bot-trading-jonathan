"""Tests synthétiques de STRAT-20261102-05 (fiche § 8). Aucune donnée de marché, aucun réseau.
Exécution : python -B test_strat05.py"""
import sys

sys.dont_write_bytecode = True
import copy
import hashlib
import io
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import moteur_xsmom as m  # noqa: E402
import signal_encombrement as se  # noqa: E402
import donnees_metrics as dm  # noqa: E402
import donnees_binance as db  # noqa: E402
import run_essai05 as r5  # noqa: E402
import test_moteur_synthetique as ts  # noqa: E402
import test_donnees_et_essai as td  # noqa: E402

T = pd.Timestamp("2022-06-06")  # lundi


def financement_constant(noms, debut, fin, freq, taux):
    idx = pd.date_range(debut, fin, freq=freq)
    return pd.DataFrame({s: taux[s] for s in noms}, index=idx)


class Mesures(unittest.TestCase):
    def test_intervalles_mixtes(self):
        """0,03 % par jour en 3 × 8 h, puis en 24 × 1 h : même taux journalier."""
        a = pd.DataFrame({"A": 0.0001}, index=pd.date_range(T - pd.Timedelta(days=7), T - pd.Timedelta(days=4, hours=1), freq="8h"))
        b = pd.DataFrame({"A": 0.0003 / 24}, index=pd.date_range(T - pd.Timedelta(days=4), T - pd.Timedelta(hours=1), freq="h"))
        f = pd.concat([a, b])
        self.assertAlmostEqual(se.taux_journalier(f, T, ["A"], 7)["A"], 0.0003)

    def test_jour_sans_evenement_exclut(self):
        f = pd.DataFrame({"A": 0.0001}, index=pd.date_range(T - pd.Timedelta(days=7), T - pd.Timedelta(hours=8), freq="8h"))
        f = f[f.index.normalize() != (T - pd.Timedelta(days=3)).normalize()]
        self.assertNotIn("A", se.taux_journalier(f, T, ["A"], 7).index)

    def test_evenement_du_lundi_ignore(self):
        f = pd.DataFrame({"A": 0.0001}, index=pd.date_range(T - pd.Timedelta(days=7), T, freq="8h"))
        f.loc[T, "A"] = 1.0  # événement du lundi 00:00 : postérieur au signal
        self.assertAlmostEqual(se.taux_journalier(f, T, ["A"], 7)["A"], 0.0003)

    def test_variation_oi_et_manque(self):
        oi = pd.DataFrame({"A": [100.0, 150.0], "B": [100.0, np.nan]},
                          index=[(T - pd.Timedelta(days=8)).normalize(), (T - pd.Timedelta(days=1)).normalize()])
        o = se.variation_oi(oi, T, ["A", "B"], 7)
        self.assertAlmostEqual(o["A"], np.log(1.5))
        self.assertNotIn("B", o.index)

    def test_z_borne(self):
        x = pd.Series([0.0] * 20 + [100.0], index=[f"S{i}" for i in range(21)])
        self.assertLessEqual(se.z_borne(x, 3).max(), 3.0)

    def test_sens_short_des_encombres(self):
        noms = [f"S{i}" for i in range(8)]
        f = financement_constant(noms, T - pd.Timedelta(days=10), T, "8h", {s: 0.0001 * i for i, s in enumerate(noms)})
        oi = pd.DataFrame(1.0, index=pd.date_range(T - pd.Timedelta(days=20), T - pd.Timedelta(days=1)), columns=noms)
        sc = se.fabrique_scores(f, oi, se.ParamsScore())(None, T, noms, None)
        lo, sh = m.selection(sc, 3)
        self.assertEqual(sh, ["S7", "S6", "S5"])  # financement le plus haut : short
        self.assertEqual(lo, ["S0", "S1", "S2"])
        sc_inv = se.fabrique_scores(f, oi, se.ParamsScore(inverse=True))(None, T, noms, None)
        self.assertEqual(m.selection(sc_inv, 3)[0], ["S7", "S6", "S5"])


def marche_encombree(graine, lien, n=36, jours=330):
    """Financement persistant par nom ; dérive de prix = −lien × rang du financement (lien = 0 : aucun edge)."""
    rng = np.random.default_rng(graine)
    niveau = rng.normal(0, 1, n)
    drift = -lien * (niveau - niveau.mean()) * 0.0004
    j, h, f = ts.marche(n_sym=n, jours=jours, graine=graine, drift_resid=drift)
    noms = [f"S{i:02d}" for i in range(n)]
    f = f.copy()
    for i, s in enumerate(noms):
        f[s] = 1e-7 * niveau[i]  # minuscule : le gain éventuel vient du prix, pas du financement encaissé
    oi = pd.DataFrame(1.0, index=j["close"].index, columns=noms + ["BTC"])
    return j, h, f, oi


class Moteur(unittest.TestCase):
    P0 = m.Params(frais=0.0, glissement=0.0, glissement_stop=0.0)
    PS = se.ParamsScore(poids_o=0.0)  # financement seul pour les cas plantés (OI constant)

    def lancer(self, j, h, f, oi, ps):
        return m.backtest(j, h, f, ts.lundis(j), self.P0, fonction_scores=se.fabrique_scores(f, oi, ps))

    def test_troncature(self):
        j, h, f, oi = marche_encombree(3, 1.0)
        fs = se.fabrique_scores(f, oi, se.ParamsScore())
        ecarts = 0
        for t in ts.lundis(j)[::3]:
            plein = fs(None, t, [f"S{i:02d}" for i in range(36)], None)
            tron = se.fabrique_scores(f.loc[f.index < t], oi.loc[oi.index < t], se.ParamsScore())(None, t, [f"S{i:02d}" for i in range(36)], None)
            ecarts += int(not plein.sort_index().equals(tron.sort_index()))
        self.assertEqual(ecarts, 0)

    def test_strat03_inchangee_par_defaut(self):
        j, h, f = ts.marche(graine=5)
        a, _ = m.backtest(j, h, f, ts.lundis(j)[:6], m.Params())
        b, _ = m.backtest(j, h, f, ts.lundis(j)[:6], m.Params(), fonction_scores=m.scores)
        pd.testing.assert_frame_equal(a, b)

    def test_edge_plante_detecte_et_inverse_perd(self):
        j, h, f, oi = marche_encombree(11, 1.0)
        base, _ = self.lancer(j, h, f, oi, self.PS)
        inv, _ = self.lancer(j, h, f, oi, se.ParamsScore(poids_o=0.0, inverse=True))
        self.assertGreater(base.pnl_prix.sum(), 0)
        self.assertLess(inv.pnl_prix.sum(), 0)
        self.assertLess(abs(base.financement.sum()), 0.01)

    def test_aucun_edge_fantome(self):
        moy = []
        for g in range(12):
            j, h, f, oi = marche_encombree(200 + g, 0.0)
            s, _ = self.lancer(j, h, f, oi, self.PS)
            moy.append(s.net.mean())
        moy = np.array(moy)
        z = moy.mean() / (moy.std(ddof=1) / np.sqrt(len(moy)))
        self.assertLess(abs(z), 3.0)


def zipper_csv(df):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x.csv", df.to_csv(index=False))
    return b.getvalue()


def poser_metrics(racine, sym, jours, valeur, piege_apres=None):
    for d in jours:
        heures = pd.date_range(d, d + pd.Timedelta(hours=23, minutes=55), freq="5min")
        v = [valeur(d)] * len(heures)
        v[-1] = valeur(d) * 1.01  # dernière ligne du jour, celle qui doit être retenue
        if piege_apres is not None:
            v = [1e15 if hh >= piege_apres else x for hh, x in zip(heures, v)]
        df = pd.DataFrame({"create_time": heures.strftime("%Y-%m-%d %H:%M:%S"), "symbol": sym,
                           "sum_open_interest": 1.0, "sum_open_interest_value": v})
        td.poser(racine, f"{db.RACINE_J}/" + dm.CHEMIN.format(s=sym, d=d.date().isoformat()), zipper_csv(df))


class Metrics(unittest.TestCase):
    def test_lecture_derniere_ligne_et_verrou(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            jours = [pd.Timestamp("2022-06-04"), pd.Timestamp("2022-06-05")]
            poser_metrics(tmp, "AAAUSDT", jours, lambda d: 1000.0, piege_apres=pd.Timestamp("2022-06-05 12:00"))
            q = {}
            oi = dm.charger_oi(db.VisionLocale(tmp), {"AAAUSDT": set(jours) | {pd.Timestamp("2022-06-03")}},
                               pd.Timestamp("2022-06-05 12:00"), journal=q)
            self.assertAlmostEqual(oi.loc[pd.Timestamp("2022-06-04"), "AAAUSDT"], 1010.0)
            self.assertLess(oi.loc[pd.Timestamp("2022-06-05"), "AAAUSDT"], 1e6)  # rien d'après la fin
            self.assertEqual(q["oi_jours_introuvables"], 1)
        finally:
            shutil.rmtree(tmp)

    def test_jours_requis(self):
        r = dm.jours_requis({T: ["A"]}, (7,))
        self.assertEqual(r["A"], {pd.Timestamp("2022-06-05"), pd.Timestamp("2022-05-29")})


class Lanceur(unittest.TestCase):
    def test_refus_tant_que_non_figee(self):
        c5, c3 = r5.charger_configs()
        self.assertEqual(c5["statut_regles"], "figees")  # gel du 02/11/2026
        c5 = copy.deepcopy(c5)
        c5["statut_regles"] = "proposees"
        with self.assertRaises(r5.r3.Refus):
            r5.executer("E01", None, c5, c3)

    def test_bout_en_bout_sur_faux_vision(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            vision = tmp / "v"
            td.faux_vision(vision, n_sym=14, jours=420, debut="2020-06-01")
            idx = pd.date_range("2020-06-01", periods=420, freq="D")
            for i in range(14):
                poser_metrics(vision, f"S{i:02d}USDT", idx[-150:], lambda d, i=i: 1e6 * (1 + 0.01 * i) ** ((d - idx[0]).days / 30))
            c5, c3 = r5.charger_configs()
            c5, c3 = copy.deepcopy(c5), copy.deepcopy(c3)
            c5["statut_regles"] = "figees"
            c5["blocs"] = {"developpement": {"essai": "E01", "premier_lundi": "2021-04-05", "dernier_lundi": "2021-06-28",
                                             "fin_donnees_prix": "2021-07-05T02:00:00Z"}}
            c5["bootstrap"]["tirages"] = 300
            c3["params_base"].update(volume_min=0, taille_univers=10)
            reg = tmp / "registre.csv"
            r_ = pd.read_csv(r5.REGISTRE, dtype=str, keep_default_na=False)
            r_["date"] = ""  # copie de test : les essais réels déjà consommés ne bloquent pas le test
            r_.to_csv(reg, index=False)
            out = r5.executer("E01", db.VisionLocale(vision), c5, c3, reg, tmp / "o")
            mt = out["metriques"]
            self.assertEqual(mt["semaines"], 13)
            self.assertGreater(mt["lignes"], 0)
            self.assertIn("prix_net_de_couts", mt["portes_internes"])
            self.assertTrue((tmp / "o" / "E01_metriques.md").exists())
            with self.assertRaises(r5.r3.Refus):
                r5.executer("E01", db.VisionLocale(vision), c5, c3, reg, tmp / "o2")
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=1)
