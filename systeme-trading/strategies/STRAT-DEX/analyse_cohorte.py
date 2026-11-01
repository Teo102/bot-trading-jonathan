"""Phases 2 et 3 : positions, filtres d'exclusion, facteurs et persistance. Protocole : FICHE_STRAT-DEX.md.
Usage : analyse_cohorte.py [marche|filtres|facteurs|rapport|tout]. Les rapports publics ne contiennent aucune adresse complète."""
import json, math, random, sys, time, datetime as D
from pathlib import Path
import numpy as np, pandas as pd
from dex_commun import ICI, STABLES, VERSION_TX, WSOL, base, gecko, rpc

MIN_POS, MIN_POS_PERSIST, SNIPE_S, MAX_PAR_MIN, MAX_PRIO, BUSY_S = 5, 3, 2, 20, 0.01, 86400
CAP_DEPLOYEURS, CAP_OHLCV, GRAINE = 400, 400, 20261101
SORTIES = ICI / "resultats"


def maintenant():
    return D.datetime.now(D.timezone.utc).isoformat(timespec="seconds")


def schema(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS sol_usd(h INTEGER PRIMARY KEY, prix REAL);
    CREATE TABLE IF NOT EXISTS jetons(mint TEXT PRIMARY KEY, prix REAL, fdv REAL, lu_le TEXT);
    CREATE TABLE IF NOT EXISTS pools_jeton(mint TEXT, pool TEXT, dex TEXT, cree INTEGER, reserve REAL, PRIMARY KEY(mint, pool));
    CREATE TABLE IF NOT EXISTS pools_lus(mint TEXT PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS deployeurs(mint TEXT PRIMARY KEY, deployeur TEXT);
    CREATE TABLE IF NOT EXISTS financeurs(financeur TEXT PRIMARY KEY, plateforme INTEGER);
    CREATE TABLE IF NOT EXISTS ohlcv(mint TEXT, ts INTEGER, haut REAL, volume REAL, PRIMARY KEY(mint, ts));
    CREATE TABLE IF NOT EXISTS ohlcv_lus(mint TEXT PRIMARY KEY);
    """)


def charger_sol(c):
    d = gecko(f"/networks/solana/tokens/{WSOL}/pools?page=1")
    usdc = next(iter(STABLES & {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}))
    pool = next(p["attributes"]["address"] for p in d["data"]
                if p["relationships"]["quote_token"]["data"]["id"] == f"solana_{usdc}"
                and p["relationships"]["base_token"]["data"]["id"] == f"solana_{WSOL}")
    # Barres journalières pour le passé lointain, puis horaires, plus fines, sur les 41 derniers jours
    for maille in ("day", "hour"):
        o = gecko(f"/networks/solana/pools/{pool}/ohlcv/{maille}?limit=1000")["data"]["attributes"]["ohlcv_list"]
        c.executemany("INSERT OR REPLACE INTO sol_usd VALUES(?,?)", [(int(x[0]) // 3600, float(x[4])) for x in o])
    c.commit()


def charger_prix(c):
    mints = [m for (m,) in c.execute("SELECT DISTINCT mint FROM mouvements WHERE mint IS NOT NULL "
                                     "AND mint NOT IN (SELECT mint FROM jetons)")]
    for i in range(0, len(mints), 30):
        lot = mints[i:i + 30]
        d = gecko("/networks/solana/tokens/multi/" + ",".join(lot)) or {"data": []}
        vus = {x["attributes"]["address"]: x["attributes"] for x in d["data"]}
        c.executemany("INSERT OR REPLACE INTO jetons VALUES(?,?,?,?)",
                      [(m, float(vus[m].get("price_usd") or 0) if m in vus else 0.0,
                        float(vus[m].get("fdv_usd") or 0) if m in vus else 0.0, maintenant()) for m in lot])
        c.commit()
    print(maintenant(), "prix lus", len(mints), flush=True)


def positions(c):
    """Une ligne par wallet et jeton. Une position avec transfert ou coût inconnu est exclue et comptée."""
    m = pd.read_sql("SELECT * FROM mouvements WHERE type IN ('achat','vente','entree_jeton','sortie_jeton')", c)
    sol = pd.read_sql("SELECT h, prix FROM sol_usd ORDER BY h", c)
    jet = pd.read_sql("SELECT mint, prix, fdv FROM jetons", c).set_index("mint")
    m["h"] = m.ts // 3600
    m = pd.merge_asof(m.sort_values("h"), sol, on="h", direction="nearest", tolerance=24)
    m["usd"] = m.sol * m.prix + m.stable
    lignes, exclus = [], {"transfert": 0, "cout_inconnu": 0, "prix_sol_absent": 0}
    for (w, mint), g in m.sort_values("ts").groupby(["wallet", "mint"]):
        if g.usd.isna().any():
            exclus["prix_sol_absent"] += 1
            continue
        if g.type.isin(["entree_jeton", "sortie_jeton"]).any():
            exclus["transfert"] += 1
            continue
        if g.type.iloc[0] != "achat":
            exclus["cout_inconnu"] += 1
            continue
        a, v = g[g.type == "achat"], g[g.type == "vente"]
        cout, recette, qa, qv = -a.usd.sum(), v.usd.sum(), a.qte.sum(), -v.qte.sum()
        if cout <= 0 or qa <= 0:
            exclus["cout_inconnu"] += 1
            continue
        prix_act = float(jet.prix.get(mint, 0.0) or 0.0)
        reliquat = max(0.0, qa - qv)
        if reliquat < 0.001 * qa:
            reliquat = 0.0
        valeur = reliquat * prix_act
        t0, pm = int(a.ts.iloc[0]), cout / qa
        pv1 = (v.usd.iloc[0] / -v.qte.iloc[0]) if len(v) else np.nan
        lignes.append(dict(wallet=w, mint=mint, t0=t0, cout=cout, recette=recette, valeur=valeur, pnl=recette + valeur - cout,
                           retour=(recette + valeur - cout) / cout, n_achats=len(a), n_ventes=len(v),
                           sorti=reliquat == 0.0, duree_h=(int(v.ts.iloc[-1]) - t0) / 3600 if len(v) else np.nan,
                           prix_entree=(-a.usd.iloc[0] / a.qte.iloc[0]), multiple_v1=pv1 / pm if len(v) else np.nan,
                           offre=float(jet.fdv.get(mint, 0) / jet.prix.get(mint, 1)) if float(jet.prix.get(mint, 0) or 0) > 0 else np.nan))
    return pd.DataFrame(lignes), exclus


def stats_wallets(p):
    def f(g):
        gains, pertes = g.pnl[g.pnl > 0], g.pnl[g.pnl <= 0]
        ordre = g.pnl.sort_values(ascending=False)
        return pd.Series(dict(n=len(g), pnl=g.pnl.sum(), cout=g.cout.sum(), retour=g.pnl.sum() / g.cout.sum(), reussite=(g.pnl > 0).mean(),
                              pf=gains.sum() / -pertes.sum() if pertes.sum() < 0 else np.inf,
                              gain_moy=gains.mean() if len(gains) else 0.0, perte_moy=pertes.mean() if len(pertes) else 0.0,
                              pnl_sans_meilleur=ordre.iloc[1:].sum()))
    return p.groupby("wallet")[["pnl", "cout"]].apply(f)


def charger_pools(c, mints):
    deja = {m for (m,) in c.execute("SELECT mint FROM pools_lus")}
    for k, m in enumerate(x for x in mints if x not in deja):
        d = gecko(f"/networks/solana/tokens/{m}/pools?page=1") or {"data": []}
        for p in d["data"]:
            a = p["attributes"]
            cree = pd.Timestamp(a["pool_created_at"]).timestamp() if a.get("pool_created_at") else None
            c.execute("INSERT OR REPLACE INTO pools_jeton VALUES(?,?,?,?,?)",
                      (m, a["address"], p["relationships"]["dex"]["data"]["id"], cree, float(a.get("reserve_in_usd") or 0)))
        c.execute("INSERT OR IGNORE INTO pools_lus VALUES(?)", (m,))
        c.commit()
        if k % 100 == 99:
            print(maintenant(), "pools lus", k + 1, flush=True)


def deployeur(mint):
    avant = None
    for _ in range(10):
        opt = {"limit": 1000}
        if avant:
            opt["before"] = avant
        page = rpc("getSignaturesForAddress", [mint, opt]) or []
        if not page:
            return None
        avant = page[-1]["signature"]
        if len(page) < 1000:
            tx = rpc("getTransaction", [avant, {"maxSupportedTransactionVersion": VERSION_TX, "encoding": "json"}])
            return tx["transaction"]["message"]["accountKeys"][0] if tx else None
    return None


def est_plateforme(adresse):
    page = rpc("getSignaturesForAddress", [adresse, {"limit": 1000}]) or []
    t = [s["blockTime"] for s in page if s.get("blockTime")]
    return int(len(page) == 1000 and t and max(t) - min(t) < BUSY_S)


def filtrer(c, p):
    """Retourne le statut de chaque wallet à au moins MIN_POS positions, et les comptes d'exclusion."""
    n = p.groupby("wallet").size()
    cands = set(n[n >= MIN_POS].index)
    w = pd.read_sql("SELECT wallet, max_par_min FROM wallets", c).set_index("wallet")
    prio = pd.read_sql("SELECT wallet, priorite_sol FROM mouvements WHERE type IN ('achat','vente')", c).groupby("wallet").priorite_sol.median()
    statut = {x: [] for x in cands}
    for x in cands:
        if w.max_par_min.get(x, 0) >= MAX_PAR_MIN or prio.get(x, 0) > MAX_PRIO:
            statut[x].append("F3")
    restants = [x for x in cands if not statut[x]]
    q = p[p.wallet.isin(restants)]
    charger_pools(c, sorted(q.mint.unique()))
    pools = pd.read_sql("SELECT mint, cree FROM pools_jeton WHERE cree IS NOT NULL", c)
    achats = pd.read_sql("SELECT wallet, mint, ts FROM mouvements WHERE type='achat'", c)
    j = achats[achats.wallet.isin(restants)].merge(pools, on="mint")
    for x in j[(j.ts >= j.cree) & (j.ts - j.cree <= SNIPE_S)].wallet.unique():
        statut[x].append("F1")
    restants = [x for x in restants if not statut[x]]
    q = p[p.wallet.isin(restants)]
    mints = sorted(q.mint.unique())
    random.Random(GRAINE).shuffle(mints)
    connus = {m for (m,) in c.execute("SELECT mint FROM deployeurs")}
    for k, m in enumerate(x for x in mints[:CAP_DEPLOYEURS] if x not in connus):
        try:
            d = deployeur(m)
        except RuntimeError:
            d = None
        c.execute("INSERT OR REPLACE INTO deployeurs VALUES(?,?)", (m, d))
        c.commit()
        if k % 50 == 49:
            print(maintenant(), "déployeurs lus", k + 1, flush=True)
    dep = dict(c.execute("SELECT mint, deployeur FROM deployeurs"))
    fin = pd.read_sql("SELECT DISTINCT wallet, financeur FROM mouvements WHERE type='financement' AND financeur IS NOT NULL", c)
    par_fin = fin.groupby("financeur").wallet.nunique()
    for a in par_fin[par_fin >= 2].index:
        if not c.execute("SELECT 1 FROM financeurs WHERE financeur=?", (a,)).fetchone():
            try:
                c.execute("INSERT OR REPLACE INTO financeurs VALUES(?,?)", (a, est_plateforme(a)))
                c.commit()
            except RuntimeError:
                pass
    plat = dict(c.execute("SELECT financeur, plateforme FROM financeurs"))
    partages = {a for a in par_fin[par_fin >= 2].index if plat.get(a) == 0}
    for x in restants:
        ses = set(fin[fin.wallet == x].financeur)
        des_mints = {dep.get(m) for m in q[q.wallet == x].mint} - {None}
        if x in des_mints or ses & des_mints:
            statut[x].append("F2_dev")
        if ses & partages:
            statut[x].append("F2_cluster")
    couverture = dict(jetons=len(mints), lus=sum(1 for m in mints if m in dep),
                      trouves=sum(1 for m in mints if dep.get(m)), financeurs_partages=int((par_fin >= 2).sum()), non_plateforme=len(partages))
    return statut, couverture


def charger_ohlcv(c, p):
    pools = pd.read_sql("SELECT mint, pool, reserve FROM pools_jeton", c).sort_values("reserve", ascending=False).drop_duplicates("mint")
    mints = sorted(set(p.mint) & set(pools.mint))
    random.Random(GRAINE).shuffle(mints)
    deja = {m for (m,) in c.execute("SELECT mint FROM ohlcv_lus")}
    pool = dict(zip(pools.mint, pools.pool))
    for k, m in enumerate(x for x in mints[:CAP_OHLCV] if x not in deja):
        d = gecko(f"/networks/solana/pools/{pool[m]}/ohlcv/hour?limit=1000&currency=usd&token=base")
        o = (d or {}).get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        c.executemany("INSERT OR REPLACE INTO ohlcv VALUES(?,?,?,?)", [(m, int(x[0]), float(x[2]), float(x[5])) for x in o])
        c.execute("INSERT OR IGNORE INTO ohlcv_lus VALUES(?)", (m,))
        c.commit()
        if k % 100 == 99:
            print(maintenant(), "ohlcv lus", k + 1, flush=True)


def contexte(c, p):
    """Ajoute à chaque position la FDV d'entrée, la phase par rapport à la migration et le contexte horaire."""
    p = p.copy()
    p["fdv_entree"] = p.prix_entree * p.offre
    pools = pd.read_sql("SELECT mint, dex, cree FROM pools_jeton WHERE cree IS NOT NULL", c)
    mig = pools[pools.dex.isin(["pumpswap", "raydium", "raydium-clmm", "meteora", "meteora-damm-v2"])].groupby("mint").cree.min()
    ecart = p.t0 - p.mint.map(mig)
    p["phase"] = np.select([ecart.isna(), ecart < 0, ecart <= 3600], ["inconnue", "avant_migration", "migration_1h"], "apres_1h")
    o = pd.read_sql("SELECT * FROM ohlcv", c)
    groupes = {m: g.sort_values("ts") for m, g in o.groupby("mint")}
    vol, ratio = [], []
    for r in p.itertuples():
        g = groupes.get(r.mint)
        if g is None:
            vol.append(np.nan); ratio.append(np.nan); continue
        h = r.t0 - r.t0 % 3600
        av = g[(g.ts < h) & (g.ts >= h - 24 * 3600)]
        v1 = g[g.ts == h - 3600].volume
        vol.append(float(v1.iloc[0]) if len(v1) else np.nan)
        ratio.append(r.prix_entree / av.haut.max() if len(av) and av.haut.max() > 0 else np.nan)
    p["volume_h1"], p["ratio_haut24"] = vol, ratio
    p["declencheur"] = np.select([np.isnan(ratio), np.array(ratio) >= 0.95, np.array(ratio) <= 0.70], ["inconnu", "cassure", "repli"], "entre_les_deux")
    return p


def mediane(x):
    x = pd.Series(x).replace([np.inf, -np.inf], np.nan).dropna()
    return float(x.median()) if len(x) else None


def resume_groupe(p):
    if p.empty:
        return dict(positions=0)
    perdants = p[p.sorti & (p.retour < 0)]
    g, pe = p.pnl[p.pnl > 0], p.pnl[p.pnl <= 0]
    return dict(positions=int(len(p)), wallets=int(p.wallet.nunique()), reussite=float((p.pnl > 0).mean()), retour_moyen=float(p.retour.mean()),
                retour_median=float(p.retour.median()), retour_pondere=float(p.pnl.sum() / p.cout.sum()),
                profit_factor=float(g.sum() / -pe.sum()) if pe.sum() < 0 else None, fdv_entree_mediane=mediane(p.fdv_entree),
                fdv_p25=float(p.fdv_entree.quantile(.25)) if p.fdv_entree.notna().any() else None,
                fdv_p75=float(p.fdv_entree.quantile(.75)) if p.fdv_entree.notna().any() else None,
                duree_mediane_h=mediane(p.duree_h), duree_p75_h=float(p.duree_h.quantile(.75)) if p.duree_h.notna().any() else None,
                perte_sortie_mediane=mediane(perdants.retour), part_echelonnee=float((p.n_ventes >= 2).mean()),
                multiple_v1_median=mediane(p.multiple_v1), volume_h1_median=mediane(p.volume_h1), part_jamais_vendu=float((p.n_ventes == 0).mean()),
                phases=p.phase.value_counts(normalize=True).round(4).to_dict(), declencheurs=p.declencheur.value_counts(normalize=True).round(4).to_dict())


def tranches(p):
    bornes = [0, 5e5, 1e6, 5e6, np.inf]
    noms = ["<500k", "500k-1M", "1M-5M", ">5M"]
    t = pd.cut(p.fdv_entree, bornes, labels=noms)
    return {n: resume_court(p[t == n]) for n in noms}


def resume_court(q):
    return dict(n=int(len(q)), reussite=float((q.pnl > 0).mean()) if len(q) else None, retour_moyen=float(q.retour.mean()) if len(q) else None,
                retour_median=float(q.retour.median()) if len(q) else None, retour_pondere=float(q.pnl.sum() / q.cout.sum()) if len(q) else None)


def fisher(a, b, c_, d):
    """Test exact bilatéral sur [[a, b], [c, d]]."""
    n, r1, c1 = a + b + c_ + d, a + b, a + c_
    pr = lambda k: math.comb(c1, k) * math.comb(n - c1, r1 - k) / math.comb(n, r1)
    p0 = pr(a)
    return min(1.0, sum(pr(k) for k in range(max(0, r1 + c1 - n), min(r1, c1) + 1) if pr(k) <= p0 * (1 + 1e-9)))


def persistance(p, t_fin):
    coupe = t_fin - 45 * 86400
    a, b = stats_wallets(p[p.t0 < coupe]), stats_wallets(p[p.t0 >= coupe])
    j = a[a.n >= MIN_POS_PERSIST].join(b[b.n >= MIN_POS_PERSIST], lsuffix="_a", rsuffix="_b", how="inner")
    if j.empty:
        return dict(wallets=0)
    ga, gb = j.pnl_a > 0, j.pnl_b > 0
    t = [int((ga & gb).sum()), int((ga & ~gb).sum()), int((~ga & gb).sum()), int((~ga & ~gb).sum())]
    return dict(wallets=int(len(j)), tableau=dict(a_pos_b_pos=t[0], a_pos_b_neg=t[1], a_neg_b_pos=t[2], a_neg_b_neg=t[3]),
                part_b_pos_si_a_pos=t[0] / (t[0] + t[1]) if t[0] + t[1] else None, part_b_pos_si_a_neg=t[2] / (t[2] + t[3]) if t[2] + t[3] else None,
                p_fisher=fisher(*t), rang_spearman=float(j.retour_a.corr(j.retour_b, method="spearman")) if len(j) > 2 else None)


def controle_lecture(c):
    j = pd.read_sql("SELECT g.sens, g.usd, m.type, m.sol, m.stable, s.prix FROM trades_gecko g JOIN mouvements m ON g.tx=m.sig AND g.wallet=m.wallet "
                    "LEFT JOIN sol_usd s ON s.h=m.ts/3600 WHERE m.type IN ('achat','vente')", c)
    if j.empty:
        return dict(n=0)
    j["recalcul"] = (j.sol * j.prix + j.stable).abs()
    sens = ((j.sens == "buy") == (j.type == "achat")).mean()
    r = (j.recalcul / j.usd).replace([np.inf, -np.inf], np.nan).dropna()
    return dict(n=int(len(j)), sens_concordant=float(sens), ratio_usd_median=float(r.median()), ratio_usd_p10=float(r.quantile(.1)), ratio_usd_p90=float(r.quantile(.9)))


def rapport(c):
    p, exclus = positions(c)
    statut, couv = filtrer(c, p)
    passe = [w for w, s in statut.items() if not s]
    q = p[p.wallet.isin(passe)]
    charger_ohlcv(c, q)
    q = contexte(c, q)
    st = stats_wallets(q)
    rentables = st[(st.n >= MIN_POS) & (st.pnl > 0) & (st.pf > 1)]
    qr, qn = q[q.wallet.isin(rentables.index)], q[~q.wallet.isin(rentables.index)]
    wallets = pd.read_sql("SELECT statut, COUNT(*) n FROM wallets GROUP BY statut", c).set_index("statut").n.to_dict()
    motifs = {}
    for s in statut.values():
        for x in s:
            motifs[x] = motifs.get(x, 0) + 1
    tout = stats_wallets(p)
    t_fin = int(pd.read_sql("SELECT MAX(ts) t FROM mouvements", c).t.iloc[0])
    ord_r = q.pnl.sort_values(ascending=False)
    pos = ord_r[ord_r > 0].sum()
    res = dict(horodatage_utc=maintenant(), sources="RPC public Solana, GeckoTerminal", periode_jours=90, wallets=wallets,
               mouvements=pd.read_sql("SELECT type, COUNT(*) n FROM mouvements GROUP BY type", c).set_index("type").n.to_dict(),
               positions_total=int(len(p)), positions_exclues=exclus, wallets_avec_positions=int(p.wallet.nunique()),
               part_wallets_positifs_avant_filtres=float((tout.pnl > 0).mean()) if len(tout) else None,
               candidats_min_positions=len(statut), exclusions=motifs, passent_filtres=len(passe), couverture_filtre_dev=couv,
               rentables=int(len(rentables)), rentables_sans_meilleure_position=int((rentables.pnl_sans_meilleur > 0).sum()),
               part_gains_top_1pct=float(ord_r.head(max(1, len(ord_r) // 100)).sum() / pos) if pos > 0 else None,
               gagnants=resume_groupe(qr), perdants_et_neutres=resume_groupe(qn), tranches_fdv=tranches(q) if len(q) else {},
               persistance=persistance(q, t_fin), persistance_avant_filtres=persistance(p, t_fin), controle_lecture=controle_lecture(c),
               par_rentable=[dict(id=f"R{i + 1}", n=int(r.n), reussite=round(float(r.reussite), 3), pf=None if math.isinf(r.pf) else round(float(r.pf), 2),
                                  retour=round(float(r.retour), 3), gain_sur_perte=round(float(r.gain_moy / -r.perte_moy), 2) if r.perte_moy < 0 else None,
                                  positif_sans_meilleure=bool(r.pnl_sans_meilleur > 0))
                             for i, r in enumerate(rentables.sort_values("pnl", ascending=False).itertuples())])
    SORTIES.mkdir(exist_ok=True)
    (SORTIES / "cohorte_pilote.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str), flush=True)


if __name__ == "__main__":
    c = base()
    schema(c)
    etape = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if etape in ("marche", "tout"):
        charger_sol(c)
        charger_prix(c)
    if etape in ("rapport", "tout"):
        rapport(c)
