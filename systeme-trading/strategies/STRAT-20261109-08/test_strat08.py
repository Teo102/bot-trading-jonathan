"""Tests synthétiques de STRAT-20261109-08 (détection, flux, compact, comptage). Aucun réseau.
Exécution : python3 -B test_strat08.py"""
import sys

sys.dont_write_bytecode = True
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
import controle_cascades as cc  # noqa: E402
import detection_cascades as dc  # noqa: E402
import donnees_1m as d1  # noqa: E402


def k1_plat(debut="2022-03-01", jours=2, prix=100.0, vol=1000.0):
    idx = pd.date_range(debut, periods=jours * 1440, freq="min")
    return pd.DataFrame({"open": prix, "high": prix, "low": prix, "close": prix, "volume_usdt": vol}, index=idx)


def oi_plat(k1, niveau=1000.0):
    return pd.Series(niveau, index=pd.date_range(k1.index.min(), k1.index.max() + pd.Timedelta(minutes=1), freq="5min"))


def cascade(k1, oi, t0="2022-03-01 10:00", minutes=10, chute=0.06, baisse_oi=0.05):
    k1, oi = k1.copy(), oi.copy()
    t0 = pd.Timestamp(t0)
    for i in range(minutes):
        p = 100 * (1 - chute * (i + 1) / minutes)
        k1.loc[t0 + pd.Timedelta(minutes=i), ["low", "close"]] = p
    apres = k1.index >= t0 + pd.Timedelta(minutes=minutes)
    k1.loc[apres, ["open", "high", "low", "close"]] = 100 * (1 - chute)
    if baisse_oi:
        oi[oi.index >= t0 + pd.Timedelta(minutes=minutes)] = 1000 * (1 - baisse_oi)
    return k1, oi


class Detection(unittest.TestCase):
    def test_cascade_detectee_au_bon_instant(self):
        k, o = cascade(k1_plat(), oi_plat(k1_plat()))
        c = dc.candidats(k, o)
        self.assertIn(pd.Timestamp("2022-03-01 10:10"), set(c["t"]))
        r = c[c["t"] == pd.Timestamp("2022-03-01 10:10")].iloc[0]
        self.assertAlmostEqual(r.rendement_15m, -0.06, places=6)
        self.assertAlmostEqual(r.var_oi_15m, -0.05, places=6)
        self.assertFalse((c["t"] < pd.Timestamp("2022-03-01 10:05")).any())  # rien avant la chute

    def test_sans_baisse_oi_pas_de_cascade(self):
        k, o = cascade(k1_plat(), oi_plat(k1_plat()), baisse_oi=0)
        self.assertTrue(dc.candidats(k, o).empty)

    def test_baisse_lente_pas_de_cascade(self):
        k, o = cascade(k1_plat(), oi_plat(k1_plat()), minutes=90, chute=0.06)
        self.assertTrue(dc.candidats(k, o, x_min=0.03).empty)  # 15 min de baisse lente < 3 %

    def test_sans_anticipation(self):
        k, o = cascade(k1_plat(), oi_plat(k1_plat()))
        a = dc.candidats(k, o)
        t = pd.Timestamp("2022-03-01 10:10")
        k2, o2 = k.copy(), o.copy()
        k2.loc[k2.index >= t, ["open", "high", "low", "close"]] = 1.0  # l'avenir change radicalement
        o2[o2.index > t] = 1.0
        b = dc.candidats(k2, o2)
        ra, rb = a[a["t"] == t].iloc[0], b[b["t"] == t].iloc[0]
        self.assertAlmostEqual(ra.rendement_15m, rb.rendement_15m)
        self.assertAlmostEqual(ra.var_oi_15m, rb.var_oi_15m)
        self.assertAlmostEqual(ra.volume_15m, rb.volume_15m)

    def test_filtrer_et_dedoublonner(self):
        c = pd.DataFrame({"symbole": ["A", "A", "A", "B"], "t": pd.to_datetime(["2022-01-01 10:00", "2022-01-01 10:05", "2022-01-01 15:00", "2022-01-01 10:05"]),
                          "rendement_15m": [-0.05, -0.05, -0.05, -0.035], "var_oi_15m": [-0.04, -0.04, -0.04, -0.04], "volume_15m": 1.0})
        f = dc.filtrer(c, 0.04, 0.03)
        self.assertEqual(len(f), 3)  # B sous X
        d = dc.dedoublonner(f, pd.Timedelta(hours=4))
        self.assertEqual(list(d["t"]), list(pd.to_datetime(["2022-01-01 10:00", "2022-01-01 15:00"])))

    def test_fenetres_union(self):
        iv = dc.fenetres_a_garder([pd.Timestamp("2022-01-01 10:00"), pd.Timestamp("2022-01-01 11:00")])
        self.assertEqual(len(iv), 2)  # autour des candidats (fusionnés) et autour des placebos (fusionnés)
        self.assertEqual(iv[0][0], pd.Timestamp("2022-01-01 09:40"))
        self.assertEqual(iv[1][0], pd.Timestamp("2022-01-02 09:40"))


