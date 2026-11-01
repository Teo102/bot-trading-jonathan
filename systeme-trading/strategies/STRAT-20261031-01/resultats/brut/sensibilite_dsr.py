"""Sensibilité du DSR à N, à V et à la série (réalisée ou réévaluée chaque jour). Lecture seule des exports et des bougies.
Calcul principal : série réévaluée, V réévaluée sur les 11 essais de même période, N = 13. Calcul second : série réalisée.
N = 19 ajoute les 6 contrôles de format antérieurs. N = 26 ajoute aussi les 7 backtests du contradicteur.
Pour E01 et E02, V vient d'une autre fenêtre : la V tranchée coupe les 11 séries sur la fenêtre de l'essai, sans rejeu de
backtest (approximation), et la V mise à l'échelle vaut V x 1673 / T."""
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
ORDRE = ["E00-ref","E01","E02","E09","R03","E03","E04","E05","E06","E07","E08","R01","R02"]
def load(e):
    data,*_=A.load_export(next((BT/e).glob("*.zip"))); return A.prepare_trades(A.select_strategy(data)[1]["trades"])
T={e:load(e) for e in PER}
def days(e): return A.parse_day(PER[e][0]),A.parse_day(PER[e][1])
RS={e:A.daily_series(T[e],10000.0,*days(e))["ret"] for e in PER}
MS={e:A.marked_series(T[e],10000.0,*days(e),A.load_closes(T[e]["pair"],DATA,*days(e)))["ret"] for e in PER}
R={e:RS[e].to_numpy() for e in PER}; M={e:MS[e].to_numpy() for e in PER}
sr=A.sharpe_daily
V11=float(np.var([sr(R[e]) for e in SAME],ddof=1)); V9=float(np.var([sr(R[e]) for e in SAMEFEE],ddof=1))
VM=float(np.var([sr(M[e]) for e in SAME],ddof=1)); VM9=float(np.var([sr(M[e]) for e in SAMEFEE],ddof=1))
print("V11 (réalisé, 11 essais)",V11,"V9 (mêmes frais, 9 essais)",V9,"V11 réévalué",VM,"V9 réévalué",VM9)
def moments(r): return float(stats.skew(r,bias=True)),float(stats.kurtosis(r,fisher=False,bias=True))
def dsr(r,n,v,g=None):
    g3,g4=g if g is not None else moments(r)
    s0,d,_=A.deflated_sharpe(sr(r),len(r),g3,g4,n,v); return d,s0
def tranche(series,e):
    a,b=days(e); vals=[sr(series[x].loc[a:b].to_numpy()) for x in SAME]
    return float(np.var(vals,ddof=1))
rows=[]
for e in ORDRE:
    r=R[e];m=M[e];t=len(r)
    g3,g4=moments(r); g3m,g4m=moments(m); s=sr(r)
    out={"essai":e,"T":t,"SR_ann_realise":A.annualize(s),"SR_ann_reevalue":A.annualize(sr(m)),"g3":g3,"g4":g4,"g3_reev":g3m,"g4_reev":g4m,
         "denominateur_psr_realise":1-g3*s+(g4-1)/4*s*s,"denominateur_psr_reevalue":1-g3m*sr(m)+(g4m-1)/4*sr(m)**2}
    cas={"N13_V11":(r,13,V11),"N12_V11":(r,12,V11),"N11_V11":(r,11,V11),"N19_V11":(r,19,V11),"N26_V11":(r,26,V11),"N13_V9":(r,13,V9),"N13_Vnul":(r,13,1.0/t),
         "N13_V11_reevalue":(m,13,VM),"N12_V11_reevalue":(m,12,VM),"N11_V11_reevalue":(m,11,VM),"N19_V11_reevalue":(m,19,VM),"N26_V11_reevalue":(m,26,VM),"N13_V9_reevalue":(m,13,VM9),"N13_Vnul_reevalue":(m,13,1.0/t)}
    for lab,(ser,n,v) in cas.items():
        d,s0=dsr(ser,n,v); out[lab]=d; out[lab+"_SR0ann"]=A.annualize(s0)
    out["N13_V11_normal"]=dsr(r,13,V11,(0.0,3.0))[0]
    if e in ("E01","E02"):
        vr,vm=tranche(RS,e),tranche(MS,e); er,em=V11*1673/t,VM*1673/t
        out.update(V_tranche_realise=vr,V_tranche_reevalue=vm,V_echelle_realise=er,V_echelle_reevalue=em,
                   N13_Vtranche=dsr(r,13,vr)[0],N13_Vechelle=dsr(r,13,er)[0],
                   N13_Vtranche_reevalue=dsr(m,13,vm)[0],N13_Vechelle_reevalue=dsr(m,13,em)[0],
                   N19_Vtranche_reevalue=dsr(m,19,vm)[0],N19_Vechelle_reevalue=dsr(m,19,em)[0],
                   N13_Vnul_T=1.0/t)
    rows.append(out)
    print({k:(round(v,4) if isinstance(v,float) else v) for k,v in out.items() if not k.endswith("_SR0ann")})
print("Sharpe réévalué par essai",{e:round(A.annualize(sr(M[e])),3) for e in SAME})
z=lambda p:stats.norm.ppf(p); g=float(np.euler_gamma); emax=lambda n:(1-g)*z(1-1/n)+g*z(1-1/(n*math.e))
print("Repère du § 4.3 refait : E[max] standardisé N=500",round(emax(500),3),"N=13",round(emax(13),3),"Sharpe annuel attendu sans edge, N=13, 4,58 ans",round(emax(13)/math.sqrt(1673/365),3),"N=19",round(emax(19)/math.sqrt(1673/365),3))
meta={"V_realise_11":V11,"V_realise_9":V9,"V_reevalue_11":VM,"V_reevalue_9":VM9,"repere_N13":float(emax(13)/math.sqrt(1673/365)),"repere_N19":float(emax(19)/math.sqrt(1673/365))}
json.dump(rows,open(base/"resultats/sensibilite_dsr.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
json.dump(meta,open(base/"resultats/sensibilite_dsr_meta.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
