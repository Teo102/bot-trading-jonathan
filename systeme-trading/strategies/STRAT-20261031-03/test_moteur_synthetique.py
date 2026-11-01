"""Tests synthétiques préalables de STRAT-20261031-03 (fiche § 1.7). Aucun prix de marché.

Exécution : python -B test_moteur_synthetique.py -v
Les données sont des marches aléatoires générées (graine fixe). Aucun essai du registre n'est consommé.
"""
import sys

sys.dont_write_bytecode = True

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import moteur_xsmom as m  # noqa: E402

DEBUT = pd.Timestamp("2022-01-01")


def marche(n_sym=40, jours=400, graine=1, vol_h=0.006, drift_resid=None, beta=None, debut=DEBUT, drift_btc=0.0):
    """Marches aléatoires 1 h log-normales. drift_resid : dérive horaire propre à chaque symbole
    (persistante sur toute la période) pour planter un momentum ; None = aucune dérive."""
    rng = np.random.default_rng(graine)
    idx = pd.date_range(debut, periods=jours * 24, freq="h")
    noms = ["BTC"] + [f"S{i:02d}" for i in range(n_sym)]
    f = rng.normal(drift_btc, vol_h, len(idx))
    beta = rng.uniform(0.6, 1.4, n_sym) if beta is None else beta
    lr = {"BTC": f}
    for i in range(n_sym):
        e = rng.normal(0, vol_h, len(idx))
        d = 0.0 if drift_resid is None else drift_resid[i]
        lr[f"S{i:02d}"] = beta[i] * f + e + d
    lr = pd.DataFrame(lr, index=idx)
    close = 100 * np.exp(lr.cumsum())
    open_ = close.shift(1).fillna(100.0)
    amp = np.abs(rng.normal(0, vol_h, close.shape))
    high = np.maximum(open_, close) * (1 + amp)
    low = np.minimum(open_, close) * (1 - amp)
    vol_h_usdt = pd.DataFrame(rng.lognormal(10, 0.5, close.shape), index=idx, columns=noms)
    heures = {"open": open_, "close": close, "mark_high": pd.DataFrame(high, index=idx, columns=noms),
              "mark_low": pd.DataFrame(low, index=idx, columns=noms)}
    jours_ = {"close": close.resample("D").last(), "volume": vol_h_usdt.resample("D").sum()}
    fin = pd.DataFrame(0.0, index=pd.date_range(debut, idx[-1], freq="8h"), columns=noms)
    return jours_, heures, fin


def lundis(jours, depuis=None):
    d = jours["close"].index
    lun = d[d.weekday == 0]
    depuis = depuis or d[0] + pd.Timedelta(days=100)
    return [t for t in lun if t >= depuis and t + pd.Timedelta(days=8) <= d[-1]]


def tronquer(jours, heures, fin, t):
    j = {k: v.loc[v.index < t] for k, v in jours.items()}
    h = {k: v.loc[v.index < t] for k, v in heures.items()}
    return j, h, fin.loc[fin.index < t]


P0 = m.Params(frais=0.0, glissement=0.0, glissement_stop=0.0)


class Troncature(unittest.TestCase):
    """Le signal à t reste identique après suppression de toutes les données postérieures."""

    def test_signal_identique_sur_toutes_les_dates(self):
        j, h, f = marche(graine=7)
        # un symbole meurt au milieu : la coupe des zombies lit la fin des données, elle ne doit rien changer avant
        j["volume"].loc[j["volume"].index >= "2022-08-15", "S05"] = 0.0
        jc, _, _, _ = m.couper_zombies(j, h, f)
        diffs = 0
        dates = lundis(j)
        for t in dates:
            jt, ht, ft = tronquer(j, h, f, t)
            jtc, _, _, _ = m.couper_zombies(jt, ht, ft)
            if m.signal(jc, t, m.Params()) != m.signal(jtc, t, m.Params()):
                diffs += 1
        self.assertGreater(len(dates), 30)
        self.assertEqual(diffs, 0)

    def test_fuite_plantee_detectee(self):
        """Contrôle du contrôle : un score qui lit le futur doit faire échouer la comparaison."""
        j, h, f = marche(graine=8)
        t = lundis(j)[10]
        def score_fuyant(jours, tt):
            c = jours["close"]
            return (c.iloc[-1] / c.iloc[-30]).drop("BTC")  # dernière ligne disponible, donc postérieure à t
        plein = score_fuyant(j, t).sort_values().index[:3].tolist()
        tronque = score_fuyant(tronquer(j, h, f, t)[0], t).sort_values().index[:3].tolist()
        self.assertNotEqual(plein, tronque)


