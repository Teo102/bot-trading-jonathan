"""Collecteur continu des trades publics des pools pump, pour construire une cohorte future de 30 à 90 jours.
GeckoTerminal ne donne que les 300 derniers trades d'un pool : sur un pool très actif, des trades manquent entre deux passages."""
import time
from dex_commun import BASE, base, gecko
from historique_wallets import maintenant, pools_pump, trades_du_pool

RAFRAICHIR_S = 3600


def boucle():
    c = base()
    pools, vu_le = {}, 0.0
    while True:
        if time.time() - vu_le > RAFRAICHIR_S:
            try:
                pools, vu_le = pools_pump() or pools, time.time()
            except RuntimeError as e:
                print(maintenant(), "pools", e, flush=True)
        total = 0
        for pool, mint in list(pools.items()):
            try:
                total += trades_du_pool(c, pool, mint)
            except RuntimeError as e:
                print(maintenant(), "trades", e, flush=True)
            (BASE / "collecte.battement").write_text(maintenant())
        print(maintenant(), f"passage terminé, pools {len(pools)}, lignes lues {total}", flush=True)


if __name__ == "__main__":
    boucle()
