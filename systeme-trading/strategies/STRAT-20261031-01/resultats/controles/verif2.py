"""Erreurs de définition : équité réévaluée, DSR sur série à zéros, IC corrélé, semestres. N'importe PAS analyse_strat."""
import csv, glob, io, json, math, re, zipfile
from datetime import date, datetime, timedelta
from statistics import NormalDist

import numpy as np
import pandas as pd

BASE = str(__import__("pathlib").Path(__file__).resolve().parents[2])
DATA = f"{BASE}/user_data/data/binance/futures"
LIMIT = pd.Timestamp("2025-07-31", tz="UTC")
ND = NormalDist()
ALL = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "R01", "R02", "R03", "E00-ref"]
SAME = ["E00-ref", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "R01", "R02", "R03"]
SAME9 = ["E00-ref", "E03", "E04", "E05", "E06", "E07", "E08", "R01", "R02"]
PER = {e: ("2021-01-01", "2025-07-31") for e in ALL}
PER["E01"] = ("2021-01-01", "2024-06-30")
PER["E02"] = ("2024-07-01", "2025-07-31")


def trades(e):
    z = zipfile.ZipFile(glob.glob(f"{BASE}/user_data/backtest_results/{e}/*.zip")[0])
    n = [x for x in z.namelist() if re.fullmatch(r"backtest-result-[\d_-]+\.json", x)][0]
    s = next(iter(json.loads(z.read(n))["strategy"].values()))
    df = pd.DataFrame(s["trades"])
    df["o"] = pd.to_datetime(df["open_date"], utc=True)
    df["c"] = pd.to_datetime(df["close_date"], utc=True)
    return df.sort_values(["o", "c", "pair"]).reset_index(drop=True)


T = {e: trades(e) for e in ALL}
_px = {}


def px(p):
    if p not in _px:
        d = pd.read_feather(f"{DATA}/{p.split('/')[0]}_USDT_USDT-1d-futures.feather", columns=["date", "high", "low", "close"])
        d["date"] = pd.to_datetime(d["date"], utc=True)
        d = d[d["date"] <= LIMIT].set_index("date")
        _px[p] = d
    return _px[p]


def series(e, mode="close"):
    a, b = PER[e]
    days = pd.date_range(a, b, freq="D", tz="UTC")
    eq = np.full(len(days), 10000.0)
    pos = {d: i for i, d in enumerate(days)}
    for _, t in T[e].iterrows():
        io_, ic = pos[t.o.normalize()], pos[t.c.normalize()]
        eq[ic:] += t.profit_abs
        if mode == "real" or ic == io_:
            continue
        sg = -1 if t.is_short else 1
        p = px(t.pair)
        n = ic - io_
        for k in range(io_, ic):
            if mode == "worst":
                row = p.loc[days[k]]
                price = row["low"] if sg == 1 else row["high"]
            else:
                price = p.loc[days[k], "close"]
            lat = sg * t.amount * (price - t.open_rate)
            if mode == "full":
                lat += -t.amount * t.fee_open * t.open_rate + t.funding_fees * ((k - io_ + 1) / (n + 1))
            eq[k] += lat
    return days, eq


def rets(eq):
    return eq / np.r_[10000.0, eq[:-1]] - 1


def sr(r):
    return r.mean() / r.std(ddof=1)


def mom(r):
    x = r - r.mean()
    m2 = (x ** 2).mean()
    return (x ** 3).mean() / m2 ** 1.5, (x ** 4).mean() / m2 ** 2


def mdd(eq):
    e = np.r_[10000.0, eq]
    pk = np.maximum.accumulate(e)
    return ((pk - e) / pk).max()


def emax(n):
    g = 0.5772156649015329
    return (1 - g) * ND.inv_cdf(1 - 1 / n) + g * ND.inv_cdf(1 - 1 / (n * math.e))


def dsr(s, t, g3, g4, n, v):
    den = 1 - g3 * s + (g4 - 1) / 4 * s * s
    return ND.cdf((s - math.sqrt(v) * emax(n)) * math.sqrt(t - 1) / math.sqrt(den))


REAL = {e: series(e, "real") for e in ALL}
R = {e: rets(REAL[e][1]) for e in ALL}
MTM = {e: series(e, "close") for e in ALL}
M = {e: rets(MTM[e][1]) for e in ALL}
FULL = {e: series(e, "full") for e in ("E01", "E02", "E09", "E00-ref")}
WORST = {e: series(e, "worst") for e in ("E01", "E02", "E09", "E00-ref")}
V11 = np.var([sr(R[e]) for e in SAME], ddof=1)
V9 = np.var([sr(R[e]) for e in SAME9], ddof=1)
VM = np.var([sr(M[e]) for e in SAME], ddof=1)
print(f"V11 {V11:.4e}  V9 {V9:.4e}  V11 reevalue {VM:.4e}  1/T(1673) {1/1673:.4e} ratio {1/1673/V11:.2f}")

