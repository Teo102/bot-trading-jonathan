"""Tests de analyse_strat.py sur des cas synthétiques connus.
Exécution : python -B test_analyse_strat.py -v"""
import sys

sys.dont_write_bytecode = True  # pas de __pycache__ dans le dossier de la stratégie

import contextlib
import hashlib
import io
import json
import math
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse_strat as a  # noqa: E402


def trade(open_date, close_date, profit, pair="BTC/USDT:USDT", is_short=False, stake=1000.0,
          fee=0.0005, funding=None, **extra):
    row = {
        "pair": pair, "open_date": f"{open_date} 00:00:00+00:00", "close_date": f"{close_date} 00:00:00+00:00",
        "profit_abs": profit, "stake_amount": stake, "amount": stake / 100.0, "open_rate": 100.0,
        "close_rate": 100.0, "fee_open": fee, "fee_close": fee, "is_short": is_short, "leverage": 1.0,
        "exit_reason": "channel_exit", "is_open": False,
    }
    if funding is not None:
        row["funding_fees"] = funding
    row.update(extra)
    return row


def day(value):
    return a.parse_day(value).normalize()


def results_payload(trades, timerange="20210101-20210131", wallet=10000.0):
    return {"strategy": {"TrendDonchianV1": {
        "trades": trades, "timerange": timerange, "starting_balance": wallet,
        "final_balance": wallet + sum(t["profit_abs"] for t in trades), "total_trades": len(trades),
        "trading_mode": "futures", "backtest_start": "2021-01-01 00:00:00", "backtest_end": "2021-01-31 00:00:00",
        "wallet_stats": {"sharpe": 1.0}, "sharpe": 0.5,
    }}, "strategy_comparison": []}


def run_quiet(argv):
    # Les tests ne dépendent pas des bougies réelles du dossier : sans --data-dir, aucune bougie.
    argv = list(argv)
    if "--agreger-registre" not in argv:
        if "--data-dir" not in argv:
            argv += ["--data-dir", "/dossier/absent/pour/les/tests"]
        if "--sims-blocs" not in argv:
            argv += ["--sims-blocs", "500"]
    with contextlib.redirect_stdout(io.StringIO()) as out:
        report = a.main(argv)
    return report, out.getvalue()


def write_candles(folder, pair, start, closes):
    """Bougies 1d synthétiques au format freqtrade, seules les colonnes lues sont écrites."""
    frame = pd.DataFrame({"date": pd.date_range(start, periods=len(closes), freq="D", tz="UTC"),
                          "close": [float(c) for c in closes]})
    frame.to_feather(a.candle_file(pair, folder))


class ReferenceEquity(unittest.TestCase):
    def setUp(self):
        self.df = a.prepare_trades([
            trade("2021-01-01", "2021-01-10", 1000.0, pair="A"),
            trade("2021-01-02", "2021-01-05", -200.0, pair="B"),
            trade("2021-01-06", "2021-01-08", 100.0, pair="C"),
            trade("2021-01-10", "2021-01-12", 50.0, pair="D"),
        ])

    def test_trades_chevauchants(self):
        # B s'ouvre pendant A : le gain de A (non clos) ne compte pas. C voit la perte de B, pas le gain de A.
        # D s'ouvre le jour de clôture de A : A compte comme clos.
        ref = a.reference_equity(self.df, 10000.0)
        self.assertEqual(ref.tolist(), [10000.0, 10000.0, 9800.0, 10900.0])

    def test_difference_avec_ancienne_somme_dans_l_ordre_d_ouverture(self):
        old = 10000.0 + self.df["profit_abs"].cumsum().shift(1, fill_value=0.0).to_numpy()
        self.assertEqual(old[1], 11000.0)  # défaut corrigé : le gain futur de A était déjà compté
        self.assertNotEqual(old[1], a.reference_equity(self.df, 10000.0)[1])

    def test_r_utilise_la_reference_corrigee(self):
        r, _, _, _ = a.r_multiples(self.df, 10000.0, 0.005)
        self.assertAlmostEqual(r[1], -200.0 / 50.0)
        self.assertAlmostEqual(r[2], 100.0 / (0.005 * 9800.0))

    def test_duree_nulle_exclue_de_sa_propre_reference(self):
        df = a.prepare_trades([
            trade("2021-01-20", "2021-01-20", 500.0, pair="E"),
            trade("2021-01-20", "2021-01-21", 70.0, pair="F"),
            trade("2021-01-22", "2021-01-23", 10.0, pair="G"),
        ])
        self.assertEqual(a.reference_equity(df, 1000.0).tolist(), [1000.0, 1000.0, 1570.0])


