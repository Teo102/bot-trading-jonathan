"""Bruit Monte Carlo de l'IC, reproduction exacte à graine fixe, force_exit, R effectif. N'importe PAS analyse_strat."""
import glob, io, json, re, zipfile
import numpy as np, pandas as pd

BASE = str(__import__("pathlib").Path(__file__).resolve().parents[2])
ALL = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "R01", "R02", "R03", "E00-ref"]


def load(e):
    z = zipfile.ZipFile(glob.glob(f"{BASE}/user_data/backtest_results/{e}/*.zip")[0])
    n = [x for x in z.namelist() if re.fullmatch(r"backtest-result-[\d_-]+\.json", x)][0]
    df = pd.DataFrame(next(iter(json.loads(z.read(n))["strategy"].values()))["trades"])
    df["o"] = pd.to_datetime(df.open_date, utc=True)
    df["c"] = pd.to_datetime(df.close_date, utc=True)
    return df.sort_values(["o", "c", "pair"], kind="stable").reset_index(drop=True)


def rm(tr):
    o, c, p = tr.o.to_numpy(), tr.c.to_numpy(), tr.profit_abs.to_numpy()
    return np.array([p[i] / (0.005 * (10000 + p[(c <= o[i]) & (o < o[i])].sum())) for i in range(len(tr))])


def dd(rs):
    e = np.r_[1.0, np.cumprod(1 + 0.005 * rs)]
    pk = np.maximum.accumulate(e)
    return ((pk - e) / pk).max()


for e in ALL:
    tr = load(e)
    r = rm(tr)
    n = len(r)
    j = json.load(open(f"{BASE}/resultats/{e}_metriques.json"))["trades"]
    rng = np.random.default_rng(0)
    b = rng.choice(r, (5000, n)).mean(1)
    lo, hi = np.percentile(b, [5, 95])
    mc = np.array([dd(rng.permutation(r)) for _ in range(5000)])
    d95 = np.percentile(mc, 95)
    # bruit de graine
    los = []
    for s in range(1, 41):
        g = np.random.default_rng(1000 + s)
        los.append(np.percentile(g.choice(r, (5000, n)).mean(1), 5))
    los = np.array(los)
    fx = tr.exit_reason == "force_exit"
    eff = tr.profit_abs / (tr.amount * (tr.open_rate - tr.stop_loss_abs).abs())
    print(f"{e:8s} seed0: lo {lo:.4f} hi {hi:.4f} dd95 {d95:.4f} ecart JSON {abs(lo-j['ic90_bas']):.1e} {abs(hi-j['ic90_haut']):.1e} {abs(d95-j['dd_95']):.1e}"
          f" | 40 graines: lo moy {los.mean():+.4f} sd {los.std():.4f} min {los.min():+.4f} max {los.max():+.4f} part>0 {(los>0).mean():.2f}"
          f" | sans force_exit esp {r[~fx.to_numpy()].mean():+.3f} (force n {int(fx.sum())} R {np.round(r[fx.to_numpy()],2).tolist()})"
          f" | R effectif moyen {eff.mean():+.3f} mediane stop {eff[tr.exit_reason=='stop_loss'].median():.3f}")