print("\n=== 1. Realise vs reevalue (cloture 1d) vs complet (+frais et financement courus) vs pire intrajour")
for e in ALL:
    d = dict(SR_real=sr(R[e]) * 365 ** .5, SR_mtm=sr(M[e]) * 365 ** .5, DD_real=mdd(REAL[e][1]), DD_mtm=mdd(MTM[e][1]))
    a = (REAL[e][1][-1] / 1e4) ** (365 / len(R[e])) - 1
    d["cal_real"] = a / d["DD_real"]
    d["cal_mtm"] = a / d["DD_mtm"]
    neg = np.minimum(M[e], 0)
    d["sortino_real"] = R[e].mean() / np.sqrt((np.minimum(R[e], 0) ** 2).mean()) * 365 ** .5
    d["sortino_mtm"] = M[e].mean() / np.sqrt((neg ** 2).mean()) * 365 ** .5
    if e in FULL:
        fr = rets(FULL[e][1])
        d["SR_full"] = sr(fr) * 365 ** .5
        d["DD_full"] = mdd(FULL[e][1])
        d["DD_worst"] = mdd(WORST[e][1])
    print(e, {k: round(float(v), 3) for k, v in d.items()})
print("DD reel > DD95 Monte Carlo :", end=" ")
for e in ALL:
    j = json.load(open(f"{BASE}/resultats/{e}_metriques.json"))
    dd95 = j["trades"]["dd_95"]
    print(f"{e}: real {mdd(REAL[e][1]):.3f} mtm {mdd(MTM[e][1]):.3f} mc95 {dd95:.3f} ;", end=" ")
print()

print("\n=== 2. DSR sous variantes")
print("essai | SR ann | den | DSR publie | normal(g3=0,g4=3) | mtm(V11mtm) | mtm(1/T) | sans meilleur jour (g3,g4 recalc) | mensuel realise | mensuel mtm")
MONTH = {}
for key, src in (("real", REAL), ("mtm", MTM)):
    MONTH[key] = {}
    for e in ALL:
        s = pd.Series(src[e][1], index=src[e][0]).resample("ME").last()
        MONTH[key][e] = (s / s.shift(1, fill_value=10000.0) - 1).to_numpy()
Vmr = np.var([sr(MONTH["real"][e]) for e in SAME], ddof=1)
Vmm = np.var([sr(MONTH["mtm"][e]) for e in SAME], ddof=1)
print(f"V mensuelle realisee {Vmr:.4e}, reevaluee {Vmm:.4e}, 1/55 = {1/55:.4e}")
for e in ALL:
    r, m = R[e], M[e]
    s = sr(r)
    g3, g4 = mom(r)
    den = 1 - g3 * s + (g4 - 1) / 4 * s * s
    pub = dsr(s, len(r), g3, g4, 13, V11)
    norm = dsr(s, len(r), 0, 3, 13, V11)
    gm3, gm4 = mom(m)
    mt = dsr(sr(m), len(m), gm3, gm4, 13, VM)
    mt2 = dsr(sr(m), len(m), gm3, gm4, 13, 1 / len(m))
    i = np.argmax(r)
    rr = np.delete(r, i)
    g3b, g4b = mom(rr)
    no = dsr(sr(rr), len(rr), g3b, g4b, 13, V11)
    mr = MONTH["real"][e]
    a3, a4 = mom(mr)
    mm = MONTH["mtm"][e]
    b3, b4 = mom(mm)
    print(f"{e:8s} SR {s*365**.5:.3f} den {den:.3f} pub {pub:.3f} norm {norm:.3f} mtm {mt:.3f} (g3 {gm3:.2f} g4 {gm4:.1f}) mtm1/T {mt2:.3f} sans_top1 {no:.3f} (SR {sr(rr)*365**.5:.3f}, meilleur jour {REAL[e][0][i].date()} {r[i]*100:.2f}%) mois_real {dsr(sr(mr),len(mr),a3,a4,13,Vmr):.3f} mois_mtm {dsr(sr(mm),len(mm),b3,b4,13,Vmm):.3f}")

