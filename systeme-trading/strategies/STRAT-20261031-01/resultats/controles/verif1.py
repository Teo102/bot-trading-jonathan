"""Recalcul indépendant depuis les .zip bruts. N'importe PAS analyse_strat."""
import csv, glob, hashlib, io, json, math, os, re, sys, zipfile
from datetime import date, datetime, timedelta, timezone
from statistics import NormalDist

import numpy as np
import pandas as pd

BASE = str(__import__("pathlib").Path(__file__).resolve().parents[2])
ND = NormalDist()
ALL = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "R01", "R02", "R03", "E00-ref"]
PER = {e: (date(2021, 1, 1), date(2025, 7, 31)) for e in ALL}
PER["E01"] = (date(2021, 1, 1), date(2024, 6, 30))
PER["E02"] = (date(2024, 7, 1), date(2025, 7, 31))
SAME = ["E00-ref", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "R01", "R02", "R03"]


def read_zip(e):
    zs = glob.glob(f"{BASE}/user_data/backtest_results/{e}/*.zip")
    assert len(zs) == 1, (e, zs)
    raw = open(zs[0], "rb").read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    names = z.namelist()
    res = [n for n in names if re.fullmatch(r"backtest-result-[\d_-]+\.json", n)][0]
    d = json.loads(z.read(res))
    assert len(d["strategy"]) == 1
    name, s = next(iter(d["strategy"].items()))
    py = [n for n in names if n.endswith(".py")]
    cfg = json.loads(z.read([n for n in names if n.endswith("_config.json")][0]))
    return dict(sha=hashlib.sha256(raw).hexdigest(), name=name, s=s, py={n: z.read(n) for n in py}, cfg=cfg, zip=zs[0])


def dt(x):
    return datetime.fromisoformat(x)


def ref_equities(tr, wallet=10000.0):
    out = []
    for i, t in enumerate(tr):
        o = dt(t["open_date"])
        acc = wallet
        for j, u in enumerate(tr):
            if j != i and dt(u["close_date"]) <= o and dt(u["open_date"]) < o:
                acc += u["profit_abs"]
        out.append(acc)
    return out


def daily_real(tr, a, b, wallet=10000.0):
    days = [a + timedelta(days=i) for i in range((b - a).days + 1)]
    pnl = {d: 0.0 for d in days}
    for t in tr:
        pnl[dt(t["close_date"]).date()] += t["profit_abs"]
    eq, cur = [], wallet
    for d in days:
        cur += pnl[d]
        eq.append(cur)
    return days, np.array(eq), pnl


def rets(eq, wallet=10000.0):
    prev = np.r_[wallet, eq[:-1]]
    return eq / prev - 1


def mdd(eq, wallet=10000.0):
    peak, worst = wallet, 0.0
    for x in eq:
        peak = max(peak, x)
        worst = max(worst, (peak - x) / peak)
    return worst


def sr(r):
    m = sum(r) / len(r)
    v = sum((x - m) ** 2 for x in r) / (len(r) - 1)
    return m / math.sqrt(v)


def moments(r):
    n = len(r)
    m = sum(r) / n
    m2 = sum((x - m) ** 2 for x in r) / n
    m3 = sum((x - m) ** 3 for x in r) / n
    m4 = sum((x - m) ** 4 for x in r) / n
    return m3 / m2 ** 1.5, m4 / m2 ** 2  # asymétrie, kurtosis NON excédentaire


def emax(n):
    g = 0.5772156649015329
    return (1 - g) * ND.inv_cdf(1 - 1 / n) + g * ND.inv_cdf(1 - 1 / (n * math.e))


def dsr(s, t, g3, g4, n, v):
    s0 = math.sqrt(v) * emax(n)
    den = 1 - g3 * s + (g4 - 1) / 4 * s * s
    return s0, ND.cdf((s - s0) * math.sqrt(t - 1) / math.sqrt(den)), den


Z = {e: read_zip(e) for e in ALL}
J = {e: json.load(open(f"{BASE}/resultats/{e}_metriques.json")) for e in ALL}
CSV = {r["id_essai"]: r for r in csv.DictReader(open(f"{BASE}/REGISTRE_ESSAIS.csv", encoding="utf-8"))}

