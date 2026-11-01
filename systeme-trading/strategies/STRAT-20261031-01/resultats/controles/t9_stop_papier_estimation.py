import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
import sim as M
from sim import *
# Ecart live : ATR de la bougie d'entrée après la première clôture (date < open_date en live car open_date = 00:00:0x)
def sim_live(a,b):
    # réutilise la boucle en modifiant le stop dès J+1 : resserré uniquement
    start=pd.Timestamp(a,tz='UTC'); end=pd.Timestamp(b,tz='UTC'); load=start-pd.Timedelta(days=220)
    D0,_=sim(a,b); tight=0; sooner=0; tot=len(D0); dd=[]
    for i,x in D0.iterrows():
        o=I[x.pair]; ae=o.loc[x.od].atr; ap=o.loc[x.od-pd.Timedelta(days=1)].atr
        s0=x.stop; s1=x.o+(1 if x.dir=='S' else -1)*2*ae
        t=(s1<s0) if x.dir=='S' else (s1>s0)
        if t:
            tight+=1; dd.append(abs(s1-s0)/abs(x.o-s0))
            w=o.loc[x.od+pd.Timedelta(days=1):x.cd]
            hit=((w.high>=s1) if x.dir=='S' else (w.low<=s1))
            if hit.any() and (x.reason!='stop_loss' or hit.idxmax()<x.cd): sooner+=1
    return dict(trades=tot,resserres=tight,part=round(tight/tot,3),med_resserrement=round(float(np.median(dd)),3),max=round(float(np.max(dd)),3),sorties_changees=sooner)
print('E01',sim_live("2021-01-01","2024-06-30")); print('E00',sim_live("2021-01-01","2025-07-31"))