class DailyMetrics(unittest.TestCase):
    """Calcul à la main. Wallet 1000 sur 5 jours, +100 le jour 2, -55 le jour 4.
    Équité 1000, 1100, 1100, 1045, 1045. Rendements 0 ; 0,1 ; 0 ; -0,05 ; 0.
    Moyenne 0,01. Variance ddof=1 = 0,012 / 4 = 0,003. Downside² = 0,0025 / 5 = 0,0005.
    Drawdown (1100 - 1045) / 1100 = 5 %."""

    def setUp(self):
        self.df = a.prepare_trades([
            trade("2021-01-01", "2021-01-02", 100.0),
            trade("2021-01-03", "2021-01-04", -55.0),
        ])
        self.series = a.daily_series(self.df, 1000.0, day("20210101"), day("20210105"))
        self.metrics = a.daily_metrics(self.series, 1000.0)

    def test_rendements(self):
        np.testing.assert_allclose(self.series["ret"].to_numpy(), [0.0, 0.1, 0.0, -0.05, 0.0], atol=1e-12)

    def test_sharpe_a_la_main(self):
        self.assertAlmostEqual(self.metrics["sharpe_quotidien"], 0.01 / math.sqrt(0.003), places=12)
        self.assertAlmostEqual(self.metrics["sharpe_annualise"], 0.01 / math.sqrt(0.003) * math.sqrt(365), places=10)

    def test_sortino_a_la_main(self):
        self.assertAlmostEqual(self.metrics["sortino_annualise"], 0.01 / math.sqrt(0.0005) * math.sqrt(365), places=10)

    def test_drawdown_a_la_main(self):
        self.assertAlmostEqual(self.metrics["dd_reel"], 0.05, places=12)

    def test_calmar_a_la_main(self):
        expected = (1.045 ** (365 / 5) - 1.0) / 0.05
        self.assertAlmostEqual(self.metrics["calmar"], expected, places=8)

    def test_jours_sans_cloture_inclus_sur_toute_la_plage(self):
        # Mêmes trades, plage étendue de 5 à 31 jours, avant et après les trades.
        series = a.daily_series(self.df, 1000.0, day("20201231"), day("20210130"))
        self.assertEqual(len(series), 31)
        metrics = a.daily_metrics(series, 1000.0)
        self.assertEqual(metrics["jours_sans_cloture"], 29)
        rets = np.array([0.1, -0.05] + [0.0] * 29)
        self.assertAlmostEqual(metrics["sharpe_quotidien"], rets.mean() / rets.std(ddof=1), places=12)
        self.assertLess(metrics["sharpe_annualise"], self.metrics["sharpe_annualise"])

    def test_drawdown_compte_depuis_le_capital_initial(self):
        self.assertAlmostEqual(a.max_drawdown([900.0, 950.0], 1000.0), 0.10)

    def test_trade_hors_plage_refuse(self):
        with self.assertRaises(ValueError):
            a.daily_series(self.df, 1000.0, day("20210103"), day("20210105"))

    def test_serie_plate_sans_valeur_trompeuse(self):
        empty = a.prepare_trades([])
        metrics = a.daily_metrics(a.daily_series(empty, 1000.0, day("20210101"), day("20210110")), 1000.0)
        self.assertIsNone(metrics["sharpe_annualise"])
        self.assertIsNone(metrics["sortino_annualise"])
        self.assertIsNone(metrics["calmar"])
        self.assertEqual(metrics["dd_reel"], 0.0)


class Semesters(unittest.TestCase):
    def setUp(self):
        self.df = a.prepare_trades([
            trade("2021-06-20", "2021-06-25", 100.0, pair="A"),
            trade("2021-06-28", "2021-07-02", -50.0, pair="B"),  # ouvert en S1, clos en S2
            trade("2021-08-01", "2021-08-05", -30.0, pair="C"),
            trade("2022-01-05", "2022-01-10", 40.0, pair="D"),
        ])
        self.series = a.daily_series(self.df, 1000.0, day("20210615"), day("20220115"))
        self.sem = a.semester_breakdown(self.df, self.series, 1000.0, 0.01)

    def test_labels_et_partiels(self):
        rows = self.sem["semestres"]
        self.assertEqual([r["semestre"] for r in rows], ["2021-S1", "2021-S2", "2022-S1"])
        self.assertEqual([r["partiel"] for r in rows], [True, False, True])
        self.assertEqual(sum(r["jours"] for r in rows), len(self.series))

    def test_affectation_a_la_cloture(self):
        rows = self.sem["semestres"]
        self.assertEqual([r["trades"] for r in rows], [1, 2, 1])
        self.assertEqual([r["pnl"] for r in rows], [100.0, -80.0, 40.0])
        self.assertAlmostEqual(rows[0]["esperance_R"], 100.0 / 10.0)
        # À risque 1 %, B a pour référence 1100 (A clos) et C 1050 (A et B clos).
        self.assertAlmostEqual(rows[1]["esperance_R"], (-50.0 / 11.0 + -30.0 / 10.5) / 2)

    def test_drawdown_du_semestre_part_de_son_equite_initiale(self):
        rows = self.sem["semestres"]
        self.assertAlmostEqual(rows[1]["dd"], 80.0 / 1100.0)
        self.assertEqual(rows[2]["dd"], 0.0)

    def test_part_positive(self):
        self.assertEqual(self.sem["n_positifs"], 2)
        self.assertAlmostEqual(self.sem["part_positifs"], 2 / 3)

    def test_semestre_sans_trade_conserve(self):
        df = a.prepare_trades([trade("2021-01-05", "2021-01-10", 10.0)])
        series = a.daily_series(df, 1000.0, day("20210101"), day("20211231"))
        rows = a.semester_breakdown(df, series, 1000.0, 0.01)["semestres"]
        self.assertEqual(rows[1]["semestre"], "2021-S2")
        self.assertEqual(rows[1]["trades"], 0)
        self.assertIsNone(rows[1]["esperance_R"])
        self.assertIsNone(rows[1]["sharpe_annualise"])