print("=== A. recalcul indépendant vs JSON vs CSV")
SR = {}
TR = {}
RET = {}
for e in ALL:
    s = Z[e]["s"]
    tr = sorted(s["trades"], key=lambda t: (t["open_date"], t["close_date"], t["pair"]))
    TR[e] = tr
    a, b = PER[e]
    days, eq, pnl = daily_real(tr, a, b)
    r = rets(eq)
    RET[e] = r
    refs = ref_equities(tr)
    R = np.array([t["profit_abs"] / (0.005 * x) for t, x in zip(tr, refs)])
    SR[e] = sr(r)
    cagr = (eq[-1] / 10000) ** (365 / len(days)) - 1
    dd = mdd(eq)
    sortino = (r.mean() / math.sqrt(np.mean(np.minimum(r, 0) ** 2))) * math.sqrt(365)
    res = dict(trades=len(tr), longs=sum(1 for t in tr if not t["is_short"]), esp=R.mean(), win=(R > 0).mean(),
               sharpe=SR[e] * math.sqrt(365), sortino=sortino, calmar=cagr / dd, dd=dd, final=eq[-1], cagr=cagr)
    m = J[e]["metriques_quotidiennes"]
    t_ = J[e]["trades"]
    jv = dict(trades=t_["trades"], longs=t_["longs"], esp=t_["esperance_R"], win=t_["taux_reussite"],
              sharpe=m["sharpe_annualise"], sortino=m["sortino_annualise"], calmar=m["calmar"], dd=m["dd_reel"],
              final=t_["capital_final"], cagr=m["rendement_annualise"])
    gaps = {k: abs(res[k] - jv[k]) for k in res}
    c = CSV[e]
    csvgap = dict(trades=int(c["trades"]) - res["trades"], esp=float(c["esperance_R"]) - res["esp"],
                  dd=float(c["dd_reel"]) - res["dd"], sharpe=float(c.get("sharpe_realise", c.get("sharpe"))) - res["sharpe"])
    print(e, {k: round(float(v), 4) for k, v in res.items()})
    print("   ecart max JSON", f"{max(gaps.values()):.2e}", "| CSV", {k: round(float(v), 5) for k, v in csvgap.items()},
          "| ft final", round(s["final_balance"], 4), "ft total_trades", s["total_trades"], "ft fee", tr[0]["fee_open"],
          "| timerange", s["timerange"], "| force_exit", sum(1 for t in tr if t["exit_reason"] == "force_exit"),
          "| derniere cloture", max(t["close_date"] for t in tr), "| left_open", s.get("left_open_trades", {}).get("trades") if isinstance(s.get("left_open_trades"), dict) else None)
    # trade par trade : prix + frais + financement = profit_abs ?
    err = []
    for t in tr:
        sg = -1 if t["is_short"] else 1
        calc = sg * t["amount"] * (t["close_rate"] - t["open_rate"]) - t["amount"] * (t["fee_open"] * t["open_rate"] + t["fee_close"] * t["close_rate"]) + (t.get("funding_fees") or 0)
        err.append(abs(calc - t["profit_abs"]))
    print("   recomposition profit_abs: ecart abs max", round(max(err), 4), "somme", round(sum(err), 4))
    if e in ("E01", "E02", "E09", "E00-ref"):
        lab = lambda d: f"{d.year}-S{1 if d.month <= 6 else 2}"
        sems = {}
        for d, ret, q in zip(days, r, [pnl[d] for d in days]):
            sems.setdefault(lab(d), dict(rets=[], pnl=0.0, n=0))
            sems[lab(d)]["rets"].append(ret)
            sems[lab(d)]["pnl"] += q
        Rs = {}
        for t, x in zip(tr, R):
            Rs.setdefault(lab(dt(t["close_date"]).date()), []).append(x)
        js = {row["semestre"]: row for row in J[e]["semestres"]["semestres"]}
        for k, v in sems.items():
            rr = Rs.get(k, [])
            sh = sr(v["rets"]) * math.sqrt(365)
            mr = np.mean(rr) if rr else None
            j = js[k]
            ok = abs(sh - j["sharpe_annualise"]) < 1e-9 and abs(v["pnl"] - j["pnl"]) < 1e-6 and len(rr) == j["trades"] and (mr is None or abs(mr - j["esperance_R"]) < 1e-9) and len(v["rets"]) == j["jours"]
            print(f"   {k} jours {len(v['rets'])} trades {len(rr)} espR {mr if mr is None else round(mr,3)} sharpe {sh:.3f} pnl {v['pnl']:.2f} accord_JSON {ok}")
        print("   positifs", sum(1 for v in sems.values() if v["pnl"] > 0), "/", len(sems), "JSON", J[e]["semestres"]["n_positifs"], "/", J[e]["semestres"]["n_semestres"])

