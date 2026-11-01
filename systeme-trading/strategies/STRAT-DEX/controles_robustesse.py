"""Contrôles de robustesse du test de persistance de STRAT-DEX (avenant 2 du 01/11/2026, écrit avant les résultats).

Lit la base SQLite produite par analyse_cohorte.py, sans réseau si les déployeurs sont déjà en cache.
Usage : python controles_robustesse.py            -> resultats/persistance_robustesse.json et .md
Aucune adresse complète n'est publiée. Aucun ordre, aucune clé.
"""
import json, math, sys
import numpy as np, pandas as pd

N_MIN, ALPHA_UNI, N_PERM, GRAINE = 30, 0.05, 10000, 20261101
COUPE_J = 45


def fisher_unilateral(a, b, c_, d):
    """P(X >= a) sous l'hypergéométrique, table [[A+B+, A+B-], [A-B+, A-B-]] : persistance positive."""
    n, r1, c1 = a + b + c_ + d, a + b, a + c_
    if n == 0 or r1 == 0 or c1 == 0:
        return 1.0
    pr = lambda k: math.comb(c1, k) * math.comb(n - c1, r1 - k) / math.comb(n, r1)
    return min(1.0, sum(pr(k) for k in range(a, min(r1, c1) + 1)))


def par_wallet(p):
    g = p.groupby("wallet")
    return pd.DataFrame({"n": g.size(), "pnl": g.pnl.sum(), "cout": g.cout.sum()}).assign(retour=lambda x: x.pnl / x.cout)


def sans_meilleure(p):
    """Retire, par wallet, sa meilleure position de la période."""
    if p.empty:
        return p
    idx = p.groupby("wallet").pnl.idxmax()
    return p.drop(index=idx)


def mesurer(p, t_fin, n_min_pos=3, rng=None):
    coupe = t_fin - COUPE_J * 86400
    pa, pb = p[p.t0 < coupe], p[p.t0 >= coupe]
    a, b = par_wallet(pa), par_wallet(pb)
    j = a[a.n >= n_min_pos].join(b[b.n >= n_min_pos], lsuffix="_a", rsuffix="_b", how="inner")
    out = {"wallets": int(len(j))}
    if len(j) < 3:
        return out
    ga, gb = j.pnl_a > 0, j.pnl_b > 0
    t = [int((ga & gb).sum()), int((ga & ~gb).sum()), int((~ga & gb).sum()), int((~ga & ~gb).sum())]
    rho = float(j.retour_a.rank().corr(j.retour_b.rank()))
    rng = rng or np.random.default_rng(GRAINE)
    ra, rb = j.retour_a.rank().to_numpy(), j.retour_b.rank().to_numpy()
    perm = np.array([np.corrcoef(ra, rng.permutation(rb))[0, 1] for _ in range(N_PERM)])
    out.update(tableau=dict(a_pos_b_pos=t[0], a_pos_b_neg=t[1], a_neg_b_pos=t[2], a_neg_b_neg=t[3]),
               part_b_pos_si_a_pos=t[0] / (t[0] + t[1]) if t[0] + t[1] else None,
               part_b_pos_si_a_neg=t[2] / (t[2] + t[3]) if t[2] + t[3] else None,
               p_fisher_unilateral=fisher_unilateral(*t), spearman=rho,
               p_spearman_unilateral=float((perm >= rho).mean()),
               survivants_observes=t[0], survivants_attendus_hasard=float(ga.mean() * gb.mean() * len(j)))
    return out


def soutient(m):
    """Règle de l'avenant 2 : n >= 30, Fisher unilatéral < 0,05, Spearman > 0 avec p < 0,05."""
    return bool(m.get("wallets", 0) >= N_MIN and m.get("p_fisher_unilateral", 1) < ALPHA_UNI
                and m.get("spearman", -1) > 0 and m.get("p_spearman_unilateral", 1) < ALPHA_UNI)


def evaluer(q, t_fin, graines):
    """q : positions des wallets qui passent les filtres. graines : ensemble (wallet, mint) qui ont fait entrer le wallet au tirage."""
    cle = list(zip(q.wallet, q.mint))
    variantes = {
        "base": q,
        "sans_jeton_graine": q[[k not in graines for k in cle]],
        "positions_soldees_seules": q[q.sorti.astype(bool)],
    }
    res = {k: mesurer(v, t_fin) for k, v in variantes.items()}
    coupe = t_fin - COUPE_J * 86400
    sm = pd.concat([sans_meilleure(q[q.t0 < coupe]), sans_meilleure(q[q.t0 >= coupe])])
    res["sans_meilleure_position_par_periode"] = mesurer(sm, t_fin)
    principal = soutient(res["base"])
    robuste = principal and all(soutient(res[k]) for k in res if k != "base")
    if res["base"].get("wallets", 0) < N_MIN:
        verdict = "non_concluant_echantillon_insuffisant"
    elif not principal:
        verdict = "aucune_persistance_detectee"
    elif not robuste:
        verdict = "persistance_fragile"
    else:
        verdict = "persistance_soutenue"
    return {"verdict": verdict, "regle": "avenant 2 du 01/11/2026", "variantes": res}


def main():
    sys.path.insert(0, ".")
    import analyse_cohorte as ac
    from dex_commun import base
    c = base()
    p, _ = ac.positions(c)
    statut, _ = ac.filtrer(c, p)
    passe = [w for w, s in statut.items() if not s]
    q = p[p.wallet.isin(passe)].copy()
    t_fin = int(pd.read_sql("SELECT MAX(ts) t FROM mouvements", c).t.iloc[0])
    g = pd.read_sql("SELECT DISTINCT wallet, mint FROM trades_gecko", c)
    res = evaluer(q, t_fin, set(zip(g.wallet, g.mint)))
    res["positions_filtrees"] = int(len(q))
    ac.SORTIES.mkdir(exist_ok=True)
    (ac.SORTIES / "persistance_robustesse.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