class DeflatedSharpe(unittest.TestCase):
    def test_exemple_du_papier(self):
        # Bailey et López de Prado (2014) : SR annualisé 2,5, 250 jours, T=1250, N=100,
        # V[SR annualisé]=0,5, g3=-3, g4=10. Attendu SR0 ≈ 0,1132 et DSR ≈ 0,90.
        sr = 2.5 / math.sqrt(250)
        sr0, dsr, reason = a.deflated_sharpe(sr, 1250, -3.0, 10.0, 100, 0.5 / 250)
        self.assertIsNone(reason)
        self.assertAlmostEqual(sr0, 0.1132, places=4)
        self.assertAlmostEqual(dsr, 0.90, places=2)

    def test_psr_a_la_main(self):
        # g3=0 et g4=1 : dénominateur égal à 1. SR=0,1, SR0=0, T=101 : z = 0,1 x 10 = 1, Phi(1) = 0,84134...
        self.assertAlmostEqual(a.probabilistic_sharpe(0.1, 0.0, 101, 0.0, 1.0), 0.8413447460685429, places=10)
        # g3=0 et g4=3 : dénominateur racine(1 + 0,1²/2) = racine(1,005).
        expected = a.stats.norm.cdf(1.0 / math.sqrt(1.005))
        self.assertAlmostEqual(a.probabilistic_sharpe(0.1, 0.0, 101, 0.0, 3.0), expected, places=12)

    def test_n_egal_1_non_calculable(self):
        sr0, dsr, reason = a.deflated_sharpe(0.1, 1000, 0.0, 3.0, 1, 0.01)
        self.assertIsNone(dsr)
        self.assertIsNone(sr0)
        self.assertIn("N = 1", reason)

    def test_v_inconnue_non_calculable(self):
        for sr_var in (None, 0.0):
            _, dsr, reason = a.deflated_sharpe(0.1, 1000, 0.0, 3.0, 11, sr_var)
            self.assertIsNone(dsr)
            self.assertIn("V[SR]", reason)

    def test_n_inconnu_non_calculable(self):
        self.assertIsNone(a.deflated_sharpe(0.1, 1000, 0.0, 3.0, None, 0.01)[1])

    def test_registre_compte_les_abandonnes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reg.json"
            path.write_text(json.dumps({"essais": [
                {"id": "E01", "sharpe_quotidien": 0.01, "timerange": "A"},
                {"id": "E02", "sharpe_quotidien": 0.03, "timerange": "A"},
                {"id": "E03", "statut": "abandonne", "sharpe_quotidien": None},
            ]}))
            n_trials, sr_var, known, warnings = a.load_registry(path)
        self.assertEqual(n_trials, 3)
        self.assertEqual(known, [0.01, 0.03])
        self.assertAlmostEqual(sr_var, 0.0002)  # (0,01² + 0,01²) / 1
        self.assertTrue(any("Sharpe connus" in w for w in warnings))

    def test_registre_frais_multiples_accepte(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reg.json"
            path.write_text(json.dumps({"essais": [
                {"id": "E01", "sharpe_quotidien": 0.01, "frais": [0.0005, 0.001]},
                {"id": "E02", "sharpe_quotidien": 0.03, "frais": 0.0005},
            ]}))
            self.assertTrue(any("frais" in w for w in a.load_registry(path)[3]))

    def test_registre_avec_un_seul_sharpe_v_inconnue(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reg.json"
            path.write_text(json.dumps({"essais": [{"id": "E01", "sharpe_quotidien": 0.01}], "n_essais_declares": 5}))
            n_trials, sr_var, _, _ = a.load_registry(path)
        self.assertEqual(n_trials, 5)
        self.assertIsNone(sr_var)

    def test_registre_heterogene_signale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reg.json"
            path.write_text(json.dumps({"essais": [
                {"id": "E01", "sharpe_quotidien": 0.01, "timerange": "A", "frais": 0.0005},
                {"id": "E02", "sharpe_quotidien": 0.03, "timerange": "B", "frais": 0.0005},
            ]}))
            warnings = a.load_registry(path)[3]
        self.assertTrue(any("hétérogène" in w and "périodes" in w for w in warnings))


class CostsAndSides(unittest.TestCase):
    def test_frais_doubles_a_la_main(self):
        # Mise 1000, frais 0,05 % par côté : 1 USDT. Risque 0,5 % de 10000 = 50 USDT, soit 0,02 R.
        df = a.prepare_trades([trade("2021-01-01", "2021-01-02", 100.0)])
        stats = a.trade_statistics(df, 10000.0, 0.005, 200, 0)
        self.assertAlmostEqual(stats["esperance_R"], 2.0)
        self.assertAlmostEqual(stats["esperance_frais_doubles_R_approx"], 1.98)

    def test_financement_paye_double_et_recu_non_double(self):
        df = a.prepare_trades([
            trade("2021-01-01", "2021-01-02", 100.0, pair="A", funding=-5.0),
            trade("2021-01-01", "2021-01-02", 100.0, pair="B", funding=5.0),
        ])
        stats = a.trade_statistics(df, 10000.0, 0.005, 200, 0)
        self.assertAlmostEqual(stats["esperance_frais_et_financement_doubles_R_approx"], 1.98 - 0.1 / 2)

    def test_longs_shorts_et_financement(self):
        df = a.prepare_trades([
            trade("2021-01-01", "2021-01-02", 100.0, pair="A", funding=-3.0),
            trade("2021-01-01", "2021-01-02", -50.0, pair="B", is_short=True, funding=2.0),
            trade("2021-01-01", "2021-01-02", 20.0, pair="C", is_short=True, funding=-1.0),
        ])
        sides = a.side_breakdown(df, 10000.0, 0.005)
        self.assertEqual((sides["longs"]["trades"], sides["shorts"]["trades"]), (1, 2))
        self.assertAlmostEqual(sides["longs"]["financement_paye"], 3.0)
        self.assertAlmostEqual(sides["shorts"]["financement_paye"], 1.0)
        self.assertAlmostEqual(sides["shorts"]["financement_recu"], 2.0)
        self.assertAlmostEqual(sides["total"]["financement_net_paye"], 2.0)
        self.assertAlmostEqual(sides["shorts"]["esperance_R"], (-1.0 + 0.4) / 2)
        self.assertAlmostEqual(sides["shorts"]["taux_reussite"], 0.5)

    def test_champ_financement_absent(self):
        df = a.prepare_trades([trade("2021-01-01", "2021-01-02", 100.0)])
        self.assertIsNone(a.side_breakdown(df, 10000.0, 0.005)["total"]["financement_paye"])


class StatsConserved(unittest.TestCase):
    def test_monte_carlo_et_intervalle(self):
        df = a.prepare_trades([trade(f"2021-01-{d:02d}", f"2021-01-{d + 1:02d}", p)
                               for d, p in zip(range(1, 9), [50, -25, 50, -25, 100, -25, -25, 50])])
        stats = a.trade_statistics(df, 10000.0, 0.005, 500, 0)
        self.assertEqual(stats["trades"], 8)
        self.assertLess(stats["ic90_bas"], stats["esperance_R"])
        self.assertGreater(stats["ic90_haut"], stats["esperance_R"])
        self.assertGreaterEqual(stats["dd_95"], 0.0)
        self.assertAlmostEqual(stats["taux_reussite"], 0.5)
        self.assertAlmostEqual(stats["capital_final"], 10150.0)
        pnl = np.array([50, -25, 50, -25, 100, -25, -25, 50], dtype=float)
        self.assertAlmostEqual(stats["part_meilleur_trade_pnl"], 100.0 / pnl.sum())

    def test_seed_reproductible(self):
        df = a.prepare_trades([trade("2021-01-01", "2021-01-02", 50.0), trade("2021-01-03", "2021-01-04", -20.0)])
        one = a.trade_statistics(df, 10000.0, 0.005, 300, 7)
        two = a.trade_statistics(df, 10000.0, 0.005, 300, 7)
        self.assertEqual(one, two)


class ExportFormats(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.trades = [
            trade("2021-01-05", "2021-01-15", 300.0, pair="A", funding=-4.0),
            trade("2021-01-06", "2021-01-10", -100.0, pair="B", is_short=True, funding=1.0),
        ]
        self.payload = results_payload(self.trades)

    def tearDown(self):
        self.tmp.cleanup()

    def make_zip(self):
        # Même structure que l'export réel de freqtrade 2026.10 (vérifiée le 31/10/2026).
        path = self.dir / "backtest-result-2026-10-31_22-18-21.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("backtest-result-2026-10-31_22-18-21_config.json", json.dumps({"strategy": "TrendDonchianV1", "dry_run": True}))
            z.writestr("backtest-result-2026-10-31_22-18-21.json", json.dumps(self.payload))
            z.writestr("backtest-result-2026-10-31_22-18-21_TrendDonchianV1.py", "# code")
            z.writestr("backtest-result-2026-10-31_22-18-21_TrendDonchianV1.json", json.dumps({"strategy_name": "x", "params": {}}))
            z.writestr("backtest-result-2026-10-31_22-18-21_market_change.feather", b"\x00")
        return path

    def test_lecture_zip_ignore_config_et_parametres(self):
        path = self.make_zip()
        data, member, sha, config = a.load_export(path)
        self.assertEqual(member, "backtest-result-2026-10-31_22-18-21.json")
        self.assertEqual(sha, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(config["strategy"], "TrendDonchianV1")
        self.assertIn("TrendDonchianV1", data["strategy"])

    def test_lecture_json(self):
        path = self.dir / "E01.json"
        path.write_text(json.dumps(self.payload))
        self.assertEqual(a.load_export(path)[1], "E01.json")

    def test_fichier_sans_resultats_refuse(self):
        path = self.dir / "x.meta.json"
        path.write_text(json.dumps({"TrendDonchianV1": {"run_id": "a"}}))
        with self.assertRaises(ValueError):
            a.load_export(path)

    def test_bout_en_bout_exports(self):
        out = self.dir / "sortie"
        rep, stdout = run_quiet([str(self.make_zip()), "--essai", "E01", "--out", str(out), "--sims", "200"])
        js = json.loads((out / "E01_metriques.json").read_text(encoding="utf-8"))
        md = (out / "E01_metriques.md").read_text(encoding="utf-8")
        self.assertEqual(js["essai"], "E01")
        self.assertEqual(js["tracabilite"]["sha256_export"], rep["tracabilite"]["sha256_export"])
        self.assertIn("--essai E01", js["tracabilite"]["commande"])
        self.assertTrue(js["tracabilite"]["horodatage_utc"].endswith("+00:00"))
        self.assertIsNone(js["tracabilite"]["freqtrade_version_export"])
        self.assertEqual(js["metriques_quotidiennes"]["T"], 31)  # timerange de l'export, janvier entier
        self.assertEqual(js["dsr"]["statut"], "non_calculable")
        self.assertEqual(js["trades"]["trades"], 2)
        self.assertAlmostEqual(js["par_sens"]["total"]["financement_paye"], 4.0)
        self.assertEqual(js["metriques_reevaluees"]["statut"], "non_calculable")
        self.assertEqual(len(js["avertissements"]), 1)
        self.assertIn("Équité réévaluée non calculée", js["avertissements"][0])
        self.assertEqual(js["monte_carlo_blocs"]["base"], "realisee")
        self.assertIn("non calculable", md)
        self.assertIn(js["tracabilite"]["sha256_export"], md)
        self.assertIn("Équité réalisée à la clôture", md)
        self.assertIn("| Trades (longs, shorts) | 2 (1, 1) |", md)
        self.assertIn("10\u202f200,00", md)  # capital final au format français
        self.assertIn("Espérance avec frais doublés (approx.)", stdout)

    def test_bout_en_bout_dsr_par_options_et_par_registre(self):
        path = self.make_zip()
        rep, _ = run_quiet([str(path), "--essai", "E02", "--out", str(self.dir), "--sims", "100",
                            "--n-trials", "11", "--sr-var", "0.001"])
        self.assertEqual(rep["dsr"]["statut"], "calcule")
        self.assertEqual(rep["dsr"]["n_essais"], 11)
        registry = self.dir / "reg.json"
        registry.write_text(json.dumps({"essais": [{"id": "E01", "sharpe_quotidien": 0.01}, {"id": "E02", "sharpe_quotidien": 0.03}]}))
        rep2, _ = run_quiet([str(path), "--essai", "E03", "--out", str(self.dir), "--sims", "100", "--registry-json", str(registry)])
        self.assertEqual(rep2["dsr"]["n_essais"], 2)
        self.assertAlmostEqual(rep2["dsr"]["v_sr_quotidien"], 0.0002)

    def test_registre_et_options_incompatibles(self):
        registry = self.dir / "reg.json"
        registry.write_text(json.dumps({"essais": []}))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            a.main([str(self.make_zip()), "--out", str(self.dir), "--n-trials", "3", "--registry-json", str(registry)])

    def test_agregation_du_registre(self):
        path = self.make_zip()
        results = self.dir / "res"
        run_quiet([str(path), "--essai", "E01", "--out", str(results), "--sims", "100"])
        csv_path = self.dir / "REGISTRE.csv"
        csv_path.write_text("id_essai,date\nE01,\nE02,\n")
        target = self.dir / "agrege.json"
        run_quiet(["--agreger-registre", str(results), "--registre-csv", str(csv_path), "--registry-json", str(target)])
        reg = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in reg["essais"]], ["E01", "E02"])
        self.assertIsNotNone(reg["essais"][0]["sharpe_quotidien"])
        self.assertIsNone(reg["essais"][1]["sharpe_quotidien"])
        self.assertEqual(a.load_registry(target)[0], 2)

    def test_aucun_trade_exporte_quand_meme(self):
        path = self.dir / "vide.json"
        path.write_text(json.dumps(results_payload([])))
        rep, stdout = run_quiet([str(path), "--essai", "E10", "--out", str(self.dir), "--sims", "10"])
        self.assertTrue((self.dir / "E10_metriques.json").exists())
        self.assertIn("Aucun trade.", stdout)
        self.assertIsNone(rep["metriques_quotidiennes"]["sharpe_annualise"])

    def test_chauffe_insuffisante_signalee(self):
        payload = results_payload(self.trades)
        payload["strategy"]["TrendDonchianV1"]["backtest_start"] = "2021-01-04 00:00:00"
        path = self.dir / "chauffe.json"
        path.write_text(json.dumps(payload))
        rep, _ = run_quiet([str(path), "--essai", "E04", "--out", str(self.dir), "--sims", "10"])
        self.assertTrue(any("chauffe" in w for w in rep["avertissements"]))

    def test_defaut_out_a_cote_du_script(self):
        self.assertEqual(a.DEFAULT_OUT, Path(a.__file__).resolve().parent / "resultats")

    def test_ecart_de_capital_signale(self):
        payload = results_payload(self.trades)
        payload["strategy"]["TrendDonchianV1"]["final_balance"] = 1.0
        strat = payload["strategy"]["TrendDonchianV1"]
        warnings = a.consistency_warnings(a.prepare_trades(self.trades), 10000.0, strat)
        self.assertTrue(any("final_balance" in w for w in warnings))


class EquiteReevaluee(unittest.TestCase):
    def setUp(self):
        self.start, self.end = day("2021-01-01"), day("2021-01-06")
        self.closes = {"A": pd.Series([100.0, 90.0, 80.0, 120.0, 130.0, 140.0],
                                      index=pd.date_range("2021-01-01", periods=6, freq="D", tz="UTC"))}

    def series(self, trades, wallet=1000.0):
        return a.marked_series(a.prepare_trades(trades), wallet, self.start, self.end, self.closes)

    def test_long_valeur_latente_a_la_main(self):
        # 10 unités à 100, sortie le 04 pour +200. Latent 0, -100, -200, puis réalisé +200.
        tr = trade("2021-01-01", "2021-01-04", 200.0, pair="A", amount=10.0, open_rate=100.0)
        out = self.series([tr])
        self.assertEqual(out["equity"].tolist(), [1000.0, 900.0, 800.0, 1200.0, 1200.0, 1200.0])
        self.assertAlmostEqual(out["ret"].iloc[1], -0.1)
        self.assertAlmostEqual(out["ret"].iloc[3], 0.5)

    def test_short_signe_inverse(self):
        tr = trade("2021-01-01", "2021-01-04", -200.0, pair="A", amount=10.0, open_rate=100.0, is_short=True)
        self.assertEqual(self.series([tr])["equity"].tolist(), [1000.0, 1100.0, 1200.0, 800.0, 800.0, 800.0])

    def test_duree_nulle_sans_latent(self):
        tr = trade("2021-01-03", "2021-01-03", -30.0, pair="A", amount=10.0, open_rate=100.0)
        self.assertEqual(self.series([tr])["equity"].tolist(), [1000.0, 1000.0, 970.0, 970.0, 970.0, 970.0])

    def test_positions_superposees_et_capital_final_identique_au_realise(self):
        trades = [trade("2021-01-01", "2021-01-04", 200.0, pair="A", amount=10.0, open_rate=100.0),
                  trade("2021-01-02", "2021-01-05", 50.0, pair="A", amount=1.0, open_rate=90.0)]
        df = a.prepare_trades(trades)
        out = a.marked_series(df, 1000.0, self.start, self.end, self.closes)
        self.assertEqual(out["equity"].tolist(), [1000.0, 900.0, 790.0, 1230.0, 1250.0, 1250.0])
        real = a.daily_series(df, 1000.0, self.start, self.end)
        self.assertAlmostEqual(out["equity"].iloc[-1], real["equity"].iloc[-1])

    def test_metriques_a_la_main_et_creux(self):
        tr = trade("2021-01-01", "2021-01-04", 200.0, pair="A", amount=10.0, open_rate=100.0)
        out = self.series([tr])
        m = a.marked_metrics(out, 1000.0)
        ret = out["ret"].to_numpy()
        self.assertAlmostEqual(m["dd_reevalue"], 0.2)
        self.assertEqual(m["date_creux"], "2021-01-03")
        self.assertAlmostEqual(m["sharpe_annualise"], ret.mean() / ret.std(ddof=1) * math.sqrt(365))
        neg = np.minimum(ret, 0.0)
        self.assertAlmostEqual(m["sortino_annualise"], ret.mean() / math.sqrt((neg ** 2).mean()) * math.sqrt(365))
        growth = 1.2 ** (365 / 6) - 1
        self.assertAlmostEqual(m["calmar"], growth / 0.2)
        self.assertIn("réévaluée", m["base"])

    def test_perte_latente_invisible_sur_la_base_realisee(self):
        tr = trade("2021-01-01", "2021-01-04", 200.0, pair="A", amount=10.0, open_rate=100.0)
        df = a.prepare_trades([tr])
        real = a.daily_metrics(a.daily_series(df, 1000.0, self.start, self.end), 1000.0)
        self.assertEqual(real["dd_reel"], 0.0)
        self.assertIn("réalisée", real["base"])
        self.assertGreater(a.marked_metrics(self.series([tr]), 1000.0)["dd_reevalue"], 0.0)

    def test_bougie_manquante_refusee(self):
        closes = {"A": self.closes["A"].drop(pd.Timestamp("2021-01-02", tz="UTC"))}
        df = a.prepare_trades([trade("2021-01-01", "2021-01-04", 10.0, pair="A", amount=10.0, open_rate=100.0)])
        with self.assertRaises(ValueError):
            a.marked_series(df, 1000.0, self.start, self.end, closes)

    def test_trade_hors_plage_refuse(self):
        df = a.prepare_trades([trade("2020-12-30", "2021-01-04", 10.0, pair="A", amount=10.0, open_rate=100.0)])
        with self.assertRaises(ValueError):
            a.marked_series(df, 1000.0, self.start, self.end, self.closes)

    def test_lecture_des_bougies_coupee_a_la_fin_de_plage(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_candles(tmp, "BTC/USDT:USDT", "2021-01-01", [1, 2, 3, 4, 5, 6, 7, 8])
            self.assertEqual(a.candle_file("BTC/USDT:USDT", tmp).name, "BTC_USDT_USDT-1d-futures.feather")
            closes = a.load_closes(["BTC/USDT:USDT"], tmp, day("2021-01-02"), day("2021-01-04"))
        self.assertEqual(closes["BTC/USDT:USDT"].tolist(), [2.0, 3.0, 4.0])


class IntervallesParBlocs(unittest.TestCase):
    def test_indices_blocs_contigus_et_circulaires(self):
        rng = np.random.default_rng(1)
        idx = a.circular_block_indices(rng, 7, 3, 50)
        self.assertEqual(idx.shape, (50, 7))
        self.assertTrue(((idx >= 0) & (idx < 7)).all())
        # Dans un bloc, chaque indice suit le précédent, modulo n.
        self.assertTrue((((idx[:, 1:3] - idx[:, 0:2]) % 7) == 1).all())

    def test_bloc_plus_long_que_la_serie(self):
        idx = a.circular_block_indices(np.random.default_rng(1), 4, 10, 5)
        self.assertEqual(idx.shape, (5, 4))

    def test_poids_egal_des_observations_donc_moyenne_conservee(self):
        # Le repli circulaire donne le même poids aux extrémités, la moyenne bootstrap reste la moyenne.
        values = np.r_[np.full(30, 5.0), np.zeros(70)]
        idx = a.circular_block_indices(np.random.default_rng(2), 100, 10, 40000)
        self.assertAlmostEqual(float(values[idx].mean()), 1.5, delta=0.02)

    def test_graine_fixe_reproductible_et_graine_differente_change(self):
        values = np.random.default_rng(3).normal(0, 1, 120)
        self.assertEqual(a.block_ci(values, 10, 2000, [7, 1]), a.block_ci(values, 10, 2000, [7, 1]))
        self.assertNotEqual(a.block_ci(values, 10, 2000, [7, 1]), a.block_ci(values, 10, 2000, [8, 1]))

    def test_lots_indifferents_a_la_taille_du_tirage(self):
        values = np.random.default_rng(3).normal(0, 1, 50)
        lo, hi = a.block_ci(values, 5, 5001, 11)  # au-dessus d'un lot, le dernier est partiel
        self.assertLess(lo, values.mean())
        self.assertGreater(hi, values.mean())

    def test_dependance_elargit_l_intervalle(self):
        # Séries de 10 valeurs de même signe : les blocs doivent voir un intervalle plus large que l'iid.
        rng = np.random.default_rng(5)
        values = np.repeat(rng.choice([-1.0, 1.0], 40), 10)
        lo_b, hi_b = a.block_ci(values, 10, 20000, 1)
        lo_i, hi_i = a.iid_ci(values, 20000, 2)
        self.assertGreater(hi_b - lo_b, 2.0 * (hi_i - lo_i))

    def test_grappes_a_la_main(self):
        # Deux grappes de moyennes 0 et 2, tailles égales : l'estimateur ne prend que 0, 1 ou 2.
        values = np.array([0.0, 0.0, 2.0, 2.0])
        lo, hi, count = a.cluster_ci(values, np.array([1, 1, 2, 2]), 4000, 3)
        self.assertEqual(count, 2)
        self.assertEqual((lo, hi), (0.0, 2.0))

    def test_grappes_tailles_differentes_estimateur_ratio(self):
        lo, hi, _ = a.cluster_ci(np.array([1.0, 1.0, 1.0, 1.0]), np.array([1, 1, 1, 2]), 500, 3)
        self.assertEqual((lo, hi), (1.0, 1.0))

    def test_episodes_a_la_main(self):
        df = a.prepare_trades([
            trade("2021-01-01", "2021-01-05", 1.0, pair="A"),
            trade("2021-01-03", "2021-01-10", 1.0, pair="B"),  # chevauche A
            trade("2021-01-09", "2021-01-12", 1.0, pair="C"),  # chevauche B, donc même épisode
            trade("2021-01-12", "2021-01-13", 1.0, pair="D"),  # ouvert à la fin de l'épisode : nouveau
            trade("2021-01-20", "2021-01-21", 1.0, pair="E"),
        ])
        self.assertEqual(a.episode_labels(df).tolist(), [0, 0, 0, 1, 2])

    def test_force_exit_retire_de_l_esperance(self):
        df = a.prepare_trades([
            trade("2021-01-01", "2021-01-02", 50.0, pair="A", stake=1000.0),
            trade("2021-01-03", "2021-01-04", -50.0, pair="B", stake=1000.0),
            trade("2021-01-05", "2021-01-06", 500.0, pair="C", stake=1000.0, exit_reason="force_exit"),
        ])
        out = a.trade_statistics(df, 10000.0, 0.005, 50, 0)
        self.assertEqual(out["trades_force_exit"], 1)
        self.assertAlmostEqual(out["pnl_force_exit"], 500.0)
        r = a.r_multiples(df, 10000.0, 0.005)[0]
        self.assertAlmostEqual(out["esperance_hors_force_exit_R"], r[:2].mean())
        self.assertAlmostEqual(out["esperance_R"], r.mean())

    def test_intervalle_iid_historique_inchange(self):
        # Les méthodes par blocs ont leur propre graine : le tirage historique à graine 0 ne bouge pas.
        df = a.prepare_trades([trade(f"2021-01-{i:02d}", f"2021-01-{i + 1:02d}", 10.0 * (-1) ** i, pair="A")
                               for i in range(1, 20)])
        r = a.r_multiples(df, 10000.0, 0.005)[0]
        rng = np.random.default_rng(0)
        boot = rng.choice(r, (300, len(r))).mean(1)
        out = a.trade_statistics(df, 10000.0, 0.005, 300, 0)
        self.assertEqual(out["ic90_bas"], float(np.percentile(boot, 5)))
        a.dependence_intervals(df, 10000.0, 0.005, 300, 1, 5)
        self.assertEqual(a.trade_statistics(df, 10000.0, 0.005, 300, 0)["ic90_bas"], out["ic90_bas"])

    def test_intervalles_graine_fixe_pour_chaque_methode(self):
        df = a.prepare_trades([trade(f"2021-01-{i:02d}", f"2021-01-{i + 1:02d}", 10.0 * i * (-1) ** i, pair="A")
                               for i in range(1, 25)])
        one = a.dependence_intervals(df, 10000.0, 0.005, 400, 9, 5)
        self.assertEqual(one, a.dependence_intervals(df, 10000.0, 0.005, 400, 9, 5))
        other = a.dependence_intervals(df, 10000.0, 0.005, 400, 10, 5)
        for method in ("iid", "blocs"):  # une seule grappe de mois ici : ces bornes-là restent constantes
            self.assertNotEqual(one[method]["bas"], other[method]["bas"], method)
        self.assertNotEqual(one["iid"]["bas"], one["blocs"]["bas"])

    def test_intervalles_moins_de_deux_trades(self):
        df = a.prepare_trades([trade("2021-01-01", "2021-01-02", 10.0)])
        self.assertEqual(a.dependence_intervals(df, 10000.0, 0.005, 100, 1, 5)["statut"], "non_calculable")


class MonteCarloParBlocs(unittest.TestCase):
    def test_rendements_constants_positifs_aucun_drawdown(self):
        q = a.block_drawdown_quantiles(np.full(100, 0.01), 30, 3000, 1)
        self.assertEqual(q["dd_95"], 0.0)

    def test_rendements_constants_negatifs_a_la_main(self):
        q = a.block_drawdown_quantiles(np.full(10, -0.01), 3, 2500, 1)
        self.assertAlmostEqual(q["dd_95"], 1 - 0.99 ** 10)

    def test_bloc_conserve_une_serie_de_pertes_groupees(self):
        # 30 pertes groupées : les blocs de 30 jours gardent le creux, un tirage iid le disperse.
        ret = np.r_[np.full(30, -0.01), np.full(270, 0.002)]
        blocs = a.block_drawdown_quantiles(ret, 30, 3000, 1)["dd_50"]
        iid = a.block_drawdown_quantiles(ret, 1, 3000, 1)["dd_50"]
        self.assertGreater(blocs, iid)

    def test_reproductible(self):
        ret = np.random.default_rng(1).normal(0, 0.01, 200)
        self.assertEqual(a.block_drawdown_quantiles(ret, 30, 2000, [5, 4]), a.block_drawdown_quantiles(ret, 30, 2000, [5, 4]))


class SemestresReevalues(unittest.TestCase):
    def setUp(self):
        days = pd.date_range("2021-06-01", "2021-07-10", freq="D", tz="UTC")
        self.closes = {"A": pd.Series(np.linspace(100.0, 139.0, len(days)), index=days)}
        self.trades = [trade("2021-06-10", "2021-07-05", 300.0, pair="A", amount=10.0, open_rate=100.0)]
        self.df = a.prepare_trades(self.trades)
        self.start, self.end = days[0], days[-1]

    def test_colonne_reevaluee_et_decomptes(self):
        real = a.daily_series(self.df, 10000.0, self.start, self.end)
        marked = a.marked_series(self.df, 10000.0, self.start, self.end, self.closes)
        sem = a.semester_breakdown(self.df, real, 10000.0, 0.005, marked)
        s1, s2 = sem["semestres"]
        latent_30_juin = 10.0 * (self.closes["A"].loc["2021-06-30 00:00:00+00:00"] - 100.0)
        self.assertAlmostEqual(s1["pnl"], 0.0)
        self.assertAlmostEqual(s1["pnl_reevalue"], latent_30_juin)
        self.assertAlmostEqual(s2["pnl_reevalue"], 300.0 - latent_30_juin)
        self.assertAlmostEqual(s1["pnl_reevalue"] + s2["pnl_reevalue"], s1["pnl"] + s2["pnl"])
        self.assertEqual((sem["n_semestres"], sem["n_semestres_hors_partiel"]), (2, 0))
        self.assertEqual((sem["n_positifs"], sem["n_positifs_reevalue"], sem["n_positifs_hors_partiel"]), (1, 2, 0))
        self.assertFalse(s1["sharpe_significatif"])

    def test_sans_serie_reevaluee(self):
        real = a.daily_series(self.df, 10000.0, self.start, self.end)
        sem = a.semester_breakdown(self.df, real, 10000.0, 0.005)
        self.assertIsNone(sem["n_positifs_reevalue"])
        self.assertIsNone(sem["semestres"][0]["pnl_reevalue"])


class BoutEnBoutReevalue(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.pair = "BTC/USDT:USDT"
        write_candles(self.dir, self.pair, "2021-01-01", [100 + i for i in range(31)])
        self.trades = [
            trade("2021-01-05", "2021-01-10", 40.0, pair=self.pair, amount=10.0, open_rate=104.0, funding=-1.0),
            trade("2021-01-12", "2021-01-14", -30.0, pair=self.pair, amount=10.0, open_rate=111.0, is_short=True, funding=0.5),
            trade("2021-01-20", "2021-01-31", 90.0, pair=self.pair, amount=10.0, open_rate=119.0, exit_reason="force_exit", funding=-2.0),
        ]
        self.path = self.dir / "export.json"
        self.path.write_text(json.dumps(results_payload(self.trades)))
        self.argv = [str(self.path), "--out", str(self.dir), "--sims", "100", "--data-dir", str(self.dir)]

    def tearDown(self):
        self._tmp.cleanup()

    def test_rapport_complet_et_libelle(self):
        rep, stdout = run_quiet(self.argv + ["--essai", "E05"])
        self.assertEqual(rep["avertissements"], [])
        self.assertEqual(rep["metriques_reevaluees"]["statut"], "calcule")
        self.assertEqual(rep["monte_carlo_blocs"]["base"], "reevaluee")
        self.assertEqual(rep["intervalles_dependance"]["statut"], "calcule")
        self.assertEqual(rep["intervalles_dependance"]["tirages"], 500)
        self.assertEqual(rep["execution"]["seed_blocs"], a.SEED_BLOCS)
        self.assertEqual(rep["trades"]["trades_force_exit"], 1)
        self.assertAlmostEqual(rep["metriques_reevaluees"]["rendement_total"], rep["metriques_quotidiennes"]["rendement_total"])
        md = (self.dir / "E05_metriques.md").read_text(encoding="utf-8")
        self.assertIn("base principale", md)
        self.assertIn("base de comparaison", md)
        self.assertIn("P&L réévalué", md)
        self.assertIn("non significatif", md)  # un mois seulement dans le semestre
        self.assertIn("Espérance hors force_exit", stdout)
        self.assertIn("DSR principal", stdout)
        json.loads((self.dir / "E05_metriques.json").read_text(encoding="utf-8"))

    def test_chemin_des_bougies_relatif_au_script(self):
        self.assertEqual(a.display_path(a.DEFAULT_DATA), str(Path("user_data") / "data" / "binance" / "futures"))
        self.assertEqual(a.display_path("/ailleurs/bougies"), "/ailleurs/bougies")

    def test_valeurs_par_defaut_de_la_procedure(self):
        args = a.parse_args(["x.zip"])[1]
        self.assertGreaterEqual(args.sims_blocs, 50000)
        self.assertEqual((args.seed_blocs, args.bloc_trades, args.bloc_jours), (20261101, 10, 30))

    def test_dsr_reevalue_utilise_sa_propre_variance(self):
        registry = self.dir / "reg.json"
        registry.write_text(json.dumps({"essais": [
            {"id": "A", "sharpe_quotidien": 0.01, "sharpe_quotidien_reevalue": 0.02},
            {"id": "B", "sharpe_quotidien": 0.03, "sharpe_quotidien_reevalue": 0.08},
            {"id": "C", "sharpe_quotidien": None, "sharpe_quotidien_reevalue": None}]}))
        rep, _ = run_quiet(self.argv + ["--essai", "E06", "--registry-json", str(registry)])
        self.assertAlmostEqual(rep["dsr"]["v_sr_quotidien"], 0.0002)
        self.assertAlmostEqual(rep["dsr_reevalue"]["v_sr_quotidien"], 0.0018)
        self.assertEqual((rep["dsr"]["n_essais"], rep["dsr_reevalue"]["n_essais"]), (3, 3))
        self.assertEqual(rep["dsr_reevalue"]["statut"], "calcule")
        self.assertNotEqual(rep["dsr"]["dsr"], rep["dsr_reevalue"]["dsr"])
        m = rep["metriques_reevaluees"]
        sr0 = a.expected_max_sharpe(0.0018, 3)
        self.assertAlmostEqual(rep["dsr_reevalue"]["dsr"], a.probabilistic_sharpe(
            m["sharpe_quotidien"], sr0, m["T"], m["g3_asymetrie"], m["g4_kurtosis"]))

    def test_options_sr_var_reevalue(self):
        rep, _ = run_quiet(self.argv + ["--essai", "E07", "--n-trials", "5", "--sr-var", "0.001", "--sr-var-reevalue", "0.002"])
        self.assertEqual(rep["dsr_reevalue"]["v_sr_quotidien"], 0.002)
        registry = self.dir / "r.json"
        registry.write_text(json.dumps({"essais": []}))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            a.main(self.argv + ["--essai", "E08", "--sr-var-reevalue", "0.002", "--registry-json", str(registry)])

    def test_aucun_trade_ne_casse_pas_la_reevaluation(self):
        path = self.dir / "vide.json"
        path.write_text(json.dumps(results_payload([])))
        rep, _ = run_quiet([str(path), "--essai", "E10", "--out", str(self.dir), "--sims", "10", "--data-dir", str(self.dir)])
        self.assertEqual(rep["metriques_reevaluees"]["statut"], "calcule")
        self.assertIsNone(rep["metriques_reevaluees"]["sharpe_quotidien"])
        self.assertEqual(rep["dsr_reevalue"]["statut"], "non_calculable")

    def test_agregation_exclut_les_lignes_hors_n(self):
        results = self.dir / "res"
        run_quiet(self.argv[:1] + ["--out", str(results), "--sims", "10", "--data-dir", str(self.dir), "--essai", "E01"])
        csv_path = self.dir / "REGISTRE.csv"
        csv_path.write_text("id_essai,statut\nE01,exécuté\nE10,verrouillé\nCTRL-FORMAT,hors N (contrôles de format)\n", encoding="utf-8")
        target = self.dir / "agrege.json"
        run_quiet(["--agreger-registre", str(results), "--registre-csv", str(csv_path), "--registry-json", str(target)])
        reg = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in reg["essais"]], ["E01", "E10"])
        self.assertIsNotNone(reg["essais"][0]["sharpe_quotidien_reevalue"])


class DatesPandas(unittest.TestCase):
    def test_plage_depuis_timerange_ouvert(self):
        start, end = a.resolve_range(None, None, {"timerange": "20210101-", "backtest_end": "2021-02-01 00:00:00"})
        self.assertEqual((start, end), (pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2021-02-01", tz="UTC")))

    def test_options_prioritaires(self):
        start, end = a.resolve_range("20200101", "20200105", {"timerange": "20210101-20210201"})
        self.assertEqual(end - start, pd.Timedelta(days=4))


if __name__ == "__main__":
    unittest.main()
