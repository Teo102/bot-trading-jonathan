import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from sim import *
pd.set_option('display.width',220); pd.set_option('display.max_rows',300)
for e,(a,b) in {"E01":("2021-01-01","2024-06-30"),"E02":("2024-07-01","2025-07-31"),"E00-ref":("2021-01-01","2025-07-31")}.items():
    D,rej=sim(a,b)
    t,s=load_trades(e)
    t['sym']=t.pair.str.split('/').str[0]
    A=set(zip(t.sym,t.open_date,t.close_date,t.exit_reason)); B=set(zip(D.pair,D.od,D.cd,D.reason))
    print(e,'export',len(t),'sim',len(D),'communs',len(A&B),'seul export',sorted(A-B)[:6],'seul sim',sorted(B-A)[:6],'rejetes sim',rej,'rejetes export',s['rejected_signals'],'pnl export',round(t.profit_abs.sum(),1),'pnl sim',round(D.pnl.sum(),1),stats(D))