class Donnees(unittest.TestCase):
    def test_compact_aller_retour(self):
        k = k1_plat()
        comp = d1.compacter(k, [(pd.Timestamp("2022-03-01 10:00"), pd.Timestamp("2022-03-01 10:09"))])
        self.assertEqual(len(comp["minute"]), 10)
        r = d1.relire_compact(comp)
        self.assertEqual(r.index[0], pd.Timestamp("2022-03-01 10:00"))
        self.assertAlmostEqual(r["close"].iloc[0], 100.0)

    def test_lecture_ephemere(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            class Faux:
                cache = tmp
                def lire(self, cle):
                    p = tmp / cle; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"x")
                    Path(str(p) + ".CHECKSUM").write_text("y")
                    return b"x"
            (tmp / "ancien").parent.mkdir(exist_ok=True); (tmp / "ancien").write_bytes(b"a")
            e = d1.LectureEphemere(Faux())
            self.assertEqual(e.lire("a/b.zip"), b"x")
            self.assertFalse((tmp / "a/b.zip").exists())
            self.assertFalse((tmp / "a/b.zip.CHECKSUM").exists())
            e.lire("ancien")
            self.assertTrue((tmp / "ancien").exists())  # déjà en cache avant l'appel : conservé
        finally:
            shutil.rmtree(tmp)

    def test_mois_eligibles(self):
        idx = pd.date_range("2021-01-01", "2021-06-30", freq="D")
        v = pd.DataFrame({"AUSDT": 30e6, "BUSDT": 5e6, "CUSDT": 0.0}, index=idx)
        v.loc[v.index < "2021-03-01", "CUSDT"] = 0.0
        v.loc[v.index >= "2021-03-01", "CUSDT"] = 50e6
        me = d1.mois_eligibles(v, age_min_j=30)   # règle d'avant le 13/11/2026
        self.assertNotIn("BUSDT", me)
        self.assertEqual(me["AUSDT"][0], "2021-02")  # âge ≥ 31 j depuis le 01/01 : février
        self.assertTrue(all(m >= "2021-04" for m in me["CUSDT"]))  # coté le 01/03 : âge de 30 j atteint en avril
        self.assertNotIn("CUSDT", d1.mois_eligibles(v, exclus={"CUSDT"}))
        # règle courante, âge ≥ 61 jours la veille (62 jours d'écart) : A coté le 01/01 devient éligible le 04/03, C coté le 01/03 le 02/05
        self.assertEqual(d1.AGE_MIN_J, 61)
        me61 = d1.mois_eligibles(v)
        self.assertEqual(me61["AUSDT"][0], "2021-03")
        self.assertEqual(me61["CUSDT"][0], "2021-05")
        el = d1.jours_eligibles(v, "AUSDT")
        self.assertFalse(el[pd.Timestamp("2021-03-03")])
        self.assertTrue(el[pd.Timestamp("2021-03-04")])

    def test_refiltrage_sans_telechargement(self):
        idx = pd.date_range("2021-01-01", "2021-06-30", freq="D")
        v = pd.DataFrame({"AUSDT": 30e6, "CUSDT": 0.0}, index=idx)
        v.loc[v.index >= "2021-03-01", "CUSDT"] = 50e6
        c = pd.DataFrame({"symbole": ["AUSDT", "AUSDT", "CUSDT", "CUSDT", "ZUSDT"],
                          "t": ["2021-02-20 10:00", "2021-03-10 10:00", "2021-04-05 10:00", "2021-05-05 10:00", "2021-05-05 10:00"],
                          "rendement_15m": -0.05, "var_oi_15m": -0.04, "volume_15m": 1.0})
        r, info = cc.refiltrer(c, v)
        self.assertEqual(list(zip(r["symbole"], r["t"].astype(str))), [("AUSDT", "2021-03-10 10:00:00"), ("CUSDT", "2021-05-05 10:00:00")])
        self.assertEqual((info["candidats_avant"], info["candidats_apres"], info["symboles_sans_volume"]), (5, 2, ["ZUSDT"]))


