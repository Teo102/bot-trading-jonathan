"""Tests synthétiques du papier à 7 cohortes de STRAT-06-bis. Aucun réseau, aucune donnée de marché.
Exécution : python3 -B test_cohortes06.py"""
import sys

sys.dont_write_bytecode = True
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import collecte_papier06 as cp  # noqa: E402
import moteur_xsmom as m  # noqa: E402
import paper_cohortes06 as pc6  # noqa: E402
import test_moteur_synthetique as ts  # noqa: E402
import test_strat06 as t6  # noqa: E402
import univers_cotations as uc  # noqa: E402

PC = uc.ParamsCotation(liquidite_min=0.0)
P = m.Params()  # frais, glissements et stop de la v1


def marche(graine=11, **kw):
    j, h, f, cot = t6.marche_cotations(graine, **kw)
    return j, h, f, cot


class EgaliteAvecLaV1(unittest.TestCase):
    def test_cohorte_rend_le_backtest_sur_semaines_closes(self):
        j, h, f, _ = marche(11)
        lun = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=40))[:12]
        cible = uc.fabrique_cible(PC, t6.DEBUT)
        sem_v1, lig_v1 = m.backtest(j, h, f, lun, P, notionnel=1 / 12, fonction_cible=cible)
        sem_c, lig_c = pc6.jouer_cohorte(j, h, f, lun, P, 1 / 12, uc.fabrique_cible(PC, t6.DEBUT), h_eval=None)
        closes = sem_c[~sem_c["provisoire"]]
        self.assertEqual(len(closes), len(sem_v1))
        self.assertGreater((sem_v1["shorts"] != "").sum(), 3)          # le test porte sur des semaines jouées
        n = len(sem_v1)
        for col in ("pnl_prix", "financement", "long", "short"):
            np.testing.assert_allclose(closes[col].to_numpy(), sem_v1[col].to_numpy(), rtol=0, atol=1e-12)
        # seule différence : le solde final imputé par le backtest à sa dernière semaine
        np.testing.assert_allclose(closes["cout"].to_numpy()[: n - 1], sem_v1["cout"].to_numpy()[: n - 1], atol=1e-12)
        self.assertGreaterEqual(sem_v1["cout"].iloc[-1], closes["cout"].iloc[-1] - 1e-15)
        self.assertEqual(list(closes["shorts"]), list(sem_v1["shorts"]))

    def test_stop_stresse_comme_stress_stops(self):
        j, h, f, _ = marche(12)
        s = [c for c in h["open"].columns if c != "BTC"][0]
        t_in = h["open"][s].first_valid_index() + pd.Timedelta(hours=5)
        px = h["open"][s][t_in]
        h2 = {k: v.copy() for k, v in h.items()}
        hs = t_in + pd.Timedelta(hours=3)
        h2["mark_high"].loc[hs, s] = px * 1.45            # le plus haut de marque traverse le stop de 30 %
        h2["open"].loc[hs, s] = px * 1.20
        r = m.jouer_ligne(h2, None, s, -1, t_in, t_in + pd.Timedelta(days=2), 1 / 84, P)
        self.assertEqual(r["statut"], "stop")
        x = pc6.stresser_stop(r, h2, P, 1 / 84)
        niveau = px * 1.30
        attendu = 0.5 * (niveau + px * 1.45) * (1 + P.glissement_stop)     # formule du mode 1 de stress_stops.py
        self.assertAlmostEqual(x["sortie"], attendu, places=9)
        self.assertLess(x["pnl_prix"], r["pnl_prix"])                     # le stress ne peut que dégrader
        self.assertAlmostEqual(r["sortie"], niveau * (1 + P.glissement_stop), places=9)


