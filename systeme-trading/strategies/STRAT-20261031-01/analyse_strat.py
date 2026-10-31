"""Analyse d'un export de backtest freqtrade pour validation-edge.
Usage : python analyse_strat.py <export .zip ou .json> [--risk 0.005] [--wallet 10000]
Sortie : nombre de trades, espérance en R et intervalle à 90 %, drawdown réalisé,
drawdown du 95e centile (Monte Carlo sur l'ordre des trades), coûts doublés."""
import argparse, json, sys, zipfile
import numpy as np

def load_trades(path):
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            name = [n for n in z.namelist() if n.endswith(".json") and "config" not in n and "meta" not in n][0]
            data = json.loads(z.read(name))
    else:
        data = json.load(open(path))
    strat = next(iter(data["strategy"].values()))
    return strat["trades"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--risk", type=float, default=0.005)
    ap.add_argument("--wallet", type=float, default=10000.0); ap.add_argument("--sims", type=int, default=5000)
    a = ap.parse_args()
    trades = sorted(load_trades(a.path), key=lambda t: t["open_date"])
    if not trades:
        sys.exit("Aucun trade.")
    eq = a.wallet; R = []; fees = []
    for t in trades:
        risk_amt = a.risk * eq                       # risque prévu à l'entrée
        R.append(t["profit_abs"] / risk_amt)
        fee = (t.get("fee_open", 0) or 0) + (t.get("fee_close", 0) or 0)
        fees.append(fee * t["stake_amount"] / risk_amt)  # coût des frais en R (approximation)
        eq += t["profit_abs"]
    R = np.array(R); fees = np.array(fees); n = len(R)
    rng = np.random.default_rng(0)
    boot = rng.choice(R, (5000, n)).mean(1)
    lo, hi = np.percentile(boot, [5, 95])
    def max_dd(rs):
        e = np.cumprod(1 + a.risk * rs); pk = np.maximum.accumulate(e); return ((pk - e) / pk).max()
    dd_real = max_dd(R)
    dd_mc = np.array([max_dd(rng.permutation(R)) for _ in range(a.sims)])
    wins = R[R > 0]; losses = R[R <= 0]
    print(f"Trades : {n}  (longs {sum(1 for t in trades if not t.get('is_short'))}, shorts {sum(1 for t in trades if t.get('is_short'))})")
    print(f"Taux de réussite : {len(wins)/n:.1%}   gain moyen {wins.mean() if len(wins) else 0:.2f} R   perte moyenne {losses.mean() if len(losses) else 0:.2f} R")
    print(f"Espérance : {R.mean():+.3f} R   intervalle 90 % : [{lo:+.3f} ; {hi:+.3f}] R")
    print(f"Espérance avec frais doublés (approx.) : {(R - fees).mean():+.3f} R")
    print(f"Drawdown réalisé : {dd_real:.1%}   drawdown 95e centile (Monte Carlo) : {np.percentile(dd_mc, 95):.1%}")
    print(f"Part du gain portée par le meilleur trade : {R.max()/R.sum():.0%}" if R.sum() > 0 else "Gain total négatif ou nul")
    print(f"Capital final : {eq:,.0f} (départ {a.wallet:,.0f})")

if __name__ == "__main__":
    main()