class Zombies(unittest.TestCase):
    def test_bougies_plates_retirees_et_financement_coupe(self):
        j, h, f = marche(graine=3)
        mort = pd.Timestamp("2022-06-10")
        s = "S01"
        j["volume"].loc[j["volume"].index > mort, s] = 0.0
        dernier_px = h["close"].loc[h["close"].index < mort + pd.Timedelta(days=1), s].iloc[-1]
        for k in ("open", "close", "mark_high", "mark_low"):
            h[k].loc[h[k].index >= mort + pd.Timedelta(days=1), s] = dernier_px  # prix figé
        f[s] = 0.001
        jc, hc, fc, dernier = m.couper_zombies(j, h, f)
        self.assertEqual(dernier[s], mort)
        self.assertTrue(jc["close"].loc[jc["close"].index > mort, s].isna().all())
        self.assertTrue(hc["open"].loc[hc["open"].index >= mort + pd.Timedelta(days=1), s].isna().all())
        self.assertTrue(fc.loc[fc.index >= mort + pd.Timedelta(days=1), s].isna().all())
        # jamais sélectionné après la mort
        for t in lundis(j, depuis=mort + pd.Timedelta(days=1)):
            self.assertNotIn(s, m.univers(jc, t, m.Params()))


class Delistage(unittest.TestCase):
    def test_sortie_derniere_cloture_et_ligne_vide(self):
        j, h, f = marche(graine=4)
        s = "S02"
        t = pd.Timestamp("2022-05-02")  # lundi
        mort = pd.Timestamp("2022-05-04")  # mercredi, dernier jour actif
        j["volume"].loc[j["volume"].index > mort, s] = 0.0
        jc, hc, fc, _ = m.couper_zombies(j, h, f)
        p = m.Params(frais=0.0005, glissement=0.0005)
        r = m.jouer_ligne(hc, fc, s, -1, t + pd.Timedelta(hours=1), t + pd.Timedelta(days=7, hours=1), 1.0, p)
        self.assertEqual(r["statut"], "delistage")
        attendu = h["close"].loc[pd.Timestamp("2022-05-04 23:00"), s]
        self.assertAlmostEqual(r["sortie"], attendu)
        self.assertAlmostEqual(r["cout_sortie_force"], (1 + (-1) * (attendu / r["entree"] - 1)) * 0.001)
        # la semaine suivante, le symbole n'est plus dans l'univers
        self.assertNotIn(s, m.univers(jc, pd.Timestamp("2022-05-09"), m.Params()))

    def test_ligne_delistee_non_remplacee_dans_la_semaine(self):
        j, h, f = marche(graine=5)
        dates = lundis(j)
        t = dates[5]
        longs, shorts = m.signal(m.couper_zombies(j, h, f)[0], t, m.Params())
        victime = longs[0]
        j["volume"].loc[j["volume"].index > t + pd.Timedelta(days=2), victime] = 0.0
        sem, lig = m.backtest(j, h, f, [t, t + pd.Timedelta(days=7)], m.Params())
        self.assertEqual(len(lig), 6)
        self.assertEqual(lig.set_index("symbole").loc[victime, "statut"], "delistage")