class Calendrier(unittest.TestCase):
    def test_sept_cohortes_decalees(self):
        j0 = pd.Timestamp("2026-12-01")
        h = pd.Timestamp("2026-12-15 01:00")
        d = {c: pc6.dates_cohorte(j0, c, h) for c in range(7)}
        self.assertEqual(d[0], [pd.Timestamp("2026-12-01"), pd.Timestamp("2026-12-08"), pd.Timestamp("2026-12-15")])
        self.assertEqual(d[6], [pd.Timestamp("2026-12-07"), pd.Timestamp("2026-12-14")])
        self.assertEqual(pc6.dates_cohorte(j0, 1, pd.Timestamp("2026-12-02 00:59")), [])   # exécution pas encore faite
        self.assertEqual(sorted(t.weekday() for c in range(7) for t in d[c][:1]), list(range(7)))

    def test_montee_en_charge_et_notionnel(self):
        j, h, f, _ = marche(13)
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        h_eval = j0 + pd.Timedelta(days=20, hours=1)
        res = pc6.calculer(j, h, f, j0, h_eval, P, PC, dernier_jour_clos=j["volume"].index.max())
        b = res.semaines[res.semaines["serie"] == "base"]
        premieres = b.groupby("cohorte")["t_in"].min().sort_index()
        self.assertEqual(list((premieres - premieres.iloc[0]).dt.days), list(range(7)))
        lig = res.lignes[(res.lignes["serie"] == "base") & (res.lignes["statut"] != "absent")]
        sh = lig[lig["sens"] < 0]
        self.assertTrue(np.allclose(sh["notionnel"], 1 / 84))
        for (c, d), g in lig.groupby(["cohorte", "lundi"]):
            n = (g["sens"] < 0).sum()
            btc = g[g["symbole"] == "BTC"]
            if n:
                self.assertAlmostEqual(float(btc["notionnel"].iloc[0]), n / 84, places=12)
        self.assertEqual(len(res.quotidien), 20)


class EnDirect(unittest.TestCase):
    def test_pas_de_faux_delistage_le_jour_en_cours(self):
        j, h, f, _ = marche(14)
        dernier = j["volume"].index[-40]
        jj = {k: v.loc[v.index <= dernier] for k, v in j.items()}             # le jour en cours n'est pas clos
        hh = {k: v.loc[v.index < dernier + pd.Timedelta(hours=30)] for k, v in h.items()}
        _, hc, _, _ = m.couper_zombies(jj, hh, f)
        _, hv, _ = pc6.couper_zombies_vivants(jj, hh, f, dernier)
        s = "BTC"
        apres = hh["open"].index >= dernier + pd.Timedelta(days=1)
        self.assertTrue(hc["open"].loc[apres, s].isna().all())                # la coupe d'origine efface le jour en cours
        self.assertFalse(hv["open"].loc[apres, s].isna().any())               # pas la version en direct

    def test_semaine_ouverte_valorisee_sans_cout_de_sortie(self):
        j, h, f, _ = marche(15)
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        lun = [j0, j0 + pd.Timedelta(days=7)]
        h_eval = j0 + pd.Timedelta(days=10, hours=1)
        sem, lig = pc6.jouer_cohorte(j, h, f, lun, P, 1 / 84, uc.fabrique_cible(PC, t6.DEBUT), h_eval=h_eval)
        self.assertEqual(list(sem["provisoire"]), [False, True])
        ouv = lig[lig["provisoire"] & (lig["statut"] != "absent")]
        self.assertFalse((ouv["statut"] == "delistage").any())
        self.assertTrue(((ouv["statut"] == "semaine") | (ouv["statut"] == "stop")).all())

    def test_valorisation_quotidienne_continue(self):
        j, h, f, _ = marche(16)
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        h_eval = j0 + pd.Timedelta(days=15, hours=1)
        res = pc6.calculer(j, h, f, j0, h_eval, P, PC, dernier_jour_clos=j["volume"].index.max())
        q = res.quotidien.set_index("heure")
        # à l'heure d'évaluation, le cumul vaut la somme des semaines closes et ouvertes valorisées à cette heure
        for serie in ("base", "stressee"):
            s = res.semaines[res.semaines["serie"] == serie]
            self.assertAlmostEqual(q.loc[h_eval, serie], s["net"].sum(), places=12)
        self.assertTrue((q["stressee"] <= q["base"] + 1e-12).all())             # le stress ne peut que dégrader