print("\n=== 3. V coherente avec la periode de E01 et E02 : V transversale sur les memes fenetres (tranches des 11 series)")
for e, (a, b) in dict(E01=("2021-01-01", "2024-06-30"), E02=("2024-07-01", "2025-07-31")).items():
    vals = []
    for x in SAME:
        days, eq = REAL[x]
        ser = pd.Series(rets(eq), index=days).loc[a:b].to_numpy()
        vals.append(sr(ser))
    Vw = np.var(vals, ddof=1)
    g3, g4 = mom(R[e])
    print(e, f"T {len(R[e])} V tranche {Vw:.4e} (x{Vw/V11:.2f}) V echelle T {V11*1673/len(R[e]):.4e} 1/T {1/len(R[e]):.4e} | DSR publie {dsr(sr(R[e]),len(R[e]),g3,g4,13,V11):.3f} V_tranche {dsr(sr(R[e]),len(R[e]),g3,g4,13,Vw):.3f} V_echelle {dsr(sr(R[e]),len(R[e]),g3,g4,13,V11*1673/len(R[e])):.3f} 1/T {dsr(sr(R[e]),len(R[e]),g3,g4,13,1/len(R[e])):.3f} | SR ann des 11 sur la tranche min {min(vals)*365**.5:.2f} max {max(vals)*365**.5:.2f}")
print("V9 sur E00-ref:", round(dsr(sr(R['E00-ref']), 1673, *mom(R['E00-ref']), 13, V9), 3))

print("\n=== 4. Calibration du PSR sur la serie a zeros : ecart-type du SR, formule vs bootstrap")
rng = np.random.default_rng(20261101)


def boot_sd(r, L, sims=4000):
    n = len(r)
    out = np.empty(sims)
    if L == 1:
        for i in range(sims):
            out[i] = sr(r[rng.integers(0, n, n)])
    else:
        k = n // L + 1
        for i in range(sims):
            st = rng.integers(0, n - L + 1, k)
            idx = (st[:, None] + np.arange(L)).ravel()[:n]
            out[i] = sr(r[idx])
    return out


for e in ("E00-ref", "E01", "E02", "E03", "R01", "E07", "E09"):
    for lab, r in (("real", R[e]), ("mtm", M[e])):
        s = sr(r)
        g3, g4 = mom(r)
        den = 1 - g3 * s + (g4 - 1) / 4 * s * s
        f = math.sqrt(den / (len(r) - 1))
        iid = boot_sd(r, 1)
        blk = boot_sd(r, 30)
        s0 = math.sqrt(V11 if lab == "real" else VM) * emax(13)
        # P(SR* > SR0) par bootstrap sur la distribution centree : part des tirages avec SR*-s < s-s0 (pivot)
        pv_iid = np.mean(iid - s < s - s0)
        pv_blk = np.mean(blk - s < s - s0)
        print(f"{e:8s} {lab:4s} SR {s:.4f} sd_formule {f:.4f} sd_iid {iid.std():.4f} sd_bloc30 {blk.std():.4f} | P(formule) {ND.cdf((s-s0)/f):.3f} P(iid) {pv_iid:.3f} P(bloc30) {pv_blk:.3f} | sd_normale {math.sqrt((1+s*s/2)/(len(r)-1)):.4f}")

print("\n=== 5. IC 90 % de l'esperance R : iid vs grappes (ouverture du meme mois, episodes chevauchants, blocs de trades)")


def Rm(e):
    tr = T[e]
    o, c, p = tr.o.to_numpy(), tr.c.to_numpy(), tr.profit_abs.to_numpy()
    return np.array([p[i] / (0.005 * (10000 + p[(c <= o[i]) & (o < o[i])].sum())) for i in range(len(tr))])


def pct(x):
    return np.percentile(x, [5, 95]).round(3).tolist()


