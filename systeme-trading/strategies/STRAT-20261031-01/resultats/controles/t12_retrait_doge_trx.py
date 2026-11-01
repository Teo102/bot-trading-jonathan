import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from sim import *
def S(D):
    D=D.sort_values('od').reset_index(drop=True); ref=[10000+D[(D.cd<=x.od)&(D.od<x.od)].pnl.sum() for i,x in D.iterrows()]
    D['r']=D.pnl/(0.005*np.array(ref)); return dict(n=len(D),exp=round(float(D.r.mean()),3),pnl=round(float(D.pnl.sum())))
import json
RESUME={}
for lab,(a,b) in {"E01":("2021-01-01","2024-06-30"),"E02":("2024-07-01","2025-07-31"),"E00":("2021-01-01","2025-07-31")}.items():
    RESUME[lab]=dict(base=S(sim(a,b)[0]),sans_doge=S(sim(a,b,order=[x for x in WL if x!='DOGE'])[0]),sans_doge_trx=S(sim(a,b,order=[x for x in WL if x not in('DOGE','TRX')])[0]))
    print(lab,RESUME[lab])
json.dump(RESUME,open(SORTIE+'/t12_resume.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
