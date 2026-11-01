import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from sim import *
import random
pd.set_option('display.width',220); pd.set_option('display.max_rows',300)
def R(D):
    D=D.sort_values('od').reset_index(drop=True); ref=[]
    for i,x in D.iterrows():
        ref.append(10000+D[(D.cd<=x.od)&(D.od<x.od)].pnl.sum())
    D['r']=D.pnl/(0.005*np.array(ref)); return D
def S(D):
    D=R(D); return dict(n=len(D),exp=round(float(D.r.mean()),3),pnl=round(float(D.pnl.sum())),L=round(float(D[D.dir=='L'].r.mean()),3),S=round(float(D[D.dir=='S'].r.mean()),3))
for lab,(a,b) in {"E01":("2021-01-01","2024-06-30"),"E02":("2024-07-01","2025-07-31"),"E00":("2021-01-01","2025-07-31")}.items():
    D,_=sim(a,b)
    # entrées prenant une place libérée par un stop du même jour
    n=0;rows=[]
    for i,x in D.iterrows():
        before=D[(D.od<x.od)&(D.cd>=x.od)]  # positions ouvertes au début du jour
        # retirer celles sorties par signal à l'ouverture du jour
        atopen=before[~((before.cd==x.od)&(before.reason=='channel_exit'))]
        same=D[(D.od==x.od)&(D.pair!=x.pair)]
        # rang : entrées du même jour avant celle-ci dans l'ordre liste
        ord_=[p for p in WL]
        earlier=same[same.pair.map(ord_.index)<ord_.index(x.pair)]
        if len(atopen)+len(earlier)>=3:
            stoppers=atopen[(atopen.cd==x.od)&(atopen.reason=='stop_loss')]
            rows.append(dict(pair=x.pair,dir=x.dir,od=x.od.date(),cd=x.cd.date(),reason=x.reason,pnl=round(x.pnl,1),stops_meme_jour=','.join(stoppers.pair),eq=len(atopen)+len(earlier)))
    A=pd.DataFrame(rows)
    print(lab,'trades',len(D),'entrees sur place liberee par un stop du meme jour',len(A),'pnl de ces trades',A.pnl.sum() if len(A) else 0)
    print(A.to_string() if len(A) else '')
    base=S(D)
    Ds,_r=sim(a,b,strict_slots=True); Dse,_=sim(a,b,strict_slots=True,strict_equity=True)
    print(' base',base,'rej',_); print(' places strictes',S(Ds),' + equite ouverture',S(Dse))
    # ordre
    Dr,_=sim(a,b,order=list(reversed(WL))); print(' ordre inverse',S(Dr))
    Dal,_=sim(a,b,order=sorted(WL)); print(' ordre alphabetique',S(Dal))
    random.seed(0); res=[]
    for k in range(200):
        o=WL[:]; random.shuffle(o); DD,_=sim(a,b,order=o); res.append(S(DD))
    Q=pd.DataFrame(res); print(' 200 ordres aleatoires exp: min/p5/med/p95/max',Q.exp.min(),Q.exp.quantile(.05).round(3),Q.exp.median().round(3),Q.exp.quantile(.95).round(3),Q.exp.max(),'pnl',Q.pnl.min(),Q.pnl.median(),Q.pnl.max(),'n',Q.n.min(),Q.n.max(), 'part exp<=.2',(Q.exp<=.2).mean().round(3),'L med',Q.L.median().round(3),'S med',Q.S.median().round(3))
    Q.to_csv(SORTIE+f"/t5_ordres_{lab}.csv",index=False)