class SignalManque(unittest.TestCase):
    def test_date_manquee_ni_rejouee_ni_remplacee(self):
        j, h, f, _ = marche(17)
        lun = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[:4]
        cible = uc.fabrique_cible(PC, t6.DEBUT)
        a, _ = pc6.jouer_cohorte(j, h, f, lun, P, 1 / 84, cible, None)
        b, lb = pc6.jouer_cohorte(j, h, f, lun, P, 1 / 84, uc.fabrique_cible(PC, t6.DEBUT), None, manquees={lun[1]})
        self.assertNotEqual(a.loc[1, "shorts"], "")
        self.assertEqual(b.loc[1, "shorts"], "")
        self.assertEqual(b.loc[1, "pnl_prix"], 0.0)
        self.assertGreater(b.loc[1, "cout"], 0.0)                               # les lignes précédentes sont soldées
        self.assertTrue(b.loc[1, "manquee"])

    def test_signaux_ecrits_a_l_heure_ou_non(self):
        j, h, f, _ = marche(18)
        tmp = Path(tempfile.mkdtemp())
        try:
            j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
            pc6.ecrire_signaux(j, PC, P, j0, j0 + pd.Timedelta(minutes=10), tmp)        # cohorte 0 à l'heure
            pc6.ecrire_signaux(j, PC, P, j0, j0 + pd.Timedelta(days=1, hours=3), tmp)   # cohorte 1 écrite après 01:00
            s = pd.read_csv(tmp / "signaux.csv", dtype=str)
            self.assertEqual(list(s["a_l_heure"]), ["oui", "non"])
            self.assertEqual(pc6.lire_manquees(tmp), {1: {j0 + pd.Timedelta(days=1)}})
            r = pc6.ecrire_signaux(j, PC, P, j0, j0 + pd.Timedelta(days=1, hours=5), tmp)   # rien de réécrit
            self.assertEqual(len(pd.read_csv(tmp / "signaux.csv")), 2)
            self.assertEqual(r["ecarts"], 0)                      # l'heure de réécriture n'est pas un écart (14/11/2026)
            self.assertFalse((tmp / "incidents.csv").exists())
            faux = pd.read_csv(tmp / "signaux.csv", dtype=str, keep_default_na=False)
            faux.loc[0, "shorts"] = "S99"
            faux.to_csv(tmp / "signaux.csv", index=False)
            self.assertEqual(pc6.ecrire_signaux(j, PC, P, j0, j0 + pd.Timedelta(days=1, hours=6), tmp)["ecarts"], 1)  # un vrai écart reste signalé
        finally:
            shutil.rmtree(tmp)


