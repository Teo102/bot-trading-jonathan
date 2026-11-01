"""Phase 1 : tire les wallets depuis les trades publics des pools, puis lit leur historique sur 30 jours.
Reprise possible : ce qui est déjà en base n'est pas relu. Usage : historique_wallets.py [graines|signatures|transactions|tout]"""
import datetime as D, json, random, sys, time
from concurrent.futures import ThreadPoolExecutor
from dex_commun import base, gecko, lire_transaction, rpc

GRAINE, N_WALLETS, BUDGET_TX, MAX_SIG, JOURS, MIN_USD = 20261101, 400, 8000, 400, 30, 50
DEXES = (("pumpswap", 5), ("pump-fun", 2), ("raydium", 2))


def maintenant():
    return D.datetime.now(D.timezone.utc).isoformat(timespec="seconds")


def pools_pump():
    vus = {}
    for dex, pages in DEXES:
        for page in range(1, pages + 1):
            d = gecko(f"/networks/solana/dexes/{dex}/pools?page={page}&sort=h24_volume_usd_desc")
            for p in (d or {}).get("data", []):
                mint = p["relationships"]["base_token"]["data"]["id"].removeprefix("solana_")
                if mint.endswith("pump"):
                    vus[p["attributes"]["address"]] = mint
    return vus


def trades_du_pool(c, pool, mint):
    d = gecko(f"/networks/solana/pools/{pool}/trades?trade_volume_in_usd_greater_than={MIN_USD}")
    lignes = []
    for t in (d or {}).get("data", []):
        a = t["attributes"]
        lignes.append((a["tx_hash"], pool, a["tx_from_address"], a["block_timestamp"], a["kind"], mint,
                       float(a.get("volume_in_usd") or 0), float(a.get("price_to_in_usd") or 0), maintenant()))
    c.executemany("INSERT OR IGNORE INTO trades_gecko VALUES(?,?,?,?,?,?,?,?,?)", lignes)
    c.commit()
    return len(lignes)


def graines(c):
    pools = pools_pump()
    total = sum(trades_du_pool(c, p, m) for p, m in pools.items())
    print(maintenant(), f"pools {len(pools)}, trades lus {total}", flush=True)
    tous = sorted(w for (w,) in c.execute("SELECT DISTINCT wallet FROM trades_gecko"))
    random.Random(GRAINE).shuffle(tous)
    tirage = tous[:N_WALLETS]
    c.executemany("INSERT OR IGNORE INTO wallets(wallet, statut) VALUES(?, 'tire')", [(w,) for w in tirage])
    c.commit()
    print(maintenant(), f"wallets distincts {len(tous)}, tirés {len(tirage)}", flush=True)


def signatures_wallet(wallet, depuis):
    page = rpc("getSignaturesForAddress", [wallet, {"limit": 1000}]) or []
    temps = [s["blockTime"] for s in page if s.get("blockTime")]
    par_min = {}
    for t in temps:
        par_min[t // 60] = par_min.get(t // 60, 0) + 1
    utiles = [(s["signature"], s["blockTime"]) for s in page
              if s.get("err") is None and s.get("blockTime") and s["blockTime"] >= depuis]
    page_coupee = len(page) == 1000 and min(temps, default=0) >= depuis
    return utiles, page_coupee, max(par_min.values(), default=0)


def signatures(c):
    depuis = int(time.time()) - JOURS * 86400
    a_lire = [w for (w,) in c.execute("SELECT wallet FROM wallets WHERE statut='tire'")]

    def lire(w):
        try:
            return w, signatures_wallet(w, depuis)
        except RuntimeError:
            return w, None

    with ThreadPoolExecutor(4) as ex:
        for k, (w, res) in enumerate(ex.map(lire, a_lire), 1):
            if res is None:
                c.execute("UPDATE wallets SET statut='erreur_rpc', lu_le=? WHERE wallet=?", (maintenant(), w))
            else:
                sigs, coupee, max_min = res
                statut = "hors_budget" if coupee or len(sigs) > MAX_SIG else "retenu"
                c.execute("UPDATE wallets SET statut=?, n_sig=?, max_par_min=?, lu_le=? WHERE wallet=?",
                          (statut, len(sigs), max_min, maintenant(), w))
                if statut == "retenu":
                    c.executemany("INSERT OR IGNORE INTO signatures VALUES(?,?,?)", [(s, w, t) for s, t in sigs])
            c.commit()
            if k % 50 == 0:
                print(maintenant(), f"signatures {k}/{len(a_lire)}", flush=True)


def transactions(c):
    """Parcourt les wallets dans l'ordre du tirage pour ne pas tronquer un wallet au hasard : un wallet commencé est terminé."""
    ordre = sorted((w for (w,) in c.execute("SELECT wallet FROM wallets WHERE statut='retenu'")))
    random.Random(GRAINE).shuffle(ordre)
    faits = c.execute("SELECT COUNT(*) FROM mouvements").fetchone()[0]

    def lire(s):
        sig, w, t = s
        try:
            tx = rpc("getTransaction", [sig, {"maxSupportedTransactionVersion": 0, "encoding": "json"}])
        except RuntimeError:
            return s, "erreur"
        return s, (lire_transaction(tx, w) if tx else None)

    for w in ordre:
        if faits >= BUDGET_TX:
            c.execute("UPDATE wallets SET statut='non_lu_budget' WHERE wallet=? AND statut='retenu' "
                      "AND NOT EXISTS(SELECT 1 FROM mouvements m WHERE m.wallet=wallets.wallet)", (w,))
            c.commit()
            continue
        reste = c.execute("SELECT sig, wallet, ts FROM signatures s WHERE wallet=? AND NOT EXISTS("
                          "SELECT 1 FROM mouvements m WHERE m.sig=s.sig AND m.wallet=s.wallet)", (w,)).fetchall()
        erreurs = 0
        with ThreadPoolExecutor(6) as ex:
            for (sig, wa, t), r in ex.map(lire, reste):
                if r == "erreur":
                    erreurs += 1
                    continue
                r = r or dict(type="vide", mint=None, qte=0, sol=0, stable=0, priorite_sol=0, financeur=None)
                c.execute("INSERT OR REPLACE INTO mouvements VALUES(?,?,?,?,?,?,?,?,?,?)",
                          (sig, wa, t, r["type"], r["mint"], r["qte"], r["sol"], r["stable"], r["priorite_sol"], r["financeur"]))
                faits += 1
        c.execute("UPDATE wallets SET statut=? WHERE wallet=?", ("lu" if not erreurs else "lu_incomplet", w))
        c.commit()
        print(maintenant(), f"wallet terminé, transactions lues {faits}, erreurs {erreurs}", flush=True)


if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else "tout"
    c = base()
    if etape in ("graines", "tout"):
        graines(c)
    if etape in ("signatures", "tout"):
        signatures(c)
    if etape in ("transactions", "tout"):
        transactions(c)
    resume = dict(c.execute("SELECT statut, COUNT(*) FROM wallets GROUP BY statut").fetchall())
    print(maintenant(), "FIN", json.dumps(resume), flush=True)