print("\n=== B. DSR indépendant vs JSON vs CSV")
V11 = np.var([SR[e] for e in SAME], ddof=1)
SAME_ = [SR[e] for e in SAME]
print("V11", V11, "liste", {e: round(SR[e], 5) for e in SAME})
print("Exemple papier (de mémoire: SR0=0.1132, DSR=0.9004):", dsr(2.5 / math.sqrt(250), 1250, -3, 10, 100, 0.5 / 250))
print("emax(13)", emax(13), "SR0 annualisé", math.sqrt(V11) * emax(13) * math.sqrt(365))
reg = json.load(open(f"{BASE}/resultats/registre_dsr.json"))
print("registre_dsr: n_essais_declares", reg["n_essais_declares"], "len", len(reg["essais"]), "Sharpe connus", sum(1 for x in reg["essais"] if x["sharpe_quotidien"] is not None))
for e in ALL:
    r = RET[e]
    g3, g4 = moments(list(r))
    s0, d, den = dsr(SR[e], len(r), g3, g4, 13, V11)
    jd = J[e]["dsr"]
    print(e, f"T {len(r)} SR {SR[e]:.5f} g3 {g3:.3f} g4 {g4:.2f} den {den:.4f} SR0 {s0:.5f} DSR {d:.4f}",
          f"| JSON N {jd['n_essais']} V {jd['v_sr_quotidien']:.4e} g3 {jd['g3_asymetrie']:.3f} g4 {jd['g4_kurtosis']:.2f} DSR {jd['dsr']:.4f} | CSV {CSV[e]['dsr']} | zeros {(r==0).sum()}")

print("\n=== C. registre <-> sortie brute")
BTXT = f"{BASE}/resultats/brut"
for e in ALL:
    c = CSV[e]
    s = Z[e]["s"]
    fee = Z[e]["s"]["trades"][0]["fee_open"]
    src = Z[e]["py"]
    ov = {}
    for n, b in src.items():
        ov.update(dict(re.findall(r"^\s{4}(entry_period|exit_period|atr_mult|atr_period|regime_period) = ([\d.]+)", b.decode(), flags=re.M)))
    jshabase = J[e]["tracabilite"]["sha256_export"]
    print(e, "| strategy", Z[e]["name"], "| variante CSV", c["variante"], "| fichiers .py", len(src), "| params source", ov,
          "| fee CSV", c["frais"], "zip", fee, "| timerange CSV", c["timerange"], "zip", s["timerange"],
          "| sha ok", jshabase == Z[e]["sha"], "| dry_run", Z[e]["cfg"].get("dry_run"),
          "| ic", c["ic90_bas"], round(J[e]["trades"]["ic90_bas"], 4), c["ic90_haut"], round(J[e]["trades"]["ic90_haut"], 4), "| dd95", c["dd_95"], round(J[e]["trades"]["dd_95"], 4))
print("sha py embarqué base:", {e: [hashlib.sha256(b).hexdigest()[:16] for b in Z[e]["py"].values()] for e in ("E01", "E02", "E09", "R03", "E00-ref", "E03")})
print("E10/E11:", {k: {f: CSV[k][f] for f in ("date", "trades", "esperance_R", "sharpe_realise", "dsr", "commentaire", "statut")} for k in ("E10", "E11")})
print("dossiers E10/E11 présents:", os.path.exists(f"{BASE}/user_data/backtest_results/E10"), os.path.exists(f"{BASE}/user_data/backtest_results/E11"), os.path.exists(f"{BASE}/resultats/E10_metriques.json"))
print("Lignes CSV hors préenregistrement:", {k: ("hors préenregistrement" in CSV[k]["commentaire"]) for k in ("R01", "R02", "R03", "E00-ref")})
np.save(os.path.join(os.path.dirname(__file__), "sr.npy"), np.array([SR[e] for e in ALL]))
