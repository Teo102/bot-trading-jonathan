"""Sensibilité de l'IC par blocs et du Monte Carlo par blocs : longueur des blocs, repli circulaire, bruit de graine.
Lecture seule des exports et des bougies. Ces chiffres servent à lire la méthode, ils ne la choisissent pas sur la performance."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
import analyse_strat as A
PER = {"E00-ref": ("2021-01-01","2025-07-31"), "E01": ("2021-01-01","2024-06-30"), "E02": ("2024-07-01","2025-07-31"), "E05": ("2021-01-01","2025-07-31"),
       "E07": ("2021-01-01","2025-07-31"), "E08": ("2021-01-01","2025-07-31"), "E09": ("2021-01-01","2025-07-31")}
DATA = ROOT/"user_data/data/binance/futures"; S = 50000
def noncirc(r, L, sims, seed):
    rng = np.random.default_rng(seed); n = len(r); out = []
    for step in A._by_batches(sims):
        st = rng.integers(0, n-L+1, (step, n//L+1)); idx = (st[:,:,None]+np.arange(L)).reshape(step,-1)[:,:n]; out.append(r[idx].mean(1))
    return [float(x) for x in np.percentile(np.concatenate(out),[5,95])]
out = {"tirages": S, "graine": A.SEED_BLOCS, "essais": {}}
for e,(a,b) in PER.items():
    data,*_ = A.load_export(next((ROOT/"user_data/backtest_results"/e).glob("*.zip")))
    df = A.prepare_trades(A.select_strategy(data)[1]["trades"]); r = A.r_multiples(df,10000.0,0.005)[0]
    st,en = A.parse_day(a),A.parse_day(b); mk = A.marked_series(df,10000.0,st,en,A.load_closes(df["pair"],DATA,st,en))
    row = {"esperance_R": float(r.mean()), "trades": len(r)}
    for L in (5,10,20): row[f"blocs_circulaires_{L}"] = list(A.block_ci(r,L,S,[A.SEED_BLOCS,1]))
    row["blocs_mobiles_sans_repli_10"] = noncirc(r,10,S,[A.SEED_BLOCS,5])
    los = [A.block_ci(r,10,S,[1000+k,1])[0] for k in range(20)]
    row["bruit_borne_basse_blocs10"] = {"graines": 20, "moyenne": float(np.mean(los)), "ecart_type": float(np.std(los)), "min": float(np.min(los)), "max": float(np.max(los))}
    for L in (15,30,60): row[f"mc_blocs_{L}_jours"] = A.block_drawdown_quantiles(mk["ret"].to_numpy(),L,S,[A.SEED_BLOCS,4])
    row["ret_vol_annualisee"] = float(mk["ret"].std(ddof=1)*365**.5)
    out["essais"][e] = row; print(e, json.dumps(row, ensure_ascii=False))
(Path(__file__).resolve().parent/"sorties/ic_sensibilite.json").write_text(json.dumps(out,ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
