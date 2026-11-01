"""Simulation avançant dans le temps de STRAT-DEX. Aucun ordre : ce script n'a ni clé, ni wallet, ni signature, ni envoi de transaction.
Les règles viennent de parametres_geles.json et ne changent pas pendant le test. Protocole : FICHE_STRAT-DEX.md § 7."""
import json, sqlite3, time
from dex_commun import BASE, ICI, gecko
import datetime as D

P = json.loads((ICI / "parametres_geles.json").read_text(encoding="utf-8"))
if P.get("dry_run") is not True:
    raise SystemExit("dry_run doit rester à true")
PAUSE_S, RESERVE_RUG, MISE = 300, 1000.0, float(P["mise_simulee_usd"])


def maintenant():
    return D.datetime.now(D.timezone.utc).isoformat(timespec="seconds")


def base_sim():
    BASE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(BASE / "simulation.sqlite", timeout=60)
    c.execute("""CREATE TABLE IF NOT EXISTS trades(pool TEXT PRIMARY KEY, mint TEXT, t_entree INTEGER, prix_vu_entree REAL, prix_entree REAL, stop REAL,
        objectif REAL, fdv REAL, volume_h1 REAL, reserve REAL, t_sortie INTEGER, prix_vu_sortie REAL, prix_sortie REAL, motif TEXT, retour REAL, r REAL)""")
    return c


def cout_cote(mise, reserve):
    """Frais et priorité forfaitaires, plus l'impact d'un pool à produit constant dont la moitié de la réserve est du côté acheté."""
    return float(P["cout_par_cote"]) + (mise / (reserve / 2) if reserve > 0 else 1.0)


def signal(a, heure_haut=None):
    """Règles d'entrée, sur les seuls champs connus au moment de la lecture."""
    fdv, vol, res = float(a.get("fdv_usd") or 0), float(a["volume_usd"].get("h1") or 0), float(a.get("reserve_in_usd") or 0)
    if not (P["fdv_min"] <= fdv <= P["fdv_max"]) or vol < P["volume_h1_min"] or res < P["reserve_min"]:
        return False
    cree = a.get("pool_created_at")
    if cree and time.time() - D.datetime.fromisoformat(cree.replace("Z", "+00:00")).timestamp() < P["age_min_h"] * 3600:
        return False
    if P["declencheur"] == "cassure":
        return float(a["price_change_percentage"].get("h1") or 0) > 0 and float(a["price_change_percentage"].get("h24") or 0) > 0
    if P["declencheur"] == "repli":
        return float(a["price_change_percentage"].get("h1") or 0) < 0
    return True


def sortie(prix, res, entree, stop, objectif, t_entree, maintenant_s):
    """Motif de sortie, ou None. Le prix lu sert au remplissage : un stop franchi entre deux lectures n'est pas rempli au stop."""
    if prix is None or res < RESERVE_RUG:
        return "rug"
    if prix <= stop:
        return "stop"
    if prix >= objectif:
        return "objectif"
    if maintenant_s - t_entree >= P["duree_max_h"] * 3600:
        return "temps"
    return None


def fermer(c, ligne, prix, res, motif, t):
    pool, entree = ligne[0], ligne[4]
    if motif == "rug":
        rempli, retour = 0.0, -1.0
    else:
        rempli = prix * (1 - cout_cote(MISE, res))
        retour = rempli / entree - 1
    c.execute("UPDATE trades SET t_sortie=?, prix_vu_sortie=?, prix_sortie=?, motif=?, retour=?, r=? WHERE pool=?",
              (t, prix, rempli, motif, retour, retour / P["stop_distance"], pool))
    c.commit()


def surveiller(c, t):
    ouverts = c.execute("SELECT pool, mint, t_entree, prix_vu_entree, prix_entree, stop, objectif FROM trades WHERE t_sortie IS NULL").fetchall()
    for i in range(0, len(ouverts), 30):
        lot = ouverts[i:i + 30]
        d = gecko("/networks/solana/pools/multi/" + ",".join(x[0] for x in lot))
        if d is None:
            continue
        vus = {x["attributes"]["address"]: x["attributes"] for x in d["data"]}
        for x in lot:
            a = vus.get(x[0])
            prix = float(a["base_token_price_usd"]) if a and a.get("base_token_price_usd") else None
            res = float(a.get("reserve_in_usd") or 0) if a else 0.0
            motif = sortie(prix, res, x[3], x[5], x[6], x[2], t)
            if motif:
                fermer(c, x, prix, res, motif, t)


def chercher(c, t):
    ouverts = c.execute("SELECT COUNT(*) FROM trades WHERE t_sortie IS NULL").fetchone()[0]
    d = gecko("/networks/solana/dexes/pumpswap/pools?page=1&sort=h24_volume_usd_desc")
    for p in (d or {}).get("data", []):
        if ouverts >= P["positions_max"]:
            break
        a = p["attributes"]
        mint = p["relationships"]["base_token"]["data"]["id"].removeprefix("solana_")
        if not mint.endswith("pump") or c.execute("SELECT 1 FROM trades WHERE mint=?", (mint,)).fetchone() or not signal(a):
            continue
        prix, res = float(a["base_token_price_usd"]), float(a.get("reserve_in_usd") or 0)
        entree = prix * (1 + cout_cote(MISE, res))
        c.execute("INSERT INTO trades(pool, mint, t_entree, prix_vu_entree, prix_entree, stop, objectif, fdv, volume_h1, reserve) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (a["address"], mint, t, prix, entree, entree * (1 - P["stop_distance"]), entree * P["objectif_multiple"],
                   float(a.get("fdv_usd") or 0), float(a["volume_usd"].get("h1") or 0), res))
        c.commit()
        ouverts += 1


def boucle():
    c = base_sim()
    while True:
        t = int(time.time())
        try:
            surveiller(c, t)
            chercher(c, t)
        except (RuntimeError, KeyError, ValueError, TypeError) as e:
            print(maintenant(), "erreur", repr(e), flush=True)
        (BASE / "simulation.battement").write_text(maintenant())
        n, o = c.execute("SELECT COUNT(*), SUM(t_sortie IS NULL) FROM trades").fetchone()
        print(maintenant(), f"trades simulés {n}, ouverts {o or 0}", flush=True)
        time.sleep(PAUSE_S)


if __name__ == "__main__":
    boucle()
