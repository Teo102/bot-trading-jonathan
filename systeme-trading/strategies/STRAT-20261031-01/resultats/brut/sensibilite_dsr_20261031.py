"""Sensibilité du DSR à N, à V et à la série (réalisée ou réévaluée chaque jour). Lecture seule."""
import json, sys, math
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
base = Path(sys.argv[1]); sys.path.insert(0, str(base))
import analyse_strat as A
BT = base/"user_data/backtest_results"; DATA = base/"user_data/data/binance/futures"
SAME = ["E00-ref","E03","E04","E05","E06","E07","E08","E09","R01","R02","R03"]
SAMEFEE = ["E00-ref","E03","E04","E05","E06","E07","E08","R01","R02"]
PER = {e:("2021-01-01","2025-07-31") for e in SAME}; PER.update({"E01":("2021-01-01","2024-06-30"),"E02":("2024-07-01","2025-07-31")})
BASES = ["E00-ref","E01","E02","E09","R03"]
px = {}
def close(p):
    if p not in px:
        d=pd.read_feather(DATA/f"{p.split('/')[0]}_USDT_USDT-1d-futures.feather"); d["date"]=pd.to_datetime(d["date"],utc=True); px[p]=d.set_index("date")["close"]
    return px[p]
def load(e):
    data,*_=A.load_export(next((BT/e).glob("*.zip"))); return A.select_strategy(data)[1]["trades"]
T={e:load(e) for e in PER}
real={},{}
def s_real(e):
    a,b=PER[e]; return A.daily_series(A.prepare_trades(T[e]),10000.0,A.parse_day(a),A.parse_day(b))["ret"].to_numpy()
def s_mtm(e):
    a,b=PER[e]; days=pd.date_range(a,b,freq="D",tz="UTC"); eq=pd.Series(10000.0,index=days)
    for x in T[e]:
        o,c=pd.Timestamp(x["open_date"]),pd.Timestamp(x["close_date"]); sg=-1 if x["is_short"] else 1
        eq[eq.index>=c.normalize()]+=x["profit_abs"]
        d=days[(days>=o.normalize())&(days<c.normalize())]
        if len(d): eq.loc[d]+=sg*x["amount"]*(close(x["pair"]).reindex(d).to_numpy()-x["open_rate"])
    return (eq/eq.shift(1,fill_value=10000.0)-1).to_numpy()
R={e:s_real(e) for e in PER}; M={e:s_mtm(e) for e in PER}
sr=lambda r:A.sharpe_daily(r)
V11=float(np.var([sr(R[e]) for e in SAME],ddof=1)); V9=float(np.var([sr(R[e]) for e in SAMEFEE],ddof=1)); VM=float(np.var([sr(M[e]) for e in SAME],ddof=1))
print("V11 (réalisé, 11 essais)",V11,"V9 (mêmes frais, 9 essais)",V9,"V11 réévalué",VM)
def dsr(r,n,v):
    g3=float(stats.skew(r,bias=True)); g4=float(stats.kurtosis(r,fisher=False,bias=True))
    s0,d,_=A.deflated_sharpe(sr(r),len(r),g3,g4,n,v); return d,s0,g3,g4
rows=[]
for e in BASES:
    r=R[e];m=M[e];t=len(r); out={"essai":e,"T":t,"SR_ann_realise":A.annualize(sr(r)),"SR_ann_reevalue":A.annualize(sr(m))}
    for lab,(ser,n,v) in {"N13_V11":(r,13,V11),"N12_V11":(r,12,V11),"N11_V11":(r,11,V11),"N13_V9":(r,13,V9),"N13_Vnul":(r,13,1.0/t),"N13_V11_reevalue":(m,13,VM),"N13_Vnul_reevalue":(m,13,1.0/t)}.items():
        d,s0,g3,g4=dsr(ser,n,v); out[lab]=d; out[lab+"_SR0ann"]=A.annualize(s0)
        if lab=="N13_V11": out["g3"],out["g4"]=g3,g4
        if lab=="N13_V11_reevalue": out["g3_reev"],out["g4_reev"]=g3,g4
    rows.append(out)
    print({k:(round(v,4) if isinstance(v,float) else v) for k,v in out.items()})
print("Sharpe réévalué par essai",{e:round(A.annualize(sr(M[e])),3) for e in SAME})
z=lambda p:stats.norm.ppf(p); g=float(np.euler_gamma); emax=lambda n:(1-g)*z(1-1/n)+g*z(1-1/(n*math.e))
print("Repère du § 4.3 refait : E[max] standardisé N=500",round(emax(500),3),"N=13",round(emax(13),3),"Sharpe annuel attendu sans edge, N=13, 4,58 ans",round(emax(13)/math.sqrt(1673/365),3))
# DOGE et stops larges
early=min((x["open_date"],e) for e in T for x in T[e] if x["pair"].startswith("DOGE"))
print("Première entrée DOGE tous essais",early)
for x in T["E00-ref"]:
    if abs(x["open_rate"]-x["stop_loss_abs"])/x["open_rate"]>0.3: print("Stop > 30 %, E00-ref",x["pair"],x["open_date"],"short" if x["is_short"] else "long",x["exit_reason"],round(abs(x["open_rate"]-x["stop_loss_abs"])/x["open_rate"],3),"profit",round(x["profit_abs"],1))
for e in ["E00-ref","E01","E02"]:
    m=json.loads((base/"resultats"/f"{e}_metriques.json").read_text(encoding="utf-8"))
    print(e,{k:round(v,3) for k,v in m["trades"].items() if k.startswith("esperance")},"par_sens",json.dumps(m["par_sens"]))
json.dump(rows,open(base/"resultats/sensibilite_dsr.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