class Financement(unittest.TestCase):
    def test_signe_et_lundi_minuit_au_portefeuille_sortant(self):
        j, h, f = marche(graine=6)
        s = "S03"
        t_in = pd.Timestamp("2022-05-02 01:00")
        t_out = pd.Timestamp("2022-05-09 01:00")
        f[s] = 0.0
        f.loc[pd.Timestamp("2022-05-02 00:00"), s] = 0.5   # appartient à la semaine précédente
        f.loc[pd.Timestamp("2022-05-03 08:00"), s] = 0.001
        f.loc[pd.Timestamp("2022-05-09 00:00"), s] = 0.002  # appartient à cette semaine
        p = m.Params(stop=None)
        lg = m.jouer_ligne(h, f, s, +1, t_in, t_out, 100.0, p)
        sh = m.jouer_ligne(h, f, s, -1, t_in, t_out, 100.0, p)
        self.assertAlmostEqual(lg["financement"], -0.3)  # long paie 0,3 % de 100
        self.assertAlmostEqual(sh["financement"], +0.3)  # short encaisse


class Stop(unittest.TestCase):
    def ligne(self, ouverture_saut, sens):
        j, h, f = marche(graine=9)
        s = "S04"
        t_in = pd.Timestamp("2022-05-02 01:00")
        px = h["open"].loc[t_in, s]
        hh = pd.Timestamp("2022-05-04 10:00")
        if sens > 0:
            h["open"].loc[hh, s] = px * ouverture_saut
            h["mark_low"].loc[hh, s] = px * min(ouverture_saut, 0.69)
        else:
            h["open"].loc[hh, s] = px * ouverture_saut
            h["mark_high"].loc[hh, s] = px * max(ouverture_saut, 1.31)
        # aucun autre déclenchement avant hh
        avant = (h["open"].index >= t_in) & (h["open"].index < hh)
        h["mark_low"].loc[avant, s] = px * 0.9
        h["mark_high"].loc[avant, s] = px * 1.1
        p = m.Params(glissement_stop=0.003, frais=0.0005)
        return m.jouer_ligne(h, f, s, sens, t_in, t_in + pd.Timedelta(days=7), 1.0, p), px

    def test_stop_long_sans_saut(self):
        r, px = self.ligne(0.80, +1)  # ouverture au-dessus du niveau, la mèche touche
        self.assertEqual(r["statut"], "stop")
        self.assertAlmostEqual(r["sortie"], px * 0.70 * (1 - 0.003))

    def test_stop_long_avec_saut(self):
        r, px = self.ligne(0.50, +1)  # ouverture déjà sous le niveau
        self.assertAlmostEqual(r["sortie"], px * 0.50 * (1 - 0.003))
        self.assertLess(r["pnl_prix"], -0.30)

    def test_stop_short_avec_saut(self):
        r, px = self.ligne(2.0, -1)  # short qui saute à +100 %
        self.assertAlmostEqual(r["sortie"], px * 2.0 * (1 + 0.003))
        self.assertAlmostEqual(r["pnl_prix"], -(2.0 * 1.003 - 1))


class Rotation(unittest.TestCase):
    def test_passage_long_short_paie_deux_cotes_et_ligne_conservee_paie_l_ecart(self):
        j, h, f = marche(graine=11)
        p = m.Params(stop=None, frais=0.0005, glissement=0.0005)
        dates = lundis(j)[:3]
        jc = m.couper_zombies(j, h, f)[0]
        sigs = [m.signal(jc, t, p) for t in dates[:2]]
        sem, lig = m.backtest(j, h, f, dates, p, notionnel=1.0)
        c = 0.001
        # semaine 1 : entrée de 6 lignes
        self.assertAlmostEqual(sem.loc[0, "cout"], 6 * c)
        # semaine 2 : recalcul indépendant de l'écart
        w1 = lig[lig.lundi == dates[0]].set_index("symbole")
        tenue = w1["valeur_fin"].to_dict()
        cible = {s: 1.0 for s in sigs[1][0]} | {s: -1.0 for s in sigs[1][1]}
        attendu = sum(abs(cible.get(s, 0) - tenue.get(s, 0)) for s in set(tenue) | set(cible)) * c
        attendu += sum(abs(v) for v in lig[lig.lundi == dates[1]]["valeur_fin"]) * c  # solde final
        self.assertAlmostEqual(sem.loc[1, "cout"], attendu)

    def test_flip_et_conservation(self):
        p = m.Params(frais=0.0005, glissement=0.0005)
        # long tenu à 1,1 qui devient short 1,0 : 2,1 échangés ; ligne conservée de 0,9 à 1,0 : 0,1 ; sortie de 1,0 ; entrée de 1,0
        tenues = {"A": 1.1, "B": 0.9, "C": -1.0}
        cible = {"A": -1.0, "B": 1.0, "D": 1.0}
        self.assertAlmostEqual(m.cout_de_rotation(tenues, cible, p), (2.1 + 0.1 + 1.0 + 1.0) * 0.001)


