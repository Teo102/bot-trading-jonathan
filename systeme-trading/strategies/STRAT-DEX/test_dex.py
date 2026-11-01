"""Tests sans réseau de la lecture des transactions et du calcul des positions."""
import sqlite3, unittest
from pathlib import Path
from analyse_cohorte import fisher, positions
from dex_commun import VERSION_TX, WSOL, lire_transaction, rpc

W, A, M, USDC = "WALLET", "AUTRE", "JETONpump", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def bal(mint, owner, q):
    return {"mint": mint, "owner": owner, "uiTokenAmount": {"uiAmountString": str(q)}}


def tx(pre, post, tpre=(), tpost=(), fee=5000, err=None, cles=(W, A)):
    return {"transaction": {"signatures": ["s"], "message": {"accountKeys": list(cles)}},
            "meta": {"err": err, "fee": fee, "preBalances": pre, "postBalances": post,
                     "preTokenBalances": list(tpre), "postTokenBalances": list(tpost)}}


class Lecture(unittest.TestCase):
    def test_achat_en_sol(self):
        r = lire_transaction(tx([2_000_000_000, 0], [1_000_000_000, 0], tpost=[bal(M, W, 500)], fee=105000), W)
        self.assertEqual((r["type"], r["mint"], r["qte"], r["sol"]), ("achat", M, 500.0, -1.0))
        self.assertAlmostEqual(r["priorite_sol"], 0.0001)

    def test_vente_en_wsol(self):
        r = lire_transaction(tx([10**9, 0], [10**9, 0], tpre=[bal(M, W, 500), bal(WSOL, W, 0)], tpost=[bal(M, W, 0), bal(WSOL, W, 2)]), W)
        self.assertEqual((r["type"], r["qte"], r["sol"]), ("vente", -500.0, 2.0))

    def test_achat_en_stable(self):
        r = lire_transaction(tx([10**9, 0], [10**9, 0], tpre=[bal(USDC, W, 100)], tpost=[bal(USDC, W, 0), bal(M, W, 7)]), W)
        self.assertEqual((r["type"], r["stable"]), ("achat", -100.0))

    def test_entree_sans_paiement_est_un_transfert(self):
        self.assertEqual(lire_transaction(tx([10**9, 0], [10**9 - 5000, 0], tpost=[bal(M, W, 7)]), W)["type"], "entree_jeton")

    def test_sortie_sans_recette_est_un_transfert(self):
        self.assertEqual(lire_transaction(tx([10**9, 0], [10**9 - 5000, 0], tpre=[bal(M, W, 7)], tpost=[bal(M, W, 0)]), W)["type"], "sortie_jeton")

    def test_deux_jetons_complexe(self):
        r = lire_transaction(tx([10**9, 0], [10**9, 0], tpre=[bal(M, W, 7)], tpost=[bal(M, W, 0), bal("B", W, 3)]), W)
        self.assertEqual(r["type"], "complexe")

    def test_financement_et_source(self):
        r = lire_transaction(tx([0, 10**10], [10**9, 9 * 10**9]), W)
        self.assertEqual((r["type"], r["financeur"]), ("financement", A))

    def test_transaction_en_echec_ignoree(self):
        self.assertIsNone(lire_transaction(tx([1, 1], [1, 1], err={"x": 1}), W))

    def test_solde_d_un_autre_proprietaire_ignore(self):
        r = lire_transaction(tx([10**9, 0], [10**9, 0], tpost=[bal(M, A, 9)]), W)
        self.assertEqual(r["type"], "autre")

    def test_adresses_chargees(self):
        t = tx([1, 1, 3 * 10**9], [1, 1, 10**9], tpost=[bal(M, W, 1)], cles=("P", A))
        t["meta"]["loadedAddresses"] = {"writable": [W], "readonly": []}
        self.assertEqual(lire_transaction(t, W)["type"], "achat")


