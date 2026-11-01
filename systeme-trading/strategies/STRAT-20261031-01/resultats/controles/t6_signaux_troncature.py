import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from common import *
sys.path.insert(0,ROOT)
pd.set_option('display.width',220); pd.set_option('display.max_rows',100)
from TrendDonchianV1 import TrendDonchianV1 as T
st=T({"timeframe":"1d","stake_currency":"USDT","trading_mode":"futures","margin_mode":"isolated","dry_run":True,"exchange":{"name":"binance"},"user_data_dir":sys.argv[1],"strategy":"T"} ) if False else None
class Dummy: pass
s=T.__new__(T); s.entry_period=20;s.exit_period=10;s.atr_period=14;s.regime_period=200
tot=0
for x in WL:
    d=raw(x); a=T.populate_indicators(s,d.copy(),{}); a=T.populate_entry_trend(s,a,{}); a=T.populate_exit_trend(s,a,{})
    o=indicators(d).reset_index()
    el=a.enter_long.fillna(0)==1; es=a.enter_short.fillna(0)==1
    xl=a.exit_long.fillna(0)==1; xs=a.exit_short.fillna(0)==1
    tagl=(a.enter_tag=="breakout_long"); tags=(a.enter_tag=="breakout_short")
    print(x,'dL',(el.values!=o.sig_long.values).sum(),'dS',(es.values!=o.sig_short.values).sum(),'dxL',(xl.values!=o.ex_long.values).sum(),'dxS',(xs.values!=o.ex_short.values).sum(),'atr rel max',np.nanmax(np.abs(a.atr.values/o.atr.values-1)),'L&S',int((el&es).sum()),'tag ok',bool((tagl==el).all() and (tags==es).all()),'nL',int(el.sum()),'nS',int(es.sum()),'sigL&exL',int((el&xl).sum()),'sigS&exS',int((es&xs).sum()),'sigL&exS',int((el&xs).sum()),'sigS&exL',int((es&xl).sum()))
    # troncature : pour dates aléatoires, recalcul sur données coupées
    idx=np.random.default_rng(0).integers(230,len(d)-1,250)
    bad=0
    for i in idx:
        c=T.populate_indicators(s,d.iloc[:i+1].copy(),{}).iloc[-1]; f=a.iloc[i]
        for col in ('dc_high','dc_low','ex_high','ex_low','atr','sma_regime'):
            if not np.isclose(c[col],f[col],rtol=1e-12): bad+=1
    # récursivité : démarrage à 220 bougies avant vs historique complet, mesuré sur chaque ligne
    rec=[]
    for start in ('2021-01-01','2024-07-01'):
        ts=pd.Timestamp(start,tz='UTC'); i0=d.index[d.date>=ts-pd.Timedelta(days=220)][0]
        c=T.populate_indicators(s,d.iloc[i0:].copy(),{})
        f=a.iloc[i0:].reset_index(drop=True)
        c=c.reset_index(drop=True)
        k=f.date>=ts
        rec.append((start,float(np.nanmax(np.abs(c.atr[k]/f.atr[k]-1))),float(np.nanmax(np.abs(c.sma_regime[k]/f.sma_regime[k]-1)))))
    print('   troncature ecarts',bad,'/',len(idx)*6,' variance relative atr, sma',rec)
