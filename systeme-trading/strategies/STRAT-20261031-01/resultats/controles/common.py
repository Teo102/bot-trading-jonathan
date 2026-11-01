import json, zipfile, glob, os, math
from pathlib import Path
import numpy as np, pandas as pd
ROOT=str(Path(__file__).resolve().parents[2])
DATA=ROOT+"/user_data/data/binance/futures"
LOCK=pd.Timestamp("2025-08-01",tz="UTC")
WL=["BTC","ETH","XRP","LTC","BCH","LINK","ADA","BNB","DOGE","TRX"]
def load_trades(e, root=ROOT):
    z=sorted(glob.glob(f"{root}/user_data/backtest_results/{e}/*.zip"))[-1]
    with zipfile.ZipFile(z) as zf:
        n=[x for x in zf.namelist() if x.endswith('.json') and 'config' not in x][0]
        d=json.loads(zf.read(n))
    k=list(d["strategy"].keys())[0]
    s=d["strategy"][k]
    df=pd.DataFrame(s["trades"])
    for c in ("open_date","close_date"): df[c]=pd.to_datetime(df[c],utc=True)
    return df,s
def raw(sym):
    d=pd.read_feather(f"{DATA}/{sym}_USDT_USDT-1d-futures.feather").sort_values("date").reset_index(drop=True)
    assert d.date.max()<LOCK
    return d
def fund(sym):
    f=pd.read_feather(f"{DATA}/{sym}_USDT_USDT-1h-funding_rate.feather"); m=pd.read_feather(f"{DATA}/{sym}_USDT_USDT-1h-mark.feather")
    assert f.date.max()<LOCK and m.date.max()<LOCK
    return f,m
def indicators(d, entry=20, exitp=10, atrp=14, reg=200):
    """Recalcul par boucles, sans reprendre le code de la stratégie."""
    h,l,c=d.high.values,d.low.values,d.close.values
    n=len(d); dch=np.full(n,np.nan); dcl=dch.copy(); exh=dch.copy(); exl=dch.copy(); sma=dch.copy(); atr=dch.copy()
    for i in range(n):
        if i>=entry: dch[i]=h[i-entry:i].max(); dcl[i]=l[i-entry:i].min()
        if i>=exitp: exh[i]=h[i-exitp:i].max(); exl[i]=l[i-exitp:i].min()
        if i>=reg-1: sma[i]=c[i-reg+1:i+1].mean()
    # Wilder récursif, ewm adjust=False : a0=tr0, a_i=(1-1/p)a_{i-1}+tr_i/p ; tr0=h-l
    a=None
    for i in range(n):
        tr=h[i]-l[i] if i==0 else max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
        a=tr if a is None else a*(1-1/atrp)+tr/atrp
        if i>=atrp-1: atr[i]=a
    o=d.copy(); o["dch"],o["dcl"],o["exh"],o["exl"],o["sma"],o["atr"]=dch,dcl,exh,exl,sma,atr
    o["sig_long"]=(o.close>o.dch)&(o.close>o.sma)&(o.volume>0)
    o["sig_short"]=(o.close<o.dcl)&(o.close<o.sma)&(o.volume>0)
    o["ex_long"]=o.close<o.exl; o["ex_short"]=o.close>o.exh
    return o.set_index("date")
