import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from sim import *
import random, json
RESUME={}
def R(D):
    D=D.sort_values('od').reset_index(drop=True); ref=[]
    for i,x in D.iterrows():
        ref.append(10000+D[(D.cd<=x.od)&(D.od<x.od)].pnl.sum())
    D['r']=D.pnl/(0.005*np.array(ref)); return D
def S(D):
    D=R(D); return dict(n=len(D),exp=round(float(D.r.mean()),3),pnl=round(float(D.pnl.sum())),L=round(float(D[D.dir=='L'].r.mean()),3),S=round(float(D[D.dir=='S'].r.mean()),3))
for lab,(a,b) in {"E01":("2021-01-01","2024-06-30"),"E02":("2024-07-01","2025-07-31"),"E00":("2021-01-01","2025-07-31")}.items():
    D,rej=sim(a,b); Ds,rejs=sim(a,b,strict_slots=True)
    ka=set(zip(D.pair,D.od)); kb=set(zip(Ds.pair,Ds.od))
    only_base=D[[k in (ka-kb) for k in zip(D.pair,D.od)]]; only_strict=Ds[[k in (kb-ka) for k in zip(Ds.pair,Ds.od)]]
    print(lab,'base',S(D),'rej',rej,'| strict',S(Ds),'rej',rejs)
    print('  seuls base',len(only_base),round(only_base.pnl.sum(),1),'seuls strict',len(only_strict),round(only_strict.pnl.sum(),1))
    # entrées du base où, au début du jour, positions ouvertes non sorties par signal >=3
    an=[]
    for i,x in D.iterrows():
        at=D[(D.od<x.od)&(D.cd>=x.od)&~((D.cd==x.od)&(D.reason=='channel_exit'))]
        stp=at[(at.cd==x.od)&(at.reason=='stop_loss')]
        if len(at)>=3 and len(stp)>0: an.append((x.pair,x.dir,str(x.od.date()),','.join(stp.pair),round(x.pnl,1)))
    print('  entrees avec >=3 positions a l ouverture, place liberee par stop du jour:',len(an),an[:15])
    random.seed(0); res=[]
    for k in range(200):
        o=WL[:]; random.shuffle(o); DD,_=sim(a,b,order=o); res.append(S(DD))
    Q=pd.DataFrame(res); Q.to_csv(SORTIE+f"/t5_ordres_{lab}.csv",index=False)
    RESUME[lab]=dict(base=S(D),rejets_base=int(rej),stricte=S(Ds),rejets_stricte=int(rejs),seuls_base=[len(only_base),round(float(only_base.pnl.sum()),1)],seuls_stricte=[len(only_strict),round(float(only_strict.pnl.sum()),1)],entrees_place_liberee=len(an),exemples=an[:15],exp_min=float(Q.exp.min()),exp_p5=round(float(Q.exp.quantile(.05)),3),exp_med=round(float(Q.exp.median()),3),exp_p95=round(float(Q.exp.quantile(.95)),3),exp_max=float(Q.exp.max()),pnl_min=float(Q.pnl.min()),pnl_med=float(Q.pnl.median()),pnl_max=float(Q.pnl.max()),n_min=int(Q.n.min()),n_max=int(Q.n.max()),part_exp_inf_02=round(float((Q.exp<=.2).mean()),3),part_ordres_sup_base=round(float((Q.exp>=S(D)['exp']).mean()),3))
    print('  200 ordres exp min/p5/med/p95/max',Q.exp.min(),round(float(Q.exp.quantile(.05)),3),round(float(Q.exp.median()),3),round(float(Q.exp.quantile(.95)),3),Q.exp.max(),'| pnl',Q.pnl.min(),Q.pnl.median(),Q.pnl.max(),'| n',Q.n.min(),Q.n.max(),'| part exp<=0.2',round(float((Q.exp<=.2).mean()),3),'| part base>=',round(float((Q.exp>=S(D)['exp']).mean()),3),'| L med',round(float(Q.L.median()),3),'S med',round(float(Q.S.median()),3))
json.dump(RESUME,open(SORTIE+'/t5_resume.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
