"""Tests sans réseau de la lecture des transactions et du calcul des positions."""
import unittest
from dex_commun import WSOL, lire_transaction, rpc

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


class Securite(unittest.TestCase):
    def test_methode_d_envoi_refusee(self):
        with self.assertRaises(ValueError):
            rpc("sendTransaction", ["x"])


if __name__ == "__main__":
    unittest.main()