class SerieDebridee(unittest.TestCase):
    CD = {"liquidite_min_usdt": 10e6, "seuil_taille_pleine_usdt": 20e6, "poids_demi_taille": 0.5,
          "declaree_utc": "2026-11-18T14:00:00Z", "jour_0": "2026-11-19", "statut": "active"}

    def jours_volumes(self, medianes: dict, cotation: pd.Timestamp, debut="2022-01-01", fin="2022-06-30"):
        idx = pd.date_range(debut, fin, freq="D")
        vol = pd.DataFrame({"BTC": 1e9, "VIEUXUSDT": 5e8}, index=idx)
        for s, v in medianes.items():
            vol[s] = 0.0
            vol.loc[vol.index >= cotation, s] = v
        return {"volume": vol, "close": pd.DataFrame(1.0, index=idx, columns=vol.columns)}

    def test_demi_taille_et_couverture(self):
        L = pd.Timestamp("2022-03-01")
        j = self.jours_volumes({"AUSDT": 25e6, "BUSDT": 15e6, "CUSDT": 5e6}, L)
        t = L + pd.Timedelta(days=20)
        pcd = uc.ParamsCotation(liquidite_min=10e6)
        poids, n = pc6.fabrique_cible_debridee(pcd, pd.Timestamp("2022-01-01"))(j, t, P)
        self.assertEqual(poids, {"AUSDT": -1.0, "BUSDT": -0.5, "BTC": 1.5})     # C sous 10 M exclu, BTC = somme des poids
        off, _ = uc.fabrique_cible(uc.ParamsCotation(liquidite_min=20e6), pd.Timestamp("2022-01-01"))(j, t, P)
        self.assertEqual(off, {"AUSDT": -1.0, "BTC": 1.0})                       # la série officielle ne voit que A
        j2 = self.jours_volumes({"AUSDT": 25e6, "DUSDT": 30e6}, L)               # sans nom entre 10 et 20 M : même cible
        a, _ = pc6.fabrique_cible_debridee(pcd, pd.Timestamp("2022-01-01"))(j2, t, P)
        b, _ = uc.fabrique_cible(uc.ParamsCotation(liquidite_min=20e6), pd.Timestamp("2022-01-01"))(j2, t, P)
        self.assertEqual(a, b)

    def test_btc_sans_financement_et_officielle_inchangee(self):
        j, h, f, _ = marche(22)
        f = f.copy(); f["BTC"] = 0.0004                                          # financement BTC non nul
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        h_eval = j0 + pd.Timedelta(days=12, hours=1)
        avant = pc6.calculer(j, h, f, j0, h_eval, P, PC, dernier_jour_clos=j["volume"].index.max())
        cd = dict(self.CD, liquidite_min_usdt=0.0, seuil_taille_pleine_usdt=0.0)   # synthétique : tous les noms en taille pleine
        d = pc6.calculer_debridee(j, h, f, j0, h_eval, P, PC, cd, dernier_jour_clos=j["volume"].index.max())
        apres = pc6.calculer(j, h, f, j0, h_eval, P, PC, dernier_jour_clos=j["volume"].index.max())
        pd.testing.assert_frame_equal(avant.semaines, apres.semaines)            # la série officielle ne bouge pas
        lo = avant.lignes[(avant.lignes["serie"] == "base") & (avant.lignes["statut"] != "absent")]
        ld = d.lignes[(d.lignes["serie"] == "debridee") & (d.lignes["statut"] != "absent")]
        self.assertTrue((lo[lo["symbole"] == "BTC"]["financement"] != 0).any())
        self.assertTrue((ld[ld["symbole"] == "BTC"]["financement"] == 0).all())  # couverture au comptant
        k = ["cohorte", "lundi", "symbole"]
        m_ = lo[lo["symbole"] != "BTC"].merge(ld[ld["symbole"] != "BTC"], on=k, suffixes=("_o", "_d"))
        self.assertGreater(len(m_), 0)
        np.testing.assert_allclose(m_["financement_o"], m_["financement_d"])     # les shorts gardent leur financement
        np.testing.assert_allclose(m_["pnl_prix_o"], m_["pnl_prix_d"])
        self.assertEqual(set(d.quotidien.columns), {"heure", "debridee", "debridee_stressee"})

    def test_fichiers_separes_et_jour0_propre(self):
        j, h, f, _ = marche(23)
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        cd = dict(self.CD, liquidite_min_usdt=0.0, seuil_taille_pleine_usdt=0.0, jour_0=str((j0 + pd.Timedelta(days=3)).date()))
        h_eval = j0 + pd.Timedelta(days=12, hours=1)
        tmp = Path(tempfile.mkdtemp())
        try:
            off = pc6.calculer(j, h, f, j0, h_eval, P, PC, dernier_jour_clos=j["volume"].index.max())
            pc6.ecrire(off, tmp, h_eval, 10000.0, 1 / 84)
            avant = {x.name: x.read_bytes() for x in tmp.iterdir()}
            d = pc6.calculer_debridee(j, h, f, cd["jour_0"], h_eval, P, PC, cd, dernier_jour_clos=j["volume"].index.max())
            e = pc6.ecrire_debridee(d, tmp, h_eval, cd, 1 / 84)
            for nom, contenu in avant.items():
                self.assertEqual((tmp / nom).read_bytes(), contenu, nom)            # aucun fichier officiel touché
            self.assertTrue((tmp / "serie_debridee.csv").exists())
            self.assertGreaterEqual(d.semaines["t_in"].min(), pd.Timestamp(cd["jour_0"]) + pd.Timedelta(hours=1))   # rien avant son jour 0
            self.assertEqual(len(e["cohortes_ouvertes"]), 7)
            etat = {"cumul": {"base": 0.0, "stressee": 0.0}, "incidents_nouveaux": 0, "cohortes_ouvertes": []}
            pc6.journal_md(tmp, etat, {}, h_eval + pd.Timedelta(hours=1), "compte", h_eval, e)
            self.assertIn("Série débridée (fantôme", (tmp / "JOURNAL_COHORTES.md").read_text())
        finally:
            shutil.rmtree(tmp)

    def test_signal_debride_marque_les_demi_tailles(self):
        L = pd.Timestamp("2022-03-01")
        j = self.jours_volumes({"AUSDT": 25e6, "BUSDT": 15e6}, L)
        tmp = Path(tempfile.mkdtemp())
        try:
            pcd = uc.ParamsCotation(liquidite_min=10e6)
            t = L + pd.Timedelta(days=20)
            pc6.ecrire_signaux(j, pcd, P, t, t + pd.Timedelta(minutes=5), tmp,
                               cible=pc6.fabrique_cible_debridee(pcd, pd.Timestamp("2022-01-01")), nom="signaux_debridee.csv")
            s = pd.read_csv(tmp / "signaux_debridee.csv", dtype=str, keep_default_na=False)
            self.assertEqual(s.loc[0, "shorts"], "AUSDT,BUSDT:0.5")
            self.assertEqual(cp.noms_a_suivre(tmp / "signaux_debridee.csv"), {"AUSDT", "BUSDT:0.5"})
            self.assertFalse((tmp / "signaux.csv").exists())
        finally:
            shutil.rmtree(tmp)