rows = {}
for e in ALL:
    r = Rm(e)
    tr = T[e]
    n = len(r)
    iid = r[rng.integers(0, n, (5000, n))].mean(1)
    # grappes par mois d'ouverture
    gm = tr.o.dt.strftime("%Y-%m").to_numpy()
    uniq = np.unique(gm)
    groups = [r[gm == u] for u in uniq]
    gs, gc = np.array([g.sum() for g in groups]), np.array([len(g) for g in groups])
    pick = rng.integers(0, len(groups), (5000, len(groups)))
    mo = gs[pick].sum(1) / gc[pick].sum(1)
    # épisodes chevauchants
    ep = []
    cur, end = -1, None
    for o, c in zip(tr.o, tr.c):
        if end is None or o >= end:
            cur += 1
            end = c
        else:
            end = max(end, c)
        ep.append(cur)
    ep = np.array(ep)
    es = np.array([r[ep == u].sum() for u in np.unique(ep)])
    ec = np.array([(ep == u).sum() for u in np.unique(ep)])
    pick = rng.integers(0, len(es), (5000, len(es)))
    em = es[pick].sum(1) / ec[pick].sum(1)
    # blocs mobiles de 10 trades
    L = 10
    st = rng.integers(0, n - L + 1, (5000, n // L + 1))
    idx = (st[:, :, None] + np.arange(L)).reshape(5000, -1)[:, :n]
    bl = r[idx].mean(1)
    # dépendance observée
    ac1 = np.corrcoef(r[:-1], r[1:])[0, 1]
    # part de trades qui chevauchent un autre
    ov = sum(1 for i in range(n) if ((tr.o <= tr.c[i]) & (tr.c >= tr.o[i])).sum() > 1) / n
    # sans les trois meilleurs
    print(f"{e:8s} n {n} esp {r.mean():+.3f} iid {pct(iid)} mois({len(uniq)}) {pct(mo)} episodes({len(es)}) {pct(em)} bloc10 {pct(bl)} ac1 {ac1:+.3f} part_chevauchement {ov:.2f}")

print("\n=== 6. Correlation entre trades simultanes (E00-ref): R des paires de trades qui se chevauchent")
r = Rm("E00-ref")
tr = T["E00-ref"]
pairs = []
for i in range(len(tr)):
    for j in range(i + 1, len(tr)):
        if tr.o[j] <= tr.c[i] and tr.c[j] >= tr.o[i]:
            pairs.append((r[i], r[j], tr.is_short[i] == tr.is_short[j]))
pa = np.array([(a, b) for a, b, _ in pairs])
same = [(a, b) for a, b, s in pairs if s]
print("paires", len(pa), "corr", round(np.corrcoef(pa.T)[0, 1], 3), "corr rang", round(pd.DataFrame(pa).corr("spearman").iloc[0, 1], 3), "meme sens", len(same), "corr rang meme sens", round(pd.DataFrame(same).corr("spearman").iloc[0, 1], 3))

print("\n=== 7. Semestres : affectation a la cloture vs reevalue chaque jour")


def lab(d):
    return f"{d.year}-S{1 if d.month <= 6 else 2}"


for e in ("E01", "E02", "E00-ref", "E09"):
    days, eq = MTM[e]
    dr, er = REAL[e]
    prev_m, prev_r = 10000.0, 10000.0
    labs = [lab(d) for d in days]
    out = []
    for L in dict.fromkeys(labs):
        idx = [i for i, x in enumerate(labs) if x == L]
        pm = eq[idx[-1]] - prev_m
        pr = er[idx[-1]] - prev_r
        prev_m, prev_r = eq[idx[-1]], er[idx[-1]]
        out.append((L, len(idx), round(pr), round(pm)))
    tr = T[e]
    st = tr[[lab(o) != lab(c) for o, c in zip(tr.o, tr.c)]]
    print(e, "(sem, jours, pnl_realise, pnl_reevalue)", out)
    print("   positifs realise", sum(x[2] > 0 for x in out), "/", len(out), "| reevalue", sum(x[3] > 0 for x in out), "/", len(out), "| hors partiel realise", sum(x[2] > 0 for x in out if x[1] > 100), "/", sum(1 for x in out if x[1] > 100), "reevalue", sum(x[3] > 0 for x in out if x[1] > 100),
          "| signes differents", [x[0] for x in out if (x[2] > 0) != (x[3] > 0)], "| trades a cheval", len(st), "pnl", round(st.profit_abs.sum()), "somme abs", round(st.profit_abs.abs().sum()), "| force_exit pnl", round(tr[tr.exit_reason == "force_exit"].profit_abs.sum()), "n", int((tr.exit_reason == "force_exit").sum()))
    last = tr[tr.c >= pd.Timestamp("2025-07-01", tz="UTC")] if e != "E01" else tr[tr.c >= pd.Timestamp("2024-01-01", tz="UTC")]
    print("   dernier semestre:", last[["pair", "open_date", "close_date", "is_short", "exit_reason", "profit_abs"]].round(1).assign(open_date=last.open_date.str[:10], close_date=last.close_date.str[:10]).tail(6).to_string(index=False).replace("\n", " || "))
    sh = {L: None for L in dict.fromkeys(labs)}
print()
print("Meilleur trade par essai (pnl, R):")
for e in ("E03", "R01", "E07", "E00-ref"):
    r = Rm(e)
    i = int(np.argmax(r))
    t = T[e].iloc[i]
    print(e, t.pair, t.open_date[:10], t.close_date[:10], "R", round(r[i], 2), "pnl", round(t.profit_abs), "mise", round(t.stake_amount), "exit", t.exit_reason, "%", round(100 * (R[e].max()), 2))
print("Controles § 13 / §14: emax(13)/sqrt(1673/365) =", round(emax(13) / math.sqrt(1673 / 365), 3), "emax(500)", round(emax(500), 3))
print("jours sans cloture E00-ref", int((R['E00-ref'] == 0).sum()), "sur", len(R['E00-ref']))
print("Autocorrelation lag1 mtm:", {e: round(float(np.corrcoef(M[e][:-1], M[e][1:])[0, 1]), 3) for e in ("E00-ref", "E01", "E02")})
sems = {"Sharpe 3 ans": None}
