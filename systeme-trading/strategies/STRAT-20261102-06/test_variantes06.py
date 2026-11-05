"""Tests des variantes E03 à E18 de STRAT-20261102-06 (03/11/2026). Aucune donnée de marché, aucun réseau.
Exécution : python -B test_variantes06.py"""
import sys

sys.dont_write_bytecode = True
import copy
import csv
import json
import shutil
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import moteur_xsmom as m  # noqa: E402
import run_essai06 as r6  # noqa: E402
import test_donnees_et_essai as td  # noqa: E402
import test_moteur_synthetique as ts  # noqa: E402
import test_strat06 as t6  # noqa: E402
import univers_cotations as uc  # noqa: E402
import variantes06 as v6  # noqa: E402

ESSAIS = [f"E{i:02d}" for i in range(3, 19)]


def bases():
    c6, c3 = r6.charger_configs()
    return c6, c3, r6.params_cotation(c6, c3), r6.r3.params_depuis(c3)


def registre_vierge(tmp: Path) -> Path:
    reg = tmp / "registre.csv"
    r_ = pd.read_csv(r6.REGISTRE, dtype=str, keep_default_na=False)
    r_["date"] = ""
    r_.to_csv(reg, index=False)
    return reg


class Transcription(unittest.TestCase):
    def test_empreinte_et_couverture_du_registre(self):
        d = v6.charger_variantes()
        self.assertEqual(sorted(d["essais"]), ESSAIS)
        self.assertNotIn("E19", d["essais"])
        reg = {r["id_essai"]: r for r in csv.DictReader(r6.REGISTRE.open())}
        _, c3, pc, p = bases()
        for e, v in d["essais"].items():
            self.assertEqual(v["variante"], reg[e]["variante"], e)
            self.assertTrue(reg[e]["bloc"].startswith("dev+val"), e)
            _, p_v, _ = v6.params_variante(v, pc, p, c3["exclusions"]["memecoins_liste_close_2026-11-01"])
            self.assertAlmostEqual(float(reg[e]["frais"]), p_v.frais, msg=e)
            self.assertAlmostEqual(float(reg[e]["glissement"]), p_v.glissement, msg=e)
        self.assertEqual(d["essais"]["E17"]["moteur"]["glissement_stop"], 0.0060)  # commentaire du registre

    def test_chaque_surcharge_ne_change_que_sa_cible(self):
        d = v6.charger_variantes()
        _, c3, pc, p = bases()
        memes = c3["exclusions"]["memecoins_liste_close_2026-11-01"]
        for e, v in d["essais"].items():
            pc_v, p_v, sp = v6.params_variante(v, pc, p, memes)
            dc = {f.name for f in fields(pc) if getattr(pc, f.name) != getattr(pc_v, f.name)}
            dm = {f.name for f in fields(p) if getattr(p, f.name) != getattr(p_v, f.name)}
            attendu_c = set(v.get("cotation", {})) | ({"exclus"} if sp["memecoins_exclus"] else set())
            self.assertEqual(dc, attendu_c, e)
            self.assertEqual(dm, set(v.get("moteur", {})), e)
        self.assertEqual(v6.params_variante(d["essais"]["E11"], pc, p, memes)[1].stop, None)

    def test_json_modifie_refuse(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            j = tmp / "variantes_strat06.json"
            shutil.copy(v6.VARIANTES, j)
            shutil.copy(str(v6.VARIANTES) + ".sha256", str(j) + ".sha256")
            v6.charger_variantes(j)
            j.write_text(j.read_text().replace('"age_max_j": 30', '"age_max_j": 31'))
            with self.assertRaises(v6.Refus):
                v6.charger_variantes(j)
        finally:
            shutil.rmtree(tmp)


class Garde_fous(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.reg = registre_vierge(self.tmp)
        self.d = v6.charger_variantes()
        _, _, self.pc, self.p = bases()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_refus(self):
        cas = []
        d = copy.deepcopy(self.d); d["essais"]["E03"]["cotation"]["inconnue"] = 1; cas.append(("E03", d))
        d = copy.deepcopy(self.d); d["essais"]["E03"]["cotation"]["age_max_j"] = 60; cas.append(("E03", d))
        d = copy.deepcopy(self.d); d["essais"]["E05"]["variante"] = "liquidite 11 M"; cas.append(("E05", d))
        d = copy.deepcopy(self.d); d["essais"]["E14"]["special"]["calendrier"] = "mardi"; cas.append(("E14", d))
        d = copy.deepcopy(self.d); d["essais"]["E09"] = {"variante": "stop 20 %"}; cas.append(("E09", d))
        cas += [("E19", self.d), ("E01", self.d)]
        for e, d in cas:
            with self.assertRaises(v6.Refus, msg=e):
                v6.valider(e, d, self.reg, self.pc, self.p)
        for e in ESSAIS:
            v6.valider(e, self.d, self.reg, self.pc, self.p)

    def test_essai_consomme_refuse(self):
        r_ = pd.read_csv(self.reg, dtype=str, keep_default_na=False)
        r_.loc[r_["id_essai"] == "E07", "date"] = "2026-11-03T00:00:00Z"
        r_.to_csv(self.reg, index=False)
        with self.assertRaises(v6.Refus):
            v6.valider("E07", self.d, self.reg, self.pc, self.p)

    def test_controle_refuse_si_e01_e02_non_lances(self):
        c6, c3 = r6.charger_configs()
        with self.assertRaises(r6.r3.Refus):
            r6.executer_variante("CDV", None, c6, c3, self.reg, self.tmp / "o")


class Calendrier_et_notionnel(unittest.TestCase):
    def test_lundis_et_jeudis(self):
        b = v6.charger_variantes()["bloc"]
        lun = v6.dates_bloc(b, "lundi")
        self.assertEqual(len(lun) - 1, 238)
        self.assertEqual(lun[0], pd.Timestamp("2021-01-04"))
        self.assertEqual(lun[-1], pd.Timestamp("2025-07-28"))
        jeu = v6.dates_bloc(b, "jeudi")
        self.assertEqual(jeu[0], pd.Timestamp("2021-01-07"))
        self.assertEqual(jeu[-1], pd.Timestamp("2025-07-24"))
        self.assertTrue(all(x.dayofweek == 3 for x in jeu))
        b2 = dict(b, fin_donnees_prix="2025-07-28T00:30:00Z")
        with self.assertRaises(v6.Refus):
            v6.dates_bloc(b2, "lundi")

    def test_notionnel(self):
        self.assertAlmostEqual(v6.notionnel(uc.ParamsCotation()), 1 / 12)
        self.assertAlmostEqual(v6.notionnel(uc.ParamsCotation(noms_max=3)), 1 / 6)
        self.assertAlmostEqual(v6.notionnel(uc.ParamsCotation(noms_max=10)), 1 / 20)


class Cible(unittest.TestCase):
    def test_sans_filtre_identique_a_la_base(self):
        j, h, f, cot = t6.marche_cotations(5)
        for pc in (t6.PC, uc.ParamsCotation(liquidite_min=0.0, multiple_couverture=1.5),
                   uc.ParamsCotation(liquidite_min=0.0, inverse=True), uc.ParamsCotation(liquidite_min=0.0, couverture=False)):
            a, b = uc.fabrique_cible(pc, t6.DEBUT), v6.fabrique_cible_variante(pc, t6.DEBUT)
            for t in ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=30)):
                self.assertEqual(a(j, t, None), b(j, t, None))

    def test_filtre_e16(self):
        j, h, f, cot = t6.marche_cotations(7)
        jeunes = sorted((L, s) for s, L in cot.items() if L > t6.DEBUT)
        L, s = jeunes[0]
        D = L + pd.Timedelta(days=20)  # délistage 20 jours après la cotation
        j = {k: x.copy() for k, x in j.items()}
        j["volume"].loc[j["volume"].index > D, s] = 0.0
        fin = j["volume"].index[-1] + pd.Timedelta(hours=2)
        _, _, _, dernier = m.couper_zombies(j, {}, None)
        self.assertEqual(dernier[s], D)
        journal = {}
        g = v6.fabrique_cible_variante(t6.PC, t6.DEBUT, dernier, 7, fin, journal)
        base = uc.fabrique_cible(t6.PC, t6.DEBUT)
        retire = 0
        for t in ts.lundis(j, depuis=L):
            dedans = t - pd.Timedelta(days=1) <= D <= t + pd.Timedelta(days=7)
            pg, pb = g(j, t, None)[0], base(j, t, None)[0]
            if dedans:
                self.assertNotIn(s, pg)
                retire += s in pb
            elif t > D + pd.Timedelta(days=7) or t < L:
                self.assertEqual(s in pg, s in pb)
        self.assertGreater(retire, 0)  # le nom était bien choisi par la base dans la fenêtre
        # la fin des données au verrou n'est pas un délistage
        derniers_vivants = {x: dernier[x] for x in dernier if dernier[x] is not None and dernier[x] >= j["volume"].index[-1] - pd.Timedelta(days=1)}
        t_fin = j["volume"].index[-1] - pd.Timedelta(days=3)
        self.assertFalse(v6.a_exclure_e16(derniers_vivants, t_fin, 7, fin))