class JournalMarkdown(unittest.TestCase):
    def test_entree_du_jour_apres_l_execution_seulement(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            pd.DataFrame([{"cohorte": 0, "date": "2026-11-14T00:00:00Z", "ecrit_utc": "2026-11-14T00:05:00Z", "shorts": "",
                           "a_l_heure": "oui"}]).to_csv(tmp / "signaux.csv", index=False)
            etat = {"cumul": {}, "incidents_nouveaux": 0, "cohortes_ouvertes": []}
            m0 = pd.Timestamp("2026-11-14 00:05")
            pc6.journal_md(tmp, etat, {}, m0, "a_blanc", h_eval=pd.Timestamp("2026-11-13 23:00"))
            self.assertFalse((tmp / "JOURNAL_COHORTES.md").exists())            # 00:05 : exécution pas encore faite
            pc6.journal_md(tmp, etat, {}, pd.Timestamp("2026-11-14 02:05"), "a_blanc", h_eval=pd.Timestamp("2026-11-14 01:00"))
            t = (tmp / "JOURNAL_COHORTES.md").read_text()
            self.assertIn("## 2026-11-14", t)
            self.assertIn("aucun nom éligible, semaine vide", t)
            pc6.journal_md(tmp, etat, {}, pd.Timestamp("2026-11-14 03:05"), "a_blanc", h_eval=pd.Timestamp("2026-11-14 02:00"))
            self.assertEqual((tmp / "JOURNAL_COHORTES.md").read_text().count("## 2026-11-14"), 1)
        finally:
            shutil.rmtree(tmp)


class AjoutSeul(unittest.TestCase):
    def test_journal_jamais_reecrit_et_ecart_signale(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            jl = pc6.JournalAjout(tmp / "x.csv", ["k", "v"], ["k"])
            self.assertEqual(jl.ajouter([{"k": "a", "v": 1.0}, {"k": "b", "v": 2.0}]), (2, []))
            n, e = jl.ajouter([{"k": "a", "v": 1.5}, {"k": "c", "v": 3.0}])
            self.assertEqual(n, 1)
            self.assertEqual(e[0]["colonne"], "v")
            self.assertEqual(list(jl.lire()["v"]), ["1.0", "2.0", "3.0"])          # la valeur écrite reste
        finally:
            shutil.rmtree(tmp)


class FauxHttp:
    """Répond comme l'API Binance Futures sur un petit marché fabriqué."""

    def __init__(self, maintenant):
        self.maintenant, self.appels = maintenant, 0

    def get(self, chemin, params=None):
        self.appels += 1
        if chemin == "/fapi/v1/exchangeInfo":
            return {"symbols": [{"symbol": "BTCUSDT", "quoteAsset": "USDT", "contractType": "PERPETUAL", "underlyingType": "COIN"},
                                {"symbol": "AAAUSDT", "quoteAsset": "USDT", "contractType": "PERPETUAL", "underlyingType": "COIN"},
                                {"symbol": "XAUUSDT", "quoteAsset": "USDT", "contractType": "PERPETUAL", "underlyingType": "COMMODITY"}]}
        if chemin in ("/fapi/v1/klines", "/fapi/v1/markPriceKlines"):
            pas = pd.Timedelta(days=1) if params["interval"] == "1d" else pd.Timedelta(hours=1)
            debut = pd.Timestamp(params["startTime"], unit="ms")
            premiere = pd.Timestamp("2026-10-01") if params["symbol"] == "AAAUSDT" else pd.Timestamp("2019-09-08")
            t = max(debut, premiere).ceil("D" if pas == pd.Timedelta(days=1) else "h")
            out = []
            while t <= self.maintenant and len(out) < params["limit"]:
                o = cp.ms(t)
                out.append([o, "10", "11", "9", "10.5", "1", o + int(pas.total_seconds() * 1000) - 1, "1000000"])
                t += pas
            return out
        if chemin == "/fapi/v1/fundingRate":
            debut = pd.Timestamp(params["startTime"], unit="ms").ceil("8h")
            return [{"fundingTime": cp.ms(t) + 3, "fundingRate": "0.0001"} for t in pd.date_range(debut, self.maintenant, freq="8h")][: params["limit"]]
        raise AssertionError(chemin)


class Collecte(unittest.TestCase):
    def test_bougies_closes_ajout_seul_et_format_du_moteur(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            now = pd.Timestamp("2026-11-13 10:30")
            c = cp.Collecteur(tmp, FauxHttp(now))
            self.assertEqual(c.symboles(), ["AAAUSDT", "BTCUSDT"])                 # contrat non crypto écarté
            n = c.maj_jours(now)
            self.assertGreater(n, 2000)
            jours = c.charger_jours()
            self.assertIn("BTC", jours["volume"].columns)                           # BTCUSDT renommé comme dans run_essai06
            self.assertEqual(jours["volume"].index.max(), pd.Timestamp("2026-11-12"))   # le jour en cours n'est pas écrit
            self.assertEqual(jours["volume"]["AAAUSDT"].first_valid_index(), pd.Timestamp("2026-10-01"))
            self.assertEqual(c.maj_jours(now), 0)                                    # rien de nouveau
            c.maj_heures(["BTCUSDT", "AAAUSDT"], pd.Timestamp("2026-11-12"), now)
            hh = c.charger_heures()
            self.assertEqual(hh["open"].index.max(), pd.Timestamp("2026-11-13 09:00"))   # heure 10:00 pas close
            c.maj_financement(["BTCUSDT"], pd.Timestamp("2026-11-12"), now)
            self.assertEqual(list(c.charger_financement().index[:1]), [pd.Timestamp("2026-11-12 00:00")])  # arrondi à la minute
            jc = pd.read_csv(tmp / "journal_collecte.csv")
            self.assertEqual(len(jc), 3)
            self.assertEqual(len(jc["sha256"].iloc[0]), 64)
        finally:
            shutil.rmtree(tmp)

    def test_selection_identique_collecte_et_archives(self):
        """Mêmes volumes au format long (collecte) ou large (archives) : même sélection à chaque date."""
        j, h, f, _ = marche(19)
        tmp = Path(tempfile.mkdtemp())
        try:
            long = j["volume"].stack().rename("volume").reset_index()
            long.columns = ["date", "symbole", "volume"]
            long["close"] = 1.0
            long["lu_utc"] = "2026-11-13T00:00:00Z"
            long["date"] = long["date"].dt.strftime("%Y-%m-%d")
            long[cp.COLS["jours"]].to_csv(tmp / "jours.csv", index=False)
            jc = cp.Collecteur(tmp).charger_jours()
            cible = uc.fabrique_cible(PC, t6.DEBUT)
            cible2 = uc.fabrique_cible(PC, t6.DEBUT)
            ref = {k: v.loc[jc["volume"].index.min():] for k, v in j.items()}
            for t in ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=30))[:20]:
                self.assertEqual(cible(ref, t, P)[0], cible2(jc, t, P)[0])
        finally:
            shutil.rmtree(tmp)


class RejeuEtVerdict(unittest.TestCase):
    def test_rejeu_signale_selection_et_prix(self):
        import rejeu_cohortes06 as rj
        j, h, f, _ = marche(20)
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        tmp = Path(tempfile.mkdtemp())
        try:
            pc6.ecrire_signaux(j, PC, P, j0, j0 + pd.Timedelta(minutes=10), tmp)
            sig = pd.read_csv(tmp / "signaux.csv", dtype=str, keep_default_na=False)
            self.assertEqual(rj.comparer_selections(j, sig, P, PC, j0, j0 + pd.Timedelta(days=7)), [])
            faux = sig.copy(); faux.loc[0, "shorts"] = "S99"
            e = rj.comparer_selections(j, faux, P, PC, j0, j0 + pd.Timedelta(days=7))
            self.assertEqual((len(e), e[0]["type"]), (1, "rejeu_selection"))
            s0 = [x for x in sig.loc[0, "shorts"].split(",") if x][0]
            lig = pd.DataFrame([{"serie": "base", "cohorte": 0, "lundi": pc6.iso(j0), "symbole": s0, "statut": "semaine",
                                 "entree": h["open"][s0][j0 + pd.Timedelta(hours=1)]}])
            self.assertEqual(rj.comparer_entrees(h, lig, j0, j0 + pd.Timedelta(days=7), 1e-4), [])
            lig.loc[0, "entree"] *= 1.001
            self.assertEqual(rj.comparer_entrees(h, lig, j0, j0 + pd.Timedelta(days=7), 1e-4)[0]["type"], "rejeu_entree")
        finally:
            shutil.rmtree(tmp)

    def test_decisions_du_verdict(self):
        import json as js
        import verdict_bis06 as vb
        cb = js.loads(pc6.CONFIG_BIS.read_text())
        j0 = pd.Timestamp("2027-01-01")
        q = lambda vals: pd.DataFrame({"heure": pd.date_range(j0 + pd.Timedelta(days=1, hours=1), periods=len(vals), freq="D"), "stressee": vals})
        vide = pd.DataFrame()
        e = vb.etat_verdict(cb, q([0.0, -0.2, -0.45]), vide, vide, j0, j0 + pd.Timedelta(days=21))
        self.assertTrue(e["arret_anticipe"]); self.assertTrue(e["decision"].startswith("rejet"))
        e = vb.etat_verdict(cb, q([0.01, 0.02]), vide, vide, j0, j0 + pd.Timedelta(days=70))
        self.assertTrue(e["decision"].startswith("en cours"))
        e = vb.etat_verdict(cb, q([0.01, -0.01]), vide, vide, j0, j0 + pd.Timedelta(weeks=27))
        self.assertEqual(e["decision"], "rejet au point d'étape")
        e = vb.etat_verdict(cb, q([0.01, 0.03]), vide, vide, j0, j0 + pd.Timedelta(weeks=53))
        self.assertEqual(e["decision"], "rejet au verdict")            # aucune semaine, aucune ligne : jamais favorable
        self.assertAlmostEqual(vb.drawdown(pd.Series([0.1, 0.05, 0.2, -0.1])), 0.3)

    def test_ecriture_complete_et_relance(self):
        j, h, f, _ = marche(21)
        j0 = ts.lundis(j, depuis=t6.DEBUT + pd.Timedelta(days=60))[0]
        h_eval = j0 + pd.Timedelta(days=12, hours=1)
        tmp = Path(tempfile.mkdtemp())
        try:
            res = pc6.calculer(j, h, f, j0, h_eval, P, PC, dernier_jour_clos=j["volume"].index.max())
            e1 = pc6.ecrire(res, tmp, h_eval, 10000.0, 1 / 84)
            self.assertEqual(e1["incidents_nouveaux"], 0)
            e2 = pc6.ecrire(res, tmp, h_eval, 10000.0, 1 / 84)               # relance : rien d'ajouté, aucun écart
            self.assertEqual(e2["ajouts"], {"semaines": 0, "lignes": 0, "jours": 0})
            self.assertEqual(e2["incidents_nouveaux"], 0)
            res2 = pc6.calculer(j, h, f, j0, h_eval + pd.Timedelta(days=3), P, PC, dernier_jour_clos=j["volume"].index.max())
            e3 = pc6.ecrire(res2, tmp, h_eval + pd.Timedelta(days=3), 10000.0, 1 / 84)
            self.assertEqual(e3["incidents_nouveaux"], 0)                    # le passé recalculé plus tard ne change pas
            self.assertGreater(e3["ajouts"]["jours"], 0)
            self.assertEqual(len(e3["cohortes_ouvertes"]), 7)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=1)
