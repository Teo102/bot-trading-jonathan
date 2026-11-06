"""Tests du hors échantillon de STRAT-20261102-06 (06/11/2026). Aucune donnée de marché, aucun réseau.
Exécution : python -B test_hors_echantillon06.py"""
import sys

sys.dont_write_bytecode = True
import copy
import csv
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import hors_echantillon06 as h6  # noqa: E402
import run_essai06 as r6  # noqa: E402
import test_donnees_et_essai as td  # noqa: E402
import variantes06 as v6  # noqa: E402


def spec_tranchee():
    d = json.loads(h6.SPEC.read_text())
    d["decision_ecrite"] = "test"
    for x in d["points_ouverts"].values():
        x["statut"] = "tranche"
    return d


def registre_vierge(tmp, maj=None):
    reg = tmp / "registre.csv"
    r_ = pd.read_csv(r6.REGISTRE, dtype=str, keep_default_na=False)
    r_.loc[r_["id_essai"].isin(["E19", "E20"]), "date"] = ""
    for (e, col), val in (maj or {}).items():
        r_.loc[r_["id_essai"] == e, col] = val
    r_.to_csv(reg, index=False)
    return reg


class Specification(unittest.TestCase):
    def test_conforme_au_registre(self):
        d = json.loads(h6.SPEC.read_text())
        reg = {r["id_essai"]: r for r in csv.DictReader(r6.REGISTRE.open())}
        self.assertEqual(d["bloc"]["timerange_registre"], reg["E19"]["timerange"])
        self.assertEqual(len(v6.dates_bloc(d["bloc"])) - 1, int(reg["E19"]["semaines"]))
        self.assertEqual(v6.dates_bloc(d["bloc"])[0], pd.Timestamp("2025-08-04"))
        self.assertEqual(v6.dates_bloc(d["bloc"])[-1], pd.Timestamp("2026-10-26"))
        self.assertEqual(d["criteres"]["sharpe_min"], json.loads((ICI / "config_strat06.json").read_text())["seuil_sharpe_hors_echantillon"])
        self.assertAlmostEqual(d["essais"]["E20"]["moteur"]["frais"], float(reg["E20"]["frais"]))
        self.assertAlmostEqual(d["essais"]["E20"]["moteur"]["glissement"], float(reg["E20"]["glissement"]))

    def test_refus_sans_decision_ni_empreinte(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            j = tmp / "hors_echantillon_strat06.json"
            shutil.copy(h6.SPEC, j)
            with self.assertRaises(h6.Refus):  # pas d'empreinte
                h6.charger_spec(j)
            import hashlib
            d_vide = json.loads(j.read_text())
            d_vide["decision_ecrite"] = ""
            j.write_text(json.dumps(d_vide))
            (tmp / "hors_echantillon_strat06.json.sha256").write_text(hashlib.sha256(j.read_bytes()).hexdigest())
            with self.assertRaises(h6.Refus):  # décision vide
                h6.charger_spec(j)
            d = json.loads(j.read_text()); d["decision_ecrite"] = "x"; j.write_text(json.dumps(d))
            with self.assertRaises(h6.Refus):  # empreinte périmée
                h6.charger_spec(j)
            d["points_ouverts"]["cs5_critere_02R"]["statut"] = "a_trancher"
            j.write_text(json.dumps(d))
            (tmp / "hors_echantillon_strat06.json.sha256").write_text(hashlib.sha256(j.read_bytes()).hexdigest())
            with self.assertRaises(h6.Refus):  # points ouverts non tranchés
                h6.charger_spec(j)
        finally:
            shutil.rmtree(tmp)

    def test_validation(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            d = spec_tranchee()
            reg = registre_vierge(tmp)
            h6.valider("E19", d, reg)
            with self.assertRaises(h6.Refus):
                h6.valider("E20", d, reg)  # E19 non lancé
            with self.assertRaises(h6.Refus):
                h6.valider("E18", d, reg)
            reg2 = registre_vierge(tmp, {("E19", "date"): "2026-11-06T00:00:00Z"})
            with self.assertRaises(h6.Refus):
                h6.valider("E19", d, reg2)
            h6.valider("E20", d, reg2)
        finally:
            shutil.rmtree(tmp)


class Verdict(unittest.TestCase):
    MT = {"rendement_net_total_brut100": 0.8, "sharpe_net_annualise": 1.9, "ic90_moyenne_hebdo_blocs": [0.001, 0.02],
          "alpha_hebdo_residuel": 0.01, "drawdown_max_brut100": 0.30, "semaines": 64, "semaines_vides": 2,
          "part_max_nom_du_gain": 0.10, "part_max_mois_du_gain": 0.30}

    def test_franchi_et_echecs(self):
        crit = json.loads(h6.SPEC.read_text())["criteres"]
        self.assertTrue(h6.verdict_e19(self.MT, crit, 300)["toutes_franchies"])
        for k, val, porte in (("sharpe_net_annualise", 1.72, "sharpe_sup_seuil"), ("ic90_moyenne_hebdo_blocs", [-0.001, 0.02], "ic90_bas_positif"),
                              ("alpha_hebdo_residuel", -0.001, "alpha_btc_positif"), ("semaines_vides", 40, "semaines_avec_position"),
                              ("part_max_mois_du_gain", 0.41, "concentration_mois")):
            mt = dict(self.MT, **{k: val})
            v = h6.verdict_e19(mt, crit, 300)
            self.assertFalse(v["portes"][porte], k)
            self.assertFalse(v["toutes_franchies"])
        self.assertFalse(h6.verdict_e19(self.MT, crit, 99)["portes"]["lignes"])


class Bout_en_bout(unittest.TestCase):
    def test_e19_puis_e20(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            vision = tmp / "v"
            td.faux_vision(vision, n_sym=10, jours=420, debut="2020-06-01")
            for s, mois_debut in (("S08USDT", "2021-02"), ("S09USDT", "2021-03")):
                for f in vision.rglob(f"{s}-*.zip"):
                    if re.search(r"(\d{4}-\d{2})", f.name).group(1) < mois_debut:
                        f.unlink(); Path(str(f) + ".CHECKSUM").unlink()
            c6, c3 = r6.charger_configs()
            c6, c3 = copy.deepcopy(c6), copy.deepcopy(c3)
            c6["univers"]["liquidite_min_usdt"] = 0
            c6["bootstrap"]["tirages"] = 200
            d = spec_tranchee()
            d["bloc"].update(premier_jour="2021-02-01", dernier_jour="2021-06-28", fin_donnees_prix="2021-07-05T02:00:00Z",
                             timerange_registre="20210201-20210705")
            maj = {(e, c): v for e in ("E19", "E20") for c, v in (("timerange", "20210201-20210705"), ("semaines", "22"))}
            reg = registre_vierge(tmp, maj)
            src = db.VisionLocale(vision)
            kw = dict(debut_donnees=pd.Timestamp("2020-06-01"), exiger_non_coin=False, spec=d)
            o19 = h6.executer_hors_echantillon("E19", src, c6, c3, reg, tmp / "o", **kw)
            self.assertIn("verdict_e19", o19["metriques"])
            self.assertIn("Portes du hors échantillon", o19["rapport"])
            self.assertTrue(v6.ligne_registre("E19", reg)["date"].strip())
            with self.assertRaises(h6.Refus):
                h6.executer_hors_echantillon("E19", src, c6, c3, reg, tmp / "o", **kw)
            o20 = h6.executer_hors_echantillon("E20", src, c6, c3, reg, tmp / "o", **kw)
            self.assertIn(o20["metriques"]["verdict_final"]["verdict"], ("rejetee", "papier autorise sous conditions CS4 à CS7"))
            m19 = json.loads((tmp / "o" / "E19_metriques.json").read_text())["meta"]
            m20 = json.loads((tmp / "o" / "E20_metriques.json").read_text())["meta"]
            self.assertEqual(m20["surcharges"]["moteur"]["glissement_stop"], 0.006)
            self.assertEqual(m19["surcharges"]["moteur"], {})
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=1)