class Decoupe(unittest.TestCase):
    def test_sous_blocs_somment_au_total(self):
        sem = pd.DataFrame({"lundi": pd.date_range("2024-05-06", periods=12, freq="W-MON"), "net": range(12)})
        lig = pd.DataFrame({"lundi": sem["lundi"], "symbole": "X"})
        sb = v6.decouper(sem, lig, "2024-07-01")
        self.assertEqual(sb["developpement"][0]["net"].sum() + sb["validation"][0]["net"].sum(), sem["net"].sum())
        self.assertTrue((pd.to_datetime(sb["validation"][0]["lundi"]) >= pd.Timestamp("2024-07-01")).all())


class Bout_en_bout(unittest.TestCase):
    def test_variante_sur_faux_vision(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            vision = tmp / "v"
            td.faux_vision(vision, n_sym=10, jours=420, debut="2020-06-01")
            for s, mois_debut in (("S08USDT", "2021-02"), ("S09USDT", "2021-03")):
                for fichier in vision.rglob(f"{s}-*.zip"):
                    import re
                    if re.search(r"(\d{4}-\d{2})", fichier.name).group(1) < mois_debut:
                        fichier.unlink()
                        Path(str(fichier) + ".CHECKSUM").unlink()
            c6, c3 = r6.charger_configs()
            c6, c3 = copy.deepcopy(c6), copy.deepcopy(c3)
            c6["univers"]["liquidite_min_usdt"] = 0
            c6["bootstrap"]["tirages"] = 200
            d = copy.deepcopy(v6.charger_variantes())
            d["bloc"] = {"nom": "dev+val", "premier_jour": "2021-02-01", "dernier_jour": "2021-06-28",
                         "fin_donnees_prix": "2021-07-05T02:00:00Z", "coupure_sous_blocs": "2021-04-05"}
            reg = registre_vierge(tmp)
            src = db.VisionLocale(vision)
            kw = dict(debut_donnees=pd.Timestamp("2020-06-01"), exiger_non_coin=False, variantes=d)
            for e in ("E09", "E13", "E14", "E16", "E18"):
                out = r6.executer_variante(e, src, c6, c3, reg, tmp / "o", **kw)
                mt = out["metriques"]
                self.assertGreater(mt["lignes"], 0, e)
                self.assertEqual(set(mt["sous_blocs"]), {"developpement", "validation"}, e)
                self.assertAlmostEqual(sum(x["rendement_net_total_brut100"] for x in mt["sous_blocs"].values()),
                                       mt["rendement_net_total_brut100"], places=10, msg=e)
                self.assertTrue((tmp / "o" / f"{e}_metriques.md").exists())
            sem13 = pd.read_csv(tmp / "o" / "E13_semaines.csv", keep_default_na=False)
            vides13 = int(((sem13["longs"] == "") & (sem13["shorts"] == "")).sum())
            self.assertEqual(json.loads((tmp / "o" / "E13_metriques.json").read_text())["metriques"]["semaines_vides"], vides13)
            self.assertLess(vides13, len(sem13))
            lig13 = pd.read_csv(tmp / "o" / "E13_lignes.csv")
            self.assertNotIn("BTC", set(lig13["symbole"]))
            lig18 = pd.read_csv(tmp / "o" / "E18_lignes.csv")
            self.assertTrue((lig18.loc[lig18["symbole"] == "BTC", "sens"] < 0).all())
            self.assertTrue((lig18.loc[lig18["symbole"] != "BTC", "sens"] > 0).all())
            sem14 = pd.read_csv(tmp / "o" / "E14_semaines.csv")
            self.assertTrue((pd.to_datetime(sem14["lundi"]).dt.dayofweek == 3).all())
            with self.assertRaises(r6.r3.Refus):  # un essai ne se relance pas
                r6.executer_variante("E09", src, c6, c3, reg, tmp / "o", **kw)
        finally:
            shutil.rmtree(tmp)


class Reproduction(unittest.TestCase):
    def test_comparaison(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            sem = pd.DataFrame({"lundi": pd.date_range("2024-05-06", periods=12, freq="W-MON"), "net": [0.01 * i for i in range(12)]})
            sem[sem["lundi"] < "2024-07-01"].to_csv(tmp / "E01_semaines.csv", index=False)
            sem[sem["lundi"] >= "2024-07-01"].to_csv(tmp / "E02_semaines.csv", index=False)
            self.assertIn("REPRODUCTION CONFORME", r6.comparer_reproduction(sem, tmp))
            s2 = sem.copy(); s2.loc[s2["lundi"] == "2024-06-24", "net"] += 0.001  # semaine de jonction : admise
            self.assertIn("REPRODUCTION CONFORME", r6.comparer_reproduction(s2, tmp))
            s3 = sem.copy(); s3.loc[2, "net"] += 0.001
            self.assertIn("ARRET", r6.comparer_reproduction(s3, tmp))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=1)