class Signal(unittest.TestCase):
    def test_residu_retire_le_beta(self):
        """Avec un bêta fort mais aucune dérive propre, le score ne classe pas par bêta."""
        n = 40
        beta = np.linspace(0.2, 2.0, n)
        j, h, f = marche(n_sym=n, graine=12, beta=beta, drift_resid=np.zeros(n), drift_btc=0.0015)
        # marché très haussier (+3,6 % par jour) : un classement brut prendrait les bêtas forts
        t0 = lundis(j)[0]
        brut = np.log(j["close"].loc[j["close"].index < t0].iloc[-1] / j["close"].loc[j["close"].index < t0].iloc[-22])
        self.assertGreater(np.corrcoef(brut[[f"S{i:02d}" for i in range(n)]].values, beta)[0, 1], 0.8)
        corr = []
        for t in lundis(j)[::4]:
            sc = m.scores(j, t, [f"S{i:02d}" for i in range(n)], m.Params())
            corr.append(np.corrcoef(sc.values, beta)[0, 1])
        self.assertLess(abs(np.mean(corr)), 0.15)

    def test_egalite_ordre_alphabetique(self):
        sc = pd.Series({"B": 1.0, "A": 1.0, "C": 0.0, "D": -1.0, "F": -1.0, "E": -1.0, "G": 2.0})
        lo, sh = m.selection(sc, 3)
        self.assertEqual(lo, ["G", "A", "B"])
        self.assertEqual(sh, ["D", "E", "F"])

    def test_anciennete_90_jours(self):
        j, h, f = marche(graine=13)
        t = pd.Timestamp("2022-06-06")
        j["volume"].loc[j["volume"].index < t - pd.Timedelta(days=80), "S07"] = 0.0
        self.assertNotIn("S07", m.univers(j, t, m.Params(taille_univers=100)))