class Positions(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(":memory:")
        self.c.execute("CREATE TABLE mouvements(sig,wallet,ts,type,mint,qte,sol,stable,priorite_sol,financeur)")
        self.c.execute("CREATE TABLE sol_usd(h INTEGER PRIMARY KEY, prix REAL)")
        self.c.execute("CREATE TABLE jetons(mint, prix, fdv, lu_le)")
        self.c.execute("INSERT INTO sol_usd VALUES(0, 100.0)")

    def mvt(self, sig, wallet, ts, type_, mint, qte, sol):
        self.c.execute("INSERT INTO mouvements VALUES(?,?,?,?,?,?,?,0,0,NULL)", (sig, wallet, ts, type_, mint, qte, sol))

    def test_vente_partielle_et_reliquat_valorise(self):
        self.mvt("a", "W", 10, "achat", "J", 100, -1.0)      # coût 100 $
        self.mvt("b", "W", 20, "vente", "J", -50, 1.5)       # recette 150 $
        self.c.execute("INSERT INTO jetons VALUES('J', 0.5, 500000000, 'x')")  # reliquat 50 x 0,5 = 25 $
        p, _ = positions(self.c)
        r = p.iloc[0]
        self.assertAlmostEqual(r.pnl, 75.0)
        self.assertAlmostEqual(r.retour, 0.75)
        self.assertFalse(r.sorti)
        self.assertAlmostEqual(r.multiple_v1, 3.0)
        self.assertAlmostEqual(r.offre, 1e9)

    def test_jeton_mort_sans_prix_vaut_zero(self):
        self.mvt("a", "W", 10, "achat", "J", 100, -1.0)
        p, _ = positions(self.c)
        self.assertAlmostEqual(p.iloc[0].retour, -1.0)

    def test_transfert_et_cout_inconnu_exclus(self):
        self.mvt("a", "W", 10, "entree_jeton", "T", 5, 0.0)
        self.mvt("b", "W", 11, "vente", "T", -5, 1.0)
        self.mvt("c", "W", 12, "vente", "U", -5, 1.0)
        p, ex = positions(self.c)
        self.assertTrue(p.empty)
        self.assertEqual((ex["transfert"], ex["cout_inconnu"]), (1, 1))

    def test_fisher_et_persistance(self):
        self.assertAlmostEqual(fisher(1, 9, 11, 3), 0.002759, places=5)   # exemple classique de table 2x2


class Simulation(unittest.TestCase):
    def test_motifs_de_sortie(self):
        import bot_simulation as B
        B.P.update(duree_max_h=24)
        args = (1.0, 0.7, 2.0, 0)
        self.assertEqual(B.sortie(None, 5000, *args, 10), "rug")
        self.assertEqual(B.sortie(1.0, 500, *args, 10), "rug")
        self.assertEqual(B.sortie(0.6, 5000, *args, 10), "stop")
        self.assertEqual(B.sortie(2.5, 5000, *args, 10), "objectif")
        self.assertEqual(B.sortie(1.1, 5000, *args, 25 * 3600), "temps")
        self.assertIsNone(B.sortie(1.1, 5000, *args, 10))

    def test_refus_sans_dry_run(self):
        src = (Path(__file__).parent / "bot_simulation.py").read_text(encoding="utf-8")
        self.assertIn('P.get("dry_run") is not True', src)
        for mot in ("sendTransaction", "private_key", "Keypair", "sign("):
            self.assertNotIn(mot, src)


class Securite(unittest.TestCase):
    def test_version_de_transaction(self):
        self.assertGreaterEqual(VERSION_TX, 1)

    def test_cle_absente_de_la_trace_d_erreur(self):
        src = (Path(__file__).parent / "dex_commun.py").read_text(encoding="utf-8")
        self.assertNotIn("print(", src)
        self.assertNotIn("{RPC}", src)

    def test_methode_d_envoi_refusee(self):
        with self.assertRaises(ValueError):
            rpc("sendTransaction", ["x"])


if __name__ == "__main__":
    unittest.main()