def zip_klines(k):
    ms = ((k.index - pd.Timestamp(0)) // pd.Timedelta(milliseconds=1)).astype("int64")
    df = pd.DataFrame({0: ms, 1: k.open, 2: k.high, 3: k.low, 4: k.close, 5: 1.0, 6: ms + 59999, 7: k.volume_usdt, 8: 1, 9: 0, 10: 0, 11: 0})
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("k.csv", df.to_csv(index=False, header=False))
    return b.getvalue()


def zip_metrics(o, s):
    """Fichier metrics à la convention de l'archive réelle : une observation faite à l'heure h est datée h − 5 minutes
    (audit du 09/11/2026 : archive(t) = API(t + 5 min)). `o` est indexé à l'heure réelle."""
    df = pd.DataFrame({"create_time": (o.index - d1.DECALAGE_METRICS).strftime("%Y-%m-%d %H:%M:%S"), "symbol": s, "sum_open_interest": o.values,
                       "sum_open_interest_value": o.values * 100})
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("m.csv", df.to_csv(index=False))
    return b.getvalue()


class Corrections(unittest.TestCase):
    """Corrections du 12/11/2026 (fiche § 13) : horodatage, valeurs nulles, départage, blocs."""

    def test_lecteur_decale_de_5_minutes(self):
        o = pd.Series([1000.0, 990.0], index=pd.to_datetime(["2024-08-05 10:00", "2024-08-05 10:05"]))  # heures réelles
        lu = d1.lire_metrics_contrats(zip_metrics(o, "XUSDT"))
        self.assertEqual(list(lu.index), list(o.index))          # heure réelle retrouvée
        brut = pd.DataFrame({"create_time": ["2024-08-05 10:00:00"], "symbol": "X", "sum_open_interest": [7.0], "sum_open_interest_value": [1.0]})
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("m.csv", brut.to_csv(index=False))
        self.assertEqual(d1.lire_metrics_contrats(b.getvalue()).index[0], pd.Timestamp("2024-08-05 10:05"))  # create_time + 5 min

    def test_avance_de_5_minutes_impossible(self):
        # L'intérêt ouvert chute réellement à 10:15, après la baisse du prix (10:00 à 10:10). L'archive date cette
        # chute 10:10. Lue telle quelle, elle déclencherait une cascade à 10:10, avant que la chute soit observable.
        k, _ = cascade(k1_plat(), oi_plat(k1_plat()), baisse_oi=0)
        o = oi_plat(k1_plat()); o[o.index >= pd.Timestamp("2022-03-01 10:15")] = 950.0
        lu = d1.lire_metrics_contrats(zip_metrics(o, "XUSDT"))
        t = set(dc.candidats(k, lu)["t"])
        self.assertNotIn(pd.Timestamp("2022-03-01 10:10"), t)
        self.assertIn(pd.Timestamp("2022-03-01 10:15"), t)
        archive_brute = lu.copy(); archive_brute.index = archive_brute.index - d1.DECALAGE_METRICS   # ce que lisait l'ancien code
        self.assertIn(pd.Timestamp("2022-03-01 10:10"), set(dc.candidats(k, archive_brute)["t"]))    # le défaut, reproduit

    def test_valeur_nulle_rejetee(self):
        k, _ = cascade(k1_plat(), oi_plat(k1_plat()), baisse_oi=0)
        o = oi_plat(k1_plat()); o[pd.Timestamp("2022-03-01 10:10")] = 0.0   # incident de la source pendant la chute du prix
        lu = d1.lire_metrics_contrats(zip_metrics(o, "XUSDT"))
        self.assertNotIn(pd.Timestamp("2022-03-01 10:10"), lu.index)
        self.assertTrue(dc.candidats(k, lu).empty)                         # pas de cascade fabriquée par un zéro

    def test_departage_par_volume_et_permutation(self):
        t = pd.Timestamp("2022-03-01 10:00")
        ev = pd.DataFrame({"symbole": list("ABCDEFG"), "t": t, "volume_15m": [1.0, 7.0, 3.0, 6.0, 2.0, 5.0, 4.0]})
        prises, ignorees = dc.attribuer(ev, 5, pd.Timedelta(hours=4))
        self.assertEqual(list(prises["symbole"]), ["B", "D", "F", "G", "C"])   # les 5 plus gros volumes, dans l'ordre
        self.assertEqual(sorted(ignorees["symbole"]), ["A", "E"])              # et non les deux derniers de l'alphabet
        for graine in range(20):                                               # l'ordre du fichier ne change rien
            m = ev.sample(frac=1, random_state=graine)
            self.assertEqual(sorted(dc.attribuer(m, 5, pd.Timedelta(hours=4))[1]["symbole"]), ["A", "E"])
            self.assertEqual(cc.occupation_ignoree(m, 5, pd.Timedelta(hours=4)), 2)
        egal = pd.DataFrame({"symbole": ["Z", "A", "M"], "t": t, "volume_15m": 1.0})
        self.assertEqual(list(dc.attribuer(egal, 2, pd.Timedelta(hours=4))[0]["symbole"]), ["A", "M"])  # égalité : alphabet

    def test_blocs_et_bornes(self):
        self.assertEqual(cc.BLOCS[0], ("developpement", "2021-12-01", "2024-01-01"))
        self.assertEqual(cc.BASE["d"], pd.Timedelta(minutes=5))
        # une cascade toutes les 5 h sur un symbole : pause de 4 h → toutes comptées ; tenue 4 h + pause 4 h → une sur deux
        t = pd.date_range("2022-06-01", periods=8, freq="5h")
        c = pd.DataFrame({"symbole": "A", "t": t.astype(str), "rendement_15m": -0.05, "var_oi_15m": -0.04, "volume_15m": 1.0})
        avant = pd.DataFrame({"symbole": "B", "t": ["2021-06-01 10:00:00"], "rendement_15m": -0.05, "var_oi_15m": -0.04, "volume_15m": 1.0})
        md, R = cc.rapport(pd.concat([c, avant]))
        self.assertEqual(R["blocs"]["developpement"]["cascades"], 8)               # l'événement de juin 2021 n'est dans aucun bloc
        self.assertEqual(R["blocs"]["developpement"]["jouables_borne_basse"], 4)
        self.assertIn("borne basse", md)


class Flux(unittest.TestCase):
    def test_symbole_deux_mois_avec_report(self):
        s = "XUSDT"
        k = k1_plat("2022-03-01", jours=61)  # mars et avril
        o = oi_plat(k)
        k, o = cascade(k, o, t0="2022-03-31 22:00")  # fenêtre et placebo débordent sur avril
        stock = {}
        for m in ("2022-03", "2022-04"):
            km = k[k.index.strftime("%Y-%m") == m]
            stock[f"{d1.RACINE_M}/klines/{s}/1m/{s}-1m-{m}.zip"] = zip_klines(km)
        for d, g in o.groupby(o.index.normalize()):
            stock[f"{d1.RACINE_J}/metrics/{s}/{s}-metrics-{d.date().isoformat()}.zip"] = zip_metrics(g, s)

        class Source:
            appels = 0
            def lire(self, cle):
                Source.appels += 1
                return stock.get(cle)
        tmp = Path(tempfile.mkdtemp())
        try:
            el = pd.Series(True, index=pd.date_range("2022-03-01", "2022-04-30"))
            cands = cc.traiter_symbole(Source(), s, ["2022-03"], el, tmp, {})
            self.assertTrue(any(pd.Timestamp(c["t"]) == pd.Timestamp("2022-03-31 22:10") for c in cands))
            self.assertEqual(len({c["t"] for c in cands}), len(cands))  # aucun instant compté deux fois
            self.assertTrue((tmp / s / "2022-03.npz").exists())
            self.assertTrue((tmp / s / "2022-04.npz").exists())  # mois chargé pour le report seulement
            self.assertFalse((tmp / s / "2022-04.json").exists())  # pas de détection sur un mois non éligible
            avril = d1.relire_compact(dict(np.load(tmp / s / "2022-04.npz")))
            self.assertGreaterEqual(avril.index.max(), pd.Timestamp("2022-04-01 22:00"))  # placebo à +24 h couvert
            n = Source.appels
            cands2 = cc.traiter_symbole(Source(), s, ["2022-03"], el, tmp, {})  # reprise : rien de relu
            self.assertEqual(Source.appels, n)
            self.assertEqual(len(cands2), len(cands))
        finally:
            shutil.rmtree(tmp)

    def test_instant_de_minuit_en_fin_de_mois(self):
        """Avec le décalage de 5 minutes, la dernière ligne d'un mois porte 00:00 du mois suivant. Cet instant se
        détecte une seule fois, dans le mois suivant s'il est éligible, jamais deux fois."""
        s = "XUSDT"
        k = k1_plat("2022-03-01", jours=61)
        k, o = cascade(k, oi_plat(k), t0="2022-03-31 23:50")  # chute de 23:50 à 23:59, détectable à 00:00 le 01/04
        stock = {}
        for m in ("2022-03", "2022-04"):
            stock[f"{d1.RACINE_M}/klines/{s}/1m/{s}-1m-{m}.zip"] = zip_klines(k[k.index.strftime("%Y-%m") == m])
        archive = o.copy(); archive.index = archive.index - d1.DECALAGE_METRICS       # heures telles que l'archive les écrit
        for d, g in archive.groupby(archive.index.normalize()):
            g = g.copy(); g.index = g.index + d1.DECALAGE_METRICS                      # zip_metrics retire les 5 minutes
            stock[f"{d1.RACINE_J}/metrics/{s}/{s}-metrics-{d.date().isoformat()}.zip"] = zip_metrics(g, s)

        class Source:
            def lire(self, cle):
                return stock.get(cle)
        el = pd.Series(True, index=pd.date_range("2022-03-01", "2022-04-30"))
        minuit = pd.Timestamp("2022-04-01 00:00")
        for mois, attendu in ((["2022-03", "2022-04"], 1), (["2022-03"], 0)):
            tmp = Path(tempfile.mkdtemp())
            try:
                cands = cc.traiter_symbole(Source(), s, mois, el, tmp, {})
                self.assertEqual(sum(pd.Timestamp(c["t"]) == minuit for c in cands), attendu, mois)
            finally:
                shutil.rmtree(tmp)

    def test_rapport_et_occupation(self):
        t = pd.to_datetime(["2022-01-01 10:00"] * 7)
        ev = pd.DataFrame({"symbole": [f"S{i}" for i in range(7)], "t": t})
        self.assertEqual(cc.occupation_ignoree(ev, 5, pd.Timedelta(hours=4)), 2)
        c = pd.DataFrame({"symbole": [f"S{i}" for i in range(7)], "t": t.astype(str), "rendement_15m": -0.05, "var_oi_15m": -0.04, "volume_15m": 1.0})
        md, R = cc.rapport(c)
        self.assertEqual(R["blocs"]["developpement"]["cascades"], 7)
        self.assertEqual(R["blocs"]["developpement"]["ignorees_k"], 2)
        self.assertIn("Contrôle sans rendement", md)


if __name__ == "__main__":
    unittest.main(verbosity=1)