class FiltresD6(unittest.TestCase):
    """Règles d'exclusion D6 du 01/11/2026 (à figer)."""

    def test_nom_de_base_et_exclusion_par_prefixe(self):
        self.assertEqual(m.nom_de_base("1000PEPEUSDT"), "PEPE")
        self.assertEqual(m.nom_de_base("1MBABYDOGEUSDT"), "BABYDOGE")
        self.assertEqual(m.nom_de_base("DOGEUSDT"), "DOGE")
        self.assertTrue(m.est_exclu("1000SHIBUSDT", {"SHIB"}))
        self.assertFalse(m.est_exclu("ETHUSDT", {"SHIB"}))

    def test_exclusion_avant_classement_laisse_entrer_le_suivant(self):
        j, h, f = marche(graine=21)
        t = pd.Timestamp("2022-06-06")
        p = m.Params(taille_univers=5)
        base = m.univers(j, t, p)
        p2 = m.Params(taille_univers=5, exclus=frozenset({base[0]}))
        u2 = m.univers(j, t, p2)
        self.assertNotIn(base[0], u2)
        self.assertEqual(len(u2), 5)
        self.assertEqual(u2[:4], base[1:])

    def test_anciennete_continue(self):
        j, h, f = marche(graine=22)
        t = pd.Timestamp("2022-09-05")
        j["volume"].loc[pd.Timestamp("2022-05-01"), "S08"] = 0.0  # un jour nul dans les 180 j
        p = m.Params(taille_univers=100, anciennete=180, anciennete_continue=True)
        self.assertNotIn("S08", m.univers(j, t, p))
        self.assertIn("S08", m.univers(j, t, m.Params(taille_univers=100, anciennete=180)))

    def test_trou_tolere(self):
        j, h, f = marche(graine=24)
        t = pd.Timestamp("2022-09-05")
        j["volume"].loc[pd.Timestamp("2022-05-01"):pd.Timestamp("2022-05-03"), "S09"] = np.nan  # 3 jours absents
        j["volume"].loc[pd.Timestamp("2022-06-01"):pd.Timestamp("2022-06-08"), "S10"] = 0.0     # 8 jours nuls
        strict = m.Params(taille_univers=100, anciennete=180, anciennete_continue=True)
        tol = m.Params(taille_univers=100, anciennete=180, anciennete_continue=True, trou_max_jours=7)
        self.assertNotIn("S09", m.univers(j, t, strict))
        self.assertIn("S09", m.univers(j, t, tol))
        self.assertNotIn("S10", m.univers(j, t, tol))
        self.assertEqual(m.plus_long_trou(np.array([1, 0, 0, 1, 0, 0, 0, 1], bool)), 3)

    def test_seuil_de_volume_et_semaine_vide(self):
        j, h, f = marche(graine=23)
        t = pd.Timestamp("2022-06-06")
        med = j["volume"].loc[(j["volume"].index >= t - pd.Timedelta(days=30)) & (j["volume"].index < t)].median()
        seuil = med.drop("BTC").sort_values().iloc[-4]  # seuls 4 noms au-dessus
        p = m.Params(volume_min=float(seuil))
        self.assertEqual(len(m.univers(j, t, p)), 4)
        self.assertEqual(m.signal(j, t, p), ([], []))  # moins de 6 noms : aucune position


class AucunEdgeFantome(unittest.TestCase):
    """Marches aléatoires sans dérive et sans coût : le moteur ne doit pas fabriquer de rendement."""

    def test_moyenne_nulle_sur_monte_carlo(self):
        moyennes = []
        for g in range(24):
            j, h, f = marche(n_sym=36, jours=330, graine=100 + g)
            sem, _ = m.backtest(j, h, f, lundis(j), P0)
            moyennes.append(sem["net"].mean())
        moy = np.array(moyennes)
        z = moy.mean() / (moy.std(ddof=1) / np.sqrt(len(moy)))
        AucunEdgeFantome.resultat = {"chemins": len(moy), "moyenne_hebdo": float(moy.mean()), "z": float(z)}
        self.assertLess(abs(z), 3.0)

    def test_momentum_plante_detecte(self):
        """Contrôle de sensibilité : une dérive résiduelle persistante doit donner un net positif."""
        rng = np.random.default_rng(5)
        d = rng.normal(0, 0.0004, 36)
        j, h, f = marche(n_sym=36, jours=330, graine=55, drift_resid=d)
        sem, _ = m.backtest(j, h, f, lundis(j), P0)
        st = m.statistiques(sem)
        AucunEdgeFantome.plante = st
        self.assertGreater(st["moyenne"], 0)
        self.assertGreater(st["sharpe_annualise"], 1.0)


if __name__ == "__main__":
    import json
    prog = unittest.main(exit=False, verbosity=2)
    print("RESULTATS", json.dumps({"monte_carlo": getattr(AucunEdgeFantome, "resultat", None),
                                   "plante": getattr(AucunEdgeFantome, "plante", None),
                                   "reussis": prog.result.testsRun - len(prog.result.failures) - len(prog.result.errors),
                                   "total": prog.result.testsRun}))
    sys.exit(0 if prog.result.wasSuccessful() else 1)
